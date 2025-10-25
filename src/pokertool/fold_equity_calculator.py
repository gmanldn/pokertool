#!/usr/bin/env python3
"""Fold Equity Calculator"""

class FoldEquityCalculator:
    def calculate_fold_equity(self, fold_percentage: float, pot_size: float) -> float:
        """Calculate fold equity value."""
        return round((fold_percentage / 100) * pot_size, 2)
    
    def calculate_bluff_ev(self, fold_pct: float, pot: float, bet: float, equity_if_called: float) -> float:
        """Calculate EV of a bluff."""
        fold_ev = (fold_pct / 100) * pot
        call_ev = (1 - fold_pct / 100) * ((equity_if_called / 100) * (pot + bet) - bet)
        return round(fold_ev + call_ev, 2)
    
    def minimum_fold_percentage(self, pot: float, bet: float) -> float:
        """Calculate minimum fold percentage for profitable bluff."""
        return round((bet / (pot + bet)) * 100, 2)
