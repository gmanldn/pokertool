#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for DetectionCPUTracker in performance_telemetry module.
"""

import time
import pytest
from src.pokertool.performance_telemetry import (
    DetectionCPUTracker,
    get_cpu_tracker,
    reset_cpu_tracker
)


class TestDetectionCPUTracker:
    """Test suite for DetectionCPUTracker class."""

    def test_init(self):
        """Test CPU tracker initialization."""
        tracker = DetectionCPUTracker(window_size=50)
        assert tracker.window_size == 50
        assert len(tracker.cpu_samples) == 0
        assert len(tracker.execution_times) == 0
        assert len(tracker.call_counts) == 0

    def test_track_single_operation(self):
        """Test tracking a single operation."""
        tracker = DetectionCPUTracker()

        with tracker.track('ocr_detection'):
            time.sleep(0.01)

        assert 'ocr_detection' in tracker.cpu_samples
        assert len(tracker.cpu_samples['ocr_detection']) == 1
        assert tracker.call_counts['ocr_detection'] == 1

    def test_track_multiple_operations(self):
        """Test tracking multiple operations."""
        tracker = DetectionCPUTracker()

        for _ in range(5):
            with tracker.track('ocr_detection'):
                time.sleep(0.005)

        assert tracker.call_counts['ocr_detection'] == 5
        assert len(tracker.cpu_samples['ocr_detection']) == 5

    def test_track_different_types(self):
        """Test tracking different detection types."""
        tracker = DetectionCPUTracker()

        with tracker.track('ocr_detection'):
            time.sleep(0.01)

        with tracker.track('template_matching'):
            time.sleep(0.01)

        with tracker.track('color_detection'):
            time.sleep(0.01)

        assert len(tracker.cpu_samples) == 3
        assert 'ocr_detection' in tracker.cpu_samples
        assert 'template_matching' in tracker.cpu_samples
        assert 'color_detection' in tracker.cpu_samples

    def test_window_size_limit(self):
        """Test that window size is respected."""
        tracker = DetectionCPUTracker(window_size=5)

        # Record 10 operations
        for _ in range(10):
            with tracker.track('test'):
                time.sleep(0.001)

        # Should only keep last 5
        assert len(tracker.cpu_samples['test']) == 5
        assert len(tracker.execution_times['test']) == 5

    def test_get_metrics_no_data(self):
        """Test metrics when no operations tracked."""
        tracker = DetectionCPUTracker()
        metrics = tracker.get_metrics('nonexistent')

        assert metrics['cpu_percent'] == 0.0
        assert metrics['total_time_ms'] == 0.0
        assert metrics['call_count'] == 0
        assert metrics['uptime_seconds'] > 0

    def test_get_metrics_with_data(self):
        """Test metrics calculation with tracked data."""
        tracker = DetectionCPUTracker()

        # Track some operations
        for _ in range(10):
            with tracker.track('test'):
                time.sleep(0.01)

        metrics = tracker.get_metrics('test')

        assert metrics['call_count'] == 10
        assert metrics['cpu_percent'] >= 0.0
        assert metrics['total_time_ms'] > 0
        assert metrics['avg_time_ms'] > 0
        assert metrics['min_time_ms'] > 0
        assert metrics['max_time_ms'] > 0
        assert metrics['min_time_ms'] <= metrics['avg_time_ms'] <= metrics['max_time_ms']

    def test_execution_time_accuracy(self):
        """Test that execution time is measured accurately."""
        tracker = DetectionCPUTracker()

        with tracker.track('test'):
            time.sleep(0.1)  # Sleep for 100ms

        metrics = tracker.get_metrics('test')

        # Should be close to 100ms (allow 20ms tolerance)
        assert 80 < metrics['avg_time_ms'] < 120

    def test_get_all_metrics(self):
        """Test getting metrics for all detection types."""
        tracker = DetectionCPUTracker()

        for _ in range(3):
            with tracker.track('ocr_detection'):
                time.sleep(0.01)

        for _ in range(2):
            with tracker.track('template_matching'):
                time.sleep(0.01)

        all_metrics = tracker.get_all_metrics()

        assert 'ocr_detection' in all_metrics
        assert 'template_matching' in all_metrics
        assert all_metrics['ocr_detection']['call_count'] == 3
        assert all_metrics['template_matching']['call_count'] == 2

    def test_reset_specific_type(self):
        """Test resetting a specific detection type."""
        tracker = DetectionCPUTracker()

        with tracker.track('ocr_detection'):
            pass

        with tracker.track('template_matching'):
            pass

        tracker.reset('ocr_detection')

        assert len(tracker.cpu_samples.get('ocr_detection', [])) == 0
        assert tracker.call_counts.get('ocr_detection', 0) == 0
        assert tracker.call_counts['template_matching'] == 1

    def test_reset_all_types(self):
        """Test resetting all detection types."""
        tracker = DetectionCPUTracker()

        with tracker.track('ocr_detection'):
            pass

        with tracker.track('template_matching'):
            pass

        tracker.reset()

        assert len(tracker.cpu_samples) == 0
        assert len(tracker.execution_times) == 0
        assert len(tracker.call_counts) == 0

    def test_log_metrics(self, caplog):
        """Test logging metrics."""
        import logging
        caplog.set_level(logging.INFO)

        tracker = DetectionCPUTracker()

        for _ in range(3):
            with tracker.track('test'):
                time.sleep(0.01)

        tracker.log_metrics('test')

        # Check that log was created
        assert len(caplog.records) > 0
        assert 'CPU [test]' in caplog.text

    def test_log_all_metrics(self, caplog):
        """Test logging all metrics."""
        import logging
        caplog.set_level(logging.INFO)

        tracker = DetectionCPUTracker()

        for _ in range(2):
            with tracker.track('ocr_detection'):
                time.sleep(0.01)
            with tracker.track('template_matching'):
                time.sleep(0.01)

        tracker.log_metrics()  # No specific type = log all

        # Check that logs were created for both types
        assert 'CPU [ocr_detection]' in caplog.text
        assert 'CPU [template_matching]' in caplog.text

    def test_get_summary_no_data(self):
        """Test summary with no data."""
        tracker = DetectionCPUTracker()
        summary = tracker.get_summary()

        assert summary['total_types'] == 0
        assert summary['total_calls'] == 0
        assert summary['avg_cpu_percent'] == 0.0
        assert summary['total_time_ms'] == 0.0
        assert summary['top_cpu_type'] is None
        assert summary['top_time_type'] is None

    def test_get_summary_with_data(self):
        """Test summary calculation with data."""
        tracker = DetectionCPUTracker()

        # Track different types with different call counts
        for _ in range(5):
            with tracker.track('ocr_detection'):
                time.sleep(0.01)

        for _ in range(2):
            with tracker.track('template_matching'):
                time.sleep(0.01)

        summary = tracker.get_summary()

        assert summary['total_types'] == 2
        assert summary['total_calls'] == 7
        assert summary['avg_cpu_percent'] >= 0.0
        assert summary['total_time_ms'] > 0
        assert summary['top_cpu_type'] in ['ocr_detection', 'template_matching']
        assert summary['top_time_type'] in ['ocr_detection', 'template_matching']

    def test_context_manager_with_exception(self):
        """Test that tracking works even when exception occurs."""
        tracker = DetectionCPUTracker()

        try:
            with tracker.track('test'):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should still record the operation
        assert tracker.call_counts['test'] == 1
        metrics = tracker.get_metrics('test')
        assert metrics['call_count'] == 1
        assert metrics['avg_time_ms'] > 0

    def test_thread_safety(self):
        """Test that CPU tracker is thread-safe."""
        import threading

        tracker = DetectionCPUTracker()

        def track_operations(detection_type, count):
            for _ in range(count):
                with tracker.track(detection_type):
                    time.sleep(0.001)

        threads = [
            threading.Thread(target=track_operations, args=('thread1', 20)),
            threading.Thread(target=track_operations, args=('thread2', 20)),
            threading.Thread(target=track_operations, args=('thread3', 20)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All operations should be recorded
        all_metrics = tracker.get_all_metrics()
        assert len(all_metrics) == 3
        assert all(m['call_count'] == 20 for m in all_metrics.values())

    def test_metrics_min_max_ranges(self):
        """Test that min/max values are within reasonable ranges."""
        tracker = DetectionCPUTracker()

        # Track operations with varying sleep times
        with tracker.track('test'):
            time.sleep(0.01)
        with tracker.track('test'):
            time.sleep(0.02)
        with tracker.track('test'):
            time.sleep(0.03)

        metrics = tracker.get_metrics('test')

        # Min should be less than average, average less than max
        assert metrics['min_time_ms'] <= metrics['avg_time_ms']
        assert metrics['avg_time_ms'] <= metrics['max_time_ms']

        # CPU percentages should be non-negative
        assert metrics['min_cpu_percent'] >= 0.0
        assert metrics['max_cpu_percent'] >= 0.0


class TestGlobalCPUTracker:
    """Test suite for global CPU tracker functions."""

    def test_get_cpu_tracker_singleton(self):
        """Test that get_cpu_tracker returns singleton."""
        tracker1 = get_cpu_tracker()
        tracker2 = get_cpu_tracker()

        assert tracker1 is tracker2

    def test_reset_cpu_tracker(self):
        """Test global reset function."""
        tracker = get_cpu_tracker()

        with tracker.track('test'):
            time.sleep(0.01)

        reset_cpu_tracker('test')

        metrics = tracker.get_metrics('test')
        assert metrics['call_count'] == 0

    def test_reset_all_global(self):
        """Test resetting all types globally."""
        tracker = get_cpu_tracker()

        with tracker.track('type1'):
            pass

        with tracker.track('type2'):
            pass

        reset_cpu_tracker()  # Reset all

        assert len(tracker.cpu_samples) == 0


class TestCPUTrackerIntegration:
    """Integration tests for CPU tracker usage patterns."""

    def test_real_world_pattern(self):
        """Test realistic detection loop pattern."""
        tracker = DetectionCPUTracker()

        # Simulate detection loop
        for _ in range(10):
            # OCR detection
            with tracker.track('ocr_detection'):
                time.sleep(0.01)

            # Template matching
            with tracker.track('template_matching'):
                time.sleep(0.005)

            # Color detection
            with tracker.track('color_detection'):
                time.sleep(0.003)

        # Verify all types tracked
        all_metrics = tracker.get_all_metrics()
        assert len(all_metrics) == 3
        assert all(m['call_count'] == 10 for m in all_metrics.values())

        # Verify relative timings
        ocr_time = all_metrics['ocr_detection']['avg_time_ms']
        template_time = all_metrics['template_matching']['avg_time_ms']
        color_time = all_metrics['color_detection']['avg_time_ms']

        # OCR should take longest, color shortest
        assert ocr_time > template_time > color_time


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
