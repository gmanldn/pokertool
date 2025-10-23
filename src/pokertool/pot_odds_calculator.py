"""Real-time Pot Odds Calculator"""
from typing import Tuple
from dataclasses import dataclass

@dataclass
class PotOdds:
    pot_size: float
    bet_to_call: float
    pot_odds_ratio: str
    pot_odds_percentage: float
    implied_odds: float
    break_even_equity: float

class PotOddsCalculator:
    """Calculate pot odds for decision making."""
    
    @staticmethod
    def calculate(pot_size: float, bet_to_call: float, implied_pot: float = 0.0) -> PotOdds:
        """Calculate comprehensive pot odds."""
        total_pot = pot_size + bet_to_call
        pot_odds_pct = (bet_to_call / total_pot) * 100 if total_pot > 0 else 0
        
        # Calculate ratio (e.g., "3:1")
        if bet_to_call > 0:
            ratio = pot_size / bet_to_call
            ratio_str = f"{ratio:.1f}:1"
        else:
            ratio_str = "N/A"
        
        # Implied odds with future betting
        implied_total = total_pot + implied_pot
        implied_pct = (bet_to_call / implied_total) * 100 if implied_total > 0 else 0
        
        return PotOdds(
            pot_size=pot_size,
            bet_to_call=bet_to_call,
            pot_odds_ratio=ratio_str,
            pot_odds_percentage=pot_odds_pct,
            implied_odds=implied_pct,
            break_even_equity=pot_odds_pct
        )
