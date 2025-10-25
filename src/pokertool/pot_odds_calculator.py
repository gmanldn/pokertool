#!/usr/bin/env python3
"""Pot Odds Calculator"""

class PotOddsCalculator:
    """Calculates pot odds and equity."""

    @staticmethod
    def calculate_pot_odds(pot_size: float, bet_to_call: float) -> float:
        """Calculate pot odds as percentage."""
        total = pot_size + bet_to_call
        return round((bet_to_call / total) * 100, 2) if total > 0 else 0.0

    @staticmethod
    def calculate_equity_needed(pot_size: float, bet_to_call: float) -> float:
        """Calculate equity needed to call profitably."""
        return PotOddsCalculator.calculate_pot_odds(pot_size, bet_to_call)

    @staticmethod
    def should_call(pot_size: float, bet_to_call: float, equity: float) -> bool:
        """Determine if call is profitable."""
        needed = PotOddsCalculator.calculate_equity_needed(pot_size, bet_to_call)
        return equity >= needed
