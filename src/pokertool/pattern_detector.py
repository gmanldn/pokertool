"""
Pattern Detector Module

Detects and analyzes patterns in player behavior, particularly focusing on
timing patterns, betting patterns, and behavioral consistency.

Part of TIMING-001: Timing Tell Analyzer
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import statistics


@dataclass
class Pattern:
    """Represents a detected behavioral pattern"""
    pattern_type: str
    confidence: float  # 0-1
    occurrences: int
    description: str
    strength: str  # "weak", "moderate", "strong"


class TimeSeriesAnalyzer:
    """Analyze time series data for patterns"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
    
    def detect_trend(self, values: List[float]) -> str:
        """Detect trend in values (increasing, decreasing, stable)"""
        if len(values) < 3:
            return "insufficient_data"
        
        # Calculate linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Fit line
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]
        
        # Determine trend
        if abs(slope) < 0.1:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def detect_cycles(self, values: List[float], min_cycle_length: int = 3) -> List[int]:
        """Detect cyclic patterns in values"""
        if len(values) < min_cycle_length * 2:
            return []
        
        detected_cycles = []
        
        # Check for repeated patterns
        for cycle_len in range(min_cycle_length, len(values) // 2 + 1):
            pattern = values[:cycle_len]
            matches = 0
            
            for i in range(cycle_len, len(values), cycle_len):
                chunk = values[i:i+cycle_len]
                if len(chunk) == cycle_len:
                    # Check similarity
                    similarity = self._calculate_similarity(pattern, chunk)
                    if similarity > 0.8:  # 80% similar
                        matches += 1
            
            if matches >= 2:  # At least 2 repetitions
                detected_cycles.append(cycle_len)
        
        return detected_cycles
    
    def _calculate_similarity(self, pattern1: List[float], pattern2: List[float]) -> float:
        """Calculate similarity between two patterns (0-1)"""
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # Normalize and compare
        norm1 = np.array(pattern1) / (np.max(pattern1) if np.max(pattern1) > 0 else 1)
        norm2 = np.array(pattern2) / (np.max(pattern2) if np.max(pattern2) > 0 else 1)
        
        # Calculate correlation
        diff = np.abs(norm1 - norm2)
        return 1.0 - np.mean(diff)
    
    def detect_outliers(self, values: List[float], threshold: float = 2.0) -> List[int]:
        """Detect outlier indices using z-score"""
        if len(values) < 3:
            return []
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev == 0:
            return []
        
        outliers = []
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev)
            if z_score > threshold:
                outliers.append(i)
        
        return outliers


class BehavioralPatternDetector:
    """Detect patterns in player behavior"""
    
    def __init__(self):
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.pattern_history: Dict[str, List[Pattern]] = {}
    
    def detect_timing_consistency(self, player_id: str, 
                                  timing_data: List[float]) -> Pattern:
        """Detect if player has consistent timing"""
        if len(timing_data) < 5:
            return Pattern(
                pattern_type="timing_consistency",
                confidence=0.0,
                occurrences=0,
                description="Insufficient data",
                strength="weak"
            )
        
        # Calculate coefficient of variation
        mean_time = statistics.mean(timing_data)
        std_dev = statistics.stdev(timing_data) if len(timing_data) > 1 else 0
        
        if mean_time == 0:
            cv = 0
        else:
            cv = std_dev / mean_time
        
        # Interpret consistency
        if cv < 0.2:
            description = f"Highly consistent timing (CV: {cv:.2f})"
            strength = "strong"
            confidence = 0.9
        elif cv < 0.5:
            description = f"Moderately consistent timing (CV: {cv:.2f})"
            strength = "moderate"
            confidence = 0.7
        else:
            description = f"Inconsistent timing (CV: {cv:.2f})"
            strength = "weak"
            confidence = 0.5
        
        pattern = Pattern(
            pattern_type="timing_consistency",
            confidence=confidence,
            occurrences=len(timing_data),
            description=description,
            strength=strength
        )
        
        self._record_pattern(player_id, pattern)
        return pattern
    
    def detect_action_speed_pattern(self, player_id: str,
                                    action_types: List[str],
                                    decision_times: List[float]) -> List[Pattern]:
        """Detect if player has different speeds for different actions"""
        if len(action_types) != len(decision_times) or len(action_types) < 10:
            return []
        
        # Group by action type
        action_times: Dict[str, List[float]] = {}
        for action, time in zip(action_types, decision_times):
            if action not in action_times:
                action_times[action] = []
            action_times[action].append(time)
        
        patterns = []
        
        # Compare action speeds
        for action, times in action_times.items():
            if len(times) < 3:
                continue
            
            mean_time = statistics.mean(times)
            overall_mean = statistics.mean(decision_times)
            
            # Check if significantly different
            if mean_time < overall_mean * 0.7:
                pattern = Pattern(
                    pattern_type=f"fast_{action}",
                    confidence=0.8,
                    occurrences=len(times),
                    description=f"Consistently fast {action} actions ({mean_time:.2f}s vs {overall_mean:.2f}s avg)",
                    strength="strong"
                )
                patterns.append(pattern)
                self._record_pattern(player_id, pattern)
            
            elif mean_time > overall_mean * 1.3:
                pattern = Pattern(
                    pattern_type=f"slow_{action}",
                    confidence=0.8,
                    occurrences=len(times),
                    description=f"Consistently slow {action} actions ({mean_time:.2f}s vs {overall_mean:.2f}s avg)",
                    strength="strong"
                )
                patterns.append(pattern)
                self._record_pattern(player_id, pattern)
        
        return patterns
    
    def detect_escalation_pattern(self, decision_times: List[float]) -> Optional[Pattern]:
        """Detect if decision times are escalating or de-escalating"""
        if len(decision_times) < 5:
            return None
        
        trend = self.time_series_analyzer.detect_trend(decision_times)
        
        if trend == "increasing":
            return Pattern(
                pattern_type="escalating_timing",
                confidence=0.75,
                occurrences=len(decision_times),
                description="Decision times increasing (possible tilt or fatigue)",
                strength="moderate"
            )
        elif trend == "decreasing":
            return Pattern(
                pattern_type="deescalating_timing",
                confidence=0.75,
                occurrences=len(decision_times),
                description="Decision times decreasing (possibly warmed up or rushing)",
                strength="moderate"
            )
        
        return None
    
    def detect_session_fatigue(self, decision_times: List[float],
                              session_duration: float) -> Optional[Pattern]:
        """Detect if player shows signs of fatigue"""
        if len(decision_times) < 20 or session_duration < 3600:  # 1 hour minimum
            return None
        
        # Compare first quarter vs last quarter
        quarter_size = len(decision_times) // 4
        first_quarter = decision_times[:quarter_size]
        last_quarter = decision_times[-quarter_size:]
        
        first_avg = statistics.mean(first_quarter)
        last_avg = statistics.mean(last_quarter)
        
        # Check for significant slowdown
        if last_avg > first_avg * 1.5:
            return Pattern(
                pattern_type="session_fatigue",
                confidence=0.85,
                occurrences=len(decision_times),
                description=f"Significant slowdown detected ({first_avg:.2f}s → {last_avg:.2f}s)",
                strength="strong"
            )
        
        return None
    
    def _record_pattern(self, player_id: str, pattern: Pattern):
        """Record detected pattern in history"""
        if player_id not in self.pattern_history:
            self.pattern_history[player_id] = []
        
        self.pattern_history[player_id].append(pattern)
    
    def get_player_patterns(self, player_id: str) -> List[Pattern]:
        """Get all detected patterns for a player"""
        return self.pattern_history.get(player_id, [])


class SequencePatternMatcher:
    """Match and identify common sequences"""
    
    def __init__(self):
        self.known_patterns = {
            ('bet', 'bet', 'bet'): {
                'name': 'triple_barrel',
                'description': 'Triple barrel bluff or value line',
                'significance': 'high'
            },
            ('check', 'call', 'call'): {
                'name': 'check_call_line',
                'description': 'Defensive check-call line',
                'significance': 'medium'
            },
            ('raise', 'bet', 'bet'): {
                'name': 'aggressive_line',
                'description': 'Continuous aggression',
                'significance': 'high'
            },
            ('check', 'raise', 'bet'): {
                'name': 'check_raise_continue',
                'description': 'Check-raise with continued aggression',
                'significance': 'high'
            }
        }
    
    def match_sequence(self, sequence: Tuple) -> Optional[Dict]:
        """Match a sequence to known patterns"""
        return self.known_patterns.get(sequence)
    
    def find_partial_matches(self, sequence: Tuple) -> List[Dict]:
        """Find partial matches with known patterns"""
        matches = []
        
        for known_seq, info in self.known_patterns.items():
            # Check if sequence is a subset
            if self._is_subsequence(sequence, known_seq):
                matches.append({
                    'pattern': known_seq,
                    'info': info,
                    'match_type': 'partial'
                })
        
        return matches
    
    def _is_subsequence(self, subseq: Tuple, sequence: Tuple) -> bool:
        """Check if subseq is a subsequence of sequence"""
        if len(subseq) > len(sequence):
            return False
        
        j = 0
        for i in range(len(sequence)):
            if j < len(subseq) and sequence[i] == subseq[j]:
                j += 1
        
        return j == len(subseq)


class AnomalyDetector:
    """Detect anomalous patterns in timing and behavior"""
    
    def __init__(self, sensitivity: float = 0.8):
        self.sensitivity = sensitivity  # 0-1, higher = more sensitive
        self.baseline_data: Dict[str, List[float]] = {}
    
    def establish_baseline(self, player_id: str, timing_data: List[float]):
        """Establish baseline timing for a player"""
        self.baseline_data[player_id] = timing_data.copy()
    
    def detect_anomaly(self, player_id: str, new_timing: float) -> Tuple[bool, float]:
        """
        Detect if new timing is anomalous
        Returns (is_anomaly, severity)
        """
        if player_id not in self.baseline_data:
            return False, 0.0
        
        baseline = self.baseline_data[player_id]
        if len(baseline) < 3:
            return False, 0.0
        
        mean = statistics.mean(baseline)
        std_dev = statistics.stdev(baseline) if len(baseline) > 1 else 0
        
        if std_dev == 0:
            return False, 0.0
        
        # Calculate z-score
        z_score = abs((new_timing - mean) / std_dev)
        
        # Adjust threshold based on sensitivity
        threshold = 3.0 * (1.0 - self.sensitivity * 0.5)
        
        is_anomaly = z_score > threshold
        severity = min(1.0, z_score / 5.0)  # Normalize to 0-1
        
        return is_anomaly, severity
    
    def update_baseline(self, player_id: str, new_timing: float,
                       max_baseline_size: int = 100):
        """Update baseline with new data point"""
        if player_id not in self.baseline_data:
            self.baseline_data[player_id] = []
        
        self.baseline_data[player_id].append(new_timing)
        
        # Keep baseline size manageable
        if len(self.baseline_data[player_id]) > max_baseline_size:
            self.baseline_data[player_id] = self.baseline_data[player_id][-max_baseline_size:]


# Utility functions
def calculate_pattern_strength(confidence: float, occurrences: int,
                              min_occurrences: int = 5) -> str:
    """Calculate overall pattern strength"""
    if occurrences < min_occurrences:
        return "weak"
    
    if confidence > 0.8 and occurrences >= 10:
        return "strong"
    elif confidence > 0.6 and occurrences >= 7:
        return "moderate"
    else:
        return "weak"


def combine_pattern_scores(patterns: List[Pattern]) -> float:
    """Combine multiple pattern scores into overall confidence"""
    if not patterns:
        return 0.0
    
    # Weight by confidence and strength
    strength_weights = {"weak": 0.5, "moderate": 1.0, "strong": 1.5}
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for pattern in patterns:
        weight = strength_weights.get(pattern.strength, 1.0)
        total_weight += weight
        weighted_sum += pattern.confidence * weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0
