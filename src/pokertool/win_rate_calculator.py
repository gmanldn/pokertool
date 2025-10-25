#!/usr/bin/env python3
"""
Win Rate Calculator
==================

Calculates and tracks win rates for poker hands.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HandResult(Enum):
    """Possible hand results"""
    WIN = "win"
    LOSS = "loss"
    TIE = "tie"


@dataclass
class HandRecord:
    """Record of a single hand result"""
    timestamp: datetime
    player_name: str
    result: HandResult
    amount_won: float
    hand_id: int
    position: Optional[str] = None
    hand_type: Optional[str] = None


class WinRateCalculator:
    """Calculates and tracks win rates."""

    def __init__(self):
        """Initialize calculator."""
        self.hand_records: List[HandRecord] = []
        self.hand_count = 0

    def record_hand(
        self,
        player_name: str,
        result: HandResult,
        amount_won: float = 0.0,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> HandRecord:
        """
        Record a hand result.

        Args:
            player_name: Player identifier
            result: Hand result (win/loss/tie)
            amount_won: Amount won (negative for losses)
            position: Player position (BTN, CO, etc.)
            hand_type: Hand type (AA, KK, etc.)

        Returns:
            HandRecord object
        """
        self.hand_count += 1
        record = HandRecord(
            timestamp=datetime.now(),
            player_name=player_name,
            result=result,
            amount_won=amount_won,
            hand_id=self.hand_count,
            position=position,
            hand_type=hand_type
        )
        self.hand_records.append(record)
        logger.debug(f"Recorded {result.value} for {player_name}")
        return record

    def get_win_rate(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> float:
        """
        Calculate win rate percentage.

        Args:
            player_name: Filter by player
            position: Filter by position
            hand_type: Filter by hand type

        Returns:
            Win rate as percentage (0.0 - 100.0)
        """
        filtered = self._filter_records(player_name, position, hand_type)

        if not filtered:
            return 0.0

        wins = sum(1 for r in filtered if r.result == HandResult.WIN)
        return round((wins / len(filtered)) * 100, 2)

    def get_total_hands(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> int:
        """Get total hands played with optional filters."""
        filtered = self._filter_records(player_name, position, hand_type)
        return len(filtered)

    def get_wins(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> int:
        """Get total wins with optional filters."""
        filtered = self._filter_records(player_name, position, hand_type)
        return sum(1 for r in filtered if r.result == HandResult.WIN)

    def get_losses(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> int:
        """Get total losses with optional filters."""
        filtered = self._filter_records(player_name, position, hand_type)
        return sum(1 for r in filtered if r.result == HandResult.LOSS)

    def get_ties(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> int:
        """Get total ties with optional filters."""
        filtered = self._filter_records(player_name, position, hand_type)
        return sum(1 for r in filtered if r.result == HandResult.TIE)

    def get_total_winnings(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> float:
        """Get total amount won/lost with optional filters."""
        filtered = self._filter_records(player_name, position, hand_type)
        total = sum(r.amount_won for r in filtered)
        return round(total, 2)

    def get_avg_win_amount(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> float:
        """Get average amount won per winning hand."""
        filtered = self._filter_records(player_name, position, hand_type)
        wins = [r for r in filtered if r.result == HandResult.WIN]

        if not wins:
            return 0.0

        avg = sum(r.amount_won for r in wins) / len(wins)
        return round(avg, 2)

    def get_player_stats(self, player_name: str) -> Dict[str, any]:
        """Get comprehensive stats for a player."""
        total_hands = self.get_total_hands(player_name=player_name)

        if total_hands == 0:
            return {
                "player_name": player_name,
                "total_hands": 0,
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "win_rate": 0.0,
                "total_winnings": 0.0,
                "avg_win_amount": 0.0
            }

        return {
            "player_name": player_name,
            "total_hands": total_hands,
            "wins": self.get_wins(player_name=player_name),
            "losses": self.get_losses(player_name=player_name),
            "ties": self.get_ties(player_name=player_name),
            "win_rate": self.get_win_rate(player_name=player_name),
            "total_winnings": self.get_total_winnings(player_name=player_name),
            "avg_win_amount": self.get_avg_win_amount(player_name=player_name)
        }

    def get_position_stats(self) -> Dict[str, Dict[str, any]]:
        """Get win rates by position."""
        positions = set(r.position for r in self.hand_records if r.position)

        stats = {}
        for pos in positions:
            stats[pos] = {
                "total_hands": self.get_total_hands(position=pos),
                "win_rate": self.get_win_rate(position=pos),
                "total_winnings": self.get_total_winnings(position=pos)
            }

        return stats

    def get_hand_type_stats(self) -> Dict[str, Dict[str, any]]:
        """Get win rates by hand type."""
        hand_types = set(r.hand_type for r in self.hand_records if r.hand_type)

        stats = {}
        for hand_type in hand_types:
            stats[hand_type] = {
                "total_hands": self.get_total_hands(hand_type=hand_type),
                "win_rate": self.get_win_rate(hand_type=hand_type),
                "total_winnings": self.get_total_winnings(hand_type=hand_type)
            }

        return stats

    def get_all_players(self) -> List[str]:
        """Get list of all players."""
        return sorted(list(set(r.player_name for r in self.hand_records)))

    def get_recent_hands(
        self,
        limit: int = 10,
        player_name: Optional[str] = None
    ) -> List[HandRecord]:
        """Get recent hand records."""
        filtered = self.hand_records

        if player_name:
            filtered = [r for r in filtered if r.player_name == player_name]

        return filtered[-limit:]

    def get_statistics(self) -> Dict[str, any]:
        """Get overall statistics."""
        if not self.hand_records:
            return {
                "total_hands": 0,
                "total_players": 0,
                "overall_win_rate": 0.0,
                "total_winnings": 0.0,
                "most_successful_player": None
            }

        players = self.get_all_players()

        # Find most successful player by win rate
        best_player = None
        best_win_rate = 0.0
        for player in players:
            win_rate = self.get_win_rate(player_name=player)
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_player = player

        return {
            "total_hands": len(self.hand_records),
            "total_players": len(players),
            "overall_win_rate": self.get_win_rate(),
            "total_winnings": self.get_total_winnings(),
            "most_successful_player": best_player
        }

    def reset(self):
        """Reset calculator."""
        self.hand_records.clear()
        self.hand_count = 0

    def _filter_records(
        self,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        hand_type: Optional[str] = None
    ) -> List[HandRecord]:
        """Filter records by criteria."""
        filtered = self.hand_records

        if player_name:
            filtered = [r for r in filtered if r.player_name == player_name]

        if position:
            filtered = [r for r in filtered if r.position == position]

        if hand_type:
            filtered = [r for r in filtered if r.hand_type == hand_type]

        return filtered


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    calc = WinRateCalculator()

    # Record some hands
    calc.record_hand("Alice", HandResult.WIN, 100.0, position="BTN", hand_type="AA")
    calc.record_hand("Alice", HandResult.LOSS, -50.0, position="CO", hand_type="KK")
    calc.record_hand("Bob", HandResult.WIN, 75.0, position="BTN", hand_type="AK")

    # Get stats
    alice_stats = calc.get_player_stats("Alice")
    print(f"\nAlice's stats:")
    print(f"  Win rate: {alice_stats['win_rate']}%")
    print(f"  Total winnings: ${alice_stats['total_winnings']}")

    position_stats = calc.get_position_stats()
    print(f"\nButton win rate: {position_stats['BTN']['win_rate']}%")
