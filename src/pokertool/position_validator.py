#!/usr/bin/env python3
"""Player position detection validation."""

from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class PositionValidator:
    """Validates detected player positions match button position."""

    def validate_positions(self, button_position: int, player_positions: Dict[int, str]) -> bool:
        """
        Validate that player positions are consistent with button.

        Args:
            button_position: Seat number of button (0-indexed)
            player_positions: Dict of seat_number -> position_name

        Returns:
            True if valid, False if inconsistent
        """
        if button_position not in player_positions:
            logger.warning(f"Button position {button_position} not in player positions")
            return False

        if player_positions[button_position] != 'BTN':
            logger.warning(f"Button position mismatch: seat {button_position} is {player_positions[button_position]}, expected BTN")
            return False

        return True

    def calculate_position(self, seat: int, button_seat: int, total_seats: int) -> str:
        """
        Calculate position name from seat and button.

        Args:
            seat: Player seat number
            button_seat: Button seat number
            total_seats: Total seats at table

        Returns:
            Position name (UTG, MP, CO, BTN, SB, BB)
        """
        offset = (seat - button_seat) % total_seats

        if offset == 0:
            return 'BTN'
        elif offset == 1:
            return 'SB'
        elif offset == 2:
            return 'BB'
        elif offset == 3:
            return 'UTG'
        elif offset == total_seats - 2:
            return 'CO'
        else:
            return 'MP'


_validator_instance: Optional[PositionValidator] = None

def get_position_validator() -> PositionValidator:
    """Get global position validator."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = PositionValidator()
    return _validator_instance
