"""
Blocker Effects Analysis Module

Advanced blocker effects calculation for poker decision-making,
including card removal analysis, equity adjustments, and bluffing opportunities.

Part of MERGE-001: Advanced Range Merging Algorithm
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class BlockerType(Enum):
    """Types of blocker effects"""
    VALUE_BLOCKER = "value_blocker"      # Blocks opponent's value hands
    BLUFF_BLOCKER = "bluff_blocker"      # Blocks opponent's bluffs
    NUT_BLOCKER = "nut_blocker"          # Blocks the absolute nuts
    STRAIGHT_BLOCKER = "straight_blocker"
    FLUSH_BLOCKER = "flush_blocker"
    SET_BLOCKER = "set_blocker"


@dataclass
class BlockerStrength:
    """Quantifies blocker strength for a hand"""
    total_blocked_combos: int
    value_combos_blocked: int
    bluff_combos_blocked: int
    nut_combos_blocked: int
    blocker_score: float  # Normalized 0-1
    blocker_types: List[BlockerType]
    recommended_action: str  # 'bluff', 'call', 'fold', 'value'


class BoardTextureAnalyzer:
    """Analyze board texture for blocker potential"""
    
    def __init__(self):
        self.suits = ['h', 'd', 'c', 's']
        self.ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        self.rank_values = {r: i for i, r in enumerate(self.ranks)}
    
    def parse_board(self, board: str) -> List[str]:
        """Parse board string into list of cards"""
        cards = []
        i = 0
        while i < len(board):
            if i + 1 < len(board):
                card = board[i:i+2]
                if card[0] in self.ranks and card[1] in self.suits:
                    cards.append(card)
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        return cards
    
    def get_flush_draw_present(self, board: str) -> Tuple[bool, str]:
        """Check if flush draw is present on board"""
        cards = self.parse_board(board)
        if len(cards) < 3:
            return False, ''
        
        suit_counts = {suit: 0 for suit in self.suits}
        for card in cards:
            if len(card) >= 2:
                suit_counts[card[1]] += 1
        
        for suit, count in suit_counts.items():
            if count >= 3:
                return True, suit
        
        return False, ''
    
    def get_straight_draw_present(self, board: str) -> bool:
        """Check if straight draw is present on board"""
        cards = self.parse_board(board)
        if len(cards) < 3:
            return False
        
        ranks = sorted([self.rank_values[c[0]] for c in cards if c[0] in self.ranks])
        
        # Check for connected cards
        for i in range(len(ranks) - 1):
            if ranks[i+1] - ranks[i] <= 2:
                return True
        
        return False
    
    def identify_potential_nuts(self, board: str) -> List[str]:
        """Identify what hands represent the nuts on this board"""
        cards = self.parse_board(board)
        if len(cards) < 3:
            return []
        
        potential_nuts = []
        
        # Check for flush possibility
        flush_possible, flush_suit = self.get_flush_draw_present(board)
        if flush_possible:
            # Nut flush would be Ax in flush suit
            potential_nuts.append(f"A{flush_suit}")
        
        # Check for straight possibility
        if self.get_straight_draw_present(board):
            potential_nuts.append("straight")
        
        # Check for set/quads possibility
        ranks = [c[0] for c in cards if c[0] in self.ranks]
        for rank in set(ranks):
            if ranks.count(rank) >= 2:
                potential_nuts.append(f"{rank}{rank}")  # Set/quads
        
        return potential_nuts


class EquityAdjuster:
    """Adjust equity calculations based on blocker effects"""
    
    def __init__(self):
        self.base_adjustments = {
            BlockerType.VALUE_BLOCKER: 0.08,      # +8% when blocking value
            BlockerType.BLUFF_BLOCKER: -0.05,     # -5% when blocking bluffs
            BlockerType.NUT_BLOCKER: 0.12,        # +12% when blocking nuts
            BlockerType.STRAIGHT_BLOCKER: 0.06,
            BlockerType.FLUSH_BLOCKER: 0.07,
            BlockerType.SET_BLOCKER: 0.05,
        }
    
    def calculate_equity_adjustment(self, blocker_types: List[BlockerType],
                                   base_equity: float) -> float:
        """Calculate equity adjustment based on blocker types"""
        total_adjustment = 0.0
        
        for blocker_type in blocker_types:
            adjustment = self.base_adjustments.get(blocker_type, 0.0)
            total_adjustment += adjustment
        
        # Cap adjustment at +/- 15%
        total_adjustment = max(-0.15, min(0.15, total_adjustment))
        
        adjusted_equity = base_equity + total_adjustment
        return max(0.0, min(1.0, adjusted_equity))
    
    def calculate_implied_odds_adjustment(self, blocker_strength: BlockerStrength) -> float:
        """Calculate implied odds multiplier based on blockers"""
        # Strong blockers reduce opponent's continuing range
        if blocker_strength.blocker_score > 0.7:
            return 0.8  # Reduce implied odds
        elif blocker_strength.blocker_score > 0.5:
            return 0.9
        else:
            return 1.0  # No adjustment


class BluffSelector:
    """Select optimal bluffing candidates based on blockers"""
    
    def __init__(self):
        self.texture_analyzer = BoardTextureAnalyzer()
        self.equity_adjuster = EquityAdjuster()
    
    def evaluate_bluff_candidate(self, hand: str, board: str,
                                 villain_range: List[str]) -> BlockerStrength:
        """Evaluate a hand's potential as a bluff based on blockers"""
        # Parse hand
        hand_cards = set()
        i = 0
        while i < len(hand):
            if i + 1 < len(hand):
                card = hand[i:i+2]
                hand_cards.add(card)
                i += 2
            else:
                i += 1
        
        # Identify blocker types
        blocker_types = []
        value_blocked = 0
        bluff_blocked = 0
        nut_blocked = 0
        
        # Check for nut blockers
        potential_nuts = self.texture_analyzer.identify_potential_nuts(board)
        for nut_hand in potential_nuts:
            if any(nut_hand[0] == card[0] for card in hand_cards):
                blocker_types.append(BlockerType.NUT_BLOCKER)
                nut_blocked += 1
        
        # Check for flush blockers
        flush_possible, flush_suit = self.texture_analyzer.get_flush_draw_present(board)
        if flush_possible:
            for card in hand_cards:
                if len(card) >= 2 and card[1] == flush_suit:
                    if card[0] in ['A', 'K']:
                        blocker_types.append(BlockerType.FLUSH_BLOCKER)
                        value_blocked += 2
        
        # Check for straight blockers
        if self.texture_analyzer.get_straight_draw_present(board):
            board_ranks = set(c[0] for c in self.texture_analyzer.parse_board(board))
            hand_ranks = set(c[0] for c in hand_cards)
            if hand_ranks & board_ranks:
                blocker_types.append(BlockerType.STRAIGHT_BLOCKER)
                value_blocked += 1
        
        # Simplified range analysis
        for vill_hand in villain_range:
            if vill_hand[0] in ['A', 'K', 'Q']:
                # Check if we block this value hand
                if any(vill_hand[0] == card[0] for card in hand_cards):
                    value_blocked += 1
            else:
                # Weaker hands (potential bluffs)
                if any(vill_hand[0] == card[0] for card in hand_cards):
                    bluff_blocked += 1
        
        # Classify blocker type
        if value_blocked > bluff_blocked:
            if BlockerType.VALUE_BLOCKER not in blocker_types:
                blocker_types.append(BlockerType.VALUE_BLOCKER)
        elif bluff_blocked > value_blocked:
            if BlockerType.BLUFF_BLOCKER not in blocker_types:
                blocker_types.append(BlockerType.BLUFF_BLOCKER)
        
        # Calculate blocker score (0-1)
        total_blocked = value_blocked + bluff_blocked + nut_blocked
        blocker_score = min(1.0, (value_blocked * 0.3 + nut_blocked * 0.5) / 
                           max(1, total_blocked))
        
        # Recommend action
        if blocker_score > 0.6 and value_blocked > bluff_blocked:
            action = 'bluff'
        elif blocker_score > 0.4:
            action = 'call'
        else:
            action = 'fold'
        
        return BlockerStrength(
            total_blocked_combos=total_blocked,
            value_combos_blocked=value_blocked,
            bluff_combos_blocked=bluff_blocked,
            nut_combos_blocked=nut_blocked,
            blocker_score=blocker_score,
            blocker_types=blocker_types,
            recommended_action=action
        )
    
    def rank_bluff_candidates(self, hands: List[str], board: str,
                            villain_range: List[str]) -> List[Tuple[str, BlockerStrength]]:
        """Rank multiple hands by bluffing potential"""
        candidates = []
        
        for hand in hands:
            strength = self.evaluate_bluff_candidate(hand, board, villain_range)
            candidates.append((hand, strength))
        
        # Sort by blocker score (higher is better for bluffing)
        return sorted(candidates, key=lambda x: x[1].blocker_score, reverse=True)
    
    def select_optimal_bluffs(self, hands: List[str], board: str,
                            villain_range: List[str], 
                            num_bluffs: int) -> List[str]:
        """Select optimal bluffing hands from candidates"""
        ranked = self.rank_bluff_candidates(hands, board, villain_range)
        
        # Select top N hands that have good bluffing potential
        selected = []
        for hand, strength in ranked:
            if len(selected) >= num_bluffs:
                break
            if strength.recommended_action in ['bluff', 'call']:
                selected.append(hand)
        
        return selected


class RangeBlockerAnalysis:
    """Analyze how a range blocks opponent's range"""
    
    def __init__(self):
        self.selector = BluffSelector()
        self.equity_adjuster = EquityAdjuster()
    
    def analyze_range_blockers(self, hero_range: List[str],
                               villain_range: List[str],
                               board: str) -> Dict[str, any]:
        """Comprehensive blocker analysis for entire range"""
        results = {
            'total_hands_analyzed': len(hero_range),
            'strong_blockers': [],
            'weak_blockers': [],
            'avg_blocker_score': 0.0,
            'recommended_bluffs': [],
            'recommended_calls': [],
            'recommended_folds': []
        }
        
        total_score = 0.0
        
        for hand in hero_range:
            strength = self.selector.evaluate_bluff_candidate(
                hand, board, villain_range
            )
            
            total_score += strength.blocker_score
            
            if strength.blocker_score > 0.6:
                results['strong_blockers'].append((hand, strength))
            elif strength.blocker_score < 0.3:
                results['weak_blockers'].append((hand, strength))
            
            # Categorize by recommendation
            if strength.recommended_action == 'bluff':
                results['recommended_bluffs'].append(hand)
            elif strength.recommended_action == 'call':
                results['recommended_calls'].append(hand)
            else:
                results['recommended_folds'].append(hand)
        
        results['avg_blocker_score'] = total_score / len(hero_range) if hero_range else 0.0
        
        return results
    
    def compare_blocker_strategies(self, strategy1_range: List[str],
                                  strategy2_range: List[str],
                                  villain_range: List[str],
                                  board: str) -> Dict[str, any]:
        """Compare blocker effectiveness of two strategies"""
        analysis1 = self.analyze_range_blockers(strategy1_range, villain_range, board)
        analysis2 = self.analyze_range_blockers(strategy2_range, villain_range, board)
        
        return {
            'strategy1': analysis1,
            'strategy2': analysis2,
            'winner': 'strategy1' if analysis1['avg_blocker_score'] > analysis2['avg_blocker_score'] else 'strategy2',
            'score_difference': abs(analysis1['avg_blocker_score'] - analysis2['avg_blocker_score'])
        }


# Utility functions
def quick_blocker_eval(hand: str, board: str, villain_value_hands: List[str]) -> float:
    """Quick blocker evaluation (0-1 score)"""
    selector = BluffSelector()
    strength = selector.evaluate_bluff_candidate(hand, board, villain_value_hands)
    return strength.blocker_score


def get_best_bluff_combos(candidate_hands: List[str], board: str,
                         villain_range: List[str], count: int = 5) -> List[str]:
    """Get the best bluff combos from a list of candidates"""
    selector = BluffSelector()
    return selector.select_optimal_bluffs(candidate_hands, board, villain_range, count)


def calculate_blocker_equity_boost(hand: str, board: str,
                                  base_equity: float) -> float:
    """Calculate equity boost from blockers"""
    selector = BluffSelector()
    adjuster = EquityAdjuster()
    
    strength = selector.evaluate_bluff_candidate(hand, board, [])
    return adjuster.calculate_equity_adjustment(strength.blocker_types, base_equity)
