#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Board Change Detector
====================

Detects and tracks community card changes (flop, turn, river)
for poker hand progression analysis.
"""

import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Street(str, Enum):
    """Poker street/betting round"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    UNKNOWN = "unknown"


class BoardChangeType(str, Enum):
    """Type of board change"""
    FLOP_DEAL = "flop_deal"      # 3 cards dealt
    TURN_DEAL = "turn_deal"      # 1 card dealt
    RIVER_DEAL = "river_deal"    # 1 card dealt
    BOARD_CLEAR = "board_clear"  # Board reset (new hand)
    UNKNOWN = "unknown"


@dataclass
class BoardState:
    """Represents the board state at a point in time"""
    timestamp: datetime
    cards: List[str]  # e.g., ["As", "Kd", "Qh", "Jc", "Ts"]
    street: Street
    frame_number: int
    confidence: float


@dataclass
class BoardChange:
    """Represents a detected board change"""
    timestamp: datetime
    previous_cards: List[str]
    new_cards: List[str]
    added_cards: List[str]
    change_type: BoardChangeType
    previous_street: Street
    new_street: Street
    frame_number: int
    confidence: float


class BoardChangeDetector:
    """
    Detects changes to the poker board (community cards).
    """

    def __init__(self):
        """Initialize board change detector."""
        self.current_board: List[str] = []
        self.previous_board: List[str] = []
        self.current_street = Street.PREFLOP
        self.change_history: List[BoardChange] = []
        self.state_history: List[BoardState] = []
        self.frame_count = 0

    def update_board(
        self,
        new_board: List[str],
        confidence: float = 1.0
    ) -> Optional[BoardChange]:
        """
        Update board state and detect changes.

        Args:
            new_board: List of card strings (e.g., ["As", "Kd", "Qh"])
            confidence: Detection confidence (0-1)

        Returns:
            BoardChange if change detected, None otherwise
        """
        self.frame_count += 1
        self.previous_board = self.current_board.copy()
        previous_street = self.current_street

        # Normalize board (sort for consistency, remove duplicates)
        new_board = self._normalize_board(new_board)

        # Detect change
        if new_board == self.current_board:
            return None  # No change

        # Calculate added cards
        added_cards = [card for card in new_board if card not in self.current_board]

        # Determine new street and change type
        new_street, change_type = self._classify_change(
            len(self.current_board),
            len(new_board),
            len(added_cards)
        )

        # Create change record
        board_change = BoardChange(
            timestamp=datetime.now(),
            previous_cards=self.current_board.copy(),
            new_cards=new_board.copy(),
            added_cards=added_cards,
            change_type=change_type,
            previous_street=previous_street,
            new_street=new_street,
            frame_number=self.frame_count,
            confidence=confidence
        )

        # Update state
        self.current_board = new_board
        self.current_street = new_street
        self.change_history.append(board_change)

        # Record state
        state = BoardState(
            timestamp=datetime.now(),
            cards=new_board.copy(),
            street=new_street,
            frame_number=self.frame_count,
            confidence=confidence
        )
        self.state_history.append(state)

        logger.info(
            f"Board change: {change_type.value} - {added_cards} "
            f"(confidence: {confidence:.2f})"
        )

        return board_change

    def _normalize_board(self, cards: List[str]) -> List[str]:
        """
        Normalize board representation.

        Args:
            cards: Raw card list

        Returns:
            Normalized card list (sorted, deduplicated)
        """
        # Remove duplicates while preserving order
        seen = set()
        normalized = []
        for card in cards:
            if card and card not in seen:
                normalized.append(card)
                seen.add(card)
        return normalized

    def _classify_change(
        self,
        previous_count: int,
        new_count: int,
        added_count: int
    ) -> Tuple[Street, BoardChangeType]:
        """
        Classify the type of board change.

        Args:
            previous_count: Number of cards before change
            new_count: Number of cards after change
            added_count: Number of cards added

        Returns:
            Tuple of (new_street, change_type)
        """
        # Board cleared (new hand)
        if new_count == 0 or (new_count < previous_count):
            return Street.PREFLOP, BoardChangeType.BOARD_CLEAR

        # Flop deal (0 → 3 cards)
        if previous_count == 0 and new_count == 3:
            return Street.FLOP, BoardChangeType.FLOP_DEAL

        # Turn deal (3 → 4 cards)
        if previous_count == 3 and new_count == 4:
            return Street.TURN, BoardChangeType.TURN_DEAL

        # River deal (4 → 5 cards)
        if previous_count == 4 and new_count == 5:
            return Street.RIVER, BoardChangeType.RIVER_DEAL

        # Unusual change patterns
        if new_count == 5:
            return Street.RIVER, BoardChangeType.UNKNOWN
        elif new_count == 4:
            return Street.TURN, BoardChangeType.UNKNOWN
        elif new_count == 3:
            return Street.FLOP, BoardChangeType.UNKNOWN

        return Street.UNKNOWN, BoardChangeType.UNKNOWN

    def get_current_board(self) -> List[str]:
        """Get current board cards."""
        return self.current_board.copy()

    def get_current_street(self) -> Street:
        """Get current street."""
        return self.current_street

    def get_recent_changes(self, count: int = 10) -> List[BoardChange]:
        """
        Get most recent board changes.

        Args:
            count: Number of recent changes to retrieve

        Returns:
            List of recent BoardChange objects
        """
        return self.change_history[-count:] if self.change_history else []

    def get_changes_by_type(self, change_type: BoardChangeType) -> List[BoardChange]:
        """
        Get all changes of a specific type.

        Args:
            change_type: Type of change to filter

        Returns:
            List of matching BoardChange objects
        """
        return [c for c in self.change_history if c.change_type == change_type]

    def get_hand_progression(self) -> List[BoardState]:
        """
        Get complete hand progression (all board states).

        Returns:
            List of BoardState objects in chronological order
        """
        return self.state_history.copy()

    def is_complete_board(self) -> bool:
        """Check if board is complete (river dealt)."""
        return len(self.current_board) == 5

    def get_statistics(self) -> Dict[str, any]:
        """
        Get board change statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.change_history:
            return {
                "total_changes": 0,
                "changes_by_type": {},
                "changes_by_street": {},
                "avg_confidence": 0.0,
                "hands_tracked": 0
            }

        changes_by_type = {}
        for change_type in BoardChangeType:
            changes = self.get_changes_by_type(change_type)
            if changes:
                changes_by_type[change_type.value] = len(changes)

        changes_by_street = {}
        for change in self.change_history:
            street = change.new_street.value
            changes_by_street[street] = changes_by_street.get(street, 0) + 1

        avg_confidence = sum(c.confidence for c in self.change_history) / len(self.change_history)

        # Count hands (board clears)
        hands_tracked = len(self.get_changes_by_type(BoardChangeType.BOARD_CLEAR))

        return {
            "total_changes": len(self.change_history),
            "changes_by_type": changes_by_type,
            "changes_by_street": changes_by_street,
            "avg_confidence": round(avg_confidence, 3),
            "hands_tracked": hands_tracked,
            "current_street": self.current_street.value,
            "current_board_size": len(self.current_board)
        }

    def reset(self):
        """Reset detector for new session."""
        self.current_board = []
        self.previous_board = []
        self.current_street = Street.PREFLOP
        self.change_history.clear()
        self.state_history.clear()
        self.frame_count = 0


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    detector = BoardChangeDetector()

    print("Board Change Detector - Example\n")

    # Simulate hand progression
    detector.update_board([])  # Preflop (no board)
    detector.update_board(["As", "Kd", "Qh"], confidence=0.95)  # Flop
    detector.update_board(["As", "Kd", "Qh", "Jc"], confidence=0.92)  # Turn
    detector.update_board(["As", "Kd", "Qh", "Jc", "Ts"], confidence=0.90)  # River
    detector.update_board([])  # New hand

    # Second hand
    detector.update_board(["2c", "3c", "4c"], confidence=0.93)  # Flop
    detector.update_board(["2c", "3c", "4c", "5c"], confidence=0.91)  # Turn

    stats = detector.get_statistics()
    print("\nStatistics:")
    print(f"  Total changes: {stats['total_changes']}")
    print(f"  Hands tracked: {stats['hands_tracked']}")
    print(f"  Current street: {stats['current_street']}")
    print(f"  Average confidence: {stats['avg_confidence']}")
    print(f"\nChanges by type:")
    for change_type, count in stats['changes_by_type'].items():
        print(f"  {change_type}: {count}")
