"""
Variance Calculator Module
Provides comprehensive variance and risk analysis tools for poker players
including standard deviation, downswing simulation, risk of ruin, and Monte Carlo analysis.
"""

import logging
import random
import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SessionResult:
    """Individual session result for variance analysis."""
    timestamp: datetime
    profit_loss: float
    buy_in: float
    session_length: float  # hours
    game_type: str = "cash"
    stakes: str = ""
    location: str = ""

@dataclass
class VarianceReport:
    """Comprehensive variance analysis report."""
    total_sessions: int
    total_profit_loss: float
    win_rate: float
    roi: float
    standard_deviation: float
    variance: float
    confidence_intervals: Dict[str, Tuple[float, float]]
    downswing_probabilities: Dict[str, float]
    risk_of_ruin: float
    expected_bankroll_swings: Dict[str, Tuple[float, float]]
    monte_carlo_results: Optional[Dict[str, Any]] = None

class VarianceCalculator:
    """Advanced variance and risk analysis calculator."""
    
    def __init__(self):
        self.sessions: List[SessionResult] = []
        
    def add_session(self, profit_loss: float, buy_in: float = 0.0, 
                   session_length: float = 1.0, game_type: str = "cash",
                   stakes: str = "", location: str = "") -> None:
        """Add a session result for variance analysis."""
        session = SessionResult(
            timestamp=datetime.utcnow(),
            profit_loss=profit_loss,
            buy_in=buy_in,
            session_length=session_length,
            game_type=game_type,
            stakes=stakes,
            location=location
        )
        self.sessions.append(session)
        
    def add_sessions_bulk(self, results: List[float]) -> None:
        """Add multiple session results at once."""
        for result in results:
            self.add_session(result)
    
    def calculate_basic_statistics(self) -> Dict[str, float]:
        """Calculate basic statistical measures."""
        if not self.sessions:
            return {}
            
        results = [s.profit_loss for s in self.sessions]
        
        return {
            'count': len(results),
            'total_profit_loss': sum(results),
            'mean': statistics.mean(results),
            'median': statistics.median(results),
            'mode': statistics.mode(results) if len(set(results)) < len(results) else None,
            'std_deviation': statistics.stdev(results) if len(results) > 1 else 0.0,
            'variance': statistics.variance(results) if len(results) > 1 else 0.0,
            'min_result': min(results),
            'max_result': max(results),
            'range': max(results) - min(results),
            'win_rate': len([r for r in results if r > 0]) / len(results),
            'loss_rate': len([r for r in results if r < 0]) / len(results),
            'break_even_rate': len([r for r in results if r == 0]) / len(results)
        }
    
    def calculate_standard_deviation(self, population: bool = False) -> float:
        """Calculate standard deviation (sample or population)."""
        if len(self.sessions) < 2:
            return 0.0
            
        results = [s.profit_loss for s in self.sessions]
        
        if population:
            return statistics.pstdev(results)
        else:
            return statistics.stdev(results)
    
    def calculate_confidence_intervals(self, confidence_levels: List[float] = None) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for expected results."""
        if confidence_levels is None:
            confidence_levels = [0.68, 0.95, 0.99]  # 1σ, 2σ, 3σ
            
        if len(self.sessions) < 2:
            return {}
            
        mean_result = statistics.mean([s.profit_loss for s in self.sessions])
        std_dev = self.calculate_standard_deviation()
        
        intervals = {}
        
        for level in confidence_levels:
            # Calculate z-score for confidence level
            z_score = self._get_z_score_for_confidence(level)
            
            margin_of_error = z_score * std_dev
            lower_bound = mean_result - margin_of_error
            upper_bound = mean_result + margin_of_error
            
            intervals[f'{level:.0%}'] = (lower_bound, upper_bound)
            
        return intervals
    
    def _get_z_score_for_confidence(self, confidence_level: float) -> float:
        """Get z-score for given confidence level."""
        # Common z-scores for confidence intervals
        z_scores = {
            0.68: 1.0,   # ~68% (1σ)
            0.90: 1.645,
            0.95: 1.96,  # 95% (2σ)
            0.99: 2.576, # 99% (3σ)
        }
        
        return z_scores.get(confidence_level, 1.96)  # Default to 95%
    
    def simulate_downswing(self, sessions: int = 1000, percentiles: List[float] = None) -> Dict[str, float]:
        """Simulate potential downswings using current statistics."""
        if percentiles is None:
            percentiles = [0.05, 0.10, 0.25, 0.50]  # 5%, 10%, 25%, 50% worst cases
            
        if len(self.sessions) < 2:
            return {}
            
        mean_result = statistics.mean([s.profit_loss for s in self.sessions])
        std_dev = self.calculate_standard_deviation()
        
        # Run Monte Carlo simulation
        simulated_cumulative = []
        
        for _ in range(1000):  # 1000 simulations
            cumulative = 0
            worst_point = 0
            
            for _ in range(sessions):
                # Sample from normal distribution
                session_result = random.normalvariate(mean_result, std_dev)
                cumulative += session_result
                worst_point = min(worst_point, cumulative)
            
            simulated_cumulative.append(worst_point)
        
        # Calculate percentiles
        simulated_cumulative.sort()
        downswings = {}
        
        for percentile in percentiles:
            index = int(len(simulated_cumulative) * percentile)
            downswings[f'{percentile:.0%}_worst'] = simulated_cumulative[index]
            
        return downswings
    
    def calculate_risk_of_ruin(self, bankroll: float, ruin_level: float = 0.0,
                             sessions_ahead: int = 1000) -> float:
        """Calculate probability of bankroll falling below ruin level."""
        if len(self.sessions) < 2 or bankroll <= ruin_level:
            return 1.0 if bankroll <= ruin_level else 0.0
            
        mean_result = statistics.mean([s.profit_loss for s in self.sessions])
        std_dev = self.calculate_standard_deviation()
        
        if mean_result <= 0:
            return 1.0  # Negative expectation = certain ruin
        
        # Use Monte Carlo simulation for more accurate risk of ruin
        ruin_count = 0
        simulations = 10000
        
        for _ in range(simulations):
            current_bankroll = bankroll
            
            for _ in range(sessions_ahead):
                session_result = random.normalvariate(mean_result, std_dev)
                current_bankroll += session_result
                
                if current_bankroll <= ruin_level:
                    ruin_count += 1
                    break
                    
        return ruin_count / simulations
    
    def monte_carlo_bankroll_projection(self, initial_bankroll: float, 
                                      sessions: int = 1000, 
                                      simulations: int = 1000) -> Dict[str, Any]:
        """Run Monte Carlo simulation for bankroll projection."""
        if len(self.sessions) < 2:
            return {'error': 'Insufficient data for Monte Carlo simulation'}
            
        mean_result = statistics.mean([s.profit_loss for s in self.sessions])
        std_dev = self.calculate_standard_deviation()
        
        final_bankrolls = []
        peak_bankrolls = []
        trough_bankrolls = []
        
        for _ in range(simulations):
            bankroll = initial_bankroll
            peak = initial_bankroll
            trough = initial_bankroll
            
            for _ in range(sessions):
                session_result = random.normalvariate(mean_result, std_dev)
                bankroll += session_result
                peak = max(peak, bankroll)
                trough = min(trough, bankroll)
                
            final_bankrolls.append(bankroll)
            peak_bankrolls.append(peak)
            trough_bankrolls.append(trough)
        
        # Calculate statistics
        final_bankrolls.sort()
        peak_bankrolls.sort()
        trough_bankrolls.sort()
        
        return {
            'sessions_simulated': sessions,
            'simulations_run': simulations,
            'expected_final_bankroll': statistics.mean(final_bankrolls),
            'median_final_bankroll': statistics.median(final_bankrolls),
            'final_bankroll_percentiles': {
                '5%': final_bankrolls[int(0.05 * len(final_bankrolls))],
                '25%': final_bankrolls[int(0.25 * len(final_bankrolls))],
                '75%': final_bankrolls[int(0.75 * len(final_bankrolls))],
                '95%': final_bankrolls[int(0.95 * len(final_bankrolls))]
            },
            'expected_peak_bankroll': statistics.mean(peak_bankrolls),
            'expected_trough_bankroll': statistics.mean(trough_bankrolls),
            'probability_of_profit': len([b for b in final_bankrolls if b > initial_bankroll]) / len(final_bankrolls),
            'probability_of_loss': len([b for b in final_bankrolls if b < initial_bankroll]) / len(final_bankrolls)
        }
    
    def calculate_hourly_variance(self) -> Dict[str, float]:
        """Calculate variance statistics on an hourly basis."""
        if not self.sessions:
            return {}
            
        # Calculate hourly results
        hourly_results = []
        for session in self.sessions:
            if session.session_length > 0:
                hourly_rate = session.profit_loss / session.session_length
                hourly_results.append(hourly_rate)
        
        if len(hourly_results) < 2:
            return {}
            
        return {
            'hourly_mean': statistics.mean(hourly_results),
            'hourly_std_dev': statistics.stdev(hourly_results),
            'hourly_variance': statistics.variance(hourly_results),
            'hourly_win_rate': len([r for r in hourly_results if r > 0]) / len(hourly_results),
            'best_hourly': max(hourly_results),
            'worst_hourly': min(hourly_results)
        }
    
    def generate_comprehensive_report(self, bankroll: float = 10000,
                                    projection_sessions: int = 1000) -> VarianceReport:
        """Generate a comprehensive variance analysis report."""
        if len(self.sessions) < 2:
            return VarianceReport(
                total_sessions=len(self.sessions),
                total_profit_loss=sum([s.profit_loss for s in self.sessions]) if self.sessions else 0,
                win_rate=0,
                roi=0,
                standard_deviation=0,
                variance=0,
                confidence_intervals={},
                downswing_probabilities={},
                risk_of_ruin=1.0,
                expected_bankroll_swings={}
            )
        
        basic_stats = self.calculate_basic_statistics()
        confidence_intervals = self.calculate_confidence_intervals()
        downswing_sims = self.simulate_downswing(projection_sessions)
        risk_of_ruin = self.calculate_risk_of_ruin(bankroll, 0, projection_sessions)
        monte_carlo = self.monte_carlo_bankroll_projection(bankroll, projection_sessions)
        
        # Calculate expected swings
        std_dev = basic_stats['std_deviation']
        expected_swings = {
            '1_std_dev': (-std_dev, std_dev),
            '2_std_dev': (-2 * std_dev, 2 * std_dev),
            '3_std_dev': (-3 * std_dev, 3 * std_dev)
        }
        
        # Calculate ROI if buy-ins are tracked
        total_buy_ins = sum([s.buy_in for s in self.sessions if s.buy_in > 0])
        roi = (basic_stats['total_profit_loss'] / total_buy_ins * 100) if total_buy_ins > 0 else 0
        
        return VarianceReport(
            total_sessions=basic_stats['count'],
            total_profit_loss=basic_stats['total_profit_loss'],
            win_rate=basic_stats['win_rate'],
            roi=roi,
            standard_deviation=basic_stats['std_deviation'],
            variance=basic_stats['variance'],
            confidence_intervals=confidence_intervals,
            downswing_probabilities=downswing_sims,
            risk_of_ruin=risk_of_ruin,
            expected_bankroll_swings=expected_swings,
            monte_carlo_results=monte_carlo
        )

# Standalone utility functions
def calculate_variance(results: List[float]) -> float:
    """Calculate variance of a list of results."""
    if len(results) < 2:
        return 0.0
    return statistics.variance(results)

def calculate_standard_deviation(results: List[float]) -> float:
    """Calculate standard deviation of a list of results."""
    if len(results) < 2:
        return 0.0
    return statistics.stdev(results)

def simulate_sessions(mean: float, std_dev: float, sessions: int = 1000) -> List[float]:
    """Simulate poker sessions with given mean and standard deviation."""
    return [random.normalvariate(mean, std_dev) for _ in range(sessions)]

def calculate_confidence_interval(results: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval for a given confidence level."""
    if len(results) < 2:
        return (0.0, 0.0)
        
    mean = statistics.mean(results)
    std_dev = statistics.stdev(results)
    
    # Simple z-score approximation
    z_score = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    margin = z_score * std_dev
    return (mean - margin, mean + margin)

def quick_risk_analysis(results: List[float], bankroll: float) -> Dict[str, Any]:
    """Quick risk analysis for a set of results."""
    if len(results) < 2:
        return {'error': 'Need at least 2 results'}
    
    calc = VarianceCalculator()
    calc.add_sessions_bulk(results)
    
    basic_stats = calc.calculate_basic_statistics()
    
    return {
        'win_rate': basic_stats['win_rate'],
        'avg_result': basic_stats['mean'],
        'std_deviation': basic_stats['std_deviation'],
        'best_result': basic_stats['max_result'],
        'worst_result': basic_stats['min_result'],
        'confidence_95': calculate_confidence_interval(results, 0.95),
        'estimated_risk_of_ruin': calc.calculate_risk_of_ruin(bankroll, 0, 500)
    }

if __name__ == '__main__':
    # Test variance calculator
    calc = VarianceCalculator()
    
    # Add sample session data
    sample_results = [
        25, -15, 40, -25, 15, 30, -10, 20, -35, 45,
        -20, 35, 10, -40, 25, 15, -30, 50, -15, 20,
        -25, 30, 5, -45, 35, -10, 25, 40, -20, 15
    ]
    
    for result in sample_results:
        calc.add_session(result, buy_in=100, session_length=2.0)
    
    print("Variance Calculator Test Results:")
    
    # Basic statistics
    basic_stats = calc.calculate_basic_statistics()
    print(f"Total sessions: {basic_stats['count']}")
    print(f"Total P&L: ${basic_stats['total_profit_loss']:.2f}")
    print(f"Average result: ${basic_stats['mean']:.2f}")
    print(f"Standard deviation: ${basic_stats['std_deviation']:.2f}")
    print(f"Win rate: {basic_stats['win_rate']:.2%}")
    
    # Confidence intervals
    confidence_intervals = calc.calculate_confidence_intervals()
    print(f"\nConfidence Intervals:")
    for level, (lower, upper) in confidence_intervals.items():
        print(f"{level}: ${lower:.2f} to ${upper:.2f}")
    
    # Downswing simulation
    downswings = calc.simulate_downswing(1000)
    print(f"\nSimulated Downswings (1000 sessions):")
    for percentile, amount in downswings.items():
        print(f"{percentile}: ${amount:.2f}")
    
    # Risk of ruin
    risk_of_ruin = calc.calculate_risk_of_ruin(1000, 0, 1000)
    print(f"\nRisk of ruin (1000 sessions, $1000 bankroll): {risk_of_ruin:.2%}")
    
    # Monte Carlo projection
    monte_carlo = calc.monte_carlo_bankroll_projection(1000, 500, 1000)
    print(f"\nMonte Carlo Projection (500 sessions):")
    print(f"Expected final bankroll: ${monte_carlo['expected_final_bankroll']:.2f}")
    print(f"Probability of profit: {monte_carlo['probability_of_profit']:.2%}")
    
    # Comprehensive report
    report = calc.generate_comprehensive_report(bankroll=1000)
    print(f"\nComprehensive Report Generated:")
    print(f"ROI: {report.roi:.2%}")
    print(f"Risk of Ruin: {report.risk_of_ruin:.2%}")
    
    print("\nVariance calculator test completed!")
