#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for DetectionFPSCounter in performance_telemetry module.
"""

import time
import pytest
from src.pokertool.performance_telemetry import (
    DetectionFPSCounter,
    get_fps_counter,
    reset_fps_counter
)


class TestDetectionFPSCounter:
    """Test suite for DetectionFPSCounter class."""

    def test_init(self):
        """Test FPS counter initialization."""
        counter = DetectionFPSCounter(window_size=50)
        assert counter.window_size == 50
        assert len(counter.frame_times) == 0

    def test_record_frame_single_type(self):
        """Test recording frames for a single detection type."""
        counter = DetectionFPSCounter()
        counter.record_frame('card_detection')
        counter.record_frame('card_detection')
        counter.record_frame('card_detection')

        assert 'card_detection' in counter.frame_times
        assert len(counter.frame_times['card_detection']) == 3

    def test_record_frame_multiple_types(self):
        """Test recording frames for multiple detection types."""
        counter = DetectionFPSCounter()
        counter.record_frame('card_detection')
        counter.record_frame('player_detection')
        counter.record_frame('pot_detection')

        assert len(counter.frame_times) == 3
        assert 'card_detection' in counter.frame_times
        assert 'player_detection' in counter.frame_times
        assert 'pot_detection' in counter.frame_times

    def test_window_size_limit(self):
        """Test that window size is respected."""
        counter = DetectionFPSCounter(window_size=5)

        # Record 10 frames
        for _ in range(10):
            counter.record_frame('test')
            time.sleep(0.01)

        # Should only keep last 5
        assert len(counter.frame_times['test']) == 5

    def test_get_metrics_no_frames(self):
        """Test metrics when no frames recorded."""
        counter = DetectionFPSCounter()
        metrics = counter.get_metrics('nonexistent')

        assert metrics['fps'] == 0.0
        assert metrics['avg_fps'] == 0.0
        assert metrics['min_fps'] == 0.0
        assert metrics['max_fps'] == 0.0
        assert metrics['frame_count'] == 0
        assert metrics['uptime_seconds'] > 0

    def test_get_metrics_single_frame(self):
        """Test metrics with only one frame."""
        counter = DetectionFPSCounter()
        counter.record_frame('test')
        metrics = counter.get_metrics('test')

        # Single frame = not enough data (returns 0 for all metrics)
        assert metrics['fps'] == 0.0
        assert metrics['frame_count'] == 0  # Returns 0 when < 2 frames

    def test_get_metrics_multiple_frames(self):
        """Test metrics calculation with multiple frames."""
        counter = DetectionFPSCounter()

        # Record frames at ~20 FPS (50ms intervals)
        for _ in range(10):
            counter.record_frame('test')
            time.sleep(0.05)

        metrics = counter.get_metrics('test')

        # Should be around 20 FPS
        assert metrics['frame_count'] == 10
        assert 15 < metrics['avg_fps'] < 25  # Allow some tolerance
        assert metrics['min_fps'] > 0
        assert metrics['max_fps'] > 0
        assert metrics['fps'] > 0

    def test_get_all_metrics(self):
        """Test getting metrics for all detection types."""
        counter = DetectionFPSCounter()

        for _ in range(5):
            counter.record_frame('card_detection')
            counter.record_frame('player_detection')
            time.sleep(0.01)

        all_metrics = counter.get_all_metrics()

        assert 'card_detection' in all_metrics
        assert 'player_detection' in all_metrics
        assert all_metrics['card_detection']['frame_count'] == 5
        assert all_metrics['player_detection']['frame_count'] == 5

    def test_reset_specific_type(self):
        """Test resetting a specific detection type."""
        counter = DetectionFPSCounter()

        counter.record_frame('card_detection')
        counter.record_frame('player_detection')
        counter.reset('card_detection')

        assert len(counter.frame_times.get('card_detection', [])) == 0
        assert len(counter.frame_times['player_detection']) == 1

    def test_reset_all_types(self):
        """Test resetting all detection types."""
        counter = DetectionFPSCounter()

        counter.record_frame('card_detection')
        counter.record_frame('player_detection')
        counter.reset()

        assert len(counter.frame_times) == 0

    def test_log_metrics(self, caplog):
        """Test logging metrics."""
        import logging
        caplog.set_level(logging.INFO)

        counter = DetectionFPSCounter()

        for _ in range(5):
            counter.record_frame('test')
            time.sleep(0.01)

        counter.log_metrics('test')

        # Check that log was created
        assert len(caplog.records) > 0
        assert 'FPS [test]' in caplog.text

    def test_log_all_metrics(self, caplog):
        """Test logging all metrics."""
        import logging
        caplog.set_level(logging.INFO)

        counter = DetectionFPSCounter()

        for _ in range(3):
            counter.record_frame('card_detection')
            counter.record_frame('player_detection')
            time.sleep(0.01)

        counter.log_metrics()  # No specific type = log all

        # Check that logs were created for both types
        assert 'FPS [card_detection]' in caplog.text
        assert 'FPS [player_detection]' in caplog.text

    def test_fps_accuracy(self):
        """Test FPS calculation accuracy."""
        counter = DetectionFPSCounter()

        # Simulate exactly 10 FPS (100ms intervals)
        for _ in range(20):
            counter.record_frame('test')
            time.sleep(0.1)

        metrics = counter.get_metrics('test')

        # Should be close to 10 FPS (allow 20% tolerance for timing variations)
        assert 8 < metrics['avg_fps'] < 12
        assert metrics['frame_count'] == 20

    def test_thread_safety(self):
        """Test that FPS counter is thread-safe."""
        import threading

        counter = DetectionFPSCounter()

        def record_frames(detection_type, count):
            for _ in range(count):
                counter.record_frame(detection_type)
                time.sleep(0.001)

        threads = [
            threading.Thread(target=record_frames, args=('thread1', 50)),
            threading.Thread(target=record_frames, args=('thread2', 50)),
            threading.Thread(target=record_frames, args=('thread3', 50)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All frames should be recorded
        metrics = counter.get_all_metrics()
        assert len(metrics) == 3
        assert all(m['frame_count'] == 50 for m in metrics.values())


class TestGlobalFPSCounter:
    """Test suite for global FPS counter functions."""

    def test_get_fps_counter_singleton(self):
        """Test that get_fps_counter returns singleton."""
        counter1 = get_fps_counter()
        counter2 = get_fps_counter()

        assert counter1 is counter2

    def test_reset_fps_counter(self):
        """Test global reset function."""
        counter = get_fps_counter()
        counter.record_frame('test')

        reset_fps_counter('test')

        metrics = counter.get_metrics('test')
        assert metrics['frame_count'] == 0

    def test_reset_all_global(self):
        """Test resetting all types globally."""
        counter = get_fps_counter()
        counter.record_frame('type1')
        counter.record_frame('type2')

        reset_fps_counter()  # Reset all

        assert len(counter.frame_times) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
