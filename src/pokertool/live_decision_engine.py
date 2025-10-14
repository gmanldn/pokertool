#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Live Decision Engine
====================

Real-time decision engine for compact live advice window.

Integrates:
- Confidence-aware decision API
- Win probability calculation (Monte Carlo)
- Ensemble decision aggregation
- Reasoning generation

Provides live updates with confidence intervals and win probability.

Version: 61.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import logging
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# Import decision engines
try:
    from .confidence_decision_api import (
        ConfidenceAwareDecisionAPI,
        DecisionRecommendation,
        get_confidence_decision_api
    )
    CONFIDENCE_API_AVAILABLE = True
except ImportError:
    CONFIDENCE_API_AVAILABLE = False
    logging.warning("confidence_decision_api not available")

try:
    from .gto_solver import EquityCalculator, calculate_range_equity
    GTO_SOLVER_AVAILABLE = True
except ImportError:
    GTO_SOLVER_AVAILABLE = False
    logging.warning("gto_solver not available")

try:
    from .ensemble_decision import EnsembleSystem, EngineDecision, DecisionType
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False
    logging.warning("ensemble_decision not available")

from .compact_live_advice_window import LiveAdviceData, ActionType

logger = logging.getLogger(__name__)


# ============================================================================
# Game State Structure
# ============================================================================

@dataclass
class GameState:
    """Current game state for decision making."""
    # Player's hand
    hole_cards: List[str] = field(default_factory=list)  # e.g., ['As', 'Kh']

    # Community cards
    community_cards: List[str] = field(default_factory=list)  # e.g., ['Qh', 'Jd', '9s']

    # Game info
    pot_size: float = 0.0
    call_amount: float = 0.0
    min_raise: float = 0.0
    max_raise: float = 0.0

    # Player info
    stack_size: float = 0.0
    position: str = "unknown"  # 'button', 'sb', 'bb', 'utg', etc.

    # Opponent info (optional)
    num_opponents: int = 1
    opponent_stack: Optional[float] = None
    opponent_tendencies: Optional[Dict[str, float]] = None

    # Street
    street: str = "preflop"  # 'preflop', 'flop', 'turn', 'river'

    # Additional context
    is_tournament: bool = False
    blinds: Tuple[float, float] = (1.0, 2.0)

    # Timestamp
    timestamp: float = field(default_factory=time.time)


# ============================================================================
# Win Probability Calculator
# ============================================================================

class WinProbabilityCalculator:
    """
    Calculate win probability using Monte Carlo simulation.

    Fast, accurate equity calculation for real-time updates.
    """

    def __init__(self, iterations: int = 10000):
        """
        Initialize win probability calculator.

        Args:
            iterations: Number of Monte Carlo iterations (default 10,000 for speed)
        """
        self.iterations = iterations
        self.cache = {}
        self.cache_ttl = 5.0  # 5 seconds cache TTL

        logger.info(f"WinProbabilityCalculator initialized with {iterations} iterations")

    def calculate(
        self,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int = 1
    ) -> float:
        """
        Calculate win probability.

        Args:
            hole_cards: Player's hole cards
            community_cards: Community cards
            num_opponents: Number of opponents

        Returns:
            Win probability (0.0-1.0)
        """
        # Check cache
        cache_key = self._make_cache_key(hole_cards, community_cards, num_opponents)
        if cache_key in self.cache:
            cached_value, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                logger.debug(f"Cache hit for win probability: {cached_value:.2%}")
                return cached_value

        # Calculate
        try:
            if GTO_SOLVER_AVAILABLE:
                win_prob = self._calculate_with_gto(hole_cards, community_cards, num_opponents)
            else:
                win_prob = self._calculate_fallback(hole_cards, community_cards, num_opponents)

            # Cache result
            self.cache[cache_key] = (win_prob, time.time())

            logger.debug(f"Calculated win probability: {win_prob:.2%}")
            return win_prob

        except Exception as e:
            logger.error(f"Error calculating win probability: {e}")
            return 0.5  # Fallback to 50%

    def _calculate_with_gto(
        self,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int
    ) -> float:
        """Calculate using GTO solver."""
        try:
            equity_calc = EquityCalculator()

            # Create opponent hands (random ranges)
            hands = [hole_cards]
            for _ in range(num_opponents):
                hands.append(["random", "random"])  # Placeholder for opponent range

            # Calculate equity
            equities = equity_calc.calculate_equity(
                hands,
                board=community_cards if community_cards else None,
                iterations=self.iterations
            )

            return equities[0] if equities else 0.5

        except Exception as e:
            logger.warning(f"GTO calculation failed: {e}")
            return self._calculate_fallback(hole_cards, community_cards, num_opponents)

    def _calculate_fallback(
        self,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int
    ) -> float:
        """
        Fallback calculation using simplified heuristics.

        Estimates based on:
        - Hand strength category
        - Number of opponents
        - Board texture
        """
        # Hand strength categories (simplified)
        strength = self._estimate_hand_strength(hole_cards, community_cards)

        # Adjust for opponents (more opponents = lower win probability)
        opponent_adjustment = 0.9 ** num_opponents

        # Final estimate
        win_prob = strength * opponent_adjustment

        return max(0.1, min(0.9, win_prob))  # Clamp to reasonable range

    def _estimate_hand_strength(
        self,
        hole_cards: List[str],
        community_cards: List[str]
    ) -> float:
        """Estimate hand strength (0.0-1.0)."""
        # Very simplified heuristic
        # In production, this would use proper hand evaluator

        if not hole_cards or len(hole_cards) < 2:
            return 0.5

        # Check for pairs
        if len(hole_cards) >= 2 and hole_cards[0][0] == hole_cards[1][0]:
            # Pocket pair
            rank_value = self._rank_to_value(hole_cards[0][0])
            return 0.5 + (rank_value / 26.0)  # 50-90% for pairs

        # High cards
        rank1 = self._rank_to_value(hole_cards[0][0])
        rank2 = self._rank_to_value(hole_cards[1][0]) if len(hole_cards) > 1 else 0
        avg_rank = (rank1 + rank2) / 2.0

        return 0.3 + (avg_rank / 26.0)  # 30-80% for high cards

    def _rank_to_value(self, rank: str) -> int:
        """Convert rank to numeric value."""
        rank_map = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        return rank_map.get(rank.upper(), 7)

    def _make_cache_key(
        self,
        hole_cards: List[str],
        community_cards: List[str],
        num_opponents: int
    ) -> str:
        """Make cache key."""
        hole_str = ''.join(sorted(hole_cards))
        comm_str = ''.join(sorted(community_cards)) if community_cards else ''
        return f"{hole_str}|{comm_str}|{num_opponents}"


# ============================================================================
# Reasoning Generator
# ============================================================================

class ReasoningGenerator:
    """
    Generate concise, actionable reasoning for decisions.

    Templates limited to 40 characters for compact display.
    """

    @staticmethod
    def generate(
        action: ActionType,
        win_prob: float,
        confidence: float,
        ev: Optional[float] = None,
        pot_odds: Optional[float] = None,
        hand_strength: Optional[float] = None
    ) -> str:
        """
        Generate concise reasoning.

        Args:
            action: Recommended action
            win_prob: Win probability (0-1)
            confidence: Confidence level (0-1)
            ev: Expected value
            pot_odds: Pot odds (0-1)
            hand_strength: Hand strength (0-1)

        Returns:
            Concise reasoning string (max 40 chars)
        """
        # Action-specific templates
        if action == ActionType.FOLD:
            return ReasoningGenerator._fold_reason(win_prob, pot_odds)
        elif action == ActionType.CALL:
            return ReasoningGenerator._call_reason(win_prob, pot_odds, ev)
        elif action == ActionType.RAISE:
            return ReasoningGenerator._raise_reason(win_prob, hand_strength, ev)
        elif action == ActionType.CHECK:
            return "Free card, check"
        elif action == ActionType.ALL_IN:
            return ReasoningGenerator._allin_reason(win_prob, confidence)
        else:
            return "Analyzing..."

    @staticmethod
    def _fold_reason(win_prob: float, pot_odds: Optional[float]) -> str:
        """Generate fold reasoning."""
        if pot_odds and pot_odds > 0:
            if win_prob < pot_odds * 0.5:
                return "Weak vs range, fold"
            elif win_prob < pot_odds:
                return "Not enough equity"
            else:
                return "Drawing dead"
        else:
            if win_prob < 0.3:
                return "Very weak hand"
            else:
                return "Fold to pressure"

    @staticmethod
    def _call_reason(win_prob: float, pot_odds: Optional[float], ev: Optional[float]) -> str:
        """Generate call reasoning."""
        if pot_odds and win_prob >= pot_odds:
            return "Good pot odds, call"
        elif ev and ev > 0:
            return "+EV call spot"
        elif win_prob > 0.5:
            return "Ahead, cautious call"
        else:
            return "Drawing, priced in"

    @staticmethod
    def _raise_reason(win_prob: float, hand_strength: Optional[float], ev: Optional[float]) -> str:
        """Generate raise reasoning."""
        if ev and ev > 10:
            return "Strong +EV, value raise"
        elif win_prob > 0.7:
            return "Strong hand, value bet"
        elif win_prob > 0.5:
            return "Ahead, semi-bluff"
        elif hand_strength and hand_strength > 0.6:
            return "Bluff spot, fold equity"
        else:
            return "Fold equity play"

    @staticmethod
    def _allin_reason(win_prob: float, confidence: float) -> str:
        """Generate all-in reasoning."""
        if win_prob > 0.8 and confidence > 0.8:
            return "Nuts, maximize value"
        elif win_prob > 0.6:
            return "Strong, commit stack"
        else:
            return "Bluff all-in, fold equity"


# ============================================================================
# Live Decision Engine
# ============================================================================

class LiveDecisionEngine:
    """
    Main decision engine for live advice.

    Integrates all decision systems and provides real-time recommendations.
    """

    def __init__(
        self,
        bankroll: float = 10000.0,
        win_calc_iterations: int = 10000
    ):
        """
        Initialize live decision engine.

        Args:
            bankroll: Current bankroll for risk calculations
            win_calc_iterations: Monte Carlo iterations for win probability
        """
        self.bankroll = bankroll

        # Initialize sub-systems
        self.confidence_api = None
        if CONFIDENCE_API_AVAILABLE:
            self.confidence_api = get_confidence_decision_api(bankroll=bankroll)
            logger.info("Confidence API initialized")

        self.win_calculator = WinProbabilityCalculator(iterations=win_calc_iterations)
        logger.info(f"Win calculator initialized ({win_calc_iterations} iterations)")

        # Performance tracking
        self.decision_count = 0
        self.avg_latency_ms = 0.0
        self.last_decision_time = 0.0

        logger.info("LiveDecisionEngine initialized")

    def get_live_advice(
        self,
        game_state: GameState,
        force_recalculate: bool = False
    ) -> LiveAdviceData:
        """
        Get live advice for current game state.

        Args:
            game_state: Current game state
            force_recalculate: Force recalculation (ignore cache)

        Returns:
            LiveAdviceData with recommendation and metrics
        """
        start_time = time.time()

        try:
            # Validate game state
            if not self._validate_game_state(game_state):
                return LiveAdviceData(
                    action=ActionType.UNKNOWN,
                    has_data=False,
                    reasoning="Invalid game state"
                )

            # Calculate win probability
            win_prob = self._calculate_win_probability(game_state)

            # Get decision recommendation
            if self.confidence_api:
                recommendation = self._get_confidence_recommendation(game_state, win_prob)
            else:
                recommendation = self._get_simple_recommendation(game_state, win_prob)

            # Convert to LiveAdviceData
            advice = self._convert_to_advice_data(recommendation, game_state)

            # Track performance
            latency_ms = (time.time() - start_time) * 1000
            self._update_performance_metrics(latency_ms)

            logger.info(f"Live advice generated in {latency_ms:.1f}ms: {advice.action.value}")

            return advice

        except Exception as e:
            logger.error(f"Error generating live advice: {e}", exc_info=True)
            return LiveAdviceData(
                action=ActionType.UNKNOWN,
                has_data=False,
                reasoning=f"Error: {str(e)[:30]}"
            )

    def _validate_game_state(self, game_state: GameState) -> bool:
        """Validate game state has minimum required data."""
        if not game_state.hole_cards or len(game_state.hole_cards) < 2:
            return False
        if game_state.pot_size < 0 or game_state.stack_size < 0:
            return False
        return True

    def _calculate_win_probability(self, game_state: GameState) -> float:
        """Calculate win probability from game state."""
        return self.win_calculator.calculate(
            game_state.hole_cards,
            game_state.community_cards,
            game_state.num_opponents
        )

    def _get_confidence_recommendation(
        self,
        game_state: GameState,
        win_prob: float
    ) -> DecisionRecommendation:
        """Get recommendation using confidence API."""
        try:
            # Calculate hand strength (simplified for now)
            hand_strength = self.win_calculator._estimate_hand_strength(
                game_state.hole_cards,
                game_state.community_cards
            )

            recommendation = self.confidence_api.recommend_decision(
                hand_strength=hand_strength,
                pot_size=game_state.pot_size,
                call_amount=game_state.call_amount,
                stack_size=game_state.stack_size,
                opponent_tendencies=game_state.opponent_tendencies,
                uncertainty_estimate=0.1  # Default uncertainty
            )

            # Override win probability with our calculated value
            recommendation.win_probability = win_prob

            return recommendation

        except Exception as e:
            logger.error(f"Confidence API error: {e}")
            return self._get_simple_recommendation(game_state, win_prob)

    def _get_simple_recommendation(
        self,
        game_state: GameState,
        win_prob: float
    ) -> Any:
        """Simple fallback recommendation without confidence API."""
        # Calculate pot odds
        pot_odds = game_state.call_amount / (game_state.pot_size + game_state.call_amount) \
                   if game_state.pot_size + game_state.call_amount > 0 else 0

        # Simple decision logic
        if win_prob < pot_odds * 0.7:
            action = "fold"
            confidence = 0.7
        elif win_prob < pot_odds * 1.2:
            action = "call"
            confidence = 0.6
        elif win_prob > 0.6:
            action = "raise"
            confidence = 0.8
        else:
            action = "call"
            confidence = 0.5

        # Create simple recommendation object
        class SimpleRecommendation:
            def __init__(self):
                self.action = action
                self.confidence_band = type('obj', (object,), {
                    'value': 'medium'
                })
                self.recommendation_strength = confidence
                self.win_probability = win_prob
                self.ev = 0.0
                self.ev_confidence_interval = type('obj', (object,), {
                    'mean': 0.0
                })
                self.win_prob_confidence_interval = None
                self.suggested_bet_size = game_state.pot_size * 0.75

        return SimpleRecommendation()

    def _convert_to_advice_data(
        self,
        recommendation: Any,
        game_state: GameState
    ) -> LiveAdviceData:
        """Convert recommendation to LiveAdviceData."""
        # Map action string to ActionType
        action_map = {
            'fold': ActionType.FOLD,
            'call': ActionType.CALL,
            'raise': ActionType.RAISE,
            'check': ActionType.CHECK,
            'all-in': ActionType.ALL_IN
        }
        action = action_map.get(recommendation.action.lower(), ActionType.UNKNOWN)

        # Extract metrics
        confidence = getattr(recommendation, 'recommendation_strength', 0.5)
        win_prob = getattr(recommendation, 'win_probability', 0.5)
        ev = getattr(recommendation, 'ev', None)

        # Calculate pot odds
        pot_odds = game_state.call_amount / (game_state.pot_size + game_state.call_amount) \
                   if game_state.pot_size + game_state.call_amount > 0 else None

        # Get bet size for raises
        action_amount = None
        if action == ActionType.RAISE:
            action_amount = getattr(recommendation, 'suggested_bet_size', game_state.pot_size * 0.75)

        # Generate reasoning
        reasoning = ReasoningGenerator.generate(
            action=action,
            win_prob=win_prob,
            confidence=confidence,
            ev=ev,
            pot_odds=pot_odds
        )

        return LiveAdviceData(
            action=action,
            action_amount=action_amount,
            win_probability=win_prob,
            confidence=confidence,
            reasoning=reasoning,
            has_data=True,
            is_calculating=False,
            ev=ev,
            pot_odds=pot_odds
        )

    def _update_performance_metrics(self, latency_ms: float):
        """Update performance tracking metrics."""
        self.decision_count += 1
        self.last_decision_time = time.time()

        # Exponential moving average
        alpha = 0.2
        self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'total_decisions': self.decision_count,
            'avg_latency_ms': self.avg_latency_ms,
            'cache_size': len(self.win_calculator.cache),
            'confidence_api_available': self.confidence_api is not None,
            'gto_solver_available': GTO_SOLVER_AVAILABLE
        }


# ============================================================================
# Factory Function
# ============================================================================

def get_live_decision_engine(
    bankroll: float = 10000.0,
    win_calc_iterations: int = 10000
) -> LiveDecisionEngine:
    """
    Factory function to create LiveDecisionEngine.

    Args:
        bankroll: Current bankroll
        win_calc_iterations: Monte Carlo iterations

    Returns:
        Configured LiveDecisionEngine instance
    """
    return LiveDecisionEngine(
        bankroll=bankroll,
        win_calc_iterations=win_calc_iterations
    )


# ============================================================================
# Demo / Testing
# ============================================================================

def demo():
    """Demo the live decision engine."""
    engine = get_live_decision_engine(bankroll=5000.0)

    # Test game states
    test_states = [
        GameState(
            hole_cards=['As', 'Kh'],
            community_cards=['Qh', 'Jd', '9s'],
            pot_size=100.0,
            call_amount=25.0,
            stack_size=500.0,
            street='flop'
        ),
        GameState(
            hole_cards=['2c', '7d'],
            community_cards=['Ah', 'Kd', 'Qs'],
            pot_size=50.0,
            call_amount=50.0,
            stack_size=200.0,
            street='flop'
        ),
        GameState(
            hole_cards=['Qd', 'Qc'],
            community_cards=[],
            pot_size=20.0,
            call_amount=10.0,
            stack_size=300.0,
            street='preflop'
        )
    ]

    for i, state in enumerate(test_states):
        print(f"\n{'='*60}")
        print(f"Test Case {i+1}:")
        print(f"  Hole Cards: {state.hole_cards}")
        print(f"  Board: {state.community_cards}")
        print(f"  Pot: ${state.pot_size}, Call: ${state.call_amount}")
        print(f"{'='*60}")

        advice = engine.get_live_advice(state)

        print(f"  Action: {advice.action.value}")
        if advice.action_amount:
            print(f"  Amount: ${advice.action_amount:.0f}")
        print(f"  Win Probability: {advice.win_probability*100:.1f}%")
        print(f"  Confidence: {advice.confidence*100:.1f}%")
        print(f"  Reasoning: {advice.reasoning}")

    # Show performance stats
    print(f"\n{'='*60}")
    print("Performance Stats:")
    stats = engine.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Starting Live Decision Engine Demo...")
    demo()
