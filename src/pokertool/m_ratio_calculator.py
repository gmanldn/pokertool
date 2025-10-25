#!/usr/bin/env python3
"""M-Ratio Calculator"""

class MRatioCalculator:
    def calculate_m_ratio(self, stack: int, small_blind: int, big_blind: int, ante: int = 0, players: int = 9) -> float:
        """Calculate M-ratio (Harrington's M)."""
        cost_per_orbit = small_blind + big_blind + (ante * players)
        return round(stack / cost_per_orbit, 2) if cost_per_orbit > 0 else 0.0
    
    def get_zone_color(self, m_ratio: float) -> str:
        """Get Harrington zone color."""
        if m_ratio >= 20: return "green"
        elif m_ratio >= 10: return "yellow"
        elif m_ratio >= 6: return "orange"
        elif m_ratio >= 1: return "red"
        else: return "dead"
    
    def calculate_effective_m(self, m_ratio: float, position_factor: float = 1.0) -> float:
        """Calculate effective M with position adjustment."""
        return round(m_ratio * position_factor, 2)
