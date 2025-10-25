#!/usr/bin/env python3
"""
Table Statistics
================

Tracks comprehensive table-level statistics and metrics.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TableSnapshot:
    """Snapshot of table state"""
    timestamp: datetime
    num_players: int
    avg_stack: float
    total_pot: float
    big_blind: float
    snapshot_id: int


class TableStatistics:
    """Tracks table-level statistics."""

    def __init__(self):
        """Initialize table statistics."""
        self.snapshots: List[TableSnapshot] = []
        self.hands_played = 0
        self.total_pots_won = 0.0
        self.snapshot_count = 0

    def record_snapshot(
        self,
        num_players: int,
        avg_stack: float,
        total_pot: float = 0.0,
        big_blind: float = 1.0
    ) -> TableSnapshot:
        """Record a table snapshot."""
        self.snapshot_count += 1
        snapshot = TableSnapshot(
            timestamp=datetime.now(),
            num_players=num_players,
            avg_stack=avg_stack,
            total_pot=total_pot,
            big_blind=big_blind,
            snapshot_id=self.snapshot_count
        )
        self.snapshots.append(snapshot)
        return snapshot

    def record_hand_complete(self, pot_size: float):
        """Record a completed hand."""
        self.hands_played += 1
        self.total_pots_won += pot_size

    def get_avg_players(self) -> float:
        """Get average number of players."""
        if not self.snapshots:
            return 0.0
        avg = sum(s.num_players for s in self.snapshots) / len(self.snapshots)
        return round(avg, 2)

    def get_avg_pot_size(self) -> float:
        """Get average pot size."""
        if self.hands_played == 0:
            return 0.0
        return round(self.total_pots_won / self.hands_played, 2)

    def get_avg_stack_size(self) -> float:
        """Get average stack size across all snapshots."""
        if not self.snapshots:
            return 0.0
        avg = sum(s.avg_stack for s in self.snapshots) / len(self.snapshots)
        return round(avg, 2)

    def get_hands_per_hour(self, hours: float = 1.0) -> float:
        """Estimate hands per hour."""
        if not self.snapshots or len(self.snapshots) < 2:
            return 0.0

        duration = (self.snapshots[-1].timestamp - self.snapshots[0].timestamp).total_seconds() / 3600
        if duration == 0:
            return 0.0

        rate = self.hands_played / duration
        return round(rate, 1)

    def get_statistics(self) -> Dict[str, any]:
        """Get comprehensive table statistics."""
        if not self.snapshots:
            return {
                "total_snapshots": 0,
                "hands_played": 0,
                "avg_players": 0.0,
                "avg_pot_size": 0.0,
                "avg_stack_size": 0.0,
                "hands_per_hour": 0.0,
                "total_pots": 0.0
            }

        return {
            "total_snapshots": len(self.snapshots),
            "hands_played": self.hands_played,
            "avg_players": self.get_avg_players(),
            "avg_pot_size": self.get_avg_pot_size(),
            "avg_stack_size": self.get_avg_stack_size(),
            "hands_per_hour": self.get_hands_per_hour(),
            "total_pots": round(self.total_pots_won, 2)
        }

    def reset(self):
        """Reset statistics."""
        self.snapshots.clear()
        self.hands_played = 0
        self.total_pots_won = 0.0
        self.snapshot_count = 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    stats = TableStatistics()

    stats.record_snapshot(6, 100.0, 15.0, 1.0)
    stats.record_hand_complete(15.0)
    stats.record_snapshot(6, 98.0, 20.0, 1.0)
    stats.record_hand_complete(20.0)

    table_stats = stats.get_statistics()
    print(f"\nTable Statistics:")
    print(f"  Hands played: {table_stats['hands_played']}")
    print(f"  Avg players: {table_stats['avg_players']}")
    print(f"  Avg pot: ${table_stats['avg_pot_size']}")
