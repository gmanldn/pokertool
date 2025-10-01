"""
Tests for Bayesian Opponent Profiler Module

This module tests the Bayesian inference system for opponent tendency prediction,
including prior distribution models, belief updating, uncertainty quantification,
action prediction, and convergence guarantees.

Author: PokerTool Development Team
Date: 2025-01-10
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.pokertool.bayesian_profiler import (
    ActionPredictor,
    BayesianOpponentProfiler,
    BeliefUpdater,
    BetaDistribution,
    GaussianDistribution,
    PlayerProfile,
    PlayerStyle,
    PlayerTendency,
)


class TestBetaDistribution(unittest.TestCase):
    """Test Beta distribution for binary outcomes"""
    
    def test_initialization(self):
        """Test distribution initialization"""
        dist = BetaDistribution()
        self.assertEqual(dist.alpha, 1.0)
        self.assertEqual(dist.beta, 1.0)
        self.assertEqual(dist.mean(), 0.5)
    
    def test_update_success(self):
        """Test updating with success"""
        dist = BetaDistribution()
        dist.update(True)
        self.assertEqual(dist.alpha, 2.0)
        self.assertEqual(dist.beta, 1.0)
        self.assertGreater(dist.mean(), 0.5)
    
    def test_update_failure(self):
        """Test updating with failure"""
        dist = BetaDistribution()
        dist.update(False)
        self.assertEqual(dist.alpha, 1.0)
        self.assertEqual(dist.beta, 2.0)
        self.assertLess(dist.mean(), 0.5)
    
    def test_variance_calculation(self):
        """Test variance calculation"""
        dist = BetaDistribution(alpha=10, beta=10)
        variance = dist.variance()
        self.assertGreater(variance, 0)
        self.assertLess(variance, 0.25)
    
    def test_confidence_interval(self):
        """Test confidence interval calculation"""
        dist = BetaDistribution(alpha=50, beta=50)
        ci_low, ci_high = dist.confidence_interval()
        self.assertLess(ci_low, 0.5)
        self.assertGreater(ci_high, 0.5)
        self.assertGreater(ci_high - ci_low, 0)
    
    def test_sample_size(self):
        """Test effective sample size"""
        dist = BetaDistribution(alpha=10, beta=20)
        self.assertEqual(dist.sample_size(), 28)


class TestGaussianDistribution(unittest.TestCase):
    """Test Gaussian distribution for continuous values"""
    
    def test_initialization(self):
        """Test distribution initialization"""
        dist = GaussianDistribution(mu=5.0, tau=0.1)
        self.assertEqual(dist.mean(), 5.0)
        self.assertEqual(dist.n_obs, 0)
    
    def test_update(self):
        """Test distribution update"""
        dist = GaussianDistribution()
        dist.update(10.0)
        self.assertGreater(dist.n_obs, 0)
        self.assertNotEqual(dist.mean(), 0.0)
    
    def test_multiple_updates(self):
        """Test multiple updates converge to mean"""
        dist = GaussianDistribution()
        values = [5.0, 5.0, 5.0, 5.0, 5.0]
        for val in values:
            dist.update(val)
        self.assertAlmostEqual(dist.mean(), 5.0, places=1)
    
    def test_variance(self):
        """Test variance calculation"""
        dist = GaussianDistribution(tau=0.1)
        variance = dist.variance()
        self.assertGreater(variance, 0)


class TestPlayerProfile(unittest.TestCase):
    """Test Player Profile creation and management"""
    
    def test_profile_creation(self):
        """Test basic profile creation"""
        profile = PlayerProfile(player_id="player123")
        self.assertEqual(profile.player_id, "player123")
        self.assertEqual(profile.style, PlayerStyle.UNKNOWN)
        self.assertEqual(profile.hands_observed, 0)
    
    def test_tendencies_initialized(self):
        """Test all tendencies are initialized"""
        profile = PlayerProfile(player_id="player123")
        self.assertEqual(len(profile.tendencies), len(PlayerTendency))
        for tendency in PlayerTendency:
            self.assertIn(tendency, profile.tendencies)
    
    def test_continuous_stats_initialized(self):
        """Test continuous stats are initialized"""
        profile = PlayerProfile(player_id="player123")
        expected_stats = ["avg_bet_size", "avg_raise_size", "vpip", "pfr", "aggression_factor"]
        for stat in expected_stats:
            self.assertIn(stat, profile.continuous_stats)


class TestBeliefUpdater(unittest.TestCase):
    """Test belief updating system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.updater = BeliefUpdater()
        self.profile = PlayerProfile(player_id="test_player")
    
    def test_update_tendency(self):
        """Test tendency update"""
        initial_alpha = self.profile.tendencies[PlayerTendency.PREFLOP_RAISE].alpha
        self.updater.update_tendency(
            self.profile,
            PlayerTendency.PREFLOP_RAISE,
            True
        )
        final_alpha = self.profile.tendencies[PlayerTendency.PREFLOP_RAISE].alpha
        self.assertEqual(final_alpha, initial_alpha + 1)
    
    def test_update_continuous_stat(self):
        """Test continuous stat update"""
        initial_obs = self.profile.continuous_stats["vpip"].n_obs
        self.updater.update_continuous_stat(self.profile, "vpip", 0.3)
        final_obs = self.profile.continuous_stats["vpip"].n_obs
        self.assertEqual(final_obs, initial_obs + 1)
    
    def test_convergence_check(self):
        """Test convergence detection"""
        dist = BetaDistribution(alpha=1, beta=1)
        self.assertFalse(self.updater.has_converged(dist))
        
        # Simulate many observations
        for _ in range(100):
            dist.update(True)
        self.assertTrue(self.updater.has_converged(dist))
    
    def test_reliability_score(self):
        """Test reliability score calculation"""
        # New profile should have low reliability
        score = self.updater.get_reliability_score(self.profile)
        self.assertLess(score, 0.5)
        
        # Increase observations
        self.profile.hands_observed = 100
        for tendency in self.profile.tendencies.values():
            for _ in range(60):
                tendency.update(True)
        
        score = self.updater.get_reliability_score(self.profile)
        self.assertGreater(score, 0.5)


class TestActionPredictor(unittest.TestCase):
    """Test action prediction system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = ActionPredictor()
        self.profile = PlayerProfile(player_id="test_player")
    
    def test_predict_action_probability(self):
        """Test action probability prediction"""
        prob, uncertainty = self.predictor.predict_action_probability(
            self.profile,
            PlayerTendency.PREFLOP_RAISE
        )
        self.assertGreaterEqual(prob, 0)
        self.assertLessEqual(prob, 1)
        self.assertGreaterEqual(uncertainty, 0)
    
    def test_context_adjustment_stack_size(self):
        """Test context-based adjustments for stack size"""
        context = {"stack_size": 15}  # Short stack
        prob, _ = self.predictor.predict_action_probability(
            self.profile,
            PlayerTendency.PREFLOP_RAISE,
            context
        )
        # Should increase aggression with short stack
        self.assertGreater(prob, 0.4)
    
    def test_context_adjustment_position(self):
        """Test context-based adjustments for position"""
        context = {"position": "button"}
        prob, _ = self.predictor.predict_action_probability(
            self.profile,
            PlayerTendency.PREFLOP_RAISE,
            context
        )
        # Should increase raising range on button
        self.assertGreater(prob, 0.4)
    
    def test_predict_best_action(self):
        """Test best action prediction"""
        available_actions = ["fold", "call", "raise"]
        action, confidence = self.predictor.predict_best_action(
            self.profile,
            available_actions
        )
        self.assertIn(action, available_actions)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
    
    def test_predict_with_trained_profile(self):
        """Test prediction with trained profile"""
        # Train profile to be aggressive
        for _ in range(50):
            self.profile.tendencies[PlayerTendency.POSTFLOP_RAISE].update(True)
        
        available_actions = ["fold", "call", "raise"]
        action, confidence = self.predictor.predict_best_action(
            self.profile,
            available_actions
        )
        # Should prefer raise with aggressive profile
        self.assertEqual(action, "raise")


class TestBayesianOpponentProfiler(unittest.TestCase):
    """Test main Bayesian profiler system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.profiler = BayesianOpponentProfiler(data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_profile(self):
        """Test profile retrieval"""
        profile = self.profiler.get_profile("player1")
        self.assertEqual(profile.player_id, "player1")
        self.assertIn("player1", self.profiler.profiles)
    
    def test_observe_action_preflop_raise(self):
        """Test observing preflop raise"""
        initial_hands = self.profiler.get_profile("player1").hands_observed
        self.profiler.observe_action("player1", "preflop_raise")
        profile = self.profiler.get_profile("player1")
        self.assertEqual(profile.hands_observed, initial_hands + 1)
        self.assertGreater(
            profile.tendencies[PlayerTendency.PREFLOP_RAISE].alpha,
            1.0
        )
    
    def test_observe_action_with_details(self):
        """Test observing action with betting details"""
        self.profiler.observe_action(
            "player1",
            "postflop_raise",
            details={"raise_size": 3.5}
        )
        profile = self.profiler.get_profile("player1")
        self.assertGreater(profile.continuous_stats["avg_raise_size"].n_obs, 0)
    
    def test_player_style_classification(self):
        """Test player style classification"""
        profile = self.profiler.get_profile("player1")
        profile.hands_observed = 30
        
        # Simulate tight-aggressive profile
        profile.continuous_stats["vpip"].update(0.20)
        profile.continuous_stats["pfr"].update(0.15)
        profile.continuous_stats["aggression_factor"].update(2.5)
        
        self.profiler._update_player_style(profile)
        self.assertEqual(profile.style, PlayerStyle.TIGHT_AGGRESSIVE)
    
    def test_player_style_loose_passive(self):
        """Test loose-passive classification"""
        profile = self.profiler.get_profile("player2")
        profile.hands_observed = 30
        
        # Simulate loose-passive profile
        profile.continuous_stats["vpip"].update(0.40)
        profile.continuous_stats["pfr"].update(0.10)
        profile.continuous_stats["aggression_factor"].update(1.0)
        
        self.profiler._update_player_style(profile)
        self.assertEqual(profile.style, PlayerStyle.LOOSE_PASSIVE)
    
    def test_predict_action(self):
        """Test action prediction"""
        available_actions = ["fold", "call", "raise"]
        action, confidence = self.profiler.predict_action(
            "player1",
            available_actions
        )
        self.assertIn(action, available_actions)
        self.assertIsInstance(confidence, float)
    
    def test_get_exploitation_strategy(self):
        """Test exploitation strategy generation"""
        # Train profile with specific tendencies
        profile = self.profiler.get_profile("player1")
        profile.hands_observed = 100
        
        # Make player fold too much
        for _ in range(80):
            profile.tendencies[PlayerTendency.POSTFLOP_FOLD].update(True)
        
        strategy = self.profiler.get_exploitation_strategy("player1")
        self.assertIn("reliability", strategy)
        self.assertIn("recommendations", strategy)
        self.assertGreater(len(strategy["recommendations"]), 0)
    
    def test_get_uncertainty_quantification(self):
        """Test uncertainty quantification"""
        metrics = self.profiler.get_uncertainty_quantification(
            "player1",
            PlayerTendency.PREFLOP_RAISE
        )
        self.assertIn("mean", metrics)
        self.assertIn("std", metrics)
        self.assertIn("confidence_interval_low", metrics)
        self.assertIn("confidence_interval_high", metrics)
        self.assertIn("sample_size", metrics)
        self.assertIn("converged", metrics)
    
    def test_export_profile(self):
        """Test profile export"""
        # Add some data
        self.profiler.observe_action("player1", "preflop_raise")
        self.profiler.observe_action("player1", "three_bet")
        
        exported = self.profiler.export_profile("player1")
        self.assertEqual(exported["player_id"], "player1")
        self.assertIn("tendencies", exported)
        self.assertIn("continuous_stats", exported)
        self.assertIn("style", exported)
    
    def test_save_and_load_profiles(self):
        """Test profile persistence"""
        # Create and save profile
        self.profiler.observe_action("player1", "preflop_raise")
        self.profiler.observe_action("player1", "three_bet")
        self.profiler.save_profiles()
        
        # Create new profiler and load profiles
        new_profiler = BayesianOpponentProfiler(data_dir=self.temp_dir)
        profile = new_profiler.get_profile("player1")
        
        self.assertGreater(profile.hands_observed, 0)
        self.assertGreater(
            profile.tendencies[PlayerTendency.PREFLOP_RAISE].alpha,
            1.0
        )
    
    def test_convergence_guarantee(self):
        """Test that beliefs converge with sufficient data"""
        player_id = "converge_test"
        profile = self.profiler.get_profile(player_id)
        
        # Simulate 100 observations with 70% raise frequency
        for i in range(100):
            if i < 70:
                self.profiler.observe_action(player_id, "preflop_raise")
                # Also manually update to ensure we track both success and failure
                profile.tendencies[PlayerTendency.PREFLOP_RAISE].update(True)
            else:
                self.profiler.observe_action(player_id, "preflop_fold")
                # When folding, they didn't raise
                profile.tendencies[PlayerTendency.PREFLOP_RAISE].update(False)
        
        raise_dist = profile.tendencies[PlayerTendency.PREFLOP_RAISE]
        
        # Check convergence
        self.assertTrue(self.profiler.belief_updater.has_converged(raise_dist))
        
        # Check mean is close to true frequency (70 successes + 1 initial / 100 failures + 1 initial)
        self.assertAlmostEqual(raise_dist.mean(), 0.7, delta=0.15)
    
    def test_exploitation_recommendations_calling_station(self):
        """Test recommendations for calling station"""
        profile = self.profiler.get_profile("calling_station")
        profile.hands_observed = 100
        
        # Make player call too much
        for _ in range(70):
            profile.tendencies[PlayerTendency.POSTFLOP_CALL].update(True)
        
        strategy = self.profiler.get_exploitation_strategy("calling_station")
        recommendations_text = " ".join(strategy["recommendations"])
        self.assertIn("calling station", recommendations_text.lower())
    
    def test_multiple_players(self):
        """Test managing multiple player profiles"""
        players = ["player1", "player2", "player3"]
        
        for player in players:
            self.profiler.observe_action(player, "preflop_raise")
        
        self.assertEqual(len(self.profiler.profiles), 3)
        for player in players:
            self.assertIn(player, self.profiler.profiles)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.profiler = BayesianOpponentProfiler(data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_profiling_workflow(self):
        """Test complete profiling workflow"""
        player_id = "test_player"
        
        # Simulate a session of hands
        actions = [
            ("preflop_raise", {"raise_size": 2.5}),
            ("cbet", {"bet_size": 0.6}),
            ("postflop_raise", {"raise_size": 3.0}),
            ("three_bet", {"raise_size": 8.0}),
            ("preflop_raise", {"raise_size": 2.5}),
            ("cbet", {"bet_size": 0.7}),
            ("postflop_fold", None),
            ("preflop_raise", {"raise_size": 2.5}),
        ]
        
        for action_type, details in actions:
            self.profiler.observe_action(player_id, action_type, details)
        
        # Check profile was built
        profile = self.profiler.get_profile(player_id)
        self.assertEqual(profile.hands_observed, len(actions))
        
        # Get exploitation strategy
        strategy = self.profiler.get_exploitation_strategy(player_id)
        self.assertIn("reliability", strategy)
        self.assertGreater(strategy["reliability"], 0)
        
        # Predict action
        action, confidence = self.profiler.predict_action(
            player_id,
            ["fold", "call", "raise"],
            context={"position": "button"}
        )
        self.assertIn(action, ["fold", "call", "raise"])
        
        # Save and reload
        self.profiler.save_profiles()
        new_profiler = BayesianOpponentProfiler(data_dir=self.temp_dir)
        reloaded_profile = new_profiler.get_profile(player_id)
        self.assertEqual(reloaded_profile.hands_observed, len(actions))


if __name__ == "__main__":
    unittest.main()
