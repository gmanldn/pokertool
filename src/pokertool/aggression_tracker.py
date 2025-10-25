#!/usr/bin/env python3
"""
Aggression Tracker
=================

Tracks player aggression levels and patterns.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AggressiveAction(Enum):
    """Aggressive action types"""
    BET = "bet"
    RAISE = "raise"
    THREE_BET = "3bet"
    FOUR_BET = "4bet"
    FIVE_BET_PLUS = "5bet+"


class PassiveAction(Enum):
    """Passive action types"""
    CALL = "call"
    CHECK = "check"
    FOLD = "fold"


@dataclass
class ActionRecord:
    """Record of a poker action"""
    timestamp: datetime
    player_name: str
    action_type: str  # BET, RAISE, CALL, CHECK, FOLD
    amount: float
    street: str  # preflop, flop, turn, river
    action_id: int


class AggressionTracker:
    """Tracks player aggression patterns."""

    def __init__(self):
        """Initialize aggression tracker."""
        self.action_records: List[ActionRecord] = []
        self.action_count = 0

    def record_action(
        self,
        player_name: str,
        action_type: str,
        amount: float = 0.0,
        street: str = "preflop"
    ) -> ActionRecord:
        """
        Record a player action.

        Args:
            player_name: Player identifier
            action_type: Action type (BET, RAISE, CALL, CHECK, FOLD, etc.)
            amount: Bet/raise amount
            street: Street (preflop, flop, turn, river)

        Returns:
            ActionRecord object
        """
        self.action_count += 1
        record = ActionRecord(
            timestamp=datetime.now(),
            player_name=player_name,
            action_type=action_type.upper(),
            amount=amount,
            street=street.lower(),
            action_id=self.action_count
        )
        self.action_records.append(record)

        logger.debug(f"Recorded {action_type} for {player_name} on {street}")
        return record

    def get_player_actions(self, player_name: str) -> List[ActionRecord]:
        """Get all actions for a player."""
        return [r for r in self.action_records if r.player_name == player_name]

    def get_aggressive_actions(
        self,
        player_name: Optional[str] = None,
        street: Optional[str] = None
    ) -> int:
        """
        Count aggressive actions (bet/raise).

        Args:
            player_name: Player identifier (None for all)
            street: Street filter (None for all)

        Returns:
            Count of aggressive actions
        """
        records = self.action_records
        if player_name:
            records = [r for r in records if r.player_name == player_name]
        if street:
            records = [r for r in records if r.street == street.lower()]

        return sum(1 for r in records if r.action_type in ['BET', 'RAISE', '3BET', '4BET', '5BET+'])

    def get_passive_actions(
        self,
        player_name: Optional[str] = None,
        street: Optional[str] = None
    ) -> int:
        """
        Count passive actions (call/check).

        Args:
            player_name: Player identifier (None for all)
            street: Street filter (None for all)

        Returns:
            Count of passive actions
        """
        records = self.action_records
        if player_name:
            records = [r for r in records if r.player_name == player_name]
        if street:
            records = [r for r in records if r.street == street.lower()]

        return sum(1 for r in records if r.action_type in ['CALL', 'CHECK'])

    def get_aggression_factor(
        self,
        player_name: Optional[str] = None,
        street: Optional[str] = None
    ) -> float:
        """
        Calculate aggression factor (aggressive actions / passive actions).

        Args:
            player_name: Player identifier (None for all)
            street: Street filter (None for all)

        Returns:
            Aggression factor (0.0 if no passive actions)
        """
        aggressive = self.get_aggressive_actions(player_name, street)
        passive = self.get_passive_actions(player_name, street)

        if passive == 0:
            return 0.0

        return round(aggressive / passive, 2)

    def get_aggression_frequency(
        self,
        player_name: Optional[str] = None,
        street: Optional[str] = None
    ) -> float:
        """
        Calculate aggression frequency (% of actions that are aggressive).

        Args:
            player_name: Player identifier (None for all)
            street: Street filter (None for all)

        Returns:
            Aggression frequency as percentage (0.0 - 100.0)
        """
        records = self.action_records
        if player_name:
            records = [r for r in records if r.player_name == player_name]
        if street:
            records = [r for r in records if r.street == street.lower()]

        # Exclude folds from frequency calculation
        non_fold_records = [r for r in records if r.action_type != 'FOLD']

        if not non_fold_records:
            return 0.0

        aggressive = sum(1 for r in non_fold_records
                        if r.action_type in ['BET', 'RAISE', '3BET', '4BET', '5BET+'])

        return round((aggressive / len(non_fold_records)) * 100, 2)

    def get_three_bet_percentage(self, player_name: str) -> float:
        """
        Calculate 3-bet percentage for preflop.

        Args:
            player_name: Player identifier

        Returns:
            3-bet percentage (0.0 - 100.0)
        """
        preflop_actions = [r for r in self.get_player_actions(player_name)
                          if r.street == 'preflop']

        # Count opportunities (facing a raise)
        total_opportunities = len([r for r in preflop_actions
                                   if r.action_type in ['3BET', 'CALL', 'FOLD']])

        if total_opportunities == 0:
            return 0.0

        three_bets = sum(1 for r in preflop_actions if r.action_type == '3BET')

        return round((three_bets / total_opportunities) * 100, 2)

    def get_continuation_bet_frequency(self, player_name: str) -> float:
        """
        Calculate continuation bet frequency on flop.

        Args:
            player_name: Player identifier

        Returns:
            C-bet frequency as percentage (0.0 - 100.0)
        """
        flop_actions = [r for r in self.get_player_actions(player_name)
                       if r.street == 'flop']

        if not flop_actions:
            return 0.0

        cbets = sum(1 for r in flop_actions if r.action_type == 'BET')

        return round((cbets / len(flop_actions)) * 100, 2)

    def get_avg_bet_size(
        self,
        player_name: Optional[str] = None,
        street: Optional[str] = None
    ) -> float:
        """
        Calculate average bet/raise size.

        Args:
            player_name: Player identifier (None for all)
            street: Street filter (None for all)

        Returns:
            Average bet size
        """
        records = self.action_records
        if player_name:
            records = [r for r in records if r.player_name == player_name]
        if street:
            records = [r for r in records if r.street == street.lower()]

        bet_records = [r for r in records
                      if r.action_type in ['BET', 'RAISE', '3BET', '4BET', '5BET+']
                      and r.amount > 0]

        if not bet_records:
            return 0.0

        avg = sum(r.amount for r in bet_records) / len(bet_records)
        return round(avg, 2)

    def get_total_bet_amount(
        self,
        player_name: Optional[str] = None,
        street: Optional[str] = None
    ) -> float:
        """
        Get total amount bet/raised.

        Args:
            player_name: Player identifier (None for all)
            street: Street filter (None for all)

        Returns:
            Total bet amount
        """
        records = self.action_records
        if player_name:
            records = [r for r in records if r.player_name == player_name]
        if street:
            records = [r for r in records if r.street == street.lower()]

        total = sum(r.amount for r in records
                   if r.action_type in ['BET', 'RAISE', '3BET', '4BET', '5BET+'])

        return round(total, 2)

    def get_street_breakdown(self, player_name: str) -> Dict[str, Dict[str, any]]:
        """
        Get aggression breakdown by street.

        Args:
            player_name: Player identifier

        Returns:
            Dictionary mapping streets to aggression metrics
        """
        streets = ['preflop', 'flop', 'turn', 'river']
        breakdown = {}

        for street in streets:
            breakdown[street] = {
                "aggressive_actions": self.get_aggressive_actions(player_name, street),
                "passive_actions": self.get_passive_actions(player_name, street),
                "aggression_factor": self.get_aggression_factor(player_name, street),
                "aggression_frequency": self.get_aggression_frequency(player_name, street),
                "avg_bet_size": self.get_avg_bet_size(player_name, street)
            }

        return breakdown

    def get_player_statistics(self, player_name: str) -> Dict[str, any]:
        """
        Get comprehensive aggression statistics for player.

        Args:
            player_name: Player identifier

        Returns:
            Statistics dictionary
        """
        total_actions = len(self.get_player_actions(player_name))

        if total_actions == 0:
            return {
                "player_name": player_name,
                "total_actions": 0,
                "aggressive_actions": 0,
                "passive_actions": 0,
                "aggression_factor": 0.0,
                "aggression_frequency": 0.0,
                "three_bet_pct": 0.0,
                "cbet_frequency": 0.0,
                "avg_bet_size": 0.0,
                "total_bet": 0.0
            }

        return {
            "player_name": player_name,
            "total_actions": total_actions,
            "aggressive_actions": self.get_aggressive_actions(player_name),
            "passive_actions": self.get_passive_actions(player_name),
            "aggression_factor": self.get_aggression_factor(player_name),
            "aggression_frequency": self.get_aggression_frequency(player_name),
            "three_bet_pct": self.get_three_bet_percentage(player_name),
            "cbet_frequency": self.get_continuation_bet_frequency(player_name),
            "avg_bet_size": self.get_avg_bet_size(player_name),
            "total_bet": self.get_total_bet_amount(player_name)
        }

    def get_all_players(self) -> List[str]:
        """Get list of all players."""
        return sorted(list(set(r.player_name for r in self.action_records)))

    def get_most_aggressive_player(self) -> Optional[str]:
        """
        Find most aggressive player by aggression factor.

        Returns:
            Player name, or None if no players
        """
        players = self.get_all_players()
        if not players:
            return None

        most_aggressive = None
        highest_af = 0.0

        for player in players:
            af = self.get_aggression_factor(player)
            if af > highest_af:
                highest_af = af
                most_aggressive = player

        return most_aggressive

    def reset(self):
        """Reset tracker."""
        self.action_records.clear()
        self.action_count = 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    tracker = AggressionTracker()

    # Record some actions
    tracker.record_action("Alice", "RAISE", 10.0, "preflop")
    tracker.record_action("Alice", "BET", 15.0, "flop")
    tracker.record_action("Alice", "CALL", 10.0, "turn")

    tracker.record_action("Bob", "CALL", 10.0, "preflop")
    tracker.record_action("Bob", "CHECK", 0.0, "flop")
    tracker.record_action("Bob", "FOLD", 0.0, "turn")

    # Get stats
    alice_stats = tracker.get_player_statistics("Alice")
    print(f"\nAlice's aggression stats:")
    print(f"  Aggression factor: {alice_stats['aggression_factor']}")
    print(f"  Aggression frequency: {alice_stats['aggression_frequency']}%")
    print(f"  Average bet size: ${alice_stats['avg_bet_size']}")

    bob_stats = tracker.get_player_statistics("Bob")
    print(f"\nBob's aggression stats:")
    print(f"  Aggression factor: {bob_stats['aggression_factor']}")
    print(f"  Aggression frequency: {bob_stats['aggression_frequency']}%")

    most_aggressive = tracker.get_most_aggressive_player()
    print(f"\nMost aggressive player: {most_aggressive}")
