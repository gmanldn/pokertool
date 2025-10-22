#!/usr/bin/env python3
"""Frame Processing Performance Tracker - Logs and analyzes frame processing times."""

import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class FrameMetrics:
    """Metrics for a single frame processing."""
    frame_id: int
    start_time: float
    end_time: float
    duration_ms: float
    detection_type: str
    success: bool
    error: Optional[str] = None

    @property
    def fps(self) -> float:
        """Calculate FPS for this frame."""
        return 1000.0 / self.duration_ms if self.duration_ms > 0 else 0


class FramePerformanceTracker:
    """Tracks and analyzes frame processing performance."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics: deque = deque(maxlen=window_size)
        self.frame_count = 0
        self.slow_frame_threshold_ms = 100  # Alert if frame takes >100ms

    def start_frame(self, detection_type: str = "default") -> Dict:
        """Start tracking a frame."""
        self.frame_count += 1
        return {
            'frame_id': self.frame_count,
            'start_time': time.time(),
            'detection_type': detection_type
        }

    def end_frame(self, frame_context: Dict, success: bool = True, error: Optional[str] = None):
        """End tracking and log frame metrics."""
        end_time = time.time()
        duration_ms = (end_time - frame_context['start_time']) * 1000

        metric = FrameMetrics(
            frame_id=frame_context['frame_id'],
            start_time=frame_context['start_time'],
            end_time=end_time,
            duration_ms=duration_ms,
            detection_type=frame_context['detection_type'],
            success=success,
            error=error
        )

        self.metrics.append(metric)

        # Log slow frames
        if duration_ms > self.slow_frame_threshold_ms:
            logger.warning(
                f"Slow frame #{metric.frame_id}: {duration_ms:.1f}ms "
                f"({metric.detection_type})"
            )

        # Log every 100 frames
        if self.frame_count % 100 == 0:
            stats = self.get_stats()
            logger.info(
                f"Frame #{self.frame_count} - Avg: {stats['avg_ms']:.1f}ms, "
                f"P95: {stats['p95_ms']:.1f}ms, FPS: {stats['avg_fps']:.1f}"
            )

    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.metrics:
            return {'avg_ms': 0, 'median_ms': 0, 'p95_ms': 0, 'avg_fps': 0}

        durations = [m.duration_ms for m in self.metrics]
        return {
            'avg_ms': statistics.mean(durations),
            'median_ms': statistics.median(durations),
            'p95_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'avg_fps': 1000.0 / statistics.mean(durations)
        }


# Global tracker
_tracker: Optional[FramePerformanceTracker] = None


def get_tracker() -> FramePerformanceTracker:
    """Get global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = FramePerformanceTracker()
    return _tracker
