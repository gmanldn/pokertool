"""Relative Position Calculator"""
from typing import List, Optional

class PositionCalculator:
    """Calculate relative positions at poker table."""
    
    POSITIONS_9MAX = ['UTG', 'UTG+1', 'UTG+2', 'MP', 'MP+1', 'CO', 'BTN', 'SB', 'BB']
    POSITIONS_6MAX = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
    
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
        
        # Select position names
        if total_seats <= 6:
            positions = PositionCalculator.POSITIONS_6MAX
        else:
            positions = PositionCalculator.POSITIONS_9MAX
        
        # Map offset to position
        if offset < len(positions):
            return positions[offset]
        return f"Seat{seat_number}"
    
    @staticmethod
    def is_late_position(position: str) -> bool:
        """Check if position is late (CO, BTN)."""
        return position in ['CO', 'BTN']
    
    @staticmethod
    def is_early_position(position: str) -> bool:
        """Check if position is early (UTG, UTG+1, UTG+2)."""
        return position.startswith('UTG')
