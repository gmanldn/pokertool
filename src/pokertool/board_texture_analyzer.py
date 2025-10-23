"""Board Texture Analysis - Wet/Dry Classification"""
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class BoardTexture:
    classification: str  # 'wet', 'dry', 'semi-wet'
    connectivity_score: float  # 0-1
    suit_coordination: float  # 0-1
    paired: bool
    monotone: bool  # All same suit
    rainbow: bool  # All different suits
    straight_possible: bool
    flush_possible: bool

class BoardTextureAnalyzer:
    """Analyze poker board texture."""
    
    def analyze(self, board_cards: List[str]) -> BoardTexture:
        """
        Analyze board texture.
        
        Args:
            board_cards: List of card strings (e.g., ['As', 'Kh', 'Qh'])
        """
        if len(board_cards) < 3:
            return BoardTexture('unknown', 0, 0, False, False, False, False, False)
        
        ranks = [self._parse_rank(c) for c in board_cards]
        suits = [self._parse_suit(c) for c in board_cards]
        
        # Check for pairs
        paired = len(ranks) != len(set(ranks))
        
        # Suit coordination
        suit_counts = {s: suits.count(s) for s in set(suits)}
        max_suited = max(suit_counts.values())
        monotone = max_suited == len(suits)
        rainbow = len(set(suits)) == len(suits)
        flush_possible = max_suited >= 2
        
        # Connectivity
        sorted_ranks = sorted(ranks)
        max_gap = max(sorted_ranks[i+1] - sorted_ranks[i] for i in range(len(sorted_ranks)-1))
        connectivity = 1.0 - (max_gap / 14.0)
        
        # Straight possible
        rank_range = max(ranks) - min(ranks)
        straight_possible = rank_range <= 4
        
        # Classify
        if flush_possible and straight_possible:
            classification = 'wet'
        elif not flush_possible and not straight_possible:
            classification = 'dry'
        else:
            classification = 'semi-wet'
        
        return BoardTexture(
            classification=classification,
            connectivity_score=connectivity,
            suit_coordination=max_suited / len(suits),
            paired=paired,
            monotone=monotone,
            rainbow=rainbow,
            straight_possible=straight_possible,
            flush_possible=flush_possible
        )
    
    def _parse_rank(self, card: str) -> int:
        """Parse rank to numeric value."""
        rank_map = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10}
        rank = card[0].upper()
        return rank_map.get(rank, int(rank))
    
    def _parse_suit(self, card: str) -> str:
        """Parse suit."""
        return card[1].lower()
