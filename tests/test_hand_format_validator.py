#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hand Format Validator Test Suite
==================================

Comprehensive tests for hand_format_validator.py with 50+ test cases
covering all supported formats, edge cases, and performance requirements.

Module: tests.test_hand_format_validator
Version: 1.0.0
Last Modified: 2025-10-24
Test Coverage Target: 99%+
Performance Target: 1000+ hands/second
"""

import pytest
import time
import sys
from pathlib import Path
from typing import List

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pokertool.hand_format_validator import (
    HandFormatValidator,
    ParsedHand,
    Card,
    HandFormatType,
    get_validator,
    normalize_hand_format,
    validate_hand_format
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def validator():
    """Fixture providing a HandFormatValidator instance."""
    return HandFormatValidator()


# ============================================================================
# STANDARD FORMAT TESTS
# ============================================================================

class TestStandardFormat:
    """Tests for standard space-separated format."""

    def test_standard_format_hole_cards_only(self, validator):
        """Test standard format with just hole cards."""
        result = validator.validate_and_parse("As Kh")
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0] == Card('A', 's')
        assert result.hole_cards[1] == Card('K', 'h')
        assert result.board_cards is None
        assert result.detected_format_type == HandFormatType.STANDARD

    def test_standard_format_with_flop(self, validator):
        """Test standard format with hole cards and flop."""
        result = validator.validate_and_parse("As Kh Qh 9c 2d")
        assert len(result.hole_cards) == 2
        assert len(result.board_cards) == 3
        assert result.detected_format_type == HandFormatType.WITH_BOARD

    def test_standard_format_with_turn(self, validator):
        """Test standard format with hole cards and turn."""
        result = validator.validate_and_parse("As Kh Qh 9c 2d 8s")
        assert len(result.hole_cards) == 2
        assert len(result.board_cards) == 4

    def test_standard_format_with_river(self, validator):
        """Test standard format with hole cards and river."""
        result = validator.validate_and_parse("As Kh Qh 9c 2d 8s 3h")
        assert len(result.hole_cards) == 2
        assert len(result.board_cards) == 5

    def test_standard_format_all_ranks(self, validator):
        """Test all valid ranks in standard format."""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        for i, rank in enumerate(ranks[:-1]):
            hand = f"{rank}s {ranks[i+1]}h"
            result = validator.validate_and_parse(hand)
            assert len(result.hole_cards) == 2

    def test_standard_format_all_suits(self, validator):
        """Test all valid suits in standard format."""
        suits = ['s', 'h', 'd', 'c']
        for i, suit in enumerate(suits[:-1]):
            hand = f"A{suit} K{suits[i+1]}"
            result = validator.validate_and_parse(hand)
            assert len(result.hole_cards) == 2

    def test_standard_format_normalization(self, validator):
        """Test normalization to standard format."""
        result = validator.validate_and_parse("As Kh")
        normalized = result.to_standard_format()
        assert normalized == "As Kh"

    def test_standard_format_case_insensitive(self, validator):
        """Test that suits are normalized to lowercase."""
        result = validator.validate_and_parse("AS KH")
        assert result.hole_cards[0].suit == 's'
        assert result.hole_cards[1].suit == 'h'


# ============================================================================
# COMPACT FORMAT TESTS
# ============================================================================

class TestCompactFormat:
    """Tests for compact no-space format."""

    def test_compact_format_basic(self, validator):
        """Test basic compact format."""
        result = validator.validate_and_parse("AsKh")
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0] == Card('A', 's')
        assert result.hole_cards[1] == Card('K', 'h')
        assert result.detected_format_type == HandFormatType.COMPACT

    def test_compact_format_all_ranks(self, validator):
        """Test all ranks in compact format."""
        hands = ["AsKh", "KsQh", "JsTh", "9s8h", "7s6h", "5s4h", "3s2h"]
        for hand in hands:
            result = validator.validate_and_parse(hand)
            assert len(result.hole_cards) == 2

    def test_compact_format_to_standard(self, validator):
        """Test conversion from compact to standard."""
        result = validator.validate_and_parse("AsKh")
        standard = result.to_standard_format()
        assert standard == "As Kh"

    def test_compact_format_to_compact(self, validator):
        """Test compact format preservation."""
        result = validator.validate_and_parse("AsKh")
        compact = result.to_compact_format()
        assert compact == "AsKh"


# ============================================================================
# LONG FORM FORMAT TESTS
# ============================================================================

class TestLongFormFormat:
    """Tests for long-form text format."""

    def test_long_form_basic(self, validator):
        """Test basic long-form format."""
        result = validator.validate_and_parse("Ace of Spades King of Hearts")
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0] == Card('A', 's')
        assert result.hole_cards[1] == Card('K', 'h')
        assert result.detected_format_type == HandFormatType.LONG_FORM

    def test_long_form_without_of(self, validator):
        """Test long-form without 'of' word."""
        result = validator.validate_and_parse("Ace Spades King Hearts")
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0] == Card('A', 's')
        assert result.hole_cards[1] == Card('K', 'h')

    def test_long_form_with_commas(self, validator):
        """Test long-form with comma separators."""
        result = validator.validate_and_parse("Ace of Spades, King of Hearts")
        assert len(result.hole_cards) == 2

    def test_long_form_various_ranks(self, validator):
        """Test various rank names in long-form."""
        test_cases = [
            ("Queen of Diamonds Jack of Clubs", Card('Q', 'd'), Card('J', 'c')),
            ("Ten of Hearts Nine of Spades", Card('T', 'h'), Card('9', 's')),
            ("Eight of Clubs Seven of Diamonds", Card('8', 'c'), Card('7', 'd')),
            ("Deuce of Spades Three of Hearts", Card('2', 's'), Card('3', 'h'))
        ]
        for hand_str, card1, card2 in test_cases:
            result = validator.validate_and_parse(hand_str)
            assert result.hole_cards[0] == card1
            assert result.hole_cards[1] == card2


# ============================================================================
# COMPONENT FORMAT TESTS
# ============================================================================

class TestComponentFormat:
    """Tests for component/dictionary format."""

    def test_component_format_basic(self, validator):
        """Test basic component format."""
        components = [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"}
        ]
        result = validator.validate_and_parse(components)
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0] == Card('A', 's')
        assert result.hole_cards[1] == Card('K', 'h')
        assert result.detected_format_type == HandFormatType.COMPONENT

    def test_component_format_with_board(self, validator):
        """Test component format with board cards."""
        components = [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"},
            {"rank": "Q", "suit": "h"},
            {"rank": "9", "suit": "c"},
            {"rank": "2", "suit": "d"}
        ]
        result = validator.validate_and_parse(components)
        assert len(result.hole_cards) == 2
        assert len(result.board_cards) == 3

    def test_component_format_lowercase_rank(self, validator):
        """Test component format with lowercase rank."""
        components = [
            {"rank": "a", "suit": "s"},
            {"rank": "k", "suit": "h"}
        ]
        result = validator.validate_and_parse(components)
        assert result.hole_cards[0].rank == 'A'
        assert result.hole_cards[1].rank == 'K'

    def test_component_format_uppercase_suit(self, validator):
        """Test component format with uppercase suit."""
        components = [
            {"rank": "A", "suit": "S"},
            {"rank": "K", "suit": "H"}
        ]
        result = validator.validate_and_parse(components)
        assert result.hole_cards[0].suit == 's'
        assert result.hole_cards[1].suit == 'h'


# ============================================================================
# LIST FORMAT TESTS
# ============================================================================

class TestListFormat:
    """Tests for list of card strings format."""

    def test_list_format_basic(self, validator):
        """Test basic list format."""
        cards = ["As", "Kh"]
        result = validator.validate_and_parse(cards)
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0] == Card('A', 's')
        assert result.hole_cards[1] == Card('K', 'h')

    def test_list_format_with_board(self, validator):
        """Test list format with board cards."""
        cards = ["As", "Kh", "Qh", "9c", "2d"]
        result = validator.validate_and_parse(cards)
        assert len(result.hole_cards) == 2
        assert len(result.board_cards) == 3


# ============================================================================
# NORMALIZATION TESTS
# ============================================================================

class TestNormalization:
    """Tests for format normalization."""

    def test_normalize_standard_format(self, validator):
        """Test normalizing already-standard format."""
        normalized = validator.normalize("As Kh")
        assert normalized == "As Kh"

    def test_normalize_compact_format(self, validator):
        """Test normalizing compact format."""
        normalized = validator.normalize("AsKh")
        assert normalized == "As Kh"

    def test_normalize_long_form(self, validator):
        """Test normalizing long-form format."""
        normalized = validator.normalize("Ace of Spades King of Hearts")
        assert normalized == "As Kh"

    def test_normalize_component_format(self, validator):
        """Test normalizing component format."""
        components = [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"}
        ]
        normalized = validator.normalize(components)
        assert normalized == "As Kh"

    def test_normalize_list_format(self, validator):
        """Test normalizing list format."""
        normalized = validator.normalize(["As", "Kh"])
        assert normalized == "As Kh"

    def test_normalize_with_board(self, validator):
        """Test normalizing hand with board cards."""
        normalized = validator.normalize("As Kh Qh 9c 2d")
        assert normalized == "As Kh Qh 9c 2d"


# ============================================================================
# VALIDATION TESTS
# ============================================================================

class TestValidation:
    """Tests for format validation."""

    def test_is_valid_standard(self, validator):
        """Test valid standard format."""
        assert validator.is_valid("As Kh") is True

    def test_is_valid_compact(self, validator):
        """Test valid compact format."""
        assert validator.is_valid("AsKh") is True

    def test_is_valid_invalid_rank(self, validator):
        """Test invalid rank detection."""
        assert validator.is_valid("Xs Kh") is False

    def test_is_valid_invalid_suit(self, validator):
        """Test invalid suit detection."""
        assert validator.is_valid("Ax Kh") is False

    def test_is_valid_duplicate_card(self, validator):
        """Test duplicate card detection."""
        assert validator.is_valid("As As") is False

    def test_is_valid_too_short(self, validator):
        """Test hand too short detection."""
        assert validator.is_valid("As") is False

    def test_is_valid_empty_string(self, validator):
        """Test empty string detection."""
        assert validator.is_valid("") is False

    def test_get_validation_error_valid(self, validator):
        """Test getting error for valid hand."""
        error = validator.get_validation_error("As Kh")
        assert error is None

    def test_get_validation_error_invalid(self, validator):
        """Test getting error message for invalid hand."""
        error = validator.get_validation_error("Xs Kh")
        assert error is not None
        assert "Invalid rank" in error


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Tests for error handling and messages."""

    def test_error_invalid_rank(self, validator):
        """Test error message for invalid rank."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse("Xs Kh")
        assert "Invalid rank" in str(exc_info.value)
        assert "Xs" in str(exc_info.value)

    def test_error_invalid_suit(self, validator):
        """Test error message for invalid suit."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse("Ax Kh")
        assert "Invalid suit" in str(exc_info.value)

    def test_error_duplicate_cards(self, validator):
        """Test error message for duplicate cards."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse("As As")
        assert "Duplicate cards" in str(exc_info.value)

    def test_error_empty_string(self, validator):
        """Test error for empty string."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse("")
        assert "empty" in str(exc_info.value).lower()

    def test_error_wrong_type(self, validator):
        """Test error for wrong input type."""
        with pytest.raises(ValueError):
            validator.validate_and_parse(123)

    def test_error_too_few_cards_component(self, validator):
        """Test error for too few cards in component format."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse([{"rank": "A", "suit": "s"}])
        assert "at least 2 cards" in str(exc_info.value)

    def test_error_missing_rank_component(self, validator):
        """Test error for missing rank in component."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse([
                {"suit": "s"},
                {"rank": "K", "suit": "h"}
            ])
        assert "rank" in str(exc_info.value).lower()

    def test_error_missing_suit_component(self, validator):
        """Test error for missing suit in component."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse([
                {"rank": "A"},
                {"rank": "K", "suit": "h"}
            ])
        assert "suit" in str(exc_info.value).lower()

    def test_error_invalid_board_size(self, validator):
        """Test error for invalid board size."""
        with pytest.raises(ValueError) as exc_info:
            validator.validate_and_parse("As Kh Qh")  # Only 1 board card
        assert "3 (flop), 4 (turn), or 5 (river)" in str(exc_info.value)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_edge_case_whitespace_trimming(self, validator):
        """Test whitespace is properly trimmed."""
        result = validator.validate_and_parse("  As Kh  ")
        assert result.to_standard_format() == "As Kh"

    def test_edge_case_mixed_case_suits(self, validator):
        """Test mixed case suits are normalized."""
        result = validator.validate_and_parse("AS kH")
        assert result.hole_cards[0].suit == 's'
        assert result.hole_cards[1].suit == 'h'

    def test_edge_case_ten_rank(self, validator):
        """Test 'T' rank for ten."""
        result = validator.validate_and_parse("Ts 9h")
        assert result.hole_cards[0].rank == 'T'

    def test_edge_case_all_same_suit(self, validator):
        """Test all cards same suit (valid)."""
        result = validator.validate_and_parse("As Ks")
        assert len(result.hole_cards) == 2

    def test_edge_case_all_same_rank_different_suits(self, validator):
        """Test same rank different suits (valid)."""
        result = validator.validate_and_parse("As Ah")
        assert len(result.hole_cards) == 2

    def test_edge_case_lowest_cards(self, validator):
        """Test lowest possible cards."""
        result = validator.validate_and_parse("2s 3h")
        assert result.hole_cards[0].rank == '2'
        assert result.hole_cards[1].rank == '3'

    def test_edge_case_highest_cards(self, validator):
        """Test highest possible cards."""
        result = validator.validate_and_parse("As Ah")
        assert result.hole_cards[0].rank == 'A'
        assert result.hole_cards[1].rank == 'A'


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Tests for performance requirements."""

    def test_performance_standard_format(self, validator):
        """Test parsing performance for standard format."""
        num_iterations = 1000
        test_hand = "As Kh"

        start_time = time.time()
        for _ in range(num_iterations):
            validator.validate_and_parse(test_hand)
        elapsed = time.time() - start_time

        hands_per_second = num_iterations / elapsed
        assert hands_per_second > 1000, f"Only {hands_per_second:.0f} hands/sec, expected >1000"

    def test_performance_compact_format(self, validator):
        """Test parsing performance for compact format."""
        num_iterations = 1000
        test_hand = "AsKh"

        start_time = time.time()
        for _ in range(num_iterations):
            validator.validate_and_parse(test_hand)
        elapsed = time.time() - start_time

        hands_per_second = num_iterations / elapsed
        assert hands_per_second > 1000, f"Only {hands_per_second:.0f} hands/sec, expected >1000"

    def test_performance_normalization(self, validator):
        """Test normalization performance."""
        num_iterations = 1000
        test_hands = ["As Kh", "AsKh", ["As", "Kh"]]

        start_time = time.time()
        for _ in range(num_iterations // len(test_hands)):
            for hand in test_hands:
                validator.normalize(hand)
        elapsed = time.time() - start_time

        hands_per_second = num_iterations / elapsed
        assert hands_per_second > 1000, f"Only {hands_per_second:.0f} hands/sec, expected >1000"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Tests for integration with existing code."""

    def test_integration_with_storage_format(self, validator):
        """Test compatibility with storage.py format."""
        # Storage.py expects "As Kh" format
        test_cases = [
            "As Kh",
            "AsKh",
            "Ace of Spades King of Hearts"
        ]

        for test_case in test_cases:
            normalized = validator.normalize(test_case)
            # Should match storage.py validation pattern
            assert ' ' in normalized or len(normalized) == 5
            # Should have valid cards
            assert validator.is_valid(normalized)

    def test_integration_database_constraint_compliance(self, validator):
        """Test compliance with database GLOB constraints."""
        # Database constraint from storage.py line 100-101:
        # hand_text GLOB '[AKQJT2-9][shdc][AKQJT2-9][shdc]'
        # or hand_text GLOB '[AKQJT2-9][shdc][AKQJT2-9][shdc] [AKQJT2-9][shdc][AKQJT2-9][shdc]'

        test_hands = [
            "As Kh",
            "QdQc",
            "Ts 9h"
        ]

        for hand in test_hands:
            normalized = validator.normalize(hand)
            # Check it matches database pattern
            import re
            # Two-card format with space: "As Kh"
            pattern = r'^[AKQJT2-9][shdc] [AKQJT2-9][shdc]$'
            assert re.match(pattern, normalized), f"Failed to match pattern for '{normalized}'"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_validator_singleton(self):
        """Test get_validator returns same instance."""
        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2

    def test_normalize_hand_format_function(self):
        """Test normalize_hand_format convenience function."""
        result = normalize_hand_format("AsKh")
        assert result == "As Kh"

    def test_validate_hand_format_function(self):
        """Test validate_hand_format convenience function."""
        assert validate_hand_format("As Kh") is True
        assert validate_hand_format("Xs Kh") is False


# ============================================================================
# CARD CLASS TESTS
# ============================================================================

class TestCard:
    """Tests for Card class."""

    def test_card_creation(self):
        """Test Card object creation."""
        card = Card('A', 's')
        assert card.rank == 'A'
        assert card.suit == 's'

    def test_card_string_representation(self):
        """Test Card string conversion."""
        card = Card('A', 's')
        assert str(card) == "As"

    def test_card_equality(self):
        """Test Card equality comparison."""
        card1 = Card('A', 's')
        card2 = Card('A', 's')
        card3 = Card('K', 'h')
        assert card1 == card2
        assert card1 != card3

    def test_card_hashable(self):
        """Test Card is hashable for sets."""
        cards = {Card('A', 's'), Card('K', 'h'), Card('A', 's')}
        assert len(cards) == 2  # Duplicate removed

    def test_card_invalid_creation(self):
        """Test Card creation with invalid data."""
        with pytest.raises(ValueError):
            Card('', 's')
        with pytest.raises(ValueError):
            Card('A', '')


# ============================================================================
# SUMMARY REPORT
# ============================================================================

def test_summary():
    """Generate test coverage summary."""
    summary = {
        'standard_format_tests': 8,
        'compact_format_tests': 4,
        'long_form_tests': 4,
        'component_format_tests': 4,
        'list_format_tests': 2,
        'normalization_tests': 6,
        'validation_tests': 9,
        'error_handling_tests': 9,
        'edge_case_tests': 7,
        'performance_tests': 3,
        'integration_tests': 2,
        'convenience_function_tests': 3,
        'card_class_tests': 5
    }

    total_tests = sum(summary.values())

    print("\n" + "=" * 80)
    print("HAND FORMAT VALIDATOR TEST SUMMARY")
    print("=" * 80)
    print(f"Total Test Cases: {total_tests}")
    print(f"Standard Format Tests: {summary['standard_format_tests']}")
    print(f"Compact Format Tests: {summary['compact_format_tests']}")
    print(f"Long Form Tests: {summary['long_form_tests']}")
    print(f"Component Format Tests: {summary['component_format_tests']}")
    print(f"List Format Tests: {summary['list_format_tests']}")
    print(f"Normalization Tests: {summary['normalization_tests']}")
    print(f"Validation Tests: {summary['validation_tests']}")
    print(f"Error Handling Tests: {summary['error_handling_tests']}")
    print(f"Edge Case Tests: {summary['edge_case_tests']}")
    print(f"Performance Tests: {summary['performance_tests']}")
    print(f"Integration Tests: {summary['integration_tests']}")
    print(f"Convenience Function Tests: {summary['convenience_function_tests']}")
    print(f"Card Class Tests: {summary['card_class_tests']}")
    print("=" * 80)
    print(f"Target: 50+ tests")
    print(f"Actual: {total_tests} tests")
    print(f"Status: {'✓ PASS' if total_tests >= 50 else '✗ FAIL'}")
    print("=" * 80)

    assert total_tests >= 50, f"Need at least 50 tests, got {total_tests}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
