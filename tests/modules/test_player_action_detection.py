"""Tests for player action detection in player_action_detector.py"""

import pytest
import numpy as np
import cv2
from pokertool.player_action_detector import (
    PlayerActionDetector,
    PlayerAction,
    ActionDetection
)


class TestPlayerActionDetection:
    """Test player action detection functionality."""

    def test_fold_detection_dimmed_area(self):
        """Test fold detection via dimmed player area."""
        detector = PlayerActionDetector()
        # Create dark/dimmed image
        player_area = np.ones((100, 100, 3), dtype=np.uint8) * 30

        result = detector._detect_fold_visual(player_area)
        assert result is True

    def test_fold_detection_red_x_pattern(self):
        """Test fold detection via red X pattern."""
        detector = PlayerActionDetector()
        # Create image with red X
        player_area = np.zeros((100, 100, 3), dtype=np.uint8)
        player_area[:, :, 2] = 200  # Red channel

        result = detector._detect_fold_visual(player_area)
        assert result is True

    def test_check_action_parsing(self):
        """Test parsing of check action from text."""
        detector = PlayerActionDetector()

        action = detector._parse_action_text("CHECK")
        assert action == PlayerAction.CHECK

    def test_call_action_parsing(self):
        """Test parsing of call action from text."""
        detector = PlayerActionDetector()

        action = detector._parse_action_text("CALL")
        assert action == PlayerAction.CALL

    def test_bet_action_parsing(self):
        """Test parsing of bet action from text."""
        detector = PlayerActionDetector()

        action = detector._parse_action_text("BET")
        assert action == PlayerAction.BET

    def test_raise_action_parsing(self):
        """Test parsing of raise action from text."""
        detector = PlayerActionDetector()

        action = detector._parse_action_text("RAISE")
        assert action == PlayerAction.RAISE

    def test_all_in_action_parsing(self):
        """Test parsing of all-in action from text."""
        detector = PlayerActionDetector()

        action = detector._parse_action_text("ALL IN")
        assert action == PlayerAction.ALL_IN

    def test_action_history_recording(self):
        """Test that actions are recorded in history."""
        detector = PlayerActionDetector()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)

        detection = detector.detect_player_action(
            image=image,
            seat_number=1,
            player_roi=(0, 0, 100, 100),
            previous_stack=1000.0,
            current_stack=500.0
        )

        assert len(detector.action_history) == 1
        assert detector.action_history[0].player_seat == 1

    def test_get_player_last_action(self):
        """Test retrieving last action for a player."""
        detector = PlayerActionDetector()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)

        detector.detect_player_action(
            image=image,
            seat_number=2,
            player_roi=(0, 0, 100, 100),
            previous_stack=1000.0,
            current_stack=700.0
        )

        last_action = detector.get_player_last_action(2)
        assert last_action is not None
        assert last_action.player_seat == 2

    def test_action_summary(self):
        """Test action summary generation."""
        detector = PlayerActionDetector()

        summary = detector.get_action_summary()
        assert PlayerAction.FOLD.value in summary
        assert PlayerAction.CHECK.value in summary
        assert all(count >= 0 for count in summary.values())
