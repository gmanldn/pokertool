#!/usr/bin/env python3
"""
Stack Size Tracker
=================

Tracks player stack sizes over time.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class StackSnapshot:
    """Snapshot of player stacks at a point in time"""
    timestamp: datetime
    player_stacks: Dict[str, float]
    snapshot_id: int


class StackTracker:
    """Tracks player stack sizes over time."""

    def __init__(self):
        """Initialize stack tracker."""
        self.current_stacks: Dict[str, float] = {}
        self.snapshots: List[StackSnapshot] = []
        self.snapshot_count = 0

    def update_stack(self, player_name: str, stack_size: float) -> None:
        """Update player's stack size."""
        self.current_stacks[player_name] = stack_size

    def take_snapshot(self) -> StackSnapshot:
        """Take snapshot of current stacks."""
        self.snapshot_count += 1
        snapshot = StackSnapshot(
            timestamp=datetime.now(),
            player_stacks=self.current_stacks.copy(),
            snapshot_id=self.snapshot_count
        )
        self.snapshots.append(snapshot)
        return snapshot

    def get_stack(self, player_name: str) -> Optional[float]:
        """Get player's current stack."""
        return self.current_stacks.get(player_name)

    def get_stack_change(self, player_name: str) -> Optional[float]:
        """Get stack change since first snapshot."""
        if not self.snapshots or player_name not in self.current_stacks:
            return None

        first_stack = self.snapshots[0].player_stacks.get(player_name)
        if first_stack is None:
            return None

        return self.current_stacks[player_name] - first_stack

    def get_biggest_stack(self) -> Optional[tuple[str, float]]:
        """Get player with biggest stack."""
        if not self.current_stacks:
            return None
        player = max(self.current_stacks, key=self.current_stacks.get)
        return (player, self.current_stacks[player])

    def get_statistics(self) -> Dict[str, any]:
        """Get stack statistics."""
        if not self.current_stacks:
            return {
                "total_players": 0,
                "total_chips": 0.0,
                "avg_stack": 0.0,
                "snapshots_taken": len(self.snapshots)
            }

        total = sum(self.current_stacks.values())
        avg = total / len(self.current_stacks)

        return {
            "total_players": len(self.current_stacks),
            "total_chips": round(total, 2),
            "avg_stack": round(avg, 2),
            "snapshots_taken": len(self.snapshots)
        }

    def reset(self):
        """Reset tracker."""
        self.current_stacks.clear()
        self.snapshots.clear()
        self.snapshot_count = 0


if __name__ == '__main__':
    tracker = StackTracker()
    tracker.update_stack("Alice", 100.0)
    tracker.update_stack("Bob", 150.0)
    tracker.take_snapshot()

    print(f"Alice stack: ${tracker.get_stack('Alice')}")
    stats = tracker.get_statistics()
    print(f"Average stack: ${stats['avg_stack']}")
