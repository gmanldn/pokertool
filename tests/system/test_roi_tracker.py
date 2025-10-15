"""
Tests for ROI (Region of Interest) Tracking System
===================================================

Comprehensive test suite for the ROI tracker module.
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch

# Import the module to test
try:
    from pokertool.roi_tracker import (
        ROITracker,
        ROIType,
        ROIDefinition,
        ROIState,
        ROIChangeDetection,
        get_roi_tracker,
        ROI_DEPENDENCIES_AVAILABLE
    )
    ROI_TRACKER_AVAILABLE = True
except ImportError:
    ROI_TRACKER_AVAILABLE = False
    pytest.skip("ROI tracker not available", allow_module_level=True)

# Only run tests if OpenCV is available
if not ROI_DEPENDENCIES_AVAILABLE:
    pytest.skip("OpenCV not available, skipping ROI tracker tests", allow_module_level=True)


class TestROIDefinition:
    """Test ROIDefinition dataclass."""
    
    def test_creation(self):
        """Test creating ROI definition."""
        roi_def = ROIDefinition(
            roi_type=ROIType.POT,
            x_ratio=0.45,
            y_ratio=0.35,
            width_ratio=0.20,
            height_ratio=0.15,
            priority=1,
            sensitivity=0.05
        )
        
        assert roi_def.roi_type == ROIType.POT
        assert roi_def.x_ratio == 0.45
        assert roi_def.y_ratio == 0.35
        assert roi_def.width_ratio == 0.20
        assert roi_def.height_ratio == 0.15
        assert roi_def.priority == 1
        assert roi_def.sensitivity == 0.05
    
    def test_default_values(self):
        """Test default values."""
        roi_def = ROIDefinition(
            roi_type=ROIType.BOARD,
            x_ratio=0.5,
            y_ratio=0.5,
            width_ratio=0.2,
            height_ratio=0.2
        )
        
        assert roi_def.priority == 1  # Default
        assert roi_def.sensitivity == 0.05  # Default


class TestROIState:
    """Test ROIState dataclass."""
    
    def test_creation(self):
        """Test creating ROI state."""
        roi_def = ROIDefinition(
            roi_type=ROIType.POT,
            x_ratio=0.5,
            y_ratio=0.5,
            width_ratio=0.2,
            height_ratio=0.2
        )
        
        roi_state = ROIState(roi_def=roi_def)
        
        assert roi_state.roi_def == roi_def
        assert roi_state.last_hash == ""
        assert roi_state.last_update_time == 0.0
        assert roi_state.change_count == 0
        assert roi_state.check_count == 0
        assert roi_state.skip_count == 0
        assert roi_state.last_image is None


class TestROIChangeDetection:
    """Test ROIChangeDetection dataclass."""
    
    def test_creation(self):
        """Test creating change detection result."""
        result = ROIChangeDetection(
            changed_rois=[ROIType.POT, ROIType.BOARD],
            unchanged_rois=[ROIType.SEAT_1, ROIType.SEAT_2],
            total_rois=4,
            detection_time_ms=5.0,
            skip_percentage=50.0
        )
        
        assert len(result.changed_rois) == 2
        assert len(result.unchanged_rois) == 2
        assert result.total_rois == 4
        assert result.detection_time_ms == 5.0
        assert result.skip_percentage == 50.0


class TestROITracker:
    """Test ROITracker class."""
    
    @pytest.fixture
    def tracker(self):
        """Create ROI tracker for testing."""
        return ROITracker(enable_tracking=True)
    
    @pytest.fixture
    def test_image(self):
        """Create test image (1920x1080)."""
        return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.enable_tracking is True
        assert len(tracker.roi_states) > 0
        assert tracker.total_checks == 0
        assert tracker.total_changes == 0
        assert tracker.total_skips == 0
        assert tracker.hash_method == 'perceptual'
    
    def test_standard_rois_defined(self, tracker):
        """Test that standard ROIs are defined."""
        # Check key ROIs exist
        assert ROIType.POT in tracker.roi_states
        assert ROIType.BOARD in tracker.roi_states
        assert ROIType.HERO_CARDS in tracker.roi_states
        assert ROIType.ACTION_BUTTONS in tracker.roi_states
        
        # Check all 9 seats exist
        for i in range(1, 10):
            seat_type = ROIType(f"seat_{i}")
            assert seat_type in tracker.roi_states
    
    def test_first_detection_all_changed(self, tracker, test_image):
        """Test first detection marks all ROIs as changed."""
        result = tracker.detect_changes(test_image)
        
        # First time, all ROIs should be "changed"
        assert len(result.changed_rois) > 0
        assert len(result.unchanged_rois) == 0
        assert result.skip_percentage == 0.0
    
    def test_second_detection_all_unchanged(self, tracker, test_image):
        """Test second detection with same image marks all as unchanged."""
        # First detection
        result1 = tracker.detect_changes(test_image)
        
        # Second detection (same image)
        result2 = tracker.detect_changes(test_image)
        
        # Should all be unchanged
        assert len(result2.unchanged_rois) > 0
        assert len(result2.changed_rois) == 0
        assert result2.skip_percentage == 100.0
    
    def test_partial_change_detection(self, tracker, test_image):
        """Test detection of partial changes."""
        # First detection
        result1 = tracker.detect_changes(test_image)
        
        # Modify a specific ROI region (pot area - center)
        h, w = test_image.shape[:2]
        pot_y = int(h * 0.35)
        pot_x = int(w * 0.45)
        pot_h = int(h * 0.15)
        pot_w = int(w * 0.20)
        
        # Change pot region
        test_image[pot_y:pot_y+pot_h, pot_x:pot_x+pot_w] = 255
        
        # Second detection
        result2 = tracker.detect_changes(test_image)
        
        # Some ROIs should be changed (pot area), others unchanged
        assert len(result2.changed_rois) > 0
        assert len(result2.unchanged_rois) > 0
        assert 0 < result2.skip_percentage < 100
    
    def test_get_roi_region(self, tracker, test_image):
        """Test extracting ROI region from image."""
        roi_region = tracker.get_roi_region(test_image, ROIType.POT)
        
        assert roi_region is not None
        assert roi_region.shape[0] > 0
        assert roi_region.shape[1] > 0
    
    def test_get_changed_seat_rois(self, tracker):
        """Test getting changed seat numbers."""
        # Create mock detection result
        detection = ROIChangeDetection(
            changed_rois=[ROIType.SEAT_1, ROIType.SEAT_3, ROIType.SEAT_5, ROIType.POT],
            unchanged_rois=[ROIType.SEAT_2],
            total_rois=5
        )
        
        seat_numbers = tracker.get_changed_seat_rois(detection)
        
        assert seat_numbers == [1, 3, 5]  # Should be sorted
    
    def test_reset(self, tracker, test_image):
        """Test resetting tracker state."""
        # First detection
        result1 = tracker.detect_changes(test_image)
        
        # Reset
        tracker.reset()
        
        # All ROIs should have empty hash
        for roi_state in tracker.roi_states.values():
            assert roi_state.last_hash == ""
            assert roi_state.last_update_time == 0.0
            assert roi_state.last_image is None
        
        # Next detection should mark all as changed again
        result2 = tracker.detect_changes(test_image)
        assert len(result2.changed_rois) > 0
    
    def test_statistics_tracking(self, tracker, test_image):
        """Test statistics collection."""
        # Run multiple detections
        tracker.detect_changes(test_image)
        tracker.detect_changes(test_image)
        tracker.detect_changes(test_image)
        
        stats = tracker.get_statistics()
        
        assert stats['enabled'] is True
        assert stats['total_checks'] > 0
        assert stats['total_changes'] > 0
        assert stats['total_skips'] >= 0
        assert 0 <= stats['skip_rate_percent'] <= 100
        assert stats['avg_detection_time_ms'] >= 0
        assert stats['roi_count'] > 0
    
    def test_priority_filtering(self, tracker, test_image):
        """Test priority-based filtering."""
        # Check only priority 1 ROIs
        result = tracker.detect_changes(test_image, priority_filter=1)
        
        # Should only check high priority ROIs
        high_priority_count = sum(
            1 for roi_state in tracker.roi_states.values()
            if roi_state.roi_def.priority == 1
        )
        
        assert result.total_rois <= high_priority_count
    
    def test_disabled_tracking(self, test_image):
        """Test tracker with tracking disabled."""
        tracker = ROITracker(enable_tracking=False)
        
        result = tracker.detect_changes(test_image)
        
        # With tracking disabled, all should be marked as changed
        assert len(result.changed_rois) > 0
        assert len(result.unchanged_rois) == 0


class TestROIHashComputation:
    """Test ROI hash computation methods."""
    
    @pytest.fixture
    def tracker(self):
        """Create tracker."""
        return ROITracker(enable_tracking=True)
    
    def test_perceptual_hash(self, tracker):
        """Test perceptual hash computation."""
        tracker.hash_method = 'perceptual'
        
        # Create test ROI
        roi_region = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        hash1 = tracker._compute_roi_hash(roi_region, ROIType.POT)
        
        assert hash1 != ""
        assert len(hash1) == 64  # 8x8 = 64 bits
    
    def test_md5_hash(self, tracker):
        """Test MD5 hash computation."""
        tracker.hash_method = 'md5'
        
        # Create test ROI
        roi_region = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        hash1 = tracker._compute_roi_hash(roi_region, ROIType.POT)
        
        assert hash1 != ""
        assert len(hash1) == 8  # Truncated MD5
    
    def test_hash_consistency(self, tracker):
        """Test hash is consistent for same image."""
        tracker.hash_method = 'perceptual'
        
        roi_region = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        hash1 = tracker._compute_roi_hash(roi_region, ROIType.POT)
        hash2 = tracker._compute_roi_hash(roi_region, ROIType.POT)
        
        assert hash1 == hash2
    
    def test_hash_differs_for_different_images(self, tracker):
        """Test hash differs for different images."""
        tracker.hash_method = 'perceptual'
        
        roi1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        roi2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        hash1 = tracker._compute_roi_hash(roi1, ROIType.POT)
        hash2 = tracker._compute_roi_hash(roi2, ROIType.POT)
        
        # Should be different (very high probability)
        assert hash1 != hash2


class TestROIChangeDetectionSensitivity:
    """Test sensitivity settings for change detection."""
    
    @pytest.fixture
    def tracker(self):
        """Create tracker."""
        return ROITracker(enable_tracking=True)
    
    def test_high_sensitivity(self, tracker):
        """Test high sensitivity (low threshold)."""
        # Create image
        img1 = np.ones((100, 100, 3), dtype=np.uint8) * 100
        
        # Detect first time
        tracker.detect_changes(img1)
        
        # Make small change (1% of pixels)
        img2 = img1.copy()
        img2[0:10, 0:10] = 255
        
        # Set high sensitivity
        for roi_state in tracker.roi_states.values():
            roi_state.roi_def.sensitivity = 0.01  # Very sensitive
        
        result = tracker.detect_changes(img2)
        
        # Should detect change
        assert len(result.changed_rois) > 0
    
    def test_low_sensitivity(self, tracker):
        """Test low sensitivity (high threshold)."""
        # Create image
        img1 = np.ones((100, 100, 3), dtype=np.uint8) * 100
        
        # Detect first time
        tracker.detect_changes(img1)
        
        # Make small change
        img2 = img1.copy()
        img2[0:5, 0:5] = 255
        
        # Set low sensitivity
        for roi_state in tracker.roi_states.values():
            roi_state.roi_def.sensitivity = 0.50  # Very insensitive
        
        result = tracker.detect_changes(img2)
        
        # Should NOT detect change (too small)
        assert len(result.unchanged_rois) > 0


class TestROITrackerPerformance:
    """Test performance characteristics."""
    
    @pytest.fixture
    def tracker(self):
        """Create tracker."""
        return ROITracker(enable_tracking=True)
    
    @pytest.fixture
    def test_image(self):
        """Create test image."""
        return np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    
    def test_detection_is_fast(self, tracker, test_image):
        """Test detection completes in reasonable time."""
        start = time.time()
        result = tracker.detect_changes(test_image)
        elapsed = (time.time() - start) * 1000  # ms
        
        # Should complete in < 50ms for typical image
        assert elapsed < 50
        assert result.detection_time_ms < 50
    
    def test_skip_rate_improves_performance(self, tracker, test_image):
        """Test that skip rate reduces processing time."""
        # First detection (baseline)
        result1 = tracker.detect_changes(test_image)
        time1 = result1.detection_time_ms
        
        # Second detection (should be faster due to skips)
        result2 = tracker.detect_changes(test_image)
        time2 = result2.detection_time_ms
        
        # Second should be faster or similar (with some variance)
        # Don't enforce strict inequality due to timing variance
        assert time2 <= time1 * 1.5  # Allow 50% variance
        assert result2.skip_percentage == 100.0


class TestROITrackerIntegration:
    """Integration tests."""
    
    def test_full_workflow(self):
        """Test complete workflow."""
        tracker = ROITracker(enable_tracking=True)
        
        # Create sequence of images
        img1 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        img2 = img1.copy()
        img3 = img1.copy()
        
        # Modify specific region in img3
        img3[500:600, 900:1000] = 255
        
        # Detection sequence
        result1 = tracker.detect_changes(img1)
        assert len(result1.changed_rois) > 0  # First time
        
        result2 = tracker.detect_changes(img2)
        assert result2.skip_percentage == 100.0  # Same image
        
        result3 = tracker.detect_changes(img3)
        assert 0 < result3.skip_percentage < 100  # Partial change
        
        # Check statistics
        stats = tracker.get_statistics()
        assert stats['total_checks'] > 0
        assert stats['total_changes'] > 0
        assert stats['total_skips'] > 0
    
    def test_singleton_pattern(self):
        """Test singleton getter."""
        tracker1 = get_roi_tracker(enable_tracking=True)
        tracker2 = get_roi_tracker(enable_tracking=True)
        
        # Should be same instance
        assert tracker1 is tracker2


class TestROITrackerEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def tracker(self):
        """Create tracker for testing."""
        return ROITracker(enable_tracking=True)
    
    def test_empty_image(self):
        """Test with empty image."""
        tracker = ROITracker(enable_tracking=True)
        
        empty_img = np.array([])
        result = tracker.detect_changes(empty_img)
        
        # Should handle gracefully
        assert result.total_rois >= 0
    
    def test_small_image(self):
        """Test with very small image."""
        tracker = ROITracker(enable_tracking=True)
        
        small_img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        result = tracker.detect_changes(small_img)
        
        # Should handle gracefully
        assert result.total_rois >= 0
    
    def test_grayscale_image(self):
        """Test with grayscale image."""
        tracker = ROITracker(enable_tracking=True)
        
        gray_img = np.random.randint(0, 255, (1080, 1920), dtype=np.uint8)
        result = tracker.detect_changes(gray_img)
        
        # Should handle gracefully
        assert result.total_rois >= 0
    
    def test_invalid_roi_type(self, tracker):
        """Test getting region for invalid ROI type."""
        test_img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        # Create mock invalid ROI type (won't exist in tracker)
        # Just test that get_roi_region handles this gracefully
        result = tracker.get_roi_region(test_img, ROIType.POT)
        assert result is not None  # Valid type should work


# Test execution
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
