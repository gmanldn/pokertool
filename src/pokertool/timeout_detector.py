#!/usr/bin/env python3
"""Player timeout detection."""

import time
from typing import Optional

class TimeoutDetector:
    """Detects when players are close to timing out."""

    def __init__(self, warning_threshold: float = 5.0):
        """
        Initialize detector.

        Args:
            warning_threshold: Seconds before timeout to emit warning
        """
        self.warning_threshold = warning_threshold
        self.action_start_time: Optional[float] = None
        self.timeout_duration: float = 30.0  # Default 30s

    def start_action_timer(self, timeout_duration: float = 30.0):
        """Start timing a player action."""
        self.action_start_time = time.time()
        self.timeout_duration = timeout_duration

    def get_time_remaining(self) -> float:
        """Get seconds remaining before timeout."""
        if self.action_start_time is None:
            return self.timeout_duration

        elapsed = time.time() - self.action_start_time
        return max(0, self.timeout_duration - elapsed)

    def is_warning_threshold(self) -> bool:
        """Check if player is close to timing out."""
        return self.get_time_remaining() <= self.warning_threshold

    def is_timed_out(self) -> bool:
        """Check if player has timed out."""
        return self.get_time_remaining() <= 0


_detector_instance: Optional[TimeoutDetector] = None

def get_timeout_detector() -> TimeoutDetector:
    """Get global timeout detector."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = TimeoutDetector()
    return _detector_instance
