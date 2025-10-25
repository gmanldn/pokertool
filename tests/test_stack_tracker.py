#!/usr/bin/env python3
"""Tests for Stack Tracker"""

import pytest
from src.pokertool.stack_tracker import StackTracker


class TestStackTracker:
    """Test suite for StackTracker"""

    def test_initialization(self):
        """Test tracker initialization"""
        tracker = StackTracker()
        assert len(tracker.current_stacks) == 0
        assert len(tracker.snapshots) == 0

    def test_update_stack(self):
        """Test updating stack"""
        tracker = StackTracker()
        tracker.update_stack("Alice", 100.0)
        assert tracker.get_stack("Alice") == 100.0

    def test_take_snapshot(self):
        """Test taking snapshot"""
        tracker = StackTracker()
        tracker.update_stack("Alice", 100.0)
        snapshot = tracker.take_snapshot()

        assert snapshot.snapshot_id == 1
        assert snapshot.player_stacks["Alice"] == 100.0

    def test_get_stack_change(self):
        """Test calculating stack change"""
        tracker = StackTracker()
        tracker.update_stack("Alice", 100.0)
        tracker.take_snapshot()
        tracker.update_stack("Alice", 150.0)

        change = tracker.get_stack_change("Alice")
        assert change == 50.0

    def test_get_biggest_stack(self):
        """Test finding biggest stack"""
        tracker = StackTracker()
        tracker.update_stack("Alice", 100.0)
        tracker.update_stack("Bob", 200.0)
        tracker.update_stack("Charlie", 150.0)

        player, stack = tracker.get_biggest_stack()
        assert player == "Bob"
        assert stack == 200.0

    def test_statistics(self):
        """Test statistics generation"""
        tracker = StackTracker()
        tracker.update_stack("Alice", 100.0)
        tracker.update_stack("Bob", 200.0)

        stats = tracker.get_statistics()
        assert stats["total_players"] == 2
        assert stats["total_chips"] == 300.0
        assert stats["avg_stack"] == 150.0

    def test_reset(self):
        """Test reset"""
        tracker = StackTracker()
        tracker.update_stack("Alice", 100.0)
        tracker.take_snapshot()

        tracker.reset()
        assert len(tracker.current_stacks) == 0
        assert len(tracker.snapshots) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
