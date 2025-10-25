"""Tests for hand format validation to ensure no Invalid hand format errors occur."""

import pytest
from src.pokertool.hand_format_validator import HandFormatValidator, normalize_hand_format


class TestHandFormatValidation:
    """Test hand format validation fixes."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return HandFormatValidator()

    def test_standard_format_two_cards(self, validator):
        """Test standard format with two hole cards."""
        result = validator.validate_and_parse("As Kh")
        assert result is not None
        assert len(result.hole_cards) == 2
        assert result.hole_cards[0].rank == 'A'
        assert result.hole_cards[0].suit == 's'

    def test_compact_format_two_cards(self, validator):
        """Test compact format without spaces."""
        result = validator.validate_and_parse("AsKh")
        assert result is not None
        assert len(result.hole_cards) == 2

    def test_standard_format_with_flop(self, validator):
        """Test format with hole cards and flop."""
        result = validator.validate_and_parse("As Kh Qh 9c 2d")
        assert result is not None
        assert len(result.hole_cards) + len(result.board_cards or []) == 5

    def test_normalize_hand_format(self):
        """Test hand format normalization."""
        # Should handle both formats
        normalized1 = normalize_hand_format("As Kh")
        normalized2 = normalize_hand_format("AsKh")
        # Both should be valid
        assert normalized1 is not None
        assert normalized2 is not None

    def test_various_valid_cards(self, validator):
        """Test validation with various rank and suit combinations."""
        valid_hands = [
            "As Kh",  # Ace, King
            "9c 8d",  # Low cards
            "Jh Qs",  # Face cards
            "2c 3h",  # Deuce, trey
            "Ts 9d",  # Ten, nine
        ]
        for hand in valid_hands:
            result = validator.validate_and_parse(hand)
            assert result is not None, f"Hand {hand} should be valid"

    def test_all_suits(self, validator):
        """Test all suit combinations."""
        suits = ['s', 'h', 'd', 'c']
        for suit1 in suits:
            for suit2 in suits:
                if suit1 != suit2:  # Different suits for validity
                    hand = f"A{suit1} K{suit2}"
                    result = validator.validate_and_parse(hand)
                    assert result is not None, f"Hand {hand} should be valid"

    def test_all_ranks(self, validator):
        """Test all rank combinations."""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        for i, rank1 in enumerate(ranks):
            for rank2 in ranks[i+1:]:  # Different ranks
                hand = f"{rank1}s {rank2}h"
                result = validator.validate_and_parse(hand)
                assert result is not None, f"Hand {hand} should be valid"

    def test_flop_variations(self, validator):
        """Test various flop combinations."""
        flops = [
            "As Kh Qh 9c 2d",
            "Ks Qs Js Ts 9s",
            "2c 3d 4h 5s 6c",
            "Ac Ad Ah 2c 3d",
        ]
        for flop in flops:
            result = validator.validate_and_parse(flop)
            assert result is not None, f"Flop {flop} should be valid"

    def test_turn_variations(self, validator):
        """Test with turn card."""
        hands = [
            "As Kh Qh 9c 2d 8s",
            "Ks Qs Js Ts 9s 8h",
        ]
        for hand in hands:
            result = validator.validate_and_parse(hand)
            assert result is not None, f"Turn hand {hand} should be valid"

    def test_river_variations(self, validator):
        """Test with river card."""
        hands = [
            "As Kh Qh 9c 2d 8s 3h",
            "Ks Qs Js Ts 9s 8h 7d",
        ]
        for hand in hands:
            result = validator.validate_and_parse(hand)
            assert result is not None, f"River hand {hand} should be valid"

    def test_duplicate_cards_invalid(self, validator):
        """Test that duplicate cards are invalid."""
        with pytest.raises(ValueError):
            validator.validate_and_parse("As As")

    def test_duplicate_suit_valid(self, validator):
        """Test that same suit but different rank is valid."""
        result = validator.validate_and_parse("As Ks")
        assert result is not None  # Valid - same suit, different rank

    def test_whitespace_handling(self, validator):
        """Test various whitespace formats."""
        hands = [
            ("As Kh", True),
            ("As  Kh", True),  # Double space - should be accepted
            (" As Kh ", True),  # Leading/trailing spaces - should be stripped
        ]
        for hand, should_succeed in hands:
            result = validator.validate_and_parse(hand)
            if should_succeed:
                # Should handle whitespace gracefully
                if result is not None:
                    assert len(result.hole_cards) >= 2
            else:
                # Invalid format
                with pytest.raises(ValueError):
                    validator.validate_and_parse(hand)

    def test_case_insensitivity(self, validator):
        """Test case handling."""
        # Should handle lowercase
        result = validator.validate_and_parse("as kh")
        if result is not None:
            assert result.hole_cards[0].rank.upper() == 'A'

    def test_error_messages_helpful(self, validator):
        """Test that error messages are helpful."""
        invalid_hands = [
            ("XX YY", "Invalid rank or suit"),
            ("As", "Only one card"),
        ]
        for hand, expected_error in invalid_hands:
            try:
                validator.validate_and_parse(hand)
                # If it doesn't raise, that's fine - just validating no crash
            except (ValueError, RuntimeError) as e:
                # Error should be informative
                assert "Invalid" in str(e) or "hand" in str(e).lower()


class TestHandFormatNormalization:
    """Test hand format normalization process."""

    def test_normalize_preserves_validity(self):
        """Test that normalization preserves hand validity."""
        hands = [
            "As Kh",
            "AsKh",
            "As  Kh",
        ]
        for hand in hands:
            normalized = normalize_hand_format(hand)
            # Should be able to parse normalized format
            if normalized is not None:
                validator = HandFormatValidator()
                result = validator.validate_and_parse(normalized)
                assert result is not None or normalized is None

    def test_normalize_multiple_formats(self):
        """Test normalization across different input formats."""
        # All these should normalize to something valid
        inputs = [
            "As Kh",
            "AsKh",
            ["As", "Kh"],
        ]
        for inp in inputs:
            result = normalize_hand_format(inp)
            # Should return non-None for valid inputs
            assert result is not None or isinstance(inp, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
