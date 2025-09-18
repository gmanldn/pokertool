from __future__ import annotations

__version__ = '20'

# -*- coding: utf-8 -*-
from enum import Enum, auto
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple, Dict

__all__ = [
    'Suit', 'Rank', 'Position', 'Card', 
    'parse_card', 'analyse_hand', 'HandAnalysisResult', 
]

class Rank(Enum):
    """Enum representing poker card ranks."""
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

    @property
    def sym(self) -> str:
        """Return the symbol representation of the rank."""
        return {
            Rank.TWO: '2', Rank.THREE: '3', Rank.FOUR: '4', Rank.FIVE: '5', 
            Rank.SIX: '6', Rank.SEVEN: '7', Rank.EIGHT: '8', Rank.NINE: '9', 
            Rank.TEN: 'T', Rank.JACK: 'J', Rank.QUEEN: 'Q', Rank.KING: 'K', Rank.ACE: 'A', 
        }[self]
    
    @property
    def val(self) -> int:  # legacy accessor
        """Return the numeric value of the rank."""
        return int(self.value)

class Suit(Enum):
    """Enum representing poker card suits."""
    spades = 's'
    hearts = 'h'
    diamonds = 'd'
    clubs = 'c'

    @property
    def glyph(self) -> str:
        """Return the Unicode glyph for the suit."""
        return {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}[self.value]

class Position(Enum):
    """Enum representing poker table positions."""
    EARLY = auto()
    MIDDLE = auto()
    LATE = auto()
    BLINDS = auto()

    @property
    def category(self) -> str:
        """Return the category name of the position."""
        return {
            Position.EARLY: 'early', 
            Position.MIDDLE: 'middle', 
            Position.LATE: 'late', 
            Position.BLINDS: 'blinds', 
        }[self]
    
    def is_late(self) -> bool:
        """Return True if this is a late position."""
        return self is Position.LATE

@dataclass(frozen=True)
class Card:
    """Represents a playing card with rank and suit."""
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f'{self.rank.sym}{self.suit.value}'
    
    def __repr__(self) -> str:
        return f'Card({self.rank.name}, {self.suit.name})'

def parse_card(s: str) -> Card:
    """Parse a card string like "As" or "Td" into a Card object."""
    s = s.strip().upper()
    rank_map: Dict[str, Rank] = {
        '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE, 
        '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE, 
        'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 'K': Rank.KING, 
        'A': Rank.ACE
    }
    suit_map = {
        's': Suit.spades, 'h': Suit.hearts, 
        'd': Suit.diamonds, 'c': Suit.clubs
    }
    if len(s) != 2 or s[0] not in rank_map or s[1].lower() not in suit_map:
        raise ValueError(f"Bad card '{s}'. Use like 'As', 'Td', '9c'.")
    return Card(rank_map[s[0]], suit_map[s[1].lower()])

@dataclass
class HandAnalysisResult:
    """Result of hand analysis containing strength, advice and details."""
    strength: float
    advice: str
    details: dict

def analyse_hand(
    hole_cards: Iterable[Card], 
    board_cards: Optional[Iterable[Card]] = None, 
    position: Optional[Position] = None, 
    pot: Optional[float] = None, 
    to_call: Optional[float] = None
) -> HandAnalysisResult:
    """Analyze a poker hand and return strength, advice and details."""
    hc = list(hole_cards)
    if len(hc) < 2:
        return HandAnalysisResult(0.0, 'fold', {'error': 'need 2 hole cards'})
    
    ranks = sorted([int(c.rank.value) for c in hc[:2]], reverse=True)
    pair = ranks[0] == ranks[1]
    
    if pair and ranks[0] >= Rank.JACK.value:
        advice = 'raise'
    elif min(ranks) < 7:
        advice = 'fold'
    else:
        advice = 'call'
    
    return HandAnalysisResult(
        strength=sum(ranks)/28.0, 
        advice=advice, 
        details={
            'ONE_PAIR': pair, 
            'position': getattr(position, 'category', None)
        }
    )
