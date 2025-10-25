#!/usr/bin/env python3
"""Tests for Board Change Detector"""

import pytest
from src.pokertool.board_change_detector import (
    BoardChangeDetector,
    BoardChangeType,
    Street,
    BoardChange,
    BoardState
)


class TestBoardChangeDetector:
    """Test suite for BoardChangeDetector"""

    def test_initialization(self):
        """Test detector initialization"""
        detector = BoardChangeDetector()
        assert len(detector.current_board) == 0
        assert detector.current_street == Street.PREFLOP
        assert len(detector.change_history) == 0
        assert len(detector.state_history) == 0
        assert detector.frame_count == 0

    def test_flop_deal_detection(self):
        """Test detection of flop deal"""
        detector = BoardChangeDetector()
        change = detector.update_board(["As", "Kd", "Qh"], confidence=0.95)

        assert change is not None
        assert change.change_type == BoardChangeType.FLOP_DEAL
        assert change.new_street == Street.FLOP
        assert len(change.new_cards) == 3
        assert len(change.added_cards) == 3
        assert change.confidence == 0.95

    def test_turn_deal_detection(self):
        """Test detection of turn card"""
        detector = BoardChangeDetector()
        detector.update_board(["As", "Kd", "Qh"])  # Flop
        change = detector.update_board(["As", "Kd", "Qh", "Jc"])  # Turn

        assert change.change_type == BoardChangeType.TURN_DEAL
        assert change.new_street == Street.TURN
        assert len(change.added_cards) == 1
        assert change.added_cards[0] == "Jc"

    def test_river_deal_detection(self):
        """Test detection of river card"""
        detector = BoardChangeDetector()
        detector.update_board(["As", "Kd", "Qh"])  # Flop
        detector.update_board(["As", "Kd", "Qh", "Jc"])  # Turn
        change = detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])  # River

        assert change.change_type == BoardChangeType.RIVER_DEAL
        assert change.new_street == Street.RIVER
        assert len(change.added_cards) == 1
        assert change.added_cards[0] == "Ts"

    def test_board_clear_detection(self):
        """Test detection of board clear (new hand)"""
        detector = BoardChangeDetector()
        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])  # Full board
        change = detector.update_board([])  # Clear

        assert change.change_type == BoardChangeType.BOARD_CLEAR
        assert change.new_street == Street.PREFLOP
        assert len(change.new_cards) == 0

    def test_no_change_detection(self):
        """Test that identical boards return None"""
        detector = BoardChangeDetector()
        detector.update_board(["As", "Kd", "Qh"])
        change = detector.update_board(["As", "Kd", "Qh"])  # Same board

        assert change is None

    def test_duplicate_card_handling(self):
        """Test handling of duplicate cards in board"""
        detector = BoardChangeDetector()
        change = detector.update_board(["As", "As", "Kd", "Qh"])  # Duplicate As

        # Should remove duplicate
        assert len(change.new_cards) == 3
        assert change.new_cards.count("As") == 1

    def test_get_current_board(self):
        """Test getting current board state"""
        detector = BoardChangeDetector()
        detector.update_board(["As", "Kd", "Qh"])

        board = detector.get_current_board()
        assert board == ["As", "Kd", "Qh"]
        # Ensure it's a copy
        board.append("Jc")
        assert len(detector.current_board) == 3

    def test_get_current_street(self):
        """Test getting current street"""
        detector = BoardChangeDetector()

        assert detector.get_current_street() == Street.PREFLOP

        detector.update_board(["As", "Kd", "Qh"])
        assert detector.get_current_street() == Street.FLOP

        detector.update_board(["As", "Kd", "Qh", "Jc"])
        assert detector.get_current_street() == Street.TURN

        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])
        assert detector.get_current_street() == Street.RIVER

    def test_is_complete_board(self):
        """Test checking if board is complete"""
        detector = BoardChangeDetector()

        assert not detector.is_complete_board()

        detector.update_board(["As", "Kd", "Qh"])
        assert not detector.is_complete_board()

        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])
        assert detector.is_complete_board()

    def test_get_recent_changes(self):
        """Test retrieval of recent changes"""
        detector = BoardChangeDetector()

        detector.update_board(["As", "Kd", "Qh"])  # Flop
        detector.update_board(["As", "Kd", "Qh", "Jc"])  # Turn
        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])  # River

        recent = detector.get_recent_changes(count=2)
        assert len(recent) == 2
        assert recent[-1].change_type == BoardChangeType.RIVER_DEAL

    def test_get_changes_by_type(self):
        """Test filtering changes by type"""
        detector = BoardChangeDetector()

        detector.update_board(["As", "Kd", "Qh"])  # Flop
        detector.update_board(["As", "Kd", "Qh", "Jc"])  # Turn
        detector.update_board([])  # Clear
        detector.update_board(["2c", "3c", "4c"])  # Flop

        flops = detector.get_changes_by_type(BoardChangeType.FLOP_DEAL)
        turns = detector.get_changes_by_type(BoardChangeType.TURN_DEAL)
        clears = detector.get_changes_by_type(BoardChangeType.BOARD_CLEAR)

        assert len(flops) == 2
        assert len(turns) == 1
        assert len(clears) == 1

    def test_get_hand_progression(self):
        """Test getting full hand progression"""
        detector = BoardChangeDetector()

        detector.update_board(["As", "Kd", "Qh"])
        detector.update_board(["As", "Kd", "Qh", "Jc"])
        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])

        progression = detector.get_hand_progression()
        assert len(progression) == 3
        assert progression[0].street == Street.FLOP
        assert progression[1].street == Street.TURN
        assert progression[2].street == Street.RIVER

    def test_statistics_generation(self):
        """Test statistics calculation"""
        detector = BoardChangeDetector()

        detector.update_board(["As", "Kd", "Qh"], confidence=0.95)
        detector.update_board(["As", "Kd", "Qh", "Jc"], confidence=0.90)
        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"], confidence=0.85)
        detector.update_board([])  # New hand

        stats = detector.get_statistics()

        assert stats["total_changes"] == 4
        assert stats["avg_confidence"] == 0.925  # (0.95 + 0.90 + 0.85 + 1.00) / 4
        assert stats["hands_tracked"] == 1
        assert "changes_by_type" in stats
        assert "changes_by_street" in stats

    def test_empty_detector_statistics(self):
        """Test statistics on empty detector"""
        detector = BoardChangeDetector()
        stats = detector.get_statistics()

        assert stats["total_changes"] == 0
        assert stats["avg_confidence"] == 0.0
        assert stats["hands_tracked"] == 0

    def test_realistic_hand_sequence(self):
        """Test realistic poker hand board progression"""
        detector = BoardChangeDetector()

        # Hand 1
        flop = detector.update_board(["Ah", "Kh", "Qh"])
        turn = detector.update_board(["Ah", "Kh", "Qh", "Jh"])
        river = detector.update_board(["Ah", "Kh", "Qh", "Jh", "Th"])
        clear = detector.update_board([])

        # Hand 2
        flop2 = detector.update_board(["2c", "3d", "4s"])
        turn2 = detector.update_board(["2c", "3d", "4s", "5h"])

        assert flop.change_type == BoardChangeType.FLOP_DEAL
        assert turn.change_type == BoardChangeType.TURN_DEAL
        assert river.change_type == BoardChangeType.RIVER_DEAL
        assert clear.change_type == BoardChangeType.BOARD_CLEAR
        assert flop2.change_type == BoardChangeType.FLOP_DEAL
        assert turn2.change_type == BoardChangeType.TURN_DEAL

        stats = detector.get_statistics()
        assert stats["total_changes"] == 6
        assert stats["hands_tracked"] == 1

    def test_confidence_tracking(self):
        """Test that confidence scores are tracked"""
        detector = BoardChangeDetector()

        change1 = detector.update_board(["As", "Kd", "Qh"], confidence=0.95)
        change2 = detector.update_board(["As", "Kd", "Qh", "Jc"], confidence=0.85)
        change3 = detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"], confidence=0.75)

        assert change1.confidence == 0.95
        assert change2.confidence == 0.85
        assert change3.confidence == 0.75

    def test_frame_number_increment(self):
        """Test that frame numbers increment correctly"""
        detector = BoardChangeDetector()

        change1 = detector.update_board(["As", "Kd", "Qh"])
        change2 = detector.update_board(["As", "Kd", "Qh", "Jc"])
        change3 = detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])

        assert change1.frame_number == 1
        assert change2.frame_number == 2
        assert change3.frame_number == 3

    def test_reset_functionality(self):
        """Test detector reset"""
        detector = BoardChangeDetector()

        detector.update_board(["As", "Kd", "Qh"])
        detector.update_board(["As", "Kd", "Qh", "Jc"])

        assert len(detector.change_history) == 2
        assert len(detector.state_history) == 2
        assert detector.frame_count == 2

        detector.reset()

        assert len(detector.current_board) == 0
        assert len(detector.change_history) == 0
        assert len(detector.state_history) == 0
        assert detector.frame_count == 0
        assert detector.current_street == Street.PREFLOP

    def test_street_progression(self):
        """Test that streets progress correctly"""
        detector = BoardChangeDetector()

        change1 = detector.update_board(["As", "Kd", "Qh"])
        assert change1.previous_street == Street.PREFLOP
        assert change1.new_street == Street.FLOP

        change2 = detector.update_board(["As", "Kd", "Qh", "Jc"])
        assert change2.previous_street == Street.FLOP
        assert change2.new_street == Street.TURN

        change3 = detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])
        assert change3.previous_street == Street.TURN
        assert change3.new_street == Street.RIVER

    def test_multiple_hands_tracking(self):
        """Test tracking multiple complete hands"""
        detector = BoardChangeDetector()

        # Hand 1
        detector.update_board(["As", "Kd", "Qh"])
        detector.update_board(["As", "Kd", "Qh", "Jc"])
        detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"])
        detector.update_board([])  # Clear

        # Hand 2
        detector.update_board(["2c", "3c", "4c"])
        detector.update_board(["2c", "3c", "4c", "5c"])
        detector.update_board([])  # Clear

        # Hand 3
        detector.update_board(["7d", "8d", "9d"])

        stats = detector.get_statistics()
        assert stats["hands_tracked"] == 2  # Two clears = 2 completed hands
        assert stats["total_changes"] == 8  # 3 (hand1) + 3 (hand2) + 2 (clears) = 8

    def test_card_format_consistency(self):
        """Test that card formats are preserved"""
        detector = BoardChangeDetector()

        cards = ["Ah", "Kd", "Qc", "Js", "Th"]
        change = detector.update_board(cards)

        assert change.new_cards == cards
        assert detector.get_current_board() == cards


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
