"""
Automated Hand Tagging System

Uses AI to automatically tag poker hands with categories like bluff, value_bet,
hero_call, made_mistake, good_fold, etc. for easier hand review and analysis.
"""
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class HandTag(str, Enum):
    """Standard hand tags"""
    BLUFF = "bluff"
    VALUE_BET = "value_bet"
    HERO_CALL = "hero_call"
    HERO_FOLD = "hero_fold"
    MADE_MISTAKE = "made_mistake"
    GOOD_FOLD = "good_fold"
    GOOD_CALL = "good_call"
    COOLER = "cooler"
    BAD_BEAT = "bad_beat"
    THIN_VALUE = "thin_value"
    OVERBET = "overbet"
    UNDERBET = "underbet"
    MISSED_VALUE = "missed_value"
    PREMIUM_HAND = "premium_hand"
    SPECULATIVE = "speculative"


@dataclass
class TaggedHand:
    """Hand with tags"""
    hand_id: str
    tags: Set[HandTag]
    confidence_scores: Dict[HandTag, float]
    reasoning: Dict[HandTag, str]
    metadata: Optional[Dict] = None


class HandTagger:
    """Automatically tag hands for review and analysis"""

    def __init__(self):
        self.confidence_threshold = 0.7  # Minimum confidence to assign tag

    def tag_hand(
        self,
        hand_id: str,
        hole_cards: List[str],
        board_cards: List[str],
        actions: List[Dict],
        pot_size: float,
        won_hand: bool,
        showdown: bool = False
    ) -> TaggedHand:
        """
        Automatically tag a poker hand

        Args:
            hand_id: Unique hand identifier
            hole_cards: Player's hole cards
            board_cards: Community cards
            actions: List of actions (bet, call, raise, fold)
            pot_size: Final pot size
            won_hand: Whether player won
            showdown: Whether hand went to showdown

        Returns:
            TaggedHand with assigned tags and reasoning
        """
        tags = set()
        confidence_scores = {}
        reasoning = {}

        # Analyze hand strength
        hand_strength = self._evaluate_hand_strength(hole_cards, board_cards)

        # Check for premium hands
        if self._is_premium_preflop(hole_cards):
            tags.add(HandTag.PREMIUM_HAND)
            confidence_scores[HandTag.PREMIUM_HAND] = 0.95
            reasoning[HandTag.PREMIUM_HAND] = "Premium starting hand (AA, KK, QQ, AKs)"

        # Analyze actions for bluffs
        bluff_analysis = self._analyze_bluff(actions, hand_strength, showdown, won_hand)
        if bluff_analysis['is_bluff'] and bluff_analysis['confidence'] >= self.confidence_threshold:
            tags.add(HandTag.BLUFF)
            confidence_scores[HandTag.BLUFF] = bluff_analysis['confidence']
            reasoning[HandTag.BLUFF] = bluff_analysis['reasoning']

        # Value bet analysis
        value_analysis = self._analyze_value_bet(actions, hand_strength, showdown)
        if value_analysis['is_value'] and value_analysis['confidence'] >= self.confidence_threshold:
            tag = HandTag.THIN_VALUE if hand_strength < 0.7 else HandTag.VALUE_BET
            tags.add(tag)
            confidence_scores[tag] = value_analysis['confidence']
            reasoning[tag] = value_analysis['reasoning']

        # Hero call/fold analysis
        if showdown:
            hero_analysis = self._analyze_hero_play(actions, hand_strength, won_hand)
            if hero_analysis['tag'] and hero_analysis['confidence'] >= self.confidence_threshold:
                tags.add(hero_analysis['tag'])
                confidence_scores[hero_analysis['tag']] = hero_analysis['confidence']
                reasoning[hero_analysis['tag']] = hero_analysis['reasoning']

        # Cooler/bad beat detection
        if not won_hand and hand_strength > 0.85:
            if showdown:
                tags.add(HandTag.BAD_BEAT)
                confidence_scores[HandTag.BAD_BEAT] = 0.9
                reasoning[HandTag.BAD_BEAT] = "Very strong hand lost at showdown"
            else:
                tags.add(HandTag.COOLER)
                confidence_scores[HandTag.COOLER] = 0.85
                reasoning[HandTag.COOLER] = "Premium hand forced to fold"

        # Betting size analysis
        sizing_analysis = self._analyze_bet_sizing(actions, pot_size)
        if sizing_analysis['tag'] and sizing_analysis['confidence'] >= self.confidence_threshold:
            tags.add(sizing_analysis['tag'])
            confidence_scores[sizing_analysis['tag']] = sizing_analysis['confidence']
            reasoning[sizing_analysis['tag']] = sizing_analysis['reasoning']

        # Mistake detection
        mistake_analysis = self._detect_mistakes(
            actions, hand_strength, won_hand, showdown
        )
        if mistake_analysis['is_mistake'] and mistake_analysis['confidence'] >= self.confidence_threshold:
            tags.add(HandTag.MADE_MISTAKE)
            confidence_scores[HandTag.MADE_MISTAKE] = mistake_analysis['confidence']
            reasoning[HandTag.MADE_MISTAKE] = mistake_analysis['reasoning']

        return TaggedHand(
            hand_id=hand_id,
            tags=tags,
            confidence_scores=confidence_scores,
            reasoning=reasoning,
            metadata={
                'hand_strength': hand_strength,
                'won_hand': won_hand,
                'showdown': showdown,
                'pot_size': pot_size
            }
        )

    def _is_premium_preflop(self, hole_cards: List[str]) -> bool:
        """Check if starting hand is premium"""
        if len(hole_cards) != 2:
            return False

        ranks = [card[0] for card in hole_cards if len(card) > 0]
        if len(ranks) != 2:
            return False

        # Pocket pairs AA-QQ
        if ranks[0] == ranks[1] and ranks[0] in ['A', 'K', 'Q']:
            return True

        # AK suited or offsuit
        if set(ranks) == {'A', 'K'}:
            return True

        return False

    def _evaluate_hand_strength(self, hole_cards: List[str], board_cards: List[str]) -> float:
        """Simple hand strength evaluation (0.0 to 1.0)"""
        # Simplified evaluation - in production use proper equity calculator
        if not hole_cards or len(hole_cards) != 2:
            return 0.0

        # Basic rank evaluation
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        rank_values = {r: i for i, r in enumerate(ranks)}

        try:
            hole_ranks = [card[0] for card in hole_cards if len(card) > 0]
            if len(hole_ranks) != 2:
                return 0.0

            # Pocket pairs get bonus
            if hole_ranks[0] == hole_ranks[1]:
                pair_value = rank_values.get(hole_ranks[0], 0) / len(ranks)
                return min(1.0, 0.6 + pair_value * 0.4)

            # High card value
            values = [rank_values.get(r, 0) for r in hole_ranks]
            return sum(values) / (2 * len(ranks))

        except (IndexError, KeyError):
            return 0.5

    def _analyze_bluff(
        self,
        actions: List[Dict],
        hand_strength: float,
        showdown: bool,
        won_hand: bool
    ) -> Dict:
        """Analyze if hand contains a bluff"""
        # Look for aggressive actions with weak hand
        aggressive_actions = [a for a in actions if a.get('type') in ['bet', 'raise']]

        if not aggressive_actions or hand_strength > 0.6:
            return {'is_bluff': False, 'confidence': 0.0, 'reasoning': ''}

        # Bluff detected if weak hand made aggressive moves
        if not showdown and won_hand:
            # Won without showdown with weak hand - likely bluff
            return {
                'is_bluff': True,
                'confidence': 0.85,
                'reasoning': f"Weak hand ({hand_strength:.2f}) won without showdown after aggressive action"
            }
        elif showdown and not won_hand and len(aggressive_actions) > 1:
            # Failed bluff attempt
            return {
                'is_bluff': True,
                'confidence': 0.75,
                'reasoning': f"Weak hand ({hand_strength:.2f}) made multiple aggressive actions but lost"
            }

        return {'is_bluff': False, 'confidence': 0.0, 'reasoning': ''}

    def _analyze_value_bet(
        self,
        actions: List[Dict],
        hand_strength: float,
        showdown: bool
    ) -> Dict:
        """Analyze value betting"""
        if hand_strength < 0.5:
            return {'is_value': False, 'confidence': 0.0, 'reasoning': ''}

        # Look for betting with strong hand
        bet_actions = [a for a in actions if a.get('type') in ['bet', 'raise']]

        if bet_actions and hand_strength >= 0.7:
            return {
                'is_value': True,
                'confidence': 0.85,
                'reasoning': f"Strong hand ({hand_strength:.2f}) bet for value"
            }
        elif bet_actions and hand_strength >= 0.55:
            # Thin value
            return {
                'is_value': True,
                'confidence': 0.70,
                'reasoning': f"Medium hand ({hand_strength:.2f}) bet thinly for value"
            }

        return {'is_value': False, 'confidence': 0.0, 'reasoning': ''}

    def _analyze_hero_play(
        self,
        actions: List[Dict],
        hand_strength: float,
        won_hand: bool
    ) -> Dict:
        """Analyze hero calls/folds"""
        # Look for big calls or folds with marginal hands
        calls = [a for a in actions if a.get('type') == 'call']
        folds = [a for a in actions if a.get('type') == 'fold']

        # Hero call: called big bet with marginal hand and won
        if calls and 0.4 <= hand_strength <= 0.65 and won_hand:
            return {
                'tag': HandTag.HERO_CALL,
                'confidence': 0.80,
                'reasoning': f"Called with marginal hand ({hand_strength:.2f}) and won"
            }

        # Hero fold: folded strong hand (difficult laydown)
        if folds and hand_strength >= 0.7:
            return {
                'tag': HandTag.HERO_FOLD,
                'confidence': 0.75,
                'reasoning': f"Folded strong hand ({hand_strength:.2f}) under pressure"
            }

        # Good fold: folded marginal/weak hand
        if folds and hand_strength < 0.5:
            return {
                'tag': HandTag.GOOD_FOLD,
                'confidence': 0.70,
                'reasoning': f"Folded weak hand ({hand_strength:.2f})"
            }

        return {'tag': None, 'confidence': 0.0, 'reasoning': ''}

    def _analyze_bet_sizing(self, actions: List[Dict], pot_size: float) -> Dict:
        """Analyze bet sizing"""
        for action in actions:
            if action.get('type') in ['bet', 'raise']:
                amount = action.get('amount', 0)
                if pot_size > 0:
                    bet_to_pot = amount / pot_size

                    # Overbet
                    if bet_to_pot > 1.5:
                        return {
                            'tag': HandTag.OVERBET,
                            'confidence': 0.85,
                            'reasoning': f"Bet {bet_to_pot:.1f}x pot (overbet)"
                        }

                    # Underbet
                    if bet_to_pot < 0.3:
                        return {
                            'tag': HandTag.UNDERBET,
                            'confidence': 0.80,
                            'reasoning': f"Bet {bet_to_pot:.1f}x pot (underbet)"
                        }

        return {'tag': None, 'confidence': 0.0, 'reasoning': ''}

    def _detect_mistakes(
        self,
        actions: List[Dict],
        hand_strength: float,
        won_hand: bool,
        showdown: bool
    ) -> Dict:
        """Detect potential mistakes"""
        # Folding premium hand preflop
        if any(a.get('type') == 'fold' for a in actions[:2]) and hand_strength > 0.85:
            return {
                'is_mistake': True,
                'confidence': 0.90,
                'reasoning': "Folded premium hand too early"
            }

        # Calling with very weak hand
        if showdown and not won_hand and hand_strength < 0.2:
            calls = [a for a in actions if a.get('type') == 'call']
            if len(calls) >= 2:
                return {
                    'is_mistake': True,
                    'confidence': 0.80,
                    'reasoning': f"Called multiple times with very weak hand ({hand_strength:.2f})"
                }

        return {'is_mistake': False, 'confidence': 0.0, 'reasoning': ''}

    def get_tag_description(self, tag: HandTag) -> str:
        """Get human-readable description of tag"""
        descriptions = {
            HandTag.BLUFF: "Aggressive play with weak hand",
            HandTag.VALUE_BET: "Betting for value with strong hand",
            HandTag.HERO_CALL: "Difficult call with marginal hand that won",
            HandTag.HERO_FOLD: "Difficult fold of strong hand",
            HandTag.MADE_MISTAKE: "Suboptimal play detected",
            HandTag.GOOD_FOLD: "Correct fold of weak hand",
            HandTag.GOOD_CALL: "Correct call that paid off",
            HandTag.COOLER: "Very strong hand that had to fold",
            HandTag.BAD_BEAT: "Very strong hand lost at showdown",
            HandTag.THIN_VALUE: "Betting marginal hand for thin value",
            HandTag.OVERBET: "Bet larger than pot",
            HandTag.UNDERBET: "Bet much smaller than pot",
            HandTag.MISSED_VALUE: "Failed to extract value from strong hand",
            HandTag.PREMIUM_HAND: "Premium starting hand (AA, KK, QQ, AK)",
            HandTag.SPECULATIVE: "Speculative hand (suited connectors, small pairs)"
        }
        return descriptions.get(tag, "No description available")
