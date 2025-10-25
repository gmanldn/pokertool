#!/usr/bin/env python3
"""Tests for ICM Calculator"""

import pytest
from src.pokertool.icm_calculator import ICMCalculator, ICMResult


class TestICMCalculator:
    def test_initialization(self):
        calc = ICMCalculator()
        assert calc is not None

    def test_calculate_icm_basic(self):
        calc = ICMCalculator()
        stacks = [5000, 3000, 2000]
        payouts = [500.0, 300.0, 200.0]
        result = calc.calculate_icm(stacks, payouts)
        assert isinstance(result, ICMResult)
        assert len(result.player_equities) == 3

    def test_calculate_icm_equal_stacks(self):
        calc = ICMCalculator()
        stacks = [1000, 1000, 1000]
        payouts = [600.0, 300.0, 100.0]
        result = calc.calculate_icm(stacks, payouts)
        # Equal stacks should have roughly equal equity
        assert all(33 <= e <= 34 for e in result.player_equities)

    def test_calculate_icm_chip_leader(self):
        calc = ICMCalculator()
        stacks = [8000, 1000, 1000]
        payouts = [500.0, 300.0, 200.0]
        result = calc.calculate_icm(stacks, payouts)
        # Chip leader should have highest equity
        assert result.player_equities[0] > result.player_equities[1]
        assert result.player_equities[0] > result.player_equities[2]

    def test_calculate_player_ev(self):
        calc = ICMCalculator()
        stacks = [5000, 3000, 2000]
        payouts = [500.0, 300.0, 200.0]
        ev = calc._calculate_player_ev(5000, stacks, payouts)
        assert ev > 0
        assert ev <= sum(payouts)

    def test_calculate_chip_ev(self):
        calc = ICMCalculator()
        stacks = [5000, 3000, 2000]
        payouts = [500.0, 300.0, 200.0]
        chip_ev = calc.calculate_chip_ev(5000, stacks, payouts, 1000)
        assert 'current_ev' in chip_ev
        assert 'win_ev' in chip_ev
        assert 'lose_ev' in chip_ev

    def test_find_push_fold_threshold_short_stack(self):
        calc = ICMCalculator()
        threshold = calc.find_push_fold_threshold(400, 50, 6)  # 8 BB
        assert threshold == 20.0  # Short stack should push wider

    def test_find_push_fold_threshold_medium_stack(self):
        calc = ICMCalculator()
        threshold = calc.find_push_fold_threshold(650, 50, 6)  # 13 BB
        assert threshold == 15.0

    def test_find_push_fold_threshold_deep_stack(self):
        calc = ICMCalculator()
        threshold = calc.find_push_fold_threshold(1500, 50, 6)
        assert threshold == 5.0  # Deep stack should push tighter

    def test_calculate_bubble_factor_in_money(self):
        calc = ICMCalculator()
        stacks = [5000, 3000, 2000]
        factor = calc.calculate_bubble_factor(stacks, 3)
        assert factor == 1.0  # All players in the money

    def test_calculate_bubble_factor_on_bubble(self):
        calc = ICMCalculator()
        stacks = [5000, 3000, 2000, 1000]
        factor = calc.calculate_bubble_factor(stacks, 3)
        assert factor == 2.5  # One player from bubble

    def test_calculate_bubble_factor_near_bubble(self):
        calc = ICMCalculator()
        stacks = [5000, 3000, 2000, 1000, 500]
        factor = calc.calculate_bubble_factor(stacks, 3)
        assert factor == 1.5  # Two players from bubble

    def test_icm_result_structure(self):
        calc = ICMCalculator()
        stacks = [1000, 2000, 3000]
        payouts = [300.0, 200.0, 100.0]
        result = calc.calculate_icm(stacks, payouts)
        assert result.player_stacks == stacks
        assert result.prize_pool == payouts
        assert len(result.player_evs) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
