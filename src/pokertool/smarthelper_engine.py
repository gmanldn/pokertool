"""
SmartHelper Recommendation Engine

Core decision-making engine for SmartHelper that analyzes game state
and provides real-time action recommendations with factor-based reasoning.
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PokerAction(str, Enum):
    """Poker action types"""
    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    BET = "BET"
    RAISE = "RAISE"
    ALL_IN = "ALL_IN"


class Street(str, Enum):
    """Poker streets"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


@dataclass
class DecisionFactor:
    """Individual decision factor with scoring"""
    name: str
    score: float
    weight: float
    description: str
    details: Optional[str] = None


@dataclass
class GTOFrequencies:
    """GTO action frequencies"""
    fold: float = 0.0
    check: float = 0.0
    call: float = 0.0
    bet: float = 0.0
    raise_: float = 0.0
    all_in: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization"""
        return {
            "fold": self.fold,
            "check": self.check,
            "call": self.call,
            "bet": self.bet,
            "raise": self.raise_,
            "all_in": self.all_in
        }


@dataclass
class Opponent:
    """Opponent information"""
    name: str
    position: str
    stack: float
    stats: Optional[Dict[str, Any]] = None


@dataclass
class GameState:
    """Current game state"""
    # Player state
    hero_cards: Optional[List[str]] = None
    hero_position: Optional[str] = None
    hero_stack: float = 0.0

    # Table state
    community_cards: List[str] = field(default_factory=list)
    pot_size: float = 0.0
    bet_to_call: float = 0.0
    street: Street = Street.PREFLOP

    # Opponents
    opponents: List[Opponent] = field(default_factory=list)

    # Action history
    action_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SmartHelperRecommendation:
    """Complete SmartHelper recommendation"""
    action: PokerAction
    amount: Optional[float]
    gto_frequencies: GTOFrequencies
    strategic_reasoning: str
    confidence: float
    factors: List[DecisionFactor]
    net_confidence: float
    timestamp: int


class FactorWeights:
    """Configurable factor weights for SmartHelper decision-making"""

    # Default weight values
    DEFAULT_WEIGHTS = {
        'pot_odds': 1.5,
        'position': 1.2,
        'equity': 2.0,
        'opponent': 1.3,
        'stack_size': 1.0,
        'board_texture': 0.8,
        'pot_commitment': 1.1
    }

    # Predefined profiles
    PROFILES = {
        'balanced': {
            'pot_odds': 1.5,
            'position': 1.2,
            'equity': 2.0,
            'opponent': 1.3,
            'stack_size': 1.0,
            'board_texture': 0.8,
            'pot_commitment': 1.1
        },
        'gto': {
            'pot_odds': 1.8,
            'position': 1.5,
            'equity': 2.2,
            'opponent': 0.8,  # Less weight on opponent reads
            'stack_size': 1.2,
            'board_texture': 1.0,
            'pot_commitment': 0.9
        },
        'exploitative': {
            'pot_odds': 1.2,
            'position': 1.0,
            'equity': 1.5,
            'opponent': 2.5,  # Heavy weight on opponent tendencies
            'stack_size': 0.9,
            'board_texture': 0.7,
            'pot_commitment': 1.0
        },
        'conservative': {
            'pot_odds': 2.0,  # High emphasis on pot odds
            'position': 1.5,
            'equity': 2.5,  # Only play strong hands
            'opponent': 0.5,  # Less bluffing
            'stack_size': 1.3,
            'board_texture': 1.2,  # Careful on wet boards
            'pot_commitment': 0.6  # Less pot committed calls
        },
        'aggressive': {
            'pot_odds': 1.0,
            'position': 1.8,  # Exploit position more
            'equity': 1.5,
            'opponent': 1.5,
            'stack_size': 0.8,
            'board_texture': 0.5,  # Aggressive on all boards
            'pot_commitment': 1.5  # More willing to commit
        }
    }

    def __init__(self, profile: str = 'balanced', custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize factor weights

        Args:
            profile: Name of predefined profile ('balanced', 'gto', 'exploitative', etc.)
            custom_weights: Optional custom weights to override profile
        """
        # Load profile or use default
        if profile in self.PROFILES:
            self._weights = self.PROFILES[profile].copy()
        else:
            logger.warning(f"Unknown profile '{profile}', using 'balanced'")
            self._weights = self.PROFILES['balanced'].copy()

        # Override with custom weights if provided
        if custom_weights:
            self._weights.update(custom_weights)

        # Validate weights
        self._validate_weights()

    def _validate_weights(self):
        """Validate that all weights are in valid range"""
        for key, value in self._weights.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Weight '{key}' must be a number, got {type(value)}")
            if value < 0 or value > 10:
                logger.warning(f"Weight '{key}' = {value} is outside recommended range [0, 10]")

    @property
    def POT_ODDS_WEIGHT(self) -> float:
        return self._weights['pot_odds']

    @POT_ODDS_WEIGHT.setter
    def POT_ODDS_WEIGHT(self, value: float):
        self._weights['pot_odds'] = value
        self._validate_weights()

    @property
    def POSITION_WEIGHT(self) -> float:
        return self._weights['position']

    @POSITION_WEIGHT.setter
    def POSITION_WEIGHT(self, value: float):
        self._weights['position'] = value
        self._validate_weights()

    @property
    def EQUITY_WEIGHT(self) -> float:
        return self._weights['equity']

    @EQUITY_WEIGHT.setter
    def EQUITY_WEIGHT(self, value: float):
        self._weights['equity'] = value
        self._validate_weights()

    @property
    def OPPONENT_WEIGHT(self) -> float:
        return self._weights['opponent']

    @OPPONENT_WEIGHT.setter
    def OPPONENT_WEIGHT(self, value: float):
        self._weights['opponent'] = value
        self._validate_weights()

    @property
    def STACK_SIZE_WEIGHT(self) -> float:
        return self._weights['stack_size']

    @STACK_SIZE_WEIGHT.setter
    def STACK_SIZE_WEIGHT(self, value: float):
        self._weights['stack_size'] = value
        self._validate_weights()

    @property
    def BOARD_TEXTURE_WEIGHT(self) -> float:
        return self._weights['board_texture']

    @BOARD_TEXTURE_WEIGHT.setter
    def BOARD_TEXTURE_WEIGHT(self, value: float):
        self._weights['board_texture'] = value
        self._validate_weights()

    @property
    def POT_COMMITMENT_WEIGHT(self) -> float:
        return self._weights['pot_commitment']

    @POT_COMMITMENT_WEIGHT.setter
    def POT_COMMITMENT_WEIGHT(self, value: float):
        self._weights['pot_commitment'] = value
        self._validate_weights()

    def get_all_weights(self) -> Dict[str, float]:
        """Get all current weights as dictionary"""
        return self._weights.copy()

    def update_weights(self, weights: Dict[str, float]):
        """Update multiple weights at once"""
        self._weights.update(weights)
        self._validate_weights()

    def load_profile(self, profile: str):
        """Load a predefined profile"""
        if profile not in self.PROFILES:
            raise ValueError(f"Unknown profile '{profile}'. Available: {list(self.PROFILES.keys())}")
        self._weights = self.PROFILES[profile].copy()
        logger.info(f"Loaded profile: {profile}")

    def save_to_file(self, filepath: str):
        """Save current weights to JSON file"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self._weights, f, indent=2)
        logger.info(f"Saved weights to {filepath}")

    def load_from_file(self, filepath: str):
        """Load weights from JSON file"""
        import json
        with open(filepath, 'r') as f:
            self._weights = json.load(f)
        self._validate_weights()
        logger.info(f"Loaded weights from {filepath}")

    def __repr__(self) -> str:
        """String representation of weights"""
        return f"FactorWeights({', '.join(f'{k}={v}' for k, v in self._weights.items())})"


class SmartHelperEngine:
    """Main recommendation engine"""

    def __init__(self, weight_profile: str = 'balanced', custom_weights: Optional[Dict[str, float]] = None):
        """
        Initialize SmartHelper engine

        Args:
            weight_profile: Weight profile to use ('balanced', 'gto', 'exploitative', 'conservative', 'aggressive')
            custom_weights: Optional custom weight overrides
        """
        self.weights = FactorWeights(profile=weight_profile, custom_weights=custom_weights)
        self._cache: Dict[str, Tuple[SmartHelperRecommendation, float]] = {}
        self._cache_ttl = 5.0  # 5 second TTL
        self._recommendation_log: List[Dict[str, Any]] = []

    def update_factor_weights(self, weights: Dict[str, float]):
        """Update factor weights dynamically"""
        self.weights.update_weights(weights)
        # Clear cache since weights changed
        self._cache.clear()
        logger.info(f"Updated factor weights: {weights}")

    def load_weight_profile(self, profile: str):
        """Load a predefined weight profile"""
        self.weights.load_profile(profile)
        # Clear cache since weights changed
        self._cache.clear()
        logger.info(f"Loaded weight profile: {profile}")

    def get_current_weights(self) -> Dict[str, float]:
        """Get current factor weights"""
        return self.weights.get_all_weights()

    def _generate_cache_key(self, game_state: GameState) -> str:
        """Generate cache key from game state"""
        import hashlib
        import json

        # Create a deterministic representation of the game state
        state_dict = {
            'hero_cards': sorted(game_state.hero_cards) if game_state.hero_cards else None,
            'hero_position': game_state.hero_position,
            'hero_stack': round(game_state.hero_stack, 2),
            'community_cards': sorted(game_state.community_cards),
            'pot_size': round(game_state.pot_size, 2),
            'bet_to_call': round(game_state.bet_to_call, 2),
            'street': game_state.street.value,
            'opponents': [
                {
                    'position': opp.position,
                    'stack': round(opp.stack, 2)
                }
                for opp in sorted(game_state.opponents, key=lambda o: o.position)
            ]
        }

        # Generate hash
        state_str = json.dumps(state_dict, sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()

    def _get_cached_recommendation(self, cache_key: str) -> Optional[SmartHelperRecommendation]:
        """Get cached recommendation if valid"""
        if cache_key in self._cache:
            recommendation, timestamp = self._cache[cache_key]
            import time
            age = time.time() - timestamp
            if age < self._cache_ttl:
                logger.debug(f"Cache hit for key {cache_key[:8]}... (age: {age:.1f}s)")
                return recommendation
            else:
                # Expired - remove from cache
                del self._cache[cache_key]
                logger.debug(f"Cache expired for key {cache_key[:8]}...")
        return None

    def _cache_recommendation(self, cache_key: str, recommendation: SmartHelperRecommendation):
        """Cache a recommendation"""
        import time
        self._cache[cache_key] = (recommendation, time.time())
        logger.debug(f"Cached recommendation for key {cache_key[:8]}...")

    def _validate_recommendation(self, recommendation: SmartHelperRecommendation, game_state: GameState) -> bool:
        """Validate recommendation for sanity checks"""
        # Check 1: Amount should not exceed hero's stack
        if recommendation.amount and recommendation.amount > game_state.hero_stack:
            logger.warning(f"Invalid recommendation: amount ${recommendation.amount:.2f} exceeds stack ${game_state.hero_stack:.2f}")
            return False

        # Check 2: Cannot fold if bet_to_call is 0
        if recommendation.action == PokerAction.FOLD and game_state.bet_to_call == 0:
            logger.warning("Invalid recommendation: folding when no bet to call")
            return False

        # Check 3: Cannot check if facing a bet
        if recommendation.action == PokerAction.CHECK and game_state.bet_to_call > 0:
            logger.warning("Invalid recommendation: checking when facing a bet")
            return False

        # Check 4: Bet/raise amounts should be reasonable
        if recommendation.amount:
            if recommendation.amount < 0:
                logger.warning(f"Invalid recommendation: negative amount ${recommendation.amount:.2f}")
                return False
            if recommendation.amount > game_state.pot_size * 10:
                logger.warning(f"Invalid recommendation: excessive bet ${recommendation.amount:.2f} (pot: ${game_state.pot_size:.2f})")
                return False

        # Check 5: Confidence should be in valid range
        if not (0 <= recommendation.confidence <= 100):
            logger.warning(f"Invalid recommendation: confidence {recommendation.confidence} out of range")
            return False

        return True

    def _log_recommendation(self, recommendation: SmartHelperRecommendation, game_state: GameState):
        """Log recommendation for analysis"""
        log_entry = {
            'timestamp': recommendation.timestamp,
            'street': game_state.street.value,
            'action': recommendation.action.value,
            'amount': recommendation.amount,
            'confidence': recommendation.confidence,
            'net_confidence': recommendation.net_confidence,
            'pot_size': game_state.pot_size,
            'bet_to_call': game_state.bet_to_call,
            'hero_stack': game_state.hero_stack,
            'num_factors': len(recommendation.factors)
        }
        self._recommendation_log.append(log_entry)

        # Keep only last 100 recommendations
        if len(self._recommendation_log) > 100:
            self._recommendation_log = self._recommendation_log[-100:]

        logger.info(
            f"Recommendation: {recommendation.action.value} "
            f"(confidence: {recommendation.confidence:.1f}%, net: {recommendation.net_confidence:+.1f})"
        )

    def recommend(self, game_state: GameState) -> SmartHelperRecommendation:
        """
        Generate action recommendation based on game state

        Args:
            game_state: Current game state

        Returns:
            Complete SmartHelper recommendation
        """
        # Check cache first
        cache_key = self._generate_cache_key(game_state)
        cached = self._get_cached_recommendation(cache_key)
        if cached:
            return cached

        logger.info(f"Generating recommendation for {game_state.street} street")

        # Calculate all factors
        factors = self._calculate_factors(game_state)

        # Calculate net confidence
        net_confidence = self._calculate_net_confidence(factors)

        # Determine optimal action using decision tree
        action, amount = self._determine_action(game_state, factors, net_confidence)

        # Get GTO frequencies for this situation
        gto_frequencies = self._get_gto_frequencies(game_state, action)

        # Generate strategic reasoning
        strategic_reasoning = self._generate_reasoning(game_state, action, factors)

        # Calculate confidence (0-100)
        confidence = min(100.0, max(0.0, 50.0 + (net_confidence * 3)))

        import time
        recommendation = SmartHelperRecommendation(
            action=action,
            amount=amount,
            gto_frequencies=gto_frequencies,
            strategic_reasoning=strategic_reasoning,
            confidence=confidence,
            factors=factors,
            net_confidence=net_confidence,
            timestamp=int(time.time() * 1000)
        )

        # Validate recommendation
        if not self._validate_recommendation(recommendation, game_state):
            logger.error("Validation failed - returning conservative recommendation")
            # Return safe fallback (check or fold)
            fallback_action = PokerAction.CHECK if game_state.bet_to_call == 0 else PokerAction.FOLD
            recommendation = SmartHelperRecommendation(
                action=fallback_action,
                amount=None,
                gto_frequencies=GTOFrequencies(),
                strategic_reasoning="Conservative play due to validation error",
                confidence=50.0,
                factors=[],
                net_confidence=0.0,
                timestamp=int(time.time() * 1000)
            )

        # Log recommendation
        self._log_recommendation(recommendation, game_state)

        # Cache recommendation
        self._cache_recommendation(cache_key, recommendation)

        return recommendation

    def _calculate_factors(self, game_state: GameState) -> List[DecisionFactor]:
        """Calculate all decision factors"""
        factors = []

        # Pot odds factor
        pot_odds_factor = self._calculate_pot_odds_factor(game_state)
        if pot_odds_factor:
            factors.append(pot_odds_factor)

        # Position factor
        position_factor = self._calculate_position_factor(game_state)
        if position_factor:
            factors.append(position_factor)

        # Equity factor
        equity_factor = self._calculate_equity_factor(game_state)
        if equity_factor:
            factors.append(equity_factor)

        # Opponent factor
        opponent_factor = self._calculate_opponent_factor(game_state)
        if opponent_factor:
            factors.append(opponent_factor)

        # Stack size factor
        stack_factor = self._calculate_stack_factor(game_state)
        if stack_factor:
            factors.append(stack_factor)

        # Board texture factor
        texture_factor = self._calculate_board_texture_factor(game_state)
        if texture_factor:
            factors.append(texture_factor)

        # Pot commitment factor
        commitment_factor = self._calculate_pot_commitment_factor(game_state)
        if commitment_factor:
            factors.append(commitment_factor)

        return factors

    def _calculate_pot_odds_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate pot odds factor"""
        if game_state.bet_to_call <= 0:
            return None

        total_pot = game_state.pot_size + game_state.bet_to_call
        if total_pot == 0:
            return None

        pot_odds_ratio = game_state.pot_size / game_state.bet_to_call
        break_even_equity = (game_state.bet_to_call / total_pot) * 100

        # Score based on pot odds quality
        if pot_odds_ratio >= 3.0:
            score = 8.0
            description = "Excellent pot odds (3:1+)"
        elif pot_odds_ratio >= 2.0:
            score = 5.0
            description = "Good pot odds (2:1+)"
        elif pot_odds_ratio >= 1.5:
            score = 2.0
            description = "Decent pot odds (1.5:1+)"
        else:
            score = -3.0
            description = "Poor pot odds"

        details = (
            f"Pot: ${game_state.pot_size:.2f}, "
            f"To Call: ${game_state.bet_to_call:.2f}, "
            f"Odds: {pot_odds_ratio:.1f}:1, "
            f"Break-even: {break_even_equity:.1f}%"
        )

        return DecisionFactor(
            name="Pot Odds",
            score=score * self.weights.POT_ODDS_WEIGHT,
            weight=self.weights.POT_ODDS_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_position_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate position factor"""
        if not game_state.hero_position:
            return None

        position = game_state.hero_position.upper()

        # Position strength scoring
        position_scores = {
            'BTN': (8.0, "Button - best position"),
            'CO': (6.0, "Cutoff - strong position"),
            'MP': (3.0, "Middle position - neutral"),
            'UTG': (-2.0, "Under the gun - weak position"),
            'SB': (-3.0, "Small blind - worst position"),
            'BB': (-1.0, "Big blind - defensive position")
        }

        score, description = position_scores.get(position, (0.0, "Unknown position"))

        details = f"Playing from {position} position"

        return DecisionFactor(
            name="Position",
            score=score * self.weights.POSITION_WEIGHT,
            weight=self.weights.POSITION_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_equity_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate hand equity factor (simplified - would use actual equity calculator)"""
        # This is a placeholder - real implementation would calculate actual equity
        # For now, we'll estimate based on street and community cards

        if not game_state.hero_cards:
            return None

        # Simplified equity estimation
        estimated_equity = 50.0  # Default to 50%

        if game_state.street == Street.PREFLOP:
            # Premium hands get higher equity
            if len(game_state.hero_cards) == 2:
                card1, card2 = game_state.hero_cards[0], game_state.hero_cards[1]
                # Check for pocket pairs, high cards, etc.
                if card1[0] == card2[0]:  # Pocket pair
                    estimated_equity = 65.0
                elif card1[0] in ['A', 'K'] and card2[0] in ['A', 'K']:  # AK
                    estimated_equity = 60.0
                elif card1[0] in ['A', 'K', 'Q'] or card2[0] in ['A', 'K', 'Q']:
                    estimated_equity = 55.0

        # Score based on equity
        if estimated_equity >= 70:
            score = 10.0
            description = "Very strong hand (70%+ equity)"
        elif estimated_equity >= 55:
            score = 6.0
            description = "Strong hand (55-70% equity)"
        elif estimated_equity >= 45:
            score = 0.0
            description = "Medium hand (45-55% equity)"
        elif estimated_equity >= 30:
            score = -4.0
            description = "Weak hand (30-45% equity)"
        else:
            score = -8.0
            description = "Very weak hand (<30% equity)"

        details = f"Estimated equity: {estimated_equity:.1f}% vs opponent range"

        return DecisionFactor(
            name="Hand Equity",
            score=score * self.weights.EQUITY_WEIGHT,
            weight=self.weights.EQUITY_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_opponent_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate opponent factor based on stats"""
        if not game_state.opponents:
            return None

        # Analyze primary opponent
        opponent = game_state.opponents[0]
        if not opponent.stats:
            return None

        stats = opponent.stats
        vpip = stats.get('vpip', 0)
        pfr = stats.get('pfr', 0)
        fold_to_cbet = stats.get('foldToCbet', 0)

        # Exploitability scoring
        score = 0.0
        exploits = []

        if fold_to_cbet > 60:
            score += 5.0
            exploits.append("folds to c-bets")

        if vpip > 40:
            score += 3.0
            exploits.append("plays too loose")

        if pfr < 10:
            score += 4.0
            exploits.append("rarely raises")

        if score > 0:
            description = f"Exploitable opponent ({', '.join(exploits)})"
        else:
            score = -2.0
            description = "Solid opponent - minimize mistakes"

        details = f"{opponent.name}: VPIP {vpip:.0f}%, PFR {pfr:.0f}%, Fold to C-bet {fold_to_cbet:.0f}%"

        return DecisionFactor(
            name="Opponent Tendencies",
            score=score * self.weights.OPPONENT_WEIGHT,
            weight=self.weights.OPPONENT_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_stack_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate stack size factor"""
        if game_state.hero_stack <= 0 or game_state.pot_size <= 0:
            return None

        spr = game_state.hero_stack / game_state.pot_size  # Stack-to-pot ratio

        if spr >= 10:
            score = 2.0
            description = "Deep stack (10+ SPR)"
        elif spr >= 5:
            score = 0.0
            description = "Medium stack (5-10 SPR)"
        elif spr >= 2:
            score = -2.0
            description = "Short stack (2-5 SPR)"
        else:
            score = -4.0
            description = "Very short stack (<2 SPR)"

        details = f"Stack: ${game_state.hero_stack:.2f}, SPR: {spr:.1f}"

        return DecisionFactor(
            name="Stack Size",
            score=score * self.weights.STACK_SIZE_WEIGHT,
            weight=self.weights.STACK_SIZE_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_board_texture_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate board texture factor (wet vs dry board)"""
        if not game_state.community_cards or len(game_state.community_cards) < 3:
            return None  # Need at least flop

        cards = game_state.community_cards

        # Count suits and ranks
        suits = [card[-1] for card in cards]
        ranks = [card[0] for card in cards]

        # Check for flush draw (3+ of same suit)
        suit_counts = {suit: suits.count(suit) for suit in set(suits)}
        max_suit_count = max(suit_counts.values())
        flush_draw = max_suit_count >= 3

        # Check for straight draw (connected cards)
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        rank_nums = sorted([rank_values.get(r, 0) for r in ranks])
        straight_draw = False
        if len(rank_nums) >= 3:
            # Check if cards are within 4 ranks of each other
            spread = rank_nums[-1] - rank_nums[0]
            straight_draw = spread <= 4

        # Check for paired board
        rank_counts = {rank: ranks.count(rank) for rank in set(ranks)}
        paired = any(count >= 2 for count in rank_counts.values())

        # Scoring
        if flush_draw and straight_draw:
            score = -4.0
            description = "Very wet board (flush + straight draws)"
        elif flush_draw or straight_draw:
            score = -2.0
            description = "Wet board (draw heavy)"
        elif paired:
            score = 1.0
            description = "Paired board (less draws)"
        else:
            score = 2.0
            description = "Dry board (few draws)"

        details = f"Board: {', '.join(cards)}"
        if flush_draw:
            details += " (flush draw)"
        if straight_draw:
            details += " (straight draw)"

        return DecisionFactor(
            name="Board Texture",
            score=score * self.weights.BOARD_TEXTURE_WEIGHT,
            weight=self.weights.BOARD_TEXTURE_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_pot_commitment_factor(self, game_state: GameState) -> Optional[DecisionFactor]:
        """Calculate pot commitment factor based on pot:stack ratio"""
        if game_state.hero_stack <= 0 or game_state.pot_size <= 0:
            return None

        # Calculate what % of stack is already in pot
        committed_percentage = (game_state.pot_size / game_state.hero_stack) * 100

        if committed_percentage >= 50:
            score = 6.0
            description = "Heavily pot committed (50%+ of stack in pot)"
        elif committed_percentage >= 33:
            score = 4.0
            description = "Pot committed (33-50% of stack in pot)"
        elif committed_percentage >= 20:
            score = 2.0
            description = "Moderately committed (20-33% in pot)"
        else:
            score = 0.0
            description = "Low commitment (<20% in pot)"

        details = f"Pot: ${game_state.pot_size:.2f}, Stack: ${game_state.hero_stack:.2f}, Committed: {committed_percentage:.1f}%"

        return DecisionFactor(
            name="Pot Commitment",
            score=score * self.weights.POT_COMMITMENT_WEIGHT,
            weight=self.weights.POT_COMMITMENT_WEIGHT,
            description=description,
            details=details
        )

    def _calculate_net_confidence(self, factors: List[DecisionFactor]) -> float:
        """Calculate net confidence from all factors"""
        return sum(factor.score for factor in factors)

    def _determine_action(
        self,
        game_state: GameState,
        factors: List[DecisionFactor],
        net_confidence: float
    ) -> Tuple[PokerAction, Optional[float]]:
        """Determine optimal action using decision tree"""

        # If no bet to call, can check or bet
        if game_state.bet_to_call == 0:
            if net_confidence >= 10:
                # Strong hand - bet for value
                amount = game_state.pot_size * 0.66  # 2/3 pot bet
                return PokerAction.BET, amount
            elif net_confidence >= 0:
                # Medium hand - check
                return PokerAction.CHECK, None
            else:
                # Weak hand - check
                return PokerAction.CHECK, None

        # Facing a bet
        else:
            if net_confidence >= 15:
                # Very strong - raise
                amount = game_state.bet_to_call * 2.5
                return PokerAction.RAISE, amount
            elif net_confidence >= 5:
                # Strong enough to call
                return PokerAction.CALL, None
            elif net_confidence >= -5:
                # Marginal - depends on pot odds
                pot_odds_factor = next((f for f in factors if f.name == "Pot Odds"), None)
                if pot_odds_factor and pot_odds_factor.score > 0:
                    return PokerAction.CALL, None
                else:
                    return PokerAction.FOLD, None
            else:
                # Weak hand - fold
                return PokerAction.FOLD, None

    def _get_gto_frequencies(
        self,
        game_state: GameState,
        recommended_action: PokerAction
    ) -> GTOFrequencies:
        """Get GTO action frequencies for this situation (simplified)"""
        # This is a placeholder - real implementation would query GTO solver database

        frequencies = GTOFrequencies()

        if game_state.bet_to_call == 0:
            # No bet to call - check/bet situation
            frequencies.check = 60.0
            frequencies.bet = 35.0
            frequencies.raise_ = 5.0
        else:
            # Facing a bet - fold/call/raise situation
            frequencies.fold = 40.0
            frequencies.call = 35.0
            frequencies.raise_ = 20.0
            frequencies.all_in = 5.0

        return frequencies

    def _generate_reasoning(
        self,
        game_state: GameState,
        action: PokerAction,
        factors: List[DecisionFactor]
    ) -> str:
        """Generate strategic reasoning one-liner"""

        # Find dominant positive factor
        positive_factors = [f for f in factors if f.score > 0]
        if positive_factors:
            dominant_factor = max(positive_factors, key=lambda f: f.score)

            if action == PokerAction.BET or action == PokerAction.RAISE:
                return f"Aggressive play justified by {dominant_factor.description.lower()}"
            elif action == PokerAction.CALL:
                return f"Call based on {dominant_factor.description.lower()}"
            elif action == PokerAction.CHECK:
                return f"Check to control pot size despite {dominant_factor.description.lower()}"

        # If no strong positive factors
        if action == PokerAction.FOLD:
            return "Fold to minimize losses in unfavorable situation"
        elif action == PokerAction.CHECK:
            return "Check to see more cards cheaply"
        else:
            return "Standard GTO play"
