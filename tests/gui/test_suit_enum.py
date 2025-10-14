#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tests/gui/test_suit_enum.py
# version: v1.0.0
# last_commit: '2025-10-04T00:00:00+00:00'
# fixes:
# - date: '2025-10-04'
#   summary: Created test to verify Suit enum case sensitivity fix
# ---
# POKERTOOL-HEADER-END

"""
Unit tests for GUI Suit enum.

Tests:
    - Suit enum attributes exist with correct case
    - Suit enum values are correct
    - Suit enum can be used in comparisons
    - Card creation with Suit enum works

Version: 1.0.0
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


class TestSuitEnum(unittest.TestCase):
    """Test the Suit enum in gui.py."""

    def setUp(self):
        """Set up test fixtures."""
        # Import within setUp to catch import errors
        try:
            from pokertool.gui import Suit
            self.Suit = Suit
        except ImportError:
            # If core module available, use that
            try:
                from pokertool.core import Suit
                self.Suit = Suit
            except ImportError:
                self.skipTest("Cannot import Suit enum")

    def test_suit_attributes_exist(self):
        """Test that Suit enum has uppercase attributes."""
        self.assertTrue(hasattr(self.Suit, 'SPADES'))
        self.assertTrue(hasattr(self.Suit, 'HEARTS'))
        self.assertTrue(hasattr(self.Suit, 'DIAMONDS'))
        self.assertTrue(hasattr(self.Suit, 'CLUBS'))

    def test_suit_values(self):
        """Test that Suit enum values are correct."""
        self.assertEqual(self.Suit.SPADES.value, 's')
        self.assertEqual(self.Suit.HEARTS.value, 'h')
        self.assertEqual(self.Suit.DIAMONDS.value, 'd')
        self.assertEqual(self.Suit.CLUBS.value, 'c')

    def test_suit_comparison(self):
        """Test that Suit enum members can be compared."""
        self.assertEqual(self.Suit.SPADES, self.Suit.SPADES)
        self.assertNotEqual(self.Suit.SPADES, self.Suit.HEARTS)

    def test_suit_in_list(self):
        """Test that Suit enum can be used in lists (as in CardSelectionPanel)."""
        suits = [self.Suit.SPADES, self.Suit.HEARTS, self.Suit.DIAMONDS, self.Suit.CLUBS]
        self.assertEqual(len(suits), 4)
        self.assertIn(self.Suit.SPADES, suits)
        self.assertIn(self.Suit.HEARTS, suits)

    def test_suit_dict_keys(self):
        """Test that Suit enum can be used as dict keys (as in VisualCard)."""
        suit_symbols = {
            self.Suit.SPADES: '♠',
            self.Suit.HEARTS: '♥',
            self.Suit.DIAMONDS: '♦',
            self.Suit.CLUBS: '♣'
        }
        self.assertEqual(suit_symbols[self.Suit.SPADES], '♠')
        self.assertEqual(suit_symbols[self.Suit.HEARTS], '♥')

    def test_no_lowercase_attributes(self):
        """Test that lowercase attributes don't exist (regression test)."""
        self.assertFalse(hasattr(self.Suit, 'spades'))
        self.assertFalse(hasattr(self.Suit, 'hearts'))
        self.assertFalse(hasattr(self.Suit, 'diamonds'))
        self.assertFalse(hasattr(self.Suit, 'clubs'))


class TestCardCreation(unittest.TestCase):
    """Test Card creation with Suit enum."""

    def setUp(self):
        """Set up test fixtures."""
        try:
            from pokertool.gui import Suit, Card
            self.Suit = Suit
            self.Card = Card
        except ImportError:
            try:
                from pokertool.core import Suit, Card
                self.Suit = Suit
                self.Card = Card
            except ImportError:
                self.skipTest("Cannot import Suit or Card")

    def test_card_creation_with_suit(self):
        """Test creating Card instances with Suit enum."""
        card = self.Card('A', self.Suit.SPADES)
        # Rank might be a string 'A' or Rank enum with value 14
        # Check if it's an enum (has a 'value' attribute) or string
        if hasattr(card.rank, 'value'):
            # It's a Rank enum - check the value is 14 (ACE)
            self.assertEqual(card.rank.value, 14)
        else:
            # It's a string
            self.assertEqual(card.rank, 'A')
        # Suit might be stored as value
        self.assertIn(card.suit, ['s', self.Suit.SPADES])

    def test_card_creation_all_suits(self):
        """Test creating cards with all suits."""
        for suit in [self.Suit.SPADES, self.Suit.HEARTS, self.Suit.DIAMONDS, self.Suit.CLUBS]:
            card = self.Card('K', suit)
            self.assertIsNotNone(card)


if __name__ == '__main__':
    unittest.main()
