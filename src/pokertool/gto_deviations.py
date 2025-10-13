#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GTO Deviations Module
=====================

Calculates profitable deviations from Game Theory Optimal (GTO) strategy
based on opponent tendencies and population biases.

This module provides tools for:
- Maximum exploitation strategy finding
- Population tendency adjustments
- Node-locking strategies
- Strategy simplification
- Deviation EV calculation

Author: PokerTool Development Team
Version: 1.0.0
Last Modified: 2025-10-02
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Poker action types."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


class StrategyType(Enum):
    """Strategy deviation types."""
    GTO = "gto"
    EXPLOITATIVE = "exploitative"
    SIMPLIFIED = "simplified"
    NODE_LOCKED = "node_locked"


@dataclass
class PopulationTendency:
    """Population tendency data."""
    action: ActionType
    frequency: float  # 0.0 to 1.0
    sample_size: int
    confidence: float  # Statistical confidence in the tendency
    
    def is_significant(self, threshold: float = 0.7) -> bool:
        """Check if tendency is statistically significant."""
        return self.confidence >= threshold and self.sample_size >= 30


@dataclass
class OpponentModel:
    """Model of opponent's strategy deviations from GTO."""
    player_id: str
    tendencies: Dict[str, PopulationTendency] = field(default_factory=dict)
    overall_vpip: float = 0.25  # Voluntarily Put In Pot
    overall_pfr: float = 0.18   # Pre-Flop Raise
    aggression_factor: float = 1.0  # Ratio of bets/raises to calls
    sample_hands: int = 0
    
    def add_tendency(self, situation: str, tendency: PopulationTendency) -> None:
        """Add or update a tendency for a specific situation."""
        self.tendencies[situation] = tendency
    
    def get_tendency(self, situation: str) -> Optional[PopulationTendency]:
        """Get tendency for a situation if it exists."""
        return self.tendencies.get(situation)
    
    def is_tight(self) -> bool:
        """Check if opponent plays tight (VPIP < 20%)."""
        return self.overall_vpip < 0.20
    
    def is_aggressive(self) -> bool:
        """Check if opponent is aggressive (AF > 2.0)."""
        return self.aggression_factor > 2.0
    
    def get_style(self) -> str:
        """Get opponent playing style."""
        tight = self.is_tight()
        aggressive = self.is_aggressive()
        
        if tight and aggressive:
            return "TAG"  # Tight-Aggressive
        elif tight and not aggressive:
            return "Tight-Passive"
        elif not tight and aggressive:
            return "LAG"  # Loose-Aggressive
        else:
            return "Loose-Passive"


@dataclass
class Deviation:
    """A profitable deviation from GTO strategy."""
    situation: str
    gto_action: ActionType
    gto_frequency: float
    exploitative_action: ActionType
    exploitative_frequency: float
    ev_gain: float  # Expected value gain in big blinds
    confidence: float  # Confidence in the deviation (0-1)
    reasoning: str  # Explanation of why this deviation is profitable

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'situation': self.situation,
            'gto_action': self.gto_action.value,
            'gto_frequency': self.gto_frequency,
            'exploitative_action': self.exploitative_action.value,
            'exploitative_frequency': self.exploitative_frequency,
            'ev_gain': self.ev_gain,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


@dataclass
class PopulationProfile:
    """Population profile for GTO deviations."""
    name: str
    action_bias: Dict[str, float] = field(default_factory=dict)
    description: str = ""


@dataclass
class DeviationRequest:
    """Request for GTO deviation calculation."""
    node_id: str
    game_state: Dict[str, Any]
    baseline_strategy: Dict[str, float]
    action_evs: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_shift: float = 0.3
    population_profile: Optional[PopulationProfile] = None
    simplification_threshold: float = 0.01
    max_actions: Optional[int] = None


@dataclass
class DeviationResult:
    """Result of GTO deviation calculation."""
    deviation_strategy: Dict[str, float]
    ev_gain: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    exploitability: float = 0.0
    confidence: float = 1.0


class MaximumExploitationFinder:
    """Finds maximum exploitation strategies against specific opponents."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.MaximumExploitationFinder')
    
    def find_exploits(
        self,
        opponent: OpponentModel,
        situation: str,
        gto_strategy: Dict[ActionType, float]
    ) -> List[Deviation]:
        """
        Find profitable deviations from GTO for a given situation.
        
        Args:
            opponent: Opponent model with tendencies
            situation: Description of the poker situation
            gto_strategy: GTO frequencies for each action
            
        Returns:
            List of profitable deviations
        """
        deviations = []
        
        # Get opponent's tendency for this situation
        tendency = opponent.get_tendency(situation)
        
        if not tendency or not tendency.is_significant():
            self.logger.debug(f"No significant tendency for {situation}")
            return deviations
        
        # Calculate exploitation based on opponent's over/under-frequency
        for gto_action, gto_freq in gto_strategy.items():
            # Skip if GTO doesn't use this action much
            if gto_freq < 0.05:
                continue
            
            # Find counter-strategy
            exploit = self._find_counter_strategy(
                gto_action, gto_freq, tendency, opponent
            )
            
            if exploit and exploit.ev_gain > 0.1:  # Minimum 0.1 BB gain
                deviations.append(exploit)
        
        return sorted(deviations, key=lambda d: d.ev_gain, reverse=True)
    
    def _find_counter_strategy(
        self,
        gto_action: ActionType,
        gto_freq: float,
        tendency: PopulationTendency,
        opponent: OpponentModel
    ) -> Optional[Deviation]:
        """Find counter-strategy to opponent's tendency."""
        
        # If opponent over-folds, increase aggression
        if tendency.action == ActionType.FOLD and tendency.frequency > 0.6:
            ev_gain = self._calculate_fold_exploit_ev(tendency.frequency, gto_freq)
            return Deviation(
                situation="",
                gto_action=gto_action,
                gto_frequency=gto_freq,
                exploitative_action=ActionType.BET,
                exploitative_frequency=min(1.0, gto_freq * 1.5),
                ev_gain=ev_gain,
                confidence=tendency.confidence,
                reasoning=f"Opponent folds {tendency.frequency:.1%} - increase aggression"
            )
        
        # If opponent over-calls, decrease bluffs, increase value bets
        elif tendency.action == ActionType.CALL and tendency.frequency > 0.5:
            ev_gain = self._calculate_call_exploit_ev(tendency.frequency, gto_freq)
            return Deviation(
                situation="",
                gto_action=gto_action,
                gto_frequency=gto_freq,
                exploitative_action=ActionType.BET,
                exploitative_frequency=gto_freq * 0.8,  # Fewer bluffs
                ev_gain=ev_gain,
                confidence=tendency.confidence,
                reasoning=f"Opponent calls {tendency.frequency:.1%} - reduce bluffs, bet value hands"
            )
        
        # If opponent over-raises, increase calling range
        elif tendency.action == ActionType.RAISE and tendency.frequency > 0.3:
            ev_gain = self._calculate_raise_exploit_ev(tendency.frequency, gto_freq)
            return Deviation(
                situation="",
                gto_action=gto_action,
                gto_frequency=gto_freq,
                exploitative_action=ActionType.CALL,
                exploitative_frequency=min(1.0, gto_freq * 1.3),
                ev_gain=ev_gain,
                confidence=tendency.confidence,
                reasoning=f"Opponent raises {tendency.frequency:.1%} - widen calling range"
            )
        
        return None
    
    def _calculate_fold_exploit_ev(self, fold_freq: float, gto_freq: float) -> float:
        """Calculate EV gain from exploiting over-folding."""
        # Simple linear model: more folding = more EV from bluffs
        excess_folds = max(0, fold_freq - 0.5)
        return excess_folds * 2.0 * (1 - gto_freq)
    
    def _calculate_call_exploit_ev(self, call_freq: float, gto_freq: float) -> float:
        """Calculate EV gain from exploiting over-calling."""
        excess_calls = max(0, call_freq - 0.4)
        return excess_calls * 1.5 * gto_freq
    
    def _calculate_raise_exploit_ev(self, raise_freq: float, gto_freq: float) -> float:
        """Calculate EV gain from exploiting over-raising."""
        excess_raises = max(0, raise_freq - 0.25)
        return excess_raises * 1.8 * (1 - gto_freq)


class NodeLocker:
    """
    Implements node-locking strategies to simplify decision trees.
    
    Node-locking "locks" certain nodes in the game tree to specific actions,
    simplifying the strategy while maintaining exploitative power.
    """
    
    def __init__(self):
        self.locked_nodes: Dict[str, ActionType] = {}
        self.logger = logging.getLogger(__name__ + '.NodeLocker')
    
    def lock_node(self, node_id: str, action: ActionType, reason: str = "") -> None:
        """Lock a node to always take a specific action."""
        self.locked_nodes[node_id] = action
        self.logger.info(f"Locked node {node_id} to {action.value}: {reason}")
    
    def unlock_node(self, node_id: str) -> None:
        """Unlock a previously locked node."""
        if node_id in self.locked_nodes:
            del self.locked_nodes[node_id]
            self.logger.info(f"Unlocked node {node_id}")
    
    def is_locked(self, node_id: str) -> bool:
        """Check if a node is locked."""
        return node_id in self.locked_nodes
    
    def get_action(self, node_id: str) -> Optional[ActionType]:
        """Get the locked action for a node."""
        return self.locked_nodes.get(node_id)
    
    def apply_locking_strategy(
        self,
        opponent: OpponentModel,
        simplified_threshold: float = 0.15
    ) -> Dict[str, ActionType]:
        """
        Generate node-locking strategy based on opponent model.
        
        Locks nodes where opponent has strong tendencies, simplifying decisions.
        
        Args:
            opponent: Opponent model
            simplified_threshold: Lock nodes where action frequency < threshold
            
        Returns:
            Dictionary of node locks
        """
        locks = {}
        
        for situation, tendency in opponent.tendencies.items():
            if not tendency.is_significant():
                continue
            
            # Lock nodes where opponent rarely takes an action
            if tendency.frequency < simplified_threshold:
                # Opponent rarely takes this action, so we can simplify
                counter_action = self._get_counter_action(tendency.action)
                locks[situation] = counter_action
                self.logger.debug(
                    f"Locking {situation} to {counter_action.value} "
                    f"(opponent {tendency.action.value} only {tendency.frequency:.1%})"
                )
            
            # Lock nodes where opponent almost always takes an action
            elif tendency.frequency > 0.85:
                counter_action = self._get_counter_action(tendency.action)
                locks[situation] = counter_action
                self.logger.debug(
                    f"Locking {situation} to {counter_action.value} "
                    f"(opponent {tendency.action.value} {tendency.frequency:.1%})"
                )
        
        return locks
    
    def _get_counter_action(self, action: ActionType) -> ActionType:
        """Get the best counter-action to an opponent's action."""
        if action == ActionType.FOLD:
            return ActionType.BET  # Bet more if they fold often
        elif action == ActionType.CALL:
            return ActionType.BET  # Value bet if they call often
        elif action == ActionType.BET:
            return ActionType.CALL  # Call more if they bet often
        elif action == ActionType.RAISE:
            return ActionType.CALL  # Call more if they raise often
        else:  # CHECK
            return ActionType.BET  # Bet if they check often


class StrategySimplifier:
    """Simplifies complex GTO strategies while maintaining EV."""

    def __init__(self, ev_loss_tolerance: float = 0.05):
        """
        Initialize simplifier.

        Args:
            ev_loss_tolerance: Maximum EV loss (in BB) acceptable from simplification
        """
        self.ev_loss_tolerance = ev_loss_tolerance
        self.logger = logging.getLogger(__name__ + '.StrategySimplifier')

    @staticmethod
    def simplify(
        strategy: Dict[str, float],
        threshold: float = 0.10,
        max_actions: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Simplify a mixed strategy by removing low-frequency actions.

        Args:
            strategy: Original mixed strategy
            threshold: Minimum frequency to keep an action
            max_actions: Maximum number of actions to keep

        Returns:
            Simplified strategy with renormalized frequencies
        """
        # Filter out low-frequency actions
        simplified = {
            action: freq
            for action, freq in strategy.items()
            if freq >= threshold
        }

        if not simplified:
            # If all actions filtered out, keep the highest frequency one
            best_action = max(strategy.items(), key=lambda x: x[1])[0]
            return {best_action: 1.0}

        # Apply max_actions constraint if specified
        if max_actions is not None and len(simplified) > max_actions:
            # Keep only top N actions by frequency
            sorted_actions = sorted(simplified.items(), key=lambda x: x[1], reverse=True)
            simplified = dict(sorted_actions[:max_actions])

        # Renormalize frequencies
        total = sum(simplified.values())
        normalized = {
            action: freq / total
            for action, freq in simplified.items()
        }

        return normalized
    
    def merge_similar_actions(
        self,
        strategy: Dict[ActionType, float]
    ) -> Dict[ActionType, float]:
        """
        Merge similar actions to reduce complexity.
        
        For example, merge different bet sizes into a single bet action.
        """
        # Merge BET and RAISE into a single "aggressive" action
        merged = dict(strategy)
        
        if ActionType.BET in merged and ActionType.RAISE in merged:
            bet_freq = merged.get(ActionType.BET, 0)
            raise_freq = merged.get(ActionType.RAISE, 0)
            
            # Keep the more frequent action
            if bet_freq >= raise_freq:
                merged[ActionType.BET] = bet_freq + raise_freq
                del merged[ActionType.RAISE]
            else:
                merged[ActionType.RAISE] = bet_freq + raise_freq
                del merged[ActionType.BET]
        
        return merged


class DeviationEVCalculator:
    """Calculator for EV-related computations in GTO deviations."""

    @staticmethod
    def expected_value(strategy: Dict[str, float], action_evs: Dict[str, float]) -> float:
        """
        Calculate expected value of a strategy.

        Args:
            strategy: Strategy with action frequencies
            action_evs: EV for each action

        Returns:
            Expected value
        """
        ev = 0.0
        for action, frequency in strategy.items():
            ev += frequency * action_evs.get(action, 0.0)
        return ev

    @staticmethod
    def ev_gain(
        baseline: Dict[str, float],
        deviated: Dict[str, float],
        action_evs: Dict[str, float]
    ) -> float:
        """
        Calculate EV gain from deviation.

        Args:
            baseline: Baseline strategy
            deviated: Deviated strategy
            action_evs: EV for each action

        Returns:
            EV gain
        """
        baseline_ev = DeviationEVCalculator.expected_value(baseline, action_evs)
        deviated_ev = DeviationEVCalculator.expected_value(deviated, action_evs)
        return deviated_ev - baseline_ev


class GTODeviationEngine:
    """Engine for calculating GTO deviations with population profiles."""

    def __init__(self, solver_api: Optional[Any] = None):
        self.logger = logging.getLogger(__name__ + '.GTODeviationEngine')
        self._population_profiles: Dict[str, PopulationProfile] = {}
        self.solver_api = solver_api

    def register_population_profile(self, profile: PopulationProfile) -> None:
        """Register a population profile."""
        self._population_profiles[profile.name] = profile
        self.logger.info(f"Registered population profile: {profile.name}")

    def get_population_profile(self, name: str) -> Optional[PopulationProfile]:
        """Get a population profile by name."""
        return self._population_profiles.get(name)

    def _apply_population_profile(
        self,
        request: DeviationRequest,
        baseline: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply population profile bias to strategy.

        Args:
            request: Deviation request with metadata
            baseline: Baseline strategy

        Returns:
            Adjusted strategy
        """
        # Get profile from request or metadata
        profile = request.population_profile
        if profile is None and 'population_profile' in request.metadata:
            profile_name = request.metadata['population_profile']
            profile = self.get_population_profile(profile_name)

        if profile is None:
            return baseline.copy()

        # Apply action bias
        adjusted = baseline.copy()
        for action, bias in profile.action_bias.items():
            if action in adjusted:
                adjusted[action] = max(0.0, adjusted[action] + bias)

        # Renormalize
        return self._normalise(adjusted)

    @staticmethod
    def _normalise(strategy: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize a strategy so frequencies sum to 1.0.

        Args:
            strategy: Strategy to normalize

        Returns:
            Normalized strategy
        """
        total = sum(strategy.values())

        if total == 0:
            # Uniform distribution if all zero
            n = len(strategy)
            return {action: 1.0 / n for action in strategy.keys()}

        return {action: freq / total for action, freq in strategy.items()}

    @staticmethod
    def _estimate_exploitability(
        baseline: Dict[str, float],
        deviation: Dict[str, float]
    ) -> float:
        """
        Estimate exploitability as distance between strategies.

        Args:
            baseline: Baseline strategy
            deviation: Deviated strategy

        Returns:
            Exploitability score (0-1)
        """
        # Calculate L1 distance
        distance = 0.0
        all_actions = set(baseline.keys()) | set(deviation.keys())

        for action in all_actions:
            baseline_freq = baseline.get(action, 0.0)
            deviation_freq = deviation.get(action, 0.0)
            distance += abs(deviation_freq - baseline_freq)

        # Scale to [0, 1], half of L1 distance (since max L1 = 2)
        return min(1.0, distance / 2.0)

    def _max_exploitation(
        self,
        strategy: Dict[str, float],
        action_evs: Dict[str, float],
        max_shift: float = 0.3
    ) -> Dict[str, float]:
        """
        Apply maximum exploitation by shifting probability to best EV action.

        Args:
            strategy: Current strategy
            action_evs: EV for each action
            max_shift: Maximum probability shift allowed

        Returns:
            Exploited strategy
        """
        if max_shift == 0:
            return self._normalise(strategy)

        # Find best action by EV
        best_action = max(action_evs.items(), key=lambda x: x[1])[0]

        # Normalize baseline
        normalized = self._normalise(strategy)

        # Calculate how much we can shift
        available_shift = sum(
            freq for action, freq in normalized.items()
            if action != best_action
        )
        actual_shift = min(max_shift, available_shift)

        if actual_shift == 0:
            return normalized

        # Shift probability to best action
        deviated = {}
        shift_ratio = actual_shift / available_shift if available_shift > 0 else 0

        for action, freq in normalized.items():
            if action == best_action:
                deviated[action] = freq + actual_shift
            else:
                deviated[action] = freq * (1 - shift_ratio)

        return self._normalise(deviated)

    def compute_deviation(
        self,
        request: DeviationRequest
    ) -> DeviationResult:
        """
        Compute GTO deviation for a request.

        Args:
            request: Deviation request

        Returns:
            Deviation result
        """
        # Apply population profile if present
        adjusted_baseline = self._apply_population_profile(
            request,
            request.baseline_strategy
        )

        # Apply maximum exploitation
        deviation_strategy = self._max_exploitation(
            adjusted_baseline,
            request.action_evs,
            request.max_shift
        )

        # Apply simplification if requested
        if request.simplification_threshold > 0 or request.max_actions is not None:
            deviation_strategy = StrategySimplifier.simplify(
                deviation_strategy,
                threshold=request.simplification_threshold,
                max_actions=request.max_actions
            )

        # Calculate EV gain
        ev_gain = DeviationEVCalculator.ev_gain(
            request.baseline_strategy,
            deviation_strategy,
            request.action_evs
        )

        # Calculate exploitability
        exploitability = self._estimate_exploitability(
            request.baseline_strategy,
            deviation_strategy
        )

        # Calculate EVs for metadata
        ev_baseline = DeviationEVCalculator.expected_value(
            request.baseline_strategy,
            request.action_evs
        )
        ev_deviation = DeviationEVCalculator.expected_value(
            deviation_strategy,
            request.action_evs
        )

        metadata = {
            'ev_baseline': ev_baseline,
            'ev_deviation': ev_deviation,
            'node_id': request.node_id,
            **request.metadata
        }

        return DeviationResult(
            deviation_strategy=deviation_strategy,
            ev_gain=ev_gain,
            metadata=metadata,
            exploitability=exploitability
        )


class GTODeviationCalculator:
    """
    Main class for calculating profitable GTO deviations.
    
    Combines exploitation finding, node locking, and simplification.
    """
    
    def __init__(self):
        self.exploit_finder = MaximumExploitationFinder()
        self.node_locker = NodeLocker()
        self.simplifier = StrategySimplifier()
        self.logger = logging.getLogger(__name__ + '.GTODeviationCalculator')
    
    def calculate_deviations(
        self,
        opponent: OpponentModel,
        situation: str,
        gto_strategy: Dict[ActionType, float],
        simplify: bool = True
    ) -> Tuple[Dict[ActionType, float], List[Deviation]]:
        """
        Calculate optimal deviations from GTO for a situation.
        
        Args:
            opponent: Opponent model
            situation: Poker situation description
            gto_strategy: GTO mixed strategy
            simplify: Whether to simplify the strategy
            
        Returns:
            Tuple of (exploitative_strategy, list_of_deviations)
        """
        # Find exploitative deviations
        deviations = self.exploit_finder.find_exploits(
            opponent, situation, gto_strategy
        )
        
        if not deviations:
            self.logger.info(f"No profitable deviations found for {situation}")
            return gto_strategy, []
        
        # Build exploitative strategy from deviations
        exploitative_strategy = self._build_exploitative_strategy(
            gto_strategy, deviations
        )
        
        # Apply node locking if beneficial
        if self.node_locker.is_locked(situation):
            locked_action = self.node_locker.get_action(situation)
            exploitative_strategy = {locked_action: 1.0}
        
        # Simplify if requested
        if simplify:
            exploitative_strategy = self.simplifier.simplify(exploitative_strategy)
        
        return exploitative_strategy, deviations
    
    def _build_exploitative_strategy(
        self,
        gto_strategy: Dict[ActionType, float],
        deviations: List[Deviation]
    ) -> Dict[ActionType, float]:
        """Build exploitative mixed strategy from deviations."""
        strategy = dict(gto_strategy)
        
        # Apply highest EV deviation
        if deviations:
            best_deviation = deviations[0]
            
            # Shift frequency from GTO action to exploitative action
            shift = min(
                0.3,  # Max 30% frequency shift
                strategy.get(best_deviation.gto_action, 0) * 0.5
            )
            
            strategy[best_deviation.gto_action] = \
                strategy.get(best_deviation.gto_action, 0) - shift
            strategy[best_deviation.exploitative_action] = \
                strategy.get(best_deviation.exploitative_action, 0) + shift
            
            # Remove zero frequencies
            strategy = {a: f for a, f in strategy.items() if f > 0.01}
        
        # Renormalize
        total = sum(strategy.values())
        if total > 0:
            strategy = {a: f / total for a, f in strategy.items()}
        
        return strategy
    
    def calculate_exploitability(
        self,
        strategy: Dict[ActionType, float],
        opponent: OpponentModel
    ) -> float:
        """
        Calculate how exploitable a strategy is.
        
        Lower values indicate less exploitable strategies.
        
        Returns:
            Exploitability score in big blinds
        """
        # Simple model: strategies that deviate more from balanced are more exploitable
        # In real implementation, would use game tree analysis
        
        # Check if strategy is balanced (similar frequencies for value/bluff)
        bet_raise_freq = (
            strategy.get(ActionType.BET, 0) +
            strategy.get(ActionType.RAISE, 0)
        )
        
        call_freq = strategy.get(ActionType.CALL, 0)
        fold_freq = strategy.get(ActionType.FOLD, 0)
        
        # Balanced strategy has bet/call/fold in reasonable proportions
        balance_score = abs(bet_raise_freq - 0.4) + abs(call_freq - 0.3) + abs(fold_freq - 0.3)
        
        exploitability = balance_score * 2.0  # Scale to BB
        
        return exploitability
    
    def generate_report(
        self,
        opponent: OpponentModel,
        deviations: List[Deviation]
    ) -> Dict[str, Any]:
        """Generate a comprehensive deviation report."""
        return {
            'opponent_style': opponent.get_style(),
            'opponent_vpip': opponent.overall_vpip,
            'opponent_pfr': opponent.overall_pfr,
            'opponent_aggression': opponent.aggression_factor,
            'sample_size': opponent.sample_hands,
            'deviation_count': len(deviations),
            'total_ev_gain': sum(d.ev_gain for d in deviations),
            'top_deviations': [d.to_dict() for d in deviations[:5]],
            'average_confidence': (
                sum(d.confidence for d in deviations) / len(deviations)
                if deviations else 0.0
            )
        }


# Convenience functions

def create_opponent_model(
    player_id: str,
    vpip: float = 0.25,
    pfr: float = 0.18,
    aggression: float = 1.0
) -> OpponentModel:
    """Create a basic opponent model."""
    return OpponentModel(
        player_id=player_id,
        overall_vpip=vpip,
        overall_pfr=pfr,
        aggression_factor=aggression
    )


def find_deviations(
    opponent: OpponentModel,
    situation: str,
    gto_strategy: Dict[str, float]
) -> List[Deviation]:
    """
    Quick function to find profitable deviations.
    
    Args:
        opponent: Opponent model
        situation: Situation description
        gto_strategy: GTO strategy as dict with action strings as keys
        
    Returns:
        List of profitable deviations
    """
    # Convert string keys to ActionType
    gto_typed = {
        ActionType(action): freq
        for action, freq in gto_strategy.items()
    }
    
    calculator = GTODeviationCalculator()
    _, deviations = calculator.calculate_deviations(
        opponent, situation, gto_typed
    )
    
    return deviations


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("=== GTO Deviations Calculator ===\n")
    
    # Create opponent model (loose-passive fish)
    opponent = create_opponent_model(
        player_id="fish123",
        vpip=0.45,  # Plays 45% of hands
        pfr=0.08,   # Raises only 8% preflop
        aggression=0.5  # Very passive
    )
    
    # Add tendency: opponent over-folds to 3-bets
    opponent.add_tendency(
        "facing_3bet_preflop",
        PopulationTendency(
            action=ActionType.FOLD,
            frequency=0.75,  # Folds 75% to 3-bets
            sample_size=50,
            confidence=0.85
        )
    )
    
    # GTO strategy: balanced 3-bet range
    gto_strategy = {
        ActionType.FOLD: 0.6,
        ActionType.CALL: 0.2,
        ActionType.RAISE: 0.2
    }
    
    # Calculate deviations
    calculator = GTODeviationCalculator()
    exploit_strategy, deviations = calculator.calculate_deviations(
        opponent,
        "facing_3bet_preflop",
        gto_strategy,
        simplify=True
    )
    
    print(f"Opponent Style: {opponent.get_style()}")
    print(f"VPIP: {opponent.overall_vpip:.1%}")
    print(f"PFR: {opponent.overall_pfr:.1%}")
    print(f"Aggression: {opponent.aggression_factor:.2f}\n")
    
    print("GTO Strategy:")
    for action, freq in gto_strategy.items():
        print(f"  {action.value}: {freq:.1%}")
    
    print("\nExploitative Strategy:")
    for action, freq in exploit_strategy.items():
        print(f"  {action.value}: {freq:.1%}")
    
    print(f"\nFound {len(deviations)} profitable deviations:")
    for dev in deviations:
        print(f"\n  {dev.exploitative_action.value}: +{dev.ev_gain:.2f} BB")
        print(f"  Confidence: {dev.confidence:.1%}")
        print(f"  Reason: {dev.reasoning}")
    
    # Generate report
    report = calculator.generate_report(opponent, deviations)
    print("\n=== Deviation Report ===")
    print(json.dumps(report, indent=2))
