#!/usr/bin/env python3
import pytest
from src.pokertool.fold_equity_calculator import FoldEquityCalculator

class TestFoldEquityCalculator:
    def test_calculate_fold_equity(self):
        calc = FoldEquityCalculator()
        assert calc.calculate_fold_equity(50.0, 100.0) == 50.0
    
    def test_calculate_bluff_ev(self):
        calc = FoldEquityCalculator()
        ev = calc.calculate_bluff_ev(60.0, 100.0, 50.0, 20.0)
        assert isinstance(ev, float)
    
    def test_minimum_fold_percentage(self):
        calc = FoldEquityCalculator()
        assert calc.minimum_fold_percentage(100.0, 50.0) == round((50/150)*100, 2)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
