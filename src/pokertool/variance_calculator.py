#!/usr/bin/env python3
"""Variance Calculator - Calculates poker variance and standard deviation"""

import logging
from typing import List
import math

logger = logging.getLogger(__name__)


class VarianceCalculator:
    """Calculates variance and standard deviation for poker results."""

    def __init__(self):
        """Initialize variance calculator."""
        pass

    def calculate_variance(self, results: List[float]) -> float:
        """Calculate variance of results."""
        if not results:
            return 0.0
        
        mean = sum(results) / len(results)
        squared_diffs = [(x - mean) ** 2 for x in results]
        variance = sum(squared_diffs) / len(results)
        
        return round(variance, 2)

    def calculate_std_dev(self, results: List[float]) -> float:
        """Calculate standard deviation."""
        variance = self.calculate_variance(results)
        return round(math.sqrt(variance), 2)

    def calculate_downswing_probability(self, winrate: float, std_dev: float, hands: int) -> float:
        """Calculate probability of a downswing."""
        if std_dev == 0:
            return 0.0
        
        # Simplified calculation
        z_score = abs(winrate) / (std_dev / math.sqrt(hands))
        probability = 1 - (1 / (1 + math.exp(-z_score)))
        
        return round(probability * 100, 2)

    def calculate_bankroll_requirement(
        self,
        winrate: float,
        std_dev: float,
        risk_of_ruin: float = 5.0
    ) -> float:
        """Calculate required bankroll in buy-ins."""
        if winrate <= 0:
            return float('inf')
        
        # Simplified bankroll requirement
        z_score = 1.65 if risk_of_ruin == 5.0 else 2.33  # 95% or 99% confidence
        buy_ins = (z_score * std_dev) / winrate
        
        return round(buy_ins, 2)

    def calculate_confidence_interval(
        self,
        results: List[float],
        confidence: float = 95.0
    ) -> tuple[float, float]:
        """Calculate confidence interval for winrate."""
        if not results:
            return (0.0, 0.0)
        
        mean = sum(results) / len(results)
        std_dev = self.calculate_std_dev(results)
        
        z_score = 1.96 if confidence == 95.0 else 2.58
        margin = z_score * (std_dev / math.sqrt(len(results)))
        
        return (round(mean - margin, 2), round(mean + margin, 2))


if __name__ == '__main__':
    calc = VarianceCalculator()
    results = [100, -50, 200, -25, 150, 75, -100, 50]
    var = calc.calculate_variance(results)
    std = calc.calculate_std_dev(results)
    print(f"Variance: {var}, StdDev: {std}")
