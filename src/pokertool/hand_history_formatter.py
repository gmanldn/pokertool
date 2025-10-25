#!/usr/bin/env python3
"""
Hand History Formatter
=====================

Formats and exports poker hand histories.
"""

import logging
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class HandHistory:
    """Hand history record"""
    hand_id: int
    timestamp: datetime
    players: List[str]
    actions: List[str]
    winner: str
    pot_size: float


class HandHistoryFormatter:
    """Formats hand histories for export."""

    def __init__(self):
        """Initialize formatter."""
        self.histories: List[HandHistory] = []

    def add_hand(
        self,
        players: List[str],
        actions: List[str],
        winner: str,
        pot_size: float
    ) -> HandHistory:
        """Add a hand history."""
        hand = HandHistory(
            hand_id=len(self.histories) + 1,
            timestamp=datetime.now(),
            players=players.copy(),
            actions=actions.copy(),
            winner=winner,
            pot_size=pot_size
        )
        self.histories.append(hand)
        return hand

    def format_hand(self, hand: HandHistory) -> str:
        """Format single hand as text."""
        lines = [
            f"Hand #{hand.hand_id}",
            f"Time: {hand.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Players: {', '.join(hand.players)}",
            "Actions:",
        ]
        lines.extend(f"  {action}" for action in hand.actions)
        lines.append(f"Winner: {hand.winner}")
        lines.append(f"Pot: ${hand.pot_size}")
        return "\n".join(lines)

    def export_all(self) -> str:
        """Export all hands as formatted text."""
        if not self.histories:
            return "No hand histories recorded."

        return "\n\n".join(self.format_hand(h) for h in self.histories)

    def export_summary(self) -> str:
        """Export summary statistics."""
        if not self.histories:
            return "No data"

        total_pots = sum(h.pot_size for h in self.histories)
        avg_pot = total_pots / len(self.histories)

        return f"Total hands: {len(self.histories)}\nAvg pot: ${avg_pot:.2f}"

    def get_player_hands(self, player_name: str) -> List[HandHistory]:
        """Get all hands for a player."""
        return [h for h in self.histories if player_name in h.players]

    def reset(self):
        """Reset all histories."""
        self.histories.clear()


if __name__ == '__main__':
    formatter = HandHistoryFormatter()
    formatter.add_hand(
        ["Alice", "Bob"],
        ["Alice raises $10", "Bob calls $10", "Bob wins"],
        "Bob",
        20.0
    )
    print(formatter.export_all())
