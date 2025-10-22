"""Button Movement Tracker - Track dealer button as it moves"""
from typing import Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ButtonPosition:
    seat_number: int
    timestamp: float
    confidence: float

class ButtonMovementTracker:
    """Track button movement for validation and anomaly detection."""
    
    def __init__(self, max_history: int = 50):
        self.history: List[ButtonPosition] = []
        self.max_history = max_history
        self.current_position: Optional[int] = None
    
    def update(self, seat_number: int, confidence: float = 1.0):
        """Update button position."""
        import time
        
        # Validate movement
        if self.current_position is not None:
            if not self._is_valid_movement(self.current_position, seat_number):
                logger.warning(
                    f"Invalid button movement detected: {self.current_position} -> {seat_number}"
                )
                return False
        
        # Record position
        self.history.append(ButtonPosition(seat_number, time.time(), confidence))
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        self.current_position = seat_number
        logger.debug(f"Button moved to seat {seat_number}")
        return True
    
    def _is_valid_movement(self, from_seat: int, to_seat: int) -> bool:
        """Validate button movement (should move clockwise by 1)."""
        # Allow button to move by 1 position or stay same
        diff = abs(to_seat - from_seat)
        return diff <= 1 or diff == 8  # Wraps around 9-max table
    
    def get_movement_pattern(self) -> List[int]:
        """Get recent button movement pattern."""
        return [pos.seat_number for pos in self.history[-10:]]
