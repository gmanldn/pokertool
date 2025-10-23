#!/usr/bin/env python3
"""AI-powered session review and summary generation."""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SessionReviewer:
    """Generates AI-powered session summaries and reviews."""

    def generate_summary(self, hands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate session summary from hands played.

        Args:
            hands: List of hand dictionaries with results

        Returns:
            Summary dict with key_hands, mistakes, wins, improvements
        """
        if not hands:
            return {
                'key_hands': [],
                'mistakes': [],
                'wins': [],
                'improvements': [],
                'stats': {}
            }

        # Calculate basic stats
        total_hands = len(hands)
        won_hands = sum(1 for h in hands if h.get('result') == 'win')
        win_rate = (won_hands / total_hands * 100) if total_hands > 0 else 0

        total_profit = sum(h.get('profit', 0) for h in hands)

        # Identify key hands (largest pots)
        key_hands = sorted(hands, key=lambda x: abs(x.get('pot', 0)), reverse=True)[:5]

        # Simple mistake detection (hands with large losses)
        mistakes = [h for h in hands if h.get('profit', 0) < -50][:3]

        # Biggest wins
        wins = sorted([h for h in hands if h.get('profit', 0) > 0],
                     key=lambda x: x.get('profit', 0), reverse=True)[:3]

        # Generate improvements
        improvements = []
        if win_rate < 40:
            improvements.append("Focus on tighter hand selection")
        if total_profit < 0:
            improvements.append("Review position-based strategy")
        if len(mistakes) > total_hands * 0.2:
            improvements.append("Reduce high-risk plays")

        return {
            'key_hands': [self._format_hand(h) for h in key_hands],
            'mistakes': [self._format_hand(h) for h in mistakes],
            'wins': [self._format_hand(h) for h in wins],
            'improvements': improvements,
            'stats': {
                'total_hands': total_hands,
                'win_rate': round(win_rate, 1),
                'total_profit': round(total_profit, 2)
            }
        }

    def _format_hand(self, hand: Dict[str, Any]) -> str:
        """Format hand for display."""
        cards = hand.get('hole_cards', 'Unknown')
        pot = hand.get('pot', 0)
        profit = hand.get('profit', 0)
        result = hand.get('result', 'unknown')

        return f"{cards} - Pot: ${pot}, Result: {result} (${profit:+.2f})"


_reviewer_instance: Optional[SessionReviewer] = None

def get_session_reviewer() -> SessionReviewer:
    """Get global session reviewer."""
    global _reviewer_instance
    if _reviewer_instance is None:
        _reviewer_instance = SessionReviewer()
    return _reviewer_instance
