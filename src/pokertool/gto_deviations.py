"""
Game Theory Optimal (GTO) deviation engine.

Provides tooling for analysing profitable deviations from equilibrium
strategies, including maximum exploitation search, population tendency
integration, node locking, strategy simplification, and EV gain
measurement.

ID: GTO-DEV-001
Status: INTEGRATED
Priority: MEDIUM
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Callable

try:
    from src.pokertool.node_locker import NodeLocker, NodeLock
except ImportError:  # pragma: no cover - fallback for relative imports during packaging
    from .node_locker import NodeLocker, NodeLock  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PopulationProfile:
    """
    Describes population tendencies that can be exploited.

    The `action_bias` mapping introduces additive deltas (positive or negative)
    to action frequencies before re-normalisation.
    """
    name: str
    action_bias: Dict[str, float]
    aggression_factor: float = 0.0
    passivity_factor: float = 0.0

    def apply(self, strategy: Dict[str, float]) -> Dict[str, float]:
        """Apply population bias to a strategy."""
        adjusted = {action: max(0.0, freq + self.action_bias.get(action, 0.0))
                    for action, freq in strategy.items()}
        total = sum(adjusted.values())
        if total <= 0.0:
            # Fall back to uniform distribution if everything cancels out.
            equal = 1.0 / max(len(strategy), 1)
            return {action: equal for action in strategy}
        return {action: freq / total for action, freq in adjusted.items()}


@dataclass(frozen=True)
class DeviationAdjustment:
    """Represents the delta applied to an action when deviating."""
    action: str
    baseline_frequency: float
    deviation_frequency: float
    ev_contribution: float

    @property
    def delta(self) -> float:
        return self.deviation_frequency - self.baseline_frequency


@dataclass(frozen=True)
class DeviationRequest:
    """
    Input payload for a deviation computation.

    Attributes:
        node_id: Unique identifier for the decision node.
        game_state: Arbitrary state blob passed to solver/engines.
        baseline_strategy: Equilibrium or current strategy to deviate from.
        action_evs: Expected value for each action (same keys as strategies).
        population_profile: Optional profile to bias deviations.
        simplification_threshold: Minimum probability retained after simplification.
        max_actions: Optional cap on number of actions kept after simplification.
        max_shift: Maximum total probability mass allowed to shift away from baseline.
    """
    node_id: str
    game_state: Dict[str, Any]
    baseline_strategy: Dict[str, float]
    action_evs: Dict[str, float]
    population_profile: Optional[PopulationProfile] = None
    simplification_threshold: float = 0.01
    max_actions: Optional[int] = 3
    max_shift: float = 0.40
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeviationResult:
    """Outcome of a deviation computation."""
    node_id: str
    baseline_strategy: Dict[str, float]
    deviation_strategy: Dict[str, float]
    adjustments: List[DeviationAdjustment]
    ev_gain: float
    exploitability_score: float
    locked_actions: Dict[str, NodeLock]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the result."""
        return {
            "node_id": self.node_id,
            "baseline_strategy": self.baseline_strategy,
            "deviation_strategy": self.deviation_strategy,
            "ev_gain": self.ev_gain,
            "exploitability_score": self.exploitability_score,
            "locked_actions": {
                action: lock.to_dict() for action, lock in self.locked_actions.items()
            },
            "adjustments": [
                {
                    "action": adj.action,
                    "baseline_frequency": adj.baseline_frequency,
                    "deviation_frequency": adj.deviation_frequency,
                    "delta": adj.delta,
                    "ev_contribution": adj.ev_contribution,
                }
                for adj in self.adjustments
            ],
            "metadata": self.metadata,
        }


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #


class StrategySimplifier:
    """Utility for pruning low-probability actions while maintaining normalisation."""

    @staticmethod
    def simplify(
        strategy: Dict[str, float],
        threshold: float = 0.01,
        max_actions: Optional[int] = None,
    ) -> Dict[str, float]:
        """Remove very small probabilities and optionally cap action count."""
        filtered = {a: f for a, f in strategy.items() if f >= threshold}
        if not filtered:
            # Keep the single best action if everything was below the threshold.
            best_action = max(strategy.items(), key=lambda item: item[1])[0]
            filtered = {best_action: 1.0}

        if max_actions is not None and len(filtered) > max_actions:
            # Keep top-N actions by probability mass.
            sorted_actions = sorted(filtered.items(), key=lambda item: item[1], reverse=True)
            filtered = dict(sorted_actions[:max_actions])

        total = sum(filtered.values())
        return {action: freq / total for action, freq in filtered.items()}


class DeviationEVCalculator:
    """Computes EV differences between strategies."""

    @staticmethod
    def expected_value(strategy: Dict[str, float], action_evs: Dict[str, float]) -> float:
        """Return sum(strategy[action] * ev[action])."""
        return sum(strategy.get(action, 0.0) * action_evs.get(action, 0.0)
                   for action in action_evs.keys())

    @classmethod
    def ev_gain(cls,
                baseline: Dict[str, float],
                deviated: Dict[str, float],
                action_evs: Dict[str, float]) -> float:
        """Compute EV gain from deviating strategy."""
        return cls.expected_value(deviated, action_evs) - cls.expected_value(baseline, action_evs)


# --------------------------------------------------------------------------- #
# Core engine
# --------------------------------------------------------------------------- #


class GTODeviationEngine:
    """Main orchestrator for deviation analysis."""

    def __init__(
        self,
        solver_api: Optional[Any] = None,
        node_locker: Optional[NodeLocker] = None,
    ) -> None:
        self.solver_api = solver_api
        self.node_locker = node_locker or NodeLocker()
        self._population_profiles: Dict[str, PopulationProfile] = {}

    # -- population -------------------------------------------------------- #

    def register_population_profile(self, profile: PopulationProfile) -> None:
        """Add or replace a population profile."""
        self._population_profiles[profile.name] = profile

    def get_population_profile(self, name: str) -> Optional[PopulationProfile]:
        """Retrieve registered population profile."""
        return self._population_profiles.get(name)

    # -- main entry -------------------------------------------------------- #

    def compute_deviation(self, request: DeviationRequest) -> DeviationResult:
        """Compute the most profitable deviation subject to constraints."""
        baseline = self._normalise(request.baseline_strategy)
        action_evs = request.action_evs

        # Step 1: Seed target with population adjustments if provided.
        target = self._apply_population_profile(request, baseline)

        # Step 2: Run maximum exploitation search by shifting probability mass.
        exploited = self._max_exploitation(target, action_evs, request.max_shift)

        # Step 3: Apply node locks.
        adjusted, locks = self.node_locker.apply(request.node_id, exploited)

        # Step 4: Simplify resulting strategy.
        simplified = StrategySimplifier.simplify(
            adjusted,
            threshold=request.simplification_threshold,
            max_actions=request.max_actions,
        )
        # Ensure original action support is preserved for downstream consumers.
        expanded_strategy: Dict[str, float] = dict(simplified)
        for action in baseline.keys():
            expanded_strategy.setdefault(action, 0.0)

        # Step 5: Calculate EV gain and exploitability.
        ev_gain = DeviationEVCalculator.ev_gain(baseline, expanded_strategy, action_evs)
        exploitability = self._estimate_exploitability(baseline, expanded_strategy)

        adjustments = self._build_adjustments(
            baseline, expanded_strategy, action_evs
        )

        metadata = dict(request.metadata)
        metadata.update({
            "population_profile": request.population_profile.name
            if request.population_profile else None,
            "ev_baseline": DeviationEVCalculator.expected_value(baseline, action_evs),
            "ev_deviation": DeviationEVCalculator.expected_value(expanded_strategy, action_evs),
            "baseline_entropy": self._entropy(baseline),
            "deviation_entropy": self._entropy(expanded_strategy),
        })

        return DeviationResult(
            node_id=request.node_id,
            baseline_strategy=baseline,
            deviation_strategy=expanded_strategy,
            adjustments=adjustments,
            ev_gain=ev_gain,
            exploitability_score=exploitability,
            locked_actions={action: lock for action, lock in locks.items()},
            metadata=metadata,
        )

    # -- helpers ----------------------------------------------------------- #

    def _apply_population_profile(
        self,
        request: DeviationRequest,
        strategy: Dict[str, float],
    ) -> Dict[str, float]:
        profile = request.population_profile
        if profile is None and request.metadata.get("population_profile"):
            profile = self.get_population_profile(request.metadata["population_profile"])

        if profile is None:
            return strategy

        return profile.apply(strategy)

    @staticmethod
    def _normalise(strategy: Dict[str, float]) -> Dict[str, float]:
        total = sum(strategy.values())
        if total <= 0.0:
            equal = 1.0 / max(len(strategy), 1)
            return {action: equal for action in strategy}
        return {action: max(0.0, freq / total) for action, freq in strategy.items()}

    def _max_exploitation(
        self,
        strategy: Dict[str, float],
        action_evs: Dict[str, float],
        max_shift: float,
    ) -> Dict[str, float]:
        """
        Shift probability mass towards higher EV actions while respecting the max_shift.

        A simple heuristic is used: move weight from lowest EV actions towards the highest
        EV actions proportionally to their EV advantage, capped by max_shift.
        """
        if max_shift <= 0.0:
            return strategy

        ev_pairs = [(action, action_evs.get(action, 0.0)) for action in strategy]
        ev_sorted = sorted(ev_pairs, key=lambda item: item[1], reverse=True)

        if not ev_sorted:
            return strategy

        best_action = ev_sorted[0][0]
        worst_action = ev_sorted[-1][0]

        if best_action == worst_action:
            return strategy

        deviation = strategy.copy()
        shift_available = min(max_shift, strategy.get(worst_action, 0.0))

        # Shift from worst to best.
        deviation[worst_action] = max(0.0, deviation[worst_action] - shift_available)
        deviation[best_action] = deviation.get(best_action, 0.0) + shift_available

        # Additional proportional redistribution based on EV advantage.
        total_advantage = sum(
            max(0.0, ev - action_evs.get(worst_action, 0.0))
            for _, ev in ev_sorted
        )
        if total_advantage > 0:
            remaining_shift = max_shift - shift_available
            for action, ev in ev_sorted[1:]:
                advantage = max(0.0, ev - action_evs.get(worst_action, 0.0))
                if advantage <= 0 or remaining_shift <= 0:
                    continue
                delta = remaining_shift * (advantage / total_advantage)
                available_pool = sum(
                    deviation[a] for a, e in ev_sorted if e <= ev and a != action
                )
                delta = min(delta, available_pool)
                deviation[action] = deviation.get(action, 0.0) + delta
                for pool_action, pool_ev in ev_sorted[::-1]:
                    if pool_action == action:
                        continue
                    reducible = min(deviation[pool_action], delta)
                    deviation[pool_action] -= reducible
                    delta -= reducible
                    if delta <= 1e-9:
                        break
                remaining_shift -= max(0.0, remaining_shift * (advantage / total_advantage))

        return self._normalise(deviation)

    @staticmethod
    def _entropy(strategy: Dict[str, float]) -> float:
        """Shannon entropy for informational comparison."""
        entropy = 0.0
        for freq in strategy.values():
            if freq > 0:
                entropy -= freq * math.log(freq, 2)
        return entropy

    @staticmethod
    def _estimate_exploitability(
        baseline: Dict[str, float],
        deviation: Dict[str, float],
    ) -> float:
        """
        Estimate exploitability via L2 distance scaled to [0, 1].

        The further the deviation is from the baseline, the higher the exploitability risk.
        """
        actions = set(baseline.keys()) | set(deviation.keys())
        squared = sum(
            (baseline.get(action, 0.0) - deviation.get(action, 0.0)) ** 2
            for action in actions
        )
        distance = math.sqrt(squared)
        return min(1.0, distance * math.sqrt(len(actions)))

    @staticmethod
    def _build_adjustments(
        baseline: Dict[str, float],
        deviation: Dict[str, float],
        action_evs: Dict[str, float],
    ) -> List[DeviationAdjustment]:
        adjustments: List[DeviationAdjustment] = []
        for action in set(baseline.keys()) | set(deviation.keys()):
            baseline_freq = baseline.get(action, 0.0)
            deviation_freq = deviation.get(action, 0.0)
            ev = action_evs.get(action, 0.0)
            adjustments.append(
                DeviationAdjustment(
                    action=action,
                    baseline_frequency=baseline_freq,
                    deviation_frequency=deviation_freq,
                    ev_contribution=ev * (deviation_freq - baseline_freq),
                )
            )
        adjustments.sort(key=lambda adj: adj.delta, reverse=True)
        return adjustments


# --------------------------------------------------------------------------- #
# Ensemble helpers
# --------------------------------------------------------------------------- #


def create_ensemble_engine(
    deviation_engine: GTODeviationEngine,
    node_id: str,
    action_evs_provider: Callable[[Dict[str, Any]], Dict[str, float]],
    population_profile: Optional[PopulationProfile] = None,
    decision_type: Any = None,
) -> Callable[[Dict[str, Any], Any], Any]:
    """
    Create an ensemble-compatible engine function.

    Args:
        deviation_engine: Configured GTODeviationEngine instance.
        node_id: Identifier for the node we are locking/analysing.
        action_evs_provider: Function mapping `game_state -> action EVs`.
        population_profile: Optional fixed profile.
        decision_type: Desired decision type (defaults to ACTION).

    Returns:
        Callable suitable for `EnsembleDecisionSystem.register_engine`.
    """
    from src.pokertool.ensemble_decision import EngineDecision, DecisionType  # local import

    decision_type = decision_type or DecisionType.ACTION

    def engine(game_state: Dict[str, Any], requested_type: Any) -> EngineDecision:
        if requested_type != decision_type:
            raise ValueError(
                f"GTO deviation engine only supports decision type {decision_type}"
            )

        baseline = game_state.get("baseline_strategy")
        if not baseline:
            raise ValueError("game_state missing 'baseline_strategy' for deviation analysis")

        action_evs = action_evs_provider(game_state)

        request = DeviationRequest(
            node_id=node_id,
            game_state=game_state,
            baseline_strategy=baseline,
            action_evs=action_evs,
            population_profile=population_profile,
            metadata={"source": "ensemble_adapter"},
        )

        result = deviation_engine.compute_deviation(request)

        if decision_type == DecisionType.ACTION:
            best_action = max(
                result.deviation_strategy.items(),
                key=lambda item: item[1],
            )[0]
            value = best_action
        else:
            value = result.deviation_strategy

        reasoning = (
            f"Deviation EV gain: {result.ev_gain:.3f}, "
            f"exploitability: {result.exploitability_score:.3f}"
        )

        confidence = max(0.0, min(1.0, 0.5 + result.ev_gain))

        metadata = {
            "strategy": result.deviation_strategy,
            "baseline": result.baseline_strategy,
            "ev_gain": result.ev_gain,
            "exploitability": result.exploitability_score,
            "adjustments": [asdict(adj) | {"delta": adj.delta} for adj in result.adjustments],
        }

        return EngineDecision(
            engine_name="gto_deviation",
            decision_type=decision_type,
            value=value,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata,
        )

    return engine
