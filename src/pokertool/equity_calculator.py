"""
Equity Calculator

Calculates hand equity and range-vs-range equity.
Note: This is a simplified implementation. Production would use Monte Carlo simulation.
"""
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class EquityCalculator:
    """Calculate poker hand equity"""

    def __init__(self):
        # Simplified hand strength rankings (0-1 scale)
        self.hand_strengths = self._build_hand_strengths()

    def _build_hand_strengths(self) -> Dict[str, float]:
        """Build approximate hand strength rankings"""
        strengths = {}

        # Pocket pairs (strongest)
        pairs = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22']
        for i, pair in enumerate(pairs):
            strengths[pair] = 1.0 - (i * 0.05)  # AA=1.0, KK=0.95, etc.

        # Suited broadway
        suited_broadway = [
            'AKs', 'AQs', 'AJs', 'ATs',
            'KQs', 'KJs', 'KTs',
            'QJs', 'QTs',
            'JTs'
        ]
        for i, hand in enumerate(suited_broadway):
            strengths[hand] = 0.85 - (i * 0.03)

        # Offsuit broadway
        offsuit_broadway = [
            'AKo', 'AQo', 'AJo', 'ATo',
            'KQo', 'KJo', 'KTo',
            'QJo', 'QTo',
            'JTo'
        ]
        for i, hand in enumerate(offsuit_broadway):
            strengths[hand] = 0.75 - (i * 0.03)

        # Suited connectors
        suited_connectors = ['T9s', '98s', '87s', '76s', '65s', '54s']
        for i, hand in enumerate(suited_connectors):
            strengths[hand] = 0.60 - (i * 0.03)

        # Medium pairs
        med_pairs = ['A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s']
        for i, hand in enumerate(med_pairs):
            strengths[hand] = 0.55 - (i * 0.02)

        # Default for unlisted hands
        return strengths

    def get_hand_strength(self, hand: str) -> float:
        """Get approximate strength of a hand (0-1 scale)"""
        return self.hand_strengths.get(hand, 0.3)  # Default to weak

    def calculate_hand_vs_hand(self, hero_hand: str, villain_hand: str) -> float:
        """
        Calculate equity of hero hand vs villain hand (simplified)

        Args:
            hero_hand: Hero's hand notation (e.g., 'AKs')
            villain_hand: Villain's hand notation (e.g., 'QQ')

        Returns:
            Hero's equity percentage (0-100)
        """
        hero_strength = self.get_hand_strength(hero_hand)
        villain_strength = self.get_hand_strength(villain_hand)

        # Simplified equity calculation
        # In reality, would need to account for blockers, board texture, etc.
        total_strength = hero_strength + villain_strength

        if total_strength == 0:
            return 50.0

        equity = (hero_strength / total_strength) * 100

        # Add variance for realism (±5%)
        import random
        variance = random.uniform(-5, 5)
        equity = max(0, min(100, equity + variance))

        logger.debug(f"{hero_hand} vs {villain_hand}: {equity:.1f}% equity")

        return equity

    def calculate_range_vs_range(
        self,
        hero_range: List[str],
        villain_range: List[str]
    ) -> Dict[str, float]:
        """
        Calculate range-vs-range equity (simplified)

        Args:
            hero_range: List of hero hands
            villain_range: List of villain hands

        Returns:
            Dictionary with equity stats
        """
        if not hero_range or not villain_range:
            return {
                'hero_equity': 50.0,
                'villain_equity': 50.0,
                'tie_equity': 0.0
            }

        # Calculate average strength of each range
        hero_avg_strength = sum(self.get_hand_strength(h) for h in hero_range) / len(hero_range)
        villain_avg_strength = sum(self.get_hand_strength(h) for h in villain_range) / len(villain_range)

        total_strength = hero_avg_strength + villain_avg_strength

        if total_strength == 0:
            hero_equity = 50.0
        else:
            hero_equity = (hero_avg_strength / total_strength) * 100

        villain_equity = 100 - hero_equity

        logger.info(
            f"Range equity: Hero ({len(hero_range)} hands) {hero_equity:.1f}% "
            f"vs Villain ({len(villain_range)} hands) {villain_equity:.1f}%"
        )

        return {
            'hero_equity': hero_equity,
            'villain_equity': villain_equity,
            'tie_equity': 0.0,
            'hero_range_size': len(hero_range),
            'villain_range_size': len(villain_range),
            'hero_avg_strength': hero_avg_strength,
            'villain_avg_strength': villain_avg_strength
        }

    def calculate_hand_vs_range(
        self,
        hero_hand: str,
        villain_range: List[str]
    ) -> float:
        """
        Calculate equity of specific hand vs opponent range

        Args:
            hero_hand: Hero's specific hand
            villain_range: Opponent's estimated range

        Returns:
            Hero's equity percentage
        """
        if not villain_range:
            return 50.0

        # Calculate equity vs each hand in range, then average
        equities = []
        for villain_hand in villain_range:
            equity = self.calculate_hand_vs_hand(hero_hand, villain_hand)
            equities.append(equity)

        avg_equity = sum(equities) / len(equities)

        logger.debug(f"{hero_hand} vs range ({len(villain_range)} hands): {avg_equity:.1f}% equity")

        return avg_equity

    def get_equity_category(self, equity: float) -> str:
        """Categorize equity into buckets"""
        if equity >= 70:
            return "Very Strong"
        elif equity >= 55:
            return "Strong"
        elif equity >= 45:
            return "Medium"
        elif equity >= 30:
            return "Weak"
        else:
            return "Very Weak"
