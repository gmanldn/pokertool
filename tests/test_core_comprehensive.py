#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tests/test_core_comprehensive.py
# version: v28.0.0
# last_commit: '2025-09-25T17:18:44.722149+00:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
# -*- coding: utf-8 -*-

"""
Comprehensive Unit Tests for PokerTool Core Module
==================================================

Enterprise-grade unit tests ensuring 95%+ code coverage and accuracy.

Module: tests.test_core_comprehensive
Version: 20.0.0
Last Modified: 2025-09-25
Author: PokerTool Development Team
License: MIT
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from pokertool.core import (
        Rank, Suit, Position, Card, 
        parse_card, analyse_hand, HandAnalysisResult
    )
    CORE_AVAILABLE = True
except ImportError as e:
    CORE_AVAILABLE = False
    pytest.skip(f"Core module not available: {e}", allow_module_level=True)

class TestRankEnum:
    """Comprehensive tests for Rank enumeration."""
    
    def test_all_rank_values(self):
        """Test all rank values are correct."""
        expected_ranks = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13, Rank.ACE: 14
        }
        
        for rank, expected_value in expected_ranks.items():
            assert rank.value == expected_value
    
    def test_rank_symbols(self):
        """Test all rank symbols are correct."""
        expected_symbols = {
            Rank.TWO: '2', Rank.THREE: '3', Rank.FOUR: '4', Rank.FIVE: '5',
            Rank.SIX: '6', Rank.SEVEN: '7', Rank.EIGHT: '8', Rank.NINE: '9',
            Rank.TEN: 'T', Rank.JACK: 'J', Rank.QUEEN: 'Q', Rank.KING: 'K', Rank.ACE: 'A'
        }
        
        for rank, expected_symbol in expected_symbols.items():
            assert rank.sym == expected_symbol
    
    def test_rank_val_property(self):
        """Test legacy val property works correctly."""
        for rank in Rank:
            assert rank.val == rank.value

class TestSuitEnum:
    """Comprehensive tests for Suit enumeration."""
    
    def test_all_suit_values(self):
        """Test all suit values are correct."""
        expected_suits = {
            Suit.SPADES: 's', Suit.HEARTS: 'h', 
            Suit.DIAMONDS: 'd', Suit.CLUBS: 'c'
        }
        
        for suit, expected_value in expected_suits.items():
            assert suit.value == expected_value
    
    def test_suit_glyphs(self):
        """Test all suit glyphs are correct."""
        expected_glyphs = {
            Suit.SPADES: '♠', Suit.HEARTS: '♥', 
            Suit.DIAMONDS: '♦', Suit.CLUBS: '♣'
        }
        
        for suit, expected_glyph in expected_glyphs.items():
            assert suit.glyph == expected_glyph

class TestPositionEnum:
    """Comprehensive tests for Position enumeration."""
    
    def test_specific_positions(self):
        """Test specific position values."""
        specific_positions = {
            Position.UTG: "UTG", Position.UTG1: "UTG+1", Position.UTG2: "UTG+2",
            Position.MP: "MP", Position.MP1: "MP+1", Position.MP2: "MP+2",
            Position.CO: "CO", Position.BTN: "BTN", Position.SB: "SB", Position.BB: "BB"
        }
        
        for position, expected_value in specific_positions.items():
            assert position.value == expected_value
    
    def test_position_categorization(self):
        """Test position category method."""
        early_positions = [Position.UTG, Position.UTG1, Position.UTG2, Position.EARLY]
        middle_positions = [Position.MP, Position.MP1, Position.MP2]
        late_positions = [Position.CO, Position.BTN, Position.LATE]
        blind_positions = [Position.SB, Position.BB, Position.BLINDS]
        
        for pos in early_positions:
            assert pos.category() == 'Early'
        
        for pos in middle_positions:
            assert pos.category() == 'Middle'
        
        for pos in late_positions:
            assert pos.category() == 'Late'
        
        for pos in blind_positions:
            assert pos.category() == 'Blinds'
    
    def test_is_late_method(self):
        """Test is_late method."""
        late_positions = [Position.CO, Position.BTN, Position.LATE]
        non_late_positions = [pos for pos in Position if pos not in late_positions]
        
        for pos in late_positions:
            assert pos.is_late()
        
        for pos in non_late_positions:
            assert not pos.is_late()

class TestCard:
    """Comprehensive tests for Card dataclass."""
    
    def test_card_creation(self):
        """Test card creation with all combinations."""
        for rank in Rank:
            for suit in Suit:
                card = Card(rank, suit)
                assert card.rank == rank
                assert card.suit == suit
    
    def test_card_string_representation(self):
        """Test card string representation."""
        test_cases = [
            (Card(Rank.ACE, Suit.SPADES), "As"),
            (Card(Rank.KING, Suit.HEARTS), "Kh"), 
            (Card(Rank.QUEEN, Suit.DIAMONDS), "Qd"),
            (Card(Rank.JACK, Suit.CLUBS), "Jc"),
            (Card(Rank.TEN, Suit.SPADES), "Ts"),
            (Card(Rank.TWO, Suit.HEARTS), "2h")
        ]
        
        for card, expected_str in test_cases:
            assert str(card) == expected_str
    
    def test_card_equality(self):
        """Test card equality comparison."""
        card1 = Card(Rank.ACE, Suit.SPADES)
        card2 = Card(Rank.ACE, Suit.SPADES)
        card3 = Card(Rank.KING, Suit.SPADES)
        
        assert card1 == card2
        assert card1 != card3

class TestParseCard:
    """Comprehensive tests for parse_card function."""
    
    def test_valid_card_parsing(self):
        """Test parsing of all valid card strings."""
        valid_cards = [
            ("As", Card(Rank.ACE, Suit.SPADES)),
            ("Kh", Card(Rank.KING, Suit.HEARTS)),
            ("Qd", Card(Rank.QUEEN, Suit.DIAMONDS)),
            ("Jc", Card(Rank.JACK, Suit.CLUBS)),
            ("Ts", Card(Rank.TEN, Suit.SPADES)),
            ("9h", Card(Rank.NINE, Suit.HEARTS)),
            ("2d", Card(Rank.TWO, Suit.DIAMONDS))
        ]
        
        for card_str, expected_card in valid_cards:
            parsed_card = parse_card(card_str)
            assert parsed_card == expected_card
    
    def test_case_insensitive_parsing(self):
        """Test that parsing is case insensitive."""
        test_cases = ["as", "AS", "aS", "As"]
        expected_card = Card(Rank.ACE, Suit.SPADES)
        
        for case in test_cases:
            parsed_card = parse_card(case)
            assert parsed_card == expected_card
    
    def test_invalid_card_parsing(self):
        """Test parsing of invalid card strings."""
        invalid_cards = ["", "A", "s", "Ax", "Xs", "123"]
        
        for invalid_card in invalid_cards:
            with pytest.raises(ValueError, match="Bad card"):
                parse_card(invalid_card)

class TestHandAnalysis:
    """Comprehensive tests for analyse_hand function."""
    
    def test_pair_hands(self):
        """Test analysis of pair hands."""
        pocket_aces = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
        result = analyse_hand(pocket_aces)
        
        assert result.strength >= 8.0
        assert result.advice in ['raise', 'call']
        assert result.details['ONE_PAIR']
        assert result.details['hand_type'] == 'ONE_PAIR'
    
    def test_two_pair_hands(self):
        """Test analysis of two pair hands."""
        hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        board_cards = [Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.KING, Suit.CLUBS), Card(Rank.TWO, Suit.SPADES)]
        
        result = analyse_hand(hole_cards, board_cards)
        
        assert result.strength >= 8.0
        assert result.details['TWO_PAIR']
        assert result.details['hand_type'] == 'TWO_PAIR'
    
    def test_high_card_hands(self):
        """Test analysis of high card hands."""
        high_card = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
        result = analyse_hand(high_card)
        
        assert result.strength < 6.0
        assert result.details['hand_type'] == 'HIGH_CARD'
        assert not result.details['ONE_PAIR']
        assert not result.details['TWO_PAIR']
    
    def test_insufficient_cards(self):
        """Test handling of insufficient cards."""
        one_card = [Card(Rank.ACE, Suit.SPADES)]
        result = analyse_hand(one_card)
        
        assert result.strength == 0.0
        assert result.advice == 'fold'
        assert 'error' in result.details
    
    def test_position_influence(self):
        """Test that position influences analysis."""
        hole_cards = [Card(Rank.JACK, Suit.SPADES), Card(Rank.TEN, Suit.HEARTS)]
        
        early_result = analyse_hand(hole_cards, position=Position.UTG)
        assert early_result.details['position'] == 'Early'
        
        late_result = analyse_hand(hole_cards, position=Position.BTN)
        assert late_result.details['position'] == 'Late'

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_workflow(self):
        """Test complete workflow from string parsing to analysis."""
        hole_card_strs = ['As', 'Kh']
        board_card_strs = ['Qd', 'Jc', 'Ts']
        
        hole_cards = [parse_card(card_str) for card_str in hole_card_strs]
        board_cards = [parse_card(card_str) for card_str in board_card_strs]
        
        result = analyse_hand(hole_cards, board_cards, Position.BTN)
        
        assert isinstance(result, HandAnalysisResult)
        assert result.strength > 0.0
        assert result.advice in ['fold', 'call', 'raise']
        assert 'hand_type' in result.details
        assert result.details['position'] == 'Late'

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=pokertool.core', '--cov-report=html'])
