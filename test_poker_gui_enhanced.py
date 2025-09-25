# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_poker_gui_enhanced.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
__version__ = '21'

"""
Unit tests for Enhanced Poker GUI
Tests visual card selection, table visualization, and user interactions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tkinter as tk
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the poker modules if not available
try:
    from poker_modules import Card, Suit, Position
except ImportError:
    from enum import Enum

    class Suit(Enum):
        """Suit enumeration for card suits."""
        spades = 's'
        hearts = 'h'
        diamonds = 'd'
        clubs = 'c'

    class Position(Enum):
        """Position enumeration for poker positions."""
        UNDER_THE_GUN = 'UTG'
        BUTTON = 'BTN'
        SMALL_BLIND = 'SB'
        BIG_BLIND = 'BB'

    class Card:
        """Card class for representing playing cards."""
        def __init__(self, rank, suit):
            self.rank = rank
            self.suit = suit

# ═══════════════════════════════════════════════════════════════════════════════
# TEST VISUAL CARD COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════

class TestVisualCard(unittest.TestCase):
    """Test the VisualCard component."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = None

    def tearDown(self):
        """Clean up after tests."""
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass

    @patch('tkinter.Tk')
    def test_visual_card_creation(self, mock_tk):
        """Test VisualCard creation and initialization."""
        try:
            from poker_gui_enhanced import VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        callback = Mock()

        card = VisualCard(mock_parent, 'A', Suit.spades, callback)

        self.assertEqual(card.rank, 'A')
        self.assertEqual(card.suit, Suit.spades)
        self.assertEqual(card.callback, callback)
        self.assertFalse(card.selected)

    @patch('tkinter.Tk')
    def test_visual_card_selection(self, mock_tk):
        """Test card selection functionality."""
        try:
            from poker_gui_enhanced import VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        callback = Mock()

        card = VisualCard(mock_parent, 'K', Suit.hearts, callback)

        # Test selection
        card.set_selected(True)
        self.assertTrue(card.selected)

        # Test deselection
        card.set_selected(False)
        self.assertFalse(card.selected)

    @patch('tkinter.Tk')
    def test_visual_card_click_callback(self, mock_tk):
        """Test card click callback."""
        try:
            from poker_gui_enhanced import VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        callback = Mock()

        card = VisualCard(mock_parent, 'Q', Suit.diamonds, callback)

        # Simulate click
        mock_event = Mock()
        card._on_click(mock_event)

        callback.assert_called_once_with(card)

    @patch('tkinter.Tk')
    def test_visual_card_hover_effects(self, mock_tk):
        """Test card hover effects."""
        try:
            from poker_gui_enhanced import VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        card = VisualCard(mock_parent, 'J', Suit.clubs, None)

        # Mock the configure method
        card.configure = Mock()
        card.label = Mock()
        card.label.configure = Mock()

        # Test mouse enter
        mock_event = Mock()
        card._on_enter(mock_event)
        card.configure.assert_called()

        # Test mouse leave
        card._on_leave(mock_event)
        self.assertEqual(card.configure.call_count, 2)

# ═══════════════════════════════════════════════════════════════════════════════
# TEST CARD SELECTION PANEL
# ═══════════════════════════════════════════════════════════════════════════════

class TestCardSelectionPanel(unittest.TestCase):
    """Test the CardSelectionPanel component."""

    @patch('tkinter.Frame')
    @patch('tkinter.Label')
    def test_panel_initialization(self, mock_label, mock_frame):
        """Test panel initialization."""
        try:
            from poker_gui_enhanced import CardSelectionPanel
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        callback = Mock()

        panel = CardSelectionPanel(mock_parent, callback)

        self.assertEqual(panel.on_card_selected, callback)
        self.assertIsInstance(panel.cards, dict)
        self.assertIsInstance(panel.selected_cards, list)
        self.assertEqual(len(panel.selected_cards), 0)

    @patch('tkinter.Frame')
    @patch('poker_gui_enhanced.VisualCard')
    def test_card_grid_creation(self, mock_visual_card, mock_frame):
        """Test that all 52 cards are created."""
        try:
            from poker_gui_enhanced import CardSelectionPanel
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        panel = CardSelectionPanel(mock_parent, None)

        # Should create 52 cards (13 ranks * 4 suits)
        expected_calls = 52
        self.assertEqual(mock_visual_card.call_count, expected_calls)

    @patch('tkinter.Frame')
    def test_card_selection_limit(self, mock_frame):
        """Test that card selection is limited to 7 cards."""
        try:
            from poker_gui_enhanced import CardSelectionPanel, VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        panel = CardSelectionPanel(mock_parent, None)

        # Create mock cards
        for i in range(8):
            mock_card = Mock(spec=VisualCard)
            mock_card.selected = False
            mock_card.rank = str(i)
            mock_card.suit = Suit.spades

            # Try to select 8 cards
            if i < 7:
                panel._on_card_click(mock_card)
                self.assertEqual(len(panel.selected_cards), i + 1)
            else:
                # 8th card should trigger warning
                with patch('tkinter.messagebox.showwarning') as mock_warning:
                    panel._on_card_click(mock_card)
                    mock_warning.assert_called_once()
                    self.assertEqual(len(panel.selected_cards), 7)

    @patch('tkinter.Frame')
    def test_clear_selection(self, mock_frame):
        """Test clearing selected cards."""
        try:
            from poker_gui_enhanced import CardSelectionPanel, VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        panel = CardSelectionPanel(mock_parent, None)

        # Add some mock cards
        for i in range(3):
            mock_card = Mock(spec=VisualCard)
            mock_card.set_selected = Mock()
            panel.selected_cards.append(mock_card)

        # Clear selection
        panel.clear_selection()

        # Check all cards were deselected
        for card in [panel.selected_cards[i] for i in range(3)]:
            card.set_selected.assert_called_with(False)

        self.assertEqual(len(panel.selected_cards), 0)

# ═══════════════════════════════════════════════════════════════════════════════
# TEST TABLE VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestTableVisualization(unittest.TestCase):
    """Test the TableVisualization component."""

    @patch('tkinter.Canvas')
    def test_table_initialization(self, mock_canvas):
        """Test table visualization initialization."""
        try:
            from poker_gui_enhanced import TableVisualization
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        table = TableVisualization(mock_parent, width=800, height=500)

        self.assertIsInstance(table.players, dict)
        self.assertEqual(table.pot_size, 0.0)
        self.assertIsInstance(table.board_cards, list)
        self.assertEqual(len(table.seat_positions), 9)

    @patch('tkinter.Canvas')
    def test_player_drawing(self, mock_canvas):
        """Test player drawing functionality."""
        try:
            from poker_gui_enhanced import TableVisualization, PlayerInfo
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        mock_parent = Mock()
        table = TableVisualization(mock_parent)

        # Mock canvas methods
        table.create_oval = Mock()
        table.create_text = Mock()
        table.winfo_width = Mock(return_value=800)
        table.winfo_height = Mock(return_value=500)

        # Create test player
        player = PlayerInfo(
            seat=1,
            is_active=True,
            stack=100.0,
            bet=10.0,
            is_hero=True
        )

        # Draw player
        table._draw_player(1, player, 800, 500)

        # Should create player circle and text
        table.create_oval.assert_called()
        table.create_text.assert_called()

# ═══════════════════════════════════════════════════════════════════════════════
# TEST MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnhancedPokerAssistant(unittest.TestCase):
    """Test the main application."""

    @patch('tkinter.Tk')
    @patch('poker_gui_enhanced.TableVisualization')
    @patch('poker_gui_enhanced.CardSelectionPanel')
    def test_app_initialization(self, mock_card_panel, mock_table, mock_tk):
        """Test application initialization."""
        try:
            from poker_gui_enhanced import EnhancedPokerAssistant
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        app = EnhancedPokerAssistant()

        self.assertIsInstance(app.hole_cards, list)
        self.assertIsInstance(app.board_cards, list)
        self.assertIsInstance(app.players, dict)
        self.assertEqual(len(app.players), 9)

    @patch('tkinter.Tk')
    def test_player_initialization(self, mock_tk):
        """Test default player configuration."""
        try:
            from poker_gui_enhanced import EnhancedPokerAssistant
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        app = EnhancedPokerAssistant()
        players = app._init_players()

        # Check all 9 seats
        self.assertEqual(len(players), 9)

        # Check default active players (seats 1-6)
        for seat in range(1, 7):
            self.assertTrue(players[seat].is_active)

        for seat in range(7, 10):
            self.assertFalse(players[seat].is_active)

        # Check hero is seat 1
        self.assertTrue(players[1].is_hero)

        # Check dealer is seat 3
        self.assertTrue(players[3].is_dealer)

# ═══════════════════════════════════════════════════════════════════════════════
# TEST INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestGUIIntegration(unittest.TestCase):
    """Test GUI component integration."""

    @patch('tkinter.Tk')
    def test_card_selection_to_analysis_flow(self, mock_tk):
        """Test flow from card selection to analysis."""
        try:
            from poker_gui_enhanced import EnhancedPokerAssistant, VisualCard
        except ImportError:
            self.skipTest("poker_gui_enhanced module not available")

        app = EnhancedPokerAssistant()

        # Mock components
        app.card_selector = Mock()
        app.table_viz = Mock()
        app.analysis_text = Mock()

        # Simulate card selection
        mock_card1 = Mock(spec=VisualCard, rank='A', suit=Suit.spades)
        mock_card2 = Mock(spec=VisualCard, rank='K', suit=Suit.hearts)

        app.card_selector.get_selected_cards = Mock(
            return_value=[('A', Suit.spades), ('K', Suit.hearts)]
        )

        # Trigger card selection callback
        app._on_card_selected(mock_card1)

        # Check cards were assigned
        self.assertEqual(len(app.hole_cards), 2 if len(app.selected_cards) >= 2 else len(app.selected_cards))

# ═══════════════════════════════════════════════════════════════════════════════
# TEST SUITE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVisualCard))
    suite.addTests(loader.loadTestsFromTestCase(TestCardSelectionPanel))
    suite.addTests(loader.loadTestsFromTestCase(TestTableVisualization))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedPokerAssistant))
    suite.addTests(loader.loadTestsFromTestCase(TestGUIIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print(f'Tests run: {result.testsRun}')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print('=' * 70)

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
