"""Bet type classification (value/bluff/block)."""
import logging
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)

class BetType(Enum):
    VALUE = "value"
    BLUFF = "bluff"
    BLOCK = "block"
    UNKNOWN = "unknown"

class BetTypeClassifier:
    """Classify bet types based on context."""
    
    def __init__(self):
        self.hand_strength_threshold_value = 0.7
        self.hand_strength_threshold_bluff = 0.3
    
    def classify_bet(
        self,
        bet_size: float,
        pot_size: float,
        hand_strength: float,
        board_texture: str = "dry"
    ) -> BetType:
        """Classify bet as value, bluff, or block."""
        bet_ratio = bet_size / pot_size if pot_size > 0 else 0
        
        if hand_strength >= self.hand_strength_threshold_value:
            # Strong hand - value bet
            return BetType.VALUE
        
        elif hand_strength <= self.hand_strength_threshold_bluff:
            # Weak hand
            if bet_ratio > 0.5:
                # Large bet with weak hand - bluff
                return BetType.BLUFF
            else:
                # Small bet - block bet
                return BetType.BLOCK
        
        return BetType.UNKNOWN
    
    def get_bet_type_stats(self, bet_history: List[Dict]) -> Dict[str, int]:
        """Get statistics on bet types."""
        stats = {bt.value: 0 for bt in BetType}
        
        for bet in bet_history:
            bet_type = bet.get('type', BetType.UNKNOWN)
            if isinstance(bet_type, BetType):
                stats[bet_type.value] += 1
        
        return stats
