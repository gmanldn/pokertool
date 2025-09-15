#!/usr/bin/env python3
"""
Poker Modules - Core classes and logic for poker hand analysis
FIXED VERSION - Resolves all regression bugs
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Union
from collections import namedtuple, Counter
import itertools
import sqlite3
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep the original Card namedtuple for backward compatibility
Card = namedtuple('Card', 'rank suit')

# Define RANK_ORDER constant for GUI compatibility
RANK_ORDER = "23456789TJQKA"

class Suit(Enum):
    """Enumeration for card suits"""
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'
    
    # Aliases for compatibility
    HEART = '♥'
    DIAMOND = '♦'
    CLUB = '♣'
    SPADE = '♠'
    
    # Single letter aliases for parsing
    H = '♥'
    D = '♦'
    C = '♣'
    S = '♠'
    
    @classmethod
    def from_symbol(cls, symbol: str):
        """Create Suit from symbol"""
        symbol_map = {
            'h': cls.HEARTS, '♥': cls.HEARTS, 'hearts': cls.HEARTS,
            'd': cls.DIAMONDS, '♦': cls.DIAMONDS, 'diamonds': cls.DIAMONDS,
            'c': cls.CLUBS, '♣': cls.CLUBS, 'clubs': cls.CLUBS,
            's': cls.SPADES, '♠': cls.SPADES, 'spades': cls.SPADES
        }
        return symbol_map.get(symbol.lower())
    
    def __str__(self):
        return self.value

class Rank(Enum):
    """Enumeration for card ranks"""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    
    @classmethod
    def from_string(cls, rank_str: str):
        """Create Rank from string"""
        rank_map = {
            '2': cls.TWO, '3': cls.THREE, '4': cls.FOUR,
            '5': cls.FIVE, '6': cls.SIX, '7': cls.SEVEN,
            '8': cls.EIGHT, '9': cls.NINE, '10': cls.TEN,
            't': cls.TEN, 'j': cls.JACK, 'q': cls.QUEEN,
            'k': cls.KING, 'a': cls.ACE,
            # Full names
            'two': cls.TWO, 'three': cls.THREE, 'four': cls.FOUR,
            'five': cls.FIVE, 'six': cls.SIX, 'seven': cls.SEVEN,
            'eight': cls.EIGHT, 'nine': cls.NINE, 'ten': cls.TEN,
            'jack': cls.JACK, 'queen': cls.QUEEN, 'king': cls.KING,
            'ace': cls.ACE
        }
        return rank_map.get(rank_str.lower())
    
    def __str__(self):
        if self.value == 10:
            return 'T'
        elif self.value == 11:
            return 'J'
        elif self.value == 12:
            return 'Q'
        elif self.value == 13:
            return 'K'
        elif self.value == 14:
            return 'A'
        else:
            return str(self.value)

class HandRank(Enum):
    """Hand ranking enumeration"""
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

# Alias for compatibility
HandRanking = HandRank

class Position(Enum):
    """Player positions at the poker table"""
    BUTTON = 'BTN'
    SMALL_BLIND = 'SB'
    BIG_BLIND = 'BB'
    UNDER_THE_GUN = 'UTG'
    UTG_PLUS_1 = 'UTG+1'
    UTG_PLUS_2 = 'UTG+2'
    MIDDLE = 'MP'
    MIDDLE_PLUS_1 = 'MP+1'
    MIDDLE_PLUS_2 = 'MP+2'
    CUTOFF = 'CO'
    HIJACK = 'HJ'
    
    def __str__(self):
        return self.value

@dataclass
class GameState:
    """Game state for hand analysis"""
    position: Position = Position.UNDER_THE_GUN
    stack_bb: int = 100
    pot: float = 0.0
    to_call: float = 0.0
    board: List[Card] = field(default_factory=list)
    players: int = 6
    stage: str = "preflop"

@dataclass 
class HandAnalysisResult:
    """Result of hand analysis with all necessary fields for GUI"""
    decision: str = "FOLD"
    spr: float = 0.0
    board_texture: str = "Unknown"
    equity: float = 0.0
    hand_strength: str = "Unknown"
    recommendation: str = "FOLD"
    reasoning: List[str] = field(default_factory=list)

@dataclass
class PokerCard:
    """Enhanced Card class with more functionality"""
    rank: Rank
    suit: Suit
    
    def __str__(self):
        return f"{str(self.rank)}{str(self.suit)}"
    
    def __repr__(self):
        return f"PokerCard({self.rank}, {self.suit})"
    
    def __eq__(self, other):
        if isinstance(other, PokerCard):
            return self.rank == other.rank and self.suit == other.suit
        return False
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    def __lt__(self, other):
        if isinstance(other, PokerCard):
            return self.rank.value < other.rank.value
        return NotImplemented
    
    @classmethod
    def from_string(cls, card_str: str):
        """Create a PokerCard from string like 'AS' or 'Ah'"""
        if len(card_str) < 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank_str = card_str[:-1]
        suit_str = card_str[-1]
        
        rank = Rank.from_string(rank_str)
        suit = Suit.from_symbol(suit_str)
        
        if rank is None or suit is None:
            raise ValueError(f"Invalid card string: {card_str}")
        
        return cls(rank, suit)

class HandAnalysis:
    """Analyzes poker hands and provides strategic recommendations"""
    
    def __init__(self):
        self.hand_history = []
        self._starting_hand_rankings = self._initialize_starting_hands()
    
    def _initialize_starting_hands(self) -> Dict[str, int]:
        """Initialize starting hand rankings"""
        rankings = {}
        
        # Premium hands
        premium = ['AA', 'KK', 'QQ', 'AKs', 'JJ', 'AQs', 'KQs', 'AJs', 'KJs', 'TT']
        for i, hand in enumerate(premium):
            rankings[hand] = 20 - i
        
        # Strong hands
        strong = ['AKo', 'ATs', 'QJs', 'KTs', 'QTs', 'JTs', '99', 'AQo', 'A9s', 'KQo']
        for i, hand in enumerate(strong):
            rankings[hand] = 10 - i * 0.5
        
        # Playable hands
        playable = ['88', '77', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
                   'AJo', 'ATo', 'KJo', 'QJo', 'JTo', 'T9s', '98s', '87s', '76s', '66', '55']
        for i, hand in enumerate(playable):
            rankings[hand] = 5 - i * 0.2
        
        return rankings
    
    def analyze_hand(self, hole_cards: List, community_cards: List = None) -> Dict:
        """Analyze a poker hand and return strategic recommendations"""
        try:
            # Convert cards to PokerCard if needed
            hole_cards = self._convert_cards(hole_cards)
            community_cards = self._convert_cards(community_cards) if community_cards else []
            
            if not hole_cards or len(hole_cards) != 2:
                raise ValueError("Must have exactly 2 hole cards")
            
            analysis = {
                'hole_cards': [str(card) for card in hole_cards],
                'community_cards': [str(card) for card in community_cards],
                'hand_strength': self._calculate_hand_strength(hole_cards, community_cards),
                'position_recommendation': self._get_position_recommendation(hole_cards),
                'starting_hand_rank': self._get_starting_hand_rank(hole_cards),
                'outs': self._calculate_outs(hole_cards, community_cards) if community_cards else 0,
                'pot_odds': None,
                'recommendation': None,
                'hand_type': None
            }
            
            # Determine current hand type if community cards exist
            if community_cards:
                analysis['hand_type'] = str(self._evaluate_hand_ranking(hole_cards + community_cards))
            
            # Generate recommendation
            analysis['recommendation'] = self._generate_recommendation(analysis)
            
            # Store in history
            self.hand_history.append(analysis)
            
            return analysis
            
        except Exception as e:
            return {
                'error': str(e),
                'hole_cards': [],
                'community_cards': [],
                'hand_strength': 'Unknown',
                'recommendation': 'Unable to analyze hand'
            }
    
    def _convert_cards(self, cards):
        """Convert Card namedtuples to PokerCard objects"""
        if not cards:
            return []
        
        converted = []
        for card in cards:
            if isinstance(card, PokerCard):
                converted.append(card)
            elif hasattr(card, 'rank') and hasattr(card, 'suit'):
                # Convert from namedtuple or similar
                rank = Rank.from_string(str(card.rank)) if not isinstance(card.rank, Rank) else card.rank
                suit = Suit.from_symbol(str(card.suit)) if not isinstance(card.suit, Suit) else card.suit
                converted.append(PokerCard(rank, suit))
            else:
                # Try to parse as string
                converted.append(PokerCard.from_string(str(card)))
        
        return converted
    
    def _get_starting_hand_rank(self, hole_cards: List[PokerCard]) -> str:
        """Get the starting hand ranking"""
        if len(hole_cards) != 2:
            return "Unknown"
        
        c1, c2 = sorted(hole_cards, reverse=True)
        
        # Format hand notation
        if c1.rank == c2.rank:
            hand = f"{str(c1.rank)}{str(c2.rank)}"
        else:
            suited = 's' if c1.suit == c2.suit else 'o'
            hand = f"{str(c1.rank)}{str(c2.rank)}{suited}"
        
        rank = self._starting_hand_rankings.get(hand, 0)
        
        if rank >= 15:
            return f"Premium ({hand})"
        elif rank >= 8:
            return f"Strong ({hand})"
        elif rank >= 3:
            return f"Playable ({hand})"
        else:
            return f"Marginal ({hand})"
    
    def _calculate_hand_strength(self, hole_cards: List[PokerCard], community_cards: List[PokerCard] = None) -> str:
        """Calculate the strength of the current hand"""
        if len(hole_cards) < 2:
            return "Insufficient cards"
        
        # Pre-flop evaluation
        if not community_cards or len(community_cards) == 0:
            return self._evaluate_preflop_strength(hole_cards)
        
        # Post-flop evaluation
        ranking = self._evaluate_hand_ranking(hole_cards + community_cards)
        return str(ranking)
    
    def _evaluate_preflop_strength(self, hole_cards: List[PokerCard]) -> str:
        """Evaluate pre-flop hand strength"""
        if len(hole_cards) != 2:
            return "Invalid hand"
        
        c1, c2 = hole_cards
        
        # Pocket pairs
        if c1.rank == c2.rank:
            if c1.rank.value >= Rank.TEN.value:
                return f"Premium Pocket {c1.rank.name}s"
            elif c1.rank.value >= Rank.SEVEN.value:
                return f"Medium Pocket {c1.rank.name}s"
            else:
                return f"Small Pocket {c1.rank.name}s"
        
        # Suited cards
        suited = c1.suit == c2.suit
        
        # High cards
        high_rank = max(c1.rank.value, c2.rank.value)
        low_rank = min(c1.rank.value, c2.rank.value)
        gap = high_rank - low_rank
        
        # Ace combinations
        if high_rank == Rank.ACE.value:
            if low_rank >= Rank.KING.value:
                return f"Premium Ace-{Rank(low_rank).name}" + (" Suited" if suited else "")
            elif low_rank >= Rank.TEN.value:
                return f"Strong Ace-{Rank(low_rank).name}" + (" Suited" if suited else "")
            else:
                return f"Ace-{Rank(low_rank).name}" + (" Suited" if suited else "")
        
        # Connectors
        if gap == 1:
            if high_rank >= Rank.JACK.value:
                return "Premium Connector" + (" Suited" if suited else "")
            else:
                return "Connector" + (" Suited" if suited else "")
        elif gap == 2:
            return "One-Gap" + (" Suited" if suited else "")
        elif gap == 3:
            return "Two-Gap" + (" Suited" if suited else "")
        
        # Face cards
        if high_rank >= Rank.JACK.value and low_rank >= Rank.TEN.value:
            return "Broadway Cards" + (" Suited" if suited else "")
        
        # Default
        return f"High Card {Rank(high_rank).name}" + (" Suited" if suited else "")
    
    def _evaluate_hand_ranking(self, cards: List[PokerCard]) -> HandRank:
        """Evaluate the best poker hand from available cards"""
        if len(cards) < 5:
            return HandRank.HIGH_CARD
        
        best_ranking = HandRank.HIGH_CARD
        
        # Evaluate all possible 5-card combinations
        for combo in itertools.combinations(cards, 5):
            ranking = self._evaluate_five_cards(list(combo))
            if ranking.value > best_ranking.value:
                best_ranking = ranking
        
        return best_ranking
    
    def _evaluate_five_cards(self, cards: List[PokerCard]) -> HandRank:
        """Evaluate exactly 5 cards for poker hand ranking"""
        # Check for flush
        suits = [card.suit for card in cards]
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        ranks = sorted([card.rank.value for card in cards])
        is_straight = False
        
        # Regular straight
        if ranks[4] - ranks[0] == 4 and len(set(ranks)) == 5:
            is_straight = True
        # Ace-low straight (wheel)
        elif set(ranks) == {2, 3, 4, 5, 14}:
            is_straight = True
        
        # Count rank frequencies
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank.value] = rank_counts.get(card.rank.value, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Determine hand ranking
        if is_straight and is_flush:
            if set(ranks) == {10, 11, 12, 13, 14}:
                return HandRank.ROYAL_FLUSH
            return HandRank.STRAIGHT_FLUSH
        elif counts == [4, 1]:
            return HandRank.FOUR_OF_A_KIND
        elif counts == [3, 2]:
            return HandRank.FULL_HOUSE
        elif is_flush:
            return HandRank.FLUSH
        elif is_straight:
            return HandRank.STRAIGHT
        elif counts == [3, 1, 1]:
            return HandRank.THREE_OF_A_KIND
        elif counts == [2, 2, 1]:
            return HandRank.TWO_PAIR
        elif counts == [2, 1, 1, 1]:
            return HandRank.PAIR
        else:
            return HandRank.HIGH_CARD
    
    def _get_position_recommendation(self, hole_cards: List[PokerCard]) -> str:
        """Get position-based recommendation for starting hands"""
        if len(hole_cards) != 2:
            return "Unknown"
        
        hand_rank = self._get_starting_hand_rank(hole_cards)
        
        if "Premium" in hand_rank:
            return "RAISE from any position - Premium hand"
        elif "Strong" in hand_rank:
            return "RAISE from any position - Strong hand"
        elif "Playable" in hand_rank:
            return "CALL or RAISE in late position"
        else:
            return "FOLD in early position, consider in late position"
    
    def _calculate_outs(self, hole_cards: List[PokerCard], community_cards: List[PokerCard]) -> int:
        """Calculate the number of outs to improve the hand"""
        if not community_cards or len(community_cards) < 3:
            return 0
        
        outs = 0
        all_cards = hole_cards + community_cards
        
        # Check for flush draw
        for suit in Suit:
            suited_cards = [c for c in all_cards if c.suit == suit]
            if len(suited_cards) == 4:
                outs += 9  # 13 total - 4 shown = 9 outs
        
        return min(outs, 20)  # Cap at reasonable number
    
    def _generate_recommendation(self, analysis: Dict) -> str:
        """Generate action recommendation based on analysis"""
        strength = analysis.get('hand_strength', 'Unknown')
        position_rec = analysis.get('position_recommendation', '')
        outs = analysis.get('outs', 0)
        hand_type = analysis.get('hand_type', '')
        
        # Pre-flop recommendations
        if not analysis.get('community_cards'):
            if 'RAISE' in position_rec:
                return "RAISE - Strong starting hand"
            elif 'CALL' in position_rec:
                return "CALL - Playable hand, see flop"
            elif 'FOLD' in position_rec:
                return "FOLD - Weak starting hand"
            else:
                return "CHECK/CALL - Proceed cautiously"
        
        # Post-flop recommendations based on hand type
        if 'ROYAL_FLUSH' in str(hand_type) or 'STRAIGHT_FLUSH' in str(hand_type):
            return "RAISE/ALL-IN - Unbeatable hand!"
        elif 'FOUR_OF_A_KIND' in str(hand_type) or 'FULL_HOUSE' in str(hand_type):
            return "RAISE - Very strong hand"
        elif 'FLUSH' in str(hand_type) or 'STRAIGHT' in str(hand_type):
            return "RAISE/CALL - Strong made hand"
        elif 'THREE_OF_A_KIND' in str(hand_type):
            return "RAISE/CALL - Good hand, bet for value"
        elif 'TWO_PAIR' in str(hand_type):
            return "CALL/RAISE - Decent hand, proceed with caution"
        elif 'PAIR' in str(hand_type):
            if outs >= 8:
                return "CALL - Pair with good draw"
            else:
                return "CHECK/FOLD - Weak pair"
        
        # Drawing hands
        if outs >= 12:
            return "CALL/RAISE - Strong draw, semi-bluff"
        elif outs >= 8:
            return "CALL - Good drawing hand"
        elif outs >= 4:
            return "CHECK/CALL - Marginal draw"
        
        return "CHECK/FOLD - Weak hand"
    
    def get_statistics(self) -> Dict:
        """Get statistics from hand history"""
        if not self.hand_history:
            return {
                'total_hands': 0,
                'message': 'No hands analyzed yet'
            }
        
        total = len(self.hand_history)
        return {
            'total_hands': total,
            'last_hand': self.hand_history[-1] if self.hand_history else None
        }
    
    def clear_history(self):
        """Clear the hand history"""
        self.hand_history = []

# ═══════════════════════════════════════════════════════════════════════════════
# COMPATIBILITY FUNCTIONS FOR GUI
# ═══════════════════════════════════════════════════════════════════════════════

def to_two_card_str(cards: List[Card]) -> str:
    """Convert two cards to standard poker notation (e.g., 'AKs', 'AKo')"""
    if len(cards) != 2:
        return "Invalid"
    
    c1, c2 = cards
    
    # Convert rank to standard notation
    def rank_to_str(rank):
        rank_map = {
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
            '7': '7', '8': '8', '9': '9', '10': 'T', 'T': 'T',
            'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
        }
        return rank_map.get(str(rank), str(rank))
    
    r1 = rank_to_str(c1.rank)
    r2 = rank_to_str(c2.rank)
    
    # Ensure higher rank comes first
    rank_order = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    
    try:
        r1_val = rank_order.index(r1)
        r2_val = rank_order.index(r2)
        
        if r1_val >= r2_val:
            high_rank, low_rank = r1, r2
            high_suit, low_suit = str(c1.suit), str(c2.suit)
        else:
            high_rank, low_rank = r2, r1
            high_suit, low_suit = str(c2.suit), str(c1.suit)
    except (ValueError, IndexError):
        # Fallback if rank mapping fails
        high_rank, low_rank = r1, r2
        high_suit, low_suit = str(c1.suit), str(c2.suit)
    
    # Add suited/offsuit indicator if ranks are different
    if high_rank != low_rank:
        if high_suit == low_suit:
            return f"{high_rank}{low_rank}s"
        else:
            return f"{high_rank}{low_rank}o"
    else:
        # Pocket pair
        return f"{high_rank}{high_rank}"

def get_hand_tier(cards: List[Card]) -> str:
    """Get hand tier classification"""
    if len(cards) != 2:
        return "Unknown"
    
    hand_str = to_two_card_str(cards)
    
    # Simple tier classification
    premium_hands = ['AA', 'KK', 'QQ', 'JJ', 'AKs', 'AQs', 'AKo']
    strong_hands = ['TT', '99', '88', 'AJs', 'ATs', 'A9s', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', 'AQo', 'AJo']
    playable_hands = ['77', '66', '55', '44', '33', '22', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s', 
                     'K9s', 'Q9s', 'J9s', 'T9s', '98s', '87s', '76s', '65s', 'ATo', 'KQo', 'KJo', 'QJo', 'JTo']
    
    if hand_str in premium_hands:
        return "1"
    elif hand_str in strong_hands:
        return "2"
    elif hand_str in playable_hands:
        return "3"
    else:
        return "4"

def analyse_hand(cards: List[Card], board_cards: List[Card] = None, game_state: GameState = None) -> HandAnalysisResult:
    """Main hand analysis function for GUI compatibility"""
    if game_state is None:
        game_state = GameState()
    
    # Use HandAnalysis class for the actual analysis
    analyzer = HandAnalysis()
    analysis = analyzer.analyze_hand(cards, board_cards)
    
    # Calculate SPR (Stack to Pot Ratio)
    spr = game_state.stack_bb / max(game_state.pot, 1.0) if game_state.pot > 0 else game_state.stack_bb
    
    # Determine board texture
    board_texture = "Dry"
    if board_cards and len(board_cards) >= 3:
        # Simple board texture analysis
        suits = [card.suit for card in board_cards]
        ranks = [card.rank for card in board_cards]
        
        # Count suits for flush potential
        suit_counts = Counter(suits)
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        if max_suit_count >= 3:
            board_texture = "Wet (Flush draw)"
        elif len(set(ranks)) <= 2:
            board_texture = "Paired"
        else:
            board_texture = "Dry"
    
    # Map analysis to expected GUI format
    result = HandAnalysisResult(
        decision=analysis.get('recommendation', 'FOLD'),
        spr=spr,
        board_texture=board_texture,
        equity=50.0,  # Default equity
        hand_strength=analysis.get('hand_strength', 'Unknown'),
        recommendation=analysis.get('recommendation', 'FOLD'),
        reasoning=[analysis.get('position_recommendation', 'Unknown position')]
    )
    
    return result

# Compatibility aliases
analyze_hand = analyse_hand

# Cache manager stub for compatibility
class CacheManager:
    @staticmethod
    def get_cache_stats():
        return {"analysis": {"hits": 0, "misses": 0}}

# Create aliases for backward compatibility
def create_card(rank, suit):
    """Helper function to create a card"""
    return Card(rank, suit)

def analyze_poker_hand(hole_cards, community_cards=None):
    """Quick analysis function"""
    analyzer = HandAnalysis()
    return analyzer.analyze_hand(hole_cards, community_cards)

if __name__ == "__main__":
    print("Poker modules loaded successfully!")
    
    # Quick test
    test_cards = [Card('A', Suit.SPADES), Card('K', Suit.HEARTS)]
    print(f"Test hand: {to_two_card_str(test_cards)}")
    print(f"Hand tier: {get_hand_tier(test_cards)}")
