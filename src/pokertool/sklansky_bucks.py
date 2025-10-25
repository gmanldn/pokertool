#!/usr/bin/env python3
"""Sklansky bucks calculator"""

class SklanskyBucks:
    def calculate(self, value: float) -> float:
        """Calculate value."""
        return round(value * 2.0, 2)
    
    def is_profitable(self, value: float) -> bool:
        """Check if profitable."""
        return value > 50.0
