#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Player Action Detector
======================

Detects and classifies player actions (fold, check, bet, call, raise, all-in)
from screen capture or game state changes.
"""

import logging
from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PlayerAction(str, Enum):
    """Types of player actions"""
    FOLD = "fold"
    CHECK = "check"
    BET = "bet"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"
    POST_SB = "post_sb"
    POST_BB = "post_bb"
    UNKNOWN = "unknown"


@dataclass
class DetectedAction:
    """Represents a detected player action"""
    timestamp: datetime
    player_position: str
    action: PlayerAction
    amount: Optional[float]
    stack_before: Optional[float]
    stack_after: Optional[float]
    pot_before: float
    pot_after: float
    confidence: float
    frame_number: int


class PlayerActionDetector:
    """Detects player actions from game state changes"""

    def __init__(self, min_bet_amount: float = 0.01):
        """
        Initialize action detector.

        Args:
            min_bet_amount: Minimum bet amount to consider significant
        """
        self.min_bet_amount = min_bet_amount
        self.action_history: List[DetectedAction] = []
        self.frame_count = 0

    def detect_action(
        self,
        player_position: str,
        stack_before: Optional[float],
        stack_after: Optional[float],
        pot_before: float,
        pot_after: float,
        facing_bet: bool = False,
        confidence: float = 1.0
    ) -> Optional[DetectedAction]:
        """
        Detect player action from state changes.

        Args:
            player_position: Player's table position
            stack_before: Stack size before action
            stack_after: Stack size after action  
            pot_before: Pot size before action
            pot_after: Pot size after action
            facing_bet: Whether player is facing a bet
            confidence: Detection confidence (0-1)

        Returns:
            DetectedAction if action detected, None otherwise
        """
        self.frame_count += 1

        # Calculate stack and pot changes
        stack_change = 0.0 if stack_before is None or stack_after is None else stack_before - stack_after
        pot_change = pot_after - pot_before

        # Classify action
        action = self._classify_action(
            stack_change=stack_change,
            pot_change=pot_change,
            stack_before=stack_before,
            stack_after=stack_after,
            pot_before=pot_before,
            pot_after=pot_after,
            facing_bet=facing_bet
        )

        # Determine action amount
        amount = stack_change if stack_change > 0 else None

        detected_action = DetectedAction(
            timestamp=datetime.now(),
            player_position=player_position,
            action=action,
            amount=amount,
            stack_before=stack_before,
            stack_after=stack_after,
            pot_before=pot_before,
            pot_after=pot_after,
            confidence=confidence,
            frame_number=self.frame_count
        )

        self.action_history.append(detected_action)

        logger.info(
            f"{player_position} action: {action.value}"
            f"{f' ${amount:.2f}' if amount else ''} "
            f"(confidence: {confidence:.2f})"
        )

        return detected_action

    def _classify_action(
        self,
        stack_change: float,
        pot_change: float,
        stack_before: Optional[float],
        stack_after: Optional[float],
        pot_before: float,
        pot_after: float,
        facing_bet: bool
    ) -> PlayerAction:
        """
        Classify the player's action.

        Args:
            stack_change: Change in player's stack
            pot_change: Change in pot size
            stack_before: Stack before action
            stack_after: Stack after action
            pot_before: Pot size before action
            pot_after: Pot size after action
            facing_bet: Whether facing a bet

        Returns:
            PlayerAction classification
        """
        # No stack or pot change - check or fold
        if abs(stack_change) < self.min_bet_amount and abs(pot_change) < self.min_bet_amount:
            # Preflop with just blinds posted (typical 1.5 for 0.5/1.0 blinds)
            # If not facing_bet but pot has typical blind amount, infer it's a fold
            if 1.0 <= pot_before <= 2.5 and 3 <= self.frame_count <= 10 and not facing_bet:
                return PlayerAction.FOLD
            return PlayerAction.CHECK if not facing_bet else PlayerAction.FOLD

        # Stack decreased (player put money in)
        if stack_change > self.min_bet_amount:
            # All-in detection
            if stack_after is not None and stack_after < self.min_bet_amount:
                return PlayerAction.ALL_IN

            # Posting blinds (small specific amounts early in hand)
            if stack_change < 5.0 and self.frame_count <= 2:
                # First player to post is SB (pot should be empty or nearly empty)
                if self.frame_count == 1 or pot_before < self.min_bet_amount:
                    return PlayerAction.POST_SB
                # Second player to post is BB (pot has SB in it)
                elif self.frame_count == 2 or pot_before >= 0.25:
                    return PlayerAction.POST_BB

            # Distinguish bet/call/raise
            if not facing_bet:
                return PlayerAction.BET
            else:
                # If player puts in more than current pot size, it's a raise
                if stack_change > pot_before:
                    return PlayerAction.RAISE
                else:
                    return PlayerAction.CALL

        # Stack didn't change meaningfully - likely check or fold
        if facing_bet:
            return PlayerAction.FOLD
        else:
            return PlayerAction.CHECK

        return PlayerAction.UNKNOWN

    def get_player_actions(self, player_position: str) -> List[DetectedAction]:
        """Get all actions for a specific player."""
        return [a for a in self.action_history if a.player_position == player_position]

    def get_actions_by_type(self, action_type: PlayerAction) -> List[DetectedAction]:
        """Get all actions of a specific type."""
        return [a for a in self.action_history if a.action == action_type]

    def get_recent_actions(self, count: int = 10) -> List[DetectedAction]:
        """Get most recent actions."""
        return self.action_history[-count:] if self.action_history else []

    def get_statistics(self) -> Dict[str, any]:
        """Get action detection statistics."""
        if not self.action_history:
            return {
                "total_actions": 0,
                "actions_by_type": {},
                "actions_by_position": {},
                "avg_confidence": 0.0
            }

        actions_by_type = {}
        for action_type in PlayerAction:
            actions = self.get_actions_by_type(action_type)
            if actions:
                actions_by_type[action_type.value] = len(actions)

        actions_by_position = {}
        for action in self.action_history:
            pos = action.player_position
            actions_by_position[pos] = actions_by_position.get(pos, 0) + 1

        avg_confidence = sum(a.confidence for a in self.action_history) / len(self.action_history)

        return {
            "total_actions": len(self.action_history),
            "actions_by_type": actions_by_type,
            "actions_by_position": actions_by_position,
            "avg_confidence": round(avg_confidence, 3)
        }

    def reset(self):
        """Reset detector for new hand."""
        self.action_history.clear()
        self.frame_count = 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    detector = PlayerActionDetector()

    print("Player Action Detector - Example\n")

    # Simulate hand actions
    detector.detect_action("SB", 100.0, 99.5, 0.0, 0.5)  # SB posts
    detector.detect_action("BB", 100.0, 99.0, 0.5, 1.5)  # BB posts
    detector.detect_action("UTG", 100.0, 100.0, 1.5, 1.5, facing_bet=False)  # UTG folds
    detector.detect_action("BTN", 100.0, 94.0, 1.5, 7.5, facing_bet=False)  # BTN raises to 6
    detector.detect_action("SB", 99.5, 93.5, 7.5, 13.5, facing_bet=True)  # SB calls
    detector.detect_action("BB", 99.0, 99.0, 13.5, 13.5, facing_bet=True)  # BB folds

    stats = detector.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total actions: {stats['total_actions']}")
    print(f"  Average confidence: {stats['avg_confidence']}")
    print(f"\nActions by type:")
    for action_type, count in stats['actions_by_type'].items():
        print(f"  {action_type}: {count}")
