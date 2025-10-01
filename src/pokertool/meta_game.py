"""
Meta-Game Optimizer

Meta-game theory optimal adjustments for poker strategy.
Handles leveling wars, dynamic strategy switching, exploitation vs protection balance,
history-dependent strategies, and reputation modeling.

ID: META-001
Priority: MEDIUM
Expected Accuracy Gain: 7-10% in regular games
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


class StrategyLevel(Enum):
    """Levels of strategic thinking"""
    LEVEL_0 = 0  # Basic play (unexploitable baseline)
    LEVEL_1 = 1  # Exploiting level 0
    LEVEL_2 = 2  # Counter-exploiting level 1
    LEVEL_3 = 3  # Counter-counter-exploiting level 2
    LEVEL_4 = 4  # Advanced meta-game


class PlayerReputation(Enum):
    """Player reputation types"""
    UNKNOWN = "unknown"
    TIGHT_PASSIVE = "tight_passive"
    TIGHT_AGGRESSIVE = "tight_aggressive"
    LOOSE_PASSIVE = "loose_passive"
    LOOSE_AGGRESSIVE = "loose_aggressive"
    BALANCED = "balanced"
    EXPLOITABLE = "exploitable"
    UNEXPLOITABLE = "unexploitable"


@dataclass
class MetaGameState:
    """Current state of the meta-game"""
    hero_level: StrategyLevel
    villain_level: StrategyLevel
    exploitation_score: float  # -1 to 1, negative = defensive, positive = exploitative
    history_weight: float  # How much to weight historical data
    reputation: PlayerReputation


@dataclass
class StrategyAdjustment:
    """Recommended strategy adjustment"""
    adjustment_type: str
    magnitude: float  # 0-1
    reasoning: str
    confidence: float  # 0-1
    expected_ev_gain: float


class LevelingWarSimulator:
    """Simulate leveling wars between players"""
    
    def __init__(self):
        self.level_matchups = self._initialize_matchups()
    
    def _initialize_matchups(self) -> Dict:
        """Initialize EV for different level matchups"""
        # EV from hero's perspective
        return {
            (StrategyLevel.LEVEL_0, StrategyLevel.LEVEL_0): 0.0,
            (StrategyLevel.LEVEL_0, StrategyLevel.LEVEL_1): -0.15,  # Level 1 exploits level 0
            (StrategyLevel.LEVEL_1, StrategyLevel.LEVEL_0): 0.15,
            (StrategyLevel.LEVEL_1, StrategyLevel.LEVEL_1): 0.0,
            (StrategyLevel.LEVEL_1, StrategyLevel.LEVEL_2): -0.10,
            (StrategyLevel.LEVEL_2, StrategyLevel.LEVEL_1): 0.10,
            (StrategyLevel.LEVEL_2, StrategyLevel.LEVEL_2): 0.0,
            (StrategyLevel.LEVEL_2, StrategyLevel.LEVEL_3): -0.08,
            (StrategyLevel.LEVEL_3, StrategyLevel.LEVEL_2): 0.08,
            (StrategyLevel.LEVEL_3, StrategyLevel.LEVEL_3): 0.0,
        }
    
    def simulate_matchup(self, hero_level: StrategyLevel,
                        villain_level: StrategyLevel) -> float:
        """Simulate EV of a level matchup"""
        key = (hero_level, villain_level)
        return self.level_matchups.get(key, 0.0)
    
    def find_optimal_level(self, estimated_villain_level: StrategyLevel) -> StrategyLevel:
        """Find optimal strategy level given villain's estimated level"""
        # Generally, play one level above opponent
        if estimated_villain_level == StrategyLevel.LEVEL_0:
            return StrategyLevel.LEVEL_1
        elif estimated_villain_level == StrategyLevel.LEVEL_1:
            return StrategyLevel.LEVEL_2
        elif estimated_villain_level == StrategyLevel.LEVEL_2:
            return StrategyLevel.LEVEL_3
        else:
            return StrategyLevel.LEVEL_3  # Cap at level 3
    
    def estimate_villain_level(self, villain_stats: Dict) -> StrategyLevel:
        """Estimate villain's strategic level from statistics"""
        # Simplified estimation based on key stats
        vpip = villain_stats.get('vpip', 25)
        pfr = villain_stats.get('pfr', 20)
        aggression = villain_stats.get('aggression', 1.0)
        fold_to_3bet = villain_stats.get('fold_to_3bet', 50)
        
        # Very basic players (level 0)
        if vpip > 40 or vpip < 15:
            return StrategyLevel.LEVEL_0
        
        # Standard players (level 1)
        if 20 < vpip < 30 and 15 < pfr < 25:
            if aggression < 1.5 or fold_to_3bet > 70:
                return StrategyLevel.LEVEL_1
        
        # Thinking players (level 2)
        if abs(vpip - pfr) < 8 and 1.5 < aggression < 3.0:
            return StrategyLevel.LEVEL_2
        
        # Advanced players (level 3+)
        if aggression > 2.5 and 50 < fold_to_3bet < 70:
            return StrategyLevel.LEVEL_3
        
        return StrategyLevel.LEVEL_1  # Default


class DynamicStrategySwit cher:
    """Dynamically switch between strategies"""
    
    def __init__(self):
        self.strategy_history = []
        self.performance_by_strategy = {}
    
    def select_strategy(self, game_state: MetaGameState,
                       available_strategies: List[str]) -> str:
        """Select optimal strategy for current state"""
        if not available_strategies:
            return "balanced"
        
        # If no history, start balanced
        if not self.performance_by_strategy:
            return "balanced"
        
        # Select strategy based on current exploitation score
        if game_state.exploitation_score > 0.5:
            # Heavy exploitation mode
            return self._select_exploitative_strategy(available_strategies)
        elif game_state.exploitation_score < -0.5:
            # Defensive mode
            return "defensive"
        else:
            # Balanced mode
            return "balanced"
    
    def _select_exploitative_strategy(self, strategies: List[str]) -> str:
        """Select best exploitative strategy"""
        exploitative = [s for s in strategies if 'exploit' in s.lower()]
        if exploitative:
            return exploitative[0]
        return strategies[0]
    
    def update_performance(self, strategy: str, result: float):
        """Update performance tracking for a strategy"""
        if strategy not in self.performance_by_strategy:
            self.performance_by_strategy[strategy] = []
        
        self.performance_by_strategy[strategy].append(result)
        self.strategy_history.append((strategy, result))
    
    def get_best_performing_strategy(self) -> Optional[str]:
        """Get strategy with best average performance"""
        if not self.performance_by_strategy:
            return None
        
        avg_performances = {
            strategy: sum(results) / len(results)
            for strategy, results in self.performance_by_strategy.items()
        }
        
        return max(avg_performances, key=avg_performances.get)


class ExploitationProtectionBalancer:
    """Balance between exploitation and protection"""
    
    def __init__(self):
        self.vulnerability_threshold = 0.3  # Threshold for switching to protection
    
    def calculate_balance_score(self, exploitation_opportunities: List[float],
                                vulnerability_risks: List[float]) -> float:
        """Calculate optimal exploitation/protection balance (-1 to 1)"""
        if not exploitation_opportunities or not vulnerability_risks:
            return 0.0  # Neutral
        
        avg_opportunity = sum(exploitation_opportunities) / len(exploitation_opportunities)
        avg_risk = sum(vulnerability_risks) / len(vulnerability_risks)
        
        # Balance = opportunity - risk
        balance = avg_opportunity - avg_risk
        
        # Normalize to -1 to 1
        return max(-1.0, min(1.0, balance))
    
    def recommend_adjustment(self, balance_score: float) -> StrategyAdjustment:
        """Recommend strategy adjustment based on balance"""
        if balance_score > 0.5:
            return StrategyAdjustment(
                adjustment_type="increase_exploitation",
                magnitude=balance_score,
                reasoning="High exploitation opportunities with low risk",
                confidence=0.8,
                expected_ev_gain=balance_score * 0.1
            )
        elif balance_score < -0.5:
            return StrategyAdjustment(
                adjustment_type="increase_protection",
                magnitude=abs(balance_score),
                reasoning="High vulnerability risk detected",
                confidence=0.8,
                expected_ev_gain=abs(balance_score) * 0.05
            )
        else:
            return StrategyAdjustment(
                adjustment_type="maintain_balance",
                magnitude=0.0,
                reasoning="Current balance is optimal",
                confidence=0.9,
                expected_ev_gain=0.0
            )
    
    def assess_vulnerability(self, player_stats: Dict) -> float:
        """Assess how vulnerable player is to exploitation"""
        vulnerabilities = []
        
        # Check for exploitable patterns
        if player_stats.get('fold_to_3bet', 50) > 75:
            vulnerabilities.append(0.8)  # Very exploitable
        
        if player_stats.get('cbet_frequency', 60) > 80:
            vulnerabilities.append(0.6)
        
        if player_stats.get('fold_to_cbet', 50) > 70:
            vulnerabilities.append(0.7)
        
        return sum(vulnerabilities) / len(vulnerabilities) if vulnerabilities else 0.0


class HistoryDependentStrategy:
    """Implement history-dependent strategic adjustments"""
    
    def __init__(self, memory_length: int = 100):
        self.memory_length = memory_length
        self.interaction_history = {}
    
    def record_interaction(self, opponent_id: str, situation: str, action: str, result: float):
        """Record an interaction with an opponent"""
        if opponent_id not in self.interaction_history:
            self.interaction_history[opponent_id] = []
        
        self.interaction_history[opponent_id].append({
            'situation': situation,
            'action': action,
            'result': result
        })
        
        # Trim to memory length
        if len(self.interaction_history[opponent_id]) > self.memory_length:
            self.interaction_history[opponent_id] = \
                self.interaction_history[opponent_id][-self.memory_length:]
    
    def get_situational_strategy(self, opponent_id: str, situation: str) -> Optional[str]:
        """Get strategy recommendation based on history with opponent"""
        if opponent_id not in self.interaction_history:
            return None
        
        # Find similar situations
        similar = [
            interaction for interaction in self.interaction_history[opponent_id]
            if interaction['situation'] == situation
        ]
        
        if not similar:
            return None
        
        # Find best performing action in this situation
        action_results = {}
        for interaction in similar:
            action = interaction['action']
            if action not in action_results:
                action_results[action] = []
            action_results[action].append(interaction['result'])
        
        # Calculate average result for each action
        avg_results = {
            action: sum(results) / len(results)
            for action, results in action_results.items()
        }
        
        return max(avg_results, key=avg_results.get) if avg_results else None


class ReputationModel:
    """Model and track player reputations"""
    
    def __init__(self):
        self.reputations: Dict[str, PlayerReputation] = {}
        self.reputation_data: Dict[str, Dict] = {}
    
    def build_reputation(self, player_id: str, stats: Dict) -> PlayerReputation:
        """Build reputation from player statistics"""
        vpip = stats.get('vpip', 25)
        pfr = stats.get('pfr', 20)
        aggression = stats.get('aggression', 1.0)
        
        # Classify based on stats
        is_tight = vpip < 23
        is_loose = vpip > 28
        is_passive = aggression < 1.2
        is_aggressive = aggression > 2.0
        
        if is_tight and is_passive:
            reputation = PlayerReputation.TIGHT_PASSIVE
        elif is_tight and is_aggressive:
            reputation = PlayerReputation.TIGHT_AGGRESSIVE
        elif is_loose and is_passive:
            reputation = PlayerReputation.LOOSE_PASSIVE
        elif is_loose and is_aggressive:
            reputation = PlayerReputation.LOOSE_AGGRESSIVE
        else:
            reputation = PlayerReputation.BALANCED
        
        self.reputations[player_id] = reputation
        self.reputation_data[player_id] = stats
        
        return reputation
    
    def get_reputation(self, player_id: str) -> PlayerReputation:
        """Get player's reputation"""
        return self.reputations.get(player_id, PlayerReputation.UNKNOWN)
    
    def get_exploitative_adjustments(self, reputation: PlayerReputation) -> List[str]:
        """Get exploitative adjustments for a reputation type"""
        adjustments = {
            PlayerReputation.TIGHT_PASSIVE: [
                "Increase bluff frequency",
                "Steal blinds more often",
                "Apply pressure with air"
            ],
            PlayerReputation.TIGHT_AGGRESSIVE: [
                "Tighten calling ranges",
                "Respect aggression",
                "Trap with strong hands"
            ],
            PlayerReputation.LOOSE_PASSIVE: [
                "Value bet thin",
                "Avoid bluffs",
                "Bet for value liberally"
            ],
            PlayerReputation.LOOSE_AGGRESSIVE: [
                "Call down lighter",
                "Trap more often",
                "Let them bluff"
            ],
            PlayerReputation.BALANCED: [
                "Play GTO",
                "Mix strategies",
                "Avoid exploitation"
            ]
        }
        
        return adjustments.get(reputation, ["Play standard strategy"])


class MetaGameOptimizer:
    """Main meta-game optimization engine"""
    
    def __init__(self):
        self.leveling_simulator = LevelingWarSimulator()
        self.strategy_switcher = DynamicStrategySwit cher()
        self.balance_calculator = ExploitationProtectionBalancer()
        self.history_strategy = HistoryDependentStrategy()
        self.reputation_model = ReputationModel()
    
    def optimize_strategy(self, game_context: Dict) -> Dict:
        """Optimize strategy for current game context"""
        opponent_id = game_context.get('opponent_id')
        opponent_stats = game_context.get('opponent_stats', {})
        
        # Estimate opponent level
        villain_level = self.leveling_simulator.estimate_villain_level(opponent_stats)
        hero_level = self.leveling_simulator.find_optimal_level(villain_level)
        
        # Build reputation
        reputation = self.reputation_model.build_reputation(opponent_id, opponent_stats)
        
        # Calculate exploitation/protection balance
        vulnerabilities = [self.balance_calculator.assess_vulnerability(opponent_stats)]
        opportunities = [0.7] if reputation != PlayerReputation.BALANCED else [0.3]
        balance_score = self.balance_calculator.calculate_balance_score(opportunities, vulnerabilities)
        
        # Get strategy adjustment
        adjustment = self.balance_calculator.recommend_adjustment(balance_score)
        
        # Get exploitative adjustments
        exploit_adjustments = self.reputation_model.get_exploitative_adjustments(reputation)
        
        return {
            'hero_level': hero_level.value,
            'villain_level': villain_level.value,
            'reputation': reputation.value,
            'exploitation_score': balance_score,
            'adjustment': {
                'type': adjustment.adjustment_type,
                'magnitude': adjustment.magnitude,
                'reasoning': adjustment.reasoning,
                'confidence': adjustment.confidence,
                'expected_ev_gain': adjustment.expected_ev_gain
            },
            'specific_adjustments': exploit_adjustments
        }
    
    def export_analysis(self, filepath: str):
        """Export meta-game analysis to JSON"""
        data = {
            'reputations': {
                player_id: rep.value
                for player_id, rep in self.reputation_model.reputations.items()
            },
            'reputation_data': self.reputation_model.reputation_data,
            'strategy_performance': self.strategy_switcher.performance_by_strategy
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
