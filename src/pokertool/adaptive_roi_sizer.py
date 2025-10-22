"""Adaptive ROI Sizing Based on Detection Confidence"""
from typing import Tuple
from dataclasses import dataclass

@dataclass
class ROISize:
    x: int
    y: int
    width: int
    height: int
    
    def expand(self, factor: float) -> 'ROISize':
        """Expand ROI by factor."""
        new_w = int(self.width * factor)
        new_h = int(self.height * factor)
        offset_x = (new_w - self.width) // 2
        offset_y = (new_h - self.height) // 2
        return ROISize(
            self.x - offset_x,
            self.y - offset_y,
            new_w,
            new_h
        )

class AdaptiveROISizer:
    """Adjust ROI sizes based on detection confidence."""
    
    def __init__(self):
        self.base_expansion = 1.2  # 20% larger
        self.max_expansion = 2.0   # 100% larger
    
    def adjust_roi(self, roi: ROISize, confidence: float) -> ROISize:
        """
        Adjust ROI based on confidence.
        Low confidence = larger ROI (more context)
        High confidence = keep base size
        """
        if confidence >= 0.9:
            return roi  # High confidence, no expansion
        elif confidence >= 0.7:
            return roi.expand(1.1)  # Slight expansion
        else:
            return roi.expand(1.3)  # Low confidence, expand more
