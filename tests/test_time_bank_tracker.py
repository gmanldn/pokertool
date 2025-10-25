#!/usr/bin/env python3
"""Tests for Time Bank Tracker"""

import pytest
from src.pokertool.time_bank_tracker import TimeBankTracker


class TestTimeBankTracker:
    def test_initialization(self):
        tracker = TimeBankTracker(300.0)
        assert tracker.initial_seconds == 300.0

    def test_record_use(self):
        tracker = TimeBankTracker(300.0)
        record = tracker.record_use("Alice", 30.0)
        assert record.seconds_used == 30.0
        assert record.remaining_seconds == 270.0

    def test_get_remaining(self):
        tracker = TimeBankTracker(300.0)
        tracker.record_use("Alice", 50.0)
        assert tracker.get_remaining("Alice") == 250.0

    def test_get_total_used(self):
        tracker = TimeBankTracker(300.0)
        tracker.record_use("Alice", 30.0)
        tracker.record_use("Alice", 20.0)
        assert tracker.get_total_used("Alice") == 50.0

    def test_reset(self):
        tracker = TimeBankTracker(300.0)
        tracker.record_use("Alice", 50.0)
        tracker.reset("Alice")
        assert tracker.get_remaining("Alice") == 300.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
