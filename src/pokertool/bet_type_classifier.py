#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bet Type Classifier
==================

Classifies poker bet types based on context, position, and action history.
"""

import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BetType(str, Enum):
    """Types of poker bets"""
    VALUE_BET = "value_bet"              # Betting for value with strong hand
    BLUFF = "bluff"                       # Betting with weak hand to fold better
    SEMI_BLUFF = "semi_bluff"            # Betting with drawing hand
    CONTINUATION_BET = "continuation_bet" # C-bet after raising preflop
    PROBE_BET = "probe_bet"              # Betting to gain information
    BLOCKING_BET = "blocking_bet"        # Small bet to control pot size
    SQUEEZE = "squeeze"                   # Re-raise against multiple opponents
    CHECK_RAISE = "check_raise"          # Check then raise
    DONK_BET = "donk_bet"                # Bet out of position into aggressor
    UNKNOWN = "unknown"


@dataclass
class BetClassification:
    """Represents a classified bet"""
    timestamp: datetime
    bet_type: BetType
    bet_amount: float
    pot_size: float
    bet_to_pot_ratio: float
    street: str
    position: str
    confidence: float
    frame_number: int


class BetTypeClassifier:
    """
    Classifies poker bet types based on context and action history.
    """

    def __init__(self):
        """Initialize bet type classifier."""
        self.classification_history: List[BetClassification] = []
        self.frame_count = 0

        # Classification thresholds
        self.value_bet_min_strength = 0.7
        self.bluff_max_strength = 0.3
        self.small_bet_threshold = 0.33  # < 1/3 pot
        self.large_bet_threshold = 0.75  # > 3/4 pot

    def classify_bet(
        self,
        bet_amount: float,
        pot_size: float,
        street: str = "flop",
        position: str = "unknown",
        hand_strength: Optional[float] = None,
        was_preflop_aggressor: bool = False,
        facing_bet: bool = False,
        was_checked_to: bool = False,
        num_opponents: int = 1,
        has_draw: bool = False,
        confidence: float = 1.0
    ) -> BetClassification:
        """
        Classify a bet type.

        Args:
            bet_amount: Size of the bet
            pot_size: Current pot size
            street: Current betting round
            position: Player's position
            hand_strength: Estimated hand strength (0-1)
            was_preflop_aggressor: Whether player raised preflop
            facing_bet: Whether facing a bet (re-raise scenario)
            was_checked_to: Whether action was checked to player
            num_opponents: Number of opponents in the hand
            has_draw: Whether player has a drawing hand
            confidence: Classification confidence (0-1)

        Returns:
            BetClassification object
        """
        self.frame_count += 1

        # Calculate bet-to-pot ratio
        bet_ratio = bet_amount / pot_size if pot_size > 0 else 0

        # Classify the bet
        bet_type = self._classify_bet_type(
            bet_amount=bet_amount,
            bet_ratio=bet_ratio,
            street=street,
            position=position,
            hand_strength=hand_strength,
            was_preflop_aggressor=was_preflop_aggressor,
            facing_bet=facing_bet,
            was_checked_to=was_checked_to,
            num_opponents=num_opponents,
            has_draw=has_draw
        )

        # Create classification record
        classification = BetClassification(
            timestamp=datetime.now(),
            bet_type=bet_type,
            bet_amount=bet_amount,
            pot_size=pot_size,
            bet_to_pot_ratio=bet_ratio,
            street=street,
            position=position,
            confidence=confidence,
            frame_number=self.frame_count
        )

        self.classification_history.append(classification)

        logger.info(
            f"Classified bet: {bet_type.value} - ${bet_amount:.2f} "
            f"({bet_ratio:.1%} pot) on {street}"
        )

        return classification

    def _classify_bet_type(
        self,
        bet_amount: float,
        bet_ratio: float,
        street: str,
        position: str,
        hand_strength: Optional[float],
        was_preflop_aggressor: bool,
        facing_bet: bool,
        was_checked_to: bool,
        num_opponents: int,
        has_draw: bool
    ) -> BetType:
        """
        Internal method to classify bet type.

        Returns:
            BetType enum value
        """
        # Continuation bet (raised preflop and betting flop)
        if was_preflop_aggressor and street in ["flop", "turn"] and not facing_bet:
            return BetType.CONTINUATION_BET

        # Check-raise (was checked to and then raising)
        if was_checked_to and facing_bet:
            return BetType.CHECK_RAISE

        # Squeeze (re-raising against multiple opponents)
        if facing_bet and num_opponents >= 2:
            return BetType.SQUEEZE

        # Donk bet (betting out of position into the aggressor)
        if not was_preflop_aggressor and position in ["BB", "SB"] and street == "flop":
            return BetType.DONK_BET

        # Blocking bet (small bet to control pot)
        if bet_ratio < self.small_bet_threshold:
            return BetType.BLOCKING_BET

        # Probe bet (betting after checked around)
        if was_checked_to and not facing_bet and street in ["turn", "river"]:
            return BetType.PROBE_BET

        # Hand strength-based classification
        if hand_strength is not None:
            # Value bet (strong hand, large bet)
            if hand_strength >= self.value_bet_min_strength:
                return BetType.VALUE_BET

            # Semi-bluff (drawing hand)
            if has_draw and 0.3 < hand_strength < 0.7:
                return BetType.SEMI_BLUFF

            # Bluff (weak hand)
            if hand_strength <= self.bluff_max_strength:
                return BetType.BLUFF

        return BetType.UNKNOWN

    def get_classifications_by_type(self, bet_type: BetType) -> List[BetClassification]:
        """
        Get all classifications of a specific type.

        Args:
            bet_type: Type to filter

        Returns:
            List of matching classifications
        """
        return [c for c in self.classification_history if c.bet_type == bet_type]

    def get_recent_classifications(self, count: int = 10) -> List[BetClassification]:
        """
        Get most recent classifications.

        Args:
            count: Number to retrieve

        Returns:
            List of recent classifications
        """
        return self.classification_history[-count:] if self.classification_history else []

    def get_statistics(self) -> Dict[str, any]:
        """
        Get classification statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.classification_history:
            return {
                "total_classifications": 0,
                "classifications_by_type": {},
                "avg_bet_to_pot_ratio": 0.0,
                "avg_confidence": 0.0
            }

        # Count by type
        by_type = {}
        for bet_type in BetType:
            classifications = self.get_classifications_by_type(bet_type)
            if classifications:
                by_type[bet_type.value] = len(classifications)

        # Calculate averages
        total_ratio = sum(c.bet_to_pot_ratio for c in self.classification_history)
        avg_ratio = total_ratio / len(self.classification_history)

        total_confidence = sum(c.confidence for c in self.classification_history)
        avg_confidence = total_confidence / len(self.classification_history)

        return {
            "total_classifications": len(self.classification_history),
            "classifications_by_type": by_type,
            "avg_bet_to_pot_ratio": round(avg_ratio, 3),
            "avg_confidence": round(avg_confidence, 3)
        }

    def reset(self):
        """Reset classifier for new session."""
        self.classification_history.clear()
        self.frame_count = 0


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)

    classifier = BetTypeClassifier()

    print("Bet Type Classifier - Example\n")

    # C-bet example
    classifier.classify_bet(
        bet_amount=10.0,
        pot_size=15.0,
        street="flop",
        position="BTN",
        was_preflop_aggressor=True,
        confidence=0.90
    )

    # Value bet example
    classifier.classify_bet(
        bet_amount=30.0,
        pot_size=40.0,
        street="river",
        hand_strength=0.9,
        confidence=0.95
    )

    # Bluff example
    classifier.classify_bet(
        bet_amount=20.0,
        pot_size=25.0,
        street="turn",
        hand_strength=0.2,
        confidence=0.85
    )

    stats = classifier.get_statistics()
    print("\nStatistics:")
    print(f"  Total classifications: {stats['total_classifications']}")
    print(f"  Average bet/pot ratio: {stats['avg_bet_to_pot_ratio']:.1%}")
    print(f"\nClassifications by type:")
    for bet_type, count in stats['classifications_by_type'].items():
        print(f"  {bet_type}: {count}")
