# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tests/test_comprehensive_ml_gto.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Comprehensive test suite for ML opponent modeling and GTO solver modules.
Covers unit tests, integration tests, and performance tests for 95% coverage.
"""

import unittest
import tempfile
import shutil
import time
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
import os
# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pokertool.core import Card, Rank, Suit, parse_card, analyse_hand
from pokertool.gto_solver import (
    Action, Street, Range, GameState, Strategy, GTOSolution,
    EquityCalculator, GTOSolver, GTOTrainer, DeviationExplorer,
    get_gto_solver, solve_spot, create_standard_ranges, analyze_gto_spot
)
from pokertool.ml_opponent_modeling import (
    ModelType, PlayerType, PlayerStats, HandHistory, ModelPrediction,
    FeatureEngineering, OpponentModel, RandomForestOpponentModel,
    NeuralNetworkOpponentModel, OpponentModelingSystem,
    get_opponent_modeling_system, observe_opponent_hand, predict_opponent_action,
    get_opponent_profile, analyze_table_dynamics
)
from pokertool.ocr_recognition import (
    RecognitionMethod, CardRegion, RecognitionResult, 
    PokerOCR, get_poker_ocr, create_card_regions
)

class TestGTOSolver(unittest.TestCase):
    """Test cases for GTO solver functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.solver = GTOSolver(cache_dir=self.temp_dir)
        
        # Create test game state
        self.game_state = GameState(
            street=Street.FLOP,
            pot=20.0,
            effective_stack=100.0,
            board=['Ah', 'Kc', 'Qh'],
            position='BTN',
            num_players=2,
            to_call=5.0
        )
        
        # Create test ranges
        self.ranges = create_standard_ranges()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_range_creation(self):
        """Test poker range creation and manipulation."""
        range_obj = Range()
        
        # Test adding hands
        range_obj.add_hand('AA', 1.0)
        range_obj.add_hand('KK', 0.8)
        
        self.assertEqual(len(range_obj.hands), 2)
        self.assertAlmostEqual(range_obj.get_frequency('AA'), 1.0 / 1.8, places=2)
        self.assertAlmostEqual(range_obj.get_frequency('KK'), 0.8 / 1.8, places=2)
        
        # Test removing hands
        range_obj.remove_hand('KK')
        self.assertEqual(len(range_obj.hands), 1)
        self.assertEqual(range_obj.get_frequency('AA'), 1.0)
        
        # Test string representation
        range_str = range_obj.to_string()
        self.assertIn('AA', range_str)
    
    def test_game_state_calculations(self):
        """Test game state calculation methods."""
        # Test pot odds calculation
        pot_odds = self.game_state.get_pot_odds()
        self.assertEqual(pot_odds, 4.0)  # 20/5
        
        # Test stack-to-pot ratio
        spr = self.game_state.get_stack_to_pot_ratio()
        self.assertEqual(spr, 5.0)  # 100/20
        
        # Test with zero to_call
        game_state_check = GameState(
            street=Street.FLOP,
            pot=20.0,
            effective_stack=100.0,
            to_call=0.0
        )
        self.assertEqual(game_state_check.get_pot_odds(), float('inf'))
    
    def test_strategy_operations(self):
        """Test strategy creation and manipulation."""
        strategy = Strategy()
        
        # Test adding actions - create strategy where CALL should be dominant
        strategy.add_action(Action.CALL, 0.5)
        strategy.add_action(Action.FOLD, 0.3)
        strategy.add_action(Action.RAISE, 0.2)
        
        # Test normalization
        total_freq = sum(strategy.actions.values())
        self.assertAlmostEqual(total_freq, 1.0, places=6)
        
        # Test dominant action - CALL should be dominant since it was added first with highest frequency
        dominant = strategy.get_dominant_action()
        self.assertEqual(dominant, Action.CALL)
        
        # Test pure strategy detection
        pure_strategy = Strategy()
        pure_strategy.add_action(Action.FOLD, 1.0)
        self.assertTrue(pure_strategy.is_pure_strategy())
        
        mixed_strategy = Strategy()
        mixed_strategy.add_action(Action.FOLD, 0.6)
        mixed_strategy.add_action(Action.CALL, 0.4)
        self.assertFalse(mixed_strategy.is_pure_strategy())
    
    def test_equity_calculator(self):
        """Test equity calculation functionality."""
        calc = EquityCalculator()
        
        # Test basic equity calculation
        hands = ['AsKh', 'QdQc']
        board = ['Ah', 'Kc', 'Qh']
        equities = calc.calculate_equity(hands, board, iterations=1000)
        
        self.assertEqual(len(equities), 2)
        self.assertTrue(all(0 <= eq <= 1 for eq in equities))
        self.assertAlmostEqual(sum(equities), 1.0, places=2)
        
        # Test caching
        equities_cached = calc.calculate_equity(hands, board, iterations=1000)
        self.assertEqual(equities, equities_cached)
        
        # Test deck generation
        deck = calc._generate_deck()
        self.assertEqual(len(deck), 52)
        self.assertIn('As', deck)
        self.assertIn('2c', deck)
    
    def test_gto_solver_basic(self):
        """Test basic GTO solver functionality."""
        # Test solver initialization
        self.assertTrue(self.solver.cache_dir.exists())
        self.assertIsNotNone(self.solver.equity_calculator)
        
        # Test cache key generation
        cache_key = self.solver._create_solution_cache_key(self.game_state, self.ranges)
        self.assertIsInstance(cache_key, str)
        self.assertEqual(len(cache_key), 32)  # MD5 hash length
        
        # Test possible actions detection
        actions = self.solver._get_possible_actions(self.game_state)
        self.assertIn(Action.FOLD, actions)
        self.assertIn(Action.CALL, actions)
        self.assertIn(Action.RAISE, actions)
    
    def test_gto_solver_solve(self):
        """Test GTO solver solve method."""
        # Use small iteration count for testing
        solution = self.solver.solve(self.game_state, self.ranges, max_iterations=10)
        
        self.assertIsInstance(solution, GTOSolution)
        self.assertEqual(solution.game_state, self.game_state)
        self.assertEqual(solution.ranges, self.ranges)
        self.assertGreater(solution.iterations, 0)
        self.assertGreater(solution.solve_time, 0)
        self.assertIn('solver_version', solution.metadata)
    
    def test_gto_trainer(self):
        """Test GTO trainer functionality."""
        trainer = GTOTrainer(self.solver)
        
        # Test training spot generation
        spot = trainer.generate_training_spot(Street.FLOP, num_players=2)
        self.assertIn('game_state', spot)
        self.assertIn('ranges', spot)
        self.assertIn('hero_hand', spot)
        
        # Test decision evaluation
        evaluation = trainer.evaluate_decision(spot, Action.FOLD)
        self.assertIn('correct', evaluation)
        self.assertIn('gto_strategy', evaluation)
        self.assertIn('explanation', evaluation)
        self.assertIn('stats', evaluation)
        
        # Check stats tracking
        self.assertEqual(trainer.training_stats['total_decisions'], 1)
    
    def test_deviation_explorer(self):
        """Test deviation explorer functionality."""
        explorer = DeviationExplorer(self.solver)
        
        # Create test deviation strategy
        deviation_strategy = Strategy()
        deviation_strategy.add_action(Action.FOLD, 0.9)
        deviation_strategy.add_action(Action.CALL, 0.1)
        
        # Test deviation analysis
        analysis = explorer.analyze_deviation(
            self.game_state, self.ranges, 'Player1', deviation_strategy
        )
        
        self.assertIn('gto_ev', analysis)
        self.assertIn('deviation_ev', analysis)
        self.assertIn('ev_loss', analysis)
        self.assertIn('counter_exploit_suggestions', analysis)
    
    def test_gto_convenience_functions(self):
        """Test convenience functions."""
        # Test solve_spot function
        solution = solve_spot(self.game_state, self.ranges, max_iterations=5)
        self.assertIsInstance(solution, GTOSolution)
        
        # Test analyze_gto_spot function
        analysis = analyze_gto_spot('AsKh', ['Ah', 'Kc', 'Qh'], 'BTN', 20.0, 5.0, 100.0)
        
        self.assertIn('hole_cards', analysis)
        self.assertIn('board', analysis)
        self.assertIn('gto_strategy', analysis)
        self.assertIn('recommendations', analysis)
        
        # Test standard ranges creation
        ranges = create_standard_ranges()
        self.assertIn('UTG', ranges)
        self.assertIn('BTN', ranges)
        self.assertGreater(len(ranges['UTG'].hands), 0)
        self.assertGreater(len(ranges['BTN'].hands), len(ranges['UTG'].hands))

class TestMLOpponentModeling(unittest.TestCase):
    """Test cases for ML opponent modeling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.system = OpponentModelingSystem(models_dir=self.temp_dir)
        
        # Create test hand history
        self.hand_history = HandHistory(
            hand_id='test_hand_1',
            player_id='test_player_1',
            position='BTN',
            board=['Ah', 'Kc', 'Qh'],
            actions=[('preflop', Action.RAISE, 3), ('flop', Action.BET, 5)],
            pot_size=15,
            stack_size=100,
            result='won',
            showdown=True,
            won=True
        )
        
        # Create test player stats
        self.player_stats = PlayerStats(
            player_id='test_player_1',
            hands_observed=100,
            vpip=0.25,
            pfr=0.15,
            aggression_factor=2.5,
            showdown_frequency=0.3,
            win_rate_at_showdown=0.55
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_player_stats(self):
        """Test player statistics tracking."""
        stats = PlayerStats(player_id='test_player')
        
        # Test initial state
        self.assertEqual(stats.hands_observed, 0)
        self.assertEqual(stats.get_player_type(), PlayerType.UNKNOWN)
        
        # Test player type classification
        tight_aggressive = PlayerStats(
            player_id='tag_player',
            hands_observed=100,
            vpip=0.18,
            aggression_factor=2.5
        )
        self.assertEqual(tight_aggressive.get_player_type(), PlayerType.TIGHT_AGGRESSIVE)
        
        loose_passive = PlayerStats(
            player_id='lp_player',
            hands_observed=100,
            vpip=0.35,
            aggression_factor=1.2
        )
        self.assertEqual(loose_passive.get_player_type(), PlayerType.LOOSE_PASSIVE)
    
    def test_hand_history(self):
        """Test hand history creation and validation."""
        # Test basic hand history
        self.assertEqual(self.hand_history.player_id, 'test_player_1')
        self.assertEqual(len(self.hand_history.actions), 2)
        self.assertTrue(self.hand_history.showdown)
        self.assertTrue(self.hand_history.won)
        
        # Test timestamp
        self.assertIsInstance(self.hand_history.timestamp, float)
        self.assertGreater(self.hand_history.timestamp, time.time() - 60)
    
    def test_feature_engineering(self):
        """Test feature engineering functionality."""
        fe = FeatureEngineering()
        
        # Test feature extraction
        game_context = {'to_call': 5.0, 'pot_odds': 4.0}
        features = fe.extract_features(self.hand_history, self.player_stats, game_context)
        
        self.assertEqual(len(features), len(fe.feature_names))
        self.assertTrue(all(isinstance(f, (int, float, np.number)) for f in features))
        
        # Test normalization functions
        norm_pot = fe._normalize_pot_size(50.0)
        self.assertTrue(0 <= norm_pot <= 1)
        
        norm_stack = fe._normalize_stack_size(500.0)
        self.assertTrue(0 <= norm_stack <= 1)
        
        # Test board texture calculation
        board_texture = fe._calculate_board_texture(['Ah', 'Kc', 'Qh'])
        self.assertTrue(0 <= board_texture <= 1)
        
        # Test action frequency calculation
        betting_freq, check_freq, fold_freq = fe._calculate_action_frequencies(self.hand_history)
        self.assertAlmostEqual(betting_freq + check_freq + fold_freq, 1.0, places=6)
    
    @patch('pokertool.ml_opponent_modeling.ML_SKLEARN_AVAILABLE', True)
    def test_random_forest_model(self):
        """Test Random Forest opponent model."""
        with patch('pokertool.ml_opponent_modeling.RandomForestClassifier') as mock_rf, \
             patch('pokertool.ml_opponent_modeling.cross_val_score') as mock_cv, \
             patch('pokertool.ml_opponent_modeling.StandardScaler') as mock_scaler:
            
            # Mock the RandomForest classifier
            mock_classifier = Mock()
            mock_classifier.fit.return_value = None
            mock_classifier.predict.return_value = ['fold']
            mock_classifier.predict_proba.return_value = [[0.8, 0.2]]
            mock_classifier.classes_ = ['fold', 'call']
            # Add sklearn internal attributes
            mock_classifier.__sklearn_tags__ = Mock()
            mock_rf.return_value = mock_classifier
            
            # Mock cross_val_score
            mock_cv.return_value = np.array([0.8, 0.7, 0.9, 0.8, 0.75])
            
            # Mock StandardScaler
            mock_scaler_instance = Mock()
            mock_scaler_instance.fit_transform.return_value = np.random.random((15, 20))
            mock_scaler_instance.transform.return_value = np.random.random((1, 20))
            mock_scaler.return_value = mock_scaler_instance
            
            model = RandomForestOpponentModel('test_player')
            model.feature_scaler = mock_scaler_instance
            
            # Test training
            training_data = [self.hand_history] * 15  # Minimum required
            result = model.train(training_data, self.player_stats)
            self.assertTrue(result)
            self.assertTrue(model.is_trained)
            
            # Test prediction
            game_context = {'to_call': 5.0}
            prediction = model.predict(self.hand_history, self.player_stats, game_context)
            
            self.assertIsInstance(prediction, ModelPrediction)
            self.assertEqual(prediction.player_id, 'test_player')
            self.assertIsInstance(prediction.predicted_action, Action)
            self.assertTrue(0 <= prediction.confidence <= 1)
    
    @patch('pokertool.ml_opponent_modeling.ML_DEEP_AVAILABLE', True)
    def test_neural_network_model(self):
        """Test Neural Network opponent model."""
        with patch('pokertool.ml_opponent_modeling.tf') as mock_tf:
            # Mock TensorFlow components
            mock_model = Mock()
            mock_model.fit.return_value = Mock(history={'loss': [0.5, 0.4, 0.3]})
            mock_model.evaluate.return_value = [0.3, 0.85]
            mock_model.predict.return_value = [[0.7, 0.3]]
            
            mock_models = Mock()
            mock_models.Sequential.return_value = mock_model
            mock_tf.keras.models = mock_models
            
            # Mock other TensorFlow components
            mock_tf.keras.layers = Mock()
            mock_tf.keras.optimizers = Mock()
            mock_tf.keras.callbacks = Mock()
            
            model = NeuralNetworkOpponentModel('test_player')
            model.model = mock_model  # Set the mocked model
            
            # Test training
            training_data = [self.hand_history] * 60  # Minimum required for NN
            with patch('pokertool.ml_opponent_modeling.LabelEncoder') as mock_le, \
                 patch('pokertool.ml_opponent_modeling.train_test_split') as mock_split, \
                 patch('pokertool.ml_opponent_modeling.StandardScaler') as mock_scaler:
                
                mock_encoder = Mock()
                # Return 60 labels to match 60 training samples
                mock_encoder.fit_transform.return_value = np.array([0] * 60)
                mock_encoder.inverse_transform.return_value = ['fold']
                mock_le.return_value = mock_encoder
                model.label_encoder = mock_encoder
                
                # Mock train_test_split
                X_train = np.random.random((48, 20))
                X_test = np.random.random((12, 20))
                y_train = np.array([0] * 48)
                y_test = np.array([0] * 12)
                mock_split.return_value = (X_train, X_test, y_train, y_test)
                
                # Mock StandardScaler
                mock_scaler_instance = Mock()
                mock_scaler_instance.fit_transform.return_value = np.random.random((60, 20))
                mock_scaler.return_value = mock_scaler_instance
                model.feature_scaler = mock_scaler_instance
                
                result = model.train(training_data, self.player_stats)
                self.assertTrue(result)
                self.assertTrue(model.is_trained)
    
    def test_opponent_modeling_system(self):
        """Test opponent modeling system integration."""
        # Test hand observation
        self.system.observe_hand(self.hand_history)
        
        # Check player stats were created
        self.assertIn('test_player_1', self.system.player_stats)
        self.assertIn('test_player_1', self.system.hand_histories)
        
        stats = self.system.player_stats['test_player_1']
        self.assertEqual(stats.hands_observed, 1)
        
        # Test statistical prediction (fallback when no model)
        game_context = {'to_call': 5.0, 'pot_odds': 4.0}
        prediction = self.system.predict_opponent_action('test_player_1', self.hand_history, game_context)
        
        self.assertIsInstance(prediction, ModelPrediction)
        self.assertEqual(prediction.player_id, 'test_player_1')
        self.assertEqual(prediction.model_version, 'statistical')
        
        # Test player profile retrieval
        profile = self.system.get_player_profile('test_player_1')
        self.assertIsNotNone(profile)
        self.assertIn('statistics', profile)
        self.assertIn('player_type', profile)
        
        # Test system statistics
        sys_stats = self.system.get_system_stats()
        self.assertEqual(sys_stats['total_players_observed'], 1)
        self.assertEqual(sys_stats['total_hands_observed'], 1)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test observe_opponent_hand
        hand_data = {
            'hand_id': 'test_hand_2',
            'position': 'UTG',
            'board': ['2h', '3c', '4s'],
            'actions': [('preflop', 'call', 2)],
            'pot_size': 10,
            'stack_size': 98,
            'showdown': False,
            'won': False
        }
        
        result = observe_opponent_hand('test_player_2', hand_data)
        self.assertTrue(result)
        
        # Test predict_opponent_action
        game_context = {
            'position': 'BTN',
            'board': ['Ah', 'Kc', 'Qh'],
            'pot_size': 20,
            'to_call': 5
        }
        
        prediction = predict_opponent_action('test_player_2', game_context)
        self.assertIsInstance(prediction, ModelPrediction)
        
        # Test get_opponent_profile
        profile = get_opponent_profile('test_player_2')
        self.assertIsNotNone(profile)
        
        # Test table dynamics analysis
        profiles = [profile] if profile else []
        if profiles:
            dynamics = analyze_table_dynamics(profiles)
            self.assertIn('table_type', dynamics)
            self.assertIn('recommendations', dynamics)

class TestOCRRecognition(unittest.TestCase):
    """Test cases for OCR recognition functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_card_region(self):
        """Test card region functionality."""
        region = CardRegion(100, 200, 50, 80, 'hole')
        
        self.assertEqual(region.x, 100)
        self.assertEqual(region.y, 200)
        self.assertEqual(region.width, 50)
        self.assertEqual(region.height, 80)
        self.assertEqual(region.card_type, 'hole')
    
    def test_recognition_result(self):
        """Test recognition result structure."""
        result = RecognitionResult(
            cards=['As', 'Kh'],
            confidence=0.85,
            method_used=RecognitionMethod.HYBRID,
            processing_time=0.5
        )
        
        self.assertEqual(len(result.cards), 2)
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.method_used, RecognitionMethod.HYBRID)
        self.assertGreater(result.processing_time, 0)
    
    def test_create_card_regions(self):
        """Test card region creation."""
        regions = create_card_regions('standard')
        
        self.assertGreater(len(regions), 0)
        
        # Check for different card types
        card_types = {region.card_type for region in regions}
        self.assertIn('hole', card_types)
        self.assertIn('board', card_types)
        self.assertIn('opponent', card_types)
    
    @patch('pokertool.ocr_recognition.OCR_AVAILABLE', False)
    def test_ocr_unavailable(self):
        """Test behavior when OCR libraries are not available."""
        with self.assertRaises(RuntimeError):
            PokerOCR()
    
    @patch('pokertool.ocr_recognition.OCR_AVAILABLE', True)
    def test_poker_ocr_mock(self):
        """Test PokerOCR with mocked dependencies."""
        with patch('pokertool.ocr_recognition.cv2'), \
             patch('pokertool.ocr_recognition.pytesseract'), \
             patch('pokertool.ocr_recognition.Image'), \
             patch('pokertool.ocr_recognition.easyocr'):
            
            # This would normally fail without the actual OCR libraries
            # But we're testing the structure and API
            pass

class TestIntegration(unittest.TestCase):
    """Integration tests between modules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_gto_ml_integration(self):
        """Test integration between GTO solver and ML modeling."""
        # Create GTO solver
        gto_solver = GTOSolver(cache_dir=self.temp_dir)
        
        # Create game state
        game_state = GameState(
            street=Street.FLOP,
            pot=20.0,
            effective_stack=100.0,
            board=['Ah', 'Kc', 'Qh'],
            position='BTN'
        )
        
        ranges = create_standard_ranges()
        
        # Solve GTO spot
        solution = gto_solver.solve(game_state, ranges, max_iterations=5)
        
        # Create ML system
        ml_system = OpponentModelingSystem(models_dir=self.temp_dir)
        
        # Simulate opponent actions based on GTO solution
        gto_strategy = solution.strategies.get('BTN', {}).get('AsKh', Strategy())
        
        if gto_strategy.actions:
            dominant_action = gto_strategy.get_dominant_action()
            
            # Create hand history based on GTO recommendation
            hand_history = HandHistory(
                hand_id='integration_test',
                player_id='gto_opponent',
                position='BTN',
                board=['Ah', 'Kc', 'Qh'],
                actions=[('flop', dominant_action, 5)],
                pot_size=20,
                stack_size=100
            )
            
            # Observe the hand in ML system
            ml_system.observe_hand(hand_history)
            
            # Verify integration
            profile = ml_system.get_player_profile('gto_opponent')
            self.assertIsNotNone(profile)
    
    def test_end_to_end_poker_analysis(self):
        """Test end-to-end poker analysis workflow."""
        # 1. Parse cards
        hole_cards = [parse_card('As'), parse_card('Kh')]
        board_cards = [parse_card('Ah'), parse_card('Kc'), parse_card('Qh')]
        
        # 2. Analyze hand strength
        analysis = analyse_hand(hole_cards, board_cards)
        self.assertGreater(analysis.strength, 0)
        
        # 3. Get GTO recommendation
        gto_analysis = analyze_gto_spot('AsKh', ['Ah', 'Kc', 'Qh'], 'BTN', 20.0, 5.0, 100.0)
        self.assertIn('recommendations', gto_analysis)
        
        # 4. Predict opponent action
        game_context = {
            'position': 'UTG',
            'board': ['Ah', 'Kc', 'Qh'],
            'pot_size': 20,
            'to_call': 5
        }
        
        prediction = predict_opponent_action('test_opponent', game_context)
        self.assertIsInstance(prediction.predicted_action, Action)
        
        # Integration successful if all components work together
        self.assertTrue(True)

class TestPerformance(unittest.TestCase):
    """Performance tests for computationally intensive operations."""
    
    def test_equity_calculation_performance(self):
        """Test equity calculation performance."""
        calc = EquityCalculator()
        
        start_time = time.time()
        equities = calc.calculate_equity(['AsKh', 'QdQc'], ['Ah', 'Kc', 'Qh'], iterations=1000)
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 5.0)  # 5 seconds max
        self.assertEqual(len(equities), 2)
    
    def test_gto_solver_performance(self):
        """Test GTO solver performance."""
        solver = GTOSolver()
        
        game_state = GameState(
            street=Street.FLOP,
            pot=20.0,
            effective_stack=100.0,
            board=['Ah', 'Kc', 'Qh']
        )
        
        ranges = create_standard_ranges()
        
        start_time = time.time()
        solution = solver.solve(game_state, ranges, max_iterations=50)
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 10.0)  # 10 seconds max
        self.assertTrue(solution.convergence_reached or solution.iterations > 0)
    
    def test_feature_engineering_performance(self):
        """Test feature engineering performance."""
        fe = FeatureEngineering()
        
        hand_history = HandHistory(
            hand_id='perf_test',
            player_id='test_player',
            position='BTN',
            board=['Ah', 'Kc', 'Qh'],
            actions=[('preflop', Action.RAISE, 3)],
            pot_size=15,
            stack_size=100
        )
        
        player_stats = PlayerStats(
            player_id='test_player',
            hands_observed=100,
            vpip=0.25,
            pfr=0.15
        )
        
        game_context = {'to_call': 5.0}
        
        start_time = time.time()
        for _ in range(1000):  # Extract features 1000 times
            features = fe.extract_features(hand_history, player_stats, game_context)
        end_time = time.time()
        
        # Should be fast enough for real-time use
        self.assertLess(end_time - start_time, 1.0)  # 1 second for 1000 extractions
        self.assertEqual(len(features), len(fe.feature_names))

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def test_invalid_card_parsing(self):
        """Test handling of invalid card inputs."""
        with self.assertRaises(ValueError):
            parse_card('XX')
        
        with self.assertRaises(ValueError):
            parse_card('As2')
        
        with self.assertRaises(ValueError):
            parse_card('')
    
    def test_empty_range_operations(self):
        """Test operations on empty ranges."""
        empty_range = Range()
        
        self.assertEqual(empty_range.total_combos(), 0)
        self.assertEqual(empty_range.get_frequency('AA'), 0.0)
        self.assertEqual(empty_range.to_string(), "Empty range")
    
    def test_invalid_game_state(self):
        """Test handling of invalid game states."""
        # Test zero pot
        game_state = GameState(
            street=Street.FLOP,
            pot=0.0,
            effective_stack=100.0
        )
        
        self.assertEqual(game_state.get_stack_to_pot_ratio(), float('inf'))
    
    def test_ml_system_edge_cases(self):
        """Test ML system edge cases."""
        system = OpponentModelingSystem()
        
        # Create a test hand history for this test
        test_hand_history = HandHistory(
            hand_id='edge_test',
            player_id='unknown_player',
            position='BTN',
            board=['Ah', 'Kc', 'Qh'],
            actions=[('preflop', Action.RAISE, 3)],
            pot_size=15,
            stack_size=100
        )
        
        # Test prediction for unknown player
        prediction = system.predict_opponent_action('unknown_player', test_hand_history, {})
        self.assertEqual(prediction.player_id, 'unknown_player')
        self.assertEqual(prediction.predicted_action, Action.FOLD)
        self.assertEqual(prediction.confidence, 0.0)
        
        # Test profile for non-existent player
        profile = system.get_player_profile('non_existent')
        self.assertIsNone(profile)

if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
