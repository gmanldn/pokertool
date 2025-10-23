#!/usr/bin/env python3
"""Card history tracking to detect anomalies."""

from typing import Set, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class CardHistoryTracker:
    """Tracks cards seen in current session to detect duplicates/anomalies."""

    def __init__(self):
        """Initialize tracker."""
        self.session_cards: List[str] = []
        self.hand_cards: Set[str] = set()
        self.anomalies: List[str] = []

    def start_new_hand(self):
        """Start tracking a new hand."""
        self.hand_cards = set()

    def add_card(self, card: str) -> bool:
        """
        Add card to current hand.

        Args:
            card: Card string (e.g., 'As', 'Kh')

        Returns:
            True if card added successfully, False if duplicate detected
        """
        if card in self.hand_cards:
            anomaly = f"Duplicate card detected: {card}"
            self.anomalies.append(anomaly)
            logger.warning(anomaly)
            return False

        self.hand_cards.add(card)
        self.session_cards.append(card)
        return True

    def get_anomalies(self) -> List[str]:
        """Get list of detected anomalies."""
        return self.anomalies.copy()

    def reset(self):
        """Reset all tracking."""
        self.session_cards.clear()
        self.hand_cards.clear()
        self.anomalies.clear()


_tracker_instance: Optional[CardHistoryTracker] = None

def get_card_history_tracker() -> CardHistoryTracker:
    """Get global card history tracker."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = CardHistoryTracker()
    return _tracker_instance
