# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/core.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
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
    SPADES = 's'
    HEARTS = 'h'
    DIAMONDS = 'd'
    CLUBS = 'c'

    @property
    def glyph(self) -> str:
        """Return the Unicode glyph for the suit."""
        return {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}[self.value]

class Position(Enum):
    """Enum representing poker table positions."""
    # Specific positions
    UTG = "UTG"
    UTG1 = "UTG+1" 
    UTG2 = "UTG+2"
    MP = "MP"
    MP1 = "MP+1"
    MP2 = "MP+2"
    CO = "CO"
    BTN = "BTN"
    SB = "SB" 
    BB = "BB"
    
    # General categories for backward compatibility
    EARLY = 1000
    MIDDLE = 2000
    LATE = 3000
    BLINDS = 4000

    def category(self) -> str:
        """Return the category name of the position."""
        late_positions = {Position.CO, Position.BTN}
        early_positions = {Position.UTG, Position.UTG1, Position.UTG2}
        blind_positions = {Position.SB, Position.BB}
        
        if self in late_positions or self is Position.LATE:
            return 'Late'
        elif self in early_positions or self is Position.EARLY:
            return 'Early'
        elif self in blind_positions or self is Position.BLINDS:
            return 'Blinds'
        else:
            return 'Middle'
    
    def is_late(self) -> bool:
        """Return True if this is a late position."""
        return self in {Position.CO, Position.BTN, Position.LATE}

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
        's': Suit.SPADES, 'h': Suit.HEARTS, 
        'd': Suit.DIAMONDS, 'c': Suit.CLUBS
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
    
    # Combine hole cards and board cards for full analysis
    all_cards = hc[:2]
    if board_cards:
        all_cards.extend(list(board_cards))
    
    # Count rank occurrences
    rank_counts = {}
    for card in all_cards:
        rank_val = int(card.rank.value)
        rank_counts[rank_val] = rank_counts.get(rank_val, 0) + 1
    
    # Sort by count and rank
    pairs = sorted([rank for rank, count in rank_counts.items() if count >= 2], reverse=True)
    
    hole_ranks = sorted([int(c.rank.value) for c in hc[:2]], reverse=True)
    pocket_pair = hole_ranks[0] == hole_ranks[1]
    
    # Determine hand type and strength
    if len(pairs) >= 2:
        # Two pair or better
        strength = 8.5 + (pairs[0] + pairs[1]) / 28.0  # Two pair strength > 8.0
        hand_type = 'TWO_PAIR'
    elif len(pairs) == 1:
        # One pair
        if pocket_pair:
            # Pocket pairs: AA=9.5, KK=9.0, QQ=8.5, JJ=8.0, etc.
            strength = 5.0 + (pairs[0] - 2) * 0.5
        else:
            # Paired with board
            strength = 6.0 + (pairs[0] - 2) * 0.2
        hand_type = 'ONE_PAIR'
    else:
        # High card only
        strength = (hole_ranks[0] + hole_ranks[1] * 0.5) / 3.0
        hand_type = 'HIGH_CARD'
    
    # Cap strength at 10.0
    strength = min(strength, 10.0)
    
    # Determine advice based on strength
    if strength >= 8.0:
        advice = 'raise'
    elif strength >= 6.0:
        advice = 'call'
    else:
        advice = 'fold'
    
    # Get position category properly
    position_category = None
    if position:
        try:
            position_category = position.category()
        except AttributeError:
            position_category = getattr(position, 'value', str(position))
    
    return HandAnalysisResult(
        strength=strength, 
        advice=advice, 
        details={
            'ONE_PAIR': len(pairs) >= 1, 
            'TWO_PAIR': len(pairs) >= 2,
            'hand_type': hand_type,
            'position': position_category
        }
    )
