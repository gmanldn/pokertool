"""Bet sizing trend analysis."""
import logging
from typing import List, Dict, Optional
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)

class BetSizingTrendAnalyzer:
    """Analyze bet sizing trends over time."""
    
    def __init__(self, history_size: int = 100):
        self.bet_history = deque(maxlen=history_size)
        self.position_history = {}
    
    def add_bet(self, bet_size: float, pot_size: float, position: str, hand_result: str):
        """Add bet to history."""
        bet_ratio = bet_size / pot_size if pot_size > 0 else 0
        
        self.bet_history.append({
            'size': bet_size,
            'pot': pot_size,
            'ratio': bet_ratio,
            'position': position,
            'result': hand_result
        })
        
        if position not in self.position_history:
            self.position_history[position] = []
        self.position_history[position].append(bet_ratio)
    
    def get_average_bet_size(self, position: Optional[str] = None) -> float:
        """Get average bet size ratio."""
        if position:
            ratios = self.position_history.get(position, [])
        else:
            ratios = [b['ratio'] for b in self.bet_history]
        
        return np.mean(ratios) if ratios else 0.0
    
    def get_bet_size_trend(self, window: int = 20) -> str:
        """Get recent bet sizing trend (increasing/decreasing/stable)."""
        if len(self.bet_history) < window:
            return "insufficient_data"
        
        recent = list(self.bet_history)[-window:]
        ratios = [b['ratio'] for b in recent]
        
        # Linear regression to detect trend
        x = np.arange(len(ratios))
        slope = np.polyfit(x, ratios, 1)[0]
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def get_position_statistics(self) -> Dict[str, Dict]:
        """Get bet statistics by position."""
        stats = {}
        
        for position, ratios in self.position_history.items():
            stats[position] = {
                'count': len(ratios),
                'avg_ratio': np.mean(ratios),
                'std_ratio': np.std(ratios),
                'min_ratio': np.min(ratios),
                'max_ratio': np.max(ratios)
            }
        
        return stats
