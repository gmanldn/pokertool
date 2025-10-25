#!/usr/bin/env python3
"""Call Frequency Calculator"""

class CallFrequencyCalculator:
    def minimum_defense_frequency(self, bet_size: float, pot_size: float) -> float:
        """Calculate MDF."""
        return round((pot_size / (pot_size + bet_size)) * 100, 2)
    
    def optimal_call_frequency(self, bluff_ratio: float) -> float:
        """Calculate optimal calling frequency against bluffs."""
        return round((bluff_ratio / (1 + bluff_ratio)) * 100, 2)
