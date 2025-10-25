#!/usr/bin/env python3
"""Tests for HUD Stats Calculator"""

import pytest
from src.pokertool.hud_stats_calculator import (
    HUDStatsCalculator, HandAction, HUDStats, Action, Street
)


class TestHUDStatsCalculator:
    def test_initialization(self):
        calc = HUDStatsCalculator()
        assert len(calc.hands) == 0

    def test_add_hand(self):
        calc = HUDStatsCalculator()
        hand = [HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False)]
        calc.add_hand(hand)
        assert len(calc.hands) == 1

    def test_calculate_vpip_basic(self):
        calc = HUDStatsCalculator()
        hand1 = [HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False)]
        hand2 = [HandAction("Alice", Street.PREFLOP, Action.FOLD, 0, False)]
        calc.add_hand(hand1)
        calc.add_hand(hand2)
        vpip = calc.calculate_vpip("Alice")
        assert vpip == 50.0  # 1 out of 2 hands

    def test_calculate_pfr_basic(self):
        calc = HUDStatsCalculator()
        hand1 = [HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False)]
        hand2 = [HandAction("Alice", Street.PREFLOP, Action.CALL, 10, False)]
        calc.add_hand(hand1)
        calc.add_hand(hand2)
        pfr = calc.calculate_pfr("Alice")
        assert pfr == 50.0  # 1 raise out of 2 hands

    def test_calculate_aggression_factor(self):
        calc = HUDStatsCalculator()
        hand = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Alice", Street.FLOP, Action.BET, 15, False),
            HandAction("Alice", Street.TURN, Action.CALL, 20, True),
        ]
        calc.add_hand(hand)
        af = calc.calculate_aggression_factor("Alice")
        assert af == 2.0  # 2 aggressive / 1 passive

    def test_calculate_wtsd(self):
        calc = HUDStatsCalculator()
        hand1 = [HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False)]
        hand2 = [HandAction("Alice", Street.PREFLOP, Action.CALL, 10, False)]
        calc.add_hand(hand1)
        calc.add_hand(hand2)
        calc.record_showdown("Alice", True)
        wtsd = calc.calculate_wtsd("Alice")
        assert wtsd == 50.0  # 1 showdown out of 2 hands

    def test_calculate_w_sd(self):
        calc = HUDStatsCalculator()
        calc.record_showdown("Alice", True)
        calc.record_showdown("Alice", False)
        calc.record_showdown("Alice", True)
        w_sd = calc.calculate_w_sd("Alice")
        assert w_sd == round(2/3 * 100, 2)

    def test_record_showdown(self):
        calc = HUDStatsCalculator()
        calc.record_showdown("Alice", True)
        assert calc.showdowns["Alice"] == 1
        assert calc.showdown_wins["Alice"] == 1

    def test_calculate_three_bet(self):
        calc = HUDStatsCalculator()
        hand1 = [HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, True)]
        hand2 = [HandAction("Alice", Street.PREFLOP, Action.CALL, 10, True)]
        calc.add_hand(hand1)
        calc.add_hand(hand2)
        three_bet = calc.calculate_three_bet("Alice")
        assert three_bet == 50.0

    def test_calculate_cbet(self):
        calc = HUDStatsCalculator()
        hand1 = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Alice", Street.FLOP, Action.BET, 15, False),
        ]
        hand2 = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Alice", Street.FLOP, Action.CHECK, 0, False),
        ]
        calc.add_hand(hand1)
        calc.add_hand(hand2)
        cbet = calc.calculate_cbet("Alice")
        assert cbet == 50.0

    def test_calculate_all_stats(self):
        calc = HUDStatsCalculator()
        hand = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Alice", Street.FLOP, Action.BET, 15, False),
        ]
        calc.add_hand(hand)
        stats = calc.calculate_all_stats("Alice")
        assert isinstance(stats, HUDStats)
        assert stats.vpip > 0
        assert stats.pfr > 0

    def test_vpip_no_hands(self):
        calc = HUDStatsCalculator()
        vpip = calc.calculate_vpip("NonExistent")
        assert vpip == 0.0

    def test_aggression_factor_only_aggressive(self):
        calc = HUDStatsCalculator()
        hand = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Alice", Street.FLOP, Action.BET, 15, False),
        ]
        calc.add_hand(hand)
        af = calc.calculate_aggression_factor("Alice")
        assert af == 2.0  # No calls, so returns count

    def test_fold_to_3bet(self):
        calc = HUDStatsCalculator()
        hand1 = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Bob", Street.PREFLOP, Action.RAISE, 30, True),
            HandAction("Alice", Street.PREFLOP, Action.FOLD, 0, True),
        ]
        hand2 = [
            HandAction("Alice", Street.PREFLOP, Action.RAISE, 10, False),
            HandAction("Bob", Street.PREFLOP, Action.RAISE, 30, True),
            HandAction("Alice", Street.PREFLOP, Action.CALL, 30, True),
        ]
        calc.add_hand(hand1)
        calc.add_hand(hand2)
        fold_to_3bet = calc.calculate_fold_to_3bet("Alice")
        assert fold_to_3bet == 50.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
