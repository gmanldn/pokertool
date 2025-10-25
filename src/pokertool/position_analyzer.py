#!/usr/bin/env python3
"""Position Analyzer - Analyzes player positions"""

from typing import List, Dict


class PositionAnalyzer:
    """Analyzes table positions."""

    POSITIONS = ["UTG", "UTG+1", "MP", "MP+1", "CO", "BTN", "SB", "BB"]

    @classmethod
    def get_position_index(cls, position: str) -> int:
        """Get position index."""
        try:
            return cls.POSITIONS.index(position.upper())
        except ValueError:
            return -1

    @classmethod
    def is_early_position(cls, position: str) -> bool:
        """Check if early position."""
        return position.upper() in ["UTG", "UTG+1"]

    @classmethod
    def is_late_position(cls, position: str) -> bool:
        """Check if late position."""
        return position.upper() in ["CO", "BTN"]

    @classmethod
    def is_blind(cls, position: str) -> bool:
        """Check if blind."""
        return position.upper() in ["SB", "BB"]

    @classmethod
    def get_position_strength(cls, position: str) -> float:
        """Get position strength score (0-1)."""
        idx = cls.get_position_index(position)
        if idx == -1:
            return 0.0
        return idx / (len(cls.POSITIONS) - 1)
