#!/usr/bin/env python3
"""Time Bank Tracker - Tracks player time bank usage"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class TimeUse:
    """Time bank usage record"""
    timestamp: datetime
    player_name: str
    seconds_used: float
    remaining_seconds: float


class TimeBankTracker:
    """Tracks player time bank usage."""

    def __init__(self, initial_seconds: float = 300.0):
        """Initialize tracker."""
        self.player_banks: Dict[str, float] = {}
        self.usage_records: List[TimeUse] = []
        self.initial_seconds = initial_seconds

    def record_use(self, player_name: str, seconds: float) -> TimeUse:
        """Record time bank usage."""
        if player_name not in self.player_banks:
            self.player_banks[player_name] = self.initial_seconds

        self.player_banks[player_name] -= seconds
        record = TimeUse(
            datetime.now(),
            player_name,
            seconds,
            self.player_banks[player_name]
        )
        self.usage_records.append(record)
        return record

    def get_remaining(self, player_name: str) -> float:
        """Get remaining time bank."""
        return self.player_banks.get(player_name, self.initial_seconds)

    def get_total_used(self, player_name: str) -> float:
        """Get total time used."""
        return sum(r.seconds_used for r in self.usage_records if r.player_name == player_name)

    def reset(self, player_name: Optional[str] = None):
        """Reset time banks."""
        if player_name:
            self.player_banks[player_name] = self.initial_seconds
        else:
            self.player_banks.clear()
            self.usage_records.clear()


if __name__ == '__main__':
    tracker = TimeBankTracker(300.0)
    tracker.record_use("Alice", 30.0)
    print(f"Alice remaining: {tracker.get_remaining('Alice')}s")
