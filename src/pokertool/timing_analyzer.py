"""
Timing Tell Analyzer

Advanced timing pattern analysis for detecting tells in online poker.
Tracks microsecond-precision timing patterns, action sequences, and deviations.

ID: TIMING-001
Priority: MEDIUM
Expected Accuracy Gain: 5-8% improvement in live play reads
"""

import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import statistics


class ActionType(Enum):
    """Types of poker actions"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass
class TimedAction:
    """Represents an action with precise timing"""
    player_id: str
    action: ActionType
    amount: float
    timestamp: float  # Unix timestamp in seconds with microsecond precision
    street: str  # preflop, flop, turn, river
    pot_size: float
    decision_time: float  # Time taken to make decision in seconds
    context: Dict = field(default_factory=dict)


@dataclass
class TimingPattern:
    """Identified timing pattern for a player"""
    player_id: str
    action: ActionType
    mean_time: float
    std_dev: float
    median_time: float
    min_time: float
    max_time: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    street: str = "all"


@dataclass
class TimingDeviation:
    """Represents a significant timing deviation"""
    player_id: str
    action: ActionType
    expected_time: float
    actual_time: float
    deviation_magnitude: float  # Standard deviations from mean
    significance: float  # 0-1, higher = more significant
    interpretation: str  # "strength", "weakness", "bluff", "value", "uncertain"


class TimingTellDatabase:
    """Database for storing timing patterns"""
    
    def __init__(self):
        self.patterns: Dict[str, Dict[str, List[float]]] = {}
        # Structure: {player_id: {action_type: [times]}}
    
    def add_timing(self, player_id: str, action: ActionType, decision_time: float):
        """Add a timing observation"""
        if player_id not in self.patterns:
            self.patterns[player_id] = {}
        
        action_key = action.value
        if action_key not in self.patterns[player_id]:
            self.patterns[player_id][action_key] = []
        
        self.patterns[player_id][action_key].append(decision_time)
    
    def get_pattern(self, player_id: str, action: ActionType) -> Optional[TimingPattern]:
        """Get timing pattern for a player and action"""
        if player_id not in self.patterns:
            return None
        
        action_key = action.value
        if action_key not in self.patterns[player_id]:
            return None
        
        times = self.patterns[player_id][action_key]
        if len(times) < 3:  # Need minimum samples
            return None
        
        mean_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        median_time = statistics.median(times)
        
        # Calculate 95% confidence interval
        z_score = 1.96  # 95% confidence
        margin = z_score * (std_dev / (len(times) ** 0.5))
        ci = (mean_time - margin, mean_time + margin)
        
        return TimingPattern(
            player_id=player_id,
            action=action,
            mean_time=mean_time,
            std_dev=std_dev,
            median_time=median_time,
            min_time=min(times),
            max_time=max(times),
            sample_size=len(times),
            confidence_interval=ci
        )
    
    def export_data(self, filepath: str):
        """Export timing database to JSON"""
        data = {
            player_id: {
                action: times
                for action, times in actions.items()
            }
            for player_id, actions in self.patterns.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_data(self, filepath: str):
        """Import timing database from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.patterns = data


class ActionSequenceAnalyzer:
    """Analyze sequences of actions and their timing"""
    
    def __init__(self):
        self.sequences: Dict[str, List[List[TimedAction]]] = {}
        # Structure: {player_id: [sequences]}
    
    def add_sequence(self, player_id: str, sequence: List[TimedAction]):
        """Add an action sequence"""
        if player_id not in self.sequences:
            self.sequences[player_id] = []
        
        self.sequences[player_id].append(sequence)
    
    def analyze_sequence_timing(self, sequence: List[TimedAction]) -> Dict:
        """Analyze timing patterns within a sequence"""
        if len(sequence) < 2:
            return {'valid': False}
        
        # Calculate time differences between actions
        time_diffs = []
        for i in range(1, len(sequence)):
            diff = sequence[i].timestamp - sequence[i-1].timestamp
            time_diffs.append(diff)
        
        # Look for patterns
        analysis = {
            'valid': True,
            'sequence_length': len(sequence),
            'total_time': sum(time_diffs),
            'avg_interval': statistics.mean(time_diffs) if time_diffs else 0,
            'actions': [a.action.value for a in sequence],
            'rapid_fire': all(d < 1.0 for d in time_diffs),  # All actions < 1 second apart
            'deliberate': all(d > 5.0 for d in time_diffs),  # All actions > 5 seconds
            'escalating': all(time_diffs[i] < time_diffs[i+1] for i in range(len(time_diffs)-1)),
            'de_escalating': all(time_diffs[i] > time_diffs[i+1] for i in range(len(time_diffs)-1))
        }
        
        return analysis
    
    def get_common_sequences(self, player_id: str, min_count: int = 3) -> List[Tuple[Tuple, int]]:
        """Get common action sequences for a player"""
        if player_id not in self.sequences:
            return []
        
        # Count sequence patterns
        sequence_counts = {}
        for sequence in self.sequences[player_id]:
            pattern = tuple(a.action.value for a in sequence)
            sequence_counts[pattern] = sequence_counts.get(pattern, 0) + 1
        
        # Filter and sort
        common = [(pattern, count) for pattern, count in sequence_counts.items()
                 if count >= min_count]
        return sorted(common, key=lambda x: x[1], reverse=True)


class TimingDeviationDetector:
    """Detect significant timing deviations"""
    
    def __init__(self, database: TimingTellDatabase):
        self.database = database
        self.deviation_threshold = 2.0  # Standard deviations
    
    def detect_deviation(self, timed_action: TimedAction) -> Optional[TimingDeviation]:
        """Detect if an action shows significant timing deviation"""
        pattern = self.database.get_pattern(timed_action.player_id, timed_action.action)
        
        if pattern is None or pattern.sample_size < 5:
            return None  # Need sufficient data
        
        # Calculate z-score
        if pattern.std_dev == 0:
            return None  # No variation to detect
        
        z_score = (timed_action.decision_time - pattern.mean_time) / pattern.std_dev
        
        if abs(z_score) < self.deviation_threshold:
            return None  # Not significant
        
        # Interpret the deviation
        interpretation = self._interpret_deviation(
            timed_action.action,
            z_score,
            timed_action.context
        )
        
        significance = min(1.0, abs(z_score) / 5.0)  # Cap at 5 std devs
        
        return TimingDeviation(
            player_id=timed_action.player_id,
            action=timed_action.action,
            expected_time=pattern.mean_time,
            actual_time=timed_action.decision_time,
            deviation_magnitude=z_score,
            significance=significance,
            interpretation=interpretation
        )
    
    def _interpret_deviation(self, action: ActionType, z_score: float,
                           context: Dict) -> str:
        """Interpret what a timing deviation might mean"""
        is_fast = z_score < 0  # Negative z = faster than normal
        is_slow = z_score > 0
        
        # Quick actions often indicate strength or automation
        if is_fast:
            if action in [ActionType.BET, ActionType.RAISE]:
                return "strength"  # Fast aggression = confident/strong
            elif action == ActionType.CALL:
                return "value"  # Fast call = clear call
            elif action == ActionType.FOLD:
                return "weakness"  # Fast fold = easy decision
        
        # Slow actions often indicate difficult decisions or bluffs
        if is_slow:
            if action in [ActionType.BET, ActionType.RAISE]:
                return "bluff"  # Slow bluff = acting/thinking
            elif action == ActionType.CALL:
                return "weakness"  # Slow call = marginal hand
            elif action == ActionType.FOLD:
                return "strength"  # Slow fold = tough laydown
        
        return "uncertain"


class PatternClusterer:
    """Cluster timing patterns to identify player types"""
    
    def __init__(self):
        self.player_profiles = {}
    
    def create_profile(self, player_id: str, patterns: List[TimingPattern]) -> Dict:
        """Create a timing profile for a player"""
        if not patterns:
            return {'valid': False}
        
        # Calculate aggregate statistics
        all_times = []
        action_stats = {}
        
        for pattern in patterns:
            all_times.extend([pattern.mean_time] * pattern.sample_size)
            action_stats[pattern.action.value] = {
                'mean': pattern.mean_time,
                'std_dev': pattern.std_dev,
                'samples': pattern.sample_size
            }
        
        profile = {
            'valid': True,
            'player_id': player_id,
            'overall_speed': statistics.mean(all_times) if all_times else 0,
            'consistency': statistics.stdev(all_times) if len(all_times) > 1 else 0,
            'action_stats': action_stats,
            'total_actions': len(all_times),
            'player_type': self._classify_player_type(all_times, action_stats)
        }
        
        self.player_profiles[player_id] = profile
        return profile
    
    def _classify_player_type(self, all_times: List[float], action_stats: Dict) -> str:
        """Classify player based on timing patterns"""
        if not all_times:
            return "unknown"
        
        avg_time = statistics.mean(all_times)
        consistency = statistics.stdev(all_times) if len(all_times) > 1 else 0
        
        # Very fast and consistent = bot or timing software
        if avg_time < 1.0 and consistency < 0.5:
            return "automated"
        
        # Fast but variable = experienced player
        if avg_time < 2.0:
            return "fast_player"
        
        # Slow and consistent = recreational/careful
        if avg_time > 5.0 and consistency < 2.0:
            return "slow_player"
        
        # Highly variable = nervous or strategic
        if consistency > 3.0:
            return "variable_player"
        
        return "standard_player"


class AdvancedTimingAnalyzer:
    """Main timing analyzer with all features"""
    
    def __init__(self):
        self.database = TimingTellDatabase()
        self.sequence_analyzer = ActionSequenceAnalyzer()
        self.deviation_detector = TimingDeviationDetector(self.database)
        self.clusterer = PatternClusterer()
        self.current_sequences: Dict[str, List[TimedAction]] = {}
    
    def record_action(self, timed_action: TimedAction) -> Optional[TimingDeviation]:
        """Record an action and check for deviations"""
        # Add to database
        self.database.add_timing(
            timed_action.player_id,
            timed_action.action,
            timed_action.decision_time
        )
        
        # Track sequences
        player_id = timed_action.player_id
        if player_id not in self.current_sequences:
            self.current_sequences[player_id] = []
        
        self.current_sequences[player_id].append(timed_action)
        
        # Check for deviation
        deviation = self.deviation_detector.detect_deviation(timed_action)
        
        return deviation
    
    def end_hand(self, player_id: str):
        """Mark end of hand and finalize sequence"""
        if player_id in self.current_sequences:
            sequence = self.current_sequences[player_id]
            if len(sequence) > 0:
                self.sequence_analyzer.add_sequence(player_id, sequence)
            self.current_sequences[player_id] = []
    
    def get_player_analysis(self, player_id: str) -> Dict:
        """Get comprehensive timing analysis for a player"""
        # Get all patterns
        patterns = []
        for action_type in ActionType:
            pattern = self.database.get_pattern(player_id, action_type)
            if pattern:
                patterns.append(pattern)
        
        # Create profile
        profile = self.clusterer.create_profile(player_id, patterns)
        
        # Get common sequences
        sequences = self.sequence_analyzer.get_common_sequences(player_id)
        
        return {
            'profile': profile,
            'patterns': [
                {
                    'action': p.action.value,
                    'mean_time': p.mean_time,
                    'std_dev': p.std_dev,
                    'samples': p.sample_size
                }
                for p in patterns
            ],
            'common_sequences': sequences[:5]  # Top 5
        }
    
    def get_tell_interpretation(self, deviation: TimingDeviation) -> Dict:
        """Get detailed interpretation of a timing tell"""
        return {
            'player_id': deviation.player_id,
            'action': deviation.action.value,
            'expected_time': round(deviation.expected_time, 3),
            'actual_time': round(deviation.actual_time, 3),
            'deviation': round(deviation.deviation_magnitude, 2),
            'significance': round(deviation.significance, 3),
            'interpretation': deviation.interpretation,
            'reliability': self._calculate_reliability(deviation),
            'recommendation': self._get_recommendation(deviation)
        }
    
    def _calculate_reliability(self, deviation: TimingDeviation) -> float:
        """Calculate reliability of the tell"""
        # More samples = more reliable
        pattern = self.database.get_pattern(deviation.player_id, deviation.action)
        if not pattern:
            return 0.0
        
        sample_factor = min(1.0, pattern.sample_size / 30)  # Cap at 30 samples
        significance_factor = deviation.significance
        
        return (sample_factor + significance_factor) / 2
    
    def _get_recommendation(self, deviation: TimingDeviation) -> str:
        """Get strategic recommendation based on tell"""
        if deviation.interpretation == "strength":
            return "Consider folding marginal hands; opponent likely has strong holding"
        elif deviation.interpretation == "weakness":
            return "Consider bluffing or applying pressure"
        elif deviation.interpretation == "bluff":
            return "Opponent may be bluffing; consider calling with bluff-catchers"
        elif deviation.interpretation == "value":
            return "Opponent likely has made hand; proceed cautiously"
        else:
            return "Insufficient information for reliable recommendation"
    
    def export_analysis(self, filepath: str):
        """Export complete analysis to JSON"""
        data = {
            'database': self.database.patterns,
            'profiles': self.clusterer.player_profiles
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Utility functions
def calculate_decision_time(action_start: float, action_end: float) -> float:
    """Calculate decision time in seconds"""
    return action_end - action_start


def is_instant_action(decision_time: float, threshold: float = 0.5) -> bool:
    """Check if action was instant (likely pre-selected)"""
    return decision_time < threshold


def is_time_bank_used(decision_time: float, typical_max: float = 30.0) -> bool:
    """Check if player used time bank"""
    return decision_time > typical_max
