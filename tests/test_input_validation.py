#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for Input Validation System
========================================

Comprehensive tests for poker-specific input validation.

Module: tests.test_input_validation
Version: 1.0.0
"""

import pytest

from pokertool.input_validation import (
    ValidationResult,
    CardValidator,
    BetValidator,
    PlayerValidator,
    TableValidator,
    validate_card,
    validate_bet,
    sanitize_table_data
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_success(self):
        """Test creating successful validation result."""
        result = ValidationResult(
            valid=True,
            value="As",
            error=None,
            warnings=[]
        )

        assert result.valid is True
        assert result.value == "As"
        assert result.error is None
        assert result.warnings == []

    def test_validation_result_failure(self):
        """Test creating failed validation result."""
        result = ValidationResult(
            valid=False,
            value=None,
            error="Invalid input"
        )

        assert result.valid is False
        assert result.error == "Invalid input"


class TestCardValidator:
    """Test CardValidator class."""

    def test_validate_valid_cards(self):
        """Test validating valid cards."""
        valid_cards = ["As", "Kh", "Qd", "Jc", "Ts", "9h", "8d", "7c",
                       "6s", "5h", "4d", "3c", "2s"]

        for card in valid_cards:
            result = CardValidator.validate(card)
            assert result.valid is True
            assert result.value is not None
            assert result.error is None

    def test_validate_ten_card(self):
        """Test validating '10' as 'T'."""
        result = CardValidator.validate("10h")
        assert result.valid is True
        assert result.value == "Th"

    def test_validate_lowercase_suit(self):
        """Test suit normalization to lowercase."""
        result = CardValidator.validate("KD")
        assert result.valid is True
        assert result.value == "Kd"

    def test_validate_invalid_rank(self):
        """Test invalid rank."""
        result = CardValidator.validate("Xs")
        assert result.valid is False
        assert "Invalid rank" in result.error

    def test_validate_invalid_suit(self):
        """Test invalid suit."""
        result = CardValidator.validate("Az")
        assert result.valid is False
        assert "Invalid suit" in result.error

    def test_validate_empty_card(self):
        """Test empty card string."""
        result = CardValidator.validate("")
        assert result.valid is False
        assert "non-empty string" in result.error

    def test_validate_wrong_length(self):
        """Test card with wrong length."""
        result = CardValidator.validate("Ash")
        assert result.valid is False
        assert "2 characters" in result.error

    def test_validate_hand_two_cards(self):
        """Test validating 2-card hand."""
        result = CardValidator.validate_hand(["As", "Kh"])
        assert result.valid is True
        assert len(result.value) == 2
        assert result.value == ["As", "Kh"]

    def test_validate_hand_five_cards(self):
        """Test validating 5-card hand."""
        result = CardValidator.validate_hand(["As", "Kh", "Qd", "Jc", "Ts"])
        assert result.valid is True
        assert len(result.value) == 5

    def test_validate_hand_empty(self):
        """Test validating empty hand."""
        result = CardValidator.validate_hand([])
        assert result.valid is True
        assert result.value == []

    def test_validate_hand_wrong_count(self):
        """Test hand with invalid number of cards."""
        result = CardValidator.validate_hand(["As", "Kh", "Qd"])
        assert result.valid is False
        assert "0, 2, or 5 cards" in result.error

    def test_validate_hand_duplicate_cards(self):
        """Test hand with duplicate cards."""
        result = CardValidator.validate_hand(["As", "As"])
        assert result.valid is True
        assert len(result.warnings) > 0
        assert "Duplicate" in result.warnings[0]

    def test_validate_hand_invalid_card(self):
        """Test hand with invalid card."""
        result = CardValidator.validate_hand(["As", "XX"])
        assert result.valid is False
        assert "Invalid card" in result.error


class TestBetValidator:
    """Test BetValidator class."""

    def test_validate_integer_bet(self):
        """Test validating integer bet."""
        result = BetValidator.validate(100)
        assert result.valid is True
        assert result.value == 100.0

    def test_validate_float_bet(self):
        """Test validating float bet."""
        result = BetValidator.validate(150.50)
        assert result.valid is True
        assert result.value == 150.50

    def test_validate_string_bet_usd(self):
        """Test validating USD string bet."""
        result = BetValidator.validate("$100.50")
        assert result.valid is True
        assert result.value == 100.50

    def test_validate_string_bet_with_comma(self):
        """Test validating bet with thousand separator."""
        result = BetValidator.validate("$1,234.56")
        assert result.valid is True
        assert result.value == 1234.56

    def test_validate_european_format(self):
        """Test European number format (comma as decimal)."""
        result = BetValidator.validate("€100,50")
        assert result.valid is True
        assert result.value == 100.50

    def test_validate_negative_bet(self):
        """Test negative bet (should fail)."""
        result = BetValidator.validate(-50)
        assert result.valid is False
        assert "cannot be negative" in result.error

    def test_validate_nan_bet(self):
        """Test NaN bet."""
        result = BetValidator.validate(float('nan'))
        assert result.valid is False
        assert "NaN" in result.error

    def test_validate_invalid_string(self):
        """Test invalid string bet."""
        result = BetValidator.validate("abc")
        assert result.valid is False
        assert "Cannot parse" in result.error

    def test_validate_bet_rounding(self):
        """Test bet rounding to 2 decimal places."""
        result = BetValidator.validate(100.123456)
        assert result.valid is True
        assert result.value == 100.12

    def test_validate_bet_range_minimum(self):
        """Test bet below minimum."""
        result = BetValidator.validate(50, min_bet=100)
        assert result.valid is True
        assert len(result.warnings) > 0
        assert "below minimum" in result.warnings[0]

    def test_validate_bet_range_maximum(self):
        """Test bet above maximum."""
        result = BetValidator.validate(2000, max_bet=1000)
        assert result.valid is True
        assert len(result.warnings) > 0
        assert "exceeds maximum" in result.warnings[0]


class TestPlayerValidator:
    """Test PlayerValidator class."""

    def test_validate_name_valid(self):
        """Test validating valid player name."""
        result = PlayerValidator.validate_name("Player1")
        assert result.valid is True
        assert result.value == "Player1"

    def test_validate_name_with_whitespace(self):
        """Test name with leading/trailing whitespace."""
        result = PlayerValidator.validate_name("  Player1  ")
        assert result.valid is True
        assert result.value == "Player1"

    def test_validate_name_too_short(self):
        """Test name that's too short."""
        result = PlayerValidator.validate_name("")
        assert result.valid is False
        assert "too short" in result.error

    def test_validate_name_too_long(self):
        """Test name that's too long."""
        long_name = "A" * 100
        result = PlayerValidator.validate_name(long_name)
        assert result.valid is False
        assert "too long" in result.error

    def test_validate_name_suspicious_sql(self):
        """Test name with SQL injection attempt."""
        result = PlayerValidator.validate_name("'; DROP TABLE users--")
        assert result.valid is True
        assert len(result.warnings) > 0
        assert "suspicious" in result.warnings[0].lower()

    def test_validate_name_suspicious_xss(self):
        """Test name with XSS attempt."""
        result = PlayerValidator.validate_name("<script>alert('xss')</script>")
        assert result.valid is True
        assert len(result.warnings) > 0

    def test_validate_seat_valid(self):
        """Test validating valid seat number."""
        result = PlayerValidator.validate_seat(5)
        assert result.valid is True
        assert result.value == 5

    def test_validate_seat_string(self):
        """Test validating seat from string."""
        result = PlayerValidator.validate_seat("7")
        assert result.valid is True
        assert result.value == 7

    def test_validate_seat_below_minimum(self):
        """Test seat below minimum."""
        result = PlayerValidator.validate_seat(0)
        assert result.valid is False
        assert "must be 1-" in result.error

    def test_validate_seat_above_maximum(self):
        """Test seat above maximum."""
        result = PlayerValidator.validate_seat(11)
        assert result.valid is False
        assert "must be 1-" in result.error

    def test_validate_player_data_complete(self):
        """Test validating complete player data."""
        player_data = {
            'name': 'TestPlayer',
            'stack': 100.50,
            'bet': 25,
            'vpip': 30.5,
            'af': 2.3,
            'pfr': 25.0,
            'is_active': True,
            'status': 'Active'
        }

        result = PlayerValidator.validate_player_data(player_data)
        assert result.valid is True
        assert result.value['name'] == 'TestPlayer'
        assert result.value['stack'] == 100.50
        assert result.value['vpip'] == 30.5

    def test_validate_player_data_invalid_name(self):
        """Test player data with invalid name."""
        player_data = {'name': ''}

        result = PlayerValidator.validate_player_data(player_data)
        assert result.valid is False
        assert "Invalid name" in result.error

    def test_validate_player_data_percentage_out_of_range(self):
        """Test player data with percentage out of range."""
        player_data = {
            'name': 'TestPlayer',
            'vpip': 150  # Invalid percentage
        }

        result = PlayerValidator.validate_player_data(player_data)
        assert result.valid is True
        assert 'vpip' not in result.value
        assert len(result.warnings) > 0


class TestTableValidator:
    """Test TableValidator class."""

    def test_validate_stage_valid(self):
        """Test validating valid game stage."""
        for stage in ['preflop', 'flop', 'turn', 'river', 'showdown']:
            result = TableValidator.validate_stage(stage)
            assert result.valid is True
            assert result.value == stage

    def test_validate_stage_case_insensitive(self):
        """Test stage validation is case-insensitive."""
        result = TableValidator.validate_stage("FLOP")
        assert result.valid is True
        assert result.value == "flop"

    def test_validate_stage_invalid(self):
        """Test invalid game stage."""
        result = TableValidator.validate_stage("invalid_stage")
        assert result.valid is False
        assert "Invalid stage" in result.error

    def test_validate_table_data_complete(self):
        """Test validating complete table data."""
        table_data = {
            'pot': 150.50,
            'small_blind': 1,
            'big_blind': 2,
            'board': ['As', 'Kh', 'Qd'],
            'stage': 'flop',
            'dealer_seat': 5,
            'players': {
                1: {'name': 'Player1', 'stack': 100},
                2: {'name': 'Player2', 'stack': 200}
            }
        }

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True
        assert result.value['pot'] == 150.50
        assert result.value['stage'] == 'flop'
        assert len(result.value['board']) == 3

    def test_validate_table_data_invalid_board(self):
        """Test table data with invalid board cards."""
        table_data = {
            'board': ['As', 'XX', 'Kh']
        }

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True
        assert len(result.warnings) > 0
        assert result.value['board'] == []

    def test_validate_table_data_invalid_player_seat(self):
        """Test table data with invalid player seat."""
        table_data = {
            'players': {
                99: {'name': 'InvalidSeat'}  # Invalid seat number
            }
        }

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True
        assert len(result.warnings) > 0
        assert 99 not in result.value.get('players', {})

    def test_validate_table_data_pot_aliases(self):
        """Test pot_size alias."""
        table_data = {'pot_size': 100.50}

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True
        assert result.value['pot'] == 100.50

    def test_validate_table_data_board_aliases(self):
        """Test board_cards alias."""
        table_data = {'board_cards': ['As', 'Kh']}

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True
        assert len(result.value['board']) == 2


class TestConvenienceFunctions:
    """Test convenience helper functions."""

    def test_validate_card_function(self):
        """Test validate_card helper function."""
        valid, card, error = validate_card("As")
        assert valid is True
        assert card == "As"
        assert error is None

    def test_validate_card_function_invalid(self):
        """Test validate_card with invalid card."""
        valid, card, error = validate_card("XX")
        assert valid is False
        assert card is None
        assert error is not None

    def test_validate_bet_function(self):
        """Test validate_bet helper function."""
        valid, amount, error = validate_bet("$100.50")
        assert valid is True
        assert amount == 100.50
        assert error is None

    def test_validate_bet_function_invalid(self):
        """Test validate_bet with invalid amount."""
        valid, amount, error = validate_bet("abc")
        assert valid is False
        assert amount is None
        assert error is not None

    def test_sanitize_table_data_function(self):
        """Test sanitize_table_data helper function."""
        table_data = {
            'pot': '$150.00',
            'board': ['As', 'Kd'],
            'stage': 'flop'
        }

        sanitized = sanitize_table_data(table_data)
        assert sanitized['pot'] == 150.00
        assert len(sanitized['board']) == 2
        assert sanitized['stage'] == 'flop'


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_card_validation_with_unicode(self):
        """Test card validation with unicode characters."""
        result = CardValidator.validate("A♠")  # Unicode spade
        assert result.valid is False

    def test_bet_validation_zero(self):
        """Test bet validation with zero."""
        result = BetValidator.validate(0)
        assert result.valid is True
        assert result.value == 0.0

    def test_bet_validation_very_large_number(self):
        """Test bet with very large number."""
        result = BetValidator.validate(1_000_000_000)
        assert result.valid is True
        assert len(result.warnings) > 0  # Exceeds max

    def test_player_name_with_control_characters(self):
        """Test player name with control characters."""
        result = PlayerValidator.validate_name("Player\x00Name")
        assert result.valid is True
        # Control characters should be removed
        assert "\x00" not in result.value

    def test_table_data_with_none_values(self):
        """Test table data with None values."""
        table_data = {
            'pot': None,
            'board': None,
            'players': None
        }

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_complete_hand_analysis_input(self):
        """Test validating complete hand analysis input."""
        # Simulate input for hand analysis
        hand_input = {
            'hero_cards': ['As', 'Kh'],
            'villain_cards': ['Qd', 'Jc'],
            'board': ['Ts', '9h', '8d'],
            'pot': '$150.50',
            'hero_stack': '$1,234.56',
            'villain_stack': '€987,65'
        }

        # Validate hero cards
        hero_result = CardValidator.validate_hand(hand_input['hero_cards'])
        assert hero_result.valid is True

        # Validate board
        board_result = CardValidator.validate_hand(hand_input['board'])
        assert board_result.valid is True

        # Validate pot
        pot_result = BetValidator.validate(hand_input['pot'])
        assert pot_result.valid is True

        # Validate stacks
        hero_stack_result = BetValidator.validate(hand_input['hero_stack'])
        villain_stack_result = BetValidator.validate(hand_input['villain_stack'])
        assert hero_stack_result.valid is True
        assert villain_stack_result.valid is True

    def test_multiplayer_table_validation(self):
        """Test validating a full multiplayer table."""
        table_data = {
            'pot': 500.00,
            'small_blind': 5,
            'big_blind': 10,
            'board': ['As', 'Kh', 'Qd', 'Jc', 'Ts'],
            'stage': 'river',
            'dealer_seat': 1,
            'players': {
                1: {'name': 'Player1', 'stack': 1000, 'bet': 0, 'status': 'Active'},
                2: {'name': 'Player2', 'stack': 800, 'bet': 50, 'status': 'Active'},
                3: {'name': 'Player3', 'stack': 1200, 'bet': 100, 'status': 'Active'},
                4: {'name': 'Player4', 'stack': 500, 'bet': 0, 'status': 'Folded'},
                5: {'name': 'Player5', 'stack': 0, 'bet': 0, 'status': 'Empty'},
            }
        }

        result = TableValidator.validate_table_data(table_data)
        assert result.valid is True
        assert len(result.value['players']) == 5
        assert len(result.value['board']) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
