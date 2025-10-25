#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Button Movement Tracker
======================

Tracks dealer button movement around the poker table to monitor
hand progression and position changes.
"""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MovementType(str, Enum):
    """Type of button movement"""
    NORMAL = "normal"          # Regular clockwise movement
    SKIP = "skip"              # Button skipped seat(s)
    BACKWARD = "backward"      # Button moved backwards (unusual)
    SAME = "same"              # Button didn't move (heads-up)
    INITIAL = "initial"        # First button position detected
    UNKNOWN = "unknown"


@dataclass
class ButtonMovement:
    """Represents a button position change"""
    timestamp: datetime
    previous_seat: Optional[int]
    new_seat: int
    movement_type: MovementType
    seats_moved: int
    table_size: int
    frame_number: int
    confidence: float


class ButtonMovementTracker:
    """
    Tracks dealer button position changes for hand progression analysis.
    """

    def __init__(self, table_size: int = 9, auto_detect_size: bool = True):
        """
        Initialize button movement tracker.

        Args:
            table_size: Expected table size (number of seats)
            auto_detect_size: Auto-detect table size from button positions
        """
        self.table_size = table_size
        self.auto_detect_size = auto_detect_size
        self.current_button_seat: Optional[int] = None
        self.previous_button_seat: Optional[int] = None
        self.movement_history: List[ButtonMovement] = []
        self.frame_count = 0
        self.hands_tracked = 0

    def update_button_position(
        self,
        seat_number: int,
        confidence: float = 1.0,
        table_size: Optional[int] = None
    ) -> Optional[ButtonMovement]:
        """
        Update button position and detect movement.

        Args:
            seat_number: New button seat number (0-indexed)
            confidence: Detection confidence (0-1)
            table_size: Override table size if provided

        Returns:
            ButtonMovement if movement detected, None if no change
        """
        self.frame_count += 1

        # Update table size if provided
        if table_size is not None:
            self.table_size = table_size

        # Validate seat number
        if seat_number < 0 or seat_number >= self.table_size:
            logger.warning(
                f"Invalid seat number {seat_number} for table size {self.table_size}"
            )
            return None

        # Check if position changed
        if self.current_button_seat == seat_number:
            return None  # No movement

        # Calculate movement
        self.previous_button_seat = self.current_button_seat
        movement_type, seats_moved = self._classify_movement(
            self.previous_button_seat,
            seat_number
        )

        # Create movement record
        movement = ButtonMovement(
            timestamp=datetime.now(),
            previous_seat=self.previous_button_seat,
            new_seat=seat_number,
            movement_type=movement_type,
            seats_moved=seats_moved,
            table_size=self.table_size,
            frame_number=self.frame_count,
            confidence=confidence
        )

        # Update state
        self.current_button_seat = seat_number
        self.movement_history.append(movement)

        # Count hands (each button movement = new hand, except initial)
        if movement_type != MovementType.INITIAL:
            self.hands_tracked += 1

        logger.info(
            f"Button moved: {movement_type.value} "
            f"(seat {self.previous_button_seat} → {seat_number}, "
            f"moved {seats_moved})"
        )

        return movement

    def _classify_movement(
        self,
        previous_seat: Optional[int],
        new_seat: int
    ) -> tuple[MovementType, int]:
        """
        Classify the type of button movement.

        Args:
            previous_seat: Previous button position
            new_seat: New button position

        Returns:
            Tuple of (movement_type, seats_moved)
        """
        # Initial position
        if previous_seat is None:
            return MovementType.INITIAL, 0

        # Calculate seats moved (clockwise)
        seats_moved = (new_seat - previous_seat) % self.table_size

        # No movement (heads-up button can stay)
        if seats_moved == 0:
            return MovementType.SAME, 0

        # Normal clockwise movement (1 seat)
        if seats_moved == 1:
            return MovementType.NORMAL, 1

        # Backward movement (counter-clockwise) - more than half table
        if seats_moved > self.table_size // 2:
            # Convert to negative (backward) distance
            backward_seats = self.table_size - seats_moved
            return MovementType.BACKWARD, -backward_seats

        # Skip seats (moved more than 1 clockwise, but not backwards)
        if 1 < seats_moved <= self.table_size // 2:
            return MovementType.SKIP, seats_moved

        return MovementType.UNKNOWN, seats_moved

    def get_current_position(self) -> Optional[int]:
        """Get current button seat number."""
        return self.current_button_seat

    def get_recent_movements(self, count: int = 10) -> List[ButtonMovement]:
        """
        Get most recent button movements.

        Args:
            count: Number of recent movements to retrieve

        Returns:
            List of recent ButtonMovement objects
        """
        return self.movement_history[-count:] if self.movement_history else []

    def get_movements_by_type(self, movement_type: MovementType) -> List[ButtonMovement]:
        """
        Get all movements of a specific type.

        Args:
            movement_type: Type of movement to filter

        Returns:
            List of matching ButtonMovement objects
        """
        return [m for m in self.movement_history if m.movement_type == movement_type]

    def get_position_frequency(self) -> Dict[int, int]:
        """
        Get frequency of button being at each seat.

        Returns:
            Dictionary mapping seat_number -> count
        """
        frequency: Dict[int, int] = {}
        for movement in self.movement_history:
            seat = movement.new_seat
            frequency[seat] = frequency.get(seat, 0) + 1
        return frequency

    def detect_anomalies(self) -> List[ButtonMovement]:
        """
        Detect anomalous button movements (skips, backwards, etc.).

        Returns:
            List of anomalous ButtonMovement objects
        """
        anomalies = []
        anomaly_types = {MovementType.SKIP, MovementType.BACKWARD, MovementType.UNKNOWN}

        for movement in self.movement_history:
            if movement.movement_type in anomaly_types:
                anomalies.append(movement)

        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalous button movements")

        return anomalies

    def get_statistics(self) -> Dict[str, any]:
        """
        Get button movement statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.movement_history:
            return {
                "total_movements": 0,
                "hands_tracked": 0,
                "movements_by_type": {},
                "current_position": None,
                "avg_confidence": 0.0,
                "anomalies": 0
            }

        movements_by_type = {}
        for movement_type in MovementType:
            movements = self.get_movements_by_type(movement_type)
            if movements:
                movements_by_type[movement_type.value] = len(movements)

        avg_confidence = sum(m.confidence for m in self.movement_history) / len(self.movement_history)
        anomalies = len(self.detect_anomalies())

        return {
            "total_movements": len(self.movement_history),
            "hands_tracked": self.hands_tracked,
            "movements_by_type": movements_by_type,
            "current_position": self.current_button_seat,
            "table_size": self.table_size,
            "avg_confidence": round(avg_confidence, 3),
            "anomalies": anomalies,
            "position_frequency": self.get_position_frequency()
        }

    def reset(self):
        """Reset tracker for new session."""
        self.current_button_seat = None
        self.previous_button_seat = None
        self.movement_history.clear()
        self.frame_count = 0
        self.hands_tracked = 0


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    tracker = ButtonMovementTracker(table_size=9)

    print("Button Movement Tracker - Example\n")

    # Simulate button progression around a 9-max table
    tracker.update_button_position(0, confidence=0.95)  # Initial
    tracker.update_button_position(1, confidence=0.93)  # Hand 1
    tracker.update_button_position(2, confidence=0.94)  # Hand 2
    tracker.update_button_position(3, confidence=0.92)  # Hand 3
    tracker.update_button_position(5, confidence=0.90)  # Skip seat 4
    tracker.update_button_position(6, confidence=0.91)  # Hand 5
    tracker.update_button_position(7, confidence=0.93)  # Hand 6
    tracker.update_button_position(8, confidence=0.94)  # Hand 7
    tracker.update_button_position(0, confidence=0.95)  # Back to start

    stats = tracker.get_statistics()
    print("\nStatistics:")
    print(f"  Total movements: {stats['total_movements']}")
    print(f"  Hands tracked: {stats['hands_tracked']}")
    print(f"  Current position: {stats['current_position']}")
    print(f"  Anomalies: {stats['anomalies']}")
    print(f"  Average confidence: {stats['avg_confidence']}")
    print(f"\nMovements by type:")
    for movement_type, count in stats['movements_by_type'].items():
        print(f"  {movement_type}: {count}")
