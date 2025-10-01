"""
Tests for Game Theory Optimal (GTO) deviation engine.

Covers:
- Population profile adjustments
- Maximum exploitation search and EV gain
- Node locking enforcement
- Strategy simplification
- Ensemble adapter integration
"""

import unittest
from typing import Dict, Any

from src.pokertool.gto_deviations import (
    PopulationProfile,
    DeviationAdjustment,
    DeviationRequest,
    DeviationResult,
    GTODeviationEngine,
    create_ensemble_engine,
)
from src.pokertool.node_locker import NodeLocker


class TestPopulationProfile(unittest.TestCase):
    """Test population profile adjustments."""

    def test_apply_bias(self):
        """Population bias shifts strategy and renormalises."""
        profile = PopulationProfile(
            name="loose-passive",
            action_bias={"call": 0.1, "fold": -0.1},
        )

        baseline = {"raise": 0.4, "call": 0.3, "fold": 0.3}
        adjusted = profile.apply(baseline)

        self.assertAlmostEqual(sum(adjusted.values()), 1.0, places=6)
        self.assertGreater(adjusted["call"], baseline["call"])
        self.assertLess(adjusted["fold"], baseline["fold"])


class TestNodeLockerIntegration(unittest.TestCase):
    """Test node locking behaviour."""

    def test_apply_node_lock(self):
        """Locked actions honour min/max bounds."""
        locker = NodeLocker()
        locker.lock_action("node1", "raise", min_frequency=0.5, max_frequency=0.6)

        strategy = {"raise": 0.2, "call": 0.5, "fold": 0.3}
        adjusted, locks = locker.apply("node1", strategy)

        self.assertAlmostEqual(sum(adjusted.values()), 1.0, places=6)
        self.assertGreaterEqual(adjusted["raise"], 0.5)
        self.assertLessEqual(adjusted["raise"], 0.6)
        self.assertIn("raise", locks)


class TestDeviationEngine(unittest.TestCase):
    """Test core deviation engine logic."""

    def setUp(self):
        self.locker = NodeLocker()
        self.engine = GTODeviationEngine(node_locker=self.locker)

        # Baseline scenario
        self.baseline = {"raise": 0.3, "call": 0.4, "fold": 0.3}
        self.action_evs = {"raise": 2.0, "call": 1.0, "fold": 0.0}

    def _build_request(self, **kwargs: Any) -> DeviationRequest:
        data = dict(
            node_id="river_node",
            game_state={"position": "BTN"},
            baseline_strategy=self.baseline,
            action_evs=self.action_evs,
        )
        data.update(kwargs)
        return DeviationRequest(**data)

    def test_compute_deviation_ev_gain(self):
        """Deviation increases EV when shifting mass to higher EV actions."""
        request = self._build_request(max_shift=0.2)
        result = self.engine.compute_deviation(request)

        self.assertIsInstance(result, DeviationResult)
        self.assertGreater(result.ev_gain, 0.0)
        self.assertAlmostEqual(sum(result.deviation_strategy.values()), 1.0, places=6)

        # Raise frequency should increase due to higher EV.
        self.assertGreater(result.deviation_strategy["raise"], self.baseline["raise"])

    def test_population_profile_applied(self):
        """Population profile biases initial target strategy."""
        profile = PopulationProfile(
            name="over-caller",
            action_bias={"call": 0.2, "fold": -0.2},
        )
        request = self._build_request(population_profile=profile, max_shift=0.1)
        result = self.engine.compute_deviation(request)

        self.assertGreater(result.deviation_strategy["call"], self.baseline["call"])
        self.assertLess(result.deviation_strategy["fold"], self.baseline["fold"])

    def test_node_lock_respected(self):
        """Locked frequencies are enforced in deviation output."""
        self.locker.lock_action("river_node", "raise", 0.5, 0.6)

        request = self._build_request(max_shift=0.4)
        result = self.engine.compute_deviation(request)

        self.assertGreaterEqual(result.deviation_strategy["raise"], 0.5)
        self.assertLessEqual(result.deviation_strategy["raise"], 0.6)
        self.assertIn("raise", result.locked_actions)

    def test_simplification_threshold(self):
        """Low-probability actions get pruned."""
        request = self._build_request(max_shift=0.05, simplification_threshold=0.25)
        result = self.engine.compute_deviation(request)

        # Actions below threshold should be removed.
        for action, freq in result.deviation_strategy.items():
            self.assertGreaterEqual(freq, 0.25)

        self.assertLessEqual(len(result.deviation_strategy), 3)

    def test_adjustments_sorted(self):
        """Adjustments are sorted by delta descending."""
        request = self._build_request(max_shift=0.2)
        result = self.engine.compute_deviation(request)

        deltas = [adj.delta for adj in result.adjustments]
        self.assertEqual(deltas, sorted(deltas, reverse=True))


class TestEnsembleAdapter(unittest.TestCase):
    """Test ensemble integration helper."""

    def test_create_ensemble_engine(self):
        """Ensemble adapter returns EngineDecision with deviation reasoning."""
        engine = GTODeviationEngine()

        def ev_provider(game_state: Dict[str, Any]) -> Dict[str, float]:
            return {"raise": 1.5, "call": 0.8, "fold": 0.1}

        ensemble_engine = create_ensemble_engine(
            deviation_engine=engine,
            node_id="flop_node",
            action_evs_provider=ev_provider,
        )

        game_state = {
            "position": "CO",
            "baseline_strategy": {"raise": 0.25, "call": 0.5, "fold": 0.25},
        }

        from src.pokertool.ensemble_decision import DecisionType

        decision = ensemble_engine(game_state, DecisionType.ACTION)

        self.assertEqual(decision.engine_name, "gto_deviation")
        self.assertEqual(decision.decision_type, DecisionType.ACTION)
        self.assertIn(decision.value, {"raise", "call", "fold"})
        self.assertIn("strategy", decision.metadata)
        self.assertIn("ev_gain", decision.metadata)
        self.assertGreaterEqual(decision.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()
