"""
Ensemble Decision System

Combines multiple decision engines with weighted voting, confidence-based weighting,
disagreement resolution, adaptive weights, and performance tracking.

ID: ENSEMBLE-001
Status: COMPLETED
Priority: MEDIUM
"""

import json
import time
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum


class DecisionType(Enum):
    """Types of decisions that can be made."""
    ACTION = "action"
    RANGE = "range"
    BET_SIZE = "bet_size"
    EQUITY = "equity"
    STRATEGY = "strategy"


@dataclass
class EngineDecision:
    """A decision from a single engine."""
    engine_name: str
    decision_type: DecisionType
    value: Any
    confidence: float  # 0.0-1.0
    reasoning: Optional[str] = None
    computation_time_ms: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'engine_name': self.engine_name,
            'decision_type': self.decision_type.value,
            'value': self.value,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'computation_time_ms': self.computation_time_ms,
            'metadata': self.metadata or {}
        }


@dataclass
class EnsembleDecision:
    """Final ensemble decision combining multiple engines."""
    decision_type: DecisionType
    value: Any
    confidence: float
    contributing_engines: List[str]
    disagreement_level: float  # 0.0-1.0
    method: str  # 'weighted_vote', 'confidence_based', etc.
    individual_decisions: List[EngineDecision]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'decision_type': self.decision_type.value,
            'value': self.value,
            'confidence': self.confidence,
            'contributing_engines': self.contributing_engines,
            'disagreement_level': self.disagreement_level,
            'method': self.method,
            'individual_decisions': [d.to_dict() for d in self.individual_decisions],
            'metadata': self.metadata
        }


class WeightOptimizer:
    """Optimizes engine weights based on performance history."""
    
    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.engine_weights: Dict[str, float] = {}
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.max_history = 100
    
    def initialize_weights(self, engine_names: List[str]) -> None:
        """Initialize equal weights for all engines."""
        initial_weight = 1.0 / len(engine_names)
        for name in engine_names:
            self.engine_weights[name] = initial_weight
    
    def get_weight(self, engine_name: str) -> float:
        """Get weight for an engine."""
        return self.engine_weights.get(engine_name, 0.5)
    
    def update_weight(self, engine_name: str, performance_score: float) -> None:
        """
        Update engine weight based on performance.
        
        Args:
            engine_name: Name of the engine
            performance_score: Score between 0.0 (bad) and 1.0 (good)
        """
        # Record performance
        self.performance_history[engine_name].append(performance_score)
        if len(self.performance_history[engine_name]) > self.max_history:
            self.performance_history[engine_name].pop(0)
        
        # Calculate average recent performance
        recent_performance = sum(self.performance_history[engine_name][-10:]) / \
                           min(10, len(self.performance_history[engine_name]))
        
        # Update weight with learning rate
        current_weight = self.engine_weights.get(engine_name, 0.5)
        target_weight = recent_performance
        new_weight = current_weight + self.learning_rate * (target_weight - current_weight)
        
        # Clamp to valid range
        self.engine_weights[engine_name] = max(0.1, min(1.0, new_weight))
        
        # Normalize all weights
        self._normalize_weights()
    
    def _normalize_weights(self) -> None:
        """Normalize weights to sum to 1.0."""
        total = sum(self.engine_weights.values())
        if total > 0:
            for name in self.engine_weights:
                self.engine_weights[name] /= total
    
    def get_all_weights(self) -> Dict[str, float]:
        """Get all engine weights."""
        return self.engine_weights.copy()
    
    def get_performance_stats(self, engine_name: str) -> Dict[str, Any]:
        """Get performance statistics for an engine."""
        history = self.performance_history[engine_name]
        if not history:
            return {
                'average': 0.5,
                'recent_average': 0.5,
                'sample_count': 0
            }
        
        return {
            'average': sum(history) / len(history),
            'recent_average': sum(history[-10:]) / min(10, len(history)),
            'sample_count': len(history)
        }


class DisagreementResolver:
    """Resolves disagreements between engines."""
    
    def __init__(self):
        self.resolution_methods = {
            'highest_confidence': self._resolve_by_confidence,
            'weighted_vote': self._resolve_by_weighted_vote,
            'majority_vote': self._resolve_by_majority,
            'average': self._resolve_by_average
        }
    
    def calculate_disagreement(self, decisions: List[EngineDecision]) -> float:
        """
        Calculate disagreement level among decisions.
        
        Returns:
            Float between 0.0 (full agreement) and 1.0 (complete disagreement)
        """
        if len(decisions) <= 1:
            return 0.0
        
        # For categorical decisions, check uniqueness
        if decisions[0].decision_type in [DecisionType.ACTION, DecisionType.STRATEGY]:
            unique_values = len(set(d.value for d in decisions))
            return (unique_values - 1) / (len(decisions) - 1)
        
        # For numerical decisions, use variance
        values = [float(d.value) if isinstance(d.value, (int, float)) else 0.5 
                 for d in decisions]
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        
        # Normalize variance to 0-1 range (assuming reasonable value ranges)
        return min(1.0, variance * 4)  # Scale factor of 4 for typical ranges
    
    def resolve(self, decisions: List[EngineDecision],
               method: str,
               weights: Optional[Dict[str, float]] = None) -> Tuple[Any, float]:
        """
        Resolve disagreement between decisions.
        
        Args:
            decisions: List of engine decisions
            method: Resolution method to use
            weights: Optional engine weights
            
        Returns:
            Tuple of (resolved_value, confidence)
        """
        if not decisions:
            return None, 0.0
        
        if len(decisions) == 1:
            return decisions[0].value, decisions[0].confidence
        
        resolver = self.resolution_methods.get(method, self._resolve_by_confidence)
        return resolver(decisions, weights)
    
    def _resolve_by_confidence(self, decisions: List[EngineDecision],
                               weights: Optional[Dict[str, float]]) -> Tuple[Any, float]:
        """Choose decision with highest confidence."""
        best = max(decisions, key=lambda d: d.confidence)
        return best.value, best.confidence
    
    def _resolve_by_weighted_vote(self, decisions: List[EngineDecision],
                                  weights: Optional[Dict[str, float]]) -> Tuple[Any, float]:
        """Use weighted voting based on engine weights and confidence."""
        if weights is None:
            weights = {d.engine_name: 1.0 for d in decisions}
        
        # For categorical decisions
        if decisions[0].decision_type in [DecisionType.ACTION, DecisionType.STRATEGY]:
            vote_counts: Dict[Any, float] = defaultdict(float)
            
            for decision in decisions:
                weight = weights.get(decision.engine_name, 1.0)
                vote_counts[decision.value] += weight * decision.confidence
            
            best_value = max(vote_counts.items(), key=lambda x: x[1])[0]
            total_weight = sum(vote_counts.values())
            confidence = vote_counts[best_value] / total_weight if total_weight > 0 else 0.5
            
            return best_value, confidence
        
        # For numerical decisions, use weighted average
        return self._resolve_by_average(decisions, weights)
    
    def _resolve_by_majority(self, decisions: List[EngineDecision],
                            weights: Optional[Dict[str, float]]) -> Tuple[Any, float]:
        """Use simple majority vote."""
        vote_counts: Dict[Any, int] = defaultdict(int)
        
        for decision in decisions:
            vote_counts[decision.value] += 1
        
        best_value = max(vote_counts.items(), key=lambda x: x[1])[0]
        confidence = vote_counts[best_value] / len(decisions)
        
        return best_value, confidence
    
    def _resolve_by_average(self, decisions: List[EngineDecision],
                           weights: Optional[Dict[str, float]]) -> Tuple[Any, float]:
        """Use weighted average for numerical decisions."""
        if weights is None:
            weights = {d.engine_name: 1.0 for d in decisions}
        
        total_weighted_value = 0.0
        total_weight = 0.0
        
        for decision in decisions:
            weight = weights.get(decision.engine_name, 1.0)
            weighted_value = weight * decision.confidence
            
            if isinstance(decision.value, (int, float)):
                total_weighted_value += decision.value * weighted_value
                total_weight += weighted_value
        
        if total_weight == 0:
            return decisions[0].value, 0.5
        
        avg_value = total_weighted_value / total_weight
        avg_confidence = total_weight / sum(weights.get(d.engine_name, 1.0) 
                                           for d in decisions)
        
        return avg_value, min(1.0, avg_confidence)


class PerformanceTracker:
    """Tracks performance of ensemble and individual engines."""
    
    def __init__(self):
        self.ensemble_results: List[Dict[str, Any]] = []
        self.engine_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.max_history = 1000
    
    def record_result(self, ensemble_decision: EnsembleDecision,
                     actual_outcome: Optional[float] = None) -> None:
        """
        Record the result of an ensemble decision.
        
        Args:
            ensemble_decision: The ensemble decision made
            actual_outcome: Optional actual outcome (for performance evaluation)
        """
        result = {
            'timestamp': time.time(),
            'decision': ensemble_decision.to_dict(),
            'actual_outcome': actual_outcome
        }
        
        self.ensemble_results.append(result)
        if len(self.ensemble_results) > self.max_history:
            self.ensemble_results.pop(0)
        
        # Track individual engine results
        for decision in ensemble_decision.individual_decisions:
            engine_result = {
                'timestamp': time.time(),
                'decision': decision.to_dict(),
                'actual_outcome': actual_outcome
            }
            self.engine_results[decision.engine_name].append(engine_result)
            if len(self.engine_results[decision.engine_name]) > self.max_history:
                self.engine_results[decision.engine_name].pop(0)
    
    def get_ensemble_stats(self) -> Dict[str, Any]:
        """Get ensemble performance statistics."""
        if not self.ensemble_results:
            return {
                'total_decisions': 0,
                'average_confidence': 0.0,
                'average_disagreement': 0.0
            }
        
        confidences = [r['decision']['confidence'] for r in self.ensemble_results]
        disagreements = [r['decision']['disagreement_level'] for r in self.ensemble_results]
        
        return {
            'total_decisions': len(self.ensemble_results),
            'average_confidence': sum(confidences) / len(confidences),
            'average_disagreement': sum(disagreements) / len(disagreements),
            'recent_confidence': sum(confidences[-10:]) / min(10, len(confidences))
        }
    
    def get_engine_stats(self, engine_name: str) -> Dict[str, Any]:
        """Get statistics for a specific engine."""
        results = self.engine_results[engine_name]
        
        if not results:
            return {
                'total_decisions': 0,
                'average_confidence': 0.0
            }
        
        confidences = [r['decision']['confidence'] for r in results]
        
        return {
            'total_decisions': len(results),
            'average_confidence': sum(confidences) / len(confidences),
            'recent_confidence': sum(confidences[-10:]) / min(10, len(confidences))
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get all performance statistics."""
        return {
            'ensemble': self.get_ensemble_stats(),
            'engines': {name: self.get_engine_stats(name) 
                       for name in self.engine_results.keys()}
        }


class EnsembleDecisionSystem:
    """
    Main ensemble decision system.
    
    Combines multiple decision engines with weighted voting, confidence-based weighting,
    disagreement resolution, adaptive weights, and performance tracking.
    """
    
    def __init__(self, learning_rate: float = 0.1):
        self.engines: Dict[str, Callable] = {}
        self.weight_optimizer = WeightOptimizer(learning_rate=learning_rate)
        self.disagreement_resolver = DisagreementResolver()
        self.performance_tracker = PerformanceTracker()
        self.default_method = 'weighted_vote'
    
    def register_engine(self, name: str, engine_func: Callable) -> None:
        """
        Register a decision engine.
        
        Args:
            name: Name of the engine
            engine_func: Function that takes game_state and returns EngineDecision
        """
        self.engines[name] = engine_func
        
        # Initialize weight if needed
        if name not in self.weight_optimizer.engine_weights:
            all_names = list(self.engines.keys())
            self.weight_optimizer.initialize_weights(all_names)
    
    def unregister_engine(self, name: str) -> None:
        """Unregister an engine."""
        if name in self.engines:
            del self.engines[name]
            if name in self.weight_optimizer.engine_weights:
                del self.weight_optimizer.engine_weights[name]
                self.weight_optimizer._normalize_weights()
    
    def make_decision(self, game_state: Dict[str, Any],
                     decision_type: DecisionType,
                     method: Optional[str] = None,
                     min_confidence: float = 0.0) -> EnsembleDecision:
        """
        Make an ensemble decision.
        
        Args:
            game_state: Current game state
            decision_type: Type of decision to make
            method: Resolution method (None = use default)
            min_confidence: Minimum confidence threshold
            
        Returns:
            EnsembleDecision combining all engines
        """
        if not self.engines:
            raise ValueError("No engines registered")
        
        method = method or self.default_method
        
        # Collect decisions from all engines
        decisions: List[EngineDecision] = []
        for name, engine_func in self.engines.items():
            try:
                start_time = time.time()
                decision = engine_func(game_state, decision_type)
                decision.computation_time_ms = (time.time() - start_time) * 1000
                
                if decision.confidence >= min_confidence:
                    decisions.append(decision)
            except Exception as e:
                # Skip engines that fail
                print(f"Engine {name} failed: {e}")
                continue
        
        if not decisions:
            raise ValueError("No valid decisions from any engine")
        
        # Calculate disagreement level
        disagreement = self.disagreement_resolver.calculate_disagreement(decisions)
        
        # Resolve disagreement
        weights = self.weight_optimizer.get_all_weights()
        final_value, final_confidence = self.disagreement_resolver.resolve(
            decisions, method, weights
        )
        
        # Create ensemble decision
        ensemble_decision = EnsembleDecision(
            decision_type=decision_type,
            value=final_value,
            confidence=final_confidence,
            contributing_engines=[d.engine_name for d in decisions],
            disagreement_level=disagreement,
            method=method,
            individual_decisions=decisions,
            metadata={
                'weights_used': weights,
                'total_engines': len(self.engines),
                'participating_engines': len(decisions)
            }
        )
        
        # Track performance
        self.performance_tracker.record_result(ensemble_decision)
        
        return ensemble_decision
    
    def update_performance(self, engine_name: str, performance_score: float) -> None:
        """
        Update engine performance and adapt weights.
        
        Args:
            engine_name: Name of the engine
            performance_score: Score between 0.0 and 1.0
        """
        self.weight_optimizer.update_weight(engine_name, performance_score)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            'performance': self.performance_tracker.get_all_stats(),
            'weights': self.weight_optimizer.get_all_weights(),
            'engine_performance': {
                name: self.weight_optimizer.get_performance_stats(name)
                for name in self.engines.keys()
            }
        }
    
    def get_engine_weights(self) -> Dict[str, float]:
        """Get current engine weights."""
        return self.weight_optimizer.get_all_weights()
    
    def set_engine_weight(self, engine_name: str, weight: float) -> None:
        """Manually set an engine weight."""
        if engine_name in self.engines:
            self.weight_optimizer.engine_weights[engine_name] = max(0.1, min(1.0, weight))
            self.weight_optimizer._normalize_weights()
    
    def set_default_method(self, method: str) -> None:
        """Set the default resolution method."""
        if method in self.disagreement_resolver.resolution_methods:
            self.default_method = method
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def export_state(self) -> Dict[str, Any]:
        """Export system state."""
        return {
            'weights': self.weight_optimizer.get_all_weights(),
            'performance_history': dict(self.weight_optimizer.performance_history),
            'default_method': self.default_method
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import system state."""
        if 'weights' in state:
            self.weight_optimizer.engine_weights = state['weights']
        if 'performance_history' in state:
            self.weight_optimizer.performance_history = defaultdict(
                list, state['performance_history']
            )
        if 'default_method' in state:
            self.default_method = state['default_method']


# Convenience functions
def create_ensemble(engine_configs: List[Dict[str, Any]],
                   learning_rate: float = 0.1) -> EnsembleDecisionSystem:
    """
    Create an ensemble system from engine configurations.
    
    Args:
        engine_configs: List of dicts with 'name' and 'function' keys
        learning_rate: Learning rate for weight adaptation
        
    Returns:
        Configured EnsembleDecisionSystem
    """
    ensemble = EnsembleDecisionSystem(learning_rate=learning_rate)
    
    for config in engine_configs:
        ensemble.register_engine(config['name'], config['function'])
    
    return ensemble
