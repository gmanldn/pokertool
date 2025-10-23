"""
Opponent Profiler

Estimates opponent ranges and profiles based on observed actions and statistics.
Enhanced with AI-powered profiling using LangChain for natural language insights.
"""
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Try to import LangChain dependencies
try:
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from langchain_community.llms import FakeListLLM
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PlayerType(str, Enum):
    """Player type classification"""
    LAG = "LAG"  # Loose-Aggressive
    TAG = "TAG"  # Tight-Aggressive
    LP = "LP"    # Loose-Passive
    TP = "TP"    # Tight-Passive
    BALANCED = "BALANCED"


class Action(str, Enum):
    """Poker actions"""
    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    BET = "BET"
    RAISE = "RAISE"
    THREE_BET = "3BET"
    FOUR_BET = "4BET"


@dataclass
class OpponentStats:
    """Opponent statistics"""
    vpip: float  # Voluntarily Put $ In Pot %
    pfr: float   # Preflop Raise %
    threebet: float  # 3-Bet %
    fold_to_cbet: float  # Fold to C-Bet %
    fold_to_threebet: float  # Fold to 3-Bet %
    aggression: float  # Aggression Factor
    hands_played: int


class OpponentProfiler:
    """Profiles opponents and estimates their ranges"""

    def __init__(self):
        # Preflop ranges by hand strength percentile
        self.all_hands = self._generate_all_hands()

    def _generate_all_hands(self) -> List[str]:
        """Generate all 169 poker hands in strength order (approximate)"""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        hands = []

        # Pocket pairs (strongest first)
        for rank in ranks:
            hands.append(f"{rank}{rank}")

        # Suited connectors and high cards
        for i, rank1 in enumerate(ranks):
            for j, rank2 in enumerate(ranks):
                if i < j:  # Upper triangle (suited)
                    hands.append(f"{rank1}{rank2}s")

        # Offsuit hands
        for i, rank1 in enumerate(ranks):
            for j, rank2 in enumerate(ranks):
                if i < j:  # Upper triangle
                    hands.append(f"{rank1}{rank2}o")

        return hands

    def classify_player_type(self, stats: OpponentStats) -> PlayerType:
        """
        Classify player type based on VPIP and PFR

        Args:
            stats: Opponent statistics

        Returns:
            Player type classification
        """
        vpip = stats.vpip
        pfr = stats.pfr

        if vpip >= 35 and pfr >= 25:
            return PlayerType.LAG
        elif vpip <= 20 and pfr >= 15:
            return PlayerType.TAG
        elif vpip >= 35 and pfr < 15:
            return PlayerType.LP
        elif vpip <= 20 and pfr < 15:
            return PlayerType.TP
        else:
            return PlayerType.BALANCED

    def estimate_range(
        self,
        stats: OpponentStats,
        position: str,
        action: Action,
        facing_raise: bool = False
    ) -> List[str]:
        """
        Estimate opponent's range based on stats, position, and action

        Args:
            stats: Opponent statistics
            position: Table position (UTG, MP, CO, BTN, SB, BB)
            action: Action taken
            facing_raise: Whether opponent is facing a raise

        Returns:
            List of hand notations in estimated range
        """
        player_type = self.classify_player_type(stats)

        # Base range percentage by position and player type
        base_range_pct = self._get_base_range_pct(position, player_type, facing_raise)

        # Adjust based on action
        if action == Action.RAISE or action == Action.THREE_BET:
            # Tighten range for aggressive actions
            range_pct = base_range_pct * 0.5
        elif action == Action.CALL:
            # Slightly tighten for calls
            range_pct = base_range_pct * 0.8
        elif action == Action.CHECK:
            # Very wide range for checks
            range_pct = min(100, base_range_pct * 1.5)
        else:
            range_pct = base_range_pct

        # Cap at 100%
        range_pct = min(100, range_pct)

        # Select top X% of hands
        num_hands = int(len(self.all_hands) * (range_pct / 100))
        estimated_range = self.all_hands[:num_hands]

        logger.debug(
            f"Estimated range for {player_type.value} in {position} "
            f"with {action.value}: {len(estimated_range)} hands ({range_pct:.1f}%)"
        )

        return estimated_range

    def _get_base_range_pct(
        self,
        position: str,
        player_type: PlayerType,
        facing_raise: bool
    ) -> float:
        """Get base range percentage by position and player type"""

        # Position multipliers (tighter in early position)
        position_multipliers = {
            'UTG': 0.7,
            'MP': 0.85,
            'CO': 1.0,
            'BTN': 1.3,
            'SB': 0.9,
            'BB': 1.1
        }

        # Base ranges by player type (% of hands played)
        type_base_ranges = {
            PlayerType.LAG: 45.0,   # Plays 45% of hands
            PlayerType.TAG: 20.0,   # Plays 20% of hands
            PlayerType.LP: 40.0,    # Plays 40% of hands
            PlayerType.TP: 15.0,    # Plays 15% of hands
            PlayerType.BALANCED: 28.0  # Plays 28% of hands
        }

        base = type_base_ranges.get(player_type, 25.0)
        multiplier = position_multipliers.get(position.upper(), 1.0)

        # Tighten significantly if facing a raise
        if facing_raise:
            multiplier *= 0.4

        return base * multiplier

    def narrow_range(
        self,
        current_range: List[str],
        action: Action,
        street: str,
        board: List[str]
    ) -> List[str]:
        """
        Narrow range based on postflop action

        Args:
            current_range: Current estimated range
            action: Action taken on this street
            street: Current street (flop, turn, river)
            board: Community cards

        Returns:
            Narrowed range
        """
        # Simplified range narrowing logic
        if action == Action.BET or action == Action.RAISE:
            # Aggressive action - keep top 60% of current range
            narrow_pct = 0.6
        elif action == Action.CALL:
            # Calling - keep top 75% (remove weakest hands)
            narrow_pct = 0.75
        elif action == Action.CHECK:
            # Checking - could be full range or weak
            narrow_pct = 0.9
        else:
            narrow_pct = 1.0

        num_hands = int(len(current_range) * narrow_pct)
        narrowed_range = current_range[:num_hands]

        logger.debug(
            f"Narrowed range on {street} after {action.value}: "
            f"{len(current_range)} → {len(narrowed_range)} hands"
        )

        return narrowed_range

    def get_range_strength(self, range_hands: List[str]) -> Dict[str, float]:
        """
        Analyze range strength

        Args:
            range_hands: List of hands in range

        Returns:
            Dictionary with range statistics
        """
        total = len(range_hands)
        if total == 0:
            return {
                'pairs': 0.0,
                'suited': 0.0,
                'offsuit': 0.0,
                'premium': 0.0,
                'broadway': 0.0
            }

        pairs = sum(1 for h in range_hands if len(h) == 2)
        suited = sum(1 for h in range_hands if 's' in h)
        offsuit = sum(1 for h in range_hands if 'o' in h)

        # Premium hands (AA-TT, AKs-AJs, AKo)
        premium_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', 'AKs', 'AQs', 'AJs', 'AKo']
        premium = sum(1 for h in range_hands if h in premium_hands)

        # Broadway hands (AKQJT)
        broadway_ranks = {'A', 'K', 'Q', 'J', 'T'}
        broadway = sum(
            1 for h in range_hands
            if len(h) >= 2 and h[0] in broadway_ranks and h[1] in broadway_ranks
        )

        return {
            'pairs': (pairs / total) * 100,
            'suited': (suited / total) * 100,
            'offsuit': (offsuit / total) * 100,
            'premium': (premium / total) * 100,
            'broadway': (broadway / total) * 100,
            'total_combos': total
        }

    def generate_ai_profile(
        self,
        stats: OpponentStats,
        hand_history: Optional[List[Dict]] = None,
        use_mock: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered natural language profile of opponent

        Args:
            stats: Opponent statistics
            hand_history: Optional list of hands played against opponent
            use_mock: Use mock LLM for testing (default False)

        Returns:
            Dictionary with profile information including:
            - playing_style: Text description of style
            - tendencies: List of key tendencies
            - exploitation_strategy: Recommended adjustments
            - confidence: Confidence score based on sample size
        """
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available, using fallback profiling")
            return self._generate_fallback_profile(stats, hand_history)

        player_type = self.classify_player_type(stats)

        # Calculate additional statistics
        fold_to_4bet = getattr(stats, 'fold_to_4bet', 0.0)
        cbet_frequency = getattr(stats, 'cbet_frequency', 0.0)

        # Build context from hand history
        hand_context = ""
        if hand_history and len(hand_history) > 0:
            recent_hands = hand_history[-5:]  # Last 5 hands
            hand_context = "\n".join([
                f"- Hand #{i+1}: {hand.get('action', 'N/A')} with {hand.get('cards', 'unknown')}"
                for i, hand in enumerate(recent_hands)
            ])

        # Create LangChain prompt
        prompt_template = PromptTemplate(
            input_variables=[
                "player_type", "vpip", "pfr", "threebet", "aggression",
                "fold_to_cbet", "fold_to_threebet", "fold_to_4bet",
                "cbet_frequency", "hands_played", "hand_context"
            ],
            template="""You are an expert poker analyst. Based on the following statistics, provide a concise player profile.

Player Type: {player_type}
VPIP: {vpip}%
PFR: {pfr}%
3-Bet: {threebet}%
Aggression Factor: {aggression}
Fold to C-Bet: {fold_to_cbet}%
Fold to 3-Bet: {fold_to_threebet}%
Fold to 4-Bet: {fold_to_4bet}%
C-Bet Frequency: {cbet_frequency}%
Hands Played: {hands_played}

Recent Hand History:
{hand_context}

Provide a brief analysis in the following format:

PLAYING STYLE:
[One sentence describing their overall approach]

KEY TENDENCIES:
- [Tendency 1]
- [Tendency 2]
- [Tendency 3]

EXPLOITATION STRATEGY:
[2-3 sentences on how to adjust against this player]

CONFIDENCE:
[HIGH/MEDIUM/LOW based on sample size]
"""
        )

        try:
            # Use FakeListLLM for testing or when LLM not configured
            if use_mock:
                responses = [
                    f"""PLAYING STYLE:
{player_type.value} player who plays {stats.vpip}% of hands with {stats.pfr}% preflop raises.

KEY TENDENCIES:
- Moderate aggression with {stats.aggression:.1f} aggression factor
- Folds to c-bets {stats.fold_to_cbet}% of the time
- 3-bets {stats.threebet}% when facing raises

EXPLOITATION STRATEGY:
Against this player, consider value betting more thinly when they show weakness. Be prepared to fold to their aggression unless you have strong holdings. Watch for their c-bet folding tendency and exploit with well-timed bluffs.

CONFIDENCE:
{'HIGH' if stats.hands_played >= 100 else 'MEDIUM' if stats.hands_played >= 50 else 'LOW'} (based on {stats.hands_played} hands)
"""
                ]
                llm = FakeListLLM(responses=responses)
            else:
                # In production, use actual LLM (OpenAI, Anthropic, etc.)
                # For now, use FakeListLLM as placeholder
                llm = FakeListLLM(responses=[
                    f"""PLAYING STYLE:
{player_type.value} player showing {stats.vpip}% VPIP with {stats.pfr}% PFR.

KEY TENDENCIES:
- Aggression factor of {stats.aggression:.1f}
- Folds to c-bets {stats.fold_to_cbet}%
- 3-bet frequency {stats.threebet}%

EXPLOITATION STRATEGY:
Adjust your strategy based on their tight/loose and passive/aggressive tendencies.

CONFIDENCE:
{'HIGH' if stats.hands_played >= 100 else 'MEDIUM' if stats.hands_played >= 50 else 'LOW'}
"""
                ])

            chain = LLMChain(llm=llm, prompt=prompt_template)

            # Generate profile
            response = chain.run(
                player_type=player_type.value,
                vpip=stats.vpip,
                pfr=stats.pfr,
                threebet=stats.threebet,
                aggression=stats.aggression,
                fold_to_cbet=stats.fold_to_cbet,
                fold_to_threebet=stats.fold_to_threebet,
                fold_to_4bet=fold_to_4bet,
                cbet_frequency=cbet_frequency,
                hands_played=stats.hands_played,
                hand_context=hand_context or "No recent hands available"
            )

            # Parse response
            profile = self._parse_profile_response(response, stats)

            logger.info(f"Generated AI profile for {player_type.value} player")
            return profile

        except Exception as e:
            logger.error(f"Error generating AI profile: {e}")
            return self._generate_fallback_profile(stats, hand_history)

    def _parse_profile_response(self, response: str, stats: OpponentStats) -> Dict[str, Any]:
        """Parse LLM response into structured profile"""
        lines = response.strip().split('\n')

        profile = {
            'playing_style': '',
            'tendencies': [],
            'exploitation_strategy': '',
            'confidence': 'MEDIUM',
            'player_type': self.classify_player_type(stats).value,
            'stats': asdict(stats)
        }

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if 'PLAYING STYLE:' in line:
                current_section = 'style'
            elif 'KEY TENDENCIES:' in line:
                current_section = 'tendencies'
            elif 'EXPLOITATION STRATEGY:' in line:
                current_section = 'strategy'
            elif 'CONFIDENCE:' in line:
                current_section = 'confidence'
            elif current_section == 'style' and not line.startswith('['):
                profile['playing_style'] = line
            elif current_section == 'tendencies' and line.startswith('-'):
                profile['tendencies'].append(line[1:].strip())
            elif current_section == 'strategy' and not line.startswith('['):
                profile['exploitation_strategy'] += line + ' '
            elif current_section == 'confidence':
                if 'HIGH' in line.upper():
                    profile['confidence'] = 'HIGH'
                elif 'LOW' in line.upper():
                    profile['confidence'] = 'LOW'
                else:
                    profile['confidence'] = 'MEDIUM'

        profile['exploitation_strategy'] = profile['exploitation_strategy'].strip()
        return profile

    def _generate_fallback_profile(
        self,
        stats: OpponentStats,
        hand_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate profile without AI when LangChain unavailable"""
        player_type = self.classify_player_type(stats)

        # Generate basic profile based on stats
        style_descriptions = {
            PlayerType.LAG: f"Loose-Aggressive player with {stats.vpip}% VPIP and {stats.pfr}% PFR",
            PlayerType.TAG: f"Tight-Aggressive player with {stats.vpip}% VPIP and {stats.pfr}% PFR",
            PlayerType.LP: f"Loose-Passive player with {stats.vpip}% VPIP and {stats.pfr}% PFR",
            PlayerType.TP: f"Tight-Passive player with {stats.vpip}% VPIP and {stats.pfr}% PFR",
            PlayerType.BALANCED: f"Balanced player with {stats.vpip}% VPIP and {stats.pfr}% PFR"
        }

        tendencies = [
            f"Aggression factor of {stats.aggression:.1f}",
            f"3-bets {stats.threebet}% of the time",
            f"Folds to c-bets {stats.fold_to_cbet}% of the time"
        ]

        exploitation_strategies = {
            PlayerType.LAG: "Value bet thinly and avoid bluffing too frequently. Tighten up your calling ranges.",
            PlayerType.TAG: "Can bluff occasionally but focus on value. Be careful with marginal hands.",
            PlayerType.LP: "Value bet aggressively and bluff frequently. They will call down light.",
            PlayerType.TP: "Steal their blinds frequently. They fold too much to aggression.",
            PlayerType.BALANCED: "Play standard GTO strategy with small adjustments based on position."
        }

        confidence = 'HIGH' if stats.hands_played >= 100 else 'MEDIUM' if stats.hands_played >= 50 else 'LOW'

        return {
            'playing_style': style_descriptions[player_type],
            'tendencies': tendencies,
            'exploitation_strategy': exploitation_strategies[player_type],
            'confidence': confidence,
            'player_type': player_type.value,
            'stats': asdict(stats)
        }
