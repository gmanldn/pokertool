"""Tests for v0.6.0: Board Format Validation

Tests board format validation including:
- Standard format: "Ks Qs Js" (space-separated)
- Compact format: "KsQsJs" (no spaces)
- Flop, turn, river validation
- Invalid format detection
"""

import pytest
from src.pokertool.validators.board_format_validator import (
    BoardFormatValidator,
    validate_board_format,
    parse_board,
    normalize_board_format,
    BoardFormatError,
)


class TestBoardFormatValidation:
    """Test board format validation."""

    def test_validate_standard_flop_format(self):
        """Test standard flop format with spaces."""
        board = "Ks Qs Js"
        assert validate_board_format(board) is True

    def test_validate_compact_flop_format(self):
        """Test compact flop format without spaces."""
        board = "KsQsJs"
        assert validate_board_format(board) is True

    def test_validate_standard_turn_format(self):
        """Test standard turn format (4 cards)."""
        board = "Ks Qs Js Ts"
        assert validate_board_format(board) is True

    def test_validate_compact_turn_format(self):
        """Test compact turn format (4 cards)."""
        board = "KsQsJsTs"
        assert validate_board_format(board) is True

    def test_validate_standard_river_format(self):
        """Test standard river format (5 cards)."""
        board = "Ks Qs Js Ts 9s"
        assert validate_board_format(board) is True

    def test_validate_compact_river_format(self):
        """Test compact river format (5 cards)."""
        board = "KsQsJsTs9s"
        assert validate_board_format(board) is True

    def test_validate_mixed_suits(self):
        """Test board with mixed suits."""
        board = "Ah Kd Qc"
        assert validate_board_format(board) is True

    def test_validate_mixed_ranks(self):
        """Test board with all rank types."""
        board = "Ah Kd Qc Jh Ts"
        assert validate_board_format(board) is True

    def test_reject_invalid_rank(self):
        """Test that invalid ranks are rejected."""
        board = "Xs Qs Js"  # X is not a valid rank
        assert validate_board_format(board) is False

    def test_reject_invalid_suit(self):
        """Test that invalid suits are rejected."""
        board = "Kx Qs Js"  # x is not a valid suit
        assert validate_board_format(board) is False

    def test_reject_too_few_cards(self):
        """Test that boards with < 3 cards are rejected."""
        board = "Ks Qs"  # Only 2 cards
        assert validate_board_format(board) is False

    def test_reject_too_many_cards(self):
        """Test that boards with > 5 cards are rejected."""
        board = "Ks Qs Js Ts 9s 8s"  # 6 cards
        assert validate_board_format(board) is False

    def test_reject_duplicate_cards(self):
        """Test that duplicate cards are rejected."""
        board = "Ks Ks Js"  # Duplicate Ks
        assert validate_board_format(board) is False

    def test_reject_empty_board(self):
        """Test that empty board is rejected."""
        board = ""
        assert validate_board_format(board) is False

    def test_reject_whitespace_only(self):
        """Test that whitespace-only board is rejected."""
        board = "   "
        assert validate_board_format(board) is False


class TestBoardFormatParsing:
    """Test board format parsing."""

    def test_parse_standard_flop(self):
        """Test parsing standard flop format."""
        board = "Ks Qs Js"
        parsed = parse_board(board)
        assert parsed == ["Ks", "Qs", "Js"]

    def test_parse_compact_flop(self):
        """Test parsing compact flop format."""
        board = "KsQsJs"
        parsed = parse_board(board)
        assert parsed == ["Ks", "Qs", "Js"]

    def test_parse_standard_river(self):
        """Test parsing standard river format."""
        board = "Ks Qs Js Ts 9s"
        parsed = parse_board(board)
        assert parsed == ["Ks", "Qs", "Js", "Ts", "9s"]

    def test_parse_compact_river(self):
        """Test parsing compact river format."""
        board = "KsQsJsTs9s"
        parsed = parse_board(board)
        assert parsed == ["Ks", "Qs", "Js", "Ts", "9s"]

    def test_parse_mixed_format_raises_error(self):
        """Test that mixed formats raise error."""
        board = "Ks QsJs"  # Partially compact
        with pytest.raises(BoardFormatError):
            parse_board(board)

    def test_parse_invalid_card_length(self):
        """Test that invalid card lengths raise error."""
        board = "K Qs Js"  # Single character K
        with pytest.raises(BoardFormatError):
            parse_board(board)


class TestBoardFormatNormalization:
    """Test board format normalization."""

    def test_normalize_compact_to_standard(self):
        """Test normalizing compact format to standard."""
        board = "KsQsJs"
        normalized = normalize_board_format(board)
        assert normalized == "Ks Qs Js"

    def test_normalize_standard_unchanged(self):
        """Test that standard format remains unchanged."""
        board = "Ks Qs Js"
        normalized = normalize_board_format(board)
        assert normalized == "Ks Qs Js"

    def test_normalize_river(self):
        """Test normalizing river format."""
        board = "KsQsJsTs9s"
        normalized = normalize_board_format(board)
        assert normalized == "Ks Qs Js Ts 9s"

    def test_normalize_preserves_case(self):
        """Test that normalization preserves case."""
        board = "AsKdQc"
        normalized = normalize_board_format(board)
        assert normalized == "As Kd Qc"

    def test_normalize_strips_extra_whitespace(self):
        """Test that extra whitespace is stripped."""
        board = "  Ks  Qs  Js  "
        normalized = normalize_board_format(board)
        assert normalized == "Ks Qs Js"


class TestBoardFormatValidator:
    """Test BoardFormatValidator class."""

    def test_validator_initialization(self):
        """Test validator can be initialized."""
        validator = BoardFormatValidator()
        assert validator is not None

    def test_validator_validate_method(self):
        """Test validator validate method."""
        validator = BoardFormatValidator()
        assert validator.validate("Ks Qs Js") is True
        assert validator.validate("invalid") is False

    def test_validator_parse_method(self):
        """Test validator parse method."""
        validator = BoardFormatValidator()
        parsed = validator.parse("KsQsJs")
        assert parsed == ["Ks", "Qs", "Js"]

    def test_validator_normalize_method(self):
        """Test validator normalize method."""
        validator = BoardFormatValidator()
        normalized = validator.normalize("KsQsJs")
        assert normalized == "Ks Qs Js"

    def test_validator_get_card_count(self):
        """Test validator can count cards."""
        validator = BoardFormatValidator()
        assert validator.get_card_count("Ks Qs Js") == 3
        assert validator.get_card_count("Ks Qs Js Ts 9s") == 5

    def test_validator_is_flop(self):
        """Test validator can identify flop."""
        validator = BoardFormatValidator()
        assert validator.is_flop("Ks Qs Js") is True
        assert validator.is_flop("Ks Qs Js Ts") is False

    def test_validator_is_turn(self):
        """Test validator can identify turn."""
        validator = BoardFormatValidator()
        assert validator.is_turn("Ks Qs Js Ts") is True
        assert validator.is_turn("Ks Qs Js") is False

    def test_validator_is_river(self):
        """Test validator can identify river."""
        validator = BoardFormatValidator()
        assert validator.is_river("Ks Qs Js Ts 9s") is True
        assert validator.is_river("Ks Qs Js Ts") is False


class TestBoardFormatEdgeCases:
    """Test edge cases and error handling."""

    def test_lowercase_cards_accepted(self):
        """Test that lowercase cards are accepted."""
        board = "ks qs js"
        assert validate_board_format(board) is True

    def test_mixed_case_cards_accepted(self):
        """Test that mixed case cards are accepted."""
        board = "Ks qs Js"
        assert validate_board_format(board) is True

    def test_numeric_ranks_accepted(self):
        """Test that numeric ranks (2-9) are accepted."""
        board = "2s 3h 4d 5c 6s"
        assert validate_board_format(board) is True

    def test_ten_rank_accepted(self):
        """Test that T/10 rank is accepted."""
        board = "Ts Th Td"
        assert validate_board_format(board) is True

    def test_all_suits_accepted(self):
        """Test all four suits are accepted."""
        board = "As Ah Ad Ac 2s"
        assert validate_board_format(board) is True

    def test_board_with_tabs_rejected(self):
        """Test that tabs are not accepted as separators."""
        board = "Ks\tQs\tJs"
        assert validate_board_format(board) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
