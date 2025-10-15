#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPE-016: Frame Differencing Engine
=====================================

Skip entire frame processing if screen is unchanged (<5% pixel difference).
Expected improvement: 5-10x faster during idle periods (waiting for action).

Module: pokertool.frame_differencing_engine
Version: 1.0.0
Created: 2025-10-15
Author: PokerTool Development Team
License: MIT
"""

__version__ = '1.0.0'

import logging
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FrameDifferenceMetrics:
    """Metrics for frame differencing engine."""
    total_frames: int = 0
    frames_processed: int = 0
    frames_skipped: int = 0
    skip_rate: float = 0.0
    speedup_factor: float = 1.0
    avg_similarity: float = 0.0
    avg_processing_time_ms: float = 0.0
    
    def update(self, processed: bool, similarity: float, processing_time: float):
        """Update metrics after processing a frame."""
        self.total_frames += 1
        
        if processed:
            self.frames_processed += 1
        else:
            self.frames_skipped += 1
        
        # Update skip rate
        if self.total_frames > 0:
            self.skip_rate = self.frames_skipped / self.total_frames
        
        # Update average similarity (running average)
        if self.total_frames == 1:
            self.avg_similarity = similarity
        else:
            self.avg_similarity = (self.avg_similarity * (self.total_frames - 1) + similarity) / self.total_frames
        
        # Update average processing time
        if self.frames_processed == 1:
            self.avg_processing_time_ms = processing_time
        else:
            self.avg_processing_time_ms = (
                self.avg_processing_time_ms * (self.frames_processed - 1) + processing_time
            ) / self.frames_processed
        
        # Calculate speedup
        # Assumes full processing takes 1 unit, similarity check takes 0.05 units
        baseline_work = self.total_frames
        actual_work = self.frames_processed + (self.frames_skipped * 0.05)
        self.speedup_factor = baseline_work / actual_work if actual_work > 0 else 1.0


class FrameDifferencingEngine:
    """
    Skip entire frame processing if screen is unchanged.
    
    Uses fast structural similarity (SSIM) computation between frames
    to detect when the screen is idle.
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize frame differencing engine.
        
        Args:
            similarity_threshold: Threshold for considering frames identical (0-1).
                                 Default 0.95 = skip if >95% similar.
        """
        self.similarity_threshold = similarity_threshold
        self.previous_frame: Optional[np.ndarray] = None
        self.previous_frame_hash: Optional[int] = None
        self.metrics = FrameDifferenceMetrics()
        
        logger.info(f"Frame differencing engine initialized (threshold: {similarity_threshold:.1%})")
    
    def _downsample_frame(self, frame: np.ndarray, target_width: int = 320) -> np.ndarray:
        """
        Downsample frame for fast comparison.
        
        Args:
            frame: Full resolution frame
            target_width: Target width for downsampled frame
            
        Returns:
            Downsampled frame
        """
        try:
            import cv2
            height, width = frame.shape[:2]
            scale = target_width / width
            target_height = int(height * scale)
            return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)
        except ImportError:
            # Fallback without cv2
            from PIL import Image
            pil_img = Image.fromarray(frame)
            height, width = frame.shape[:2]
            scale = target_width / width
            target_height = int(height * scale)
            pil_img = pil_img.resize((target_width, target_height), Image.LANCZOS)
            return np.array(pil_img)
    
    def _compute_ssim_fast(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Compute fast structural similarity between two frames.
        
        This is a simplified SSIM that's much faster than the full algorithm.
        
        Args:
            frame1: First frame (downsampled)
            frame2: Second frame (downsampled)
            
        Returns:
            Similarity score (0-1, where 1 = identical)
        """
        try:
            # Convert to grayscale if needed
            if len(frame1.shape) == 3:
                import cv2
                frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        except ImportError:
            # Fallback: average RGB channels
            if len(frame1.shape) == 3:
                frame1 = frame1.mean(axis=2).astype(np.uint8)
                frame2 = frame2.mean(axis=2).astype(np.uint8)
        
        # Compute means
        mean1 = frame1.mean()
        mean2 = frame2.mean()
        
        # Compute variances
        var1 = frame1.var()
        var2 = frame2.var()
        
        # Compute covariance
        covar = ((frame1 - mean1) * (frame2 - mean2)).mean()
        
        # SSIM formula (simplified)
        c1 = (0.01 * 255) ** 2
        c2 = (0.03 * 255) ** 2
        
        numerator = (2 * mean1 * mean2 + c1) * (2 * covar + c2)
        denominator = (mean1**2 + mean2**2 + c1) * (var1 + var2 + c2)
        
        if denominator == 0:
            return 1.0 if numerator == 0 else 0.0
        
        ssim = numerator / denominator
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, ssim))
    
    def _compute_pixel_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Compute percentage of pixels that differ.
        
        Args:
            frame1: First frame (downsampled)
            frame2: Second frame (downsampled)
            
        Returns:
            Percentage of different pixels (0-1)
        """
        # Absolute difference
        diff = np.abs(frame1.astype(np.int16) - frame2.astype(np.int16))
        
        # Consider pixel different if any channel differs by >10
        threshold = 10
        different = (diff > threshold).any(axis=2) if len(diff.shape) == 3 else (diff > threshold)
        
        # Calculate percentage
        return different.mean()
    
    def should_process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        """
        Check if frame should be processed or skipped.
        
        Args:
            frame: Current frame (full resolution)
            
        Returns:
            Tuple of (should_process, similarity_score)
        """
        start_time = time.time()
        
        # Always process first frame
        if self.previous_frame is None:
            downsampled = self._downsample_frame(frame)
            self.previous_frame = downsampled
            self.metrics.update(processed=True, similarity=0.0, processing_time=0.0)
            return True, 0.0
        
        # Downsample for fast comparison
        downsampled = self._downsample_frame(frame)
        
        # Quick hash check (very fast)
        current_hash = hash(downsampled.tobytes())
        if self.previous_frame_hash is not None and current_hash == self.previous_frame_hash:
            # Identical frames
            processing_time = (time.time() - start_time) * 1000
            self.metrics.update(processed=False, similarity=1.0, processing_time=processing_time)
            logger.debug("Frame skipped (hash match, 100% identical)")
            return False, 1.0
        
        # Compute similarity
        try:
            similarity = self._compute_ssim_fast(downsampled, self.previous_frame)
        except Exception as e:
            logger.debug(f"SSIM computation failed, using pixel difference: {e}")
            # Fallback to pixel difference
            diff_pct = self._compute_pixel_difference(downsampled, self.previous_frame)
            similarity = 1.0 - diff_pct
        
        processing_time = (time.time() - start_time) * 1000
        
        # Check if similar enough to skip
        should_process = similarity < self.similarity_threshold
        
        # Update previous frame if processing
        if should_process:
            self.previous_frame = downsampled
            self.previous_frame_hash = current_hash
        
        self.metrics.update(processed=should_process, similarity=similarity, processing_time=processing_time)
        
        if not should_process:
            logger.debug(f"Frame skipped (similarity: {similarity:.1%} >= {self.similarity_threshold:.1%})")
        else:
            logger.debug(f"Frame processing (similarity: {similarity:.1%} < {self.similarity_threshold:.1%})")
        
        return should_process, similarity
    
    def reset(self):
        """Reset frame differencing state."""
        self.previous_frame = None
        self.previous_frame_hash = None
        self.metrics = FrameDifferenceMetrics()
        logger.info("Frame differencing engine reset")
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            'total_frames': self.metrics.total_frames,
            'frames_processed': self.metrics.frames_processed,
            'frames_skipped': self.metrics.frames_skipped,
            'skip_rate': f"{self.metrics.skip_rate:.1%}",
            'speedup_factor': f"{self.metrics.speedup_factor:.2f}x",
            'avg_similarity': f"{self.metrics.avg_similarity:.1%}",
            'avg_processing_time_ms': f"{self.metrics.avg_processing_time_ms:.2f}ms",
            'similarity_threshold': f"{self.similarity_threshold:.1%}"
        }


# Global singleton
_frame_diff_engine: Optional[FrameDifferencingEngine] = None


def get_frame_diff_engine(similarity_threshold: float = 0.95) -> FrameDifferencingEngine:
    """Get global frame differencing engine instance."""
    global _frame_diff_engine
    if _frame_diff_engine is None:
        _frame_diff_engine = FrameDifferencingEngine(similarity_threshold=similarity_threshold)
    return _frame_diff_engine


def reset_frame_diff_engine():
    """Reset global frame differencing engine."""
    global _frame_diff_engine
    if _frame_diff_engine:
        _frame_diff_engine.reset()


if __name__ == '__main__':
    # Test frame differencing
    print("Frame Differencing Engine Test")
    
    engine = FrameDifferencingEngine(similarity_threshold=0.95)
    
    # Create test frames
    frame1 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    frame2 = frame1.copy()  # Identical
    frame3 = frame1.copy()
    frame3[100:200, 100:200] = 255  # Small change
    frame4 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)  # Completely different
    
    # Test frame 1
    should_process1, sim1 = engine.should_process_frame(frame1)
    print(f"Frame 1: process={should_process1}, similarity={sim1:.1%} (first frame)")
    
    # Test frame 2 (identical)
    should_process2, sim2 = engine.should_process_frame(frame2)
    print(f"Frame 2: process={should_process2}, similarity={sim2:.1%} (identical)")
    
    # Test frame 3 (small change)
    should_process3, sim3 = engine.should_process_frame(frame3)
    print(f"Frame 3: process={should_process3}, similarity={sim3:.1%} (small change)")
    
    # Test frame 4 (completely different)
    should_process4, sim4 = engine.should_process_frame(frame4)
    print(f"Frame 4: process={should_process4}, similarity={sim4:.1%} (different)")
    
    # Show metrics
    metrics = engine.get_metrics()
    print(f"\nMetrics:")
    print(f"  Total frames: {metrics['total_frames']}")
    print(f"  Skip rate: {metrics['skip_rate']}")
    print(f"  Speedup: {metrics['speedup_factor']}")
    print(f"  Avg similarity: {metrics['avg_similarity']}")
