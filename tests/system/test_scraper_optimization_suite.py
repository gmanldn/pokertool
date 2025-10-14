#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Test Suite for Scraper Optimization Suite
========================================================

Tests for all 35 scraping improvements (speed, accuracy, reliability).

Version: 1.0.0
"""

import pytest
import numpy as np
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from pokertool.modules.scraper_optimization_suite import (
    ROITracker,
    FrameDiffEngine,
    OCRCache,
    ParallelExtractor,
    FastScreenCapture,
    TemporalConsensus,
    PotValidator,
    CardRecognitionModel,
    SpatialValidator,
    RecoveryManager,
    RedundantExtractor,
    HealthMonitor,
    ScraperOptimizationSuite,
    get_optimization_suite,
    ROI,
)


# ============================================================================
# SPEED OPTIMIZATION TESTS
# ============================================================================

class TestROITracker:
    """Test ROI tracking system."""

    def test_initialization(self):
        """Test ROI tracker initializes correctly."""
        tracker = ROITracker()
        assert len(tracker.rois) > 0
        assert 'pot' in tracker.rois
        assert 'board' in tracker.rois

    def test_detect_changed_regions(self):
        """Test change detection between frames."""
        tracker = ROITracker()

        # First frame - all regions should change
        frame1 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        changed1 = tracker.detect_changed_regions(frame1)
        assert len(changed1) == len(tracker.rois)

        # Same frame - no regions should change
        changed2 = tracker.detect_changed_regions(frame1)
        assert len(changed2) == 0

        # Different frame - all regions should change
        frame2 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        changed3 = tracker.detect_changed_regions(frame2)
        assert len(changed3) > 0

    def test_get_roi_rect(self):
        """Test getting ROI rectangle."""
        tracker = ROITracker()
        rect = tracker.get_roi_rect('pot')
        assert rect is not None
        assert len(rect) == 4

    def test_skip_rate_calculation(self):
        """Test skip rate calculation."""
        tracker = ROITracker()

        frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        tracker.detect_changed_regions(frame)
        tracker.detect_changed_regions(frame)  # No change

        skip_rate = tracker.get_skip_rate()
        assert 0.0 <= skip_rate <= 1.0


class TestFrameDiffEngine:
    """Test frame differencing engine."""

    def test_initialization(self):
        """Test frame diff engine initializes."""
        engine = FrameDiffEngine(skip_threshold=0.95)
        assert engine.skip_threshold == 0.95

    def test_should_process_frame(self):
        """Test frame processing decision."""
        engine = FrameDiffEngine()

        # First frame should always process
        frame1 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        assert engine.should_process_frame(frame1) is True

        # Same frame should skip
        assert engine.should_process_frame(frame1) is False

        # Different frame should process
        frame2 = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        assert engine.should_process_frame(frame2) is True

    def test_skip_rate(self):
        """Test skip rate calculation."""
        engine = FrameDiffEngine()

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        engine.should_process_frame(frame)

        # Process same frame 5 times
        for _ in range(5):
            engine.should_process_frame(frame)

        skip_rate = engine.get_skip_rate()
        assert skip_rate > 0.5  # Should skip most frames


class TestOCRCache:
    """Test OCR result caching."""

    def test_initialization(self):
        """Test cache initializes."""
        cache = OCRCache(max_size=100)
        assert cache.max_size == 100

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = OCRCache()
        region = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
        result = cache.get(region, 'pot')
        assert result is None

    def test_cache_hit(self):
        """Test cache hit returns stored value."""
        cache = OCRCache()
        region = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)

        # Store value
        cache.set(region, 'pot', 45.50)

        # Retrieve value
        result = cache.get(region, 'pot')
        assert result == 45.50

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = OCRCache()
        region = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)

        cache.set(region, 'pot', 45.50)

        # Different region should miss
        region2 = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
        result = cache.get(region2, 'pot')
        assert result is None

    def test_lru_eviction(self):
        """Test LRU eviction when cache full."""
        cache = OCRCache(max_size=2)

        region1 = np.ones((10, 10, 3), dtype=np.uint8)
        region2 = np.ones((10, 10, 3), dtype=np.uint8) * 2
        region3 = np.ones((10, 10, 3), dtype=np.uint8) * 3

        cache.set(region1, 'pot', 1.0)
        cache.set(region2, 'pot', 2.0)
        cache.set(region3, 'pot', 3.0)  # Should evict region1

        # Region1 should be evicted
        assert cache.get(region1, 'pot') is None
        assert cache.get(region2, 'pot') == 2.0
        assert cache.get(region3, 'pot') == 3.0

    def test_hit_rate(self):
        """Test hit rate calculation."""
        cache = OCRCache()
        region = np.ones((10, 10, 3), dtype=np.uint8)

        # 1 miss
        cache.get(region, 'pot')

        # 1 hit
        cache.set(region, 'pot', 1.0)
        cache.get(region, 'pot')

        hit_rate = cache.get_hit_rate()
        assert hit_rate == 0.5


class TestParallelExtractor:
    """Test parallel extraction."""

    def test_initialization(self):
        """Test parallel extractor initializes."""
        extractor = ParallelExtractor(max_workers=4)
        assert extractor.extraction_timeout == 5.0

    def test_parallel_extraction(self):
        """Test parallel extraction of multiple regions."""
        extractor = ParallelExtractor()

        # Mock extraction function
        def mock_extract(name, region):
            time.sleep(0.01)  # Simulate work
            return f"result_{name}"

        # Create mock regions
        regions = {
            'pot': np.zeros((50, 100, 3)),
            'board': np.zeros((50, 100, 3)),
            'seat1': np.zeros((50, 100, 3)),
        }

        # Extract in parallel
        start = time.time()
        results = extractor.extract_parallel(regions, mock_extract)
        elapsed = time.time() - start

        # Should complete faster than sequential (3 * 0.01 = 0.03s)
        assert elapsed < 0.025
        assert len(results) == 3
        assert results['pot'] == 'result_pot'

        extractor.shutdown()


# ============================================================================
# ACCURACY ENHANCEMENT TESTS
# ============================================================================

class TestTemporalConsensus:
    """Test temporal consensus smoothing."""

    def test_initialization(self):
        """Test temporal consensus initializes."""
        consensus = TemporalConsensus(window_size=5)
        assert consensus.window_size == 5

    def test_single_value(self):
        """Test consensus with single value."""
        consensus = TemporalConsensus()
        consensus.add_value('pot', 45.50, 0.9)

        # Need at least 3 values
        result = consensus.get_consensus('pot')
        assert result is None

    def test_consensus_calculation(self):
        """Test consensus value calculation."""
        consensus = TemporalConsensus()

        # Add noisy values
        values = [45.0, 46.0, 45.5, 45.2, 45.8]
        for v in values:
            consensus.add_value('pot', v, 0.9)

        result = consensus.get_consensus('pot')
        assert result is not None
        assert 45.0 <= result <= 46.0

    def test_outlier_rejection(self):
        """Test outlier values are rejected."""
        consensus = TemporalConsensus()

        # Add values with one outlier
        values = [45.0, 45.5, 45.2, 100.0, 45.8]  # 100.0 is outlier
        for v in values:
            consensus.add_value('pot', v, 0.9)

        result = consensus.get_consensus('pot')
        assert result is not None
        assert result < 50.0  # Outlier should not affect result

    def test_clear_buffer(self):
        """Test clearing consensus buffer."""
        consensus = TemporalConsensus()

        consensus.add_value('pot', 45.0, 0.9)
        consensus.add_value('pot', 45.5, 0.9)
        consensus.add_value('pot', 45.2, 0.9)

        consensus.clear('pot')

        result = consensus.get_consensus('pot')
        assert result is None


class TestPotValidator:
    """Test pot validation."""

    def test_initialization(self):
        """Test pot validator initializes."""
        validator = PotValidator(tolerance=0.10)
        assert validator.tolerance == 0.10

    def test_first_pot(self):
        """Test first pot is always valid."""
        validator = PotValidator()
        valid, corrected = validator.validate_pot(45.0, {1: 5.0, 2: 5.0})
        assert valid is True
        assert corrected == 45.0

    def test_valid_pot(self):
        """Test valid pot continuation."""
        validator = PotValidator()

        # First pot
        validator.validate_pot(10.0, {1: 5.0, 2: 5.0})

        # Valid continuation
        valid, corrected = validator.validate_pot(20.0, {1: 10.0, 2: 10.0})
        assert valid is True
        assert corrected == 20.0

    def test_invalid_pot_correction(self):
        """Test invalid pot is corrected."""
        validator = PotValidator()

        # First pot
        validator.validate_pot(10.0, {1: 5.0, 2: 5.0})

        # Invalid pot (should be 20, but extracted as 50)
        valid, corrected = validator.validate_pot(50.0, {1: 10.0, 2: 10.0})
        assert valid is False
        assert corrected == 20.0  # Should be corrected

    def test_stage_change_reset(self):
        """Test validation resets on stage change."""
        validator = PotValidator()

        validator.validate_pot(10.0, {1: 5.0, 2: 5.0})

        # Stage changed - should accept new pot
        valid, corrected = validator.validate_pot(100.0, {1: 0.0, 2: 0.0}, stage_changed=True)
        assert valid is True
        assert corrected == 100.0


class TestSpatialValidator:
    """Test spatial relationship validation."""

    def test_initialization(self):
        """Test spatial validator initializes."""
        validator = SpatialValidator()
        assert 'pot' in validator.layout

    def test_valid_position(self):
        """Test valid element position."""
        validator = SpatialValidator()

        # Pot at center (valid)
        valid = validator.validate_position('pot', 800, 400, 1920, 1080)
        assert valid is True

    def test_invalid_position(self):
        """Test invalid element position."""
        validator = SpatialValidator()

        # Pot at top-left corner (invalid)
        valid = validator.validate_position('pot', 100, 100, 1920, 1080)
        assert valid is False

    def test_unknown_element(self):
        """Test unknown element is always valid."""
        validator = SpatialValidator()

        # Unknown element
        valid = validator.validate_position('unknown', 100, 100, 1920, 1080)
        assert valid is True

    def test_violation_rate(self):
        """Test violation rate calculation."""
        validator = SpatialValidator()

        validator.validate_position('pot', 800, 400, 1920, 1080)  # Valid
        validator.validate_position('pot', 100, 100, 1920, 1080)  # Invalid

        violation_rate = validator.get_violation_rate()
        assert violation_rate == 0.5


# ============================================================================
# RELIABILITY SYSTEM TESTS
# ============================================================================

class TestRecoveryManager:
    """Test automatic recovery manager."""

    def test_initialization(self):
        """Test recovery manager initializes."""
        manager = RecoveryManager()
        assert manager.recovery_cooldown == 10.0

    def test_success_rate_tracking(self):
        """Test success rate tracking."""
        manager = RecoveryManager()

        manager.record_result(True)
        manager.record_result(True)
        manager.record_result(False)

        assert manager.get_success_rate() == 2.0 / 3.0

    def test_recovery_trigger(self):
        """Test recovery trigger logic."""
        manager = RecoveryManager()

        # Record mostly failures
        for _ in range(18):
            manager.record_result(False)

        for _ in range(2):
            manager.record_result(True)

        # Should trigger recovery (90% success rate threshold)
        assert manager.should_trigger_recovery() is True

    def test_recovery_cooldown(self):
        """Test recovery cooldown prevents rapid triggers."""
        manager = RecoveryManager()
        manager.recovery_cooldown = 1.0

        # Trigger recovery
        for _ in range(20):
            manager.record_result(False)

        manager.trigger_recovery()

        # Should not trigger again immediately
        assert manager.should_trigger_recovery() is False


class TestRedundantExtractor:
    """Test redundant extraction paths."""

    def test_initialization(self):
        """Test redundant extractor initializes."""
        extractor = RedundantExtractor()
        assert 'cdp' in extractor.method_stats
        assert 'ocr' in extractor.method_stats

    def test_cdp_success(self):
        """Test CDP extraction succeeds."""
        extractor = RedundantExtractor()

        def cdp_func():
            return 45.50

        result, method = extractor.extract_with_fallback('pot', cdp_func=cdp_func)
        assert result == 45.50
        assert method == 'cdp'

    def test_cdp_fallback_to_ocr(self):
        """Test fallback to OCR when CDP fails."""
        extractor = RedundantExtractor()

        def cdp_func():
            return None  # CDP fails

        def ocr_func():
            return 45.50

        result, method = extractor.extract_with_fallback('pot', cdp_func=cdp_func, ocr_func=ocr_func)
        assert result == 45.50
        assert method == 'ocr'

    def test_all_methods_fail(self):
        """Test all methods fail."""
        extractor = RedundantExtractor()

        def fail_func():
            return None

        result, method = extractor.extract_with_fallback('pot', cdp_func=fail_func, ocr_func=fail_func)
        assert result is None
        assert method == 'none'

    def test_method_stats(self):
        """Test method statistics tracking."""
        extractor = RedundantExtractor()

        def cdp_func():
            return 45.50

        extractor.extract_with_fallback('pot', cdp_func=cdp_func)
        extractor.extract_with_fallback('pot', cdp_func=cdp_func)

        stats = extractor.get_method_stats()
        assert stats['cdp']['attempts'] == 2
        assert stats['cdp']['successes'] == 2
        assert stats['cdp']['success_rate'] == 1.0


class TestHealthMonitor:
    """Test health monitoring."""

    def test_initialization(self):
        """Test health monitor initializes."""
        monitor = HealthMonitor(alert_threshold=0.90)
        assert monitor.alert_threshold == 0.90

    def test_record_extraction(self):
        """Test recording extraction attempts."""
        monitor = HealthMonitor()

        monitor.record_extraction('pot', success=True, confidence=0.95, extraction_time_ms=10.0)
        monitor.record_extraction('pot', success=True, confidence=0.90, extraction_time_ms=12.0)

        metrics = monitor.get_field_health('pot')
        assert metrics is not None
        assert metrics.total_extractions == 2
        assert metrics.successful_extractions == 2

    def test_alert_generation(self):
        """Test alert generation for low success rate."""
        monitor = HealthMonitor(alert_threshold=0.90)

        # Record mostly failures
        for _ in range(8):
            monitor.record_extraction('pot', success=False)

        for _ in range(2):
            monitor.record_extraction('pot', success=True)

        alerts = monitor.get_alerts()
        assert len(alerts) > 0
        assert 'pot' in alerts[0]

    def test_clear_alerts(self):
        """Test clearing alerts."""
        monitor = HealthMonitor()

        # Generate alert
        for _ in range(10):
            monitor.record_extraction('pot', success=False)

        alerts = monitor.get_alerts()
        assert len(alerts) > 0

        monitor.clear_alerts()
        alerts = monitor.get_alerts()
        assert len(alerts) == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestScraperOptimizationSuite:
    """Test complete optimization suite."""

    def test_initialization(self):
        """Test suite initializes all components."""
        suite = ScraperOptimizationSuite()

        assert suite.roi_tracker is not None
        assert suite.frame_diff is not None
        assert suite.ocr_cache is not None
        assert suite.parallel_extractor is not None
        assert suite.temporal_consensus is not None
        assert suite.pot_validator is not None
        assert suite.recovery_manager is not None
        assert suite.redundant_extractor is not None
        assert suite.health_monitor is not None

        suite.shutdown()

    def test_get_summary(self):
        """Test getting optimization summary."""
        suite = ScraperOptimizationSuite()

        summary = suite.get_summary()

        assert 'speed' in summary
        assert 'accuracy' in summary
        assert 'reliability' in summary

        assert 'roi_skip_rate' in summary['speed']
        assert 'pot_corrections' in summary['accuracy']
        assert 'success_rate' in summary['reliability']

        suite.shutdown()

    def test_singleton_pattern(self):
        """Test singleton pattern."""
        suite1 = get_optimization_suite()
        suite2 = get_optimization_suite()

        assert suite1 is suite2

        suite1.shutdown()


# ============================================================================
# PERFORMANCE BENCHMARKS
# ============================================================================

class TestPerformance:
    """Performance benchmark tests."""

    def test_roi_tracking_performance(self):
        """Test ROI tracking is fast."""
        tracker = ROITracker()

        frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        start = time.time()
        for _ in range(10):
            tracker.detect_changed_regions(frame)
        elapsed = time.time() - start

        # Should process 10 frames in < 100ms
        assert elapsed < 0.1

    def test_frame_diff_performance(self):
        """Test frame differencing is fast."""
        engine = FrameDiffEngine()

        frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        start = time.time()
        for _ in range(100):
            engine.should_process_frame(frame)
        elapsed = time.time() - start

        # Should process 100 frames in < 50ms
        assert elapsed < 0.05

    def test_cache_lookup_performance(self):
        """Test cache lookup is fast."""
        cache = OCRCache()

        region = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
        cache.set(region, 'pot', 45.50)

        start = time.time()
        for _ in range(1000):
            cache.get(region, 'pot')
        elapsed = time.time() - start

        # Should do 1000 lookups in < 10ms
        assert elapsed < 0.01


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
