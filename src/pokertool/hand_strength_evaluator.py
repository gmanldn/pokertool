#!/usr/bin/env python3
"""
Hand Strength Evaluator
======================

Evaluates poker hand strength and provides rankings.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


class HandRank(Enum):
    """Poker hand rankings"""
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


class Suit(Enum):
    """Card suits"""
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"
    SPADES = "s"


@dataclass
class Card:
    """Poker card"""
    rank: str  # '2'-'9', 'T', 'J', 'Q', 'K', 'A'
    suit: Suit

    def __str__(self):
        return f"{self.rank}{self.suit.value}"

    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create card from string like 'Ah' or 'Kd'"""
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")

        rank = card_str[0].upper()
        suit_char = card_str[1].lower()

        suit_map = {'h': Suit.HEARTS, 'd': Suit.DIAMONDS,
                    'c': Suit.CLUBS, 's': Suit.SPADES}

        if suit_char not in suit_map:
            raise ValueError(f"Invalid suit: {suit_char}")

        return cls(rank=rank, suit=suit_map[suit_char])


@dataclass
class HandEvaluation:
    """Result of hand evaluation"""
    hand_rank: HandRank
    rank_description: str
    high_cards: List[str]
    strength_score: int


class HandStrengthEvaluator:
    """Evaluates poker hand strength."""

    # Rank values for comparison
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
        'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    def __init__(self):
        """Initialize evaluator."""
        self.evaluations_count = 0

    def parse_cards(self, card_strings: List[str]) -> List[Card]:
        """
        Parse card strings to Card objects.

        Args:
            card_strings: List of card strings like ['Ah', 'Kd']

        Returns:
            List of Card objects
        """
        cards = []
        for card_str in card_strings:
            try:
                cards.append(Card.from_string(card_str))
            except ValueError as e:
                logger.error(f"Error parsing card: {e}")
                continue
        return cards

    def evaluate_hand(
        self,
        hole_cards: List[str],
        board_cards: Optional[List[str]] = None
    ) -> HandEvaluation:
        """
        Evaluate poker hand strength.

        Args:
            hole_cards: Player's hole cards
            board_cards: Community cards (optional)

        Returns:
            HandEvaluation object
        """
        self.evaluations_count += 1

        # Parse cards
        hole = self.parse_cards(hole_cards)
        board = self.parse_cards(board_cards or [])
        all_cards = hole + board

        if len(all_cards) < 2:
            return HandEvaluation(
                hand_rank=HandRank.HIGH_CARD,
                rank_description="Invalid hand",
                high_cards=[],
                strength_score=0
            )

        # Evaluate best 5-card hand
        return self._evaluate_best_hand(all_cards)

    def _evaluate_best_hand(self, cards: List[Card]) -> HandEvaluation:
        """Evaluate best 5-card hand from available cards."""
        if len(cards) < 5:
            # Pre-flop or incomplete hand
            return self._evaluate_partial_hand(cards)

        # Check for each hand type (highest to lowest)
        if eval_result := self._check_royal_flush(cards):
            return eval_result
        if eval_result := self._check_straight_flush(cards):
            return eval_result
        if eval_result := self._check_four_of_kind(cards):
            return eval_result
        if eval_result := self._check_full_house(cards):
            return eval_result
        if eval_result := self._check_flush(cards):
            return eval_result
        if eval_result := self._check_straight(cards):
            return eval_result
        if eval_result := self._check_three_of_kind(cards):
            return eval_result
        if eval_result := self._check_two_pair(cards):
            return eval_result
        if eval_result := self._check_pair(cards):
            return eval_result

        return self._check_high_card(cards)

    def _evaluate_partial_hand(self, cards: List[Card]) -> HandEvaluation:
        """Evaluate hand with less than 5 cards."""
        ranks = [c.rank for c in cards]
        rank_counts = Counter(ranks)

        # Check for pair
        pairs = [r for r, count in rank_counts.items() if count == 2]
        if pairs:
            pair_rank = max(pairs, key=lambda r: self.RANK_VALUES[r])
            # Include kickers if available
            kickers = sorted([r for r in ranks if r != pair_rank],
                           key=lambda r: self.RANK_VALUES[r], reverse=True)
            high_cards = [pair_rank] + kickers
            return HandEvaluation(
                hand_rank=HandRank.PAIR,
                rank_description=f"Pair of {pair_rank}s",
                high_cards=high_cards,
                strength_score=self._calculate_score(HandRank.PAIR, high_cards)
            )

        # High card
        sorted_ranks = sorted(ranks, key=lambda r: self.RANK_VALUES[r], reverse=True)
        return HandEvaluation(
            hand_rank=HandRank.HIGH_CARD,
            rank_description=f"{sorted_ranks[0]}-high",
            high_cards=sorted_ranks,
            strength_score=self._calculate_score(HandRank.HIGH_CARD, sorted_ranks)
        )

    def _check_royal_flush(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for royal flush."""
        for suit in Suit:
            suited_cards = [c for c in cards if c.suit == suit]
            if len(suited_cards) < 5:
                continue

            ranks = set(c.rank for c in suited_cards)
            if {'A', 'K', 'Q', 'J', 'T'}.issubset(ranks):
                return HandEvaluation(
                    hand_rank=HandRank.ROYAL_FLUSH,
                    rank_description="Royal Flush",
                    high_cards=['A'],
                    strength_score=self._calculate_score(HandRank.ROYAL_FLUSH, ['A'])
                )
        return None

    def _check_straight_flush(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for straight flush."""
        for suit in Suit:
            suited_cards = [c for c in cards if c.suit == suit]
            if len(suited_cards) < 5:
                continue

            straight = self._find_straight([c.rank for c in suited_cards])
            if straight:
                return HandEvaluation(
                    hand_rank=HandRank.STRAIGHT_FLUSH,
                    rank_description=f"{straight[0]}-high Straight Flush",
                    high_cards=straight,
                    strength_score=self._calculate_score(HandRank.STRAIGHT_FLUSH, straight)
                )
        return None

    def _check_four_of_kind(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for four of a kind."""
        ranks = [c.rank for c in cards]
        rank_counts = Counter(ranks)

        quads = [r for r, count in rank_counts.items() if count == 4]
        if quads:
            quad_rank = quads[0]
            return HandEvaluation(
                hand_rank=HandRank.FOUR_OF_KIND,
                rank_description=f"Four {quad_rank}s",
                high_cards=[quad_rank],
                strength_score=self._calculate_score(HandRank.FOUR_OF_KIND, [quad_rank])
            )
        return None

    def _check_full_house(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for full house."""
        ranks = [c.rank for c in cards]
        rank_counts = Counter(ranks)

        trips = [r for r, count in rank_counts.items() if count == 3]
        pairs = [r for r, count in rank_counts.items() if count == 2]

        if trips and (pairs or len(trips) >= 2):
            trip_rank = max(trips, key=lambda r: self.RANK_VALUES[r])
            pair_rank = max([r for r in pairs + trips if r != trip_rank],
                          key=lambda r: self.RANK_VALUES[r]) if (pairs + trips) else trip_rank

            return HandEvaluation(
                hand_rank=HandRank.FULL_HOUSE,
                rank_description=f"{trip_rank}s full of {pair_rank}s",
                high_cards=[trip_rank, pair_rank],
                strength_score=self._calculate_score(HandRank.FULL_HOUSE, [trip_rank, pair_rank])
            )
        return None

    def _check_flush(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for flush."""
        for suit in Suit:
            suited_cards = [c for c in cards if c.suit == suit]
            if len(suited_cards) >= 5:
                ranks = sorted([c.rank for c in suited_cards],
                             key=lambda r: self.RANK_VALUES[r], reverse=True)[:5]
                return HandEvaluation(
                    hand_rank=HandRank.FLUSH,
                    rank_description=f"{ranks[0]}-high Flush",
                    high_cards=ranks,
                    strength_score=self._calculate_score(HandRank.FLUSH, ranks)
                )
        return None

    def _check_straight(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for straight."""
        ranks = [c.rank for c in cards]
        straight = self._find_straight(ranks)
        if straight:
            return HandEvaluation(
                hand_rank=HandRank.STRAIGHT,
                rank_description=f"{straight[0]}-high Straight",
                high_cards=straight,
                strength_score=self._calculate_score(HandRank.STRAIGHT, straight)
            )
        return None

    def _check_three_of_kind(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for three of a kind."""
        ranks = [c.rank for c in cards]
        rank_counts = Counter(ranks)

        trips = [r for r, count in rank_counts.items() if count == 3]
        if trips:
            trip_rank = max(trips, key=lambda r: self.RANK_VALUES[r])
            # Include kickers
            kickers = sorted([r for r in ranks if r != trip_rank],
                           key=lambda r: self.RANK_VALUES[r], reverse=True)[:2]
            high_cards = [trip_rank] + kickers
            return HandEvaluation(
                hand_rank=HandRank.THREE_OF_KIND,
                rank_description=f"Three {trip_rank}s",
                high_cards=high_cards,
                strength_score=self._calculate_score(HandRank.THREE_OF_KIND, high_cards)
            )
        return None

    def _check_two_pair(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for two pair."""
        ranks = [c.rank for c in cards]
        rank_counts = Counter(ranks)

        pairs = [r for r, count in rank_counts.items() if count == 2]
        if len(pairs) >= 2:
            sorted_pairs = sorted(pairs, key=lambda r: self.RANK_VALUES[r], reverse=True)[:2]
            # Include kicker
            kicker = sorted([r for r in ranks if r not in sorted_pairs],
                          key=lambda r: self.RANK_VALUES[r], reverse=True)[:1]
            high_cards = sorted_pairs + kicker
            return HandEvaluation(
                hand_rank=HandRank.TWO_PAIR,
                rank_description=f"{sorted_pairs[0]}s and {sorted_pairs[1]}s",
                high_cards=high_cards,
                strength_score=self._calculate_score(HandRank.TWO_PAIR, high_cards)
            )
        return None

    def _check_pair(self, cards: List[Card]) -> Optional[HandEvaluation]:
        """Check for pair."""
        ranks = [c.rank for c in cards]
        rank_counts = Counter(ranks)

        pairs = [r for r, count in rank_counts.items() if count == 2]
        if pairs:
            pair_rank = max(pairs, key=lambda r: self.RANK_VALUES[r])
            # Include kickers
            kickers = sorted([r for r in ranks if r != pair_rank],
                           key=lambda r: self.RANK_VALUES[r], reverse=True)[:3]
            high_cards = [pair_rank] + kickers
            return HandEvaluation(
                hand_rank=HandRank.PAIR,
                rank_description=f"Pair of {pair_rank}s",
                high_cards=high_cards,
                strength_score=self._calculate_score(HandRank.PAIR, high_cards)
            )
        return None

    def _check_high_card(self, cards: List[Card]) -> HandEvaluation:
        """Get high card."""
        ranks = sorted([c.rank for c in cards],
                      key=lambda r: self.RANK_VALUES[r], reverse=True)[:5]
        return HandEvaluation(
            hand_rank=HandRank.HIGH_CARD,
            rank_description=f"{ranks[0]}-high",
            high_cards=ranks,
            strength_score=self._calculate_score(HandRank.HIGH_CARD, ranks)
        )

    def _find_straight(self, ranks: List[str]) -> Optional[List[str]]:
        """Find straight in ranks."""
        unique_ranks = list(set(ranks))
        values = sorted([self.RANK_VALUES[r] for r in unique_ranks], reverse=True)

        # Check for wheel (A-2-3-4-5)
        if set([14, 2, 3, 4, 5]).issubset(set(values)):
            return ['5', '4', '3', '2', 'A']

        # Check for regular straight
        for i in range(len(values) - 4):
            if values[i] - values[i+4] == 4:
                straight_values = values[i:i+5]
                return [next(r for r in unique_ranks if self.RANK_VALUES[r] == v)
                       for v in straight_values]

        return None

    def _calculate_score(self, hand_rank: HandRank, high_cards: List[str]) -> int:
        """Calculate numeric strength score."""
        base_score = hand_rank.value * 1000000

        # Add high card values
        multiplier = 10000
        for card in high_cards[:5]:
            base_score += self.RANK_VALUES[card] * multiplier
            multiplier //= 100

        return base_score

    def compare_hands(
        self,
        hand1_cards: List[str],
        hand2_cards: List[str],
        board_cards: Optional[List[str]] = None
    ) -> int:
        """
        Compare two hands.

        Args:
            hand1_cards: First player's hole cards
            hand2_cards: Second player's hole cards
            board_cards: Community cards (optional)

        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        eval1 = self.evaluate_hand(hand1_cards, board_cards)
        eval2 = self.evaluate_hand(hand2_cards, board_cards)

        if eval1.strength_score > eval2.strength_score:
            return 1
        elif eval1.strength_score < eval2.strength_score:
            return -1
        else:
            return 0

    def get_hand_category(self, hole_cards: List[str]) -> str:
        """
        Categorize preflop hand.

        Args:
            hole_cards: Two hole cards

        Returns:
            Hand category (e.g., "Premium", "Pocket Pair", "Suited Connectors")
        """
        if len(hole_cards) != 2:
            return "Invalid"

        cards = self.parse_cards(hole_cards)
        if len(cards) != 2:
            return "Invalid"

        r1, r2 = cards[0].rank, cards[1].rank
        v1, v2 = self.RANK_VALUES[r1], self.RANK_VALUES[r2]
        suited = cards[0].suit == cards[1].suit

        # Pocket pair
        if r1 == r2:
            if v1 >= 11:  # JJ+
                return "Premium Pair"
            elif v1 >= 8:  # 88-TT
                return "Medium Pair"
            else:
                return "Small Pair"

        # High cards
        if min(v1, v2) >= 11:
            return "Premium (suited)" if suited else "Premium"

        # Suited connectors
        if suited and abs(v1 - v2) <= 2:
            return "Suited Connectors"

        # Broadway cards
        if min(v1, v2) >= 10:
            return "Broadway"

        return "Speculative"

    def reset(self):
        """Reset evaluator."""
        self.evaluations_count = 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    evaluator = HandStrengthEvaluator()

    # Example usage
    result = evaluator.evaluate_hand(['Ah', 'Kh'], ['Qh', 'Jh', 'Th', '5c', '2d'])
    print(f"\nHand: {result.rank_description}")
    print(f"Rank: {result.hand_rank.name}")
    print(f"Score: {result.strength_score}")

    category = evaluator.get_hand_category(['Ah', 'Kd'])
    print(f"\nHand category: {category}")
