"""
Timing Tell Analyzer - Advanced timing pattern analysis for poker decisions.

This module provides microsecond precision tracking, action sequence timing,
timing deviation detection, pattern clustering, and confidence intervals.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import math


@dataclass
class TimingData:
    """Store timing information for a single action."""
    player_id: str
    action: str
    decision_time: float  # in seconds
    timestamp: float
    street: str
    pot_size: float
    stack_size: float
    action_type: str  # 'bet', 'raise', 'call', 'fold', 'check'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'player_id': self.player_id,
            'action': self.action,
            'decision_time': self.decision_time,
            'timestamp': self.timestamp,
            'street': self.street,
            'pot_size': self.pot_size,
            'stack_size': self.stack_size,
            'action_type': self.action_type
        }


@dataclass
class TimingPattern:
    """Detected timing pattern for a player."""
    pattern_type: str
    confidence: float
    mean_time: float
    std_dev: float
    sample_size: int
    correlation: float
    description: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'pattern_type': self.pattern_type,
            'confidence': self.confidence,
            'mean_time': self.mean_time,
            'std_dev': self.std_dev,
            'sample_size': self.sample_size,
            'correlation': self.correlation,
            'description': self.description
        }


class MicrosecondPrecisionTracker:
    """Track action timing with microsecond precision."""
    
    def __init__(self):
        self.timing_data: List[TimingData] = []
        self.action_start_times: Dict[str, float] = {}
        
    def start_action_timer(self, player_id: str) -> None:
        """Start timing an action."""
        self.action_start_times[player_id] = time.perf_counter()
        
    def record_action(
        self,
        player_id: str,
        action: str,
        street: str,
        pot_size: float,
        stack_size: float,
        action_type: str
    ) -> Optional[TimingData]:
        """Record action with timing data."""
        if player_id not in self.action_start_times:
            return None
            
        decision_time = time.perf_counter() - self.action_start_times[player_id]
        timing_data = TimingData(
            player_id=player_id,
            action=action,
            decision_time=decision_time,
            timestamp=time.time(),
            street=street,
            pot_size=pot_size,
            stack_size=stack_size,
            action_type=action_type
        )
        
        self.timing_data.append(timing_data)
        del self.action_start_times[player_id]
        return timing_data
        
    def get_player_timings(self, player_id: str) -> List[TimingData]:
        """Get all timing data for a specific player."""
        return [td for td in self.timing_data if td.player_id == player_id]
        
    def get_action_type_timings(self, action_type: str) -> List[TimingData]:
        """Get timing data for specific action type."""
        return [td for td in self.timing_data if td.action_type == action_type]


class ActionSequenceTimer:
    """Analyze timing patterns in action sequences."""
    
    def __init__(self):
        self.sequences: Dict[str, List[TimingData]] = defaultdict(list)
        
    def add_to_sequence(self, hand_id: str, timing_data: TimingData) -> None:
        """Add timing data to a hand sequence."""
        self.sequences[hand_id].append(timing_data)
        
    def get_sequence_pattern(self, hand_id: str) -> Dict:
        """Analyze timing pattern for a sequence."""
        sequence = self.sequences.get(hand_id, [])
        if not sequence:
            return {}
            
        times = [td.decision_time for td in sequence]
        return {
            'hand_id': hand_id,
            'action_count': len(sequence),
            'total_time': sum(times),
            'mean_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': self._calculate_std_dev(times)
        }
        
    def detect_speed_changes(self, hand_id: str) -> List[Dict]:
        """Detect significant speed changes in sequence."""
        sequence = self.sequences.get(hand_id, [])
        if len(sequence) < 3:
            return []
            
        changes = []
        for i in range(1, len(sequence) - 1):
            prev_time = sequence[i - 1].decision_time
            curr_time = sequence[i].decision_time
            next_time = sequence[i + 1].decision_time
            
            # Detect sudden speed changes
            if curr_time > prev_time * 1.5 and curr_time > next_time * 1.5:
                changes.append({
                    'position': i,
                    'action': sequence[i].action,
                    'time': curr_time,
                    'deviation': (curr_time - prev_time) / prev_time,
                    'type': 'slowdown'
                })
            elif curr_time < prev_time * 0.5 and curr_time < next_time * 0.5:
                changes.append({
                    'position': i,
                    'action': sequence[i].action,
                    'time': curr_time,
                    'deviation': (prev_time - curr_time) / prev_time,
                    'type': 'speedup'
                })
                
        return changes
        
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


class TimingDeviationDetector:
    """Detect timing deviations from baseline patterns."""
    
    def __init__(self):
        self.baselines: Dict[str, Dict] = {}
        
    def establish_baseline(self, player_id: str, timings: List[TimingData]) -> None:
        """Establish baseline timing for a player."""
        if not timings:
            return
            
        by_action_type = defaultdict(list)
        for td in timings:
            by_action_type[td.action_type].append(td.decision_time)
            
        self.baselines[player_id] = {}
        for action_type, times in by_action_type.items():
            self.baselines[player_id][action_type] = {
                'mean': sum(times) / len(times),
                'std_dev': self._calculate_std_dev(times),
                'sample_size': len(times)
            }
            
    def detect_deviation(
        self,
        player_id: str,
        action_type: str,
        decision_time: float
    ) -> Optional[Dict]:
        """Detect if timing deviates from baseline."""
        if player_id not in self.baselines:
            return None
            
        if action_type not in self.baselines[player_id]:
            return None
            
        baseline = self.baselines[player_id][action_type]
        mean = baseline['mean']
        std_dev = baseline['std_dev']
        
        if std_dev == 0:
            return None
            
        z_score = (decision_time - mean) / std_dev
        
        return {
            'player_id': player_id,
            'action_type': action_type,
            'decision_time': decision_time,
            'baseline_mean': mean,
            'z_score': z_score,
            'is_deviation': abs(z_score) > 2.0,
            'deviation_type': 'slower' if z_score > 0 else 'faster',
            'confidence': min(abs(z_score) / 3.0, 1.0)
        }
        
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


class PatternClusterer:
    """Cluster timing patterns to identify player tendencies."""
    
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.clusters: Dict[str, List[Dict]] = {}
        
    def cluster_timings(self, player_id: str, timings: List[TimingData]) -> List[Dict]:
        """Cluster timing data for a player."""
        if not timings:
            return []
            
        # Group by action type and street
        groups = defaultdict(list)
        for td in timings:
            key = f"{td.action_type}_{td.street}"
            groups[key].append(td.decision_time)
            
        clusters = []
        for key, times in groups.items():
            action_type, street = key.split('_')
            clusters.append({
                'action_type': action_type,
                'street': street,
                'mean_time': sum(times) / len(times),
                'std_dev': self._calculate_std_dev(times),
                'sample_size': len(times),
                'min_time': min(times),
                'max_time': max(times)
            })
            
        self.clusters[player_id] = clusters
        return clusters
        
    def identify_patterns(self, player_id: str) -> List[TimingPattern]:
        """Identify timing patterns from clusters."""
        if player_id not in self.clusters:
            return []
            
        clusters = self.clusters[player_id]
        patterns = []
        
        for cluster in clusters:
            # Fast decisions (< 2 seconds)
            if cluster['mean_time'] < 2.0:
                patterns.append(TimingPattern(
                    pattern_type='fast_decision',
                    confidence=min(cluster['sample_size'] / 20.0, 1.0),
                    mean_time=cluster['mean_time'],
                    std_dev=cluster['std_dev'],
                    sample_size=cluster['sample_size'],
                    correlation=0.8,
                    description=f"Fast {cluster['action_type']} on {cluster['street']}"
                ))
                
            # Slow decisions (> 10 seconds)
            elif cluster['mean_time'] > 10.0:
                patterns.append(TimingPattern(
                    pattern_type='slow_decision',
                    confidence=min(cluster['sample_size'] / 20.0, 1.0),
                    mean_time=cluster['mean_time'],
                    std_dev=cluster['std_dev'],
                    sample_size=cluster['sample_size'],
                    correlation=0.75,
                    description=f"Slow {cluster['action_type']} on {cluster['street']}"
                ))
                
            # Consistent timing
            if cluster['std_dev'] < cluster['mean_time'] * 0.3:
                patterns.append(TimingPattern(
                    pattern_type='consistent_timing',
                    confidence=min(cluster['sample_size'] / 15.0, 1.0),
                    mean_time=cluster['mean_time'],
                    std_dev=cluster['std_dev'],
                    sample_size=cluster['sample_size'],
                    correlation=0.85,
                    description=f"Consistent {cluster['action_type']} timing on {cluster['street']}"
                ))
                
        return patterns
        
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


class ConfidenceIntervalCalculator:
    """Calculate confidence intervals for timing patterns."""
    
    def calculate_interval(
        self,
        mean: float,
        std_dev: float,
        sample_size: int,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for timing mean."""
        if sample_size < 2:
            return (mean, mean)
            
        # Use t-distribution approximation
        # For 95% confidence, t ≈ 1.96 for large samples
        t_score = 1.96 if confidence_level == 0.95 else 2.576
        
        margin_of_error = t_score * (std_dev / math.sqrt(sample_size))
        
        return (mean - margin_of_error, mean + margin_of_error)
        
    def calculate_pattern_confidence(self, pattern: TimingPattern) -> float:
        """Calculate overall confidence in a pattern."""
        # Base confidence on sample size
        sample_confidence = min(pattern.sample_size / 30.0, 1.0)
        
        # Factor in consistency (lower std_dev = higher confidence)
        consistency_confidence = 1.0 - min(pattern.std_dev / pattern.mean_time, 1.0)
        
        # Factor in correlation
        correlation_confidence = pattern.correlation
        
        # Weighted average
        overall_confidence = (
            sample_confidence * 0.4 +
            consistency_confidence * 0.3 +
            correlation_confidence * 0.3
        )
        
        return overall_confidence


class TimingTellAnalyzer:
    """Main class orchestrating all timing analysis components."""
    
    def __init__(self):
        self.tracker = MicrosecondPrecisionTracker()
        self.sequence_timer = ActionSequenceTimer()
        self.deviation_detector = TimingDeviationDetector()
        self.clusterer = PatternClusterer()
        self.confidence_calculator = ConfidenceIntervalCalculator()
        
    def start_action(self, player_id: str) -> None:
        """Start timing an action."""
        self.tracker.start_action_timer(player_id)
        
    def record_action(
        self,
        player_id: str,
        action: str,
        street: str,
        pot_size: float,
        stack_size: float,
        action_type: str,
        hand_id: Optional[str] = None
    ) -> Optional[TimingData]:
        """Record action with timing."""
        timing_data = self.tracker.record_action(
            player_id, action, street, pot_size, stack_size, action_type
        )
        
        if timing_data and hand_id:
            self.sequence_timer.add_to_sequence(hand_id, timing_data)
            
        return timing_data
        
    def analyze_player(self, player_id: str) -> Dict:
        """Comprehensive timing analysis for a player."""
        timings = self.tracker.get_player_timings(player_id)
        
        if not timings:
            return {'error': 'No timing data available'}
            
        # Establish baseline
        self.deviation_detector.establish_baseline(player_id, timings)
        
        # Cluster patterns
        clusters = self.clusterer.cluster_timings(player_id, timings)
        patterns = self.clusterer.identify_patterns(player_id)
        
        # Calculate confidence intervals for each pattern
        pattern_analysis = []
        for pattern in patterns:
            interval = self.confidence_calculator.calculate_interval(
                pattern.mean_time,
                pattern.std_dev,
                pattern.sample_size
            )
            confidence = self.confidence_calculator.calculate_pattern_confidence(pattern)
            
            pattern_analysis.append({
                'pattern': pattern.to_dict(),
                'confidence_interval': interval,
                'overall_confidence': confidence
            })
            
        return {
            'player_id': player_id,
            'total_actions': len(timings),
            'clusters': clusters,
            'patterns': pattern_analysis,
            'baseline': self.deviation_detector.baselines.get(player_id, {})
        }
        
    def detect_live_deviation(
        self,
        player_id: str,
        action_type: str,
        decision_time: float
    ) -> Optional[Dict]:
        """Detect live timing deviation."""
        return self.deviation_detector.detect_deviation(
            player_id, action_type, decision_time
        )
        
    def get_hand_sequence_analysis(self, hand_id: str) -> Dict:
        """Analyze timing sequence for a hand."""
        pattern = self.sequence_timer.get_sequence_pattern(hand_id)
        changes = self.sequence_timer.detect_speed_changes(hand_id)
        
        return {
            'sequence_pattern': pattern,
            'speed_changes': changes
        }
        
    def export_data(self) -> Dict:
        """Export all timing data."""
        return {
            'timing_data': [td.to_dict() for td in self.tracker.timing_data],
            'baselines': self.deviation_detector.baselines,
            'clusters': self.clusters
        }
        
    def import_data(self, data: Dict) -> None:
        """Import timing data."""
        if 'baselines' in data:
            self.deviation_detector.baselines = data['baselines']
        if 'clusters' in data:
            self.clusterer.clusters = data['clusters']


# Utility functions
def analyze_timing_patterns(timings: List[TimingData]) -> List[TimingPattern]:
    """Quick utility to analyze timing patterns."""
    analyzer = TimingTellAnalyzer()
    for td in timings:
        analyzer.tracker.timing_data.append(td)
        
    if timings:
        player_id = timings[0].player_id
        return analyzer.clusterer.identify_patterns(player_id)
    return []


def detect_timing_tell(
    baseline_mean: float,
    baseline_std: float,
    decision_time: float
) -> Dict:
    """Quick utility to detect timing tell."""
    if baseline_std == 0:
        return {'is_tell': False}
        
    z_score = (decision_time - baseline_mean) / baseline_std
    
    return {
        'is_tell': abs(z_score) > 2.0,
        'z_score': z_score,
        'deviation_type': 'slower' if z_score > 0 else 'faster',
        'confidence': min(abs(z_score) / 3.0, 1.0)
    }
