#!/usr/bin/env python3
"""Tests for Player Action Detector"""

import pytest
from src.pokertool.player_action_detector import (
    PlayerActionDetector,
    PlayerAction,
    DetectedAction
)


class TestPlayerActionDetector:
    """Test suite for PlayerActionDetector"""

    def test_initialization(self):
        """Test detector initialization"""
        detector = PlayerActionDetector(min_bet_amount=0.01)
        assert detector.min_bet_amount == 0.01
        assert len(detector.action_history) == 0
        assert detector.frame_count == 0

    def test_fold_detection(self):
        """Test detection of fold action"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="UTG",
            stack_before=100.0,
            stack_after=100.0,
            pot_before=3.0,
            pot_after=3.0,
            facing_bet=True
        )

        assert action.action == PlayerAction.FOLD
        assert action.amount is None
        assert action.player_position == "UTG"

    def test_check_detection(self):
        """Test detection of check action"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="BB",
            stack_before=100.0,
            stack_after=100.0,
            pot_before=5.0,
            pot_after=5.0,
            facing_bet=False
        )

        assert action.action == PlayerAction.CHECK
        assert action.amount is None

    def test_bet_detection(self):
        """Test detection of bet action"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="BTN",
            stack_before=100.0,
            stack_after=90.0,
            pot_before=3.0,
            pot_after=13.0,
            facing_bet=False
        )

        assert action.action == PlayerAction.BET
        assert action.amount == 10.0

    def test_call_detection(self):
        """Test detection of call action"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="BB",
            stack_before=100.0,
            stack_after=90.0,
            pot_before=13.0,
            pot_after=23.0,
            facing_bet=True
        )

        assert action.action == PlayerAction.CALL
        assert action.amount == 10.0

    def test_raise_detection(self):
        """Test detection of raise action"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="SB",
            stack_before=100.0,
            stack_after=70.0,
            pot_before=13.0,
            pot_after=43.0,
            facing_bet=True
        )

        assert action.action == PlayerAction.RAISE
        assert action.amount == 30.0

    def test_all_in_detection(self):
        """Test detection of all-in action"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="BTN",
            stack_before=50.0,
            stack_after=0.0,
            pot_before=20.0,
            pot_after=70.0,
            facing_bet=True
        )

        assert action.action == PlayerAction.ALL_IN
        assert action.amount == 50.0
        assert action.stack_after == 0.0

    def test_small_blind_post_detection(self):
        """Test detection of small blind post"""
        detector = PlayerActionDetector()
        action = detector.detect_action(
            player_position="SB",
            stack_before=100.0,
            stack_after=99.5,
            pot_before=0.0,
            pot_after=0.5
        )

        assert action.action == PlayerAction.POST_SB
        assert action.amount == 0.5

    def test_big_blind_post_detection(self):
        """Test detection of big blind post"""
        detector = PlayerActionDetector()
        # First SB posts
        detector.detect_action("SB", 100.0, 99.5, 0.0, 0.5)
        # Then BB posts
        action = detector.detect_action(
            player_position="BB",
            stack_before=100.0,
            stack_after=99.0,
            pot_before=0.5,
            pot_after=1.5
        )

        assert action.action == PlayerAction.POST_BB
        assert action.amount == 1.0

    def test_get_player_actions(self):
        """Test filtering actions by player"""
        detector = PlayerActionDetector()

        detector.detect_action("BTN", 100.0, 90.0, 0.0, 10.0, facing_bet=False)
        detector.detect_action("SB", 100.0, 90.0, 10.0, 20.0, facing_bet=True)
        detector.detect_action("BTN", 90.0, 70.0, 20.0, 40.0, facing_bet=True)

        btn_actions = detector.get_player_actions("BTN")
        assert len(btn_actions) == 2
        assert all(a.player_position == "BTN" for a in btn_actions)

    def test_get_actions_by_type(self):
        """Test filtering actions by type"""
        detector = PlayerActionDetector()

        detector.detect_action("BTN", 100.0, 90.0, 0.0, 10.0, facing_bet=False)  # BET
        detector.detect_action("SB", 100.0, 90.0, 10.0, 20.0, facing_bet=True)   # CALL
        detector.detect_action("BB", 100.0, 100.0, 20.0, 20.0, facing_bet=True)  # FOLD

        bets = detector.get_actions_by_type(PlayerAction.BET)
        calls = detector.get_actions_by_type(PlayerAction.CALL)
        folds = detector.get_actions_by_type(PlayerAction.FOLD)

        assert len(bets) == 1
        assert len(calls) == 1
        assert len(folds) == 1

    def test_get_recent_actions(self):
        """Test getting recent actions"""
        detector = PlayerActionDetector()

        # Create 5 actions
        for i in range(5):
            detector.detect_action(
                f"P{i}", 100.0, 90.0, i * 10.0, (i + 1) * 10.0, facing_bet=False
            )

        recent = detector.get_recent_actions(count=3)
        assert len(recent) == 3
        assert recent[-1].player_position == "P4"  # Most recent

    def test_statistics_generation(self):
        """Test statistics calculation"""
        detector = PlayerActionDetector()

        detector.detect_action("BTN", 100.0, 90.0, 0.0, 10.0, facing_bet=False, confidence=0.95)
        detector.detect_action("SB", 100.0, 90.0, 10.0, 20.0, facing_bet=True, confidence=0.90)
        detector.detect_action("BB", 100.0, 100.0, 20.0, 20.0, facing_bet=True, confidence=0.85)

        stats = detector.get_statistics()

        assert stats["total_actions"] == 3
        assert stats["avg_confidence"] == 0.9
        assert "actions_by_type" in stats
        assert "actions_by_position" in stats

    def test_empty_detector_statistics(self):
        """Test statistics on empty detector"""
        detector = PlayerActionDetector()
        stats = detector.get_statistics()

        assert stats["total_actions"] == 0
        assert stats["avg_confidence"] == 0.0
        assert stats["actions_by_type"] == {}

    def test_realistic_hand_sequence(self):
        """Test realistic poker hand action sequence"""
        detector = PlayerActionDetector()

        # Preflop
        detector.detect_action("SB", 100.0, 99.5, 0.0, 0.5)  # Post SB
        detector.detect_action("BB", 100.0, 99.0, 0.5, 1.5)  # Post BB
        detector.detect_action("UTG", 100.0, 100.0, 1.5, 1.5, facing_bet=False)  # Fold
        detector.detect_action("MP", 100.0, 94.0, 1.5, 7.5, facing_bet=False)  # Raise to 6
        detector.detect_action("BTN", 100.0, 94.0, 7.5, 13.5, facing_bet=True)  # Call
        detector.detect_action("SB", 99.5, 99.5, 13.5, 13.5, facing_bet=True)  # Fold
        detector.detect_action("BB", 99.0, 93.0, 13.5, 19.5, facing_bet=True)  # Call

        # Flop
        detector.detect_action("BB", 93.0, 93.0, 19.5, 19.5, facing_bet=False)  # Check
        detector.detect_action("MP", 94.0, 84.0, 19.5, 29.5, facing_bet=False)  # Bet
        detector.detect_action("BTN", 94.0, 94.0, 29.5, 29.5, facing_bet=True)  # Fold

        stats = detector.get_statistics()

        assert stats["total_actions"] == 10
        assert stats["actions_by_type"]["fold"] == 3
        assert stats["actions_by_type"]["call"] == 2

    def test_confidence_tracking(self):
        """Test confidence score tracking"""
        detector = PlayerActionDetector()

        action1 = detector.detect_action("BTN", 100.0, 90.0, 0.0, 10.0, confidence=0.95)
        action2 = detector.detect_action("SB", 100.0, 90.0, 10.0, 20.0, confidence=0.85)

        assert action1.confidence == 0.95
        assert action2.confidence == 0.85

    def test_frame_number_increment(self):
        """Test frame number increments"""
        detector = PlayerActionDetector()

        action1 = detector.detect_action("P1", 100.0, 90.0, 0.0, 10.0)
        action2 = detector.detect_action("P2", 100.0, 90.0, 10.0, 20.0)
        action3 = detector.detect_action("P3", 100.0, 90.0, 20.0, 30.0)

        assert action1.frame_number == 1
        assert action2.frame_number == 2
        assert action3.frame_number == 3

    def test_reset_functionality(self):
        """Test detector reset"""
        detector = PlayerActionDetector()

        detector.detect_action("P1", 100.0, 90.0, 0.0, 10.0)
        detector.detect_action("P2", 100.0, 90.0, 10.0, 20.0)

        assert len(detector.action_history) == 2
        assert detector.frame_count == 2

        detector.reset()

        assert len(detector.action_history) == 0
        assert detector.frame_count == 0

    def test_pot_and_stack_tracking(self):
        """Test that pot and stack sizes are tracked correctly"""
        detector = PlayerActionDetector()

        action = detector.detect_action(
            player_position="BTN",
            stack_before=100.0,
            stack_after=85.0,
            pot_before=20.0,
            pot_after=35.0
        )

        assert action.stack_before == 100.0
        assert action.stack_after == 85.0
        assert action.pot_before == 20.0
        assert action.pot_after == 35.0
        assert action.amount == 15.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
