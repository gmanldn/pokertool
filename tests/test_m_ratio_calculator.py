#!/usr/bin/env python3
import pytest
from src.pokertool.m_ratio_calculator import MRatioCalculator

class TestMRatioCalculator:
    def test_calculate_m_ratio(self):
        calc = MRatioCalculator()
        m = calc.calculate_m_ratio(1000, 25, 50, 0, 9)
        assert m == round(1000/75, 2)
    
    def test_get_zone_color(self):
        calc = MRatioCalculator()
        assert calc.get_zone_color(25.0) == "green"
        assert calc.get_zone_color(15.0) == "yellow"
        assert calc.get_zone_color(8.0) == "orange"
        assert calc.get_zone_color(3.0) == "red"
    
    def test_calculate_effective_m(self):
        calc = MRatioCalculator()
        assert calc.calculate_effective_m(10.0, 1.2) == 12.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
