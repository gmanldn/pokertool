"""
HUD Suggestions Module

Provides real-time contextual hand analysis suggestions during live play.
Integrates with existing hand analysis to show actionable advice in the HUD overlay.
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SuggestionType(str, Enum):
    """Types of suggestions"""
    PREFLOP = "preflop"
    POSTFLOP = "postflop"
    BLUFF = "bluff"
    VALUE = "value"
    FOLD_EQUITY = "fold_equity"
    POT_ODDS = "pot_odds"
    IMPLIED_ODDS = "implied_odds"
    POSITION = "position"


class SuggestionPriority(str, Enum):
    """Suggestion priority levels"""
    CRITICAL = "critical"  # Major mistake avoidance
    HIGH = "high"  # Strong strategic adjustment
    MEDIUM = "medium"  # Helpful optimization
    LOW = "low"  # Minor refinement


@dataclass
class Suggestion:
    """Individual suggestion"""
    type: SuggestionType
    priority: SuggestionPriority
    message: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    metadata: Optional[Dict[str, Any]] = None


class HUDSuggestionEngine:
    """Generate real-time hand analysis suggestions for HUD overlay"""

    def __init__(self):
        self.min_confidence = 0.6  # Minimum confidence to show suggestion
        self.max_suggestions = 3  # Maximum suggestions to show at once
        self.similar_situation_threshold = 0.75  # Similarity threshold for historical comparison

    def analyze_situation(
        self,
        hole_cards: List[str],
        board_cards: List[str],
        position: str,
        pot_size: float,
        to_call: float,
        stack_size: float,
        opponent_stats: Optional[Dict[str, float]] = None,
        action_history: Optional[List[Dict]] = None
    ) -> List[Suggestion]:
        """
        Analyze current situation and generate suggestions

        Args:
            hole_cards: Player's hole cards (e.g., ['As', 'Kh'])
            board_cards: Community cards (e.g., ['9s', '8c', '2d'])
            position: Player position (BTN, CO, etc.)
            pot_size: Current pot size
            to_call: Amount to call
            stack_size: Player's stack size
            opponent_stats: Optional opponent statistics
            action_history: Optional list of actions in current hand

        Returns:
            List of suggestions sorted by priority
        """
        suggestions = []

        # Preflop suggestions
        if len(board_cards) == 0:
            suggestions.extend(self._generate_preflop_suggestions(
                hole_cards, position, pot_size, to_call, stack_size, opponent_stats
            ))
        # Postflop suggestions
        else:
            suggestions.extend(self._generate_postflop_suggestions(
                hole_cards, board_cards, position, pot_size, to_call,
                stack_size, opponent_stats, action_history
            ))

        # Filter by confidence and limit count
        suggestions = [s for s in suggestions if s.confidence >= self.min_confidence]
        suggestions.sort(key=lambda x: (
            self._priority_score(x.priority),
            -x.confidence
        ), reverse=True)

        return suggestions[:self.max_suggestions]

    def _generate_preflop_suggestions(
        self,
        hole_cards: List[str],
        position: str,
        pot_size: float,
        to_call: float,
        stack_size: float,
        opponent_stats: Optional[Dict[str, float]]
    ) -> List[Suggestion]:
        """Generate preflop suggestions"""
        suggestions = []

        # Evaluate hand strength
        hand_strength = self._evaluate_preflop_strength(hole_cards)

        # Position-based suggestion
        if position in ['BTN', 'CO'] and hand_strength >= 0.6:
            suggestions.append(Suggestion(
                type=SuggestionType.POSITION,
                priority=SuggestionPriority.MEDIUM,
                message="Strong position - consider aggressive play",
                confidence=0.8,
                reasoning=f"Late position ({position}) with decent hand strength allows for wider range"
            ))

        # 3-bet suggestion based on opponent stats
        if opponent_stats and to_call > 0:
            opponent_fold_to_3bet = opponent_stats.get('fold_to_3bet', 50.0)
            if opponent_fold_to_3bet > 60 and hand_strength >= 0.5:
                suggestions.append(Suggestion(
                    type=SuggestionType.BLUFF,
                    priority=SuggestionPriority.HIGH,
                    message=f"Opponent folds to 3-bet {opponent_fold_to_3bet:.0f}% - 3-bet opportunity",
                    confidence=0.85,
                    reasoning=f"High fold-to-3bet percentage suggests profitable 3-bet bluff spots",
                    metadata={'fold_to_3bet': opponent_fold_to_3bet}
                ))

        # Stack-to-pot ratio consideration
        spr = stack_size / (pot_size + to_call) if (pot_size + to_call) > 0 else float('inf')
        if spr < 3 and hand_strength >= 0.7:
            suggestions.append(Suggestion(
                type=SuggestionType.VALUE,
                priority=SuggestionPriority.HIGH,
                message=f"Low SPR ({spr:.1f}) - consider all-in",
                confidence=0.75,
                reasoning="Low stack-to-pot ratio makes commitment easier with strong hands",
                metadata={'spr': spr}
            ))

        return suggestions

    def _generate_postflop_suggestions(
        self,
        hole_cards: List[str],
        board_cards: List[str],
        position: str,
        pot_size: float,
        to_call: float,
        stack_size: float,
        opponent_stats: Optional[Dict[str, float]],
        action_history: Optional[List[Dict]]
    ) -> List[Suggestion]:
        """Generate postflop suggestions"""
        suggestions = []

        # Calculate pot odds
        if to_call > 0:
            pot_odds = to_call / (pot_size + to_call)
            suggestions.append(Suggestion(
                type=SuggestionType.POT_ODDS,
                priority=SuggestionPriority.MEDIUM,
                message=f"Getting {(1/pot_odds):.1f}:1 pot odds ({pot_odds*100:.1f}% equity needed)",
                confidence=0.9,
                reasoning="Clear pot odds calculation for calling decision",
                metadata={'pot_odds': pot_odds, 'odds_ratio': 1/pot_odds}
            ))

        # Fold equity analysis
        if opponent_stats:
            fold_to_cbet = opponent_stats.get('fold_to_cbet', 40.0)
            if fold_to_cbet > 50 and len(board_cards) == 3:  # Flop
                suggestions.append(Suggestion(
                    type=SuggestionType.FOLD_EQUITY,
                    priority=SuggestionPriority.HIGH,
                    message=f"Fold equity increases - opponent folds to c-bets {fold_to_cbet:.0f}%",
                    confidence=0.8,
                    reasoning="High fold-to-cbet percentage creates profitable bluffing opportunities",
                    metadata={'fold_to_cbet': fold_to_cbet}
                ))

        # Board texture analysis
        board_texture = self._analyze_board_texture(board_cards)
        if board_texture['is_draw_heavy']:
            suggestions.append(Suggestion(
                type=SuggestionType.POSTFLOP,
                priority=SuggestionPriority.MEDIUM,
                message="Draw-heavy board - protect your hand",
                confidence=0.75,
                reasoning="Multiple draws possible - consider larger bet sizing",
                metadata=board_texture
            ))

        # Similar situation analysis
        if action_history:
            similar_advice = self._find_similar_situations(
                hole_cards, board_cards, action_history
            )
            if similar_advice:
                suggestions.append(Suggestion(
                    type=SuggestionType.POSTFLOP,
                    priority=SuggestionPriority.HIGH,
                    message=f"Similar situations suggest: {similar_advice['action']}",
                    confidence=similar_advice['confidence'],
                    reasoning=f"Based on {similar_advice['sample_size']} similar hands",
                    metadata=similar_advice
                ))

        return suggestions

    def _evaluate_preflop_strength(self, hole_cards: List[str]) -> float:
        """
        Evaluate preflop hand strength (0.0 to 1.0)

        Simple evaluation based on card ranks
        """
        if len(hole_cards) != 2:
            return 0.0

        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        rank_values = {r: i for i, r in enumerate(ranks)}

        try:
            card1_rank = hole_cards[0][0]
            card2_rank = hole_cards[1][0]
            card1_suit = hole_cards[0][1] if len(hole_cards[0]) > 1 else ''
            card2_suit = hole_cards[1][1] if len(hole_cards[1]) > 1 else ''

            value1 = rank_values.get(card1_rank, 0)
            value2 = rank_values.get(card2_rank, 0)

            # Base strength from high cards
            base_strength = (value1 + value2) / (2 * len(ranks))

            # Bonus for pairs
            if card1_rank == card2_rank:
                base_strength += 0.3

            # Bonus for suited
            if card1_suit == card2_suit and card1_suit:
                base_strength += 0.1

            # Bonus for connected cards
            if abs(value1 - value2) <= 1:
                base_strength += 0.05

            return min(1.0, base_strength)

        except (IndexError, KeyError):
            logger.warning(f"Invalid hole cards format: {hole_cards}")
            return 0.0

    def _analyze_board_texture(self, board_cards: List[str]) -> Dict[str, Any]:
        """Analyze board texture for draw possibilities"""
        if not board_cards:
            return {'is_draw_heavy': False}

        suits = [card[1] if len(card) > 1 else '' for card in board_cards]
        ranks = [card[0] for card in board_cards]

        # Check for flush draws
        suit_counts = {suit: suits.count(suit) for suit in set(suits) if suit}
        flush_draw = any(count >= 2 for count in suit_counts.values())

        # Check for straight draws (simple check for connected ranks)
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                      '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        values = sorted([rank_values.get(r, 0) for r in ranks if r in rank_values])
        straight_draw = False
        if len(values) >= 2:
            # Check for connected cards
            for i in range(len(values) - 1):
                if values[i+1] - values[i] <= 2:
                    straight_draw = True
                    break

        is_draw_heavy = flush_draw or straight_draw

        return {
            'is_draw_heavy': is_draw_heavy,
            'flush_draw': flush_draw,
            'straight_draw': straight_draw,
            'board_cards': board_cards
        }

    def _find_similar_situations(
        self,
        hole_cards: List[str],
        board_cards: List[str],
        action_history: List[Dict]
    ) -> Optional[Dict[str, Any]]:
        """
        Find similar situations from hand history

        In production, this would query a database of past hands
        For now, returns mock data
        """
        # Mock implementation - in production, would query hand history database
        if len(action_history) >= 2:
            return {
                'action': '4-bet',
                'confidence': 0.72,
                'sample_size': 15,
                'success_rate': 0.67
            }
        return None

    def _priority_score(self, priority: SuggestionPriority) -> int:
        """Convert priority to numeric score for sorting"""
        scores = {
            SuggestionPriority.CRITICAL: 4,
            SuggestionPriority.HIGH: 3,
            SuggestionPriority.MEDIUM: 2,
            SuggestionPriority.LOW: 1
        }
        return scores.get(priority, 0)

    def format_suggestion_for_hud(self, suggestion: Suggestion) -> Dict[str, Any]:
        """Format suggestion for HUD display"""
        priority_colors = {
            SuggestionPriority.CRITICAL: '#FF0000',
            SuggestionPriority.HIGH: '#FF9900',
            SuggestionPriority.MEDIUM: '#FFD700',
            SuggestionPriority.LOW: '#00FF00'
        }

        return {
            'message': suggestion.message,
            'reasoning': suggestion.reasoning,
            'priority': suggestion.priority.value,
            'color': priority_colors[suggestion.priority],
            'confidence': f"{suggestion.confidence * 100:.0f}%",
            'type': suggestion.type.value,
            'metadata': suggestion.metadata or {}
        }
