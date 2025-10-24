"""Tests for bet sizing detection in player_action_detector.py"""

import pytest
import numpy as np
from pokertool.player_action_detector import (
    PlayerActionDetector,
    PlayerAction,
    ActionDetection
)


class TestBetSizingDetection:
    """Test bet sizing detection from player action detector."""

    def test_small_bet_detection(self):
        """Test detection of small bets (< 10% of stack)."""
        detector = PlayerActionDetector()
        previous_stack = 1000.0
        current_stack = 950.0

        action = detector._infer_action_from_stack_change(
            stack_delta=50.0,
            previous_stack=previous_stack,
            current_stack=current_stack
        )

        assert action == PlayerAction.CALL

    def test_medium_bet_detection(self):
        """Test detection of medium bets (10-50% of stack)."""
        detector = PlayerActionDetector()
        previous_stack = 1000.0
        current_stack = 700.0

        action = detector._infer_action_from_stack_change(
            stack_delta=300.0,
            previous_stack=previous_stack,
            current_stack=current_stack
        )

        assert action == PlayerAction.RAISE

    def test_all_in_detection(self):
        """Test all-in detection (stack goes to 0)."""
        detector = PlayerActionDetector()
        previous_stack = 500.0
        current_stack = 0.0

        action = detector._infer_action_from_stack_change(
            stack_delta=500.0,
            previous_stack=previous_stack,
            current_stack=current_stack
        )

        assert action == PlayerAction.ALL_IN

    def test_no_bet_check_detection(self):
        """Test check detection (no stack change)."""
        detector = PlayerActionDetector()

        action = detector._infer_action_from_stack_change(
            stack_delta=0.0,
            previous_stack=1000.0,
            current_stack=1000.0
        )

        assert action == PlayerAction.CHECK

    def test_bet_amount_recording(self):
        """Test that bet amounts are correctly recorded."""
        detector = PlayerActionDetector()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)

        detection = detector.detect_player_action(
            image=image,
            seat_number=1,
            player_roi=(0, 0, 100, 100),
            previous_stack=1000.0,
            current_stack=700.0
        )

        assert detection is not None
        assert detection.amount == 300.0
        assert detection.action in [PlayerAction.RAISE, PlayerAction.BET]

    def test_small_bet_boundary_5_percent(self):
        """Test bet at 5% of stack boundary."""
        detector = PlayerActionDetector()

        action = detector._infer_action_from_stack_change(
            stack_delta=50.0,
            previous_stack=1000.0,
            current_stack=950.0
        )

        assert action == PlayerAction.CALL

    def test_large_bet_boundary_50_percent(self):
        """Test bet at 50% of stack boundary."""
        detector = PlayerActionDetector()

        action = detector._infer_action_from_stack_change(
            stack_delta=500.0,
            previous_stack=1000.0,
            current_stack=500.0
        )

        assert action == PlayerAction.RAISE

    def test_minimum_bet_detection(self):
        """Test minimum bet detection (blinds level)."""
        detector = PlayerActionDetector()

        action = detector._infer_action_from_stack_change(
            stack_delta=2.0,
            previous_stack=1000.0,
            current_stack=998.0
        )

        assert action == PlayerAction.CALL

    def test_pot_sized_bet_detection(self):
        """Test pot-sized bet detection."""
        detector = PlayerActionDetector()

        action = detector._infer_action_from_stack_change(
            stack_delta=400.0,
            previous_stack=1000.0,
            current_stack=600.0
        )

        assert action == PlayerAction.RAISE

    def test_overbet_detection(self):
        """Test overbet detection (>100% pot)."""
        detector = PlayerActionDetector()

        action = detector._infer_action_from_stack_change(
            stack_delta=800.0,
            previous_stack=1000.0,
            current_stack=200.0
        )

        assert action == PlayerAction.RAISE
