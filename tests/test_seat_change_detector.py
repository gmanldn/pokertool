#!/usr/bin/env python3
"""Tests for Seat Change Detector"""

import pytest
from src.pokertool.seat_change_detector import SeatChangeDetector, SeatChange


class TestSeatChangeDetector:
    """Test suite for SeatChangeDetector"""

    def test_initialization(self):
        """Test detector initialization"""
        detector = SeatChangeDetector(table_size=9)
        assert detector.table_size == 9
        assert len(detector.player_seats) == 0
        assert len(detector.change_history) == 0

    def test_first_player_seat(self):
        """Test first seat assignment returns None"""
        detector = SeatChangeDetector()
        change = detector.update_player_seat("Alice", 0)
        assert change is None
        assert detector.get_player_seat("Alice") == 0

    def test_seat_change_detection(self):
        """Test seat change is detected"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        change = detector.update_player_seat("Alice", 3)

        assert change is not None
        assert change.player_name == "Alice"
        assert change.old_seat == 0
        assert change.new_seat == 3

    def test_no_change_same_seat(self):
        """Test no change when seat stays same"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        change = detector.update_player_seat("Alice", 0)

        assert change is None

    def test_multiple_players(self):
        """Test tracking multiple players"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        detector.update_player_seat("Bob", 1)
        detector.update_player_seat("Charlie", 2)

        assert detector.get_player_seat("Alice") == 0
        assert detector.get_player_seat("Bob") == 1
        assert detector.get_player_seat("Charlie") == 2

    def test_get_seat_occupant(self):
        """Test getting player at seat"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 3)
        detector.update_player_seat("Bob", 5)

        assert detector.get_seat_occupant(3) == "Alice"
        assert detector.get_seat_occupant(5) == "Bob"
        assert detector.get_seat_occupant(7) is None

    def test_get_player_changes(self):
        """Test getting changes for specific player"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        detector.update_player_seat("Alice", 3)
        detector.update_player_seat("Alice", 5)

        changes = detector.get_player_changes("Alice")
        assert len(changes) == 2

    def test_change_id_increment(self):
        """Test change IDs increment"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        c1 = detector.update_player_seat("Alice", 1)
        c2 = detector.update_player_seat("Alice", 2)

        assert c1.change_id == 1
        assert c2.change_id == 2

    def test_statistics(self):
        """Test statistics generation"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        detector.update_player_seat("Bob", 1)
        detector.update_player_seat("Alice", 3)

        stats = detector.get_statistics()
        assert stats["total_changes"] == 1
        assert stats["unique_players"] == 2
        assert stats["most_active_player"] == "Alice"

    def test_invalid_seat_number(self):
        """Test invalid seat number"""
        detector = SeatChangeDetector(table_size=9)
        change = detector.update_player_seat("Alice", 10)
        assert change is None

    def test_reset(self):
        """Test reset clears all data"""
        detector = SeatChangeDetector()
        detector.update_player_seat("Alice", 0)
        detector.update_player_seat("Alice", 3)

        detector.reset()
        assert len(detector.player_seats) == 0
        assert len(detector.change_history) == 0
        assert detector.change_count == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
