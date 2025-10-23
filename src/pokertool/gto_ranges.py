#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GTO Range Calculator
====================

Provides Game Theory Optimal (GTO) range calculations and analysis.

Features:
- Hand range parsing and representation
- Range vs range equity calculation
- GTO frequency calculations
- Position-based opening ranges
- 3-bet/4-bet ranges
- Calling ranges vs aggression
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import itertools

logger = logging.getLogger(__name__)


class HandCategory(str, Enum):
    """Hand strength categories."""
    PREMIUM = "premium"      # AA, KK, QQ, AK
    STRONG = "strong"        # JJ, TT, AQ, AJs
    MEDIUM = "medium"        # 99-77, AJ, KQ, suited connectors
    WEAK = "weak"            # 66-22, Ax, Kx, suited gappers
    TRASH = "trash"          # 72o, 83o, etc.


@dataclass
class HandRange:
    """
    Represents a range of poker hands.

    Ranges can be specified as:
    - Specific hands: "AA", "AKs", "AKo"
    - Hand groups: "JJ+", "ATs+", "KQs+"
    - Ranges: "22+"  (all pairs 22 and above)
    - Suited/offsuit: "AKs", "AKo"
    """
    combos: Set[Tuple[str, str]] = field(default_factory=set)
    description: str = ""

    @classmethod
    def from_string(cls, range_str: str) -> HandRange:
        """
        Parse range from string notation.

        Examples:
            "AA" - Pocket aces
            "AKs" - Ace-king suited
            "AKo" - Ace-king offsuit
            "JJ+" - All pairs JJ and above
            "ATs+" - AT suited and above (AJs, AQs, AKs)
            "22-77" - Pairs from 22 to 77
        """
        range_obj = cls(description=range_str)

        # Split by comma for multiple ranges
        parts = [p.strip() for p in range_str.split(',')]

        for part in parts:
            range_obj._parse_range_part(part)

        return range_obj

    def _parse_range_part(self, part: str):
        """Parse a single range part."""
        # Handle plus notation (JJ+, ATs+)
        if '+' in part:
            self._parse_plus_notation(part)
        # Handle dash notation (22-77)
        elif '-' in part:
            self._parse_dash_notation(part)
        # Handle specific hands (AA, AKs, AKo)
        else:
            self._parse_specific_hand(part)

    def _parse_plus_notation(self, part: str):
        """Parse plus notation like 'JJ+' or 'ATs+'."""
        base = part.replace('+', '')

        if len(base) == 2:
            # Pair (JJ+)
            rank = base[0]
            rank_value = self._rank_to_value(rank)
            for r in range(rank_value, 15):  # Up to AA
                rank_str = self._value_to_rank(r)
                self._add_pair(rank_str)

        elif len(base) == 3:
            # Suited or offsuit (ATs+, AKo+)
            high_rank = base[0]
            low_rank = base[1]
            is_suited = base[2] == 's'

            low_value = self._rank_to_value(low_rank)
            high_value = self._rank_to_value(high_rank)

            # Add all combinations from low to high-1
            for r in range(low_value, high_value):
                low_str = self._value_to_rank(r)
                self._add_offsuit_or_suited(high_rank, low_str, is_suited)

    def _parse_dash_notation(self, part: str):
        """Parse dash notation like '22-77'."""
        start, end = part.split('-')

        start_value = self._rank_to_value(start[0])
        end_value = self._rank_to_value(end[0])

        for r in range(start_value, end_value + 1):
            rank_str = self._value_to_rank(r)
            self._add_pair(rank_str)

    def _parse_specific_hand(self, part: str):
        """Parse specific hand like 'AA', 'AKs', 'AKo'."""
        if len(part) == 2:
            # Pair (AA, KK, etc.)
            self._add_pair(part[0])

        elif len(part) == 3:
            # Suited or offsuit
            high_rank = part[0]
            low_rank = part[1]
            is_suited = part[2] == 's'

            self._add_offsuit_or_suited(high_rank, low_rank, is_suited)

    def _add_pair(self, rank: str):
        """Add all combinations of a pair."""
        suits = ['h', 'd', 'c', 's']
        for suit1, suit2 in itertools.combinations(suits, 2):
            self.combos.add((rank + suit1, rank + suit2))

    def _add_offsuit_or_suited(self, high_rank: str, low_rank: str, is_suited: bool):
        """Add suited or offsuit combinations."""
        suits = ['h', 'd', 'c', 's']

        if is_suited:
            # Suited - same suit
            for suit in suits:
                self.combos.add((high_rank + suit, low_rank + suit))
        else:
            # Offsuit - different suits
            for suit1 in suits:
                for suit2 in suits:
                    if suit1 != suit2:
                        self.combos.add((high_rank + suit1, low_rank + suit2))

    @staticmethod
    def _rank_to_value(rank: str) -> int:
        """Convert rank to numerical value."""
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
                      '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        return rank_values[rank]

    @staticmethod
    def _value_to_rank(value: int) -> str:
        """Convert numerical value to rank."""
        value_ranks = {2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
                      8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        return value_ranks[value]

    def combo_count(self) -> int:
        """Get total number of combinations in range."""
        return len(self.combos)

    def contains(self, card1: str, card2: str) -> bool:
        """Check if specific hand is in range."""
        return (card1, card2) in self.combos or (card2, card1) in self.combos

    def __len__(self) -> int:
        return len(self.combos)

    def __str__(self) -> str:
        return f"HandRange({self.description}, {len(self.combos)} combos)"


class GTOCalculator:
    """
    Calculates GTO frequencies and ranges.

    Example:
        calc = GTOCalculator()
        range = calc.get_opening_range(position="BTN", stack_bb=100)
        print(f"BTN opening range: {range.description}")
        print(f"Combos: {range.combo_count()}")
    """

    def __init__(self):
        """Initialize GTO calculator."""
        # Preflop opening ranges by position (100BB deep)
        self.opening_ranges = {
            'UTG': "JJ+,AQs+,AKo",
            'UTG+1': "TT+,AJs+,KQs,AQo+",
            'UTG+2': "TT+,AJs+,KQs,AQo+",
            'MP': "99+,ATs+,KJs+,QJs,AJo+,KQo",
            'MP+1': "99+,ATs+,KTs+,QTs+,JTs,T9s,98s,87s,76s,65s,AJo+,KQo",
            'MP+2': "88+,A9s+,K9s+,Q9s+,J9s+,T8s+,97s+,86s+,75s+,64s+,54s,ATo+,KJo+,QJo",
            'HJ': "77+,A2s+,K9s+,Q9s+,J9s+,T8s+,97s+,86s+,75s+,64s+,54s,A9o+,KTo+,QTo+,JTo",
            'CO': "66+,A2s+,K7s+,Q8s+,J8s+,T8s+,97s+,86s+,75s+,64s+,54s,43s,A8o+,K9o+,Q9o+,J9o+,T9o",
            'BTN': "22+,A2s+,K2s+,Q2s+,J6s+,T6s+,96s+,86s+,75s+,64s+,54s,43s,32s,A2o+,K8o+,Q9o+,J9o+,T9o,98o",
            'SB': "22+,A2s+,K2s+,Q4s+,J7s+,T7s+,97s+,86s+,75s+,65s,54s,A5o+,K9o+,Q9o+,J9o+,T9o",
            'BB': ""  # BB defends, doesn't open
        }

        # 3-bet ranges
        self.three_bet_ranges = {
            'BTN': "QQ+,AKs,AKo,AQs,AJs,KQs",  # vs CO open
            'SB': "TT+,AJs+,KQs,AQo+",         # vs BTN open
            'BB': "JJ+,AKs,AKo,AQs",           # vs BTN open
        }

    def get_opening_range(
        self,
        position: str,
        stack_bb: int = 100
    ) -> HandRange:
        """
        Get GTO opening range for position.

        Args:
            position: Position (UTG, MP, CO, BTN, SB, BB).
            stack_bb: Stack size in big blinds.

        Returns:
            HandRange for opening.
        """
        range_str = self.opening_ranges.get(position, "")

        if not range_str:
            return HandRange(description=f"{position} opening range")

        # Adjust for stack size
        if stack_bb < 20:
            # Short stack - tighten significantly
            range_str = self._tighten_range(range_str, factor=0.5)
        elif stack_bb < 40:
            # Medium stack - somewhat tighter
            range_str = self._tighten_range(range_str, factor=0.75)

        return HandRange.from_string(range_str)

    def get_three_bet_range(
        self,
        position: str,
        vs_position: str
    ) -> HandRange:
        """
        Get GTO 3-bet range.

        Args:
            position: Your position.
            vs_position: Opponent's position.

        Returns:
            HandRange for 3-betting.
        """
        range_str = self.three_bet_ranges.get(position, "QQ+,AKs,AKo")
        return HandRange.from_string(range_str)

    def get_calling_range(
        self,
        position: str,
        vs_position: str,
        bet_size_ratio: float
    ) -> HandRange:
        """
        Get GTO calling range vs raise.

        Args:
            position: Your position.
            vs_position: Opponent's position.
            bet_size_ratio: Size of bet relative to pot.

        Returns:
            HandRange for calling.
        """
        # Simplified calling range logic
        # Larger bets = tighter calling range

        if bet_size_ratio < 0.5:
            # Small bet - wider calling range
            base_range = "88+,A9s+,KTs+,QTs+,JTs,AJo+,KQo"
        elif bet_size_ratio < 1.0:
            # Pot-sized - medium calling range
            base_range = "99+,ATs+,KJs+,AQo+"
        else:
            # Overbet - tight calling range
            base_range = "TT+,AJs+,AQo+"

        return HandRange.from_string(base_range)

    def calculate_gto_frequencies(
        self,
        hero_range: HandRange,
        villain_range: HandRange,
        pot_size: float,
        bet_size: float
    ) -> Dict[str, float]:
        """
        Calculate GTO action frequencies.

        Args:
            hero_range: Hero's range.
            villain_range: Villain's range.
            pot_size: Current pot size.
            bet_size: Bet size.

        Returns:
            Dictionary with fold/call/raise frequencies.
        """
        # Simplified GTO frequency calculation
        # Real GTO requires solving game tree

        # Calculate pot odds
        pot_odds = bet_size / (pot_size + bet_size)

        # Estimate equity (simplified)
        hero_combos = len(hero_range)
        villain_combos = len(villain_range)

        # Very simplified equity estimate
        equity = hero_combos / (hero_combos + villain_combos)

        # GTO frequencies based on pot odds and equity
        if equity > pot_odds * 1.5:
            # Strong range - mostly raise/call
            return {
                'fold': 0.0,
                'call': 0.4,
                'raise': 0.6
            }
        elif equity > pot_odds:
            # Medium strength - mix of all actions
            return {
                'fold': 0.2,
                'call': 0.6,
                'raise': 0.2
            }
        else:
            # Weak range - mostly fold
            return {
                'fold': 0.7,
                'call': 0.25,
                'raise': 0.05
            }

    def _tighten_range(self, range_str: str, factor: float) -> str:
        """
        Tighten a range by a factor.

        Args:
            range_str: Original range string.
            factor: Tightening factor (0.5 = half as wide).

        Returns:
            Tightened range string.
        """
        # Simplified - just return tighter default ranges
        if factor < 0.5:
            return "QQ+,AKs,AKo"
        elif factor < 0.75:
            return "JJ+,AQs+,AKo"
        else:
            return range_str


# Example GTO ranges for common situations
GTO_RANGES = {
    'utg_open_100bb': "JJ+,AQs+,AKo",
    'btn_open_100bb': "22+,A2s+,K2s+,Q2s+,J6s+,T6s+,96s+,86s+,75s+,64s+,54s,43s,32s,A2o+,K8o+,Q9o+,J9o+,T9o,98o",
    'bb_vs_btn_defend': "22+,A2s+,K2s+,Q2s+,J4s+,T6s+,96s+,86s+,76s,65s,54s,A2o+,K7o+,Q8o+,J8o+,T8o+,98o",
    'btn_vs_co_3bet': "QQ+,AKs,AKo,AQs,AJs,KQs",
}
