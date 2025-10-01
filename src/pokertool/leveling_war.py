"""
Leveling War Module

Advanced leveling war analysis and simulation for poker meta-game.
Analyzes iterative strategic thinking between players.

Part of META-001: Meta-Game Optimizer
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json


class ThinkingLevel(Enum):
    """Levels of iterative thinking"""
    LEVEL_0 = "No strategic adjustment"
    LEVEL_1 = "First level thinking - what do they have?"
    LEVEL_2 = "Second level - what do they think I have?"
    LEVEL_3 = "Third level - what do they think I think they have?"
    LEVEL_4 = "Fourth level and beyond"


@dataclass
class LevelingOutcome:
    """Outcome of a leveling war analysis"""
    recommended_level: int
    reasoning: str
    confidence: float
    counter_strategies: List[str]
    risk_assessment: float


class LevelEstimator:
    """Estimate opponent's thinking level"""
    
    def __init__(self):
        self.level_indicators = self._initialize_indicators()
    
    def _initialize_indicators(self) -> Dict:
        """Initialize indicators for each level"""
        return {
            0: {
                'indicators': ['plays ABC poker', 'straightforward', 'no adjustments'],
                'stats_profile': {'consistency': 'high', 'exploitability': 'high'}
            },
            1: {
                'indicators': ['adjusts to opponents', 'exploits weaknesses', 'basic reads'],
                'stats_profile': {'consistency': 'medium', 'exploitability': 'medium'}
            },
            2: {
                'indicators': ['considers image', 'balances ranges', 'counter-exploitation'],
                'stats_profile': {'consistency': 'medium', 'exploitability': 'low'}
            },
            3: {
                'indicators': ['meta-game aware', 'history dependent', 'advanced theory'],
                'stats_profile': {'consistency': 'variable', 'exploit ability': 'very low'}
            }
        }
    
    def estimate_level(self, observations: List[str], stats: Dict) -> int:
        """Estimate opponent's thinking level"""
        scores = {0: 0, 1: 0, 2: 0, 3: 0}
        
        # Score based on observations
        for level, info in self.level_indicators.items():
            for indicator in info['indicators']:
                if any(indicator.lower() in obs.lower() for obs in observations):
                    scores[level] += 1
        
        # Adjust based on stats
        if stats.get('variance', 0) < 20:
            scores[0] += 2  # Low variance suggests level 0
        if stats.get('aggression', 1) > 2.5:
            scores[2] += 1  # High aggression suggests level 2+
        
        return max(scores, key=scores.get)


class StrategyEvolution:
    """Track evolution of strategies in leveling war"""
    
    def __init__(self):
        self.history = []
        self.convergence_threshold = 3
    
    def record_interaction(self, hero_action: str, villain_response: str, result: float):
        """Record an interaction in the leveling war"""
        self.history.append({
            'hero_action': hero_action,
            'villain_response': villain_response,
            'result': result
        })
    
    def detect_pattern(self) -> Optional[str]:
        """Detect if a pattern has emerged"""
        if len(self.history) < self.convergence_threshold:
            return None
        
        recent = self.history[-self.convergence_threshold:]
        
        # Check if villain consistently responds the same way
        responses = [h['villain_response'] for h in recent]
        if len(set(responses)) == 1:
            return f"Villain consistently responds with: {responses[0]}"
        
        return None
    
    def suggest_evolution(self) -> str:
        """Suggest how to evolve strategy"""
        pattern = self.detect_pattern()
        
        if pattern:
            return "Change strategy - opponent has adapted"
        
        if not self.history:
            return "Start with level 1 thinking"
        
        # Check recent success
        recent_results = [h['result'] for h in self.history[-5:]]
        avg_result = sum(recent_results) / len(recent_results) if recent_results else 0
        
        if avg_result > 0.5:
            return "Continue current strategy - working well"
        else:
            return "Escalate to next level - current strategy not optimal"


class CounterStrategyGenerator:
    """Generate counter-strategies for each level"""
    
    def generate_counters(self, opponent_level: int) -> List[str]:
        """Generate counter-strategies for opponent's level"""
        strategies = {
            0: [
                "Exploit their predictability",
                "Increase bluff frequency when they're weak",
                "Value bet thinner"
            ],
            1: [
                "Play more balanced to avoid exploitation",
                "Mix your strategies",
                "Don't be predictable"
            ],
            2: [
                "Implement level 3 thinking",
                "Counter their counter-exploitation",
                "Use reverse tells"
            ],
            3: [
                "Simplify to GTO baseline",
                "Avoid leveling yourself",
                "Focus on fundamentals"
            ]
        }
        
        return strategies.get(opponent_level, ["Play standard GTO"])
    
    def assess_counter_risk(self, counter_strategy: str, game_context: Dict) -> float:
        """Assess risk of a counter-strategy"""
        # Simplified risk assessment
        risk_factors = {
            'Increase bluff frequency': 0.6,
            'Play more balanced': 0.2,
            'Simplify to GTO': 0.1,
            'Counter their counter-exploitation': 0.7
        }
        
        for phrase, risk in risk_factors.items():
            if phrase.lower() in counter_strategy.lower():
                return risk
        
        return 0.5  # Default medium risk


class LevelingWarSimulator:
    """Simulate multi-iteration leveling wars"""
    
    def __init__(self):
        self.estimator = LevelEstimator()
        self.evolution_tracker = StrategyEvolution()
        self.counter_generator = CounterStrategyGenerator()
    
    def analyze_situation(self, opponent_observations: List[str],
                         opponent_stats: Dict,
                         game_context: Dict) -> LevelingOutcome:
        """Analyze leveling war situation and recommend strategy"""
        # Estimate opponent's level
        opponent_level = self.estimator.estimate_level(opponent_observations, opponent_stats)
        
        # Recommend one level above
        recommended_level = min(opponent_level + 1, 3)
        
        # Generate counter-strategies
        counters = self.counter_generator.generate_counters(opponent_level)
        
        # Assess overall risk
        risks = [self.counter_generator.assess_counter_risk(c, game_context) for c in counters]
        avg_risk = sum(risks) / len(risks) if risks else 0.5
        
        # Generate reasoning
        reasoning = (
            f"Opponent is at level {opponent_level} thinking. "
            f"Recommended to play level {recommended_level} to stay ahead. "
            f"{self.evolution_tracker.suggest_evolution()}"
        )
        
        # Calculate confidence based on sample size
        confidence = min(0.9, 0.5 + (len(opponent_observations) / 20))
        
        return LevelingOutcome(
            recommended_level=recommended_level,
            reasoning=reasoning,
            confidence=confidence,
            counter_strategies=counters,
            risk_assessment=avg_risk
        )
    
    def simulate_iterations(self, initial_hero_level: int,
                          initial_villain_level: int,
                          num_iterations: int = 10) -> List[Tuple[int, int, float]]:
        """Simulate multiple iterations of leveling war"""
        results = []
        hero_level = initial_hero_level
        villain_level = initial_villain_level
        
        for i in range(num_iterations):
            # Calculate EV for this matchup
            ev = self._calculate_matchup_ev(hero_level, villain_level)
            results.append((hero_level, villain_level, ev))
            
            # Simulate adaptation
            if ev < 0:  # Hero losing
                hero_level = min(hero_level + 1, 3)
            elif ev > 0.1:  # Hero winning significantly
                # Villain might level up
                if self._should_adapt(villain_level, ev):
                    villain_level = min(villain_level + 1, 3)
        
        return results
    
    def _calculate_matchup_ev(self, hero_level: int, villain_level: int) -> float:
        """Calculate EV for level matchup"""
        if hero_level > villain_level:
            return 0.1 * (hero_level - villain_level)
        elif villain_level > hero_level:
            return -0.1 * (villain_level - hero_level)
        return 0.0
    
    def _should_adapt(self, current_level: int, opponent_ev: float) -> bool:
        """Determine if player should adapt/level up"""
        # More likely to adapt if losing badly
        adaptation_threshold = 0.15
        return opponent_ev > adaptation_threshold and current_level < 3


class MetaGameTracker:
    """Track meta-game developments over time"""
    
    def __init__(self):
        self.game_history = []
        self.meta_trends = {}
    
    def record_game(self, hero_level: int, villain_level: int,
                   outcome: float, context: Dict):
        """Record a game result"""
        self.game_history.append({
            'hero_level': hero_level,
            'villain_level': villain_level,
            'outcome': outcome,
            'context': context
        })
    
    def detect_meta_shift(self) -> Optional[str]:
        """Detect if meta-game is shifting"""
        if len(self.game_history) < 20:
            return None
        
        # Compare early vs recent games
        early = self.game_history[:10]
        recent = self.game_history[-10:]
        
        early_avg_level = sum(g['villain_level'] for g in early) / len(early)
        recent_avg_level = sum(g['villain_level'] for g in recent) / len(recent)
        
        if recent_avg_level > early_avg_level + 0.5:
            return "Meta-game is evolving - opponents playing higher levels"
        elif recent_avg_level < early_avg_level - 0.5:
            return "Meta-game simplifying - opponents playing lower levels"
        
        return "Meta-game stable"
    
    def get_optimal_strategy(self) -> str:
        """Get optimal strategy based on meta trends"""
        meta_shift = self.detect_meta_shift()
        
        if not meta_shift:
            return "Balanced approach"
        
        if "evolving" in meta_shift:
            return "Increase sophistication - play level 2-3"
        elif "simplifying" in meta_shift:
            return "Exploit basics - focus on level 1 exploitation"
        
        return "Balanced approach"


def analyze_leveling_war(hero_observations: List[str],
                        villain_observations: List[str],
                        stats: Dict) -> Dict:
    """Quick analysis of leveling war situation"""
    simulator = LevelingWarSimulator()
    
    outcome = simulator.analyze_situation(
        villain_observations,
        stats,
        {}
    )
    
    return {
        'recommended_level': outcome.recommended_level,
        'reasoning': outcome.reasoning,
        'confidence': outcome.confidence,
        'counter_strategies': outcome.counter_strategies,
        'risk': outcome.risk_assessment
    }
