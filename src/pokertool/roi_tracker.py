"""
Region-of-Interest (ROI) Tracking System for Poker Screen Scraper
==================================================================

Tracks which screen regions change between frames and only processes those regions.
Expected improvement: 3-4x faster when table is stable (most of the time).

Key Features:
- Standard ROI grid (pot, board, 9 seats, action buttons)
- Fast region hashing (perceptual hash per ROI)
- Difference detector with configurable sensitivity
- Integration with scraper to skip unchanged regions
- Metrics tracking (regions processed, skip rate)
"""

import logging
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# Check for required dependencies
try:
    import cv2
    ROI_DEPENDENCIES_AVAILABLE = True
except ImportError:
    logger.warning("ROI tracker dependencies not available (requires opencv-python)")
    ROI_DEPENDENCIES_AVAILABLE = False
    cv2 = None


class ROIType(Enum):
    """Types of regions of interest on poker table."""
    POT = "pot"
    BOARD = "board"
    HERO_CARDS = "hero_cards"
    SEAT_1 = "seat_1"
    SEAT_2 = "seat_2"
    SEAT_3 = "seat_3"
    SEAT_4 = "seat_4"
    SEAT_5 = "seat_5"
    SEAT_6 = "seat_6"
    SEAT_7 = "seat_7"
    SEAT_8 = "seat_8"
    SEAT_9 = "seat_9"
    ACTION_BUTTONS = "action_buttons"
    DEALER_BUTTON = "dealer_button"
    BLINDS_INFO = "blinds_info"


@dataclass
class ROIDefinition:
    """Definition of a region of interest."""
    roi_type: ROIType
    x_ratio: float  # X coordinate as ratio of image width (0.0-1.0)
    y_ratio: float  # Y coordinate as ratio of image height (0.0-1.0)
    width_ratio: float  # Width as ratio of image width
    height_ratio: float  # Height as ratio of image height
    priority: int = 1  # Higher priority regions checked first (1=highest, 3=lowest)
    sensitivity: float = 0.05  # Change threshold (0.0-1.0, lower=more sensitive)


@dataclass
class ROIState:
    """State of a tracked ROI."""
    roi_def: ROIDefinition
    last_hash: str = ""
    last_update_time: float = 0.0
    change_count: int = 0
    check_count: int = 0
    skip_count: int = 0
    last_image: Optional[np.ndarray] = None


@dataclass
class ROIChangeDetection:
    """Result of ROI change detection."""
    changed_rois: List[ROIType] = field(default_factory=list)
    unchanged_rois: List[ROIType] = field(default_factory=list)
    total_rois: int = 0
    detection_time_ms: float = 0.0
    skip_percentage: float = 0.0


class ROITracker:
    """
    Region-of-Interest tracker for efficient poker table scraping.
    
    Maintains a grid of ROIs and tracks which regions change between frames.
    Only processes changed regions to achieve 3-4x speedup.
    """
    
    def __init__(self, enable_tracking: bool = True):
        """
        Initialize ROI tracker.
        
        Args:
            enable_tracking: Enable ROI tracking (disable for debugging)
        """
        if not ROI_DEPENDENCIES_AVAILABLE:
            logger.warning("ROI tracker disabled: dependencies not available")
            enable_tracking = False
        
        self.enable_tracking = enable_tracking
        self.roi_states: Dict[ROIType, ROIState] = {}
        
        # Define standard ROI grid for poker table
        self._define_standard_rois()
        
        # Performance metrics
        self.total_checks = 0
        self.total_changes = 0
        self.total_skips = 0
        self.total_processing_time_ms = 0.0
        
        # Configuration
        self.global_sensitivity = 0.05  # Default sensitivity threshold
        self.hash_method = 'perceptual'  # 'perceptual' or 'md5'
        self.enable_adaptive_sensitivity = True
        
        logger.info(f"✓ ROI Tracker initialized (tracking: {enable_tracking})")
    
    def _define_standard_rois(self):
        """Define standard ROI grid for 9-seat poker table."""
        # Standard ROI definitions based on typical poker table layout
        roi_definitions = [
            # High priority regions (checked first, change frequently)
            ROIDefinition(ROIType.POT, 0.45, 0.35, 0.20, 0.15, priority=1, sensitivity=0.03),
            ROIDefinition(ROIType.BOARD, 0.35, 0.40, 0.30, 0.20, priority=1, sensitivity=0.05),
            ROIDefinition(ROIType.HERO_CARDS, 0.45, 0.75, 0.15, 0.12, priority=1, sensitivity=0.05),
            ROIDefinition(ROIType.ACTION_BUTTONS, 0.40, 0.88, 0.25, 0.10, priority=1, sensitivity=0.08),
            
            # Medium priority regions (player seats - change moderately)
            ROIDefinition(ROIType.SEAT_1, 0.45, 0.82, 0.22, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_2, 0.20, 0.79, 0.20, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_3, 0.05, 0.62, 0.18, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_4, 0.05, 0.35, 0.18, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_5, 0.20, 0.15, 0.20, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_6, 0.45, 0.12, 0.22, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_7, 0.70, 0.15, 0.20, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_8, 0.88, 0.35, 0.18, 0.15, priority=2, sensitivity=0.07),
            ROIDefinition(ROIType.SEAT_9, 0.88, 0.62, 0.18, 0.15, priority=2, sensitivity=0.07),
            
            # Low priority regions (change rarely)
            ROIDefinition(ROIType.DEALER_BUTTON, 0.40, 0.50, 0.20, 0.10, priority=3, sensitivity=0.10),
            ROIDefinition(ROIType.BLINDS_INFO, 0.02, 0.05, 0.20, 0.10, priority=3, sensitivity=0.15),
        ]
        
        # Initialize ROI states
        for roi_def in roi_definitions:
            self.roi_states[roi_def.roi_type] = ROIState(roi_def=roi_def)
        
        logger.info(f"Defined {len(roi_definitions)} standard ROIs")
    
    def detect_changes(self, image: np.ndarray, 
                      priority_filter: Optional[int] = None) -> ROIChangeDetection:
        """
        Detect which ROIs have changed since last frame.
        
        Args:
            image: Current frame (BGR format)
            priority_filter: Only check ROIs with this priority or higher (1=highest)
        
        Returns:
            ROIChangeDetection with lists of changed/unchanged ROIs
        """
        if not self.enable_tracking or image is None or image.size == 0:
            # Return all ROIs as changed if tracking disabled
            all_rois = list(self.roi_states.keys())
            return ROIChangeDetection(
                changed_rois=all_rois,
                unchanged_rois=[],
                total_rois=len(all_rois),
                skip_percentage=0.0
            )
        
        start_time = time.time()
        changed_rois: List[ROIType] = []
        unchanged_rois: List[ROIType] = []
        
        h, w = image.shape[:2]
        
        # Sort ROIs by priority (check high priority first)
        sorted_rois = sorted(
            self.roi_states.items(),
            key=lambda x: x[1].roi_def.priority
        )
        
        for roi_type, roi_state in sorted_rois:
            # Apply priority filter if specified
            if priority_filter is not None and roi_state.roi_def.priority > priority_filter:
                continue
            
            self.total_checks += 1
            roi_state.check_count += 1
            
            # Extract ROI region
            roi_def = roi_state.roi_def
            x = int(w * roi_def.x_ratio)
            y = int(h * roi_def.y_ratio)
            roi_w = int(w * roi_def.width_ratio)
            roi_h = int(h * roi_def.height_ratio)
            
            # Bounds check
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            roi_w = min(roi_w, w - x)
            roi_h = min(roi_h, h - y)
            
            if roi_w <= 0 or roi_h <= 0:
                continue
            
            roi_region = image[y:y+roi_h, x:x+roi_w]
            
            if roi_region.size == 0:
                continue
            
            # Compute hash for this ROI
            current_hash = self._compute_roi_hash(roi_region, roi_def.roi_type)
            
            # Check if changed
            if roi_state.last_hash == "":
                # First time seeing this ROI
                changed = True
            else:
                # Compare with previous hash
                changed = self._is_roi_changed(
                    current_hash,
                    roi_state.last_hash,
                    roi_region,
                    roi_state.last_image,
                    roi_def.sensitivity
                )
            
            # Update state
            if changed:
                changed_rois.append(roi_type)
                roi_state.change_count += 1
                self.total_changes += 1
                roi_state.last_hash = current_hash
                roi_state.last_update_time = time.time()
                roi_state.last_image = roi_region.copy()
            else:
                unchanged_rois.append(roi_type)
                roi_state.skip_count += 1
                self.total_skips += 1
        
        detection_time_ms = (time.time() - start_time) * 1000
        self.total_processing_time_ms += detection_time_ms
        
        total_checked = len(changed_rois) + len(unchanged_rois)
        skip_percentage = (len(unchanged_rois) / total_checked * 100) if total_checked > 0 else 0.0
        
        result = ROIChangeDetection(
            changed_rois=changed_rois,
            unchanged_rois=unchanged_rois,
            total_rois=total_checked,
            detection_time_ms=detection_time_ms,
            skip_percentage=skip_percentage
        )
        
        if len(changed_rois) > 0:
            logger.debug(
                f"[ROI] Changed: {len(changed_rois)}/{total_checked} "
                f"({skip_percentage:.1f}% skip rate) in {detection_time_ms:.1f}ms"
            )
        
        return result
    
    def _compute_roi_hash(self, roi_region: np.ndarray, roi_type: ROIType) -> str:
        """
        Compute fast hash for ROI region.
        
        Uses perceptual hashing for better change detection.
        
        Args:
            roi_region: ROI image region
            roi_type: Type of ROI (for cache key)
        
        Returns:
            Hash string
        """
        try:
            if self.hash_method == 'perceptual':
                # Perceptual hash (robust to minor changes)
                # 1. Convert to grayscale
                if len(roi_region.shape) == 3:
                    gray = cv2.cvtColor(roi_region, cv2.COLOR_BGR2GRAY)
                else:
                    gray = roi_region
                
                # 2. Resize to 8x8 for fast hashing
                resized = cv2.resize(gray, (8, 8), interpolation=cv2.INTER_AREA)
                
                # 3. Compute average pixel value
                avg = resized.mean()
                
                # 4. Create hash bits (1 if > avg, 0 otherwise)
                hash_bits = (resized > avg).astype(int)
                
                # 5. Convert to hex string
                hash_str = ''.join([str(b) for b in hash_bits.flatten()])
                return hash_str
            
            else:
                # Fast MD5 hash (exact matching)
                # Downsample for speed
                small = cv2.resize(roi_region, (16, 16), interpolation=cv2.INTER_AREA)
                hash_str = hashlib.md5(small.tobytes()).hexdigest()[:8]
                return hash_str
        
        except Exception as e:
            logger.debug(f"ROI hash computation failed for {roi_type}: {e}")
            return ""
    
    def _is_roi_changed(self, hash1: str, hash2: str, 
                       img1: Optional[np.ndarray], img2: Optional[np.ndarray],
                       sensitivity: float) -> bool:
        """
        Determine if ROI has changed based on hash and/or pixel comparison.
        
        Args:
            hash1: Current hash
            hash2: Previous hash
            img1: Current image (optional, for pixel comparison)
            img2: Previous image (optional, for pixel comparison)
            sensitivity: Change threshold (0.0-1.0)
        
        Returns:
            True if changed, False if unchanged
        """
        # Quick hash comparison
        if hash1 == hash2:
            return False
        
        # If hashes differ, check Hamming distance for perceptual hash
        if self.hash_method == 'perceptual' and len(hash1) == len(hash2):
            # Count differing bits
            hamming_distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
            max_distance = len(hash1)
            difference_ratio = hamming_distance / max_distance
            
            # Use sensitivity threshold
            return difference_ratio > sensitivity
        
        # For MD5 hash, any difference = change
        return True
    
    def get_roi_region(self, image: np.ndarray, roi_type: ROIType) -> Optional[np.ndarray]:
        """
        Extract ROI region from image.
        
        Args:
            image: Full image
            roi_type: Type of ROI to extract
        
        Returns:
            ROI region or None if invalid
        """
        if roi_type not in self.roi_states:
            return None
        
        roi_def = self.roi_states[roi_type].roi_def
        h, w = image.shape[:2]
        
        x = int(w * roi_def.x_ratio)
        y = int(h * roi_def.y_ratio)
        roi_w = int(w * roi_def.width_ratio)
        roi_h = int(h * roi_def.height_ratio)
        
        # Bounds check
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        roi_w = min(roi_w, w - x)
        roi_h = min(roi_h, h - y)
        
        if roi_w <= 0 or roi_h <= 0:
            return None
        
        return image[y:y+roi_h, x:x+roi_w]
    
    def get_changed_seat_rois(self, detection: ROIChangeDetection) -> List[int]:
        """
        Get list of seat numbers that have changed.
        
        Args:
            detection: ROI change detection result
        
        Returns:
            List of seat numbers (1-9)
        """
        seat_numbers = []
        for roi_type in detection.changed_rois:
            if roi_type.value.startswith('seat_'):
                try:
                    seat_num = int(roi_type.value.split('_')[1])
                    seat_numbers.append(seat_num)
                except (ValueError, IndexError):
                    pass
        return sorted(seat_numbers)
    
    def reset(self):
        """Reset all ROI tracking state."""
        for roi_state in self.roi_states.values():
            roi_state.last_hash = ""
            roi_state.last_update_time = 0.0
            roi_state.last_image = None
        
        logger.info("ROI tracker state reset")
    
    def get_statistics(self) -> Dict[str, any]:
        """Get ROI tracking statistics."""
        avg_processing_time = (
            self.total_processing_time_ms / self.total_checks
            if self.total_checks > 0 else 0.0
        )
        
        skip_rate = (
            self.total_skips / self.total_checks * 100
            if self.total_checks > 0 else 0.0
        )
        
        # Per-ROI statistics
        roi_stats = {}
        for roi_type, roi_state in self.roi_states.items():
            if roi_state.check_count > 0:
                roi_stats[roi_type.value] = {
                    'checks': roi_state.check_count,
                    'changes': roi_state.change_count,
                    'skips': roi_state.skip_count,
                    'skip_rate': roi_state.skip_count / roi_state.check_count * 100,
                    'priority': roi_state.roi_def.priority,
                    'sensitivity': roi_state.roi_def.sensitivity
                }
        
        return {
            'enabled': self.enable_tracking,
            'total_checks': self.total_checks,
            'total_changes': self.total_changes,
            'total_skips': self.total_skips,
            'skip_rate_percent': skip_rate,
            'avg_detection_time_ms': avg_processing_time,
            'total_processing_time_ms': self.total_processing_time_ms,
            'hash_method': self.hash_method,
            'global_sensitivity': self.global_sensitivity,
            'roi_count': len(self.roi_states),
            'per_roi_stats': roi_stats
        }
    
    def print_statistics(self):
        """Print human-readable statistics."""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print("ROI TRACKER STATISTICS")
        print("=" * 70)
        print(f"Status: {'ENABLED' if stats['enabled'] else 'DISABLED'}")
        print(f"Total ROI Checks: {stats['total_checks']:,}")
        print(f"Changes Detected: {stats['total_changes']:,}")
        print(f"Unchanged (Skipped): {stats['total_skips']:,}")
        print(f"Skip Rate: {stats['skip_rate_percent']:.1f}%")
        print(f"Avg Detection Time: {stats['avg_detection_time_ms']:.2f}ms")
        print(f"Total Processing Time: {stats['total_processing_time_ms']:.1f}ms")
        print(f"Hash Method: {stats['hash_method']}")
        print(f"Global Sensitivity: {stats['global_sensitivity']:.2%}")
        
        print("\nPer-ROI Statistics (Top 10 by checks):")
        print("-" * 70)
        
        roi_stats = stats['per_roi_stats']
        sorted_rois = sorted(
            roi_stats.items(),
            key=lambda x: x[1]['checks'],
            reverse=True
        )[:10]
        
        for roi_name, roi_stat in sorted_rois:
            print(f"  {roi_name:20s}: "
                  f"{roi_stat['checks']:5d} checks, "
                  f"{roi_stat['changes']:4d} changes, "
                  f"{roi_stat['skip_rate']:5.1f}% skip rate, "
                  f"pri={roi_stat['priority']}, "
                  f"sens={roi_stat['sensitivity']:.2%}")
        
        print("=" * 70)


# Singleton instance
_roi_tracker_instance: Optional[ROITracker] = None


def get_roi_tracker(enable_tracking: bool = True) -> ROITracker:
    """
    Get singleton ROI tracker instance.
    
    Args:
        enable_tracking: Enable ROI tracking
    
    Returns:
        ROITracker instance
    """
    global _roi_tracker_instance
    
    if _roi_tracker_instance is None:
        _roi_tracker_instance = ROITracker(enable_tracking=enable_tracking)
    
    return _roi_tracker_instance


if __name__ == '__main__':
    # Test ROI tracker
    print("Testing ROI Tracker...")
    
    tracker = get_roi_tracker(enable_tracking=True)
    
    # Create dummy test image
    if ROI_DEPENDENCIES_AVAILABLE:
        test_img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        # First detection (all should be "changed")
        result1 = tracker.detect_changes(test_img)
        print(f"\nFirst detection: {len(result1.changed_rois)} changed, "
              f"{len(result1.unchanged_rois)} unchanged")
        
        # Second detection (same image, all should be "unchanged")
        result2 = tracker.detect_changes(test_img)
        print(f"Second detection: {len(result2.changed_rois)} changed, "
              f"{len(result2.unchanged_rois)} unchanged "
              f"({result2.skip_percentage:.1f}% skip rate)")
        
        # Modify a small region
        test_img[500:600, 900:1000] = 255
        result3 = tracker.detect_changes(test_img)
        print(f"After modification: {len(result3.changed_rois)} changed, "
              f"{len(result3.unchanged_rois)} unchanged "
              f"({result3.skip_percentage:.1f}% skip rate)")
        
        # Print statistics
        tracker.print_statistics()
        
        print("\n✓ ROI Tracker test complete")
    else:
        print("✗ OpenCV not available, skipping tests")
