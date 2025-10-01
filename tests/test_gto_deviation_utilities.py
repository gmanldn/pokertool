import unittest

from src.pokertool.gto_deviations import (
    PopulationProfile,
    StrategySimplifier,
    DeviationEVCalculator,
    GTODeviationEngine,
    DeviationRequest,
)


class TestStrategySimplifier(unittest.TestCase):
    """Unit tests for strategy simplification helper."""

    def test_uniform_distribution_when_all_pruned(self):
        """When every action falls below the threshold, best action becomes deterministic."""
        strategy = {"raise": 0.1, "call": 0.1, "fold": 0.1}
        simplified = StrategySimplifier.simplify(strategy, threshold=0.5)

        self.assertEqual(set(simplified.keys()), {"raise"})
        self.assertAlmostEqual(simplified["raise"], 1.0, places=6)

    def test_respects_max_actions_constraint(self):
        """Simplifier keeps only the top-N actions and re-normalises."""
        strategy = {"raise": 0.6, "call": 0.25, "fold": 0.15}
        simplified = StrategySimplifier.simplify(strategy, threshold=0.0, max_actions=2)

        self.assertEqual(set(simplified.keys()), {"raise", "call"})
        self.assertAlmostEqual(sum(simplified.values()), 1.0, places=6)
        self.assertGreater(simplified["raise"], simplified["call"])


class TestDeviationEVCalculator(unittest.TestCase):
    """Unit tests for EV calculation helpers."""

    def test_expected_value_and_gain(self):
        """Expected value and EV gain calculations match manual computation."""
        baseline = {"raise": 0.5, "fold": 0.5}
        deviated = {"raise": 0.8, "fold": 0.2}
        action_evs = {"raise": 2.0, "fold": 0.0}

        baseline_ev = DeviationEVCalculator.expected_value(baseline, action_evs)
        deviated_ev = DeviationEVCalculator.expected_value(deviated, action_evs)
        gain = DeviationEVCalculator.ev_gain(baseline, deviated, action_evs)

        self.assertAlmostEqual(baseline_ev, 1.0)
        self.assertAlmostEqual(deviated_ev, 1.6)
        self.assertAlmostEqual(gain, 0.6)


class TestPopulationProfileLookup(unittest.TestCase):
    """Ensure population profiles can be resolved from request metadata."""

    def test_profile_resolved_from_metadata(self):
        """Engine finds registered profile when only metadata specifies it."""
        engine = GTODeviationEngine()
        profile = PopulationProfile(
            name="aggro",
            action_bias={"raise": 0.2, "fold": -0.2},
        )
        engine.register_population_profile(profile)

        baseline = {"raise": 0.3, "call": 0.4, "fold": 0.3}
        request = DeviationRequest(
            node_id="river_node",
            game_state={"position": "BTN"},
            baseline_strategy=baseline,
            action_evs={"raise": 1.5, "call": 0.9, "fold": 0.2},
            metadata={"population_profile": "aggro"},
        )

        adjusted = engine._apply_population_profile(request, baseline)

        self.assertGreater(adjusted["raise"], baseline["raise"])
        self.assertLess(adjusted["fold"], baseline["fold"])
        self.assertAlmostEqual(sum(adjusted.values()), 1.0, places=6)


class TestExploitabilityEstimator(unittest.TestCase):
    """Unit tests for exploitability estimation helper."""

    def test_zero_for_identical_strategies(self):
        """Exploitability score is zero when strategies are identical."""
        baseline = {"raise": 0.5, "call": 0.5}
        deviation = {"raise": 0.5, "call": 0.5}

        score = GTODeviationEngine._estimate_exploitability(baseline, deviation)
        self.assertEqual(score, 0.0)

    def test_scaled_distance_capped_at_one(self):
        """Exploitability score respects the [0, 1] cap."""
        baseline = {"raise": 1.0, "call": 0.0}
        deviation = {"raise": 0.0, "call": 1.0}

        score = GTODeviationEngine._estimate_exploitability(baseline, deviation)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestNormalizationUtilities(unittest.TestCase):
    """Tests for strategy normalisation behaviour."""

    def test_normalise_handles_zero_total(self):
        """Normalisation falls back to uniform distribution when sum is zero."""
        strategy = {"raise": 0.0, "call": 0.0, "fold": 0.0}
        normalised = GTODeviationEngine._normalise(strategy)

        self.assertEqual(set(normalised.keys()), set(strategy.keys()))
        self.assertTrue(all(freq == 1 / 3 for freq in normalised.values()))
        self.assertAlmostEqual(sum(normalised.values()), 1.0, places=6)

    def test_normalise_preserves_relative_ratios(self):
        """Normalisation rescales positive entries but preserves ratios."""
        strategy = {"raise": 2.0, "call": 1.0, "fold": 1.0}
        normalised = GTODeviationEngine._normalise(strategy)

        self.assertAlmostEqual(normalised["raise"], 0.5)
        self.assertAlmostEqual(normalised["call"], 0.25)
        self.assertAlmostEqual(normalised["fold"], 0.25)


class TestMaxExploitation(unittest.TestCase):
    """Unit tests for maximum exploitation heuristic."""

    def setUp(self):
        self.engine = GTODeviationEngine()
        self.action_evs = {"raise": 3.0, "call": 1.5, "fold": 0.1}
        self.strategy = {"raise": 0.4, "call": 0.35, "fold": 0.25}

    def test_no_shift_returns_normalised_strategy(self):
        """Zero max_shift should return the original normalised strategy."""
        deviated = self.engine._max_exploitation(
            self.strategy,
            self.action_evs,
            max_shift=0.0,
        )
        self.assertEqual(deviated, GTODeviationEngine._normalise(self.strategy))

    def test_shift_does_not_exceed_budget(self):
        """Total probability moved to best action does not exceed max_shift."""
        max_shift = 0.1
        deviated = self.engine._max_exploitation(
            self.strategy,
            self.action_evs,
            max_shift=max_shift,
        )

        delta_raise = deviated["raise"] - GTODeviationEngine._normalise(self.strategy)["raise"]
        self.assertGreater(delta_raise, 0.0)
        self.assertLessEqual(delta_raise, max_shift + 1e-9)
        self.assertAlmostEqual(sum(deviated.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
