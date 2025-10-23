"""
Unit Tests for Equity Calculator

Tests hand strength, equity calculations, and range analysis.

Author: PokerTool Team
Created: 2025-10-22
"""

import pytest
from pokertool.equity_calculator import EquityCalculator


class TestEquityCalculator:
    """Test suite for EquityCalculator"""

    @pytest.fixture
    def calc(self):
        """Create EquityCalculator instance"""
        return EquityCalculator()

    # Hand Strength Tests

    def test_hand_strength_pocket_aces(self, calc):
        """Test AA has highest strength"""
        strength = calc.get_hand_strength('AA')
        assert strength == 1.0

    def test_hand_strength_pocket_kings(self, calc):
        """Test KK has second highest strength"""
        strength = calc.get_hand_strength('KK')
        assert strength == 0.95

    def test_hand_strength_suited_broadway(self, calc):
        """Test AKs has high strength"""
        strength = calc.get_hand_strength('AKs')
        assert strength > 0.80

    def test_hand_strength_offsuit_broadway(self, calc):
        """Test AKo has lower strength than AKs"""
        suited_strength = calc.get_hand_strength('AKs')
        offsuit_strength = calc.get_hand_strength('AKo')
        assert offsuit_strength < suited_strength

    def test_hand_strength_unknown_hand(self, calc):
        """Test unknown hands default to 0.3"""
        strength = calc.get_hand_strength('72o')
        assert strength == 0.3

    # Hand vs Hand Tests

    def test_hand_vs_hand_aa_vs_qq(self, calc):
        """Test AA vs QQ equity"""
        equity = calc.calculate_hand_vs_hand('AA', 'QQ')
        assert equity > 80.0  # AA is heavily favored
        assert equity < 100.0

    def test_hand_vs_hand_aks_vs_qq(self, calc):
        """Test AKs vs QQ is close to 50/50"""
        equity = calc.calculate_hand_vs_hand('AKs', 'QQ')
        assert 40.0 < equity < 60.0  # Coin flip

    def test_hand_vs_hand_equity_adds_to_100(self, calc):
        """Test hero + villain equity ≈ 100%"""
        hero_equity = calc.calculate_hand_vs_hand('AKs', 'QQ')
        villain_equity = 100 - hero_equity
        assert abs((hero_equity + villain_equity) - 100.0) < 0.1

    # Hand vs Range Tests

    def test_hand_vs_range_aa_vs_premium(self, calc):
        """Test AA vs premium range"""
        equity = calc.calculate_hand_vs_range(
            hero_hand='AA',
            villain_range=['KK', 'QQ', 'JJ', 'AKs']
        )
        assert equity > 70.0  # AA dominates

    def test_hand_vs_range_ak_vs_pairs(self, calc):
        """Test AKs vs pocket pair range"""
        equity = calc.calculate_hand_vs_range(
            hero_hand='AKs',
            villain_range=['AA', 'KK', 'QQ', 'JJ', 'TT']
        )
        assert 30.0 < equity < 60.0  # Mixed equity

    def test_hand_vs_range_empty_range(self, calc):
        """Test hand vs empty range defaults to 50%"""
        equity = calc.calculate_hand_vs_range(
            hero_hand='AA',
            villain_range=[]
        )
        assert equity == 50.0

    # Range vs Range Tests

    def test_range_vs_range_tight_vs_loose(self, calc):
        """Test tight range vs loose range"""
        result = calc.calculate_range_vs_range(
            hero_range=['AA', 'KK', 'QQ'],
            villain_range=['TT', '99', '88', '77', '66']
        )

        assert result['hero_equity'] > result['villain_equity']
        assert abs((result['hero_equity'] + result['villain_equity']) - 100.0) < 0.1

    def test_range_vs_range_equal_ranges(self, calc):
        """Test identical ranges should be close to 50/50"""
        range_hands = ['AA', 'KK', 'QQ', 'JJ']
        result = calc.calculate_range_vs_range(
            hero_range=range_hands,
            villain_range=range_hands
        )

        assert 45.0 < result['hero_equity'] < 55.0  # Approximately equal

    def test_range_vs_range_empty_ranges(self, calc):
        """Test empty ranges default to 50/50"""
        result = calc.calculate_range_vs_range(
            hero_range=[],
            villain_range=[]
        )

        assert result['hero_equity'] == 50.0
        assert result['villain_equity'] == 50.0

    def test_range_vs_range_includes_stats(self, calc):
        """Test result includes range statistics"""
        result = calc.calculate_range_vs_range(
            hero_range=['AA', 'KK'],
            villain_range=['QQ', 'JJ', 'TT']
        )

        assert 'hero_range_size' in result
        assert 'villain_range_size' in result
        assert 'hero_avg_strength' in result
        assert 'villain_avg_strength' in result

        assert result['hero_range_size'] == 2
        assert result['villain_range_size'] == 3

    # Equity Category Tests

    def test_equity_category_very_strong(self, calc):
        """Test very strong equity category (≥70%)"""
        category = calc.get_equity_category(75.0)
        assert category == "Very Strong"

    def test_equity_category_strong(self, calc):
        """Test strong equity category (55-69%)"""
        category = calc.get_equity_category(60.0)
        assert category == "Strong"

    def test_equity_category_medium(self, calc):
        """Test medium equity category (45-54%)"""
        category = calc.get_equity_category(50.0)
        assert category == "Medium"

    def test_equity_category_weak(self, calc):
        """Test weak equity category (30-44%)"""
        category = calc.get_equity_category(35.0)
        assert category == "Weak"

    def test_equity_category_very_weak(self, calc):
        """Test very weak equity category (<30%)"""
        category = calc.get_equity_category(20.0)
        assert category == "Very Weak"

    # Edge Cases

    def test_hand_vs_hand_same_hand(self, calc):
        """Test same hand vs itself"""
        equity = calc.calculate_hand_vs_hand('AA', 'AA')
        assert 45.0 < equity < 55.0  # Should be close to 50%

    def test_equity_never_negative(self, calc):
        """Test equity is never negative"""
        equity = calc.calculate_hand_vs_hand('72o', 'AA')
        assert equity >= 0.0

    def test_equity_never_exceeds_100(self, calc):
        """Test equity never exceeds 100%"""
        equity = calc.calculate_hand_vs_hand('AA', '72o')
        assert equity <= 100.0

    # Performance Tests

    def test_hand_vs_range_performance(self, calc):
        """Test hand vs range calculation is fast"""
        import time

        large_range = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77']

        start = time.time()
        calc.calculate_hand_vs_range('AKs', large_range)
        duration = time.time() - start

        assert duration < 0.1  # Should complete in < 100ms

    def test_range_vs_range_performance(self, calc):
        """Test range vs range calculation is fast"""
        import time

        range_a = ['AA', 'KK', 'QQ', 'JJ', 'TT']
        range_b = ['99', '88', '77', '66', '55']

        start = time.time()
        calc.calculate_range_vs_range(range_a, range_b)
        duration = time.time() - start

        assert duration < 0.1  # Should complete in < 100ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
