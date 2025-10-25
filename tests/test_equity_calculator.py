#!/usr/bin/env python3
"""Tests for Equity Calculator"""

import pytest
from src.pokertool.equity_calculator import (
    EquityCalculator, Card, Suit, EquityResult
)


class TestEquityCalculator:
    def test_initialization(self):
        calc = EquityCalculator()
        assert len(calc.deck) == 52

    def test_build_deck(self):
        calc = EquityCalculator()
        # Deck already built in __init__, check it has 4 aces
        aces = [c for c in calc.deck if c.rank == 'A']
        assert len(aces) == 4
        assert len(calc.deck) == 52

    def test_calculate_equity_basic(self):
        calc = EquityCalculator()
        aa = [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)]
        kk = [Card('K', Suit.SPADES), Card('K', Suit.HEARTS)]
        result = calc.calculate_equity(aa, [kk])
        assert isinstance(result, EquityResult)
        assert result.win_equity == 100.0

    def test_calculate_equity_tie(self):
        calc = EquityCalculator()
        aa1 = [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)]
        aa2 = [Card('A', Suit.DIAMONDS), Card('A', Suit.CLUBS)]
        result = calc.calculate_equity(aa1, [aa2])
        assert result.tie_equity == 100.0

    def test_count_outs_no_board(self):
        calc = EquityCalculator()
        hand = [Card('A', Suit.SPADES), Card('K', Suit.HEARTS)]
        outs = calc.count_outs(hand, [])
        assert outs == 0

    def test_count_outs_with_board(self):
        calc = EquityCalculator()
        hand = [Card('7', Suit.SPADES), Card('6', Suit.HEARTS)]
        board = [Card('K', Suit.DIAMONDS), Card('Q', Suit.CLUBS), Card('J', Suit.SPADES)]
        outs = calc.count_outs(hand, board)
        assert outs >= 0

    def test_calculate_pot_equity(self):
        calc = EquityCalculator()
        equity_value = calc.calculate_pot_equity(50.0, 100.0, 50.0)
        assert equity_value == 75.0

    def test_calculate_required_equity(self):
        calc = EquityCalculator()
        required = calc.calculate_required_equity(100.0, 50.0)
        assert required == round((50 / 150) * 100, 2)

    def test_is_profitable_call_yes(self):
        calc = EquityCalculator()
        assert calc.is_profitable_call(50.0, 100.0, 25.0) is True

    def test_is_profitable_call_no(self):
        calc = EquityCalculator()
        assert calc.is_profitable_call(20.0, 100.0, 50.0) is False

    def test_calculate_outs_to_equity_one_card(self):
        calc = EquityCalculator()
        equity = calc.calculate_outs_to_equity(9, 1)
        assert equity > 0
        assert equity < 100

    def test_calculate_outs_to_equity_two_cards(self):
        calc = EquityCalculator()
        equity = calc.calculate_outs_to_equity(9, 2)
        assert equity > 0
        assert equity < 100

    def test_calculate_ev_positive(self):
        calc = EquityCalculator()
        ev = calc.calculate_ev(60.0, 100.0, 100.0, 50.0)
        assert ev > 0

    def test_calculate_ev_negative(self):
        calc = EquityCalculator()
        # 10% equity to win 200, but calling 50 = negative EV
        ev = calc.calculate_ev(10.0, 100.0, 100.0, 50.0)
        assert ev < 0

    def test_format_hand(self):
        calc = EquityCalculator()
        hand = [Card('A', Suit.SPADES), Card('K', Suit.HEARTS)]
        formatted = calc._format_hand(hand)
        assert 'A' in formatted
        assert 'K' in formatted

    def test_get_hand_vs_range_equity(self):
        calc = EquityCalculator()
        equity = calc.get_hand_vs_range_equity('AA', 100)
        assert 'win' in equity
        assert 'total' in equity
        assert equity['total'] > 0

    def test_estimate_hand_strength_high(self):
        calc = EquityCalculator()
        strength = calc._estimate_hand_strength('AA')
        assert strength > 0.8

    def test_estimate_hand_strength_low(self):
        calc = EquityCalculator()
        strength = calc._estimate_hand_strength('23')
        assert strength < 0.3

    def test_compare_hands_win(self):
        calc = EquityCalculator()
        aa = [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)]
        kk = [Card('K', Suit.SPADES), Card('K', Suit.HEARTS)]
        result = calc._compare_hands(aa, kk, [])
        assert result == 1

    def test_compare_hands_lose(self):
        calc = EquityCalculator()
        kk = [Card('K', Suit.SPADES), Card('K', Suit.HEARTS)]
        aa = [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)]
        result = calc._compare_hands(kk, aa, [])
        assert result == -1

    def test_compare_hands_tie(self):
        calc = EquityCalculator()
        aa1 = [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)]
        aa2 = [Card('A', Suit.DIAMONDS), Card('A', Suit.CLUBS)]
        result = calc._compare_hands(aa1, aa2, [])
        assert result == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
