"""
Opponent Profiler

Estimates opponent ranges and profiles based on observed actions and statistics.
"""
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlayerType(str, Enum):
    """Player type classification"""
    LAG = "LAG"  # Loose-Aggressive
    TAG = "TAG"  # Tight-Aggressive
    LP = "LP"    # Loose-Passive
    TP = "TP"    # Tight-Passive
    BALANCED = "BALANCED"


class Action(str, Enum):
    """Poker actions"""
    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    BET = "BET"
    RAISE = "RAISE"
    THREE_BET = "3BET"
    FOUR_BET = "4BET"


@dataclass
class OpponentStats:
    """Opponent statistics"""
    vpip: float  # Voluntarily Put $ In Pot %
    pfr: float   # Preflop Raise %
    threebet: float  # 3-Bet %
    fold_to_cbet: float  # Fold to C-Bet %
    fold_to_threebet: float  # Fold to 3-Bet %
    aggression: float  # Aggression Factor
    hands_played: int


class OpponentProfiler:
    """Profiles opponents and estimates their ranges"""

    def __init__(self):
        # Preflop ranges by hand strength percentile
        self.all_hands = self._generate_all_hands()

    def _generate_all_hands(self) -> List[str]:
        """Generate all 169 poker hands in strength order (approximate)"""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        hands = []

        # Pocket pairs (strongest first)
        for rank in ranks:
            hands.append(f"{rank}{rank}")

        # Suited connectors and high cards
        for i, rank1 in enumerate(ranks):
            for j, rank2 in enumerate(ranks):
                if i < j:  # Upper triangle (suited)
                    hands.append(f"{rank1}{rank2}s")

        # Offsuit hands
        for i, rank1 in enumerate(ranks):
            for j, rank2 in enumerate(ranks):
                if i < j:  # Upper triangle
                    hands.append(f"{rank1}{rank2}o")

        return hands

    def classify_player_type(self, stats: OpponentStats) -> PlayerType:
        """
        Classify player type based on VPIP and PFR

        Args:
            stats: Opponent statistics

        Returns:
            Player type classification
        """
        vpip = stats.vpip
        pfr = stats.pfr

        if vpip >= 35 and pfr >= 25:
            return PlayerType.LAG
        elif vpip <= 20 and pfr >= 15:
            return PlayerType.TAG
        elif vpip >= 35 and pfr < 15:
            return PlayerType.LP
        elif vpip <= 20 and pfr < 15:
            return PlayerType.TP
        else:
            return PlayerType.BALANCED

    def estimate_range(
        self,
        stats: OpponentStats,
        position: str,
        action: Action,
        facing_raise: bool = False
    ) -> List[str]:
        """
        Estimate opponent's range based on stats, position, and action

        Args:
            stats: Opponent statistics
            position: Table position (UTG, MP, CO, BTN, SB, BB)
            action: Action taken
            facing_raise: Whether opponent is facing a raise

        Returns:
            List of hand notations in estimated range
        """
        player_type = self.classify_player_type(stats)

        # Base range percentage by position and player type
        base_range_pct = self._get_base_range_pct(position, player_type, facing_raise)

        # Adjust based on action
        if action == Action.RAISE or action == Action.THREE_BET:
            # Tighten range for aggressive actions
            range_pct = base_range_pct * 0.5
        elif action == Action.CALL:
            # Slightly tighten for calls
            range_pct = base_range_pct * 0.8
        elif action == Action.CHECK:
            # Very wide range for checks
            range_pct = min(100, base_range_pct * 1.5)
        else:
            range_pct = base_range_pct

        # Cap at 100%
        range_pct = min(100, range_pct)

        # Select top X% of hands
        num_hands = int(len(self.all_hands) * (range_pct / 100))
        estimated_range = self.all_hands[:num_hands]

        logger.debug(
            f"Estimated range for {player_type.value} in {position} "
            f"with {action.value}: {len(estimated_range)} hands ({range_pct:.1f}%)"
        )

        return estimated_range

    def _get_base_range_pct(
        self,
        position: str,
        player_type: PlayerType,
        facing_raise: bool
    ) -> float:
        """Get base range percentage by position and player type"""

        # Position multipliers (tighter in early position)
        position_multipliers = {
            'UTG': 0.7,
            'MP': 0.85,
            'CO': 1.0,
            'BTN': 1.3,
            'SB': 0.9,
            'BB': 1.1
        }

        # Base ranges by player type (% of hands played)
        type_base_ranges = {
            PlayerType.LAG: 45.0,   # Plays 45% of hands
            PlayerType.TAG: 20.0,   # Plays 20% of hands
            PlayerType.LP: 40.0,    # Plays 40% of hands
            PlayerType.TP: 15.0,    # Plays 15% of hands
            PlayerType.BALANCED: 28.0  # Plays 28% of hands
        }

        base = type_base_ranges.get(player_type, 25.0)
        multiplier = position_multipliers.get(position.upper(), 1.0)

        # Tighten significantly if facing a raise
        if facing_raise:
            multiplier *= 0.4

        return base * multiplier

    def narrow_range(
        self,
        current_range: List[str],
        action: Action,
        street: str,
        board: List[str]
    ) -> List[str]:
        """
        Narrow range based on postflop action

        Args:
            current_range: Current estimated range
            action: Action taken on this street
            street: Current street (flop, turn, river)
            board: Community cards

        Returns:
            Narrowed range
        """
        # Simplified range narrowing logic
        if action == Action.BET or action == Action.RAISE:
            # Aggressive action - keep top 60% of current range
            narrow_pct = 0.6
        elif action == Action.CALL:
            # Calling - keep top 75% (remove weakest hands)
            narrow_pct = 0.75
        elif action == Action.CHECK:
            # Checking - could be full range or weak
            narrow_pct = 0.9
        else:
            narrow_pct = 1.0

        num_hands = int(len(current_range) * narrow_pct)
        narrowed_range = current_range[:num_hands]

        logger.debug(
            f"Narrowed range on {street} after {action.value}: "
            f"{len(current_range)} → {len(narrowed_range)} hands"
        )

        return narrowed_range

    def get_range_strength(self, range_hands: List[str]) -> Dict[str, float]:
        """
        Analyze range strength

        Args:
            range_hands: List of hands in range

        Returns:
            Dictionary with range statistics
        """
        total = len(range_hands)
        if total == 0:
            return {
                'pairs': 0.0,
                'suited': 0.0,
                'offsuit': 0.0,
                'premium': 0.0,
                'broadway': 0.0
            }

        pairs = sum(1 for h in range_hands if len(h) == 2)
        suited = sum(1 for h in range_hands if 's' in h)
        offsuit = sum(1 for h in range_hands if 'o' in h)

        # Premium hands (AA-TT, AKs-AJs, AKo)
        premium_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AKs', 'AQs', 'AJs', 'AKo']
        premium = sum(1 for h in range_hands if h in premium_hands)

        # Broadway hands (AKQJT)
        broadway_ranks = {'A', 'K', 'Q', 'J', 'T'}
        broadway = sum(
            1 for h in range_hands
            if len(h) >= 2 and h[0] in broadway_ranks and h[1] in broadway_ranks
        )

        return {
            'pairs': (pairs / total) * 100,
            'suited': (suited / total) * 100,
            'offsuit': (offsuit / total) * 100,
            'premium': (premium / total) * 100,
            'broadway': (broadway / total) * 100,
            'total_combos': total
        }
