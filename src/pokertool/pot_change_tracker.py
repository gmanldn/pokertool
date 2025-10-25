#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pot Size Change Tracker
=======================

Tracks pot size changes frame-by-frame to detect bets, calls, raises, and rake.
Provides historical tracking and change detection for poker game analysis.
"""

import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Type of pot change"""
    BET = "bet"
    CALL = "call"
    RAISE = "raise"
    RAKE = "rake"
    RETURN = "return"  # Uncalled bet returned
    AWARD = "award"  # Pot awarded to winner
    UNKNOWN = "unknown"


@dataclass
class PotChange:
    """Represents a single pot size change"""
    timestamp: datetime
    previous_size: float
    new_size: float
    change_amount: float
    change_type: ChangeType
    frame_number: int
    confidence: float
    player_position: Optional[str] = None
    session_id: Optional[str] = None


class PotChangeTracker:
    """
    Tracks pot size changes over time for game analysis.
    """

    def __init__(self, rake_percentage: float = 0.05, min_change_threshold: float = 0.01):
        """
        Initialize pot change tracker.

        Args:
            rake_percentage: Expected rake percentage (default 5%)
            min_change_threshold: Minimum change to track (default $0.01)
        """
        self.rake_percentage = rake_percentage
        self.min_change_threshold = min_change_threshold
        self.current_pot_size = 0.0
        self.previous_pot_size = 0.0
        self.change_history: List[PotChange] = []
        self.frame_count = 0

    def update_pot_size(
        self,
        new_pot_size: float,
        confidence: float = 1.0,
        player_position: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[PotChange]:
        """
        Update pot size and detect changes.

        Args:
            new_pot_size: New pot size detected
            confidence: Detection confidence (0-1)
            player_position: Position of player who acted
            session_id: Current session ID

        Returns:
            PotChange object if significant change detected, None otherwise
        """
        self.frame_count += 1
        self.previous_pot_size = self.current_pot_size
        self.current_pot_size = new_pot_size

        change_amount = new_pot_size - self.previous_pot_size

        # Ignore insignificant changes
        if abs(change_amount) < self.min_change_threshold:
            return None

        # Classify change type
        change_type = self._classify_change(change_amount, self.previous_pot_size, new_pot_size)

        pot_change = PotChange(
            timestamp=datetime.now(),
            previous_size=self.previous_pot_size,
            new_size=new_pot_size,
            change_amount=change_amount,
            change_type=change_type,
            frame_number=self.frame_count,
            confidence=confidence,
            player_position=player_position,
            session_id=session_id
        )

        self.change_history.append(pot_change)

        logger.info(
            f"Pot change detected: {change_type.value} ${abs(change_amount):.2f} "
            f"({self.previous_pot_size:.2f} -> {new_pot_size:.2f})"
        )

        return pot_change

    def _classify_change(
        self,
        change_amount: float,
        previous_size: float,
        new_size: float
    ) -> ChangeType:
        """
        Classify the type of pot change.

        Args:
            change_amount: Amount of change
            previous_size: Previous pot size
            new_size: New pot size

        Returns:
            ChangeType classification
        """
        # Pot decreased
        if change_amount < 0:
            # Pot went to zero - awarded to winner
            if new_size == 0:
                return ChangeType.AWARD
            # Small decrease - likely rake
            rake_amount = previous_size * self.rake_percentage
            if abs(change_amount) <= rake_amount * 1.5:  # Within 50% of expected rake
                return ChangeType.RAKE
            # Large decrease - uncalled bet returned
            return ChangeType.RETURN

        # Pot increased
        if change_amount > 0:
            # First bet (pot was empty)
            if previous_size == 0 or previous_size < 0.01:
                return ChangeType.BET
            # Large increase relative to pot - likely a raise (more than 100% of pot)
            elif change_amount > previous_size:
                return ChangeType.RAISE
            # Moderate increase - likely a call (up to 100% of pot)
            else:
                return ChangeType.CALL

        return ChangeType.UNKNOWN

    def get_recent_changes(self, count: int = 10) -> List[PotChange]:
        """
        Get most recent pot changes.

        Args:
            count: Number of recent changes to retrieve

        Returns:
            List of recent PotChange objects
        """
        return self.change_history[-count:] if self.change_history else []

    def get_changes_by_type(self, change_type: ChangeType) -> List[PotChange]:
        """
        Get all changes of a specific type.

        Args:
            change_type: Type of change to filter

        Returns:
            List of matching PotChange objects
        """
        return [change for change in self.change_history if change.change_type == change_type]

    def get_total_action(self) -> float:
        """
        Calculate total action (sum of all bets, calls, raises).

        Returns:
            Total action amount
        """
        action_types = {ChangeType.BET, ChangeType.CALL, ChangeType.RAISE}
        return sum(
            change.change_amount
            for change in self.change_history
            if change.change_type in action_types
        )

    def get_total_rake(self) -> float:
        """
        Calculate total rake collected.

        Returns:
            Total rake amount
        """
        return sum(
            abs(change.change_amount)
            for change in self.change_history
            if change.change_type == ChangeType.RAKE
        )

    def get_action_by_position(self) -> Dict[str, float]:
        """
        Get total action grouped by position.

        Returns:
            Dictionary mapping position -> total action amount
        """
        position_action: Dict[str, float] = {}
        action_types = {ChangeType.BET, ChangeType.CALL, ChangeType.RAISE}

        for change in self.change_history:
            if change.change_type in action_types and change.player_position:
                position_action[change.player_position] = (
                    position_action.get(change.player_position, 0) + change.change_amount
                )

        return position_action

    def detect_anomalies(self, std_dev_threshold: float = 2.0) -> List[PotChange]:
        """
        Detect anomalous pot changes (unusually large or suspicious).

        Args:
            std_dev_threshold: Number of standard deviations for anomaly detection

        Returns:
            List of anomalous PotChange objects
        """
        if len(self.change_history) < 3:
            return []

        # Calculate mean and std dev of change amounts
        changes = [abs(c.change_amount) for c in self.change_history]
        mean_change = sum(changes) / len(changes)
        variance = sum((x - mean_change) ** 2 for x in changes) / len(changes)
        std_dev = variance ** 0.5

        threshold = mean_change + (std_dev_threshold * std_dev)

        anomalies = [
            change for change in self.change_history
            if abs(change.change_amount) > threshold
        ]

        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalous pot changes")

        return anomalies

    def reset(self):
        """Reset tracker state for new hand."""
        self.current_pot_size = 0.0
        self.previous_pot_size = 0.0
        self.change_history.clear()
        self.frame_count = 0

    def get_statistics(self) -> Dict[str, any]:
        """
        Get tracking statistics.

        Returns:
            Dictionary with tracker statistics
        """
        if not self.change_history:
            return {
                "total_changes": 0,
                "total_action": 0.0,
                "total_rake": 0.0,
                "avg_change": 0.0,
                "largest_change": 0.0
            }

        changes_by_type = {}
        for change_type in ChangeType:
            changes = self.get_changes_by_type(change_type)
            changes_by_type[change_type.value] = len(changes)

        change_amounts = [abs(c.change_amount) for c in self.change_history]

        return {
            "total_changes": len(self.change_history),
            "total_action": self.get_total_action(),
            "total_rake": self.get_total_rake(),
            "avg_change": sum(change_amounts) / len(change_amounts),
            "largest_change": max(change_amounts),
            "changes_by_type": changes_by_type,
            "action_by_position": self.get_action_by_position()
        }


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    tracker = PotChangeTracker(rake_percentage=0.05)

    # Simulate hand progression
    print("Simulating poker hand pot changes...\n")

    # Preflop betting
    tracker.update_pot_size(1.5, confidence=0.95, player_position="SB")  # SB posts
    tracker.update_pot_size(3.0, confidence=0.95, player_position="BB")  # BB posts
    tracker.update_pot_size(9.0, confidence=0.92, player_position="BTN")  # BTN raises to 9
    tracker.update_pot_size(12.0, confidence=0.94, player_position="SB")  # SB calls

    # Flop action
    tracker.update_pot_size(27.0, confidence=0.90, player_position="SB")  # SB bets
    tracker.update_pot_size(54.0, confidence=0.91, player_position="BTN")  # BTN raises

    # Turn (no action)

    # River action
    tracker.update_pot_size(104.0, confidence=0.89, player_position="SB")  # SB bets
    tracker.update_pot_size(0, confidence=1.0)  # Pot awarded

    # Get statistics
    stats = tracker.get_statistics()
    print("\nPot Change Statistics:")
    print(f"  Total changes: {stats['total_changes']}")
    print(f"  Total action: ${stats['total_action']:.2f}")
    print(f"  Average change: ${stats['avg_change']:.2f}")
    print(f"  Largest change: ${stats['largest_change']:.2f}")
    print(f"\nChanges by type:")
    for change_type, count in stats['changes_by_type'].items():
        if count > 0:
            print(f"  {change_type}: {count}")
