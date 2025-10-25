#!/usr/bin/env python3
"""Range Calculator - Manages poker hand ranges"""

import logging
from typing import List, Set, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RangeType(Enum):
    """Range types"""
    OPENING = "opening"
    CALLING = "calling"
    THREE_BET = "three_bet"
    FOUR_BET = "four_bet"
    SQUEEZE = "squeeze"


@dataclass
class HandRange:
    """Hand range definition"""
    name: str
    range_type: RangeType
    hands: Set[str]
    percentage: float


class RangeCalculator:
    """Manages and calculates poker hand ranges."""

    RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

    def __init__(self):
        """Initialize range calculator."""
        self.ranges: dict[str, HandRange] = {}
        self._load_standard_ranges()

    def _load_standard_ranges(self):
        """Load standard opening ranges."""
        # Tight opening range (~15%)
        tight_hands = self._parse_range_string(
            "AA,KK,QQ,JJ,TT,99,88,77,AKs,AQs,AJs,AKo,AQo"
        )
        self.ranges['tight_open'] = HandRange(
            'tight_open', RangeType.OPENING, tight_hands, 15.0
        )

        # Standard opening range (~20%)
        standard_hands = self._parse_range_string(
            "AA,KK,QQ,JJ,TT,99,88,77,66,55,AKs,AQs,AJs,ATs,A9s,KQs,KJs,AKo,AQo,KQo"
        )
        self.ranges['standard_open'] = HandRange(
            'standard_open', RangeType.OPENING, standard_hands, 20.0
        )

        # Loose opening range (~30%)
        loose_hands = self._parse_range_string(
            "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,"
            "KQs,KJs,KTs,QJs,QTs,JTs,T9s,98s,87s,AKo,AQo,AJo,ATo,KQo,KJo"
        )
        self.ranges['loose_open'] = HandRange(
            'loose_open', RangeType.OPENING, loose_hands, 30.0
        )

    def _parse_range_string(self, range_str: str) -> Set[str]:
        """Parse comma-separated range string."""
        hands = set()
        for hand in range_str.split(','):
            hand = hand.strip()
            if hand:
                hands.add(hand)
        return hands

    def add_range(self, name: str, range_type: RangeType, hands: Set[str]) -> HandRange:
        """Add a custom range."""
        percentage = self.calculate_range_percentage(hands)
        hand_range = HandRange(name, range_type, hands, percentage)
        self.ranges[name] = hand_range
        logger.info(f"Added range '{name}' with {len(hands)} combos ({percentage}%)")
        return hand_range

    def get_range(self, name: str) -> Optional[HandRange]:
        """Get a range by name."""
        return self.ranges.get(name)

    def calculate_range_percentage(self, hands: Set[str]) -> float:
        """Calculate percentage of all possible hands."""
        total_combos = 1326  # Total poker hand combinations
        range_combos = 0

        for hand in hands:
            if hand.endswith('s'):  # Suited
                range_combos += 4
            elif hand.endswith('o'):  # Offsuit
                range_combos += 12
            elif len(hand) == 2 and hand[0] == hand[1]:  # Pocket pair
                range_combos += 6
            else:
                # Generic hand like AK (both suited and offsuit)
                range_combos += 16

        return round((range_combos / total_combos) * 100, 2)

    def combine_ranges(self, range1_name: str, range2_name: str, new_name: str) -> Optional[HandRange]:
        """Combine two ranges into a new range."""
        r1 = self.get_range(range1_name)
        r2 = self.get_range(range2_name)

        if not r1 or not r2:
            return None

        combined_hands = r1.hands | r2.hands
        return self.add_range(new_name, r1.range_type, combined_hands)

    def subtract_ranges(self, range1_name: str, range2_name: str, new_name: str) -> Optional[HandRange]:
        """Subtract range2 from range1."""
        r1 = self.get_range(range1_name)
        r2 = self.get_range(range2_name)

        if not r1 or not r2:
            return None

        subtracted_hands = r1.hands - r2.hands
        if not subtracted_hands:
            return None

        return self.add_range(new_name, r1.range_type, subtracted_hands)

    def is_hand_in_range(self, hand: str, range_name: str) -> bool:
        """Check if a hand is in a range."""
        hand_range = self.get_range(range_name)
        if not hand_range:
            return False

        return hand in hand_range.hands

    def get_range_strength(self, range_name: str) -> float:
        """Get average strength of range (simplified)."""
        hand_range = self.get_range(range_name)
        if not hand_range:
            return 0.0

        # Simplified strength based on premium hands
        premium_count = sum(1 for h in hand_range.hands if h in ['AA', 'KK', 'QQ', 'AKs'])
        return round((premium_count / len(hand_range.hands)) * 100, 2) if hand_range.hands else 0.0

    def polarize_range(self, range_name: str, top_percent: float, bottom_percent: float) -> Optional[HandRange]:
        """Create a polarized range (strong + weak hands)."""
        original = self.get_range(range_name)
        if not original:
            return None

        all_hands = sorted(list(original.hands))
        total = len(all_hands)

        top_count = int(total * (top_percent / 100))
        bottom_count = int(total * (bottom_percent / 100))

        polarized = set(all_hands[:top_count] + all_hands[-bottom_count:])
        return self.add_range(f"{range_name}_polarized", original.range_type, polarized)

    def get_all_range_names(self) -> List[str]:
        """Get all range names."""
        return list(self.ranges.keys())

    def export_range(self, range_name: str) -> str:
        """Export range as formatted string."""
        hand_range = self.get_range(range_name)
        if not hand_range:
            return ""

        hands_str = ','.join(sorted(hand_range.hands))
        return f"{range_name} ({hand_range.percentage}%): {hands_str}"


if __name__ == '__main__':
    calc = RangeCalculator()
    tight = calc.get_range('tight_open')
    print(f"Tight opening range: {tight.percentage}% of hands")
    print(f"Contains AA: {calc.is_hand_in_range('AA', 'tight_open')}")
