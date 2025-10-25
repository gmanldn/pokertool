#!/usr/bin/env python3
import pytest
from src.pokertool.pot_odds_calculator import PotOddsCalculator

class TestPotOddsCalculator:
    def test_calculate_pot_odds(self):
        odds = PotOddsCalculator.calculate_pot_odds(100.0, 50.0)
        assert odds == 33.33

    def test_calculate_equity_needed(self):
        equity = PotOddsCalculator.calculate_equity_needed(100.0, 25.0)
        assert equity == 20.0

    def test_should_call_yes(self):
        assert PotOddsCalculator.should_call(100.0, 25.0, 25.0) is True

    def test_should_call_no(self):
        assert PotOddsCalculator.should_call(100.0, 50.0, 20.0) is False

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
