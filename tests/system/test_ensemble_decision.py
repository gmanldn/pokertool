"""
Tests for Ensemble Decision System

Tests weighted voting, confidence-based weighting, disagreement resolution,
adaptive weights, and performance tracking.
"""

import unittest
from src.pokertool.ensemble_decision import (
    EnsembleDecisionSystem,
    EngineDecision,
    DecisionType,
    WeightOptimizer,
    DisagreementResolver,
    PerformanceTracker,
    create_ensemble
)


class TestEngineDecision(unittest.TestCase):
    """Test EngineDecision functionality."""
    
    def test_decision_creation(self):
        """Test creating an engine decision."""
        decision = EngineDecision(
            engine_name='test_engine',
            decision_type=DecisionType.ACTION,
            value='raise',
            confidence=0.8
        )
        
        self.assertEqual(decision.engine_name, 'test_engine')
        self.assertEqual(decision.decision_type, DecisionType.ACTION)
        self.assertEqual(decision.value, 'raise')
        self.assertEqual(decision.confidence, 0.8)
    
    def test_to_dict(self):
        """Test converting decision to dictionary."""
        decision = EngineDecision(
            engine_name='test_engine',
            decision_type=DecisionType.ACTION,
            value='raise',
            confidence=0.8,
            reasoning='Strong hand'
        )
        
        d = decision.to_dict()
        
        self.assertEqual(d['engine_name'], 'test_engine')
        self.assertEqual(d['decision_type'], 'action')
        self.assertEqual(d['value'], 'raise')
        self.assertEqual(d['confidence'], 0.8)


class TestWeightOptimizer(unittest.TestCase):
    """Test WeightOptimizer functionality."""
    
    def setUp(self):
        """Set up test optimizer."""
        self.optimizer = WeightOptimizer(learning_rate=0.1)
    
    def test_initialize_weights(self):
        """Test weight initialization."""
        engines = ['engine1', 'engine2', 'engine3']
        self.optimizer.initialize_weights(engines)
        
        weights = self.optimizer.get_all_weights()
        
        self.assertEqual(len(weights), 3)
        # Weights should sum to 1.0
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        # Each weight should be equal
        self.assertAlmostEqual(weights['engine1'], 1.0/3.0, places=6)
    
    def test_get_weight(self):
        """Test getting individual weight."""
        engines = ['engine1', 'engine2']
        self.optimizer.initialize_weights(engines)
        
        weight = self.optimizer.get_weight('engine1')
        
        self.assertAlmostEqual(weight, 0.5, places=6)
    
    def test_update_weight(self):
        """Test updating weights."""
        engines = ['engine1', 'engine2']
        self.optimizer.initialize_weights(engines)
        
        initial_weight = self.optimizer.get_weight('engine1')
        
        # Update with good performance
        self.optimizer.update_weight('engine1', 0.9)
        
        updated_weight = self.optimizer.get_weight('engine1')
        
        # Weight should increase
        self.assertGreater(updated_weight, initial_weight)
        
        # Weights should still sum to 1.0
        weights = self.optimizer.get_all_weights()
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
    
    def test_performance_stats(self):
        """Test getting performance statistics."""
        engines = ['engine1']
        self.optimizer.initialize_weights(engines)
        
        self.optimizer.update_weight('engine1', 0.8)
        self.optimizer.update_weight('engine1', 0.9)
        
        stats = self.optimizer.get_performance_stats('engine1')
        
        self.assertIn('average', stats)
        self.assertIn('recent_average', stats)
        self.assertIn('sample_count', stats)
        self.assertEqual(stats['sample_count'], 2)
        self.assertAlmostEqual(stats['average'], 0.85, places=2)


class TestDisagreementResolver(unittest.TestCase):
    """Test DisagreementResolver functionality."""
    
    def setUp(self):
        """Set up test resolver."""
        self.resolver = DisagreementResolver()
    
    def test_calculate_disagreement_agreement(self):
        """Test disagreement calculation when all agree."""
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8),
            EngineDecision('engine2', DecisionType.ACTION, 'raise', 0.7),
            EngineDecision('engine3', DecisionType.ACTION, 'raise', 0.9)
        ]
        
        disagreement = self.resolver.calculate_disagreement(decisions)
        
        # All agree, so disagreement should be 0
        self.assertEqual(disagreement, 0.0)
    
    def test_calculate_disagreement_full(self):
        """Test disagreement calculation when all disagree."""
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8),
            EngineDecision('engine2', DecisionType.ACTION, 'call', 0.7),
            EngineDecision('engine3', DecisionType.ACTION, 'fold', 0.9)
        ]
        
        disagreement = self.resolver.calculate_disagreement(decisions)
        
        # All disagree, so disagreement should be 1.0
        self.assertEqual(disagreement, 1.0)
    
    def test_resolve_by_confidence(self):
        """Test resolution by highest confidence."""
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8),
            EngineDecision('engine2', DecisionType.ACTION, 'call', 0.9),
            EngineDecision('engine3', DecisionType.ACTION, 'fold', 0.7)
        ]
        
        value, confidence = self.resolver.resolve(decisions, 'highest_confidence')
        
        # Should choose 'call' (highest confidence)
        self.assertEqual(value, 'call')
        self.assertEqual(confidence, 0.9)
    
    def test_resolve_by_weighted_vote(self):
        """Test resolution by weighted voting."""
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8),
            EngineDecision('engine2', DecisionType.ACTION, 'raise', 0.7),
            EngineDecision('engine3', DecisionType.ACTION, 'call', 0.6)
        ]
        
        weights = {'engine1': 0.5, 'engine2': 0.3, 'engine3': 0.2}
        value, confidence = self.resolver.resolve(decisions, 'weighted_vote', weights)
        
        # Should choose 'raise' (more weighted votes)
        self.assertEqual(value, 'raise')
        self.assertGreater(confidence, 0.5)
    
    def test_resolve_by_majority(self):
        """Test resolution by majority vote."""
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8),
            EngineDecision('engine2', DecisionType.ACTION, 'raise', 0.7),
            EngineDecision('engine3', DecisionType.ACTION, 'call', 0.9)
        ]
        
        value, confidence = self.resolver.resolve(decisions, 'majority_vote')
        
        # Should choose 'raise' (2 out of 3)
        self.assertEqual(value, 'raise')
        self.assertAlmostEqual(confidence, 2.0/3.0, places=2)
    
    def test_resolve_numeric_by_average(self):
        """Test resolution of numeric values by average."""
        decisions = [
            EngineDecision('engine1', DecisionType.BET_SIZE, 50, 0.8),
            EngineDecision('engine2', DecisionType.BET_SIZE, 60, 0.7),
            EngineDecision('engine3', DecisionType.BET_SIZE, 70, 0.9)
        ]
        
        value, confidence = self.resolver.resolve(decisions, 'average')
        
        # Should be weighted average
        self.assertGreater(value, 50)
        self.assertLess(value, 70)
        self.assertGreater(confidence, 0)


class TestPerformanceTracker(unittest.TestCase):
    """Test PerformanceTracker functionality."""
    
    def setUp(self):
        """Set up test tracker."""
        self.tracker = PerformanceTracker()
    
    def test_record_result(self):
        """Test recording results."""
        from src.pokertool.ensemble_decision import EnsembleDecision
        
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8)
        ]
        
        ensemble_decision = EnsembleDecision(
            decision_type=DecisionType.ACTION,
            value='raise',
            confidence=0.8,
            contributing_engines=['engine1'],
            disagreement_level=0.0,
            method='weighted_vote',
            individual_decisions=decisions,
            metadata={}
        )
        
        self.tracker.record_result(ensemble_decision)
        
        stats = self.tracker.get_ensemble_stats()
        
        self.assertEqual(stats['total_decisions'], 1)
    
    def test_get_ensemble_stats(self):
        """Test getting ensemble statistics."""
        from src.pokertool.ensemble_decision import EnsembleDecision
        
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8)
        ]
        
        ensemble_decision = EnsembleDecision(
            decision_type=DecisionType.ACTION,
            value='raise',
            confidence=0.8,
            contributing_engines=['engine1'],
            disagreement_level=0.2,
            method='weighted_vote',
            individual_decisions=decisions,
            metadata={}
        )
        
        self.tracker.record_result(ensemble_decision)
        self.tracker.record_result(ensemble_decision)
        
        stats = self.tracker.get_ensemble_stats()
        
        self.assertEqual(stats['total_decisions'], 2)
        self.assertAlmostEqual(stats['average_confidence'], 0.8, places=2)
        self.assertAlmostEqual(stats['average_disagreement'], 0.2, places=2)
    
    def test_get_engine_stats(self):
        """Test getting engine-specific statistics."""
        from src.pokertool.ensemble_decision import EnsembleDecision
        
        decisions = [
            EngineDecision('engine1', DecisionType.ACTION, 'raise', 0.8)
        ]
        
        ensemble_decision = EnsembleDecision(
            decision_type=DecisionType.ACTION,
            value='raise',
            confidence=0.8,
            contributing_engines=['engine1'],
            disagreement_level=0.0,
            method='weighted_vote',
            individual_decisions=decisions,
            metadata={}
        )
        
        self.tracker.record_result(ensemble_decision)
        
        stats = self.tracker.get_engine_stats('engine1')
        
        self.assertEqual(stats['total_decisions'], 1)
        self.assertAlmostEqual(stats['average_confidence'], 0.8, places=2)


class TestEnsembleDecisionSystem(unittest.TestCase):
    """Test EnsembleDecisionSystem functionality."""
    
    def setUp(self):
        """Set up test ensemble."""
        self.ensemble = EnsembleDecisionSystem(learning_rate=0.1)
        
        # Register test engines
        def engine1(game_state, decision_type):
            return EngineDecision('engine1', decision_type, 'raise', 0.8)
        
        def engine2(game_state, decision_type):
            return EngineDecision('engine2', decision_type, 'call', 0.7)
        
        self.ensemble.register_engine('engine1', engine1)
        self.ensemble.register_engine('engine2', engine2)
    
    def test_register_engine(self):
        """Test registering engines."""
        def engine3(game_state, decision_type):
            return EngineDecision('engine3', decision_type, 'fold', 0.6)
        
        self.ensemble.register_engine('engine3', engine3)
        
        self.assertIn('engine3', self.ensemble.engines)
        weights = self.ensemble.get_engine_weights()
        self.assertIn('engine3', weights)
    
    def test_unregister_engine(self):
        """Test unregistering engines."""
        self.ensemble.unregister_engine('engine1')
        
        self.assertNotIn('engine1', self.ensemble.engines)
        weights = self.ensemble.get_engine_weights()
        self.assertNotIn('engine1', weights)
    
    def test_make_decision(self):
        """Test making an ensemble decision."""
        game_state = {'position': 'BTN', 'stack': 100}
        
        decision = self.ensemble.make_decision(
            game_state,
            DecisionType.ACTION
        )
        
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision_type, DecisionType.ACTION)
        self.assertGreater(decision.confidence, 0)
        self.assertEqual(len(decision.contributing_engines), 2)
    
    def test_make_decision_with_method(self):
        """Test making decision with specific method."""
        game_state = {'position': 'BTN'}
        
        decision = self.ensemble.make_decision(
            game_state,
            DecisionType.ACTION,
            method='highest_confidence'
        )
        
        self.assertEqual(decision.method, 'highest_confidence')
        self.assertEqual(decision.value, 'raise')  # engine1 has higher confidence
    
    def test_make_decision_min_confidence(self):
        """Test filtering by minimum confidence."""
        game_state = {'position': 'BTN'}
        
        decision = self.ensemble.make_decision(
            game_state,
            DecisionType.ACTION,
            min_confidence=0.75
        )
        
        # Only engine1 (0.8) should participate
        self.assertEqual(len(decision.contributing_engines), 1)
        self.assertIn('engine1', decision.contributing_engines)
    
    def test_update_performance(self):
        """Test updating engine performance."""
        initial_weight = self.ensemble.get_engine_weights()['engine1']
        
        # Update with good performance
        self.ensemble.update_performance('engine1', 0.9)
        
        updated_weight = self.ensemble.get_engine_weights()['engine1']
        
        # Weight should increase
        self.assertGreater(updated_weight, initial_weight)
    
    def test_get_stats(self):
        """Test getting comprehensive statistics."""
        game_state = {'position': 'BTN'}
        self.ensemble.make_decision(game_state, DecisionType.ACTION)
        
        stats = self.ensemble.get_stats()
        
        self.assertIn('performance', stats)
        self.assertIn('weights', stats)
        self.assertIn('engine_performance', stats)
    
    def test_set_engine_weight(self):
        """Test manually setting engine weight."""
        self.ensemble.set_engine_weight('engine1', 0.7)
        
        weight = self.ensemble.get_engine_weights()['engine1']
        
        # Weight should be set (and normalized)
        self.assertGreater(weight, 0)
        
        # All weights should sum to 1.0
        weights = self.ensemble.get_engine_weights()
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
    
    def test_set_default_method(self):
        """Test setting default resolution method."""
        self.ensemble.set_default_method('highest_confidence')
        
        self.assertEqual(self.ensemble.default_method, 'highest_confidence')
    
    def test_export_import_state(self):
        """Test exporting and importing system state."""
        # Make some decisions to build history
        game_state = {'position': 'BTN'}
        self.ensemble.make_decision(game_state, DecisionType.ACTION)
        self.ensemble.update_performance('engine1', 0.9)
        
        # Export state
        state = self.ensemble.export_state()
        
        self.assertIn('weights', state)
        self.assertIn('performance_history', state)
        self.assertIn('default_method', state)
        
        # Create new ensemble and import state
        new_ensemble = EnsembleDecisionSystem()
        new_ensemble.import_state(state)
        
        # Weights should match
        self.assertEqual(
            new_ensemble.weight_optimizer.engine_weights,
            self.ensemble.weight_optimizer.engine_weights
        )


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def test_create_ensemble(self):
        """Test creating ensemble with convenience function."""
        def engine1(game_state, decision_type):
            return EngineDecision('engine1', decision_type, 'raise', 0.8)
        
        def engine2(game_state, decision_type):
            return EngineDecision('engine2', decision_type, 'call', 0.7)
        
        configs = [
            {'name': 'engine1', 'function': engine1},
            {'name': 'engine2', 'function': engine2}
        ]
        
        ensemble = create_ensemble(configs, learning_rate=0.2)
        
        self.assertIsInstance(ensemble, EnsembleDecisionSystem)
        self.assertEqual(len(ensemble.engines), 2)
        self.assertIn('engine1', ensemble.engines)
        self.assertIn('engine2', ensemble.engines)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_no_engines_registered(self):
        """Test making decision with no engines."""
        ensemble = EnsembleDecisionSystem()
        
        with self.assertRaises(ValueError):
            ensemble.make_decision({}, DecisionType.ACTION)
    
    def test_all_engines_fail(self):
        """Test when all engines fail."""
        ensemble = EnsembleDecisionSystem()
        
        def failing_engine(game_state, decision_type):
            raise Exception("Engine failure")
        
        ensemble.register_engine('failing', failing_engine)
        
        with self.assertRaises(ValueError):
            ensemble.make_decision({}, DecisionType.ACTION)
    
    def test_single_engine(self):
        """Test with only one engine."""
        ensemble = EnsembleDecisionSystem()
        
        def engine1(game_state, decision_type):
            return EngineDecision('engine1', decision_type, 'raise', 0.8)
        
        ensemble.register_engine('engine1', engine1)
        
        decision = ensemble.make_decision({}, DecisionType.ACTION)
        
        self.assertEqual(decision.value, 'raise')
        self.assertEqual(decision.confidence, 0.8)
        self.assertEqual(decision.disagreement_level, 0.0)


if __name__ == '__main__':
    unittest.main()
