#!/usr/bin/env python3
"""Tests for Tournament Clock"""

import pytest
from datetime import datetime, timedelta
from src.pokertool.tournament_clock import TournamentClock, BlindLevel, ClockSnapshot
import time


class TestTournamentClock:
    def test_initialization(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        assert clock.current_level == 0
        assert clock.is_running is False
        assert clock.is_paused is False

    def test_start_clock(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        clock.start()
        assert clock.is_running is True
        assert clock.start_time is not None

    def test_pause_and_resume(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        clock.start()
        time.sleep(0.1)
        clock.pause()
        assert clock.is_paused is True
        assert clock.pause_time is not None
        time.sleep(0.1)
        clock.resume()
        assert clock.is_paused is False
        assert clock.total_paused_seconds > 0

    def test_get_current_level(self):
        structure = [
            BlindLevel(1, 25, 50, 0, 15),
            BlindLevel(2, 50, 100, 0, 15)
        ]
        clock = TournamentClock(structure)
        level = clock.get_current_level()
        assert level.level == 1
        assert level.small_blind == 25
        assert level.big_blind == 50

    def test_advance_level(self):
        structure = [
            BlindLevel(1, 25, 50, 0, 15),
            BlindLevel(2, 50, 100, 0, 15)
        ]
        clock = TournamentClock(structure)
        clock.advance_level()
        assert clock.current_level == 1
        level = clock.get_current_level()
        assert level.level == 2

    def test_break_levels(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        clock.set_break_level(0)
        assert clock.is_break_level(0) is True
        assert clock.is_break_level() is True

    def test_take_snapshot(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        clock.start()
        snapshot = clock.take_snapshot()
        assert isinstance(snapshot, ClockSnapshot)
        assert snapshot.current_level == 0
        assert len(clock.snapshots) == 1

    def test_average_level_duration(self):
        structure = [
            BlindLevel(1, 25, 50, 0, 15),
            BlindLevel(2, 50, 100, 0, 20),
            BlindLevel(3, 75, 150, 25, 25)
        ]
        clock = TournamentClock(structure)
        avg = clock.get_average_level_duration()
        assert avg == 20.0

    def test_get_elapsed_seconds(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        assert clock.get_elapsed_seconds() == 0
        clock.start()
        time.sleep(1.1)
        elapsed = clock.get_elapsed_seconds()
        assert elapsed >= 1

    def test_time_remaining_in_level(self):
        structure = [BlindLevel(1, 25, 50, 0, 15)]
        clock = TournamentClock(structure)
        clock.start()
        remaining = clock.get_time_remaining_in_level()
        assert remaining > 0
        assert remaining <= 15 * 60


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
