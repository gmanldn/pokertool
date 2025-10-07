#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Multi-Table Layout Segmenter
=====================================

Reliably isolates individual poker tables, boards, and HUD panels when multiple 
instances are visible or overlapping.

This module trains a lightweight segmentation model that produces bounding boxes 
for tables, cards, chip stacks, and HUD widgets, then feeds the cropped regions 
into the downstream OCR and classifier stages.

Module: pokertool.modules.multi_table_segmenter
Version: 1.0.0
Last Modified: 2025-01-07
Author: PokerTool Development Team
License: MIT

Key Features:
- YOLOv8-inspired lightweight segmentation model
- Real-time bounding box detection for poker elements
- GPU inference with CPU fallback
- Multi-table isolation and cropping
- HUD widget detection and separation
- Integration with existing OCR pipeline
"""

import os
import logging
import time
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Check for required dependencies
try:
    import cv2
    from PIL import Image
    OPENCV_AVAILABLE = True
except ImportError as e:
    logging.warning(f"OpenCV not available: {e}")
    OPENCV_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy classes for type hints
    class nn:
        class Module:
            pass
    torch = None

# Alternative ML frameworks when torch not available
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================================
# Data Models and Configuration
# ============================================================================

class ElementType(Enum):
    """Types of poker table elements that can be detected."""
    TABLE = "table"
    CARDS = "cards"
    CHIPS = "chips"
    BUTTONS = "buttons"
    TEXT = "text"
    HUD = "hud"
    LOGO = "logo"
    TIMER = "timer"

@dataclass
class BoundingBox:
    """Bounding box for detected element."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    element_type: ElementType
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def x2(self) -> int:
        return self.x + self.width
    
    @property
    def y2(self) -> int:
        return self.y + self.height
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    def iou(self, other: 'BoundingBox') -> float:
        """Calculate Intersection over Union with another bounding box."""
        # Calculate intersection
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x2, other.x2)
        y2 = min(self.y2, other.y2)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        union = self.area + other.area - intersection
        
        return intersection / max(union, 1)

@dataclass
class SegmentationResult:
    """Result of multi-table segmentation."""
    tables: List[BoundingBox] = field(default_factory=list)
    cards: List[BoundingBox] = field(default_factory=list)
    chips: List[BoundingBox] = field(default_factory=list)
    buttons: List[BoundingBox] = field(default_factory=list)
    text_regions: List[BoundingBox] = field(default_factory=list)
    hud_widgets: List[BoundingBox] = field(default_factory=list)
    processing_time: float = 0.0
    model_used: str = ""
    
    def get_table_count(self) -> int:
        """Get number of detected tables."""
        return len(self.tables)
    
    def get_element_count(self, element_type: ElementType) -> int:
        """Get count of specific element type."""
        mapping = {
            ElementType.TABLE: self.tables,
            ElementType.CARDS: self.cards,
            ElementType.CHIPS: self.chips,
            ElementType.BUTTONS: self.buttons,
            ElementType.TEXT: self.text_regions,
            ElementType.HUD: self.hud_widgets
        }
        return len(mapping.get(element_type, []))

# ============================================================================
# Lightweight Segmentation Model (PyTorch)
# ============================================================================

class LightweightSegmentationModel(nn.Module):
    """
    Lightweight segmentation model inspired by YOLOv8n optimized for poker table detection.
    
    Architecture:
    - Efficient backbone with depthwise separable convolutions
    - Feature Pyramid Network (FPN) for multi-scale detection
    - Anchor-free detection head
    - Optimized for 1080p inputs with real-time inference
    """
    
    def __init__(self, num_classes: int = 8, input_size: Tuple[int, int] = (640, 640)):
        super().__init__()
        self.num_classes = num_classes
        self.input_size = input_size
        
        # Efficient backbone
        self.backbone = self._create_backbone()
        
        # Feature Pyramid Network
        self.fpn = self._create_fpn()
        
        # Detection head
        self.detection_head = self._create_detection_head()
        
        # Initialize weights
        self._initialize_weights()
    
    def _create_backbone(self) -> nn.Module:
        """Create efficient backbone network."""
        return nn.Sequential(
            # Initial conv
            nn.Conv2d(3, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            
            # Stage 1: 32 -> 64
            self._make_stage(32, 64, num_blocks=2, stride=2),
            
            # Stage 2: 64 -> 128
            self._make_stage(64, 128, num_blocks=3, stride=2),
            
            # Stage 3: 128 -> 256
            self._make_stage(128, 256, num_blocks=3, stride=2),
            
            # Stage 4: 256 -> 512
            self._make_stage(256, 512, num_blocks=2, stride=2),
        )
    
    def _make_stage(self, in_channels: int, out_channels: int, num_blocks: int, stride: int) -> nn.Module:
        """Create a stage with multiple depthwise separable blocks."""
        layers = []
        
        # First block with stride
        layers.append(self._depthwise_separable_block(in_channels, out_channels, stride))
        
        # Remaining blocks
        for _ in range(num_blocks - 1):
            layers.append(self._depthwise_separable_block(out_channels, out_channels, 1))
        
        return nn.Sequential(*layers)
    
    def _depthwise_separable_block(self, in_channels: int, out_channels: int, stride: int) -> nn.Module:
        """Create depthwise separable convolution block."""
        return nn.Sequential(
            # Depthwise conv
            nn.Conv2d(in_channels, in_channels, 3, stride=stride, padding=1, 
                     groups=in_channels, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True),
            
            # Pointwise conv
            nn.Conv2d(in_channels, out_channels, 1, stride=1, padding=0, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def _create_fpn(self) -> nn.Module:
        """Create Feature Pyramid Network for multi-scale detection."""
        return nn.ModuleDict({
            'lateral_512': nn.Conv2d(512, 256, 1),
            'lateral_256': nn.Conv2d(256, 256, 1),
            'lateral_128': nn.Conv2d(128, 256, 1),
            
            'smooth_p3': nn.Conv2d(256, 256, 3, padding=1),
            'smooth_p4': nn.Conv2d(256, 256, 3, padding=1),
            'smooth_p5': nn.Conv2d(256, 256, 3, padding=1),
        })
    
    def _create_detection_head(self) -> nn.Module:
        """Create detection head for bounding box prediction."""
        return nn.ModuleDict({
            'cls_head': nn.Sequential(
                nn.Conv2d(256, 256, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(256, self.num_classes, 1)
            ),
            'bbox_head': nn.Sequential(
                nn.Conv2d(256, 256, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(256, 4, 1)  # x, y, w, h
            ),
            'obj_head': nn.Sequential(
                nn.Conv2d(256, 256, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(256, 1, 1)  # objectness
            )
        })
    
    def _initialize_weights(self) -> None:
        """Initialize model weights."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Forward pass through the model."""
        # Extract features through backbone
        features = []
        for i, layer in enumerate(self.backbone):
            x = layer(x)
            if i in [3, 6, 9, 12]:  # Collect features at different scales
                features.append(x)
        
        # FPN processing
        p5 = self.fpn['lateral_512'](features[-1])
        p4 = self.fpn['lateral_256'](features[-2]) + F.interpolate(p5, scale_factor=2)
        p3 = self.fpn['lateral_128'](features[-3]) + F.interpolate(p4, scale_factor=2)
        
        p5 = self.fpn['smooth_p5'](p5)
        p4 = self.fpn['smooth_p4'](p4)
        p3 = self.fpn['smooth_p3'](p3)
        
        # Detection head
        outputs = {}
        for level_name, features in [('p3', p3), ('p4', p4), ('p5', p5)]:
            outputs[f'cls_{level_name}'] = self.detection_head['cls_head'](features)
            outputs[f'bbox_{level_name}'] = self.detection_head['bbox_head'](features)
            outputs[f'obj_{level_name}'] = self.detection_head['obj_head'](features)
        
        return outputs

# ============================================================================
# Multi-Table Layout Segmenter
# ============================================================================

class MultiTableSegmenter:
    """
    Advanced multi-table layout segmentation system.
    
    This class uses machine learning models to detect and isolate individual poker 
    tables, cards, chips, and HUD elements from complex multi-table screenshots.
    """
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True, 
                 confidence_threshold: float = 0.5):
        """
        Initialize the multi-table segmenter.
        
        Args:
            model_path: Path to trained model file. If None, uses default model.
            use_gpu: Whether to use GPU acceleration if available
            confidence_threshold: Minimum confidence for detections
        """
        self.confidence_threshold = confidence_threshold
        self.use_gpu = use_gpu and torch.cuda.is_available() if TORCH_AVAILABLE else False
        
        # Model and preprocessing
        self.model = None
        self.device = None
        self.transform = None
        self.model_type = None
        
        # Fallback traditional detector
        self.traditional_detector = TraditionalMultiTableDetector()
        
        # Detection statistics
        self.detection_count = 0
        self.total_processing_time = 0.0
        
        # Initialize model
        self._initialize_model(model_path)
        
        logger.info(f"Multi-table segmenter initialized (GPU: {self.use_gpu}, Model: {self.model_type})")
    
    def _initialize_model(self, model_path: Optional[str]) -> None:
        """Initialize the segmentation model with fallback options."""
        
        # Try PyTorch model first
        if TORCH_AVAILABLE and self._try_pytorch_model(model_path):
            return
        
        # Try ONNX runtime as fallback
        if ONNX_AVAILABLE and self._try_onnx_model(model_path):
            return
        
        # Try TensorFlow as fallback
        if TF_AVAILABLE and self._try_tensorflow_model(model_path):
            return
        
        # Fall back to traditional computer vision methods
        logger.info("Using traditional computer vision methods for segmentation")
        self.model_type = "traditional"
    
    def _try_pytorch_model(self, model_path: Optional[str]) -> bool:
        """Try to initialize PyTorch model."""
        try:
            self.device = torch.device('cuda' if self.use_gpu else 'cpu')
            
            # Create model
            self.model = LightweightSegmentationModel(num_classes=8)
            
            # Load weights if available
            if model_path and Path(model_path).exists():
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                logger.info(f"Loaded trained model from {model_path}")
            else:
                logger.info("Using untrained model (will use traditional fallback for now)")
            
            self.model.to(self.device)
            self.model.eval()
            
            # Setup preprocessing
            self.transform = transforms.Compose([
                transforms.Resize((640, 640)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            self.model_type = "pytorch"
            return True
            
        except Exception as e:
            logger.warning(f"PyTorch model initialization failed: {e}")
            return False
    
    def _try_onnx_model(self, model_path: Optional[str]) -> bool:
        """Try to initialize ONNX model."""
        try:
            # Look for ONNX model file
            onnx_path = model_path or "models/segmentation/multi_table_segmenter.onnx"
            
            if not Path(onnx_path).exists():
                return False
            
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.use_gpu else ['CPUExecutionProvider']
            self.model = ort.InferenceSession(onnx_path, providers=providers)
            
            self.model_type = "onnx"
            logger.info(f"Loaded ONNX model from {onnx_path}")
            return True
            
        except Exception as e:
            logger.warning(f"ONNX model initialization failed: {e}")
            return False
    
    def _try_tensorflow_model(self, model_path: Optional[str]) -> bool:
        """Try to initialize TensorFlow model."""
        try:
            tf_path = model_path or "models/segmentation/multi_table_segmenter.h5"
            
            if not Path(tf_path).exists():
                return False
            
            self.model = tf.keras.models.load_model(tf_path)
            self.model_type = "tensorflow"
            logger.info(f"Loaded TensorFlow model from {tf_path}")
            return True
            
        except Exception as e:
            logger.warning(f"TensorFlow model initialization failed: {e}")
            return False
    
    def segment_image(self, image: np.ndarray, method: str = "auto") -> SegmentationResult:
        """
        Segment image to detect poker table elements.
        
        Args:
            image: Input image in BGR format
            method: Segmentation method ('auto', 'ml', 'traditional')
            
        Returns:
            SegmentationResult with detected elements
        """
        start_time = time.time()
        self.detection_count += 1
        
        if not OPENCV_AVAILABLE or image is None or image.size == 0:
            return SegmentationResult(model_used="unavailable")
        
        try:
            # Choose segmentation method
            if method == "auto":
                if self.model_type in ["pytorch", "onnx", "tensorflow"]:
                    method = "ml"
                else:
                    method = "traditional"
            
            # Perform segmentation
            if method == "ml" and self.model is not None:
                result = self._segment_with_ml(image)
            else:
                result = self._segment_traditional(image)
            
            # Post-processing
            result = self._post_process_detections(result, image.shape[:2])
            
            processing_time = (time.time() - start_time) * 1000
            result.processing_time = processing_time
            self.total_processing_time += processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            return SegmentationResult(
                processing_time=(time.time() - start_time) * 1000,
                model_used="error"
            )
    
    def _segment_with_ml(self, image: np.ndarray) -> SegmentationResult:
        """Segment image using machine learning model."""
        if self.model_type == "pytorch":
            return self._segment_pytorch(image)
        elif self.model_type == "onnx":
            return self._segment_onnx(image)
        elif self.model_type == "tensorflow":
            return self._segment_tensorflow(image)
        else:
            return self._segment_traditional(image)
    
    def _segment_pytorch(self, image: np.ndarray) -> SegmentationResult:
        """Segment image using PyTorch model."""
        try:
            # Preprocess
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.model(input_tensor)
            
            # Post-process outputs to bounding boxes
            detections = self._decode_pytorch_outputs(outputs, image.shape[:2])
            
            return SegmentationResult(
                tables=detections.get(ElementType.TABLE, []),
                cards=detections.get(ElementType.CARDS, []),
                chips=detections.get(ElementType.CHIPS, []),
                buttons=detections.get(ElementType.BUTTONS, []),
                text_regions=detections.get(ElementType.TEXT, []),
                hud_widgets=detections.get(ElementType.HUD, []),
                model_used="pytorch"
            )
            
        except Exception as e:
            logger.warning(f"PyTorch segmentation failed: {e}")
            return self._segment_traditional(image)
    
    def _segment_onnx(self, image: np.ndarray) -> SegmentationResult:
        """Segment image using ONNX model."""
        try:
            # Preprocess for ONNX
            resized = cv2.resize(image, (640, 640))
            normalized = resized.astype(np.float32) / 255.0
            input_tensor = np.transpose(normalized, (2, 0, 1))[np.newaxis, ...]
            
            # Inference
            outputs = self.model.run(None, {'input': input_tensor})
            
            # Process outputs
            detections = self._decode_onnx_outputs(outputs, image.shape[:2])
            
            return SegmentationResult(
                tables=detections.get(ElementType.TABLE, []),
                cards=detections.get(ElementType.CARDS, []),
                chips=detections.get(ElementType.CHIPS, []),
                buttons=detections.get(ElementType.BUTTONS, []),
                text_regions=detections.get(ElementType.TEXT, []),
                hud_widgets=detections.get(ElementType.HUD, []),
                model_used="onnx"
            )
            
        except Exception as e:
            logger.warning(f"ONNX segmentation failed: {e}")
            return self._segment_traditional(image)
    
    def _segment_tensorflow(self, image: np.ndarray) -> SegmentationResult:
        """Segment image using TensorFlow model."""
        try:
            # Preprocess for TensorFlow
            resized = cv2.resize(image, (640, 640))
            normalized = resized.astype(np.float32) / 255.0
            input_tensor = np.expand_dims(normalized, axis=0)
            
            # Inference
            outputs = self.model.predict(input_tensor, verbose=0)
            
            # Process outputs
            detections = self._decode_tensorflow_outputs(outputs, image.shape[:2])
            
            return SegmentationResult(
                tables=detections.get(ElementType.TABLE, []),
                cards=detections.get(ElementType.CARDS, []),
                chips=detections.get(ElementType.CHIPS, []),
                buttons=detections.get(ElementType.BUTTONS, []),
                text_regions=detections.get(ElementType.TEXT, []),
                hud_widgets=detections.get(ElementType.HUD, []),
                model_used="tensorflow"
            )
            
        except Exception as e:
            logger.warning(f"TensorFlow segmentation failed: {e}")
            return self._segment_traditional(image)
    
    def _segment_traditional(self, image: np.ndarray) -> SegmentationResult:
        """Segment image using traditional computer vision methods."""
        return self.traditional_detector.segment(image)
    
    def _decode_pytorch_outputs(self, outputs: Dict[str, torch.Tensor], 
                              original_shape: Tuple[int, int]) -> Dict[ElementType, List[BoundingBox]]:
        """Decode PyTorch model outputs to bounding boxes."""
        detections = {element_type: [] for element_type in ElementType}
        
        try:
            # Process each scale level
            for level in ['p3', 'p4', 'p5']:
                cls_pred = outputs[f'cls_{level}'].squeeze()
                bbox_pred = outputs[f'bbox_{level}'].squeeze()
                obj_pred = outputs[f'obj_{level}'].squeeze()
                
                # Apply confidence threshold
                obj_scores = torch.sigmoid(obj_pred)
                valid_indices = obj_scores > self.confidence_threshold
                
                if valid_indices.any():
                    # Get class predictions
                    cls_scores = torch.sigmoid(cls_pred[valid_indices])
                    bbox_coords = bbox_pred[valid_indices]
                    
                    # Convert to bounding boxes
                    for i in range(cls_scores.shape[0]):
                        class_id = torch.argmax(cls_scores[i]).item()
                        confidence = obj_scores[valid_indices][i].item()
                        
                        # Convert bbox coordinates to original image space
                        x, y, w, h = bbox_coords[i].cpu().numpy()
                        
                        # Scale to original image dimensions
                        scale_x = original_shape[1] / 640
                        scale_y = original_shape[0] / 640
                        
                        bbox = BoundingBox(
                            x=int(x * scale_x),
                            y=int(y * scale_y), 
                            width=int(w * scale_x),
                            height=int(h * scale_y),
                            confidence=confidence,
                            element_type=list(ElementType)[class_id]
                        )
                        
                        detections[bbox.element_type].append(bbox)
        
        except Exception as e:
            logger.warning(f"PyTorch output decoding failed: {e}")
        
        return detections
    
    def _decode_onnx_outputs(self, outputs: List[np.ndarray], 
                           original_shape: Tuple[int, int]) -> Dict[ElementType, List[BoundingBox]]:
        """Decode ONNX model outputs to bounding boxes."""
        detections = {element_type: [] for element_type in ElementType}
        
        try:
            # Process ONNX outputs (implementation depends on specific model format)
            # This is a placeholder implementation
            if outputs and len(outputs) > 0:
                predictions = outputs[0]
                # Decode predictions to bounding boxes
                # (Implementation would depend on specific ONNX model output format)
                pass
        
        except Exception as e:
            logger.warning(f"ONNX output decoding failed: {e}")
        
        return detections
    
    def _decode_tensorflow_outputs(self, outputs: np.ndarray, 
                                 original_shape: Tuple[int, int]) -> Dict[ElementType, List[BoundingBox]]:
        """Decode TensorFlow model outputs to bounding boxes."""
        detections = {element_type: [] for element_type in ElementType}
        
        try:
            # Process TensorFlow outputs (implementation depends on specific model format)
            # This is a placeholder implementation
            if outputs is not None and outputs.size > 0:
                # Decode predictions to bounding boxes
                # (Implementation would depend on specific TensorFlow model output format)
                pass
        
        except Exception as e:
            logger.warning(f"TensorFlow output decoding failed: {e}")
        
        return detections
    
    def _post_process_detections(self, result: SegmentationResult, 
                               image_shape: Tuple[int, int]) -> SegmentationResult:
        """Post-process detections with NMS and filtering."""
        try:
            # Apply Non-Maximum Suppression to each element type
            for element_type in ElementType:
                detections = getattr(result, element_type.value, [])
                if not detections:
                    continue
                
                # Apply NMS
                filtered_detections = self._apply_nms(detections, iou_threshold=0.5)
                
                # Update result
                setattr(result, element_type.value, filtered_detections)
        
        except Exception as e:
            logger.warning(f"Post-processing failed: {e}")
        
        return result
    
    def _apply_nms(self, detections: List[BoundingBox], iou_threshold: float = 0.5) -> List[BoundingBox]:
        """Apply Non-Maximum Suppression to remove duplicate detections."""
        if not detections:
            return []
        
        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply NMS
        keep = []
        while detections:
            # Keep highest confidence detection
            best = detections.pop(0)
            keep.append(best)
            
            # Remove overlapping detections
            remaining = []
            for detection in detections:
                if best.iou(detection) < iou_threshold:
                    remaining.append(detection)
            
            detections = remaining
        
        return keep
    
    def extract_table_regions(self, image: np.ndarray, 
                            result: SegmentationResult) -> List[Tuple[np.ndarray, BoundingBox]]:
        """
        Extract individual table regions from segmented image.
        
        Args:
            image: Original image
            result: Segmentation result with bounding boxes
            
        Returns:
            List of (table_image, bounding_box) pairs
        """
        table_regions = []
        
        try:
            for table_bbox in result.tables:
                # Extract table region with padding
                padding = 20
                x1 = max(0, table_bbox.x - padding)
                y1 = max(0, table_bbox.y - padding)
                x2 = min(image.shape[1], table_bbox.x2 + padding)
                y2 = min(image.shape[0], table_bbox.y2 + padding)
                
                table_region = image[y1:y2, x1:x2]
                
                # Adjust bounding box coordinates for extracted region
                adjusted_bbox = BoundingBox(
                    x=x1,
                    y=y1,
                    width=x2 - x1,
                    height=y2 - y1,
                    confidence=table_bbox.confidence,
                    element_type=ElementType.TABLE,
                    metadata={
                        'original_bbox': table_bbox,
                        'extracted_region': True
                    }
                )
                
                table_regions.append((table_region, adjusted_bbox))
        
        except Exception as e:
            logger.error(f"Table region extraction failed: {e}")
        
        return table_regions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get segmentation statistics."""
        avg_processing_time = (
            self.total_processing_time / max(1, self.detection_count)
        )
        
        return {
            'total_segmentations': self.detection_count,
            'avg_processing_time_ms': avg_processing_time,
            'model_type': self.model_type,
            'gpu
