"""
Tests for Meta-Game Optimizer (META-001)

Tests leveling war simulation, dynamic strategy switching, exploitation/protection balance,
history-dependent strategies, and reputation modeling.
"""

import unittest
from src.pokertool.meta_game import (
    MetaGameOptimizer,
    LevelingWarSimulator,
    DynamicStrategySwitcher,
    ExploitationProtectionBalancer,
    HistoryDependentStrategy,
    ReputationModel,
    StrategyLevel,
    PlayerReputation,
    MetaGameState,
    StrategyAdjustment
)


class TestLevelingWarSimulator(unittest.TestCase):
    """Test leveling war simulation"""
    
    def setUp(self):
        self.simulator = LevelingWarSimulator()
    
    def test_initialization(self):
        """Test simulator initialization"""
        self.assertIsNotNone(self.simulator.level_matchups)
        self.assertGreater(len(self.simulator.level_matchups), 0)
    
    def test_simulate_matchup_level0_vs_level1(self):
        """Test level 0 vs level 1 matchup"""
        ev = self.simulator.simulate_matchup(StrategyLevel.LEVEL_0, StrategyLevel.LEVEL_1)
        self.assertLess(ev, 0)  # Level 1 should exploit level 0
    
    def test_simulate_matchup_level1_vs_level0(self):
        """Test level 1 vs level 0 matchup"""
        ev = self.simulator.simulate_matchup(StrategyLevel.LEVEL_1, StrategyLevel.LEVEL_0)
        self.assertGreater(ev, 0)  # Level 1 should profit against level 0
    
    def test_simulate_matchup_same_level(self):
        """Test same level matchup"""
        ev = self.simulator.simulate_matchup(StrategyLevel.LEVEL_1, StrategyLevel.LEVEL_1)
        self.assertEqual(ev, 0.0)  # Same level should be neutral
    
    def test_find_optimal_level_vs_level0(self):
        """Test finding optimal level vs level 0"""
        optimal = self.simulator.find_optimal_level(StrategyLevel.LEVEL_0)
        self.assertEqual(optimal, StrategyLevel.LEVEL_1)
    
    def test_find_optimal_level_vs_level2(self):
        """Test finding optimal level vs level 2"""
        optimal = self.simulator.find_optimal_level(StrategyLevel.LEVEL_2)
        self.assertEqual(optimal, StrategyLevel.LEVEL_3)
    
    def test_estimate_villain_level_fishy_stats(self):
        """Test level estimation for fishy player"""
        stats = {'vpip': 45, 'pfr': 10, 'aggression': 0.5, 'fold_to_3bet': 80}
        level = self.simulator.estimate_villain_level(stats)
        self.assertEqual(level, StrategyLevel.LEVEL_0)
    
    def test_estimate_villain_level_standard_stats(self):
        """Test level estimation for standard player"""
        stats = {'vpip': 25, 'pfr': 20, 'aggression': 1.3, 'fold_to_3bet': 75}
        level = self.simulator.estimate_villain_level(stats)
        self.assertEqual(level, StrategyLevel.LEVEL_1)
    
    def test_estimate_villain_level_thinking_player(self):
        """Test level estimation for thinking player"""
        stats = {'vpip': 24, 'pfr': 20, 'aggression': 2.0, 'fold_to_3bet': 65}
        level = self.simulator.estimate_villain_level(stats)
        self.assertEqual(level, StrategyLevel.LEVEL_2)
    
    def test_estimate_villain_level_advanced_player(self):
        """Test level estimation for advanced player"""
        stats = {'vpip': 26, 'pfr': 22, 'aggression': 3.0, 'fold_to_3bet': 60}
        level = self.simulator.estimate_villain_level(stats)
        self.assertEqual(level, StrategyLevel.LEVEL_3)


class TestDynamicStrategySwitcher(unittest.TestCase):
    """Test dynamic strategy switching"""
    
    def setUp(self):
        self.switcher = DynamicStrategySwitcher()
    
    def test_initialization(self):
        """Test switcher initialization"""
        self.assertEqual(len(self.switcher.strategy_history), 0)
        self.assertEqual(len(self.switcher.performance_by_strategy), 0)
    
    def test_select_strategy_no_history(self):
        """Test strategy selection with no history"""
        state = MetaGameState(
            hero_level=StrategyLevel.LEVEL_1,
            villain_level=StrategyLevel.LEVEL_1,
            exploitation_score=0.0,
            history_weight=0.5,
            reputation=PlayerReputation.BALANCED
        )
        strategy = self.switcher.select_strategy(state, ['balanced', 'aggressive', 'defensive'])
        self.assertEqual(strategy, 'balanced')
    
    def test_select_strategy_exploitative(self):
        """Test strategy selection in exploitation mode"""
        # Add some performance history first
        self.switcher.update_performance('exploit_passive', 10.0)
        
        state = MetaGameState(
            hero_level=StrategyLevel.LEVEL_2,
            villain_level=StrategyLevel.LEVEL_0,
            exploitation_score=0.7,
            history_weight=0.5,
            reputation=PlayerReputation.LOOSE_PASSIVE
        )
        strategy = self.switcher.select_strategy(state, ['balanced', 'exploit_passive', 'defensive'])
        self.assertIn('exploit', strategy)
    
    def test_select_strategy_defensive(self):
        """Test strategy selection in defensive mode"""
        # Add some performance history first
        self.switcher.update_performance('defensive', 5.0)
        
        state = MetaGameState(
            hero_level=StrategyLevel.LEVEL_1,
            villain_level=StrategyLevel.LEVEL_3,
            exploitation_score=-0.7,
            history_weight=0.5,
            reputation=PlayerReputation.TIGHT_AGGRESSIVE
        )
        strategy = self.switcher.select_strategy(state, ['balanced', 'aggressive', 'defensive'])
        self.assertEqual(strategy, 'defensive')
    
    def test_update_performance(self):
        """Test performance tracking update"""
        self.switcher.update_performance('balanced', 10.5)
        self.assertIn('balanced', self.switcher.performance_by_strategy)
        self.assertEqual(len(self.switcher.performance_by_strategy['balanced']), 1)
        self.assertEqual(len(self.switcher.strategy_history), 1)
    
    def test_get_best_performing_strategy(self):
        """Test getting best performing strategy"""
        self.switcher.update_performance('aggressive', 5.0)
        self.switcher.update_performance('aggressive', 15.0)
        self.switcher.update_performance('defensive', 8.0)
        self.switcher.update_performance('defensive', 7.0)
        
        best = self.switcher.get_best_performing_strategy()
        self.assertEqual(best, 'aggressive')
    
    def test_get_best_performing_strategy_no_history(self):
        """Test getting best strategy with no history"""
        best = self.switcher.get_best_performing_strategy()
        self.assertIsNone(best)


class TestExploitationProtectionBalancer(unittest.TestCase):
    """Test exploitation/protection balancing"""
    
    def setUp(self):
        self.balancer = ExploitationProtectionBalancer()
    
    def test_calculate_balance_high_opportunity(self):
        """Test balance calculation with high opportunity"""
        opportunities = [0.8, 0.7, 0.9]
        risks = [0.2, 0.3, 0.1]
        score = self.balancer.calculate_balance_score(opportunities, risks)
        self.assertGreater(score, 0.3)
    
    def test_calculate_balance_high_risk(self):
        """Test balance calculation with high risk"""
        opportunities = [0.2, 0.3, 0.1]
        risks = [0.8, 0.9, 0.7]
        score = self.balancer.calculate_balance_score(opportunities, risks)
        self.assertLess(score, -0.3)
    
    def test_calculate_balance_neutral(self):
        """Test balance calculation when neutral"""
        opportunities = [0.5, 0.5, 0.5]
        risks = [0.5, 0.5, 0.5]
        score = self.balancer.calculate_balance_score(opportunities, risks)
        self.assertAlmostEqual(score, 0.0, places=1)
    
    def test_calculate_balance_empty_lists(self):
        """Test balance calculation with empty lists"""
        score = self.balancer.calculate_balance_score([], [])
        self.assertEqual(score, 0.0)
    
    def test_recommend_adjustment_exploitation(self):
        """Test recommendation for exploitation"""
        adjustment = self.balancer.recommend_adjustment(0.7)
        self.assertEqual(adjustment.adjustment_type, 'increase_exploitation')
        self.assertGreater(adjustment.magnitude, 0.5)
        self.assertGreater(adjustment.expected_ev_gain, 0)
    
    def test_recommend_adjustment_protection(self):
        """Test recommendation for protection"""
        adjustment = self.balancer.recommend_adjustment(-0.7)
        self.assertEqual(adjustment.adjustment_type, 'increase_protection')
        self.assertGreater(adjustment.magnitude, 0.5)
        self.assertGreater(adjustment.expected_ev_gain, 0)
    
    def test_recommend_adjustment_balanced(self):
        """Test recommendation for balanced play"""
        adjustment = self.balancer.recommend_adjustment(0.2)
        self.assertEqual(adjustment.adjustment_type, 'maintain_balance')
        self.assertEqual(adjustment.magnitude, 0.0)
    
    def test_assess_vulnerability_high_fold_to_3bet(self):
        """Test vulnerability assessment with high fold to 3bet"""
        stats = {'fold_to_3bet': 80, 'cbet_frequency': 60, 'fold_to_cbet': 50}
        vulnerability = self.balancer.assess_vulnerability(stats)
        self.assertGreater(vulnerability, 0.5)
    
    def test_assess_vulnerability_low(self):
        """Test vulnerability assessment with low exploitability"""
        stats = {'fold_to_3bet': 50, 'cbet_frequency': 60, 'fold_to_cbet': 50}
        vulnerability = self.balancer.assess_vulnerability(stats)
        self.assertLess(vulnerability, 0.5)


class TestHistoryDependentStrategy(unittest.TestCase):
    """Test history-dependent strategy"""
    
    def setUp(self):
        self.strategy = HistoryDependentStrategy(memory_length=10)
    
    def test_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(len(self.strategy.interaction_history), 0)
        self.assertEqual(self.strategy.memory_length, 10)
    
    def test_record_interaction(self):
        """Test recording interaction"""
        self.strategy.record_interaction('player1', 'preflop_raise', 'call', 15.0)
        self.assertIn('player1', self.strategy.interaction_history)
        self.assertEqual(len(self.strategy.interaction_history['player1']), 1)
    
    def test_memory_length_limit(self):
        """Test memory length limiting"""
        for i in range(15):
            self.strategy.record_interaction('player1', f'situation_{i}', 'action', 10.0)
        
        self.assertEqual(len(self.strategy.interaction_history['player1']), 10)
    
    def test_get_situational_strategy_no_history(self):
        """Test getting strategy with no history"""
        result = self.strategy.get_situational_strategy('player1', 'preflop_raise')
        self.assertIsNone(result)
    
    def test_get_situational_strategy_with_history(self):
        """Test getting strategy with history"""
        self.strategy.record_interaction('player1', 'preflop_raise', 'fold', 5.0)
        self.strategy.record_interaction('player1', 'preflop_raise', 'call', 20.0)
        self.strategy.record_interaction('player1', 'preflop_raise', 'call', 25.0)
        
        result = self.strategy.get_situational_strategy('player1', 'preflop_raise')
        self.assertEqual(result, 'call')  # Call has better avg result
    
    def test_get_situational_strategy_no_match(self):
        """Test getting strategy with no matching situation"""
        self.strategy.record_interaction('player1', 'preflop_raise', 'fold', 5.0)
        result = self.strategy.get_situational_strategy('player1', 'postflop_bet')
        self.assertIsNone(result)


class TestReputationModel(unittest.TestCase):
    """Test reputation modeling"""
    
    def setUp(self):
        self.model = ReputationModel()
    
    def test_initialization(self):
        """Test model initialization"""
        self.assertEqual(len(self.model.reputations), 0)
        self.assertEqual(len(self.model.reputation_data), 0)
    
    def test_build_reputation_tight_passive(self):
        """Test building tight-passive reputation"""
        stats = {'vpip': 20, 'pfr': 15, 'aggression': 0.8}
        reputation = self.model.build_reputation('player1', stats)
        self.assertEqual(reputation, PlayerReputation.TIGHT_PASSIVE)
    
    def test_build_reputation_tight_aggressive(self):
        """Test building tight-aggressive reputation"""
        stats = {'vpip': 22, 'pfr': 18, 'aggression': 2.5}
        reputation = self.model.build_reputation('player2', stats)
        self.assertEqual(reputation, PlayerReputation.TIGHT_AGGRESSIVE)
    
    def test_build_reputation_loose_passive(self):
        """Test building loose-passive reputation"""
        stats = {'vpip': 35, 'pfr': 12, 'aggression': 0.9}
        reputation = self.model.build_reputation('player3', stats)
        self.assertEqual(reputation, PlayerReputation.LOOSE_PASSIVE)
    
    def test_build_reputation_loose_aggressive(self):
        """Test building loose-aggressive reputation"""
        stats = {'vpip': 32, 'pfr': 28, 'aggression': 2.8}
        reputation = self.model.build_reputation('player4', stats)
        self.assertEqual(reputation, PlayerReputation.LOOSE_AGGRESSIVE)
    
    def test_build_reputation_balanced(self):
        """Test building balanced reputation"""
        stats = {'vpip': 25, 'pfr': 20, 'aggression': 1.5}
        reputation = self.model.build_reputation('player5', stats)
        self.assertEqual(reputation, PlayerReputation.BALANCED)
    
    def test_get_reputation(self):
        """Test getting reputation"""
        stats = {'vpip': 25, 'pfr': 20, 'aggression': 1.5}
        self.model.build_reputation('player1', stats)
        reputation = self.model.get_reputation('player1')
        self.assertEqual(reputation, PlayerReputation.BALANCED)
    
    def test_get_reputation_unknown(self):
        """Test getting unknown reputation"""
        reputation = self.model.get_reputation('unknown_player')
        self.assertEqual(reputation, PlayerReputation.UNKNOWN)
    
    def test_get_exploitative_adjustments_tight_passive(self):
        """Test exploitative adjustments for tight-passive"""
        adjustments = self.model.get_exploitative_adjustments(PlayerReputation.TIGHT_PASSIVE)
        self.assertGreater(len(adjustments), 0)
        self.assertTrue(any('bluff' in adj.lower() for adj in adjustments))
    
    def test_get_exploitative_adjustments_loose_passive(self):
        """Test exploitative adjustments for loose-passive"""
        adjustments = self.model.get_exploitative_adjustments(PlayerReputation.LOOSE_PASSIVE)
        self.assertGreater(len(adjustments), 0)
        self.assertTrue(any('value' in adj.lower() for adj in adjustments))
    
    def test_get_exploitative_adjustments_balanced(self):
        """Test exploitative adjustments for balanced"""
        adjustments = self.model.get_exploitative_adjustments(PlayerReputation.BALANCED)
        self.assertGreater(len(adjustments), 0)
        self.assertTrue(any('gto' in adj.lower() for adj in adjustments))


class TestMetaGameOptimizer(unittest.TestCase):
    """Test meta-game optimizer"""
    
    def setUp(self):
        self.optimizer = MetaGameOptimizer()
    
    def test_initialization(self):
        """Test optimizer initialization"""
        self.assertIsNotNone(self.optimizer.leveling_simulator)
        self.assertIsNotNone(self.optimizer.strategy_switcher)
        self.assertIsNotNone(self.optimizer.balance_calculator)
        self.assertIsNotNone(self.optimizer.history_strategy)
        self.assertIsNotNone(self.optimizer.reputation_model)
    
    def test_optimize_strategy_tight_passive(self):
        """Test strategy optimization for tight-passive opponent"""
        context = {
            'opponent_id': 'player1',
            'opponent_stats': {
                'vpip': 18,
                'pfr': 12,
                'aggression': 0.7,
                'fold_to_3bet': 85,
                'cbet_frequency': 50,
                'fold_to_cbet': 70
            }
        }
        
        result = self.optimizer.optimize_strategy(context)
        
        self.assertIn('hero_level', result)
        self.assertIn('villain_level', result)
        self.assertIn('reputation', result)
        self.assertIn('exploitation_score', result)
        self.assertIn('adjustment', result)
        self.assertIn('specific_adjustments', result)
        
        # Should identify tight-passive
        self.assertEqual(result['reputation'], PlayerReputation.TIGHT_PASSIVE.value)
        
        # Should recommend exploitative adjustments
        self.assertGreater(len(result['specific_adjustments']), 0)
    
    def test_optimize_strategy_loose_aggressive(self):
        """Test strategy optimization for loose-aggressive opponent"""
        context = {
            'opponent_id': 'player2',
            'opponent_stats': {
                'vpip': 35,
                'pfr': 30,
                'aggression': 3.0,
                'fold_to_3bet': 45,
                'cbet_frequency': 80,
                'fold_to_cbet': 40
            }
        }
        
        result = self.optimizer.optimize_strategy(context)
        
        # Should identify loose-aggressive
        self.assertEqual(result['reputation'], PlayerReputation.LOOSE_AGGRESSIVE.value)
        
        # Should have valid adjustment
        self.assertIsNotNone(result['adjustment']['type'])
        self.assertGreaterEqual(result['adjustment']['confidence'], 0)
        self.assertLessEqual(result['adjustment']['confidence'], 1)
    
    def test_optimize_strategy_balanced_opponent(self):
        """Test strategy optimization for balanced opponent"""
        context = {
            'opponent_id': 'player3',
            'opponent_stats': {
                'vpip': 25,
                'pfr': 20,
                'aggression': 1.8,
                'fold_to_3bet': 60,
                'cbet_frequency': 65,
                'fold_to_cbet': 55
            }
        }
        
        result = self.optimizer.optimize_strategy(context)
        
        # Should identify balanced
        self.assertEqual(result['reputation'], PlayerReputation.BALANCED.value)
        
        # Exploitation score should be moderate
        self.assertLess(abs(result['exploitation_score']), 0.8)
    
    def test_export_analysis(self):
        """Test exporting meta-game analysis"""
        import tempfile
        import os
        import json
        
        # Optimize some strategies first
        for i in range(3):
            context = {
                'opponent_id': f'player{i}',
                'opponent_stats': {
                    'vpip': 25 + i * 5,
                    'pfr': 20 + i * 3,
                    'aggression': 1.5 + i * 0.5,
                    'fold_to_3bet': 60 - i * 5
                }
            }
            self.optimizer.optimize_strategy(context)
        
        # Export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            self.optimizer.export_analysis(filepath)
            
            # Verify file exists and is valid JSON
            self.assertTrue(os.path.exists(filepath))
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.assertIn('reputations', data)
            self.assertIn('reputation_data', data)
            self.assertIn('strategy_performance', data)
            
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)


if __name__ == '__main__':
    unittest.main()
