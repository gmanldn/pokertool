#!/usr/bin/env python3
"""Tests for Win Rate Calculator"""

import pytest
from src.pokertool.win_rate_calculator import (
    WinRateCalculator,
    HandResult,
    HandRecord
)


class TestWinRateCalculator:
    """Test suite for WinRateCalculator"""

    def test_initialization(self):
        """Test calculator initialization"""
        calc = WinRateCalculator()
        assert len(calc.hand_records) == 0
        assert calc.hand_count == 0

    def test_record_win(self):
        """Test recording a win"""
        calc = WinRateCalculator()
        record = calc.record_hand("Alice", HandResult.WIN, 100.0)

        assert record.player_name == "Alice"
        assert record.result == HandResult.WIN
        assert record.amount_won == 100.0
        assert record.hand_id == 1

    def test_record_loss(self):
        """Test recording a loss"""
        calc = WinRateCalculator()
        record = calc.record_hand("Bob", HandResult.LOSS, -50.0)

        assert record.player_name == "Bob"
        assert record.result == HandResult.LOSS
        assert record.amount_won == -50.0

    def test_record_tie(self):
        """Test recording a tie"""
        calc = WinRateCalculator()
        record = calc.record_hand("Charlie", HandResult.TIE, 0.0)

        assert record.result == HandResult.TIE
        assert record.amount_won == 0.0

    def test_record_with_position(self):
        """Test recording hand with position"""
        calc = WinRateCalculator()
        record = calc.record_hand("Alice", HandResult.WIN, 100.0, position="BTN")

        assert record.position == "BTN"

    def test_record_with_hand_type(self):
        """Test recording hand with hand type"""
        calc = WinRateCalculator()
        record = calc.record_hand("Alice", HandResult.WIN, 100.0, hand_type="AA")

        assert record.hand_type == "AA"

    def test_win_rate_100_percent(self):
        """Test win rate calculation for all wins"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.WIN, 50.0)

        win_rate = calc.get_win_rate("Alice")
        assert win_rate == 100.0

    def test_win_rate_0_percent(self):
        """Test win rate calculation for all losses"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.LOSS, -100.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)

        win_rate = calc.get_win_rate("Alice")
        assert win_rate == 0.0

    def test_win_rate_50_percent(self):
        """Test win rate calculation for 50/50"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)

        win_rate = calc.get_win_rate("Alice")
        assert win_rate == 50.0

    def test_win_rate_with_ties(self):
        """Test win rate includes ties in denominator"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.TIE, 0.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)
        calc.record_hand("Alice", HandResult.TIE, 0.0)

        # 1 win out of 4 hands = 25%
        win_rate = calc.get_win_rate("Alice")
        assert win_rate == 25.0

    def test_win_rate_by_position(self):
        """Test win rate filtered by position"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0, position="BTN")
        calc.record_hand("Alice", HandResult.WIN, 50.0, position="BTN")
        calc.record_hand("Alice", HandResult.LOSS, -50.0, position="CO")

        btn_win_rate = calc.get_win_rate(position="BTN")
        assert btn_win_rate == 100.0

    def test_win_rate_by_hand_type(self):
        """Test win rate filtered by hand type"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0, hand_type="AA")
        calc.record_hand("Alice", HandResult.WIN, 75.0, hand_type="AA")
        calc.record_hand("Alice", HandResult.LOSS, -50.0, hand_type="72")

        aa_win_rate = calc.get_win_rate(hand_type="AA")
        assert aa_win_rate == 100.0

    def test_total_hands_count(self):
        """Test total hands counting"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Bob", HandResult.LOSS, -50.0)
        calc.record_hand("Alice", HandResult.TIE, 0.0)

        assert calc.get_total_hands() == 3
        assert calc.get_total_hands(player_name="Alice") == 2
        assert calc.get_total_hands(player_name="Bob") == 1

    def test_wins_count(self):
        """Test wins counting"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.WIN, 50.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)

        assert calc.get_wins(player_name="Alice") == 2

    def test_losses_count(self):
        """Test losses counting"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)
        calc.record_hand("Alice", HandResult.LOSS, -25.0)

        assert calc.get_losses(player_name="Alice") == 2

    def test_ties_count(self):
        """Test ties counting"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.TIE, 0.0)
        calc.record_hand("Alice", HandResult.TIE, 0.0)
        calc.record_hand("Alice", HandResult.WIN, 100.0)

        assert calc.get_ties(player_name="Alice") == 2

    def test_total_winnings(self):
        """Test total winnings calculation"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)
        calc.record_hand("Alice", HandResult.WIN, 75.0)

        total = calc.get_total_winnings(player_name="Alice")
        assert total == 125.0

    def test_total_winnings_negative(self):
        """Test total winnings when losing overall"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 50.0)
        calc.record_hand("Alice", HandResult.LOSS, -100.0)

        total = calc.get_total_winnings(player_name="Alice")
        assert total == -50.0

    def test_avg_win_amount(self):
        """Test average win amount calculation"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.WIN, 50.0)
        calc.record_hand("Alice", HandResult.LOSS, -25.0)

        avg = calc.get_avg_win_amount(player_name="Alice")
        assert avg == 75.0  # (100 + 50) / 2

    def test_avg_win_amount_no_wins(self):
        """Test average win amount with no wins"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.LOSS, -50.0)

        avg = calc.get_avg_win_amount(player_name="Alice")
        assert avg == 0.0

    def test_player_stats(self):
        """Test comprehensive player stats"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.WIN, 50.0)
        calc.record_hand("Alice", HandResult.LOSS, -30.0)
        calc.record_hand("Alice", HandResult.TIE, 0.0)

        stats = calc.get_player_stats("Alice")

        assert stats["player_name"] == "Alice"
        assert stats["total_hands"] == 4
        assert stats["wins"] == 2
        assert stats["losses"] == 1
        assert stats["ties"] == 1
        assert stats["win_rate"] == 50.0
        assert stats["total_winnings"] == 120.0
        assert stats["avg_win_amount"] == 75.0

    def test_player_stats_no_hands(self):
        """Test player stats with no hands played"""
        calc = WinRateCalculator()
        stats = calc.get_player_stats("Alice")

        assert stats["total_hands"] == 0
        assert stats["wins"] == 0
        assert stats["win_rate"] == 0.0

    def test_position_stats(self):
        """Test win rates by position"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0, position="BTN")
        calc.record_hand("Alice", HandResult.WIN, 50.0, position="BTN")
        calc.record_hand("Bob", HandResult.LOSS, -50.0, position="CO")

        pos_stats = calc.get_position_stats()

        assert "BTN" in pos_stats
        assert pos_stats["BTN"]["total_hands"] == 2
        assert pos_stats["BTN"]["win_rate"] == 100.0
        assert pos_stats["BTN"]["total_winnings"] == 150.0

    def test_hand_type_stats(self):
        """Test win rates by hand type"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0, hand_type="AA")
        calc.record_hand("Alice", HandResult.WIN, 75.0, hand_type="AA")
        calc.record_hand("Bob", HandResult.LOSS, -50.0, hand_type="72")

        hand_stats = calc.get_hand_type_stats()

        assert "AA" in hand_stats
        assert hand_stats["AA"]["total_hands"] == 2
        assert hand_stats["AA"]["win_rate"] == 100.0

    def test_get_all_players(self):
        """Test getting all players"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Bob", HandResult.LOSS, -50.0)
        calc.record_hand("Charlie", HandResult.WIN, 75.0)
        calc.record_hand("Alice", HandResult.WIN, 50.0)

        players = calc.get_all_players()
        assert players == ["Alice", "Bob", "Charlie"]

    def test_get_recent_hands(self):
        """Test getting recent hands"""
        calc = WinRateCalculator()
        for i in range(15):
            calc.record_hand("Alice", HandResult.WIN, 10.0 * i)

        recent = calc.get_recent_hands(limit=5)
        assert len(recent) == 5
        assert recent[-1].hand_id == 15

    def test_get_recent_hands_by_player(self):
        """Test getting recent hands for specific player"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Bob", HandResult.LOSS, -50.0)
        calc.record_hand("Alice", HandResult.WIN, 75.0)

        alice_recent = calc.get_recent_hands(player_name="Alice")
        assert len(alice_recent) == 2
        assert all(r.player_name == "Alice" for r in alice_recent)

    def test_overall_statistics(self):
        """Test overall statistics"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.WIN, 50.0)
        calc.record_hand("Bob", HandResult.LOSS, -50.0)

        stats = calc.get_statistics()

        assert stats["total_hands"] == 3
        assert stats["total_players"] == 2
        assert stats["overall_win_rate"] > 0
        assert stats["most_successful_player"] == "Alice"

    def test_statistics_empty(self):
        """Test statistics with no data"""
        calc = WinRateCalculator()
        stats = calc.get_statistics()

        assert stats["total_hands"] == 0
        assert stats["total_players"] == 0
        assert stats["overall_win_rate"] == 0.0
        assert stats["most_successful_player"] is None

    def test_hand_id_increment(self):
        """Test hand IDs increment correctly"""
        calc = WinRateCalculator()
        r1 = calc.record_hand("Alice", HandResult.WIN, 100.0)
        r2 = calc.record_hand("Bob", HandResult.LOSS, -50.0)
        r3 = calc.record_hand("Charlie", HandResult.TIE, 0.0)

        assert r1.hand_id == 1
        assert r2.hand_id == 2
        assert r3.hand_id == 3

    def test_multiple_filters_combined(self):
        """Test combining multiple filters"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0, position="BTN", hand_type="AA")
        calc.record_hand("Alice", HandResult.LOSS, -50.0, position="BTN", hand_type="KK")
        calc.record_hand("Alice", HandResult.WIN, 75.0, position="CO", hand_type="AA")

        # Alice, BTN position, AA hand type
        win_rate = calc.get_win_rate(
            player_name="Alice",
            position="BTN",
            hand_type="AA"
        )
        assert win_rate == 100.0

        total = calc.get_total_hands(
            player_name="Alice",
            position="BTN",
            hand_type="AA"
        )
        assert total == 1

    def test_reset_functionality(self):
        """Test reset clears all data"""
        calc = WinRateCalculator()
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Bob", HandResult.LOSS, -50.0)

        assert len(calc.hand_records) == 2

        calc.reset()

        assert len(calc.hand_records) == 0
        assert calc.hand_count == 0
        assert calc.get_win_rate() == 0.0

    def test_large_dataset(self):
        """Test with large number of hands"""
        calc = WinRateCalculator()

        for i in range(1000):
            result = HandResult.WIN if i % 2 == 0 else HandResult.LOSS
            calc.record_hand("Alice", result, 10.0 if result == HandResult.WIN else -10.0)

        assert calc.get_total_hands(player_name="Alice") == 1000
        assert calc.get_win_rate(player_name="Alice") == 50.0

    def test_win_rate_rounding(self):
        """Test win rate is properly rounded"""
        calc = WinRateCalculator()
        # 1 win out of 3 = 33.333...%
        calc.record_hand("Alice", HandResult.WIN, 100.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)
        calc.record_hand("Alice", HandResult.LOSS, -50.0)

        win_rate = calc.get_win_rate(player_name="Alice")
        assert win_rate == 33.33


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
