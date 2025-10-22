"""
GTO Calculator

Simplified Game Theory Optimal strategy calculator for poker.
Provides GTO frequencies, ranges, and preflop charts.

Note: This is a simplified heuristic implementation.
Production use would integrate PioSolver or similar GTO solver library.

Author: PokerTool Team
Created: 2025-10-22
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Position(str, Enum):
    """Table positions"""
    UTG = "UTG"
    MP = "MP"
    CO = "CO"
    BTN = "BTN"
    SB = "SB"
    BB = "BB"


class Street(str, Enum):
    """Poker streets"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


@dataclass
class GTOFrequencies:
    """GTO action frequencies"""
    fold: float = 0.0
    check: float = 0.0
    call: float = 0.0
    bet: float = 0.0
    raise_: float = 0.0
    all_in: float = 0.0

    def normalize(self):
        """Normalize frequencies to sum to 100"""
        total = self.fold + self.check + self.call + self.bet + self.raise_ + self.all_in
        if total > 0:
            self.fold = (self.fold / total) * 100
            self.check = (self.check / total) * 100
            self.call = (self.call / total) * 100
            self.bet = (self.bet / total) * 100
            self.raise_ = (self.raise_ / total) * 100
            self.all_in = (self.all_in / total) * 100


@dataclass
class GTORange:
    """GTO range for a position/action"""
    hands: List[str]
    percentage: float


class GTOCalculator:
    """
    Simplified GTO calculator

    Provides approximations of GTO strategy using heuristics.
    Not a substitute for proper GTO solver in production.
    """

    def __init__(self):
        # Preflop range charts
        self.preflop_ranges = self._load_preflop_ranges()

        # Pot odds to equity ratios
        self.pot_odds_table = self._build_pot_odds_table()

    def _load_preflop_ranges(self) -> Dict[Position, Dict[str, GTORange]]:
        """Load GTO preflop raising ranges by position"""

        ranges = {
            Position.UTG: GTORange(
                hands=[
                    'AA', 'KK', 'QQ', 'JJ', 'TT', '99',
                    'AKs', 'AQs', 'AJs', 'ATs',
                    'KQs', 'KJs',
                    'AKo'
                ],
                percentage=15.0
            ),
            Position.MP: GTORange(
                hands=[
                    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77',
                    'AKs', 'AQs', 'AJs', 'ATs', 'A9s',
                    'KQs', 'KJs', 'KTs',
                    'QJs', 'QTs',
                    'JTs',
                    'AKo', 'AQo'
                ],
                percentage=18.0
            ),
            Position.CO: GTORange(
                hands=[
                    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55',
                    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A5s', 'A4s',
                    'KQs', 'KJs', 'KTs', 'K9s',
                    'QJs', 'QTs', 'Q9s',
                    'JTs', 'J9s',
                    'T9s', 'T8s',
                    'AKo', 'AQo', 'AJo', 'KQo'
                ],
                percentage=26.0
            ),
            Position.BTN: GTORange(
                hands=[
                    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
                    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
                    'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'K6s',
                    'QJs', 'QTs', 'Q9s', 'Q8s',
                    'JTs', 'J9s', 'J8s',
                    'T9s', 'T8s', 'T7s',
                    '98s', '97s',
                    '87s', '86s',
                    '76s', '65s', '54s',
                    'AKo', 'AQo', 'AJo', 'ATo', 'A9o',
                    'KQo', 'KJo', 'KTo',
                    'QJo', 'QTo',
                    'JTo'
                ],
                percentage=48.0
            ),
            Position.SB: GTORange(
                hands=[
                    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
                    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
                    'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s',
                    'QJs', 'QTs', 'Q9s',
                    'JTs', 'J9s',
                    'T9s', 'T8s',
                    '98s', '87s', '76s', '65s',
                    'AKo', 'AQo', 'AJo', 'ATo',
                    'KQo', 'KJo',
                    'QJo'
                ],
                percentage=38.0
            ),
            Position.BB: GTORange(
                hands=[],  # BB defends based on pot odds
                percentage=0.0
            )
        }

        return {pos: {"open_raise": range_data} for pos, range_data in ranges.items()}

    def _build_pot_odds_table(self) -> Dict[float, float]:
        """Build pot odds to required equity table"""
        return {
            0.10: 9.1,   # 10% pot odds = 9.1% equity needed
            0.15: 13.0,
            0.20: 16.7,
            0.25: 20.0,
            0.30: 23.1,
            0.33: 25.0,
            0.40: 28.6,
            0.50: 33.3,
            0.60: 37.5,
            0.75: 42.9,
            1.00: 50.0,
            1.50: 60.0,
            2.00: 66.7
        }

    def get_preflop_range(self, position: Position, action: str = "open_raise") -> GTORange:
        """
        Get GTO preflop range for position and action

        Args:
            position: Table position
            action: Action type (open_raise, 3bet, 4bet, etc.)

        Returns:
            GTORange with hands and percentage
        """
        try:
            return self.preflop_ranges.get(position, {}).get(action, GTORange([], 0.0))
        except Exception as e:
            logger.error(f"Error getting preflop range: {e}")
            return GTORange([], 0.0)

    def calculate_frequencies(
        self,
        street: Street,
        pot_size: float,
        bet_to_call: float,
        stack_to_pot_ratio: float,
        equity: Optional[float] = None
    ) -> GTOFrequencies:
        """
        Calculate GTO action frequencies for a spot

        Simplified heuristic implementation based on:
        - Pot odds
        - SPR (Stack-to-Pot Ratio)
        - Estimated equity
        - Game theory principles

        Args:
            street: Current street
            pot_size: Pot size
            bet_to_call: Amount to call
            stack_to_pot_ratio: SPR
            equity: Estimated equity (optional)

        Returns:
            GTOFrequencies with normalized frequencies
        """
        freq = GTOFrequencies()

        # Calculate pot odds
        pot_odds = bet_to_call / (pot_size + bet_to_call) if pot_size + bet_to_call > 0 else 0

        # Preflop frequencies
        if street == Street.PREFLOP:
            if bet_to_call == 0:
                # Unopened pot
                freq.fold = 60.0
                freq.raise_ = 35.0
                freq.call = 5.0
            elif bet_to_call < pot_size * 0.5:
                # Facing small raise
                freq.fold = 40.0
                freq.call = 35.0
                freq.raise_ = 25.0
            else:
                # Facing large raise
                freq.fold = 55.0
                freq.call = 25.0
                freq.raise_ = 20.0

        # Postflop frequencies
        else:
            if bet_to_call == 0:
                # First to act
                if stack_to_pot_ratio > 2.0:
                    # Deep stacks
                    freq.check = 45.0
                    freq.bet = 45.0
                    freq.all_in = 10.0
                else:
                    # Short stacks
                    freq.check = 40.0
                    freq.bet = 35.0
                    freq.all_in = 25.0
            else:
                # Facing bet
                if equity:
                    required_equity = pot_odds * 100

                    if equity > required_equity * 1.3:
                        # Strong hand
                        freq.fold = 10.0
                        freq.call = 30.0
                        freq.raise_ = 50.0
                        freq.all_in = 10.0
                    elif equity > required_equity:
                        # Marginal hand
                        freq.fold = 25.0
                        freq.call = 60.0
                        freq.raise_ = 15.0
                    else:
                        # Weak hand
                        freq.fold = 70.0
                        freq.call = 20.0
                        freq.raise_ = 10.0
                else:
                    # No equity info - default mixed strategy
                    freq.fold = 50.0
                    freq.call = 35.0
                    freq.raise_ = 15.0

        # Normalize to 100%
        freq.normalize()

        logger.debug(f"GTO frequencies calculated for {street.value}: "
                    f"Fold {freq.fold:.1f}%, Call {freq.call:.1f}%, "
                    f"Raise {freq.raise_:.1f}%")

        return freq

    def calculate_range_gto(
        self,
        hero_range: List[str],
        villain_range: List[str],
        board: List[str],
        pot_size: float
    ) -> Dict[str, float]:
        """
        Calculate GTO strategy for range vs range

        Simplified implementation - returns action frequencies
        for hero's range against villain's range.

        Args:
            hero_range: Hero's hand range
            villain_range: Villain's hand range
            board: Community cards
            pot_size: Current pot size

        Returns:
            Dictionary with action frequencies
        """
        # Simplified: Calculate average equity of ranges
        # In production, would use proper GTO solver

        hero_strength = len(hero_range) / 169  # Rough strength estimate
        villain_strength = len(villain_range) / 169

        # Calculate approximate frequencies based on relative range strength
        if hero_strength > villain_strength * 1.3:
            return {
                "bet": 65.0,
                "check": 25.0,
                "fold": 10.0
            }
        elif hero_strength > villain_strength:
            return {
                "bet": 45.0,
                "check": 40.0,
                "fold": 15.0
            }
        else:
            return {
                "check": 50.0,
                "bet": 20.0,
                "fold": 30.0
            }

    def get_bb_defense_range(self, pot_odds: float) -> GTORange:
        """
        Get BB defense range based on pot odds

        Args:
            pot_odds: Pot odds offered (as decimal, e.g., 0.33 for 3:1)

        Returns:
            GTORange for defense
        """
        # Defend with hands that have equity > pot odds
        # Simplified: defend wider with better pot odds

        if pot_odds <= 0.25:
            # Bad pot odds (< 3:1)
            percentage = 30.0
            hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', 'AKs', 'AQs', 'AJs', 'AKo']
        elif pot_odds <= 0.35:
            # Mediocre pot odds (2-3:1)
            percentage = 45.0
            hands = [
                'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77',
                'AKs', 'AQs', 'AJs', 'ATs', 'A9s',
                'KQs', 'KJs',
                'QJs',
                'AKo', 'AQo', 'AJo'
            ]
        else:
            # Good pot odds (> 1.5:1)
            percentage = 65.0
            hands = [
                'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
                'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s',
                'KQs', 'KJs', 'KTs', 'K9s',
                'QJs', 'QTs', 'Q9s',
                'JTs', 'J9s',
                'T9s', '98s', '87s', '76s',
                'AKo', 'AQo', 'AJo', 'ATo',
                'KQo', 'KJo'
            ]

        return GTORange(hands=hands, percentage=percentage)

    def get_optimal_bet_size(
        self,
        pot_size: float,
        street: Street,
        stack_remaining: float
    ) -> Tuple[float, str]:
        """
        Get GTO bet size for a spot

        Args:
            pot_size: Current pot size
            street: Current street
            stack_remaining: Remaining stack

        Returns:
            Tuple of (bet_size, size_description)
        """
        # GTO bet sizes by street
        if street == Street.FLOP:
            size = pot_size * 0.66  # 2/3 pot
            description = "2/3 pot"
        elif street == Street.TURN:
            size = pot_size * 0.75  # 3/4 pot
            description = "3/4 pot"
        elif street == Street.RIVER:
            size = pot_size * 0.75  # 3/4 pot
            description = "3/4 pot"
        else:
            size = pot_size * 0.5
            description = "1/2 pot"

        # Cap at remaining stack
        if size > stack_remaining:
            size = stack_remaining
            description = "all-in"

        return (size, description)


# Global GTO calculator instance
_gto_calc: Optional[GTOCalculator] = None


def get_gto_calculator() -> GTOCalculator:
    """Get or create global GTO calculator instance"""
    global _gto_calc
    if _gto_calc is None:
        _gto_calc = GTOCalculator()
    return _gto_calc
