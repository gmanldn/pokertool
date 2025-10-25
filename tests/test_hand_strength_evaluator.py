#!/usr/bin/env python3
"""Tests for Hand Strength Evaluator"""

import pytest
from src.pokertool.hand_strength_evaluator import (
    HandStrengthEvaluator,
    HandRank,
    Card,
    Suit
)


class TestHandStrengthEvaluator:
    """Test suite for HandStrengthEvaluator"""

    def test_initialization(self):
        """Test evaluator initialization"""
        evaluator = HandStrengthEvaluator()
        assert evaluator.evaluations_count == 0

    def test_parse_card(self):
        """Test parsing single card"""
        card = Card.from_string('Ah')
        assert card.rank == 'A'
        assert card.suit == Suit.HEARTS

    def test_parse_multiple_cards(self):
        """Test parsing multiple cards"""
        evaluator = HandStrengthEvaluator()
        cards = evaluator.parse_cards(['Ah', 'Kd', 'Qc', 'Js'])

        assert len(cards) == 4
        assert cards[0].rank == 'A'
        assert cards[1].suit == Suit.DIAMONDS

    def test_royal_flush(self):
        """Test royal flush detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ah', 'Kh'], ['Qh', 'Jh', 'Th', '5c', '2d'])

        assert result.hand_rank == HandRank.ROYAL_FLUSH
        assert "Royal Flush" in result.rank_description

    def test_straight_flush(self):
        """Test straight flush detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['9h', '8h'], ['7h', '6h', '5h', 'Ac', '2d'])

        assert result.hand_rank == HandRank.STRAIGHT_FLUSH
        assert "Straight Flush" in result.rank_description

    def test_four_of_kind(self):
        """Test four of a kind detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['As', 'Ah'], ['Ad', 'Ac', 'Kh', 'Qd', 'Jc'])

        assert result.hand_rank == HandRank.FOUR_OF_KIND
        assert "Four" in result.rank_description
        assert 'A' in result.high_cards

    def test_full_house(self):
        """Test full house detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ks', 'Kh'], ['Kd', 'Qc', 'Qh', '5d', '2c'])

        assert result.hand_rank == HandRank.FULL_HOUSE
        assert "full of" in result.rank_description

    def test_flush(self):
        """Test flush detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ah', 'Kh'], ['Qh', 'Jh', '9h', '5c', '2d'])

        assert result.hand_rank == HandRank.FLUSH
        assert "Flush" in result.rank_description

    def test_straight(self):
        """Test straight detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['9h', '8d'], ['7c', '6s', '5h', 'Ac', '2d'])

        assert result.hand_rank == HandRank.STRAIGHT
        assert "Straight" in result.rank_description

    def test_wheel_straight(self):
        """Test wheel (A-2-3-4-5) straight"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ah', '2d'], ['3c', '4s', '5h', 'Kc', 'Qd'])

        assert result.hand_rank == HandRank.STRAIGHT
        assert '5' in result.high_cards[0]

    def test_three_of_kind(self):
        """Test three of a kind detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ks', 'Kh'], ['Kd', 'Qc', 'Jh', '5d', '2c'])

        assert result.hand_rank == HandRank.THREE_OF_KIND
        assert "Three" in result.rank_description

    def test_two_pair(self):
        """Test two pair detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ks', 'Kh'], ['Qd', 'Qc', 'Jh', '5d', '2c'])

        assert result.hand_rank == HandRank.TWO_PAIR
        assert " and " in result.rank_description

    def test_pair(self):
        """Test pair detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ks', 'Kh'], ['Qd', 'Jc', 'Th', '5d', '2c'])

        assert result.hand_rank == HandRank.PAIR
        assert "Pair" in result.rank_description

    def test_high_card(self):
        """Test high card detection"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ah', 'Kd'], ['Qc', 'Js', '9h', '7d', '2c'])

        assert result.hand_rank == HandRank.HIGH_CARD
        assert "high" in result.rank_description

    def test_preflop_pair(self):
        """Test preflop pocket pair"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ks', 'Kh'])

        assert result.hand_rank == HandRank.PAIR
        assert 'K' in result.high_cards

    def test_preflop_high_card(self):
        """Test preflop high card"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ah', 'Kd'])

        assert result.hand_rank == HandRank.HIGH_CARD
        assert 'A' in result.high_cards

    def test_compare_hands_winner(self):
        """Test hand comparison with clear winner"""
        evaluator = HandStrengthEvaluator()

        # Pair vs high card
        result = evaluator.compare_hands(
            ['Ks', 'Kh'],
            ['Ah', 'Qd'],
            ['Jc', '9s', '7h', '2d', '3c']
        )

        assert result == 1  # Hand 1 (pair) wins

    def test_compare_hands_loser(self):
        """Test hand comparison with clear loser"""
        evaluator = HandStrengthEvaluator()

        # High card vs pair
        result = evaluator.compare_hands(
            ['Ah', 'Qd'],
            ['Ks', 'Kh'],
            ['Jc', '9s', '7h', '2d', '3c']
        )

        assert result == -1  # Hand 2 (pair) wins

    def test_compare_hands_tie(self):
        """Test hand comparison with tie"""
        evaluator = HandStrengthEvaluator()

        # Same high card
        result = evaluator.compare_hands(
            ['Ah', 'Kd'],
            ['As', 'Kc'],
            ['Qh', 'Js', '9d', '7c', '2h']
        )

        assert result == 0  # Tie

    def test_hand_category_premium_pair(self):
        """Test premium pair categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['Ks', 'Kh'])

        assert category == "Premium Pair"

    def test_hand_category_medium_pair(self):
        """Test medium pair categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['9s', '9h'])

        assert category == "Medium Pair"

    def test_hand_category_small_pair(self):
        """Test small pair categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['5s', '5h'])

        assert category == "Small Pair"

    def test_hand_category_premium(self):
        """Test premium hand categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['As', 'Kh'])

        assert category == "Premium"

    def test_hand_category_premium_suited(self):
        """Test premium suited categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['As', 'Ks'])

        assert category == "Premium (suited)"

    def test_hand_category_suited_connectors(self):
        """Test suited connectors categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['8h', '7h'])

        assert category == "Suited Connectors"

    def test_hand_category_broadway(self):
        """Test broadway categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['Jh', 'Td'])

        assert category == "Broadway"

    def test_hand_category_speculative(self):
        """Test speculative hand categorization"""
        evaluator = HandStrengthEvaluator()
        category = evaluator.get_hand_category(['7h', '4d'])

        assert category == "Speculative"

    def test_strength_score_ordering(self):
        """Test that strength scores order hands correctly"""
        evaluator = HandStrengthEvaluator()

        royal = evaluator.evaluate_hand(['Ah', 'Kh'], ['Qh', 'Jh', 'Th', '2c', '3d'])
        straight_flush = evaluator.evaluate_hand(['9h', '8h'], ['7h', '6h', '5h', '2c', '3d'])
        quads = evaluator.evaluate_hand(['As', 'Ah'], ['Ad', 'Ac', 'Kh', 'Qd', 'Jc'])
        full_house = evaluator.evaluate_hand(['Ks', 'Kh'], ['Kd', 'Qc', 'Qh', '5d', '2c'])

        assert royal.strength_score > straight_flush.strength_score
        assert straight_flush.strength_score > quads.strength_score
        assert quads.strength_score > full_house.strength_score

    def test_evaluations_counter(self):
        """Test evaluations counter increments"""
        evaluator = HandStrengthEvaluator()

        evaluator.evaluate_hand(['Ah', 'Kd'])
        evaluator.evaluate_hand(['Qs', 'Jh'])
        evaluator.evaluate_hand(['Ts', '9d'])

        assert evaluator.evaluations_count == 3

    def test_invalid_card_string(self):
        """Test parsing invalid card string"""
        with pytest.raises(ValueError):
            Card.from_string('invalid')

    def test_invalid_suit(self):
        """Test parsing invalid suit"""
        with pytest.raises(ValueError):
            Card.from_string('Ax')

    def test_card_string_representation(self):
        """Test card string conversion"""
        card = Card.from_string('Ah')
        assert str(card) == 'Ah'

    def test_reset_functionality(self):
        """Test reset clears counter"""
        evaluator = HandStrengthEvaluator()

        evaluator.evaluate_hand(['Ah', 'Kd'])
        evaluator.evaluate_hand(['Qs', 'Jh'])

        assert evaluator.evaluations_count == 2

        evaluator.reset()
        assert evaluator.evaluations_count == 0

    def test_flush_beats_straight(self):
        """Test flush beats straight"""
        evaluator = HandStrengthEvaluator()

        flush = evaluator.evaluate_hand(['Ah', 'Kh'], ['Qh', 'Jh', '9h', '5c', '2d'])
        straight = evaluator.evaluate_hand(['9h', '8d'], ['7c', '6s', '5h', 'Ac', '2d'])

        assert flush.strength_score > straight.strength_score

    def test_same_rank_different_kickers(self):
        """Test hands with same rank but different kickers"""
        evaluator = HandStrengthEvaluator()

        pair_a = evaluator.evaluate_hand(['Ks', 'Kh'], ['Ah', 'Qd', 'Jc', '5s', '2h'])
        pair_b = evaluator.evaluate_hand(['Ks', 'Kh'], ['Qh', 'Jd', 'Tc', '5s', '2h'])

        assert pair_a.strength_score > pair_b.strength_score

    def test_higher_pair_wins(self):
        """Test higher pair beats lower pair"""
        evaluator = HandStrengthEvaluator()

        result = evaluator.compare_hands(
            ['As', 'Ah'],
            ['Ks', 'Kh'],
            ['Qd', 'Jc', '9h', '7s', '2d']
        )

        assert result == 1

    def test_broadway_straight(self):
        """Test broadway straight (T-J-Q-K-A)"""
        evaluator = HandStrengthEvaluator()
        result = evaluator.evaluate_hand(['Ah', 'Kd'], ['Qc', 'Js', 'Th', '5d', '2c'])

        assert result.hand_rank == HandRank.STRAIGHT
        assert 'A' in result.high_cards[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
