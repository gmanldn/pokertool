#!/usr/bin/env python3
"""Tests for Variance Calculator"""

import pytest
from src.pokertool.variance_calculator import VarianceCalculator


class TestVarianceCalculator:
    def test_calculate_variance(self):
        calc = VarianceCalculator()
        results = [10, 20, 30, 40, 50]
        var = calc.calculate_variance(results)
        assert var == 200.0

    def test_calculate_std_dev(self):
        calc = VarianceCalculator()
        results = [10, 20, 30, 40, 50]
        std = calc.calculate_std_dev(results)
        assert std == 14.14

    def test_calculate_variance_empty(self):
        calc = VarianceCalculator()
        var = calc.calculate_variance([])
        assert var == 0.0

    def test_calculate_downswing_probability(self):
        calc = VarianceCalculator()
        prob = calc.calculate_downswing_probability(5.0, 50.0, 1000)
        assert 0 <= prob <= 100

    def test_calculate_bankroll_requirement(self):
        calc = VarianceCalculator()
        br = calc.calculate_bankroll_requirement(5.0, 100.0, 5.0)
        assert br > 0

    def test_calculate_confidence_interval(self):
        calc = VarianceCalculator()
        results = [100, 120, 80, 110, 90]
        ci = calc.calculate_confidence_interval(results, 95.0)
        assert ci[0] < ci[1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
