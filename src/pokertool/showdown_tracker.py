#!/usr/bin/env python3
"""
Showdown Tracker
===============

Tracks showdown events and player hand revelations.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ShowdownResult(Enum):
    """Showdown result types"""
    WON = "won"
    LOST = "lost"
    SPLIT = "split"


@dataclass
class ShowdownEvent:
    """Record of a showdown event"""
    timestamp: datetime
    player_name: str
    hole_cards: List[str]
    board_cards: List[str]
    hand_description: str
    result: ShowdownResult
    pot_won: float
    opponents_shown: int
    showdown_id: int


class ShowdownTracker:
    """Tracks showdown events and statistics."""

    def __init__(self):
        """Initialize showdown tracker."""
        self.showdown_events: List[ShowdownEvent] = []
        self.showdown_count = 0

    def record_showdown(
        self,
        player_name: str,
        hole_cards: List[str],
        board_cards: List[str],
        hand_description: str,
        result: ShowdownResult,
        pot_won: float = 0.0,
        opponents_shown: int = 1
    ) -> ShowdownEvent:
        """
        Record a showdown event.

        Args:
            player_name: Player identifier
            hole_cards: Player's hole cards
            board_cards: Community cards
            hand_description: Description of final hand
            result: Showdown result (won/lost/split)
            pot_won: Amount won
            opponents_shown: Number of opponents who showed

        Returns:
            ShowdownEvent object
        """
        self.showdown_count += 1
        event = ShowdownEvent(
            timestamp=datetime.now(),
            player_name=player_name,
            hole_cards=hole_cards.copy(),
            board_cards=board_cards.copy(),
            hand_description=hand_description,
            result=result,
            pot_won=pot_won,
            opponents_shown=opponents_shown,
            showdown_id=self.showdown_count
        )
        self.showdown_events.append(event)

        logger.debug(f"Recorded showdown for {player_name}: {hand_description} ({result.value})")
        return event

    def get_player_showdowns(self, player_name: str) -> List[ShowdownEvent]:
        """
        Get all showdown events for a player.

        Args:
            player_name: Player identifier

        Returns:
            List of ShowdownEvent objects
        """
        return [e for e in self.showdown_events if e.player_name == player_name]

    def get_showdown_win_rate(self, player_name: Optional[str] = None) -> float:
        """
        Calculate showdown win rate.

        Args:
            player_name: Player identifier (None for all players)

        Returns:
            Win rate as percentage (0.0 - 100.0)
        """
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        if not events:
            return 0.0

        wins = sum(1 for e in events if e.result == ShowdownResult.WON)
        return round((wins / len(events)) * 100, 2)

    def get_total_showdowns(self, player_name: Optional[str] = None) -> int:
        """
        Get total number of showdowns.

        Args:
            player_name: Player identifier (None for all)

        Returns:
            Total showdown count
        """
        if player_name:
            return len(self.get_player_showdowns(player_name))
        return len(self.showdown_events)

    def get_showdown_wins(self, player_name: Optional[str] = None) -> int:
        """Get number of showdown wins."""
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        return sum(1 for e in events if e.result == ShowdownResult.WON)

    def get_showdown_losses(self, player_name: Optional[str] = None) -> int:
        """Get number of showdown losses."""
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        return sum(1 for e in events if e.result == ShowdownResult.LOST)

    def get_showdown_splits(self, player_name: Optional[str] = None) -> int:
        """Get number of showdown splits."""
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        return sum(1 for e in events if e.result == ShowdownResult.SPLIT)

    def get_total_won_at_showdown(self, player_name: Optional[str] = None) -> float:
        """
        Get total amount won at showdown.

        Args:
            player_name: Player identifier (None for all)

        Returns:
            Total amount won
        """
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        total = sum(e.pot_won for e in events)
        return round(total, 2)

    def get_avg_pot_won(self, player_name: Optional[str] = None) -> float:
        """
        Get average pot won at showdown.

        Args:
            player_name: Player identifier (None for all)

        Returns:
            Average pot amount
        """
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        winning_events = [e for e in events if e.result == ShowdownResult.WON]
        if not winning_events:
            return 0.0

        avg = sum(e.pot_won for e in winning_events) / len(winning_events)
        return round(avg, 2)

    def get_hand_types_shown(self, player_name: str) -> Dict[str, int]:
        """
        Get distribution of hand types shown.

        Args:
            player_name: Player identifier

        Returns:
            Dictionary mapping hand descriptions to counts
        """
        events = self.get_player_showdowns(player_name)
        hand_types = {}

        for event in events:
            hand_types[event.hand_description] = hand_types.get(event.hand_description, 0) + 1

        return hand_types

    def get_most_common_showdown_hand(self, player_name: str) -> Optional[str]:
        """
        Get most commonly shown hand type.

        Args:
            player_name: Player identifier

        Returns:
            Hand description, or None if no showdowns
        """
        hand_types = self.get_hand_types_shown(player_name)
        if not hand_types:
            return None

        return max(hand_types, key=hand_types.get)

    def get_multiway_showdowns(self, player_name: Optional[str] = None) -> int:
        """
        Get number of multiway showdowns (3+ players).

        Args:
            player_name: Player identifier (None for all)

        Returns:
            Count of multiway showdowns
        """
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        return sum(1 for e in events if e.opponents_shown >= 2)

    def get_heads_up_showdowns(self, player_name: Optional[str] = None) -> int:
        """
        Get number of heads-up showdowns.

        Args:
            player_name: Player identifier (None for all)

        Returns:
            Count of heads-up showdowns
        """
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        return sum(1 for e in events if e.opponents_shown == 1)

    def get_player_statistics(self, player_name: str) -> Dict[str, any]:
        """
        Get comprehensive showdown statistics for player.

        Args:
            player_name: Player identifier

        Returns:
            Statistics dictionary
        """
        total = self.get_total_showdowns(player_name)

        if total == 0:
            return {
                "player_name": player_name,
                "total_showdowns": 0,
                "wins": 0,
                "losses": 0,
                "splits": 0,
                "win_rate": 0.0,
                "total_won": 0.0,
                "avg_pot_won": 0.0,
                "most_common_hand": None,
                "heads_up_showdowns": 0,
                "multiway_showdowns": 0
            }

        return {
            "player_name": player_name,
            "total_showdowns": total,
            "wins": self.get_showdown_wins(player_name),
            "losses": self.get_showdown_losses(player_name),
            "splits": self.get_showdown_splits(player_name),
            "win_rate": self.get_showdown_win_rate(player_name),
            "total_won": self.get_total_won_at_showdown(player_name),
            "avg_pot_won": self.get_avg_pot_won(player_name),
            "most_common_hand": self.get_most_common_showdown_hand(player_name),
            "heads_up_showdowns": self.get_heads_up_showdowns(player_name),
            "multiway_showdowns": self.get_multiway_showdowns(player_name)
        }

    def get_recent_showdowns(
        self,
        limit: int = 10,
        player_name: Optional[str] = None
    ) -> List[ShowdownEvent]:
        """
        Get recent showdown events.

        Args:
            limit: Maximum number to return
            player_name: Filter by player (None for all)

        Returns:
            List of recent ShowdownEvent objects
        """
        events = self.showdown_events
        if player_name:
            events = self.get_player_showdowns(player_name)

        return events[-limit:]

    def get_all_players(self) -> List[str]:
        """Get list of all players with showdowns."""
        return sorted(list(set(e.player_name for e in self.showdown_events)))

    def get_overall_statistics(self) -> Dict[str, any]:
        """
        Get overall showdown statistics.

        Returns:
            Statistics dictionary
        """
        if not self.showdown_events:
            return {
                "total_showdowns": 0,
                "total_players": 0,
                "overall_win_rate": 0.0,
                "total_pot_won": 0.0,
                "most_active_player": None
            }

        players = self.get_all_players()

        # Find most active player
        most_active = None
        most_showdowns = 0
        for player in players:
            showdowns = self.get_total_showdowns(player)
            if showdowns > most_showdowns:
                most_showdowns = showdowns
                most_active = player

        return {
            "total_showdowns": len(self.showdown_events),
            "total_players": len(players),
            "overall_win_rate": self.get_showdown_win_rate(),
            "total_pot_won": self.get_total_won_at_showdown(),
            "most_active_player": most_active
        }

    def reset(self):
        """Reset tracker."""
        self.showdown_events.clear()
        self.showdown_count = 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    tracker = ShowdownTracker()

    # Record some showdowns
    tracker.record_showdown(
        "Alice",
        ["Ah", "Kh"],
        ["Qh", "Jh", "Th", "5c", "2d"],
        "Royal Flush",
        ShowdownResult.WON,
        pot_won=100.0,
        opponents_shown=2
    )

    tracker.record_showdown(
        "Alice",
        ["Ks", "Kh"],
        ["Kd", "7c", "2h", "5s", "9d"],
        "Three of a Kind",
        ShowdownResult.LOST,
        pot_won=0.0,
        opponents_shown=1
    )

    # Get stats
    stats = tracker.get_player_statistics("Alice")
    print(f"\nAlice's showdown stats:")
    print(f"  Total showdowns: {stats['total_showdowns']}")
    print(f"  Win rate: {stats['win_rate']}%")
    print(f"  Total won: ${stats['total_won']}")
    print(f"  Most common hand: {stats['most_common_hand']}")
