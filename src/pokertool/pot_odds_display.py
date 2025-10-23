#!/usr/bin/env python3
"""Pot odds calculator integration for real-time display."""

from typing import Optional

class PotOddsDisplay:
    """Integrates pot odds calculation with real-time display."""

    def calculate_and_format(self, pot_size: float, bet_size: float) -> dict:
        """
        Calculate pot odds and format for display.

        Args:
            pot_size: Current pot size
            bet_size: Bet to call

        Returns:
            Dict with odds_ratio, odds_percent, recommendation
        """
        if bet_size <= 0:
            return {'odds_ratio': 'N/A', 'odds_percent': 0, 'recommendation': 'Check'}

        total_pot = pot_size + bet_size
        odds_ratio = total_pot / bet_size
        odds_percent = (bet_size / total_pot) * 100

        # Simple recommendation
        if odds_percent < 20:
            recommendation = "Good odds - consider calling"
        elif odds_percent < 33:
            recommendation = "Marginal odds"
        else:
            recommendation = "Poor odds - need strong hand"

        return {
            'odds_ratio': f"{odds_ratio:.1f}:1",
            'odds_percent': round(odds_percent, 1),
            'recommendation': recommendation
        }


_display_instance: Optional[PotOddsDisplay] = None

def get_pot_odds_display() -> PotOddsDisplay:
    """Get global pot odds display."""
    global _display_instance
    if _display_instance is None:
        _display_instance = PotOddsDisplay()
    return _display_instance
