"""
Range Generator for Solver-Based Preflop Charts

Generates optimal preflop ranges for various situations using GTO solver principles.
Supports 100bb deep ranges, ante adjustments, straddle adaptations, ICM adjustments,
and multi-way pot ranges.

Part of PREFLOP-001
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


class Position(Enum):
    """Player positions"""
    UTG = "utg"
    UTG1 = "utg1"
    UTG2 = "utg2"
    MP = "mp"
    MP1 = "mp1"
    MP2 = "mp2"
    LJ = "lj"
    HJ = "hj"
    CO = "co"
    BTN = "btn"
    SB = "sb"
    BB = "bb"


class Action(Enum):
    """Preflop actions"""
    OPEN_RAISE = "open_raise"
    CALL = "call"
    THREE_BET = "three_bet"
    FOUR_BET = "four_bet"
    FIVE_BET = "five_bet"
    FOLD = "fold"
    ALL_IN = "all_in"


@dataclass
class RangeParameters:
    """Parameters for range generation"""
    position: Position
    action: Action
    stack_depth: float  # In big blinds
    ante: float  # Ante as fraction of BB (0 for no ante)
    straddle: bool
    num_players: int  # For multi-way adjustments
    icm_pressure: float  # 0-1, higher = more ICM pressure
    facing_raise: bool
    raise_size: float  # Size of raise to call/3bet


@dataclass
class HandRange:
    """Represents a hand range"""
    hands: Dict[str, float]  # Hand -> frequency (0-1)
    total_combos: int
    vpip: float  # Percentage
    description: str


class HandParser:
    """Parse and manipulate poker hand notations"""
    
    SUITS = ['s', 'h', 'd', 'c']
    RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    
    @staticmethod
    def expand_notation(notation: str) -> List[str]:
        """Expand hand notation to specific hands"""
        # Examples: "AKs" -> ["AKs"], "AK" -> ["AKs", "AKo"], "88+" -> ["AA", "KK", ...]
        hands = []
        
        if notation == "any":
            return ["any"]
        
        # Handle pairs with +
        if len(notation) == 3 and notation[2] == '+' and notation[0] == notation[1]:
            rank = notation[0]
            rank_idx = HandParser.RANKS.index(rank)
            for i in range(rank_idx + 1):
                r = HandParser.RANKS[i]
                hands.append(f"{r}{r}")
            return hands
        
        # Handle suited with +
        if len(notation) == 4 and notation[2] == 's' and notation[3] == '+':
            rank1, rank2 = notation[0], notation[1]
            rank1_idx = HandParser.RANKS.index(rank1)
            rank2_idx = HandParser.RANKS.index(rank2)
            for i in range(rank1_idx + 1, rank2_idx + 1):
                r = HandParser.RANKS[i]
                hands.append(f"{rank1}{r}s")
            return hands
        
        # Handle offsuit with +
        if len(notation) == 4 and notation[2] == 'o' and notation[3] == '+':
            rank1, rank2 = notation[0], notation[1]
            rank1_idx = HandParser.RANKS.index(rank1)
            rank2_idx = HandParser.RANKS.index(rank2)
            for i in range(rank1_idx + 1, rank2_idx + 1):
                r = HandParser.RANKS[i]
                hands.append(f"{rank1}{r}o")
            return hands
        
        # Handle specific hands
        if len(notation) == 2:
            if notation[0] == notation[1]:
                hands.append(notation)  # Pair
            else:
                hands.append(f"{notation}s")  # Suited
                hands.append(f"{notation}o")  # Offsuit
        elif len(notation) == 3:
            hands.append(notation)  # Already specific
        
        return hands
    
    @staticmethod
    def count_combos(hand: str) -> int:
        """Count number of combinations for a hand"""
        if len(hand) == 2 and hand[0] == hand[1]:
            return 6  # Pairs
        elif hand.endswith('s'):
            return 4  # Suited
        elif hand.endswith('o'):
            return 12  # Offsuit
        return 0


class AnteAdjuster:
    """Adjust ranges based on ante"""
    
    @staticmethod
    def calculate_pot_odds_adjustment(ante: float, num_players: int = 9) -> float:
        """Calculate how much wider ranges should be with ante"""
        # With ante, pot is bigger, so we need better pot odds
        # This means we can play wider
        base_pot = 1.5  # SB + BB
        ante_contribution = ante * num_players
        total_pot = base_pot + ante_contribution
        
        # Calculate adjustment factor (1.0 = no adjustment)
        adjustment = total_pot / base_pot
        return adjustment
    
    @staticmethod
    def adjust_range(base_range: HandRange, ante: float, num_players: int = 9) -> HandRange:
        """Adjust range for ante"""
        adjustment_factor = AnteAdjuster.calculate_pot_odds_adjustment(ante, num_players)
        
        # Widen range by adjustment factor
        # This is a simplified model - real implementation would use solver data
        adjusted_hands = {}
        for hand, freq in base_range.hands.items():
            # Increase frequency slightly for marginal hands
            new_freq = min(1.0, freq * adjustment_factor * 0.1 + freq * 0.9)
            adjusted_hands[hand] = new_freq
        
        return HandRange(
            hands=adjusted_hands,
            total_combos=base_range.total_combos,
            vpip=base_range.vpip * adjustment_factor * 0.05 + base_range.vpip * 0.95,
            description=f"{base_range.description} (ante adjusted)"
        )


class StraddleAdapter:
    """Adapt ranges for straddle situations"""
    
    @staticmethod
    def adjust_for_straddle(base_range: HandRange, position: Position) -> HandRange:
        """Adjust range when there's a straddle"""
        # Straddle effectively moves positions back one
        # And increases required hand strength
        
        adjusted_hands = {}
        for hand, freq in base_range.hands.items():
            # Tighten up slightly
            new_freq = freq * 0.85  # Play ~15% tighter
            adjusted_hands[hand] = new_freq
        
        return HandRange(
            hands=adjusted_hands,
            total_combos=int(base_range.total_combos * 0.85),
            vpip=base_range.vpip * 0.85,
            description=f"{base_range.description} (straddle adapted)"
        )


class ICMAdjuster:
    """Adjust ranges based on ICM pressure"""
    
    @staticmethod
    def calculate_icm_adjustment(icm_pressure: float, position: Position) -> float:
        """Calculate ICM adjustment factor"""
        # Higher ICM pressure = tighter play
        # Early position needs more tightening
        position_multiplier = {
            Position.UTG: 1.3,
            Position.UTG1: 1.25,
            Position.UTG2: 1.2,
            Position.MP: 1.15,
            Position.LJ: 1.1,
            Position.HJ: 1.05,
            Position.CO: 1.0,
            Position.BTN: 0.95,
            Position.SB: 1.1,
            Position.BB: 1.0,
        }.get(position, 1.0)
        
        # Calculate tightening factor
        tightening = 1.0 - (icm_pressure * 0.3 * position_multiplier)
        return max(0.5, tightening)  # Cap at 50% tightening
    
    @staticmethod
    def adjust_range(base_range: HandRange, icm_pressure: float, position: Position) -> HandRange:
        """Adjust range for ICM"""
        adjustment_factor = ICMAdjuster.calculate_icm_adjustment(icm_pressure, position)
        
        adjusted_hands = {}
        for hand, freq in base_range.hands.items():
            # Reduce frequency based on ICM pressure
            new_freq = freq * adjustment_factor
            if new_freq > 0.1:  # Only include hands we play >10% of time
                adjusted_hands[hand] = new_freq
        
        return HandRange(
            hands=adjusted_hands,
            total_combos=int(base_range.total_combos * adjustment_factor),
            vpip=base_range.vpip * adjustment_factor,
            description=f"{base_range.description} (ICM adjusted)"
        )


class MultiWayAdjuster:
    """Adjust ranges for multi-way pots"""
    
    @staticmethod
    def calculate_multiway_adjustment(num_players: int) -> float:
        """Calculate how much to tighten for multi-way"""
        # More players = need stronger hands
        # 2 players = 1.0, 3 = 0.85, 4 = 0.75, etc.
        if num_players <= 2:
            return 1.0
        
        tightening = 1.0 - (num_players - 2) * 0.12
        return max(0.5, tightening)
    
    @staticmethod
    def adjust_range(base_range: HandRange, num_players: int) -> HandRange:
        """Adjust range for multi-way pot"""
        adjustment_factor = MultiWayAdjuster.calculate_multiway_adjustment(num_players)
        
        adjusted_hands = {}
        for hand, freq in base_range.hands.items():
            # Reduce frequency for multi-way
            new_freq = freq * adjustment_factor
            if new_freq > 0.1:
                adjusted_hands[hand] = new_freq
        
        return HandRange(
            hands=adjusted_hands,
            total_combos=int(base_range.total_combos * adjustment_factor),
            vpip=base_range.vpip * adjustment_factor,
            description=f"{base_range.description} (multi-way adjusted)"
        )


class BaseRangeGenerator:
    """Generate base GTO ranges for 100bb"""
    
    def __init__(self):
        self.ranges = self._initialize_base_ranges()
    
    def _initialize_base_ranges(self) -> Dict:
        """Initialize base GTO ranges"""
        # Simplified GTO ranges - in production, these would come from solver
        return {
            # UTG Open Raise (100bb)
            (Position.UTG, Action.OPEN_RAISE): self._create_range(
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
                 "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s", "A4s",
                 "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "T9s", "98s",
                 "AKo", "AQo", "AJo", "KQo"],
                "UTG Open Raise 100bb"
            ),
            
            # HJ Open Raise (100bb)
            (Position.HJ, Action.OPEN_RAISE): self._create_range(
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
                 "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A5s", "A4s", "A3s", "A2s",
                 "KQs", "KJs", "KTs", "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s", "T8s", "98s", "87s",
                 "AKo", "AQo", "AJo", "ATo", "KQo", "KJo"],
                "HJ Open Raise 100bb"
            ),
            
            # CO Open Raise (100bb)
            (Position.CO, Action.OPEN_RAISE): self._create_range(
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                 "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                 "KQs", "KJs", "KTs", "K9s", "K8s", "QJs", "QTs", "Q9s", "Q8s",
                 "JTs", "J9s", "J8s", "T9s", "T8s", "98s", "97s", "87s", "76s",
                 "AKo", "AQo", "AJo", "ATo", "A9o", "KQo", "KJo", "KTo", "QJo"],
                "CO Open Raise 100bb"
            ),
            
            # BTN Open Raise (100bb)
            (Position.BTN, Action.OPEN_RAISE): self._create_range(
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                 "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                 "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                 "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "JTs", "J9s", "J8s", "J7s",
                 "T9s", "T8s", "T7s", "98s", "97s", "96s", "87s", "86s", "76s", "75s", "65s",
                 "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o",
                 "KQo", "KJo", "KTo", "K9o", "QJo", "QTo", "JTo"],
                "BTN Open Raise 100bb"
            ),
            
            # SB Open Raise (100bb)
            (Position.SB, Action.OPEN_RAISE): self._create_range(
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                 "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                 "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s",
                 "QJs", "QTs", "Q9s", "Q8s", "Q7s", "JTs", "J9s", "J8s", "T9s", "T8s", "98s", "87s", "76s",
                 "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o",
                 "KQo", "KJo", "KTo", "K9o", "QJo", "QTo", "JTo"],
                "SB Open Raise 100bb"
            ),
        }
    
    def _create_range(self, hands: List[str], description: str) -> HandRange:
        """Create a hand range from hand list"""
        hand_dict = {}
        total_combos = 0
        
        for hand in hands:
            expanded = HandParser.expand_notation(hand)
            for h in expanded:
                hand_dict[h] = 1.0  # 100% frequency
                total_combos += HandParser.count_combos(h)
        
        # Calculate VPIP (simplified)
        vpip = len(hand_dict) * 100 / 169  # 169 total hand combinations
        
        return HandRange(
            hands=hand_dict,
            total_combos=total_combos,
            vpip=vpip,
            description=description
        )
    
    def get_base_range(self, position: Position, action: Action) -> Optional[HandRange]:
        """Get base range for position and action"""
        return self.ranges.get((position, action))


class RangeGenerator:
    """Main range generator with all adjustments"""
    
    def __init__(self):
        self.base_generator = BaseRangeGenerator()
        self.ante_adjuster = AnteAdjuster()
        self.straddle_adapter = StraddleAdapter()
        self.icm_adjuster = ICMAdjuster()
        self.multiway_adjuster = MultiWayAdjuster()
    
    def generate_range(self, params: RangeParameters) -> Optional[HandRange]:
        """Generate adjusted range based on parameters"""
        # Get base range
        base_range = self.base_generator.get_base_range(params.position, params.action)
        if not base_range:
            return None
        
        # Apply adjustments in order
        adjusted_range = base_range
        
        # Ante adjustment
        if params.ante > 0:
            adjusted_range = self.ante_adjuster.adjust_range(
                adjusted_range, params.ante, params.num_players
            )
        
        # Straddle adjustment
        if params.straddle:
            adjusted_range = self.straddle_adapter.adjust_for_straddle(
                adjusted_range, params.position
            )
        
        # ICM adjustment
        if params.icm_pressure > 0:
            adjusted_range = self.icm_adjuster.adjust_range(
                adjusted_range, params.icm_pressure, params.position
            )
        
        # Multi-way adjustment
        if params.num_players > 2:
            adjusted_range = self.multiway_adjuster.adjust_range(
                adjusted_range, params.num_players
            )
        
        return adjusted_range
    
    def export_range(self, hand_range: HandRange, filepath: str):
        """Export range to JSON file"""
        data = {
            'description': hand_range.description,
            'hands': hand_range.hands,
            'total_combos': hand_range.total_combos,
            'vpip': hand_range.vpip
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_range(self, filepath: str) -> HandRange:
        """Import range from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return HandRange(
            hands=data['hands'],
            total_combos=data['total_combos'],
            vpip=data['vpip'],
            description=data['description']
        )
