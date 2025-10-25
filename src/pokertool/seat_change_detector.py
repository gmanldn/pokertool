#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Seat Change Detector
===================

Detects when players change seats at the poker table.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SeatChange:
    """Record of a seat change"""
    timestamp: datetime
    player_name: str
    old_seat: int
    new_seat: int
    change_id: int


class SeatChangeDetector:
    """Detects and tracks player seat changes."""

    def __init__(self, table_size: int = 9):
        """
        Initialize detector.

        Args:
            table_size: Number of seats at table
        """
        self.table_size = table_size
        self.player_seats: Dict[str, int] = {}
        self.change_history: List[SeatChange] = []
        self.change_count = 0

    def update_player_seat(
        self,
        player_name: str,
        seat_number: int
    ) -> Optional[SeatChange]:
        """
        Update player's seat and detect changes.

        Args:
            player_name: Player identifier
            seat_number: New seat number

        Returns:
            SeatChange if change detected, None otherwise
        """
        # Validate seat number
        if not (0 <= seat_number < self.table_size):
            logger.warning(f"Invalid seat number {seat_number} for table size {self.table_size}")
            return None

        # Check for change
        if player_name in self.player_seats:
            old_seat = self.player_seats[player_name]
            if old_seat == seat_number:
                return None  # No change

            # Record change
            self.change_count += 1
            change = SeatChange(
                timestamp=datetime.now(),
                player_name=player_name,
                old_seat=old_seat,
                new_seat=seat_number,
                change_id=self.change_count
            )
            self.change_history.append(change)
            self.player_seats[player_name] = seat_number

            logger.info(f"{player_name} moved from seat {old_seat} → {seat_number}")
            return change
        else:
            # First time seeing player
            self.player_seats[player_name] = seat_number
            return None

    def get_player_seat(self, player_name: str) -> Optional[int]:
        """Get player's current seat."""
        return self.player_seats.get(player_name)

    def get_seat_occupant(self, seat_number: int) -> Optional[str]:
        """Get player at seat."""
        for player, seat in self.player_seats.items():
            if seat == seat_number:
                return player
        return None

    def get_player_changes(self, player_name: str) -> List[SeatChange]:
        """Get all seat changes for a player."""
        return [c for c in self.change_history if c.player_name == player_name]

    def get_statistics(self) -> Dict[str, any]:
        """Get seat change statistics."""
        if not self.change_history:
            return {
                "total_changes": 0,
                "unique_players": len(self.player_seats),
                "most_active_player": None
            }

        # Count changes per player
        player_changes = {}
        for change in self.change_history:
            player = change.player_name
            player_changes[player] = player_changes.get(player, 0) + 1

        most_active = max(player_changes, key=player_changes.get) if player_changes else None

        return {
            "total_changes": len(self.change_history),
            "unique_players": len(self.player_seats),
            "most_active_player": most_active
        }

    def reset(self):
        """Reset detector."""
        self.player_seats.clear()
        self.change_history.clear()
        self.change_count = 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    detector = SeatChangeDetector()

    print("Seat Change Detector - Example\n")

    detector.update_player_seat("Alice", 0)
    detector.update_player_seat("Bob", 1)
    change = detector.update_player_seat("Alice", 3)  # Alice changes seats

    if change:
        print(f"Detected: {change.player_name} moved to seat {change.new_seat}")

    stats = detector.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total changes: {stats['total_changes']}")
    print(f"  Unique players: {stats['unique_players']}")
