"""Detection Metrics Tracker

Tracks and aggregates detection performance metrics for monitoring and analysis.
Integrates with performance telemetry system.
"""

import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class DetectionMetrics:
    """Metrics for a specific detection type."""
    total_detections: int = 0
    successful_detections: int = 0
    failed_detections: int = 0
    total_confidence: float = 0.0
    avg_confidence: float = 0.0
    min_confidence: float = 1.0
    max_confidence: float = 0.0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    last_detection_time: Optional[float] = None

    def update_confidence(self, confidence: float) -> None:
        """Update confidence statistics."""
        self.total_confidence += confidence
        self.min_confidence = min(self.min_confidence, confidence)
        self.max_confidence = max(self.max_confidence, confidence)
        if self.total_detections > 0:
            self.avg_confidence = self.total_confidence / self.total_detections

    def update_duration(self, duration_ms: float) -> None:
        """Update duration statistics."""
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        if self.total_detections > 0:
            self.avg_duration_ms = self.total_duration_ms / self.total_detections

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'total': self.total_detections,
            'successful': self.successful_detections,
            'failed': self.failed_detections,
            'success_rate': self.successful_detections / self.total_detections if self.total_detections > 0 else 0,
            'avg_confidence': round(self.avg_confidence, 3),
            'min_confidence': round(self.min_confidence, 3),
            'max_confidence': round(self.max_confidence, 3),
            'avg_duration_ms': round(self.avg_duration_ms, 2),
            'min_duration_ms': round(self.min_duration_ms, 2),
            'max_duration_ms': round(self.max_duration_ms, 2),
            'last_detection': self.last_detection_time,
        }


class DetectionMetricsTracker:
    """Track detection performance metrics across all detection types."""

    def __init__(self):
        self.metrics: Dict[str, DetectionMetrics] = defaultdict(DetectionMetrics)
        self.lock = Lock()

        # FPS tracking
        self.frame_times: deque = deque(maxlen=60)  # Last 60 frames
        self.last_frame_time: Optional[float] = None

        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque = deque(maxlen=50)

    def record_detection(
        self,
        detection_type: str,
        success: bool,
        confidence: float = 0.0,
        duration_ms: float = 0.0
    ) -> None:
        """
        Record a detection attempt.

        Args:
            detection_type: Type of detection (pot, card, player, etc.)
            success: Whether detection succeeded
            confidence: Detection confidence (0-1)
            duration_ms: Time taken in milliseconds
        """
        with self.lock:
            metrics = self.metrics[detection_type]
            metrics.total_detections += 1
            metrics.last_detection_time = time.time()

            if success:
                metrics.successful_detections += 1
                if confidence > 0:
                    metrics.update_confidence(confidence)
            else:
                metrics.failed_detections += 1

            if duration_ms > 0:
                metrics.update_duration(duration_ms)

    def record_frame(self) -> None:
        """Record a frame for FPS calculation."""
        current_time = time.time()
        with self.lock:
            if self.last_frame_time is not None:
                frame_time = current_time - self.last_frame_time
                self.frame_times.append(frame_time)
            self.last_frame_time = current_time

    def get_fps(self) -> float:
        """Get current FPS."""
        with self.lock:
            if len(self.frame_times) < 2:
                return 0.0
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_avg_frame_time_ms(self) -> float:
        """Get average frame time in milliseconds."""
        with self.lock:
            if not self.frame_times:
                return 0.0
            return (sum(self.frame_times) / len(self.frame_times)) * 1000

    def record_error(self, detection_type: str, error_message: str) -> None:
        """Record a detection error."""
        with self.lock:
            self.error_counts[detection_type] += 1
            self.recent_errors.append({
                'type': detection_type,
                'message': error_message,
                'timestamp': time.time()
            })

    def get_metrics(self, detection_type: str) -> Optional[Dict]:
        """Get metrics for a specific detection type."""
        with self.lock:
            if detection_type not in self.metrics:
                return None
            return self.metrics[detection_type].to_dict()

    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all detection types."""
        with self.lock:
            return {
                detection_type: metrics.to_dict()
                for detection_type, metrics in self.metrics.items()
            }

    def get_summary(self) -> Dict:
        """Get summary of all detection metrics."""
        with self.lock:
            total_detections = sum(m.total_detections for m in self.metrics.values())
            total_successful = sum(m.successful_detections for m in self.metrics.values())
            total_failed = sum(m.failed_detections for m in self.metrics.values())

            return {
                'total_detections': total_detections,
                'successful_detections': total_successful,
                'failed_detections': total_failed,
                'overall_success_rate': total_successful / total_detections if total_detections > 0 else 0,
                'fps': round(self.get_fps(), 2),
                'avg_frame_time_ms': round(self.get_avg_frame_time_ms(), 2),
                'detection_types': list(self.metrics.keys()),
                'error_count': sum(self.error_counts.values()),
                'recent_errors': list(self.recent_errors)[-10:],  # Last 10 errors
                'by_type': self.get_all_metrics()
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.frame_times.clear()
            self.last_frame_time = None
            self.error_counts.clear()
            self.recent_errors.clear()


# Global instance
_global_metrics_tracker: Optional[DetectionMetricsTracker] = None


def get_detection_metrics_tracker() -> DetectionMetricsTracker:
    """Get the global detection metrics tracker instance."""
    global _global_metrics_tracker
    if _global_metrics_tracker is None:
        _global_metrics_tracker = DetectionMetricsTracker()
    return _global_metrics_tracker


def record_detection(
    detection_type: str,
    success: bool,
    confidence: float = 0.0,
    duration_ms: float = 0.0
) -> None:
    """Convenience function to record a detection."""
    tracker = get_detection_metrics_tracker()
    tracker.record_detection(detection_type, success, confidence, duration_ms)


def record_frame() -> None:
    """Convenience function to record a frame."""
    tracker = get_detection_metrics_tracker()
    tracker.record_frame()


def get_detection_summary() -> Dict:
    """Convenience function to get detection summary."""
    tracker = get_detection_metrics_tracker()
    return tracker.get_summary()
