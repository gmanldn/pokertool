"""Tests for position calculation."""

import pytest
from pokertool.position_calculator import PositionCalculator


class TestPositionCalculator:
    """Test position calculation functionality."""

    def test_button_position_6max(self):
        """Test button position in 6-max."""
        pos = PositionCalculator.calculate_position(seat_number=0, button_seat=0, total_seats=6)
        assert pos == "UTG"  # Offset 0 = UTG in POSITIONS_6MAX

    def test_sb_position_6max(self):
        """Test small blind position in 6-max."""
        pos = PositionCalculator.calculate_position(seat_number=4, button_seat=0, total_seats=6)
        assert pos == "SB"

    def test_bb_position_6max(self):
        """Test big blind position in 6-max."""
        pos = PositionCalculator.calculate_position(seat_number=5, button_seat=0, total_seats=6)
        assert pos == "BB"

    def test_utg_position_6max(self):
        """Test UTG position in 6-max."""
        pos = PositionCalculator.calculate_position(seat_number=0, button_seat=0, total_seats=6)
        assert pos == "UTG"

    def test_co_position_6max(self):
        """Test cutoff position in 6-max."""
        pos = PositionCalculator.calculate_position(seat_number=2, button_seat=0, total_seats=6)
        assert pos == "CO"

    def test_utg_position_9max(self):
        """Test UTG position in 9-max."""
        pos = PositionCalculator.calculate_position(seat_number=3, button_seat=3, total_seats=9)
        assert pos == "UTG"

    def test_is_early_position(self):
        """Test early position detection."""
        assert PositionCalculator.is_early_position("UTG") is True
        assert PositionCalculator.is_early_position("UTG+1") is True
        assert PositionCalculator.is_early_position("BTN") is False

    def test_is_late_position(self):
        """Test late position detection."""
        assert PositionCalculator.is_late_position("BTN") is True
        assert PositionCalculator.is_late_position("CO") is True
        assert PositionCalculator.is_late_position("UTG") is False

    def test_position_6max_list(self):
        """Test 6-max position list."""
        assert len(PositionCalculator.POSITIONS_6MAX) == 6
        assert "BTN" in PositionCalculator.POSITIONS_6MAX
        assert "SB" in PositionCalculator.POSITIONS_6MAX
