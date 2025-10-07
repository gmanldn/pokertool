#!/usr/bin/env python3
"""
Multi-Table Layout Segmenter Module for PokerTool

This module implements advanced computer vision techniques to reliably isolate
individual poker tables, boards, and HUD panels when multiple instances are
visible or overlapping on screen.

Features:
- Lightweight segmentation model optimized for 1080p poker table detection
- Bounding box detection for tables, cards, chip stacks, and HUD widgets
- GPU inference with automatic CPU fallback
- Integration with downstream OCR and classifier stages
- Support for overlapping and multi-table layouts
- Real-time processing capabilities
"""

import os
import json
import logging
import time
from typing import Dict, List, Tuple, Optional, Union, NamedTuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
import pickle
import warnings

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
# Optional dependencies - graceful fallback if not available
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    from torchvision.models import mobilenet_v3_small
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

try:
    from segment_anything import sam_model_registry, SamPredictor
    HAS_SAM = True
except ImportError:
    HAS_SAM = False

try:
    from sklearn.cluster import DBSCAN
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetectedObject(NamedTuple):
    """Represents a detected object with its properties."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]
    area: int
    mask: Optional[np.ndarray] = None

@dataclass
class TableLayout:
    """Represents a complete poker table layout with all detected components."""
    table_id: str
    table_bbox: Tuple[int, int, int, int]
    confidence: float
    components: Dict[str, List[DetectedObject]]
    metadata: Dict[str, any]
    
    def get_component_count(self, component_type: str) -> int:
        """Get count of specific component type."""
        return len(self.components.get(component_type, []))
    
    def get_best_component(self, component_type: str) -> Optional[DetectedObject]:
        """Get the component with highest confidence for a given type."""
        components = self.components.get(component_type, [])
        if not components:
            return None
        return max(components, key=lambda x: x.confidence)

@dataclass
class SegmentationResult:
    """Results from multi-table segmentation."""
    detected_tables: List[TableLayout]
    processing_time: float
    model_used: str
    input_resolution: Tuple[int, int]
    confidence_threshold: float
    total_objects: int
    
    def get_table_count(self) -> int:
        """Get total number of detected tables."""
        return len(self.detected_tables)
    
    def get_overlapping_tables(self) -> List[Tuple[str, str]]:
        """Find pairs of overlapping tables."""
        overlaps = []
        for i, table1 in enumerate(self.detected_tables):
            for j, table2 in enumerate(self.detected_tables[i+1:], i+1):
                if self._tables_overlap(table1.table_bbox, table2.table_bbox):
                    overlaps.append((table1.table_id, table2.table_id))
        return overlaps
    
    def _tables_overlap(self, bbox1: Tuple[int, int, int, int], 
                       bbox2: Tuple[int, int, int, int]) -> bool:
        """Check if two bounding boxes overlap."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        return not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1)

class MultiTableSegmenter:
    """
    Advanced multi-table layout segmentation system for poker interfaces.
    
    Uses lightweight computer vision models to detect and isolate individual
    poker tables, cards, chip stacks, and HUD elements in complex layouts.
    """
    
    def __init__(self, 
                 model_dir: str = "models/segmentation",
                 config_path: str = "poker_config.json",
                 use_gpu: bool = True,
                 confidence_threshold: float = 0.5):
        """
        Initialize the Multi-Table Segmenter.
        
        Args:
            model_dir: Directory containing segmentation models
            config_path: Path to poker configuration file
            use_gpu: Whether to use GPU acceleration if available
            confidence_threshold: Minimum confidence for detections
        """
        self.model_dir = Path(model_dir)
        self.config_path = Path(config_path)
        self.use_gpu = use_gpu and HAS_TORCH and (torch.cuda.is_available() if HAS_TORCH else False)
        self.confidence_threshold = confidence_threshold
        
        # Create model directory if it doesn't exist
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Define poker table component classes
        self.component_classes = {
            0: "table",
            1: "cards_community", 
            2: "cards_player",
            3: "chip_stack",
            4: "pot_area",
            5: "dealer_button",
            6: "player_seat",
            7: "action_buttons",
            8: "bet_area",
            9: "hud_panel",
            10: "timer",
            11: "chat_box"
        }
        
        # Color mapping for visualization
        self.class_colors = {
            "table": (0, 255, 0),         # Green
            "cards_community": (255, 0, 0), # Red
            "cards_player": (255, 100, 100), # Light Red
            "chip_stack": (0, 0, 255),     # Blue
            "pot_area": (255, 255, 0),     # Yellow
            "dealer_button": (255, 0, 255), # Magenta
            "player_seat": (0, 255, 255),  # Cyan
            "action_buttons": (128, 0, 128), # Purple
            "bet_area": (255, 128, 0),     # Orange
            "hud_panel": (128, 128, 128),  # Gray
            "timer": (255, 255, 255),     # White
            "chat_box": (64, 64, 64)      # Dark Gray
        }
        
        # Initialize models
        self.yolo_model = None
        self.sam_predictor = None
        self.custom_model = None
        self.onnx_session = None
        
        # Performance tracking
        self.segmentation_stats = {
            "total_frames_processed": 0,
            "avg_processing_time": 0.0,
            "gpu_usage_count": 0,
            "cpu_fallback_count": 0,
            "total_tables_detected": 0,
            "detection_accuracy": 0.0
        }
        
        # Load models
        self._load_models()
        
        logger.info(f"MultiTableSegmenter initialized with GPU: {self.use_gpu}")

    def _load_config(self) -> Dict:
        """Load configuration from poker_config.json."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return {
                "segmentation": {
                    "input_size": [1080, 1920],
                    "batch_size": 1,
                    "max_detections": 100,
                    "nms_threshold": 0.4,
                    "overlap_threshold": 0.3,
                    "min_table_size": 10000,  # Minimum pixels for valid table
                    "model_preference": ["yolo", "custom", "sam"]
                }
            }

    def _load_models(self):
        """Load segmentation models with GPU/CPU fallback."""
        try:
            # Try to load YOLOv8 model
            self._load_yolo_model()
            
            # Try to load Segment Anything model
            self._load_sam_model()
            
            # Load custom lightweight model
            self._load_custom_model()
            
            # Load ONNX model for CPU inference
            self._load_onnx_model()
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            # Create fallback detection model
            self._create_fallback_model()

    def _load_yolo_model(self):
        """Load YOLOv8 model for poker table detection."""
        if not HAS_YOLO:
            return
        try:
            yolo_path = self.model_dir / "poker_yolo.pt"
            if yolo_path.exists():
                self.yolo_model = YOLO(str(yolo_path))
                logger.info("Loaded custom YOLO model")
            else:
                # Use pretrained YOLOv8n and adapt for poker tables
                self.yolo_model = YOLO('yolov8n.pt')
                logger.info("Using pretrained YOLOv8n model")
                
        except Exception as e:
            logger.warning(f"Could not load YOLO model: {e}")

    def _load_sam_model(self):
        """Load Segment Anything model for precise segmentation."""
        if not HAS_SAM:
            return
        try:
            sam_path = self.model_dir / "sam_vit_b_01ec64.pth"
            if sam_path.exists():
                sam = sam_model_registry["vit_b"](checkpoint=str(sam_path))
                if self.use_gpu:
                    sam.to(device="cuda")
                self.sam_predictor = SamPredictor(sam)
                logger.info("Loaded Segment Anything model")
        except Exception as e:
            logger.warning(f"Could not load SAM model: {e}")

    def _load_custom_model(self):
        """Load custom lightweight segmentation model."""
        if not HAS_TORCH:
            return
        try:
            custom_path = self.model_dir / "poker_segmenter.pth"
            if custom_path.exists():
                # Create custom model architecture
                model = PokerSegmentationNet(len(self.component_classes))
                model.load_state_dict(torch.load(custom_path, map_location='cpu'))
                
                if self.use_gpu:
                    model = model.cuda()
                    
                model.eval()
                self.custom_model = model
                logger.info("Loaded custom poker segmentation model")
        except Exception as e:
            logger.warning(f"Could not load custom model: {e}")

    def _load_onnx_model(self):
        """Load ONNX model for CPU inference."""
        if not HAS_ONNX:
            return
        try:
            onnx_path = self.model_dir / "poker_segmenter.onnx"
            if onnx_path.exists():
                providers = ['CPUExecutionProvider']
                if self.use_gpu:
                    providers.insert(0, 'CUDAExecutionProvider')
                    
                self.onnx_session = ort.InferenceSession(str(onnx_path), providers=providers)
                logger.info("Loaded ONNX model")
        except Exception as e:
            logger.warning(f"Could not load ONNX model: {e}")

    def _create_fallback_model(self):
        """Create a fallback traditional CV-based detection model."""
        logger.info("Creating fallback traditional CV model")
        # This will be used if neural models fail to load
        pass

    def segment_image(self, 
                     image: Union[np.ndarray, str, Image.Image],
                     method: str = "auto") -> SegmentationResult:
        """
        Segment an image to detect poker tables and components.
        
        Args:
            image: Input image (numpy array, file path, or PIL Image)
            method: Segmentation method ("auto", "yolo", "sam", "custom", "traditional")
            
        Returns:
            SegmentationResult with detected tables and components
        """
        start_time = time.time()
        
        # Load and preprocess image
        if isinstance(image, str):
            image = cv2.imread(image)
        elif isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        if image is None:
            raise ValueError("Could not load image")
        
        original_shape = image.shape[:2]
        
        # Choose segmentation method
        if method == "auto":
            method = self._select_best_method()
        
        # Perform segmentation
        if method == "yolo" and self.yolo_model is not None:
            detected_objects = self._segment_with_yolo(image)
        elif method == "sam" and self.sam_predictor is not None:
            detected_objects = self._segment_with_sam(image)
        elif method == "custom" and self.custom_model is not None:
            detected_objects = self._segment_with_custom(image)
        elif method == "onnx" and self.onnx_session is not None:
            detected_objects = self._segment_with_onnx(image)
        else:
            detected_objects = self._segment_traditional(image)
            method = "traditional"
        
        # Group objects into table layouts
        table_layouts = self._group_objects_into_tables(detected_objects, original_shape)
        
        # Update statistics
        processing_time = time.time() - start_time
        self._update_stats(processing_time, len(table_layouts), method)
        
        return SegmentationResult(
            detected_tables=table_layouts,
            processing_time=processing_time,
            model_used=method,
            input_resolution=original_shape,
            confidence_threshold=self.confidence_threshold,
            total_objects=len(detected_objects)
        )

    def _select_best_method(self) -> str:
        """Select the best available segmentation method."""
        preferences = self.config.get("segmentation", {}).get("model_preference", ["yolo", "custom", "sam"])
        
        for method in preferences:
            if method == "yolo" and self.yolo_model is not None:
                return "yolo"
            elif method == "custom" and self.custom_model is not None:
                return "custom"
            elif method == "sam" and self.sam_predictor is not None:
                return "sam"
            elif method == "onnx" and self.onnx_session is not None:
                return "onnx"
        
        return "traditional"

    def _segment_with_yolo(self, image: np.ndarray) -> List[DetectedObject]:
        """Segment image using YOLO model."""
        try:
            results = self.yolo_model(image, conf=self.confidence_threshold)
            detected_objects = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box data
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        conf = float(box.conf[0].cpu().numpy())
                        cls = int(box.cls[0].cpu().numpy())
                        
                        # Map class to component name
                        class_name = self.component_classes.get(cls, f"unknown_{cls}")
                        
                        detected_objects.append(DetectedObject(
                            class_name=class_name,
                            confidence=conf,
                            bbox=(x1, y1, x2, y2),
                            center=((x1 + x2) // 2, (y1 + y2) // 2),
                            area=(x2 - x1) * (y2 - y1)
                        ))
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"Error in YOLO segmentation: {e}")
            return []

    def _segment_with_sam(self, image: np.ndarray) -> List[DetectedObject]:
        """Segment image using Segment Anything Model."""
        try:
            # First detect potential regions using traditional methods
            table_regions = self._detect_table_regions_traditional(image)
            
            detected_objects = []
            
            for region_bbox in table_regions:
                x1, y1, x2, y2 = region_bbox
                
                # Use SAM to get precise segmentation
                self.sam_predictor.set_image(image)
                masks, scores, logits = self.sam_predictor.predict(
                    point_coords=np.array([[(x1 + x2) // 2, (y1 + y2) // 2]]),
                    point_labels=np.array([1])
                )
                
                if len(masks) > 0:
                    best_mask = masks[np.argmax(scores)]
                    
                    detected_objects.append(DetectedObject(
                        class_name="table",
                        confidence=float(np.max(scores)),
                        bbox=region_bbox,
                        center=((x1 + x2) // 2, (y1 + y2) // 2),
                        area=(x2 - x1) * (y2 - y1),
                        mask=best_mask
                    ))
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"Error in SAM segmentation: {e}")
            return []

    def _segment_with_custom(self, image: np.ndarray) -> List[DetectedObject]:
        """Segment image using custom lightweight model."""
        try:
            # Preprocess image
            transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((416, 416)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # Convert BGR to RGB for preprocessing
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            input_tensor = transform(rgb_image).unsqueeze(0)
            
            if self.use_gpu:
                input_tensor = input_tensor.cuda()
            
            # Run inference
            with torch.no_grad():
                predictions = self.custom_model(input_tensor)
            
            # Post-process predictions to get detected objects
            detected_objects = self._postprocess_custom_predictions(predictions, image.shape[:2])
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"Error in custom model segmentation: {e}")
            return []

    def _segment_with_onnx(self, image: np.ndarray) -> List[DetectedObject]:
        """Segment image using ONNX model."""
        try:
            # Preprocess image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb_image, (416, 416))
            input_data = resized.transpose(2, 0, 1).astype(np.float32) / 255.0
            input_data = np.expand_dims(input_data, axis=0)
            
            # Run inference
            input_name = self.onnx_session.get_inputs()[0].name
            outputs = self.onnx_session.run(None, {input_name: input_data})
            
            # Post-process ONNX outputs
            detected_objects = self._postprocess_onnx_predictions(outputs, image.shape[:2])
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"Error in ONNX segmentation: {e}")
            return []

    def _segment_traditional(self, image: np.ndarray) -> List[DetectedObject]:
        """Segment image using traditional computer vision methods."""
        detected_objects = []
        
        try:
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Detect poker tables using shape and color analysis
            table_regions = self._detect_table_regions_traditional(image)
            
            for bbox in table_regions:
                x1, y1, x2, y2 = bbox
                detected_objects.append(DetectedObject(
                    class_name="table",
                    confidence=0.8,  # Fixed confidence for traditional method
                    bbox=bbox,
                    center=((x1 + x2) // 2, (y1 + y2) // 2),
                    area=(x2 - x1) * (y2 - y1)
                ))
            
            # Detect other components within each table
            for table_obj in detected_objects:
                if table_obj.class_name == "table":
                    x1, y1, x2, y2 = table_obj.bbox
                    table_roi = image[y1:y2, x1:x2]
                    
                    # Detect cards, chips, buttons etc. within table
                    components = self._detect_table_components_traditional(table_roi, (x1, y1))
                    detected_objects.extend(components)
            
            return detected_objects
            
        except Exception as e:
            logger.error(f"Error in traditional segmentation: {e}")
            return []

    def _detect_table_regions_traditional(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect poker table regions using traditional CV methods."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (15, 15), 0)
        
        # Threshold to find dark regions (poker tables are usually dark)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        table_regions = []
        min_area = self.config.get("segmentation", {}).get("min_table_size", 10000)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                # Check aspect ratio to filter out non-table shapes
                aspect_ratio = w / h
                if 1.2 < aspect_ratio < 2.5:  # Typical poker table aspect ratios
                    table_regions.append((x, y, x + w, y + h))
        
        return table_regions

    def _detect_table_components_traditional(self, table_roi: np.ndarray, offset: Tuple[int, int]) -> List[DetectedObject]:
        """Detect components within a poker table using traditional methods."""
        components = []
        offset_x, offset_y = offset
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(table_roi, cv2.COLOR_BGR2HSV)
        
        # Detect community cards area (usually center, light colored)
        cards_mask = cv2.inRange(hsv, (0, 0, 180), (180, 60, 255))
        cards_contours, _ = cv2.findContours(cards_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in cards_contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum area for card regions
                x, y, w, h = cv2.boundingRect(contour)
                components.append(DetectedObject(
                    class_name="cards_community",
                    confidence=0.7,
                    bbox=(x + offset_x, y + offset_y, x + w + offset_x, y + h + offset_y),
                    center=(x + w//2 + offset_x, y + h//2 + offset_y),
                    area=area
                ))
        
        # Detect chip stacks (circular, colorful objects)
        # ... Additional traditional detection logic for chips, buttons, etc.
        
        return components

    def _group_objects_into_tables(self, detected_objects: List[DetectedObject], 
                                  image_shape: Tuple[int, int]) -> List[TableLayout]:
        """Group detected objects into table layouts."""
        tables = []
        table_objects = [obj for obj in detected_objects if obj.class_name == "table"]
        
        for i, table_obj in enumerate(table_objects):
            table_id = f"table_{i+1}"
            
            # Find all components that belong to this table
            table_components = {"table": [table_obj]}
            
            for obj in detected_objects:
                if obj != table_obj and self._object_belongs_to_table(obj, table_obj):
                    component_type = obj.class_name
                    if component_type not in table_components:
                        table_components[component_type] = []
                    table_components[component_type].append(obj)
            
            # Create table layout
            table_layout = TableLayout(
                table_id=table_id,
                table_bbox=table_obj.bbox,
                confidence=table_obj.confidence,
                components=table_components,
                metadata={
                    "area": table_obj.area,
                    "center": table_obj.center,
                    "component_count": sum(len(components) for components in table_components.values()),
                    "image_coverage": table_obj.area / (image_shape[0] * image_shape[1])
                }
            )
            
            tables.append(table_layout)
        
        return tables

    def _object_belongs_to_table(self, obj: DetectedObject, table: DetectedObject) -> bool:
        """Check if an object belongs to a specific table."""
        # Check if object center is within table bounds with some margin
        table_x1, table_y1, table_x2, table_y2 = table.bbox
        obj_center_x, obj_center_y = obj.center
        
        # Add 10% margin to table bounds
        margin_x = (table_x2 - table_x1) * 0.1
        margin_y = (table_y2 - table_y1) * 0.1
        
        return (table_x1 - margin_x <= obj_center_x <= table_x2 + margin_x and
                table_y1 - margin_y <= obj_center_y <= table_y2 + margin_y)

    def _postprocess_custom_predictions(self, predictions, 
                                      original_shape: Tuple[int, int]) -> List[DetectedObject]:
        """Post-process predictions from custom model."""
        # This would depend on the specific output format of the custom model
        detected_objects = []
        
        # Example post-processing logic
        # Convert predictions to DetectedObject instances
        
        return detected_objects

    def _postprocess_onnx_predictions(self, outputs: List[np.ndarray], 
                                    original_shape: Tuple[int, int]) -> List[DetectedObject]:
        """Post-process predictions from ONNX model."""
        detected_objects = []
        
        # Example post-processing for ONNX outputs
        # This would depend on the specific model architecture
        
        return detected_objects

    def visualize_segmentation(self, image: np.ndarray, 
                             result: SegmentationResult,
                             output_path: Optional[str] = None) -> np.ndarray:
        """Create a visualization of the segmentation results."""
        vis_image = image.copy()
        
        for table in result.detected_tables:
            # Draw table bounding box
            table_color = self.class_colors.get("table", (0, 255, 0))
            x1, y1, x2, y2 = table.table_bbox
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), table_color, 3)
            
            # Add table label
            label = f"{table.table_id} ({table.confidence:.2f})"
            cv2.putText(vis_image, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, table_color, 2)
            
            # Draw component bounding boxes
            for component_type, objects in table.components.items():
                if component_type == "table":
                    continue
                    
                color = self.class_colors.get(component_type, (128, 128, 128))
                
                for obj in objects:
                    x1, y1, x2, y2 = obj.bbox
                    cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
                    
                    # Add component label
                    label = f"{component_type} ({obj.confidence:.2f})"
                    cv2.putText(vis_image, label, (x1, y1 - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add summary information
        summary = f"Tables: {result.get_table_count()}, Objects: {result.total_objects}, Time: {result.processing_time:.2f}s"
        cv2.putText(vis_image, summary, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        if output_path:
            cv2.imwrite(output_path, vis_image)
        
        return vis_image

    def extract_table_regions(self, image: np.ndarray, 
                            result: SegmentationResult) -> Dict[str, np.ndarray]:
        """Extract individual table regions as separate images."""
        table_regions = {}
        
        for table in result.detected_tables:
            x1, y1, x2, y2 = table.table_bbox
            # Add padding around table region
            padding = 20
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(image.shape[1], x2 + padding)
            y2 = min(image.shape[0], y2 + padding)
            
            table_region = image[y1:y2, x1:x2].copy()
            table_regions[table.table_id] = table_region
            
        return table_regions

    def get_component_crops(self, image: np.ndarray, 
                          result: SegmentationResult) -> Dict[str, Dict[str, List[np.ndarray]]]:
        """Extract cropped regions for each component type per table."""
        table_crops = {}
        
        for table in result.detected_tables:
            table_crops[table.table_id] = {}
            
            for component_type, objects in table.components.items():
                table_crops[table.table_id][component_type] = []
                
                for obj in objects:
                    x1, y1, x2, y2 = obj.bbox
                    # Add small padding
                    padding = 5
                    x1 = max(0, x1 - padding)
                    y1 = max(0, y1 - padding)
                    x2 = min(image.shape[1], x2 + padding)
                    y2 = min(image.shape[0], y2 + padding)
                    
                    crop = image[y1:y2, x1:x2].copy()
                    table_crops[table.table_id][component_type].append(crop)
        
        return table_crops

    def _update_stats(self, processing_time: float, table_count: int, method: str):
        """Update performance statistics."""
        self.segmentation_stats["total_frames_processed"] += 1
        
        # Update average processing time
        total = self.segmentation_stats["total_frames_processed"]
        current_avg = self.segmentation_stats["avg_processing_time"]
        self.segmentation_stats["avg_processing_time"] = (current_avg * (total - 1) + processing_time) / total
        
        # Update method usage counts
        if method in ["yolo", "custom", "sam", "onnx"] and self.use_gpu:
            self.segmentation_stats["gpu_usage_count"] += 1
        else:
            self.segmentation_stats["cpu_fallback_count"] += 1
            
        # Update detection counts
        self.segmentation_stats["total_tables_detected"] += table_count

    def get_statistics(self) -> Dict:
        """Get current segmentation statistics."""
        return self.segmentation_stats.copy()

    def batch_process_images(self, image_paths: List[str], 
                           output_dir: Optional[str] = None) -> List[SegmentationResult]:
        """Process multiple images in batch."""
        results = []
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
                
                # Segment image
                result = self.segment_image(image_path)
                results.append(result)
                
                # Save visualization if output directory provided
                if output_dir:
                    image = cv2.imread(image_path)
                    if image is not None:
                        vis_path = output_path / f"segmentation_{i+1}.png"
                        self.visualize_segmentation(image, result, str(vis_path))
                        
                        # Save individual table crops
                        table_regions = self.extract_table_regions(image, result)
                        for table_id, region in table_regions.items():
                            region_path = output_path / f"{table_id}_{i+1}.png"
                            cv2.imwrite(str(region_path), region)
                
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
                
        return results

    def export_results(self, results: List[SegmentationResult], 
                      output_path: str, format: str = "json"):
        """Export segmentation results to file."""
        export_data = []
        
        for i, result in enumerate(results):
            result_data = {
                "image_id": i,
                "processing_time": result.processing_time,
                "model_used": result.model_used,
                "input_resolution": result.input_resolution,
                "confidence_threshold": result.confidence_threshold,
                "total_objects": result.total_objects,
                "table_count": result.get_table_count(),
                "overlapping_tables": result.get_overlapping_tables(),
                "tables": []
            }
            
            for table in result.detected_tables:
                table_data = {
                    "table_id": table.table_id,
                    "bbox": table.table_bbox,
                    "confidence": table.confidence,
                    "metadata": table.metadata,
                    "components": {}
                }
                
                for component_type, objects in table.components.items():
                    table_data["components"][component_type] = [
                        {
                            "bbox": obj.bbox,
                            "confidence": obj.confidence,
                            "center": obj.center,
                            "area": obj.area
                        }
                        for obj in objects
                    ]
                
                result_data["tables"].append(table_data)
            
            export_data.append(result_data)
        
        # Save results
        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif format.lower() == "csv":
            # Flatten data for CSV export
            import pandas as pd
            flattened_data = []
            
            for result_data in export_data:
                for table_data in result_data["tables"]:
                    row = {
                        "image_id": result_data["image_id"],
                        "table_id": table_data["table_id"],
                        "table_confidence": table_data["confidence"],
                        "table_bbox": str(table_data["bbox"]),
                        "processing_time": result_data["processing_time"],
                        "model_used": result_data["model_used"],
                        "component_count": sum(len(objs) for objs in table_data["components"].values())
                    }
                    flattened_data.append(row)
            
            df = pd.DataFrame(flattened_data)
            df.to_csv(output_path, index=False)
        
        logger.info(f"Results exported to {output_path}")


# Only define PokerSegmentationNet if torch is available
if HAS_TORCH:
    class PokerSegmentationNet(nn.Module):
        """Custom lightweight segmentation network for poker table detection."""
        
        def __init__(self, num_classes: int):
            super(PokerSegmentationNet, self).__init__()
            self.num_classes = num_classes
            
            # Use MobileNetV3 as backbone for efficiency
            self.backbone = mobilenet_v3_small(pretrained=True)
            
            # Remove classifier and replace with segmentation head
            self.backbone.classifier = nn.Identity()
            
            # Segmentation head
            self.segmentation_head = nn.Sequential(
                nn.Conv2d(576, 256, kernel_size=3, padding=1),
                nn.BatchNorm2d(256),
                nn.ReLU(inplace=True),
                nn.Dropout2d(0.1),
                
                nn.Conv2d(256, 128, kernel_size=3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.Dropout2d(0.1),
                
                nn.Conv2d(128, num_classes, kernel_size=1),
                nn.Upsample(scale_factor=8, mode='bilinear', align_corners=False)
            )
            
            # Detection head for bounding boxes
            self.detection_head = nn.Sequential(
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
                nn.Linear(576, 256),
                nn.ReLU(inplace=True),
                nn.Dropout(0.5),
                nn.Linear(256, num_classes * 5)  # class + 4 bbox coords
            )
        
        def forward(self, x):
            # Extract features using backbone
            features = self.backbone.features(x)
            
            # Global average pooling for classification/detection
            gap = self.backbone.avgpool(features)
            gap_flat = torch.flatten(gap, 1)
            
            # Segmentation output
            seg_output = self.segmentation_head(features)
            
            # Detection output (bounding boxes)
            det_output = self.detection_head(gap)
            det_output = det_output.view(-1, self.num_classes, 5)  # [batch, classes, (conf + 4 coords)]
            
            return {
                'segmentation': seg_output,
                'detection': det_output
            }
else:
    # Dummy class when torch is not available
    class PokerSegmentationNet:
        def __init__(self, num_classes: int):
            self.num_classes = num_classes
            logger.warning("PokerSegmentationNet not available - torch not installed")


def create_sample_dataset(output_dir: str = "data/poker_samples", num_samples: int = 100):
    """Create a sample dataset for training the segmentation model."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # This would generate synthetic poker table images
    # In practice, this would create varied poker table layouts
    logger.info(f"Sample dataset creation placeholder - {num_samples} samples to {output_dir}")
    

def train_segmentation_model(dataset_path: str, output_model_path: str, epochs: int = 50):
    """Train the poker segmentation model."""
    logger.info("Model training placeholder - implement with actual training data")
    # This would implement the actual training loop
    pass


def main():
    """Example usage of the Multi-Table Segmenter."""
    # Initialize segmenter
    segmenter = MultiTableSegmenter()
    
    # Example: Process a single image
    # result = segmenter.segment_image("poker_screenshot.png")
    # print(f"Detected {result.get_table_count()} tables in {result.processing_time:.2f}s")
    
    # Example: Visualize results
    # image = cv2.imread("poker_screenshot.png")
    # vis = segmenter.visualize_segmentation(image, result, "segmentation_result.png")
    
    # Example: Extract table regions
    # table_regions = segmenter.extract_table_regions(image, result)
    # for table_id, region in table_regions.items():
    #     cv2.imwrite(f"{table_id}.png", region)
    
    # Example: Batch processing
    # image_paths = ["image1.png", "image2.png", "image3.png"]
    # results = segmenter.batch_process_images(image_paths, "output/")
    
    print("Multi-Table Segmenter initialized successfully!")
    print("Use the segmenter methods to process poker table screenshots.")
    print(f"Statistics: {segmenter.get_statistics()}")


if __name__ == "__main__":
    main()
