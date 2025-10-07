#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Adaptive UI Change Detection Module
============================================

Detects layout, colour, and component level changes in supported poker clients
so scraping pipelines can be updated before production regressions occur.

The detector keeps a library of canonical baseline screenshots, compares every
new capture against the closest baseline using perceptual hashes and regional
similarity metrics, and emits rich alert reports (optionally with diff
visualisations) whenever the deviation exceeds configured thresholds.

All functionality in this module is intentionally dependency-light so it can
run inside CI and automated QA harnesses without GPU access.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple
from typing import NamedTuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight data structures
# ---------------------------------------------------------------------------


class RegionOfInterest(NamedTuple):
    """Normalised description of a region to analyse within a screenshot.

    Coordinates are expressed in relative units (0.0 - 1.0) so they can be
    reused across resolutions. The ``critical`` flag elevates alerts whenever
    the region falls below its similarity threshold.
    """

    name: str
    x: float
    y: float
    width: float
    height: float
    threshold: float
    critical: bool = False


@dataclass
class BaselineState:
    """Serialisable description of a baseline screenshot."""

    baseline_id: str
    site_name: str
    resolution: str
    theme: str
    file_path: str
    created_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    hashes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "site_name": self.site_name,
            "resolution": self.resolution,
            "theme": self.theme,
            "file_path": self.file_path,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "hashes": self.hashes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BaselineState":
        return cls(
            baseline_id=payload["baseline_id"],
            site_name=payload["site_name"],
            resolution=payload["resolution"],
            theme=payload.get("theme", "default"),
            file_path=payload["file_path"],
            created_at=float(payload.get("created_at", time.time())),
            metadata=dict(payload.get("metadata", {})),
            hashes=dict(payload.get("hashes", {})),
        )


@dataclass
class ComparisonResult:
    """Outcome generated when comparing an image to the baseline library."""

    is_match: bool
    best_match_score: float
    best_match_baseline: str
    hash_distances: Dict[str, int]
    ssim_scores: Dict[str, float]
    diff_regions: List[str]
    critical_changes: List[str]
    analysis_time_ms: float = 0.0
    evaluated_baselines: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_match": self.is_match,
            "best_match_score": self.best_match_score,
            "best_match_baseline": self.best_match_baseline,
            "hash_distances": self.hash_distances,
            "ssim_scores": self.ssim_scores,
            "diff_regions": self.diff_regions,
            "critical_changes": self.critical_changes,
            "analysis_time_ms": self.analysis_time_ms,
            "evaluated_baselines": self.evaluated_baselines,
        }


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _parse_resolution(resolution: str) -> Tuple[int, int]:
    try:
        width, height = resolution.lower().split("x")
        return int(width), int(height)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid resolution string: {resolution!r}") from exc


def _ensure_uint8(image: np.ndarray) -> np.ndarray:
    if image.dtype == np.uint8:
        return image
    image = np.clip(image, 0, 255)
    return image.astype(np.uint8)


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _average_hash(image: np.ndarray, hash_size: int = 8) -> str:
    gray = _to_grayscale(image)
    resized = cv2.resize(gray, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
    mean = resized.mean()
    bits = (resized > mean).astype(np.uint8).flatten()
    return "".join(str(bit) for bit in bits)


def _difference_hash(image: np.ndarray, hash_size: int = 8) -> str:
    gray = _to_grayscale(image)
    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return "".join("1" if value else "0" for value in diff.flatten())


def _phash(image: np.ndarray, hash_size: int = 8) -> str:
    gray = _to_grayscale(image)
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    resized = np.float32(resized)
    dct = cv2.dct(resized)
    dct_low_freq = dct[:hash_size, :hash_size]
    median = np.median(dct_low_freq)
    return "".join("1" if coeff > median else "0" for coeff in dct_low_freq.flatten())


def _hamming_distance(hash_a: str, hash_b: str) -> int:
    if len(hash_a) != len(hash_b):
        return max(len(hash_a), len(hash_b))
    return sum(ch1 != ch2 for ch1, ch2 in zip(hash_a, hash_b))


# ---------------------------------------------------------------------------
# Adaptive UI Detector implementation
# ---------------------------------------------------------------------------


class AdaptiveUIDetector:
    """High level manager for UI baseline comparison and alerting."""

    def __init__(
        self,
        baseline_dir: Optional[str] = None,
        reports_dir: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        root_dir = Path(__file__).resolve().parents[3]
        self.baseline_dir = Path(baseline_dir) if baseline_dir else root_dir / "assets" / "ui_baselines"
        self.reports_dir = Path(reports_dir) if reports_dir else root_dir / "reports" / "ui_changes"

        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config(config_path)
        self.regions_of_interest = self._initialise_regions()

        self.baselines: Dict[str, BaselineState] = {}
        self._load_existing_baselines()

        self._stats: Dict[str, float] = {
            "total_comparisons": 0,
            "matches_found": 0,
            "changes_detected": 0,
            "total_processing_time_ms": 0.0,
        }

        logger.debug(
            "AdaptiveUIDetector initialised (baselines=%s, baseline_dir=%s)",
            len(self.baselines),
            self.baseline_dir,
        )

    # ------------------------------------------------------------------ #
    # Configuration
    # ------------------------------------------------------------------ #

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        config = {
            "ui_detection": {
                "global_ssim_threshold": 0.85,
                "hash_distance_threshold": 10,
                "alert_critical_changes": True,
                "generate_visualizations": False,
                "max_baselines_per_site": 50,
            },
            "regions": {
                "default": [
                    {
                        "name": "cards_area",
                        "x": 0.35,
                        "y": 0.42,
                        "width": 0.30,
                        "height": 0.16,
                        "threshold": 0.9,
                        "critical": True,
                    },
                    {
                        "name": "pot_area",
                        "x": 0.44,
                        "y": 0.30,
                        "width": 0.12,
                        "height": 0.10,
                        "threshold": 0.88,
                        "critical": True,
                    },
                    {
                        "name": "action_buttons",
                        "x": 0.60,
                        "y": 0.78,
                        "width": 0.30,
                        "height": 0.18,
                        "threshold": 0.80,
                        "critical": False,
                    },
                ]
            },
        }

        if config_path and Path(config_path).is_file():
            try:
                with open(config_path, "r", encoding="utf-8") as handle:
                    disk_config = json.load(handle)
                config = self._merge_dicts(config, disk_config)
                logger.debug("Loaded UI detection config from %s", config_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to load config %s: %s", config_path, exc)

        return config

    def _merge_dicts(self, base: MutableMapping[str, Any], update: Mapping[str, Any]) -> Dict[str, Any]:
        for key, value in update.items():
            if key in base and isinstance(base[key], MutableMapping) and isinstance(value, Mapping):
                base[key] = self._merge_dicts(base[key], value)
            else:
                base[key] = value
        return dict(base)

    def _initialise_regions(self) -> Dict[str, RegionOfInterest]:
        entries = self.config.get("regions", {}).get("default", [])
        regions: Dict[str, RegionOfInterest] = {}
        for entry in entries:
            roi = RegionOfInterest(
                entry["name"],
                float(entry["x"]),
                float(entry["y"]),
                float(entry["width"]),
                float(entry["height"]),
                float(entry.get("threshold", 0.85)),
                bool(entry.get("critical", False)),
            )
            regions[roi.name] = roi
        return regions

    # ------------------------------------------------------------------ #
    # Baseline management
    # ------------------------------------------------------------------ #

    def _load_existing_baselines(self) -> None:
        for meta_file in self.baseline_dir.glob("*.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                baseline = BaselineState.from_dict(payload)
                if Path(baseline.file_path).exists():
                    self.baselines[baseline.baseline_id] = baseline
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to load baseline metadata %s: %s", meta_file, exc)

    def add_baseline_screenshot(
        self,
        screenshot_path: str,
        site_name: str,
        resolution: str,
        theme: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        image_path = Path(screenshot_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

        image = cv2.imread(str(image_path))
        if image is None:  # pragma: no cover - defensive
            raise ValueError(f"Unable to read screenshot: {screenshot_path}")

        baseline_id = self._build_baseline_id(site_name, resolution)
        file_name = f"{baseline_id}.png"
        dest_path = self.baseline_dir / file_name

        cv2.imwrite(str(dest_path), _ensure_uint8(image))

        hashes = self._compute_hashes(image)
        baseline = BaselineState(
            baseline_id=baseline_id,
            site_name=site_name,
            resolution=resolution,
            theme=theme,
            file_path=str(dest_path),
            created_at=time.time(),
            metadata=metadata or {},
            hashes=hashes,
        )

        self.baselines[baseline_id] = baseline
        self._enforce_baseline_limit(site_name)
        self._persist_baseline(baseline)

        logger.info("Added baseline %s for %s (%s)", baseline_id, site_name, resolution)
        return baseline_id

    def _build_baseline_id(self, site_name: str, resolution: str) -> str:
        identifier = uuid.uuid4().hex[:8]
        safe_site = site_name.lower().replace(" ", "_")
        safe_res = resolution.lower().replace(" ", "")
        return f"{safe_site}_{safe_res}_{identifier}"

    def _enforce_baseline_limit(self, site_name: str) -> None:
        max_baselines = int(
            self.config.get("ui_detection", {}).get("max_baselines_per_site", 50)
        )
        entries = [
            baseline
            for baseline in self.baselines.values()
            if baseline.site_name.lower() == site_name.lower()
        ]
        if len(entries) <= max_baselines:
            return
        entries.sort(key=lambda item: item.created_at)
        for baseline in entries[:-max_baselines]:
            self._remove_baseline(baseline.baseline_id)

    def _remove_baseline(self, baseline_id: str) -> None:
        baseline = self.baselines.pop(baseline_id, None)
        if not baseline:
            return
        try:
            Path(baseline.file_path).unlink(missing_ok=True)
            meta_path = self.baseline_dir / f"{baseline_id}.json"
            meta_path.unlink(missing_ok=True)
            logger.debug("Pruned baseline %s", baseline_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to prune baseline %s: %s", baseline_id, exc)

    def _persist_baseline(self, baseline: BaselineState) -> None:
        meta_path = self.baseline_dir / f"{baseline.baseline_id}.json"
        with open(meta_path, "w", encoding="utf-8") as handle:
            json.dump(baseline.to_dict(), handle, indent=2)

    # ------------------------------------------------------------------ #
    # Comparison workflow
    # ------------------------------------------------------------------ #

    def compare_screenshot(
        self,
        screenshot: Any,
        site_name: str,
        resolution: str,
        theme: str = "default",
    ) -> ComparisonResult:
        start = time.perf_counter()
        image = self._load_image(screenshot)
        candidate_baselines = self._select_candidate_baselines(site_name, resolution, theme)

        if not candidate_baselines:
            duration_ms = (time.perf_counter() - start) * 1000
            return ComparisonResult(
                is_match=False,
                best_match_score=0.0,
                best_match_baseline="",
                hash_distances={},
                ssim_scores={},
                diff_regions=[],
                critical_changes=[],
                analysis_time_ms=duration_ms,
                evaluated_baselines=0,
            )

        best_score = -1.0
        best_result: Optional[ComparisonResult] = None

        current_hashes = self._compute_hashes(image)

        for baseline in candidate_baselines:
            baseline_image = cv2.imread(baseline.file_path)
            if baseline_image is None:  # pragma: no cover - defensive
                continue

            baseline_image = self._ensure_same_size(baseline_image, image)

            score, region_scores, diff_regions, critical_regions = self._compare_regions(
                baseline_image, image, site_name
            )

            hash_distances = {
                key: _hamming_distance(baseline.hashes.get(key, ""), current_hashes.get(key, ""))
                for key in current_hashes
            }

            result = ComparisonResult(
                is_match=self._is_match(score, hash_distances, critical_regions),
                best_match_score=score,
                best_match_baseline=baseline.baseline_id,
                hash_distances=hash_distances,
                ssim_scores=region_scores,
                diff_regions=diff_regions,
                critical_changes=critical_regions,
                analysis_time_ms=0.0,  # set after loop
            )

            if score > best_score:
                best_score = score
                best_result = result

        duration_ms = (time.perf_counter() - start) * 1000

        if best_result is None:
            best_result = ComparisonResult(
                is_match=False,
                best_match_score=0.0,
                best_match_baseline="",
                hash_distances={},
                ssim_scores={},
                diff_regions=[],
                critical_changes=[],
                analysis_time_ms=duration_ms,
                evaluated_baselines=len(candidate_baselines),
            )
        else:
            best_result.analysis_time_ms = duration_ms
            best_result.evaluated_baselines = len(candidate_baselines)

        self._update_statistics(best_result, duration_ms)
        return best_result

    def _load_image(self, screenshot: Any) -> np.ndarray:
        if isinstance(screenshot, str):
            image_path = Path(screenshot)
            if not image_path.exists():
                raise FileNotFoundError(f"Screenshot not found: {screenshot}")
            image = cv2.imread(str(image_path))
            if image is None:  # pragma: no cover - defensive
                raise ValueError(f"Unable to read screenshot: {screenshot}")
            return image
        if isinstance(screenshot, np.ndarray):
            return _ensure_uint8(screenshot)
        raise ValueError("Unsupported screenshot type. Provide file path or numpy array.")

    def _select_candidate_baselines(
        self,
        site_name: str,
        resolution: str,
        theme: str,
    ) -> List[BaselineState]:
        def _match(b: BaselineState, by_theme: bool = True) -> bool:
            if b.site_name.lower() != site_name.lower():
                return False
            if b.resolution.lower() != resolution.lower():
                return False
            if by_theme and b.theme.lower() != theme.lower():
                return False
            return True

        # Prefer exact match including theme.
        exact = [baseline for baseline in self.baselines.values() if _match(baseline)]
        if exact:
            return exact

        # Fallback to matching site + resolution.
        resolution_match = [baseline for baseline in self.baselines.values() if _match(baseline, by_theme=False)]
        if resolution_match:
            return resolution_match

        # Fallback to site level.
        site_match = [
            baseline for baseline in self.baselines.values() if baseline.site_name.lower() == site_name.lower()
        ]
        if site_match:
            return site_match

        return list(self.baselines.values())

    def _ensure_same_size(self, baseline: np.ndarray, current: np.ndarray) -> np.ndarray:
        if baseline.shape[:2] == current.shape[:2]:
            return baseline
        target_size = (current.shape[1], current.shape[0])
        return cv2.resize(baseline, target_size, interpolation=cv2.INTER_AREA)

    def _compare_regions(
        self,
        baseline_image: np.ndarray,
        current_image: np.ndarray,
        site_name: str,
    ) -> Tuple[float, Dict[str, float], List[str], List[str]]:
        height, width = current_image.shape[:2]
        regions = self._resolve_regions(width, height, site_name)

        total_score = 0.0
        total_weight = 0.0
        ssim_scores: Dict[str, float] = {}
        diff_regions: List[str] = []
        critical_regions: List[str] = []

        for roi in regions:
            x1, y1, x2, y2 = roi
            baseline_roi = baseline_image[y1:y2, x1:x2]
            current_roi = current_image[y1:y2, x1:x2]
            if baseline_roi.size == 0 or current_roi.size == 0:
                continue

            score = self._region_similarity(baseline_roi, current_roi)
            name = self._region_name_lookup[(x1, y1, x2, y2)]
            region_config = self.regions_of_interest[name]

            ssim_scores[name] = score
            weight = 2.0 if region_config.critical else 1.0
            total_score += score * weight
            total_weight += weight

            if score < region_config.threshold:
                diff_regions.append(name)
                if region_config.critical:
                    critical_regions.append(name)

        if total_weight == 0:
            average_score = 0.0
        else:
            average_score = total_score / total_weight

        # Global sanity check if no regions defined.
        if not ssim_scores:
            average_score = self._region_similarity(baseline_image, current_image)

        return average_score, ssim_scores, diff_regions, critical_regions

    def _resolve_regions(self, width: int, height: int, site_name: str) -> List[Tuple[int, int, int, int]]:
        # For now site specific overrides reuse default regions, but hook is left
        # in place for future extensions.
        region_entries = list(self.regions_of_interest.values())
        bounds: List[Tuple[int, int, int, int]] = []
        self._region_name_lookup: Dict[Tuple[int, int, int, int], str] = {}
        for entry in region_entries:
            x1 = int(entry.x * width)
            y1 = int(entry.y * height)
            x2 = int(min(width, x1 + entry.width * width))
            y2 = int(min(height, y1 + entry.height * height))
            x1, y1 = max(0, x1), max(0, y1)
            x2 = max(x2, x1 + 1)
            y2 = max(y2, y1 + 1)
            bounds.append((x1, y1, x2, y2))
            self._region_name_lookup[(x1, y1, x2, y2)] = entry.name
        return bounds

    def _region_similarity(self, baseline: np.ndarray, current: np.ndarray) -> float:
        baseline_uint8 = _ensure_uint8(baseline)
        current_uint8 = _ensure_uint8(current)

        baseline_gray = _to_grayscale(baseline_uint8).astype(np.float32) / 255.0
        current_gray = _to_grayscale(current_uint8).astype(np.float32) / 255.0
        if baseline_gray.shape != current_gray.shape:
            current_gray = cv2.resize(
                current_gray,
                (baseline_gray.shape[1], baseline_gray.shape[0]),
                interpolation=cv2.INTER_AREA,
            )

        gray_diff = np.abs(baseline_gray - current_gray).mean()

        baseline_lab = cv2.cvtColor(baseline_uint8, cv2.COLOR_BGR2LAB).astype(np.float32)
        current_lab = cv2.cvtColor(current_uint8, cv2.COLOR_BGR2LAB).astype(np.float32)
        if baseline_lab.shape != current_lab.shape:
            current_lab = cv2.resize(
                current_lab,
                (baseline_lab.shape[1], baseline_lab.shape[0]),
                interpolation=cv2.INTER_AREA,
            )
        colour_diff = np.abs(baseline_lab - current_lab).mean() / 255.0

        baseline_rgb = baseline_uint8.astype(np.float32)
        current_rgb = current_uint8.astype(np.float32)
        channel_diff = np.abs(baseline_rgb - current_rgb).mean() / 255.0

        combined = (gray_diff + colour_diff + channel_diff) / 3.0
        score = 1.0 - min(1.0, combined * 4.5)
        return float(max(0.0, min(1.0, score)))

    def _compute_hashes(self, image: np.ndarray) -> Dict[str, str]:
        return {
            "average": _average_hash(image),
            "difference": _difference_hash(image),
            "perceptual": _phash(image),
        }

    def _is_match(self, score: float, hashes: Mapping[str, int], critical_regions: Iterable[str]) -> bool:
        threshold = float(self.config["ui_detection"].get("global_ssim_threshold", 0.85))
        hash_threshold = int(self.config["ui_detection"].get("hash_distance_threshold", 10))
        hash_ok = all(distance <= hash_threshold for distance in hashes.values())

        if score >= threshold and hash_ok and not list(critical_regions):
            return True
        return False

    def _update_statistics(self, result: ComparisonResult, duration_ms: float) -> None:
        self._stats["total_comparisons"] += 1
        self._stats["total_processing_time_ms"] += duration_ms
        if result.is_match:
            self._stats["matches_found"] += 1
        if result.critical_changes:
            self._stats["changes_detected"] += 1

    # ------------------------------------------------------------------ #
    # Reporting utilities
    # ------------------------------------------------------------------ #

    def generate_alert_report(
        self,
        result: ComparisonResult,
        screenshot_path: str,
        site_name: str,
    ) -> str:
        report_id = f"ui_change_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        report_path = self.reports_dir / f"{report_id}.json"

        alert_level = "INFO"
        if result.critical_changes:
            alert_level = "CRITICAL"
        elif result.diff_regions:
            alert_level = "WARNING"

        payload = {
            "report_id": report_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "site_name": site_name,
            "alert_level": alert_level,
            "is_match": result.is_match,
            "match_score": result.best_match_score,
            "best_baseline": result.best_match_baseline,
            "critical_regions": result.critical_changes,
            "diff_regions": result.diff_regions,
            "hash_distances": result.hash_distances,
            "ssim_scores": result.ssim_scores,
            "recommendations": self._generate_recommendations(result),
            "screenshot_path": screenshot_path,
        }

        visualization_path = None
        if self.config["ui_detection"].get("generate_visualizations", False):
            try:
                visualization_path = self._generate_visualization(
                    screenshot_path,
                    result.best_match_baseline,
                    report_id,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to generate visualization: %s", exc)

        if visualization_path:
            payload["visualization_path"] = visualization_path

        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        logger.info("UI change report generated at %s", report_path)
        return str(report_path)

    def _generate_visualization(self, screenshot_path: str, baseline_id: str, report_id: str) -> Optional[str]:
        baseline = self.baselines.get(baseline_id)
        if baseline is None:
            return None

        live_image = cv2.imread(screenshot_path)
        baseline_image = cv2.imread(baseline.file_path)
        if live_image is None or baseline_image is None:
            return None

        baseline_image = self._ensure_same_size(baseline_image, live_image)

        diff = cv2.absdiff(baseline_image, live_image)
        heatmap = cv2.applyColorMap(cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(live_image, 0.6, heatmap, 0.4, 0)

        vis_path = self.reports_dir / f"{report_id}_diff.png"
        cv2.imwrite(str(vis_path), overlay)
        return str(vis_path)

    def _generate_recommendations(self, result: ComparisonResult) -> List[str]:
        if result.critical_changes:
            recommendations = [
                "IMMEDIATE ACTION REQUIRED: Critical UI regions changed.",
                "Card detection may be affected; validate OCR pipelines before deploying.",
                "Re-run adaptive scraper QA harness and notify on-call engineer.",
            ]
        elif result.diff_regions:
            recommendations = [
                "Review UI diffs and adjust scraper templates if necessary.",
                "Schedule targeted regression tests for affected regions.",
            ]
        else:
            recommendations = ["No significant changes detected. Continue monitoring."]
        return recommendations

    # ------------------------------------------------------------------ #
    # Statistics and helpers
    # ------------------------------------------------------------------ #

    def get_detection_statistics(self) -> Dict[str, Any]:
        comparisons = max(1, int(self._stats["total_comparisons"]))
        return {
            "total_comparisons": int(self._stats["total_comparisons"]),
            "matches_found": int(self._stats["matches_found"]),
            "changes_detected": int(self._stats["changes_detected"]),
            "avg_processing_time": self._stats["total_processing_time_ms"] / comparisons,
        }


def create_detector(baseline_dir: Optional[str] = None, reports_dir: Optional[str] = None) -> AdaptiveUIDetector:
    """Factory for external callers."""
    return AdaptiveUIDetector(baseline_dir=baseline_dir, reports_dir=reports_dir)
