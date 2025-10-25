#!/usr/bin/env python3
"""Tournament Clock - Tracks tournament blind levels and timing"""

import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class BlindLevel:
    """Blind level configuration"""
    level: int
    small_blind: float
    big_blind: float
    ante: float
    duration_minutes: int


@dataclass
class ClockSnapshot:
    """Tournament clock snapshot"""
    timestamp: datetime
    current_level: int
    time_remaining_seconds: int
    total_elapsed_seconds: int
    is_paused: bool
    is_break: bool


class TournamentClock:
    """Manages tournament clock and blind levels."""

    def __init__(self, blind_structure: List[BlindLevel]):
        """Initialize tournament clock."""
        self.blind_structure = blind_structure
        self.current_level = 0
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.total_paused_seconds = 0
        self.snapshots: List[ClockSnapshot] = []
        self.is_running = False
        self.is_paused = False
        self.break_levels: List[int] = []

    def start(self):
        """Start the tournament clock."""
        if not self.is_running:
            self.start_time = datetime.now()
            self.is_running = True
            self.is_paused = False
            logger.info("Tournament clock started")

    def pause(self):
        """Pause the tournament clock."""
        if self.is_running and not self.is_paused:
            self.pause_time = datetime.now()
            self.is_paused = True
            logger.info("Tournament clock paused")

    def resume(self):
        """Resume the tournament clock."""
        if self.is_running and self.is_paused and self.pause_time:
            pause_duration = (datetime.now() - self.pause_time).total_seconds()
            self.total_paused_seconds += pause_duration
            self.is_paused = False
            self.pause_time = None
            logger.info(f"Tournament clock resumed after {pause_duration}s pause")

    def get_elapsed_seconds(self) -> int:
        """Get total elapsed time in seconds."""
        if not self.start_time:
            return 0

        now = datetime.now()
        if self.is_paused and self.pause_time:
            elapsed = (self.pause_time - self.start_time).total_seconds()
        else:
            elapsed = (now - self.start_time).total_seconds()

        return int(elapsed - self.total_paused_seconds)

    def get_current_level(self) -> Optional[BlindLevel]:
        """Get current blind level."""
        if not self.blind_structure or self.current_level >= len(self.blind_structure):
            return None
        return self.blind_structure[self.current_level]

    def get_time_remaining_in_level(self) -> int:
        """Get time remaining in current level (seconds)."""
        level = self.get_current_level()
        if not level:
            return 0

        elapsed = self.get_elapsed_seconds()
        level_start_time = sum(
            self.blind_structure[i].duration_minutes * 60
            for i in range(self.current_level)
        )
        time_in_level = elapsed - level_start_time
        level_duration = level.duration_minutes * 60

        return max(0, level_duration - time_in_level)

    def advance_level(self):
        """Manually advance to next level."""
        if self.current_level < len(self.blind_structure) - 1:
            self.current_level += 1
            logger.info(f"Advanced to level {self.current_level}")

    def set_break_level(self, level: int):
        """Mark a level as a break."""
        if level not in self.break_levels:
            self.break_levels.append(level)

    def is_break_level(self, level: Optional[int] = None) -> bool:
        """Check if current or specified level is a break."""
        check_level = level if level is not None else self.current_level
        return check_level in self.break_levels

    def take_snapshot(self) -> ClockSnapshot:
        """Take a snapshot of current clock state."""
        snapshot = ClockSnapshot(
            timestamp=datetime.now(),
            current_level=self.current_level,
            time_remaining_seconds=self.get_time_remaining_in_level(),
            total_elapsed_seconds=self.get_elapsed_seconds(),
            is_paused=self.is_paused,
            is_break=self.is_break_level()
        )
        self.snapshots.append(snapshot)
        return snapshot

    def get_average_level_duration(self) -> float:
        """Get average blind level duration in minutes."""
        if not self.blind_structure:
            return 0.0
        return sum(level.duration_minutes for level in self.blind_structure) / len(self.blind_structure)


if __name__ == '__main__':
    structure = [
        BlindLevel(1, 25, 50, 0, 15),
        BlindLevel(2, 50, 100, 0, 15),
        BlindLevel(3, 75, 150, 25, 15),
    ]
    clock = TournamentClock(structure)
    clock.start()
    print(f"Current level: {clock.get_current_level()}")
    print(f"Time remaining: {clock.get_time_remaining_in_level()}s")
