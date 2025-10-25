#!/usr/bin/env python3
"""Equity Calculator - Calculates hand equity"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Suit(Enum):
    """Card suits"""
    SPADES = "s"
    HEARTS = "h"
    DIAMONDS = "d"
    CLUBS = "c"


@dataclass
class Card:
    """Playing card"""
    rank: str
    suit: Suit


@dataclass
class EquityResult:
    """Equity calculation result"""
    hand: str
    win_equity: float
    tie_equity: float
    total_equity: float
    outs: int


class EquityCalculator:
    """Calculates poker hand equity."""

    RANK_VALUES = {
        'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
        '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2
    }

    def __init__(self):
        """Initialize equity calculator."""
        self.simulations = 1000
        self.deck: List[Card] = []
        self._build_deck()

    def _build_deck(self):
        """Build a standard 52-card deck."""
        for suit in Suit:
            for rank in self.RANK_VALUES.keys():
                self.deck.append(Card(rank, suit))

    def calculate_equity(
        self,
        hero_hand: List[Card],
        villain_range: List[List[Card]],
        board: Optional[List[Card]] = None
    ) -> EquityResult:
        """Calculate equity against a range."""
        if board is None:
            board = []

        wins = 0
        ties = 0
        total = len(villain_range)

        for villain_hand in villain_range:
            result = self._compare_hands(hero_hand, villain_hand, board)
            if result > 0:
                wins += 1
            elif result == 0:
                ties += 1

        win_equity = round((wins / total) * 100, 2) if total > 0 else 0.0
        tie_equity = round((ties / total) * 100, 2) if total > 0 else 0.0
        total_equity = round(win_equity + (tie_equity / 2), 2)

        outs = self.count_outs(hero_hand, board)

        return EquityResult(
            hand=self._format_hand(hero_hand),
            win_equity=win_equity,
            tie_equity=tie_equity,
            total_equity=total_equity,
            outs=outs
        )

    def _compare_hands(
        self,
        hand1: List[Card],
        hand2: List[Card],
        board: List[Card]
    ) -> int:
        """Compare two hands. Returns 1 if hand1 wins, -1 if hand2 wins, 0 for tie."""
        # Simplified comparison based on high card
        hand1_value = max(self.RANK_VALUES[c.rank] for c in hand1)
        hand2_value = max(self.RANK_VALUES[c.rank] for c in hand2)

        if hand1_value > hand2_value:
            return 1
        elif hand1_value < hand2_value:
            return -1
        else:
            return 0

    def count_outs(self, hand: List[Card], board: List[Card]) -> int:
        """Count number of outs (simplified)."""
        if not board:
            return 0

        # Count cards that could improve hand
        used_cards = set((c.rank, c.suit) for c in hand + board)
        remaining = 52 - len(used_cards)

        # Simplified: count cards that beat board
        outs = 0
        board_high = max(self.RANK_VALUES[c.rank] for c in board) if board else 0
        hand_high = max(self.RANK_VALUES[c.rank] for c in hand)

        if hand_high < board_high:
            # Count higher cards
            for card in self.deck:
                if (card.rank, card.suit) not in used_cards:
                    if self.RANK_VALUES[card.rank] > board_high:
                        outs += 1

        return min(outs, remaining)

    def calculate_pot_equity(self, equity: float, pot_size: float, bet_size: float) -> float:
        """Calculate pot equity value."""
        total_pot = pot_size + bet_size
        equity_value = (equity / 100) * total_pot
        return round(equity_value, 2)

    def calculate_required_equity(self, pot_size: float, bet_to_call: float) -> float:
        """Calculate required equity to call profitably."""
        total = pot_size + bet_to_call
        return round((bet_to_call / total) * 100, 2) if total > 0 else 0.0

    def is_profitable_call(self, equity: float, pot_size: float, bet_to_call: float) -> bool:
        """Check if call is profitable."""
        required = self.calculate_required_equity(pot_size, bet_to_call)
        return equity >= required

    def calculate_outs_to_equity(self, outs: int, cards_to_come: int = 1) -> float:
        """Convert outs to equity percentage."""
        if cards_to_come == 1:
            # Turn or river
            remaining = 52 - 5  # Assume 2 hole cards + 3 flop cards seen
            return round((outs / remaining) * 100, 2)
        elif cards_to_come == 2:
            # Turn and river
            equity = 1 - ((47 - outs) / 47) * ((46 - outs) / 46)
            return round(equity * 100, 2)
        return 0.0

    def calculate_ev(self, equity: float, pot_size: float, bet_size: float, call_amount: float) -> float:
        """Calculate expected value of a call."""
        win_ev = (equity / 100) * (pot_size + bet_size)
        lose_ev = (1 - equity / 100) * call_amount
        ev = win_ev - lose_ev
        return round(ev, 2)

    def _format_hand(self, hand: List[Card]) -> str:
        """Format hand as string."""
        if len(hand) != 2:
            return ""
        return f"{hand[0].rank}{hand[0].suit.value}{hand[1].rank}{hand[1].suit.value}"

    def get_hand_vs_range_equity(
        self,
        hand_str: str,
        range_size: int
    ) -> Dict[str, float]:
        """Get approximate equity vs range (simplified)."""
        # Simplified equity calculation
        hand_strength = self._estimate_hand_strength(hand_str)
        base_equity = 50.0

        if hand_strength > 0.7:
            base_equity = 65.0
        elif hand_strength > 0.5:
            base_equity = 55.0
        elif hand_strength < 0.3:
            base_equity = 35.0

        return {
            'win': round(base_equity, 2),
            'tie': round(5.0, 2),
            'total': round(base_equity + 2.5, 2)
        }

    def _estimate_hand_strength(self, hand_str: str) -> float:
        """Estimate hand strength (simplified)."""
        if len(hand_str) < 2:
            return 0.0

        rank1 = hand_str[0]
        rank2 = hand_str[1] if len(hand_str) > 1 else rank1

        value1 = self.RANK_VALUES.get(rank1, 0)
        value2 = self.RANK_VALUES.get(rank2, 0)

        avg_value = (value1 + value2) / 2
        normalized = (avg_value - 2) / 12  # Normalize to 0-1

        return round(normalized, 2)


if __name__ == '__main__':
    calc = EquityCalculator()

    # Example: AA vs KK
    aa = [Card('A', Suit.SPADES), Card('A', Suit.HEARTS)]
    kk = [Card('K', Suit.SPADES), Card('K', Suit.HEARTS)]

    result = calc.calculate_equity(aa, [kk])
    print(f"AA equity vs KK: {result.total_equity}%")
