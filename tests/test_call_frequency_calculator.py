#!/usr/bin/env python3
import pytest
from src.pokertool.call_frequency_calculator import CallFrequencyCalculator

class TestCallFrequencyCalculator:
    def test_minimum_defense_frequency(self):
        calc = CallFrequencyCalculator()
        mdf = calc.minimum_defense_frequency(50.0, 100.0)
        assert mdf == round((100/150)*100, 2)
    
    def test_optimal_call_frequency(self):
        calc = CallFrequencyCalculator()
        freq = calc.optimal_call_frequency(0.5)
        assert freq == round((0.5/1.5)*100, 2)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
