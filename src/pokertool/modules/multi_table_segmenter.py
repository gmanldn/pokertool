#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Multi-Table Layout Segmenter
=====================================

Provides deterministic, dependency-light segmentation utilities that isolate
individual poker tables and their surrounding HUD components across single and
multi-table screenshots. The implementation is intentionally pragmatic so it
can execute inside continuous integration pipelines without GPU access whilst
still exposing hooks for more advanced models (YOLO/ONNX/Torch).
"""

from __future__ import annotations

import itertools
import json
import logging
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, NamedTuple, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class DetectedObject(NamedTuple):
    """Unified representation for detected regions."""

    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    area: float
    mask: Optional[np.ndarray] = None


@dataclass
class TableLayout:
    """Metadata for a single detected table and related components."""

    table_id: str
    table_bbox: Tuple[int, int, int, int]
    confidence: float
    components: Dict[str, List[DetectedObject]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_component_count(self, component_type: str) -> int:
        return len(self.components.get(component_type, []))

    def get_best_component(self, component_type: str) -> Optional[DetectedObject]:
        candidates = self.components.get(component_type, [])
        if not candidates:
            return None
        return max(candidates, key=lambda obj: obj.confidence)


@dataclass
class SegmentationResult:
    """High-level result returned by the segmenter."""

    detected_tables: List[TableLayout] = field(default_factory=list)
    processing_time: float = 0.0
    model_used: str = ""
    input_resolution: Tuple[int, int] = (0, 0)  # (height, width)
    confidence_threshold: float = 0.5
    total_objects: int = 0

    def get_table_count(self) -> int:
        return len(self.detected_tables)

    def get_overlapping_tables(self) -> List[Tuple[str, str]]:
        overlaps: List[Tuple[str, str]] = []
        for first, second in itertools.combinations(self.detected_tables, 2):
            if self._boxes_overlap(first.table_bbox, second.table_bbox):
                overlaps.append((first.table_id, second.table_id))
        return overlaps

    @staticmethod
    def _boxes_overlap(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> bool:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        if ax1 >= bx2 or bx1 >= ax2:
            return False
        if ay1 >= by2 or by1 >= ay2:
            return False
        return True


# ---------------------------------------------------------------------------
# Lightweight Torch model (placeholder architecture)
# ---------------------------------------------------------------------------


class PokerSegmentationNet(nn.Module):
    """Minimal convolutional network used for experimentation and tests."""

    def __init__(self, num_classes: int = 12) -> None:
        super().__init__()
        self.num_classes = num_classes

        self.backbone = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )

        self.segmentation_head = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, num_classes, kernel_size=1),
        )

        self.detection_head = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(64, num_classes * 5),
        )

    def forward(self, x: torch.Tensor) -> Dict[str, Any]:
        if getattr(torch, "_POKERTOOL_STUB", False):
            batch, _, height, width = x.shape
            segmentation_map = torch.zeros((batch, self.num_classes, height, width))
            detections = torch.zeros((batch, self.num_classes, 5))
            return {"segmentation": segmentation_map, "detection": detections}

        features = self.backbone(x)
        segmentation_map = self.segmentation_head(features)
        detections_flat = self.detection_head(features)
        detections = detections_flat.view(x.shape[0], self.num_classes, 5)
        return {"segmentation": segmentation_map, "detection": detections}


# ---------------------------------------------------------------------------
# Segmenter implementation
# ---------------------------------------------------------------------------


class MultiTableSegmenter:
    """Detector that isolates tables and major HUD components."""

    SUPPORTED_METHODS = {"traditional", "yolo", "custom", "sam", "onnx"}

    def __init__(
        self,
        model_dir: Optional[str] = None,
        config_path: Optional[str] = None,
        use_gpu: bool = False,
        confidence_threshold: float = 0.55,
        nms_threshold: float = 0.4,
    ) -> None:
        root_dir = Path(__file__).resolve().parents[3]
        self.model_dir = Path(model_dir) if model_dir else root_dir / "models" / "segmenter"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config(config_path)
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold

        self.component_classes = {
            "table": 0,
            "cards_community": 1,
            "chip_stack": 2,
            "dealer_button": 3,
            "hud_panel": 4,
            "timer": 5,
        }

        self.class_colors = {
            "table": (0, 180, 0),
            "cards_community": (240, 240, 240),
            "chip_stack": (0, 0, 220),
            "dealer_button": (0, 220, 220),
            "hud_panel": (220, 120, 0),
            "timer": (180, 0, 180),
        }

        self._table_counter = 0
        self._statistics = {
            "total_frames_processed": 0,
            "total_processing_time": 0.0,
            "total_tables_detected": 0,
        }

    # ------------------------------------------------------------------ #
    # Configuration helpers
    # ------------------------------------------------------------------ #

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        default_config = {
            "segmentation": {
                "input_size": [640, 640],
                "batch_size": 1,
                "max_detections": 100,
                "nms_threshold": 0.4,
                "overlap_threshold": 0.3,
                "min_table_size": 8000,
                "model_preference": ["traditional", "yolo", "custom"],
            }
        }
        if config_path and Path(config_path).is_file():
            try:
                with open(config_path, "r", encoding="utf-8") as handle:
                    disk_config = json.load(handle)
                default_config = self._merge_dicts(default_config, disk_config)
                logger.debug("Loaded segmenter config from %s", config_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to read config %s: %s", config_path, exc)
        return default_config

    def _merge_dicts(self, base: Mapping[str, Any], update: Mapping[str, Any]) -> Dict[str, Any]:
        result = dict(base)
        for key, value in update.items():
            if key in result and isinstance(result[key], Mapping) and isinstance(value, Mapping):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def segment_image(self, image: Any, method: str = "auto") -> SegmentationResult:
        frame = self._load_image(image)
        selected_method = self._select_method(method)

        start = time.perf_counter()
        if selected_method == "traditional":
            tables = self._segment_traditional(frame)
        else:
            # Advanced methods fall back to the deterministic approach for now.
            tables = self._segment_traditional(frame)

        processing_time = time.perf_counter() - start
        result = SegmentationResult(
            detected_tables=tables,
            processing_time=processing_time,
            model_used=selected_method,
            input_resolution=frame.shape[:2],
            confidence_threshold=self.confidence_threshold,
            total_objects=sum(layout.get_component_count("table") for layout in tables),
        )

        self._update_statistics(result)
        return result

    def visualize_segmentation(
        self,
        image: Any,
        result: SegmentationResult,
        output_path: Optional[str] = None,
    ) -> np.ndarray:
        frame = self._load_image(image)
        canvas = frame.copy()

        for layout in result.detected_tables:
            x1, y1, x2, y2 = layout.table_bbox
            cv2.rectangle(canvas, (x1, y1), (x2, y2), self.class_colors["table"], 2)
            cv2.putText(
                canvas,
                layout.table_id,
                (x1 + 4, y1 + 16),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            for component_type, objects in layout.components.items():
                color = self.class_colors.get(component_type, (200, 200, 200))
                for detected in objects:
                    cx1, cy1, cx2, cy2 = detected.bbox
                    cv2.rectangle(canvas, (cx1, cy1), (cx2, cy2), color, 1)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), canvas)

        return canvas

    def extract_table_regions(self, image: Any, result: SegmentationResult) -> Dict[str, np.ndarray]:
        frame = self._load_image(image)
        regions: Dict[str, np.ndarray] = {}
        for layout in result.detected_tables:
            x1, y1, x2, y2 = layout.table_bbox
            regions[layout.table_id] = frame[y1:y2, x1:x2].copy()
        return regions

    def get_component_crops(self, image: Any, result: SegmentationResult) -> Dict[str, Dict[str, List[np.ndarray]]]:
        frame = self._load_image(image)
        crops: Dict[str, Dict[str, List[np.ndarray]]] = {}
        for layout in result.detected_tables:
            table_crops: Dict[str, List[np.ndarray]] = {}
            for component_type, objects in layout.components.items():
                table_crops[component_type] = []
                for obj in objects:
                    x1, y1, x2, y2 = obj.bbox
                    crop = frame[y1:y2, x1:x2]
                    if crop.size > 0:
                        table_crops[component_type].append(crop.copy())
            crops[layout.table_id] = table_crops
        return crops

    def batch_process_images(self, image_paths: Iterable[str], output_dir: Optional[str] = None) -> List[SegmentationResult]:
        results: List[SegmentationResult] = []
        output_root = Path(output_dir) if output_dir else None
        if output_root:
            output_root.mkdir(parents=True, exist_ok=True)

        for path in image_paths:
            result = self.segment_image(path, method="auto")
            results.append(result)

            if output_root:
                stem = Path(path).stem
                vis_path = output_root / f"{stem}_viz.png"
                json_path = output_root / f"{stem}_result.json"
                frame = self._load_image(path)
                self.visualize_segmentation(frame, result, str(vis_path))
                self.export_results([result], str(json_path))

        return results

    def export_results(self, results: Iterable[SegmentationResult], output_path: str, format: str = "json") -> None:
        if format.lower() != "json":
            raise ValueError("Only JSON export is currently supported.")

        payload = []
        for index, result in enumerate(results):
            tables = []
            for layout in result.detected_tables:
                tables.append(
                    {
                        "table_id": layout.table_id,
                        "bbox": layout.table_bbox,
                        "confidence": layout.confidence,
                        "components": [
                            {
                                "type": component_type,
                                "objects": [
                                    {
                                        "class_name": obj.class_name,
                                        "confidence": obj.confidence,
                                        "bbox": obj.bbox,
                                        "area": obj.area,
                                    }
                                    for obj in objects
                                ],
                            }
                            for component_type, objects in layout.components.items()
                        ],
                        "metadata": layout.metadata,
                    }
                )

            payload.append(
                {
                    "image_id": index,
                    "processing_time": result.processing_time,
                    "model_used": result.model_used,
                    "table_count": result.get_table_count(),
                    "tables": tables,
                }
            )

        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def get_statistics(self) -> Dict[str, Any]:
        processed = max(1, self._statistics["total_frames_processed"])
        return {
            "total_frames_processed": self._statistics["total_frames_processed"],
            "total_tables_detected": self._statistics["total_tables_detected"],
            "avg_processing_time": self._statistics["total_processing_time"] / processed,
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _load_image(self, image: Any) -> np.ndarray:
        if isinstance(image, str):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image}")
            frame = cv2.imread(str(image_path))
            if frame is None:  # pragma: no cover - defensive
                raise ValueError(f"Unable to read image: {image}")
            return frame
        if isinstance(image, np.ndarray):
            if image.dtype != np.uint8:
                frame = np.clip(image, 0, 255).astype(np.uint8)
            else:
                frame = image
            return frame
        raise ValueError("Unsupported image type. Provide a path or numpy array.")

    def _select_method(self, requested: str) -> str:
        if requested == "auto":
            preference = self.config["segmentation"].get("model_preference", ["traditional"])
            for candidate in preference:
                if candidate in self.SUPPORTED_METHODS:
                    return candidate
            return "traditional"
        if requested in self.SUPPORTED_METHODS:
            return requested
        logger.debug("Requested segmentation method '%s' unsupported; falling back to traditional", requested)
        return "traditional"

    def _segment_traditional(self, frame: np.ndarray) -> List[TableLayout]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Broad green range captures the felt of most poker tables.
        lower_green = np.array([35, 25, 25])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        mask = cv2.medianBlur(mask, 5)
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = int(self.config["segmentation"].get("min_table_size", 8000))

        layouts: List[TableLayout] = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            x1, y1, x2, y2 = x, y, x + w, y + h

            confidence = self._confidence_from_area(area, frame.shape[:2])
            if confidence < self.confidence_threshold:
                continue

            table_id = self._next_table_id()
            detected = DetectedObject(
                class_name="table",
                confidence=confidence,
                bbox=(x1, y1, x2, y2),
                center=(x1 + w // 2, y1 + h // 2),
                area=float(area),
            )

            components = {"table": [detected]}
            components.update(self._detect_secondary_components(frame, detected))

            layouts.append(
                TableLayout(
                    table_id=table_id,
                    table_bbox=(x1, y1, x2, y2),
                    confidence=confidence,
                    components=components,
                    metadata={"method": "traditional"},
                )
            )

        layouts.sort(key=lambda layout: layout.confidence, reverse=True)
        return layouts

    def _confidence_from_area(self, area: float, resolution: Tuple[int, int]) -> float:
        height, width = resolution
        frame_area = height * width
        if frame_area == 0:
            return 0.0
        ratio = min(1.0, area / max(frame_area * 0.4, 1))  # expect up to ~40% coverage
        return 0.6 + 0.4 * ratio

    def _detect_secondary_components(self, frame: np.ndarray, table_object: DetectedObject) -> Dict[str, List[DetectedObject]]:
        x1, y1, x2, y2 = table_object.bbox
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return {}

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        cards_contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        components: Dict[str, List[DetectedObject]] = {}
        card_objects: List[DetectedObject] = []
        for contour in cards_contours:
            area = cv2.contourArea(contour)
            if area < 150:
                continue
            cx, cy, cw, ch = cv2.boundingRect(contour)
            card_objects.append(
                DetectedObject(
                    class_name="cards_community",
                    confidence=0.7,
                    bbox=(x1 + cx, y1 + cy, x1 + cx + cw, y1 + cy + ch),
                    center=(x1 + cx + cw // 2, y1 + cy + ch // 2),
                    area=float(area),
                )
            )

        if card_objects:
            components["cards_community"] = card_objects

        return components

    def _next_table_id(self) -> str:
        self._table_counter += 1
        return f"table_{self._table_counter}"

    def _update_statistics(self, result: SegmentationResult) -> None:
        self._statistics["total_frames_processed"] += 1
        self._statistics["total_processing_time"] += result.processing_time
        self._statistics["total_tables_detected"] += result.get_table_count()


# Public factory -------------------------------------------------------------


def create_segmenter(**kwargs: Any) -> MultiTableSegmenter:
    return MultiTableSegmenter(**kwargs)
