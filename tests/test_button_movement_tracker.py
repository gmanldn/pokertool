#!/usr/bin/env python3
"""Tests for Button Movement Tracker"""

import pytest
from src.pokertool.button_movement_tracker import (
    ButtonMovementTracker,
    MovementType,
    ButtonMovement
)


class TestButtonMovementTracker:
    """Test suite for ButtonMovementTracker"""

    def test_initialization(self):
        """Test tracker initialization"""
        tracker = ButtonMovementTracker(table_size=9)
        assert tracker.table_size == 9
        assert tracker.current_button_seat is None
        assert len(tracker.movement_history) == 0
        assert tracker.hands_tracked == 0
        assert tracker.frame_count == 0

    def test_initial_position_detection(self):
        """Test detection of initial button position"""
        tracker = ButtonMovementTracker()
        movement = tracker.update_button_position(0, confidence=0.95)

        assert movement is not None
        assert movement.movement_type == MovementType.INITIAL
        assert movement.new_seat == 0
        assert movement.previous_seat is None
        assert movement.seats_moved == 0
        assert movement.confidence == 0.95

    def test_normal_movement_detection(self):
        """Test detection of normal clockwise movement"""
        tracker = ButtonMovementTracker(table_size=9)
        tracker.update_button_position(0)  # Initial
        movement = tracker.update_button_position(1)  # Normal move

        assert movement.movement_type == MovementType.NORMAL
        assert movement.seats_moved == 1
        assert movement.previous_seat == 0
        assert movement.new_seat == 1

    def test_skip_seats_detection(self):
        """Test detection of button skipping seats"""
        tracker = ButtonMovementTracker(table_size=9)
        tracker.update_button_position(0)  # Initial
        movement = tracker.update_button_position(3)  # Skip 2 seats

        assert movement.movement_type == MovementType.SKIP
        assert movement.seats_moved == 3
        assert movement.new_seat == 3

    def test_backward_movement_detection(self):
        """Test detection of backward button movement"""
        tracker = ButtonMovementTracker(table_size=9)
        tracker.update_button_position(5)  # Initial
        movement = tracker.update_button_position(3)  # Backward 2 seats

        assert movement.movement_type == MovementType.BACKWARD
        assert movement.seats_moved == -2
        assert movement.new_seat == 3

    def test_no_movement_detection(self):
        """Test that same position returns None"""
        tracker = ButtonMovementTracker()
        tracker.update_button_position(0)
        movement = tracker.update_button_position(0)  # Same position

        assert movement is None

    def test_wrap_around_normal(self):
        """Test normal movement wrapping around table"""
        tracker = ButtonMovementTracker(table_size=9)
        tracker.update_button_position(8)  # Initial at last seat
        movement = tracker.update_button_position(0)  # Wrap to first seat

        assert movement.movement_type == MovementType.NORMAL
        assert movement.seats_moved == 1

    def test_get_current_position(self):
        """Test getting current button position"""
        tracker = ButtonMovementTracker()
        assert tracker.get_current_position() is None

        tracker.update_button_position(5)
        assert tracker.get_current_position() == 5

        tracker.update_button_position(6)
        assert tracker.get_current_position() == 6

    def test_get_recent_movements(self):
        """Test retrieval of recent movements"""
        tracker = ButtonMovementTracker()

        for i in range(5):
            tracker.update_button_position(i)

        recent = tracker.get_recent_movements(count=3)
        assert len(recent) == 3
        assert recent[-1].new_seat == 4  # Most recent

    def test_get_movements_by_type(self):
        """Test filtering movements by type"""
        tracker = ButtonMovementTracker(table_size=9)

        tracker.update_button_position(0)  # INITIAL
        tracker.update_button_position(1)  # NORMAL
        tracker.update_button_position(2)  # NORMAL
        tracker.update_button_position(5)  # SKIP

        initial = tracker.get_movements_by_type(MovementType.INITIAL)
        normal = tracker.get_movements_by_type(MovementType.NORMAL)
        skip = tracker.get_movements_by_type(MovementType.SKIP)

        assert len(initial) == 1
        assert len(normal) == 2
        assert len(skip) == 1

    def test_get_position_frequency(self):
        """Test position frequency calculation"""
        tracker = ButtonMovementTracker()

        tracker.update_button_position(0)
        tracker.update_button_position(1)
        tracker.update_button_position(2)
        tracker.update_button_position(0)  # Back to 0
        tracker.update_button_position(1)  # Back to 1

        frequency = tracker.get_position_frequency()

        assert frequency[0] == 2
        assert frequency[1] == 2
        assert frequency[2] == 1

    def test_detect_anomalies(self):
        """Test anomaly detection"""
        tracker = ButtonMovementTracker(table_size=9)

        tracker.update_button_position(0)  # INITIAL
        tracker.update_button_position(1)  # NORMAL
        tracker.update_button_position(5)  # SKIP (anomaly)
        tracker.update_button_position(3)  # BACKWARD (anomaly)

        anomalies = tracker.detect_anomalies()

        assert len(anomalies) == 2
        assert any(a.movement_type == MovementType.SKIP for a in anomalies)
        assert any(a.movement_type == MovementType.BACKWARD for a in anomalies)

    def test_hands_tracked(self):
        """Test hand counting"""
        tracker = ButtonMovementTracker()

        tracker.update_button_position(0)  # Initial (not counted)
        assert tracker.hands_tracked == 0

        tracker.update_button_position(1)  # Hand 1
        assert tracker.hands_tracked == 1

        tracker.update_button_position(2)  # Hand 2
        assert tracker.hands_tracked == 2

        tracker.update_button_position(3)  # Hand 3
        assert tracker.hands_tracked == 3

    def test_statistics_generation(self):
        """Test statistics calculation"""
        tracker = ButtonMovementTracker(table_size=9)

        tracker.update_button_position(0, confidence=0.95)
        tracker.update_button_position(1, confidence=0.90)
        tracker.update_button_position(2, confidence=0.85)
        tracker.update_button_position(5, confidence=0.80)

        stats = tracker.get_statistics()

        assert stats["total_movements"] == 4
        assert stats["hands_tracked"] == 3  # Excludes initial
        assert stats["current_position"] == 5
        assert stats["table_size"] == 9
        assert stats["anomalies"] == 1  # One skip
        assert "movements_by_type" in stats
        assert "position_frequency" in stats

    def test_empty_tracker_statistics(self):
        """Test statistics on empty tracker"""
        tracker = ButtonMovementTracker()
        stats = tracker.get_statistics()

        assert stats["total_movements"] == 0
        assert stats["hands_tracked"] == 0
        assert stats["current_position"] is None
        assert stats["avg_confidence"] == 0.0
        assert stats["anomalies"] == 0

    def test_realistic_session(self):
        """Test realistic poker session button progression"""
        tracker = ButtonMovementTracker(table_size=9)

        # Play 10 hands with normal progression
        for i in range(10):
            seat = i % 9
            tracker.update_button_position(seat)

        stats = tracker.get_statistics()

        assert stats["total_movements"] == 10
        assert stats["hands_tracked"] == 9  # Excludes initial
        assert stats["current_position"] == 0  # Wrapped back around
        assert stats["anomalies"] == 0  # No skips or backwards

    def test_confidence_tracking(self):
        """Test that confidence scores are tracked"""
        tracker = ButtonMovementTracker()

        m1 = tracker.update_button_position(0, confidence=0.95)
        m2 = tracker.update_button_position(1, confidence=0.85)
        m3 = tracker.update_button_position(2, confidence=0.75)

        assert m1.confidence == 0.95
        assert m2.confidence == 0.85
        assert m3.confidence == 0.75

    def test_frame_number_increment(self):
        """Test that frame numbers increment correctly"""
        tracker = ButtonMovementTracker()

        m1 = tracker.update_button_position(0)
        m2 = tracker.update_button_position(1)
        m3 = tracker.update_button_position(2)

        assert m1.frame_number == 1
        assert m2.frame_number == 2
        assert m3.frame_number == 3

    def test_reset_functionality(self):
        """Test tracker reset"""
        tracker = ButtonMovementTracker()

        tracker.update_button_position(0)
        tracker.update_button_position(1)
        tracker.update_button_position(2)

        assert len(tracker.movement_history) == 3
        assert tracker.hands_tracked == 2

        tracker.reset()

        assert tracker.current_button_seat is None
        assert len(tracker.movement_history) == 0
        assert tracker.hands_tracked == 0
        assert tracker.frame_count == 0

    def test_invalid_seat_number(self):
        """Test handling of invalid seat numbers"""
        tracker = ButtonMovementTracker(table_size=9)

        # Too high
        movement1 = tracker.update_button_position(10)
        assert movement1 is None

        # Negative
        movement2 = tracker.update_button_position(-1)
        assert movement2 is None

    def test_table_size_override(self):
        """Test table size override"""
        tracker = ButtonMovementTracker(table_size=9)

        # Override to 6-max
        movement = tracker.update_button_position(5, table_size=6)
        assert tracker.table_size == 6
        assert movement is not None

    def test_different_table_sizes(self):
        """Test tracking with different table sizes"""
        # 6-max table
        tracker_6max = ButtonMovementTracker(table_size=6)
        tracker_6max.update_button_position(0)
        tracker_6max.update_button_position(1)
        assert tracker_6max.movement_history[-1].table_size == 6

        # Heads-up table
        tracker_hu = ButtonMovementTracker(table_size=2)
        tracker_hu.update_button_position(0)
        tracker_hu.update_button_position(1)
        assert tracker_hu.movement_history[-1].table_size == 2

    def test_complex_movement_pattern(self):
        """Test complex movement pattern with skips and normal moves"""
        tracker = ButtonMovementTracker(table_size=9)

        tracker.update_button_position(0)  # Initial
        tracker.update_button_position(1)  # Normal
        tracker.update_button_position(2)  # Normal
        tracker.update_button_position(5)  # Skip 3 seats
        tracker.update_button_position(6)  # Normal
        tracker.update_button_position(8)  # Skip 2 seats
        tracker.update_button_position(0)  # Wrap normal
        tracker.update_button_position(3)  # Skip 3 seats

        stats = tracker.get_statistics()

        assert stats["total_movements"] == 8
        assert stats["movements_by_type"]["normal"] == 4
        assert stats["movements_by_type"]["skip"] == 3
        assert stats["anomalies"] == 3  # 3 skips


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
