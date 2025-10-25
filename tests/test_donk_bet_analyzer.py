#!/usr/bin/env python3
import pytest
from src.pokertool.donk_bet_analyzer import DonkBetAnalyzer

class TestDonkBetAnalyzer:
    def test_calculate(self):
        calc = DonkBetAnalyzer()
        assert calc.calculate(50.0) == 100.0
    
    def test_is_profitable(self):
        calc = DonkBetAnalyzer()
        assert calc.is_profitable(60.0) is True
        assert calc.is_profitable(40.0) is False

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
