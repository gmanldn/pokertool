#!/usr/bin/env python3
"""Tests for Hand History Formatter"""

import pytest
from src.pokertool.hand_history_formatter import HandHistoryFormatter


class TestHandHistoryFormatter:
    """Test suite for HandHistoryFormatter"""

    def test_initialization(self):
        """Test formatter initialization"""
        formatter = HandHistoryFormatter()
        assert len(formatter.histories) == 0

    def test_add_hand(self):
        """Test adding hand"""
        formatter = HandHistoryFormatter()
        hand = formatter.add_hand(["Alice", "Bob"], ["Alice raises"], "Alice", 10.0)

        assert hand.hand_id == 1
        assert hand.winner == "Alice"
        assert len(formatter.histories) == 1

    def test_format_hand(self):
        """Test formatting hand"""
        formatter = HandHistoryFormatter()
        hand = formatter.add_hand(["Alice"], ["Alice wins"], "Alice", 5.0)

        formatted = formatter.format_hand(hand)
        assert "Hand #1" in formatted
        assert "Alice wins" in formatted

    def test_export_all(self):
        """Test exporting all hands"""
        formatter = HandHistoryFormatter()
        formatter.add_hand(["Alice"], ["Alice wins"], "Alice", 10.0)
        formatter.add_hand(["Bob"], ["Bob wins"], "Bob", 15.0)

        export = formatter.export_all()
        assert "Hand #1" in export
        assert "Hand #2" in export

    def test_export_summary(self):
        """Test export summary"""
        formatter = HandHistoryFormatter()
        formatter.add_hand(["Alice"], [], "Alice", 10.0)
        formatter.add_hand(["Bob"], [], "Bob", 20.0)

        summary = formatter.export_summary()
        assert "Total hands: 2" in summary
        assert "Avg pot: $15.00" in summary

    def test_get_player_hands(self):
        """Test getting player hands"""
        formatter = HandHistoryFormatter()
        formatter.add_hand(["Alice", "Bob"], [], "Alice", 10.0)
        formatter.add_hand(["Bob", "Charlie"], [], "Bob", 15.0)

        alice_hands = formatter.get_player_hands("Alice")
        assert len(alice_hands) == 1

    def test_reset(self):
        """Test reset"""
        formatter = HandHistoryFormatter()
        formatter.add_hand(["Alice"], [], "Alice", 10.0)
        formatter.reset()

        assert len(formatter.histories) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
