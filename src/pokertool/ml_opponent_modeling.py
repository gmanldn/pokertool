"""
Machine Learning Opponent Modeling Module
Provides advanced ML-based opponent modeling with neural networks, feature engineering,
online learning, and model versioning for dynamic player adaptation.
"""

import os
import logging
import time
import pickle
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
import numpy as np

# Try to import ML dependencies
try:
    import pandas as pd
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.pipeline import Pipeline
    import joblib
    ML_SKLEARN_AVAILABLE = True
except ImportError:
    ML_SKLEARN_AVAILABLE = False
    pd = None

# Try to import deep learning dependencies
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers, callbacks
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    ML_DEEP_AVAILABLE = True
except ImportError:
    ML_DEEP_AVAILABLE = False
    tf = None
    torch = None

from .core import Card, parse_card, analyse_hand
from .gto_solver import Action, Street, Strategy
from .threading import get_thread_pool, TaskPriority, cpu_intensive
from .error_handling import retry_on_failure
from .database import get_production_db

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Types of opponent models available."""
    STATISTICAL = 'statistical'
    RANDOM_FOREST = 'random_forest'
    GRADIENT_BOOSTING = 'gradient_boosting'
    NEURAL_NETWORK = 'neural_network'
    LSTM = 'lstm'
    TRANSFORMER = 'transformer'

class PlayerType(Enum):
    """Opponent player type classifications."""
    TIGHT_PASSIVE = 'tight_passive'
    TIGHT_AGGRESSIVE = 'tight_aggressive'
    LOOSE_PASSIVE = 'loose_passive'
    LOOSE_AGGRESSIVE = 'loose_aggressive'
    MANIAC = 'maniac'
    NIT = 'nit'
    TAG = 'tag'
    LAG = 'lag'
    UNKNOWN = 'unknown'

@dataclass
class PlayerStats:
    """Statistical profile of a player."""
    player_id: str
    hands_observed: int = 0
    vpip: float = 0.0  # Voluntarily put money in pot
    pfr: float = 0.0   # Preflop raise
    aggression_factor: float = 0.0
    cbet_frequency: float = 0.0
    fold_to_cbet: float = 0.0
    three_bet_frequency: float = 0.0
    fold_to_three_bet: float = 0.0
    steal_frequency: float = 0.0
    fold_to_steal: float = 0.0
    showdown_frequency: float = 0.0
    win_rate_at_showdown: float = 0.0
    avg_pot_size: float = 0.0
    position_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    street_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    
    def get_player_type(self) -> PlayerType:
        """Classify player type based on stats."""
        if self.hands_observed < 50:
            return PlayerType.UNKNOWN
        
        is_tight = self.vpip < 0.2
        is_aggressive = self.aggression_factor > 2.0
        
        if is_tight and is_aggressive:
            return PlayerType.TIGHT_AGGRESSIVE
        elif is_tight and not is_aggressive:
            return PlayerType.TIGHT_PASSIVE
        elif not is_tight and is_aggressive:
            return PlayerType.LOOSE_AGGRESSIVE
        else:
            return PlayerType.LOOSE_PASSIVE

@dataclass
class HandHistory:
    """Single hand history for ML training."""
    hand_id: str
    player_id: str
    position: str
    hole_cards: Optional[List[str]] = None
    board: List[str] = field(default_factory=list)
    actions: List[Tuple[str, Action, float]] = field(default_factory=list)  # (street, action, amount)
    pot_size: float = 0.0
    stack_size: float = 0.0
    num_players: int = 2
    result: str = 'unknown'  # fold, call, raise, etc.
    showdown: bool = False
    won: bool = False
    amount_won: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class ModelPrediction:
    """Prediction from opponent model."""
    player_id: str
    predicted_action: Action
    confidence: float
    probability_distribution: Dict[Action, float] = field(default_factory=dict)
    features_used: Dict[str, float] = field(default_factory=dict)
    model_version: str = '1.0'
    prediction_time: float = field(default_factory=time.time)

class FeatureEngineering:
    """
    Feature engineering for opponent modeling.
    Extracts relevant features from hand histories and game states.
    """
    
    def __init__(self):
        self.feature_names = [
            'position_numeric', 'num_players', 'pot_size_norm', 'stack_size_norm',
            'pot_odds', 'stack_to_pot_ratio', 'board_texture_score',
            'vpip', 'pfr', 'aggression_factor', 'cbet_frequency',
            'preflop_raise_size', 'betting_frequency', 'check_frequency',
            'fold_frequency', 'recent_win_rate', 'hands_since_last_showdown',
            'position_frequency', 'street_aggression', 'bluff_frequency_estimate'
        ]
    
    def extract_features(self, hand_history: HandHistory, player_stats: PlayerStats,
                        game_context: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector from hand history and player stats."""
        features = []
        
        # Position features
        position_map = {'UTG': 0, 'UTG+1': 1, 'MP': 2, 'MP+1': 3, 'CO': 4, 'BTN': 5, 'SB': 6, 'BB': 7}
        features.append(position_map.get(hand_history.position, 0))
        
        # Table dynamics
        features.append(hand_history.num_players)
        features.append(self._normalize_pot_size(hand_history.pot_size))
        features.append(self._normalize_stack_size(hand_history.stack_size))
        
        # Pot odds and SPR
        pot_odds = self._calculate_pot_odds(hand_history, game_context)
        features.append(pot_odds)
        
        spr = hand_history.stack_size / max(hand_history.pot_size, 1)
        features.append(min(spr, 20))  # Cap SPR for normalization
        
        # Board texture (simplified)
        board_texture = self._calculate_board_texture(hand_history.board)
        features.append(board_texture)
        
        # Player statistics
        features.append(player_stats.vpip)
        features.append(player_stats.pfr)
        features.append(min(player_stats.aggression_factor, 10))  # Cap aggression factor
        features.append(player_stats.cbet_frequency)
        
        # Betting pattern features
        preflop_raise_size = self._extract_preflop_raise_size(hand_history)
        features.append(preflop_raise_size)
        
        # Action frequency features
        betting_freq, check_freq, fold_freq = self._calculate_action_frequencies(hand_history)
        features.extend([betting_freq, check_freq, fold_freq])
        
        # Recent performance
        recent_win_rate = self._calculate_recent_win_rate(player_stats)
        features.append(recent_win_rate)
        
        # Hands since showdown (recency bias)
        hands_since_showdown = self._calculate_hands_since_showdown(player_stats)
        features.append(min(hands_since_showdown, 100))  # Cap for normalization
        
        # Position-specific features
        position_freq = player_stats.position_stats.get(hand_history.position, {}).get('frequency', 0)
        features.append(position_freq)
        
        # Street-specific aggression
        street_aggression = self._calculate_street_aggression(hand_history, player_stats)
        features.append(street_aggression)
        
        # Bluff frequency estimate
        bluff_freq = self._estimate_bluff_frequency(player_stats)
        features.append(bluff_freq)
        
        return np.array(features, dtype=np.float32)
    
    def _normalize_pot_size(self, pot_size: float) -> float:
        """Normalize pot size to [0, 1] range."""
        return min(pot_size / 200.0, 1.0)  # Assume max pot of 200 for normalization
    
    def _normalize_stack_size(self, stack_size: float) -> float:
        """Normalize stack size to [0, 1] range."""
        return min(stack_size / 1000.0, 1.0)  # Assume max stack of 1000
    
    def _calculate_pot_odds(self, hand_history: HandHistory, game_context: Dict[str, Any]) -> float:
        """Calculate pot odds for the current situation."""
        to_call = game_context.get('to_call', 0)
        if to_call == 0:
            return float('inf')
        return hand_history.pot_size / to_call
    
    def _calculate_board_texture(self, board: List[str]) -> float:
        """Calculate board texture score (0-1, higher = more coordinated)."""
        if len(board) < 3:
            return 0.0
        
        try:
            # Parse board cards
            cards = [parse_card(card) for card in board[:5]]
            ranks = [card.rank.value for card in cards]
            suits = [card.suit for card in cards]
            
            texture_score = 0.0
            
            # Check for flush draws
            suit_counts = {}
            for suit in suits:
                suit_counts[suit] = suit_counts.get(suit, 0) + 1
            max_suit_count = max(suit_counts.values()) if suit_counts else 0
            if max_suit_count >= 3:
                texture_score += 0.3
            
            # Check for straight draws
            unique_ranks = sorted(set(ranks))
            if len(unique_ranks) >= 3:
                for i in range(len(unique_ranks) - 2):
                    if unique_ranks[i+2] - unique_ranks[i] <= 4:
                        texture_score += 0.2
                        break
            
            # Check for pairs
            rank_counts = {}
            for rank in ranks:
                rank_counts[rank] = rank_counts.get(rank, 0) + 1
            if max(rank_counts.values()) >= 2:
                texture_score += 0.1
            
            return min(texture_score, 1.0)
            
        except Exception:
            return 0.0
    
    def _extract_preflop_raise_size(self, hand_history: HandHistory) -> float:
        """Extract preflop raise size (normalized)."""
        for street, action, amount in hand_history.actions:
            if street == 'preflop' and action in [Action.RAISE, Action.BET]:
                return min(amount / 10.0, 1.0)  # Normalize to [0, 1]
        return 0.0
    
    def _calculate_action_frequencies(self, hand_history: HandHistory) -> Tuple[float, float, float]:
        """Calculate betting, checking, folding frequencies."""
        total_actions = len(hand_history.actions)
        if total_actions == 0:
            return 0.0, 0.0, 0.0
        
        betting_count = sum(1 for _, action, _ in hand_history.actions 
                           if action in [Action.BET, Action.RAISE])
        check_count = sum(1 for _, action, _ in hand_history.actions 
                         if action == Action.CHECK)
        fold_count = sum(1 for _, action, _ in hand_history.actions 
                        if action == Action.FOLD)
        
        return (betting_count / total_actions, 
                check_count / total_actions, 
                fold_count / total_actions)
    
    def _calculate_recent_win_rate(self, player_stats: PlayerStats) -> float:
        """Calculate recent win rate."""
        # Simplified - in practice, would track recent hands
        return player_stats.win_rate_at_showdown
    
    def _calculate_hands_since_showdown(self, player_stats: PlayerStats) -> int:
        """Calculate hands since last showdown."""
        # Simplified - would track actual hand sequence
        return max(0, int(time.time() - player_stats.last_updated) // 60)
    
    def _calculate_street_aggression(self, hand_history: HandHistory, player_stats: PlayerStats) -> float:
        """Calculate street-specific aggression."""
        return player_stats.aggression_factor
    
    def _estimate_bluff_frequency(self, player_stats: PlayerStats) -> float:
        """Estimate bluff frequency based on player stats."""
        # Simplified bluff frequency estimation
        if player_stats.aggression_factor > 3 and player_stats.vpip > 0.3:
            return min(player_stats.aggression_factor / 10, 0.5)
        return 0.0

class OpponentModel:
    """Base class for opponent models."""
    
    def __init__(self, model_type: ModelType, player_id: str):
        self.model_type = model_type
        self.player_id = player_id
        self.model = None
        self.feature_scaler = StandardScaler()
        self.is_trained = False
        self.version = '1.0'
        self.training_history = []
        self.last_updated = time.time()
        
    def train(self, training_data: List[HandHistory], player_stats: PlayerStats) -> bool:
        """Train the model with historical data."""
        raise NotImplementedError
    
    def predict(self, hand_history: HandHistory, player_stats: PlayerStats, 
                game_context: Dict[str, Any]) -> ModelPrediction:
        """Make prediction for opponent's next action."""
        raise NotImplementedError
    
    def update_online(self, hand_history: HandHistory, actual_action: Action) -> bool:
        """Update model with new data (online learning)."""
        raise NotImplementedError
    
    def save_model(self, filepath: str) -> bool:
        """Save model to disk."""
        try:
            model_data = {
                'model_type': self.model_type.value,
                'player_id': self.player_id,
                'model': self.model,
                'feature_scaler': self.feature_scaler,
                'is_trained': self.is_trained,
                'version': self.version,
                'last_updated': self.last_updated
            }
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """Load model from disk."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model_type = ModelType(model_data['model_type'])
            self.player_id = model_data['player_id']
            self.model = model_data['model']
            self.feature_scaler = model_data['feature_scaler']
            self.is_trained = model_data['is_trained']
            self.version = model_data['version']
            self.last_updated = model_data['last_updated']
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

class RandomForestOpponentModel(OpponentModel):
    """Random Forest-based opponent model."""
    
    def __init__(self, player_id: str):
        super().__init__(ModelType.RANDOM_FOREST, player_id)
        if ML_SKLEARN_AVAILABLE:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
        self.feature_engineering = FeatureEngineering()
    
    def train(self, training_data: List[HandHistory], player_stats: PlayerStats) -> bool:
        """Train Random Forest model."""
        if not ML_SKLEARN_AVAILABLE:
            logger.error("Scikit-learn not available for Random Forest model")
            return False
        
        if len(training_data) < 10:
            logger.warning(f"Insufficient training data: {len(training_data)} hands")
            return False
        
        try:
            # Extract features and labels
            features = []
            labels = []
            
            for hand in training_data:
                # Simulate game context
                game_context = {'to_call': 5.0}  # Simplified
                
                feature_vector = self.feature_engineering.extract_features(
                    hand, player_stats, game_context
                )
                features.append(feature_vector)
                
                # Extract label (last action in the hand)
                if hand.actions:
                    last_action = hand.actions[-1][1]
                    labels.append(last_action.value)
                else:
                    labels.append(Action.FOLD.value)
            
            features = np.array(features)
            
            # Scale features
            features_scaled = self.feature_scaler.fit_transform(features)
            
            # Train model
            self.model.fit(features_scaled, labels)
            self.is_trained = True
            self.last_updated = time.time()
            
            # Evaluate model
            if len(features) > 5:
                scores = cross_val_score(self.model, features_scaled, labels, cv=min(5, len(features)//2))
                logger.info(f"Model trained for {self.player_id}: CV Score = {scores.mean():.3f} ± {scores.std():.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Training failed for {self.player_id}: {e}")
            return False
    
    def predict(self, hand_history: HandHistory, player_stats: PlayerStats, 
                game_context: Dict[str, Any]) -> ModelPrediction:
        """Make prediction using Random Forest."""
        if not self.is_trained:
            # Return default prediction
            return ModelPrediction(
                player_id=self.player_id,
                predicted_action=Action.FOLD,
                confidence=0.0,
                probability_distribution={Action.FOLD: 1.0}
            )
        
        try:
            # Extract features
            feature_vector = self.feature_engineering.extract_features(
                hand_history, player_stats, game_context
            )
            features_scaled = self.feature_scaler.transform([feature_vector])
            
            # Get prediction
            prediction = self.model.predict(features_scaled)[0]
            prediction_proba = self.model.predict_proba(features_scaled)[0]
            
            # Convert to Action enum
            predicted_action = Action(prediction)
            confidence = max(prediction_proba)
            
            # Build probability distribution
            classes = self.model.classes_
            prob_dist = {}
            for i, class_name in enumerate(classes):
                try:
                    action = Action(class_name)
                    prob_dist[action] = prediction_proba[i]
                except ValueError:
                    continue
            
            return ModelPrediction(
                player_id=self.player_id,
                predicted_action=predicted_action,
                confidence=confidence,
                probability_distribution=prob_dist,
                features_used=dict(zip(self.feature_engineering.feature_names, feature_vector)),
                model_version=self.version
            )
            
        except Exception as e:
            logger.error(f"Prediction failed for {self.player_id}: {e}")
            return ModelPrediction(
                player_id=self.player_id,
                predicted_action=Action.FOLD,
                confidence=0.0
            )

class NeuralNetworkOpponentModel(OpponentModel):
    """Neural Network-based opponent model using TensorFlow."""
    
    def __init__(self, player_id: str):
        super().__init__(ModelType.NEURAL_NETWORK, player_id)
        self.feature_engineering = FeatureEngineering()
        self.label_encoder = LabelEncoder()
        
        if ML_DEEP_AVAILABLE:
            self._build_model()
    
    def _build_model(self):
        """Build neural network architecture."""
        if not tf:
            return
        
        input_dim = len(self.feature_engineering.feature_names)
        
        self.model = models.Sequential([
            layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(len(Action), activation='softmax')  # Output for each action
        ])
        
        self.model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
    
    def train(self, training_data: List[HandHistory], player_stats: PlayerStats) -> bool:
        """Train neural network model."""
        if not ML_DEEP_AVAILABLE:
            logger.error("TensorFlow not available for Neural Network model")
            return False
        
        if len(training_data) < 50:
            logger.warning(f"Insufficient training data: {len(training_data)} hands")
            return False
        
        try:
            # Extract features and labels
            features = []
            labels = []
            
            for hand in training_data:
                game_context = {'to_call': 5.0}
                
                feature_vector = self.feature_engineering.extract_features(
                    hand, player_stats, game_context
                )
                features.append(feature_vector)
                
                if hand.actions:
                    last_action = hand.actions[-1][1]
                    labels.append(last_action.value)
                else:
                    labels.append(Action.FOLD.value)
            
            features = np.array(features)
            labels = np.array(labels)
            
            # Encode labels
            labels_encoded = self.label_encoder.fit_transform(labels)
            
            # Scale features
            features_scaled = self.feature_scaler.fit_transform(features)
            
            # Train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, labels_encoded, test_size=0.2, random_state=42
            )
            
            # Callbacks
            early_stopping = callbacks.EarlyStopping(
                patience=10, restore_best_weights=True
            )
            
            # Train model
            history = self.model.fit(
                X_train, y_train,
                epochs=100,
                batch_size=32,
                validation_split=0.2,
                callbacks=[early_stopping],
                verbose=0
            )
            
            # Evaluate
            test_loss, test_acc = self.model.evaluate(X_test, y_test, verbose=0)
            
            self.is_trained = True
            self.last_updated = time.time()
            self.training_history.append({
                'timestamp': time.time(),
                'test_accuracy': test_acc,
                'test_loss': test_loss,
                'epochs_trained': len(history.history['loss'])
            })
            
            logger.info(f"Neural network trained for {self.player_id}: "
                       f"Test Accuracy = {test_acc:.3f}, Test Loss = {test_loss:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Neural network training failed for {self.player_id}: {e}")
            return False
    
    def predict(self, hand_history: HandHistory, player_stats: PlayerStats, 
                game_context: Dict[str, Any]) -> ModelPrediction:
        """Make prediction using neural network."""
        if not self.is_trained:
            return ModelPrediction(
                player_id=self.player_id,
                predicted_action=Action.FOLD,
                confidence=0.0
            )
        
        try:
            # Extract features
            feature_vector = self.feature_engineering.extract_features(
                hand_history, player_stats, game_context
            )
            features_scaled = self.feature_scaler.transform([feature_vector])
            
            # Get prediction
            predictions = self.model.predict(features_scaled, verbose=0)[0]
            predicted_class = np.argmax(predictions)
            confidence = predictions[predicted_class]
            
            # Convert to Action
            action_label = self.label_encoder.inverse_transform([predicted_class])[0]
            predicted_action = Action(action_label)
            
            # Build probability distribution
            prob_dist = {}
            for i, prob in enumerate(predictions):
                try:
                    label = self.label_encoder.inverse_transform([i])[0]
                    action = Action(label)
                    prob_dist[action] = float(prob)
                except (ValueError, IndexError):
                    continue
            
            return ModelPrediction(
                player_id=self.player_id,
                predicted_action=predicted_action,
                confidence=float(confidence),
                probability_distribution=prob_dist,
                features_used=dict(zip(self.feature_engineering.feature_names, feature_vector)),
                model_version=self.version
            )
            
        except Exception as e:
            logger.error(f"Neural network prediction failed for {self.player_id}: {e}")
            return ModelPrediction(
                player_id=self.player_id,
                predicted_action=Action.FOLD,
                confidence=0.0
            )

class OpponentModelingSystem:
    """
    Central system for managing opponent models.
    Handles model creation, training, prediction, and versioning.
    """
    
    def __init__(self, models_dir: str = None):
        self.models_dir = Path(models_dir) if models_dir else Path(__file__).parent / "opponent_models"
        self.models_dir.mkdir(exist_ok=True)
        
        self.player_models: Dict[str, OpponentModel] = {}
        self.player_stats: Dict[str, PlayerStats] = {}
        self.hand_histories: Dict[str, List[HandHistory]] = {}
        
        self.thread_pool = get_thread_pool()
        
        # System parameters
        self.min_hands_for_training = 30
        self.retrain_interval = 3600  # 1 hour
        self.max_history_length = 1000
        
        logger.info(f"Opponent modeling system initialized: {self.models_dir}")
    
    def observe_hand(self, hand_history: HandHistory):
        """Observe a new hand and update player statistics."""
        player_id = hand_history.player_id
        
        # Initialize player if not seen before
        if player_id not in self.player_stats:
            self.player_stats[player_id] = PlayerStats(player_id=player_id)
            self.hand_histories[player_id] = []
        
        # Add to hand history
        self.hand_histories[player_id].append(hand_history)
        
        # Limit history length
        if len(self.hand_histories[player_id]) > self.max_history_length:
            self.hand_histories[player_id] = self.hand_histories[player_id][-self.max_history_length:]
        
        # Update player statistics
        self._update_player_stats(player_id, hand_history)
        
        # Check if model needs retraining
        if self._should_retrain_model(player_id):
            self.thread_pool.submit_priority_task(
                self._retrain_player_model,
                player_id,
                priority=TaskPriority.NORMAL
            )
    
    def _update_player_stats(self, player_id: str, hand_history: HandHistory):
        """Update statistical profile of a player."""
        stats = self.player_stats[player_id]
        stats.hands_observed += 1
        
        # Update VPIP (voluntarily put money in pot)
        if any(action in [Action.CALL, Action.BET, Action.RAISE] 
               for _, action, _ in hand_history.actions):
            vpip_count = sum(1 for h in self.hand_histories[player_id][-100:]
                           if any(action in [Action.CALL, Action.BET, Action.RAISE] 
                                 for _, action, _ in h.actions))
            stats.vpip = vpip_count / min(len(self.hand_histories[player_id]), 100)
        
        # Update PFR (preflop raise)
        preflop_raises = sum(1 for h in self.hand_histories[player_id][-100:]
                           if any(street == 'preflop' and action in [Action.BET, Action.RAISE]
                                 for street, action, _ in h.actions))
        stats.pfr = preflop_raises / min(len(self.hand_histories[player_id]), 100)
        
        # Update aggression factor
        aggressive_actions = sum(1 for _, action, _ in hand_history.actions
                               if action in [Action.BET, Action.RAISE])
        passive_actions = sum(1 for _, action, _ in hand_history.actions
                            if action in [Action.CALL, Action.CHECK])
        
        if passive_actions > 0:
            hand_aggression = aggressive_actions / passive_actions
            # Moving average of aggression factor
            stats.aggression_factor = (stats.aggression_factor * 0.9 + hand_aggression * 0.1)
        
        # Update position statistics
        if hand_history.position not in stats.position_stats:
            stats.position_stats[hand_history.position] = {
                'frequency': 0.0, 'vpip': 0.0, 'pfr': 0.0
            }
        
        # Update other statistics
        if hand_history.showdown:
            stats.showdown_frequency = (stats.showdown_frequency * 0.9 + 1.0 * 0.1)
            if hand_history.won:
                stats.win_rate_at_showdown = (stats.win_rate_at_showdown * 0.9 + 1.0 * 0.1)
        
        stats.avg_pot_size = (stats.avg_pot_size * 0.9 + hand_history.pot_size * 0.1)
        stats.last_updated = time.time()
    
    def _should_retrain_model(self, player_id: str) -> bool:
        """Check if model should be retrained."""
        if player_id not in self.player_models:
            return len(self.hand_histories[player_id]) >= self.min_hands_for_training
        
        model = self.player_models[player_id]
        time_since_update = time.time() - model.last_updated
        hands_since_training = len(self.hand_histories[player_id])
        
        return (time_since_update > self.retrain_interval and 
                hands_since_training >= self.min_hands_for_training)
    
    def _retrain_player_model(self, player_id: str):
        """Retrain model for a specific player."""
        try:
            player_stats = self.player_stats[player_id]
            training_data = self.hand_histories[player_id]
            
            # Create or get existing model
            if player_id not in self.player_models:
                # Choose model type based on data size and ML availability
                if ML_DEEP_AVAILABLE and len(training_data) >= 100:
                    self.player_models[player_id] = NeuralNetworkOpponentModel(player_id)
                elif ML_SKLEARN_AVAILABLE:
                    self.player_models[player_id] = RandomForestOpponentModel(player_id)
                else:
                    logger.warning(f"No ML libraries available for {player_id}")
                    return
            
            model = self.player_models[player_id]
            
            # Train model
            if model.train(training_data, player_stats):
                # Save trained model
                model_path = self.models_dir / f"{player_id}_{model.model_type.value}.pkl"
                model.save_model(str(model_path))
                logger.info(f"Model retrained and saved for {player_id}")
            
        except Exception as e:
            logger.error(f"Model retraining failed for {player_id}: {e}")
    
    def predict_opponent_action(self, player_id: str, hand_history: HandHistory, 
                              game_context: Dict[str, Any]) -> ModelPrediction:
        """Predict opponent's next action."""
        if player_id not in self.player_stats:
            # Return default prediction for unknown player
            return ModelPrediction(
                player_id=player_id,
                predicted_action=Action.FOLD,
                confidence=0.0,
                probability_distribution={Action.FOLD: 1.0}
            )
        
        player_stats = self.player_stats[player_id]
        
        # If model exists, use it
        if player_id in self.player_models:
            model = self.player_models[player_id]
            return model.predict(hand_history, player_stats, game_context)
        
        # Otherwise, use statistical prediction
        return self._statistical_prediction(player_id, hand_history, player_stats, game_context)
    
    def _statistical_prediction(self, player_id: str, hand_history: HandHistory,
                               player_stats: PlayerStats, game_context: Dict[str, Any]) -> ModelPrediction:
        """Make prediction based on statistical profile."""
        # Simple statistical prediction based on player type
        player_type = player_stats.get_player_type()
        
        prob_dist = {}
        
        if player_type == PlayerType.TIGHT_PASSIVE:
            prob_dist = {Action.FOLD: 0.6, Action.CALL: 0.3, Action.CHECK: 0.1}
        elif player_type == PlayerType.TIGHT_AGGRESSIVE:
            prob_dist = {Action.FOLD: 0.4, Action.BET: 0.3, Action.RAISE: 0.2, Action.CALL: 0.1}
        elif player_type == PlayerType.LOOSE_PASSIVE:
            prob_dist = {Action.CALL: 0.5, Action.CHECK: 0.3, Action.FOLD: 0.2}
        elif player_type == PlayerType.LOOSE_AGGRESSIVE:
            prob_dist = {Action.BET: 0.3, Action.RAISE: 0.3, Action.CALL: 0.2, Action.FOLD: 0.2}
        else:
            # Unknown or default
            prob_dist = {Action.FOLD: 0.4, Action.CALL: 0.3, Action.CHECK: 0.2, Action.BET: 0.1}
        
        # Adjust based on pot odds
        pot_odds = game_context.get('pot_odds', 3.0)
        if pot_odds < 2:  # Good pot odds
            prob_dist[Action.CALL] = prob_dist.get(Action.CALL, 0) + 0.1
            prob_dist[Action.FOLD] = prob_dist.get(Action.FOLD, 0) - 0.1
        
        # Normalize probabilities
        total_prob = sum(prob_dist.values())
        if total_prob > 0:
            prob_dist = {action: prob/total_prob for action, prob in prob_dist.items()}
        
        # Get dominant action
        predicted_action = max(prob_dist, key=prob_dist.get)
        confidence = prob_dist[predicted_action]
        
        return ModelPrediction(
            player_id=player_id,
            predicted_action=predicted_action,
            confidence=confidence,
            probability_distribution=prob_dist,
            model_version='statistical'
        )
    
    def get_player_profile(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive player profile."""
        if player_id not in self.player_stats:
            return None
        
        stats = self.player_stats[player_id]
        player_type = stats.get_player_type()
        
        has_model = player_id in self.player_models
        model_info = {}
        if has_model:
            model = self.player_models[player_id]
            model_info = {
                'model_type': model.model_type.value,
                'is_trained': model.is_trained,
                'version': model.version,
                'last_updated': model.last_updated
            }
        
        return {
            'player_id': player_id,
            'player_type': player_type.value,
            'statistics': {
                'hands_observed': stats.hands_observed,
                'vpip': stats.vpip,
                'pfr': stats.pfr,
                'aggression_factor': stats.aggression_factor,
                'cbet_frequency': stats.cbet_frequency,
                'showdown_frequency': stats.showdown_frequency,
                'win_rate_at_showdown': stats.win_rate_at_showdown,
                'avg_pot_size': stats.avg_pot_size
            },
            'model_info': model_info,
            'last_updated': stats.last_updated,
            'hands_in_history': len(self.hand_histories.get(player_id, []))
        }
    
    def export_player_data(self, player_id: str, filepath: str) -> bool:
        """Export player data to file."""
        try:
            profile = self.get_player_profile(player_id)
            if not profile:
                return False
            
            # Add hand histories
            profile['hand_histories'] = [
                {
                    'hand_id': h.hand_id,
                    'position': h.position,
                    'board': h.board,
                    'actions': [(street, action.value, amount) for street, action, amount in h.actions],
                    'pot_size': h.pot_size,
                    'stack_size': h.stack_size,
                    'result': h.result,
                    'showdown': h.showdown,
                    'won': h.won,
                    'timestamp': h.timestamp
                } for h in self.hand_histories.get(player_id, [])
            ]
            
            with open(filepath, 'w') as f:
                json.dump(profile, f, indent=2, default=str)
            
            logger.info(f"Player data exported for {player_id}: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export player data for {player_id}: {e}")
            return False
    
    def load_models(self):
        """Load all saved models from disk."""
        try:
            for model_file in self.models_dir.glob("*.pkl"):
                try:
                    # Extract player ID from filename
                    filename = model_file.stem
                    player_id = filename.split('_')[0]
                    
                    # Determine model type
                    if 'neural_network' in filename:
                        model = NeuralNetworkOpponentModel(player_id)
                    elif 'random_forest' in filename:
                        model = RandomForestOpponentModel(player_id)
                    else:
                        continue
                    
                    if model.load_model(str(model_file)):
                        self.player_models[player_id] = model
                        logger.debug(f"Loaded model for {player_id}")
                
                except Exception as e:
                    logger.warning(f"Failed to load model {model_file}: {e}")
            
            logger.info(f"Loaded {len(self.player_models)} opponent models")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        total_players = len(self.player_stats)
        total_models = len(self.player_models)
        total_hands = sum(len(histories) for histories in self.hand_histories.values())
        
        model_types = {}
        for model in self.player_models.values():
            model_type = model.model_type.value
            model_types[model_type] = model_types.get(model_type, 0) + 1
        
        player_types = {}
        for stats in self.player_stats.values():
            player_type = stats.get_player_type().value
            player_types[player_type] = player_types.get(player_type, 0) + 1
        
        return {
            'total_players_observed': total_players,
            'total_models_trained': total_models,
            'total_hands_observed': total_hands,
            'model_type_distribution': model_types,
            'player_type_distribution': player_types,
            'ml_libraries_available': {
                'sklearn': ML_SKLEARN_AVAILABLE,
                'tensorflow': ML_DEEP_AVAILABLE
            }
        }

# Global opponent modeling system
_opponent_modeling_system: Optional[OpponentModelingSystem] = None

def get_opponent_modeling_system() -> OpponentModelingSystem:
    """Get the global opponent modeling system."""
    global _opponent_modeling_system
    if _opponent_modeling_system is None:
        _opponent_modeling_system = OpponentModelingSystem()
        _opponent_modeling_system.load_models()
    return _opponent_modeling_system

# Convenience functions
def observe_opponent_hand(player_id: str, hand_data: Dict[str, Any]) -> bool:
    """Convenience function to observe opponent hand."""
    try:
        system = get_opponent_modeling_system()
        
        # Convert hand data to HandHistory
        hand_history = HandHistory(
            hand_id=hand_data.get('hand_id', f"hand_{int(time.time())}"),
            player_id=player_id,
            position=hand_data.get('position', 'UTG'),
            hole_cards=hand_data.get('hole_cards'),
            board=hand_data.get('board', []),
            actions=[(street, Action(action), amount) for street, action, amount in hand_data.get('actions', [])],
            pot_size=hand_data.get('pot_size', 0),
            stack_size=hand_data.get('stack_size', 100),
            num_players=hand_data.get('num_players', 2),
            result=hand_data.get('result', 'unknown'),
            showdown=hand_data.get('showdown', False),
            won=hand_data.get('won', False),
            amount_won=hand_data.get('amount_won', 0.0)
        )
        
        system.observe_hand(hand_history)
        return True
        
    except Exception as e:
        logger.error(f"Failed to observe opponent hand for {player_id}: {e}")
        return False

def predict_opponent_action(player_id: str, game_context: Dict[str, Any]) -> ModelPrediction:
    """Convenience function to predict opponent action."""
    system = get_opponent_modeling_system()
    
    # Create simplified hand history for prediction
    hand_history = HandHistory(
        hand_id=f"prediction_{int(time.time())}",
        player_id=player_id,
        position=game_context.get('position', 'UTG'),
        board=game_context.get('board', []),
        pot_size=game_context.get('pot_size', 10),
        stack_size=game_context.get('stack_size', 100),
        num_players=game_context.get('num_players', 2)
    )
    
    return system.predict_opponent_action(player_id, hand_history, game_context)

def get_opponent_profile(player_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get opponent profile."""
    system = get_opponent_modeling_system()
    return system.get_player_profile(player_id)

def analyze_table_dynamics(player_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze overall table dynamics based on player profiles."""
    if not player_profiles:
        return {'table_type': 'unknown', 'avg_vpip': 0.0, 'avg_aggression': 0.0}
    
    total_vpip = sum(p['statistics']['vpip'] for p in player_profiles)
    total_aggression = sum(p['statistics']['aggression_factor'] for p in player_profiles)
    avg_vpip = total_vpip / len(player_profiles)
    avg_aggression = total_aggression / len(player_profiles)
    
    # Classify table
    if avg_vpip < 0.2 and avg_aggression < 2:
        table_type = 'tight_passive'
    elif avg_vpip < 0.2 and avg_aggression >= 2:
        table_type = 'tight_aggressive'
    elif avg_vpip >= 0.2 and avg_aggression < 2:
        table_type = 'loose_passive'
    else:
        table_type = 'loose_aggressive'
    
    # Player type distribution
    player_types = [p['player_type'] for p in player_profiles]
    type_distribution = {ptype: player_types.count(ptype) for ptype in set(player_types)}
    
    return {
        'table_type': table_type,
        'avg_vpip': avg_vpip,
        'avg_aggression': avg_aggression,
        'num_players': len(player_profiles),
        'player_type_distribution': type_distribution,
        'recommendations': _generate_table_recommendations(table_type, avg_vpip, avg_aggression)
    }

def _generate_table_recommendations(table_type: str, avg_vpip: float, avg_aggression: float) -> List[str]:
    """Generate recommendations based on table dynamics."""
    recommendations = []
    
    if table_type == 'tight_passive':
        recommendations.extend([
            "Table is tight-passive. Consider stealing more blinds.",
            "Value bet thinly - opponents will call with weak hands.",
            "Avoid bluffing too much - opponents fold easily."
        ])
    elif table_type == 'tight_aggressive':
        recommendations.extend([
            "Table is tight-aggressive. Be selective with starting hands.",
            "Expect more 3-betting. Adjust ranges accordingly.",
            "Look for spots to play back against aggressive players."
        ])
    elif table_type == 'loose_passive':
        recommendations.extend([
            "Table is loose-passive. Value bet heavily.",
            "Avoid bluffing - calling stations everywhere.",
            "Play tight and wait for strong hands."
        ])
    else:  # loose_aggressive
        recommendations.extend([
            "Table is loose-aggressive. Expect high variance.",
            "Tighten up preflop ranges.",
            "Be prepared for big swings and 4-bet wars."
        ])
    
    if avg_vpip > 0.35:
        recommendations.append("High VPIP table - tighten up and value bet more.")
    
    if avg_aggression > 4:
        recommendations.append("Very aggressive table - consider more defensive plays.")
    
    return recommendations

if __name__ == '__main__':
    # Test ML opponent modeling
    print("Testing ML Opponent Modeling System...")
    print(f"Scikit-learn available: {ML_SKLEARN_AVAILABLE}")
    print(f"TensorFlow available: {ML_DEEP_AVAILABLE}")
    
    # Initialize system
    system = get_opponent_modeling_system()
    
    # Test observing hands
    test_hand_data = {
        'hand_id': 'test_hand_1',
        'position': 'BTN',
        'board': ['Ah', 'Kc', 'Qh'],
        'actions': [('preflop', 'raise', 3), ('flop', 'bet', 5)],
        'pot_size': 15,
        'stack_size': 100,
        'result': 'won',
        'showdown': True,
        'won': True
    }
    
    observe_opponent_hand('test_player_1', test_hand_data)
    
    # Test prediction
    game_context = {
        'position': 'BTN',
        'board': ['Ah', 'Kc', 'Qh'],
        'pot_size': 20,
        'to_call': 5,
        'stack_size': 95
    }
    
    prediction = predict_opponent_action('test_player_1', game_context)
    print(f"Prediction: {prediction.predicted_action.value} (confidence: {prediction.confidence:.2f})")
    
    # Test system stats
    stats = system.get_system_stats()
    print(f"System stats: {stats}")
    
    print("ML Opponent Modeling test completed!")
