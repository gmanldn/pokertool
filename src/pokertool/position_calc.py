"""Relative position calculation for poker tables."""

from enum import Enum
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class Position(Enum):
    """Poker table positions."""
    BTN = "BTN"  # Button
    SB = "SB"    # Small Blind
    BB = "BB"    # Big Blind
    UTG = "UTG"  # Under the Gun
    UTG1 = "UTG+1"
    UTG2 = "UTG+2"
    MP = "MP"    # Middle Position
    MP1 = "MP+1"
    MP2 = "MP+2"
    LJ = "LJ"    # Lojack
    HJ = "HJ"    # Hijack
    CO = "CO"    # Cutoff


class PositionCalculator:
    """Calculate relative positions at poker table."""

    def __init__(self):
        self.position_names_6max = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
        self.position_names_9max = ["UTG", "UTG1", "UTG2", "LJ", "HJ", "CO", "BTN", "SB", "BB"]
        self.position_names_heads_up = ["BTN", "BB"]

    def calculate_position(
        self,
        seat_number: int,
        dealer_seat: int,
        num_active_players: int
    ) -> Position:
        """
        Calculate position relative to button.

        Args:
            seat_number: Player's seat number
            dealer_seat: Dealer button seat number
            num_active_players: Number of active players

        Returns:
            Position enum
        """
        # Calculate seats after button (clockwise)
        seats_after_button = (seat_number - dealer_seat) % num_active_players

        # Map to position based on table size
        position_name = self._get_position_name(seats_after_button, num_active_players)

        return Position[position_name.replace("+", "")]

    def _get_position_name(self, seats_after_button: int, num_players: int) -> str:
        """Get position name based on seats after button."""
        if num_players == 2:
            # Heads up
            return self.position_names_heads_up[seats_after_button]

        elif num_players <= 6:
            # 6-max
            position_map = {
                0: "BTN",
                1: "SB",
                2: "BB",
                3: "UTG",
                4: "MP",
                5: "CO"
            }
            return position_map.get(seats_after_button, "MP")

        else:
            # 9-max (7-9 players)
            position_map = {
                0: "BTN",
                1: "SB",
                2: "BB",
                3: "UTG",
                4: "UTG1",
                5: "UTG2" if num_players >= 9 else "LJ",
                6: "LJ" if num_players >= 9 else "HJ",
                7: "HJ",
                8: "CO"
            }
            return position_map.get(seats_after_button, "MP")

    def is_early_position(self, position: Position) -> bool:
        """Check if position is early (UTG, UTG+1, UTG+2)."""
        return position in [Position.UTG, Position.UTG1, Position.UTG2]

    def is_middle_position(self, position: Position) -> bool:
        """Check if position is middle (LJ, HJ, MP)."""
        return position in [Position.LJ, Position.HJ, Position.MP, Position.MP1, Position.MP2]

    def is_late_position(self, position: Position) -> bool:
        """Check if position is late (CO, BTN)."""
        return position in [Position.CO, Position.BTN]

    def is_blind(self, position: Position) -> bool:
        """Check if position is a blind."""
        return position in [Position.SB, Position.BB]

    def get_position_strength(self, position: Position) -> float:
        """
        Get position strength score (0.0 = worst, 1.0 = best).

        Returns:
            Position strength score
        """
        strength_map = {
            Position.BB: 0.1,
            Position.SB: 0.2,
            Position.UTG: 0.3,
            Position.UTG1: 0.35,
            Position.UTG2: 0.4,
            Position.MP: 0.45,
            Position.MP1: 0.5,
            Position.MP2: 0.55,
            Position.LJ: 0.6,
            Position.HJ: 0.7,
            Position.CO: 0.85,
            Position.BTN: 1.0
        }
        return strength_map.get(position, 0.5)

    def get_all_positions(self, num_players: int) -> List[str]:
        """Get all position names for a given table size."""
        if num_players == 2:
            return self.position_names_heads_up
        elif num_players <= 6:
            return self.position_names_6max[:num_players]
        else:
            return self.position_names_9max[:num_players]
