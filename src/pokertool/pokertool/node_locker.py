"""
Node locking utilities for Game Theory Optimal (GTO) deviation workflows.

Provides helpers for clamping action frequencies when solving with
node-locking constraints. Designed to be used by the GTO deviation
engine to enforce exploitative or equilibrium-preserving adjustments.

ID: GTO-DEV-001
Status: INTEGRATED
Priority: MEDIUM
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Iterable, Optional, Tuple


@dataclass(frozen=True)
class NodeLock:
    """Represents a single node locking constraint for an action."""
    node_id: str
    action: str
    min_frequency: float
    max_frequency: float

    def clamp(self, frequency: float) -> float:
        """Clamp frequency to the lock bounds."""
        return max(self.min_frequency, min(self.max_frequency, frequency))

    def to_dict(self) -> Dict[str, float]:
        """Export lock definition."""
        return {
            "node_id": self.node_id,
            "action": self.action,
            "min_frequency": self.min_frequency,
            "max_frequency": self.max_frequency,
        }


class NodeLocker:
    """
    Manages node locking constraints and applies them to action strategies.

    The locker stores per-node constraints allowing the deviation engine to
    restrict solver outputs (e.g. fix frequencies, enforce bluffs/value ratios,
    or mimic population tendencies).
    """

    def __init__(self) -> None:
        self._locks: Dict[str, Dict[str, NodeLock]] = {}

    # --------------------------------------------------------------------- #
    # CRUD operations on locks
    # --------------------------------------------------------------------- #

    def lock_action(
        self,
        node_id: str,
        action: str,
        min_frequency: float,
        max_frequency: float,
    ) -> None:
        """
        Register or update a lock for a specific node/action pair.

        Args:
            node_id: Identifier for the decision node (string-based for flexibility).
            action: Action label (e.g. 'raise', 'call', 'fold').
            min_frequency: Lower bound for the action frequency (0.0-1.0).
            max_frequency: Upper bound for the action frequency (0.0-1.0).

        Raises:
            ValueError: If min/max bounds are invalid.
        """
        if not (0.0 <= min_frequency <= 1.0):
            raise ValueError("min_frequency must be within [0.0, 1.0]")
        if not (0.0 <= max_frequency <= 1.0):
            raise ValueError("max_frequency must be within [0.0, 1.0]")
        if min_frequency > max_frequency:
            raise ValueError("min_frequency cannot exceed max_frequency")

        self._locks.setdefault(node_id, {})[action] = NodeLock(
            node_id=node_id,
            action=action,
            min_frequency=min_frequency,
            max_frequency=max_frequency,
        )

    def unlock_action(self, node_id: str, action: Optional[str] = None) -> None:
        """
        Remove locks for a node.

        Args:
            node_id: Identifier for the decision node.
            action: Specific action to unlock. If omitted, removes all locks for the node.
        """
        if node_id not in self._locks:
            return

        if action is None:
            del self._locks[node_id]
            return

        self._locks[node_id].pop(action, None)
        if not self._locks[node_id]:
            del self._locks[node_id]

    def get_locks(self, node_id: Optional[str] = None) -> Dict[str, List[NodeLock]]:
        """
        Retrieve registered locks.

        Args:
            node_id: Optional node filter.

        Returns:
            Mapping of node_id to list of NodeLock instances.
        """
        if node_id is not None:
            locks = list(self._locks.get(node_id, {}).values())
            return {node_id: locks} if locks else {}
        return {
            nid: list(action_map.values())
            for nid, action_map in self._locks.items()
        }

    # --------------------------------------------------------------------- #
    # Application of locks
    # --------------------------------------------------------------------- #

    def apply(
        self,
        node_id: str,
        strategy: Dict[str, float],
        tolerance: float = 1e-6,
    ) -> Tuple[Dict[str, float], Dict[str, NodeLock]]:
        """
        Clamp a strategy to honour registered node locks.

        Args:
            node_id: Identifier for the decision node being adjusted.
            strategy: Mapping action -> frequency (expected to sum to ~1.0).
            tolerance: Allowed numeric slack when normalising.

        Returns:
            Tuple of (adjusted_strategy, applied_locks)
        """
        if node_id not in self._locks:
            return self._normalise(strategy, tolerance=tolerance), {}

        locks = self._locks[node_id]
        locked_actions = set(locks.keys())

        # Clamp locked actions first
        adjusted: Dict[str, float] = {}
        locked_total = 0.0
        for action, freq in strategy.items():
            if action in locks:
                clamped = locks[action].clamp(freq)
                adjusted[action] = clamped
                locked_total += clamped
            else:
                adjusted[action] = freq

        locked_total = min(locked_total, 1.0)

        # Adjust remaining actions to fill residual probability mass
        residual = max(0.0, 1.0 - locked_total)
        free_actions = [a for a in strategy if a not in locked_actions]
        free_total = sum(strategy[a] for a in free_actions)

        if not free_actions:
            # All actions locked; renormalise locked mass if necessary
            if locked_total <= 0.0:
                equal_freq = 1.0 / max(len(strategy), 1)
                adjusted = {action: equal_freq for action in strategy}
            else:
                scale = 1.0 / locked_total
                adjusted = {action: freq * scale for action, freq in adjusted.items()}
        else:
            if free_total <= 0.0:
                equal_share = residual / len(free_actions) if residual > 0.0 else 0.0
                for action in free_actions:
                    adjusted[action] = equal_share
            else:
                scale = residual / free_total if free_total > 0 else 0.0
                for action in free_actions:
                    adjusted[action] = max(0.0, adjusted[action] * scale)

        return self._normalise(adjusted, tolerance=tolerance), locks

    # --------------------------------------------------------------------- #
    # Utilities
    # --------------------------------------------------------------------- #

    @staticmethod
    def _normalise(strategy: Dict[str, float], tolerance: float = 1e-6) -> Dict[str, float]:
        """Normalise a strategy to ensure probabilities sum to one (within tolerance)."""
        total = sum(strategy.values())
        if total <= tolerance:
            equal = 1.0 / max(len(strategy), 1)
            return {action: equal for action in strategy}

        return {action: max(0.0, freq / total) for action, freq in strategy.items()}

    def export(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Export all node locks to a serialisable structure."""
        return {
            node_id: {action: lock.to_dict() for action, lock in action_map.items()}
            for node_id, action_map in self._locks.items()
        }

    def clear(self) -> None:
        """Remove all registered locks."""
        self._locks.clear()
