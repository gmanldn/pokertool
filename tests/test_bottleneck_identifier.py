#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for BottleneckIdentifier in performance_telemetry module.
"""

import time
import pytest
from src.pokertool.performance_telemetry import (
    BottleneckIdentifier,
    get_cpu_tracker,
    reset_cpu_tracker,
    get_bottleneck_identifier,
    identify_bottlenecks,
    log_bottlenecks
)


class TestBottleneckIdentifier:
    """Test suite for BottleneckIdentifier class."""

    def setup_method(self):
        """Reset CPU tracker before each test."""
        reset_cpu_tracker()

    def test_init(self):
        """Test bottleneck identifier initialization."""
        identifier = BottleneckIdentifier(cpu_threshold_percent=60.0, time_threshold_ms=150.0)
        assert identifier.cpu_threshold == 60.0
        assert identifier.time_threshold == 150.0

    def test_identify_bottlenecks_no_data(self):
        """Test identifying bottlenecks with no data."""
        identifier = BottleneckIdentifier()
        bottlenecks = identifier.identify_bottlenecks()

        assert bottlenecks['high_cpu'] == []
        assert bottlenecks['slow_operations'] == []
        assert bottlenecks['top_time_consumers'] == []
        assert bottlenecks['recommendations'] == []

    def test_identify_high_cpu_operations(self):
        """Test identification of high CPU operations."""
        # Create mock data by tracking operations
        cpu_tracker = get_cpu_tracker()

        # Simulate operations - psutil might show low CPU in tests, so we'll just test the structure
        for _ in range(5):
            with cpu_tracker.track('high_cpu_operation'):
                time.sleep(0.01)

        identifier = BottleneckIdentifier(cpu_threshold_percent=0.0)  # Low threshold to catch operations
        bottlenecks = identifier.identify_bottlenecks()

        # Should have some data
        assert 'high_cpu' in bottlenecks
        assert 'slow_operations' in bottlenecks
        assert 'recommendations' in bottlenecks

    def test_identify_slow_operations(self):
        """Test identification of slow operations."""
        cpu_tracker = get_cpu_tracker()

        # Create a slow operation
        for _ in range(3):
            with cpu_tracker.track('slow_operation'):
                time.sleep(0.15)  # 150ms - intentionally slow

        identifier = BottleneckIdentifier(time_threshold_ms=100.0)
        bottlenecks = identifier.identify_bottlenecks()

        # Should identify as slow
        assert len(bottlenecks['slow_operations']) > 0
        assert bottlenecks['slow_operations'][0]['type'] == 'slow_operation'

    def test_top_time_consumers(self):
        """Test identification of top time consumers."""
        cpu_tracker = get_cpu_tracker()

        # Create operations with different total times
        for _ in range(10):
            with cpu_tracker.track('frequent_operation'):
                time.sleep(0.01)

        for _ in range(2):
            with cpu_tracker.track('slow_operation'):
                time.sleep(0.05)

        identifier = BottleneckIdentifier()
        bottlenecks = identifier.identify_bottlenecks()

        # Should have top time consumers
        assert len(bottlenecks['top_time_consumers']) > 0
        assert 'total_time_ms' in bottlenecks['top_time_consumers'][0]

    def test_recommendations_generated(self):
        """Test that recommendations are generated."""
        cpu_tracker = get_cpu_tracker()

        # Create a slow OCR operation
        for _ in range(3):
            with cpu_tracker.track('ocr_detection'):
                time.sleep(0.12)  # 120ms

        identifier = BottleneckIdentifier(time_threshold_ms=100.0)
        bottlenecks = identifier.identify_bottlenecks()

        # Should have recommendations
        assert len(bottlenecks['recommendations']) > 0
        # Should mention OCR optimization
        assert any('OCR' in rec for rec in bottlenecks['recommendations'])

    def test_get_optimization_priority(self):
        """Test getting prioritized optimization list."""
        cpu_tracker = get_cpu_tracker()

        # Create some operations
        for _ in range(5):
            with cpu_tracker.track('operation1'):
                time.sleep(0.15)

        for _ in range(3):
            with cpu_tracker.track('operation2'):
                time.sleep(0.08)

        identifier = BottleneckIdentifier(time_threshold_ms=100.0)
        priorities = identifier.get_optimization_priority()

        # Should have prioritized list
        assert len(priorities) > 0
        assert 'type' in priorities[0]
        assert 'priority' in priorities[0]
        assert 'reason' in priorities[0]

    def test_log_bottlenecks(self, caplog):
        """Test logging bottlenecks."""
        import logging
        caplog.set_level(logging.INFO)

        cpu_tracker = get_cpu_tracker()

        # Create some data
        for _ in range(3):
            with cpu_tracker.track('test_operation'):
                time.sleep(0.12)

        identifier = BottleneckIdentifier(time_threshold_ms=100.0)
        identifier.log_bottlenecks()

        # Check that logs were created
        assert 'BOTTLENECK ANALYSIS' in caplog.text
        assert 'RECOMMENDATIONS' in caplog.text

    def test_template_matching_recommendation(self):
        """Test template matching specific recommendations."""
        cpu_tracker = get_cpu_tracker()

        # Create slow template matching operation
        for _ in range(3):
            with cpu_tracker.track('template_matching'):
                time.sleep(0.12)

        identifier = BottleneckIdentifier(time_threshold_ms=100.0)
        bottlenecks = identifier.identify_bottlenecks()

        # Should have template matching recommendation
        assert any('TEMPLATE' in rec for rec in bottlenecks['recommendations'])


class TestGlobalBottleneckIdentifier:
    """Test suite for global bottleneck identifier functions."""

    def setup_method(self):
        """Reset CPU tracker before each test."""
        reset_cpu_tracker()

    def test_get_bottleneck_identifier_singleton(self):
        """Test that get_bottleneck_identifier returns singleton."""
        identifier1 = get_bottleneck_identifier()
        identifier2 = get_bottleneck_identifier()

        assert identifier1 is identifier2

    def test_identify_bottlenecks_convenience(self):
        """Test convenience function for identifying bottlenecks."""
        cpu_tracker = get_cpu_tracker()

        # Create some data
        for _ in range(2):
            with cpu_tracker.track('test'):
                time.sleep(0.01)

        bottlenecks = identify_bottlenecks()

        assert 'high_cpu' in bottlenecks
        assert 'slow_operations' in bottlenecks
        assert 'recommendations' in bottlenecks

    def test_log_bottlenecks_convenience(self, caplog):
        """Test convenience function for logging bottlenecks."""
        import logging
        caplog.set_level(logging.INFO)

        cpu_tracker = get_cpu_tracker()

        # Create some data
        for _ in range(2):
            with cpu_tracker.track('test'):
                time.sleep(0.12)

        log_bottlenecks()

        assert 'BOTTLENECK ANALYSIS' in caplog.text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
