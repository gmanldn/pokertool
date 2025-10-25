"""Relative Position Calculator"""
from typing import List, Optional, Dict

class PositionCalculator:
    """Calculate relative positions at poker table."""

    POSITIONS_9MAX = ['BTN', 'SB', 'BB', 'UTG', 'UTG+1', 'UTG+2', 'MP', 'MP+1', 'CO']
    POSITIONS_6MAX = ['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO']
    POSITIONS_3MAX = ['BTN', 'SB', 'BB']  # Heads-up and 3-handed

    # Position strength scores (higher = better position)
    POSITION_STRENGTH = {
        'BTN': 10, 'CO': 9, 'HJ': 8, 'MP+1': 7, 'MP': 6,
        'UTG+2': 5, 'UTG+1': 4, 'UTG': 3, 'SB': 2, 'BB': 1
    }

    @staticmethod
    def calculate_position(
        seat_number: int,
        button_seat: int,
        total_seats: int
    ) -> str:
        """
        Calculate position relative to button.

        Args:
            seat_number: Player's seat (0-indexed)
            button_seat: Button position (0-indexed)
            total_seats: Total seats at table

        Returns:
            Position string (UTG, MP, CO, BTN, SB, BB)
        """
        # Calculate offset from button
        offset = (seat_number - button_seat) % total_seats

        # Select position names based on table size
        if total_seats <= 3:
            positions = PositionCalculator.POSITIONS_3MAX
        elif total_seats <= 6:
            positions = PositionCalculator.POSITIONS_6MAX
        else:
            positions = PositionCalculator.POSITIONS_9MAX

        # Map offset to position
        if offset < len(positions):
            return positions[offset]
        return f"Seat{seat_number}"

    @staticmethod
    def is_late_position(position: str) -> bool:
        """Check if position is late (CO, BTN, HJ)."""
        return position in ['CO', 'BTN', 'HJ']

    @staticmethod
    def is_early_position(position: str) -> bool:
        """Check if position is early (UTG, UTG+1, UTG+2)."""
        return position.startswith('UTG')

    @staticmethod
    def is_middle_position(position: str) -> bool:
        """Check if position is middle (MP, MP+1, MP+2)."""
        return position.startswith('MP')

    @staticmethod
    def is_blind(position: str) -> bool:
        """Check if position is in the blinds (SB, BB)."""
        return position in ['SB', 'BB']

    @staticmethod
    def get_position_strength(position: str) -> int:
        """
        Get numerical strength of position (higher = better).

        Args:
            position: Position name

        Returns:
            Strength score (0-10)
        """
        return PositionCalculator.POSITION_STRENGTH.get(position, 0)

    @staticmethod
    def get_position_category(position: str) -> str:
        """
        Get position category for stats tracking.

        Args:
            position: Position name

        Returns:
            Category: "EARLY", "MIDDLE", "LATE", or "BLINDS"
        """
        if PositionCalculator.is_early_position(position):
            return "EARLY"
        elif PositionCalculator.is_middle_position(position):
            return "MIDDLE"
        elif PositionCalculator.is_late_position(position):
            return "LATE"
        elif PositionCalculator.is_blind(position):
            return "BLINDS"
        else:
            return "UNKNOWN"

    @staticmethod
    def is_in_position(player_pos: str, opponent_pos: str) -> bool:
        """
        Check if player is in position relative to opponent.

        Args:
            player_pos: Player's position
            opponent_pos: Opponent's position

        Returns:
            True if player acts after opponent (in position)
        """
        player_strength = PositionCalculator.get_position_strength(player_pos)
        opponent_strength = PositionCalculator.get_position_strength(opponent_pos)
        return player_strength > opponent_strength

    @staticmethod
    def get_opening_range_multiplier(position: str) -> float:
        """
        Get range adjustment multiplier for opening raises by position.

        Args:
            position: Position name

        Returns:
            Multiplier (0.5 = tighten by 50%, 1.5 = widen by 50%)

        Example:
            If base range is 20%:
            - UTG: 20% * 0.6 = 12% (tighter)
            - BTN: 20% * 1.4 = 28% (wider)
        """
        multipliers = {
            'BTN': 1.4, 'CO': 1.3, 'HJ': 1.1,
            'MP+1': 1.0, 'MP': 0.9,
            'UTG+2': 0.8, 'UTG+1': 0.7, 'UTG': 0.6,
            'SB': 1.2, 'BB': 0.0  # Don't open from BB
        }
        return multipliers.get(position, 1.0)

    @staticmethod
    def get_all_positions(button_seat: int, total_seats: int) -> Dict[int, str]:
        """
        Get position names for all seats at the table.

        Args:
            button_seat: Dealer button seat number
            total_seats: Total number of seats

        Returns:
            Dictionary mapping seat_number -> position_name
        """
        positions = {}
        for seat in range(total_seats):
            positions[seat] = PositionCalculator.calculate_position(
                seat, button_seat, total_seats
            )
        return positions
