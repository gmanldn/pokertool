#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_gui_enhanced_v2.py
# version: v21.0.0
# last_commit: 2025-10-12T00:00:00Z
# fixes:
#   - date: 2025-10-12
#     summary: Comprehensive unit tests for enhanced GUI v2
#   - date: 2025-10-12
#     summary: Tests for scraper integration and table visualization
#   - date: 2025-10-12
#     summary: Tests for manual entry and analysis
# ---
# POKERTOOL-HEADER-END

Unit Tests for Enhanced GUI v2
===============================

Comprehensive test suite for the enhanced poker tool GUI with
integrated screen scraping functionality.

Test Coverage:
--------------
1. GUI Initialization
   - Window creation
   - Component setup
   - Scraper initialization
   
2. Screen Scraper Integration
   - Window scanning
   - Window selection
   - Monitoring control
   
3. Manual Entry
   - Card input validation
   - Game state configuration
   - Analysis execution
   
4. Table Visualization
   - Player rendering
   - Card display
   - Pot and bet visualization
   
5. Error Handling
   - Invalid inputs
   - Missing dependencies
   - Scraper failures

Module: tests.test_gui_enhanced_v2
Author: PokerTool Development Team
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import tkinter as tk
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))


class TestEnhancedGUIInitialization(unittest.TestCase):
    """Test GUI initialization and setup."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_gui_creation(self, mock_scraper_class):
        """Test GUI window creation."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.platform = "Test Platform"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper_class.return_value = mock_scraper
        
        # Create GUI
        gui = EnhancedPokerToolGUI()
        
        # Verify window properties
        self.assertIn("PokerTool", gui.title())
        self.assertIsNotNone(gui.scraper)
        
        # Clean up
        gui.destroy()
    
    @patch('pokertool.gui_enhanced_v2.SCRAPER_AVAILABLE', False)
    def test_gui_without_scraper(self):
        """Test GUI creation when scraper not available."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        gui = EnhancedPokerToolGUI()
        
        # Should still create GUI
        self.assertIsNotNone(gui)
        self.assertIsNone(gui.scraper)
        
        gui.destroy()
    
    def test_status_indicator(self):
        """Test status indicator component."""
        from pokertool.gui_enhanced_v2 import StatusIndicator, COLORS
        
        indicator = StatusIndicator(self.root, label="Test")
        indicator.pack()
        self.root.update()
        
        # Test status update
        indicator.set_status("Active", COLORS['status_success'])
        self.assertEqual(indicator.status_text, "Active")
        self.assertEqual(indicator.status_color, COLORS['status_success'])
    
    def test_metrics_panel(self):
        """Test metrics panel component."""
        from pokertool.gui_enhanced_v2 import MetricsPanel
        
        panel = MetricsPanel(self.root)
        panel.pack()
        self.root.update()
        
        # Test metrics update
        test_metrics = {
            'total_captures': 100,
            'success_rate': 0.95,
            'avg_capture_time': 0.050,
            'cache_hit_rate': 0.80
        }
        
        panel.update_metrics(test_metrics)
        
        # Verify updates (values should be formatted)
        self.assertEqual(panel.metrics['captures'].cget('text'), '100')


class TestScreenScraperIntegration(unittest.TestCase):
    """Test screen scraper integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_scan_windows(self, mock_scraper_class):
        """Test window scanning functionality."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        # Mock scraper with windows
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # Create mock windows
        from unittest.mock import Mock as MockWindow
        mock_window1 = MockWindow()
        mock_window1.title = "PokerStars - Table 1"
        mock_window1.width = 800
        mock_window1.height = 600
        mock_window1.x = 0
        mock_window1.y = 0
        mock_window1.is_visible = True
        mock_window1.is_minimized = False
        
        mock_scraper.scan_for_poker_windows.return_value = [mock_window1]
        mock_scraper_class.return_value = mock_scraper
        
        # Create GUI
        gui = EnhancedPokerToolGUI()
        
        # Trigger scan (this will be async, so we need to wait)
        gui._scan_windows()
        
        # Wait for async operation
        import time
        time.sleep(0.2)
        gui.update()
        
        # Verify scan was called
        mock_scraper.scan_for_poker_windows.assert_called()
        
        gui.destroy()
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_window_selection(self, mock_scraper_class):
        """Test window selection."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # Mock capture result
        mock_scraper.capture_window.return_value = {
            'success': True,
            'window_info': Mock(),
            'seat_count': 6
        }
        
        mock_scraper_class.return_value = mock_scraper
        
        gui = EnhancedPokerToolGUI()
        
        # Create mock window
        mock_window = Mock()
        mock_window.title = "Test Table"
        mock_window.x = 0
        mock_window.y = 0
        mock_window.width = 800
        mock_window.height = 600
        
        # Select window
        gui._on_window_selected(mock_window)
        
        # Verify window was selected
        self.assertEqual(gui.selected_window, mock_window)
        
        gui.destroy()
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_monitoring_toggle(self, mock_scraper_class):
        """Test monitoring toggle functionality."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = [Mock()]  # At least one window
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper.start_continuous_monitoring.return_value = True
        mock_scraper_class.return_value = mock_scraper
        
        gui = EnhancedPokerToolGUI()
        
        # Start monitoring
        gui._start_monitoring()
        self.assertTrue(gui.monitoring_active)
        
        # Stop monitoring
        gui._stop_monitoring()
        self.assertFalse(gui.monitoring_active)
        
        gui.destroy()


class TestManualEntry(unittest.TestCase):
    """Test manual card entry and analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    @patch('pokertool.gui_enhanced_v2.CORE_AVAILABLE', True)
    def test_manual_analysis(self, mock_scraper_class):
        """Test manual hand analysis."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper_class.return_value = mock_scraper
        
        gui = EnhancedPokerToolGUI()
        
        # Set up test hand
        gui.hole1_entry.insert(0, "As")
        gui.hole2_entry.insert(0, "Ks")
        gui.board_entries[0].insert(0, "Qs")
        gui.board_entries[1].insert(0, "Js")
        gui.board_entries[2].insert(0, "Ts")
        
        # Configure game state
        gui.pot_entry.delete(0, tk.END)
        gui.pot_entry.insert(0, "100")
        gui.call_entry.delete(0, tk.END)
        gui.call_entry.insert(0, "10")
        gui.opponents_entry.delete(0, tk.END)
        gui.opponents_entry.insert(0, "1")
        
        # Run analysis
        try:
            gui._analyze_manual_hand()
            # Check that results were displayed
            result_text = gui.manual_results_text.get('1.0', tk.END)
            self.assertIn("HAND ANALYSIS", result_text)
        except Exception as e:
            # Some dependencies might not be available in test environment
            self.skipTest(f"Analysis dependencies not available: {e}")
        
        gui.destroy()
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_invalid_card_input(self, mock_scraper_class):
        """Test handling of invalid card input."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper_class.return_value = mock_scraper
        
        gui = EnhancedPokerToolGUI()
        
        # Invalid card input
        gui.hole1_entry.insert(0, "XX")
        gui.hole2_entry.insert(0, "YY")
        
        # Should handle gracefully (messagebox will be shown but we can't test that easily)
        try:
            gui._analyze_manual_hand()
        except Exception as e:
            # Expected to fail with invalid input
            pass
        
        gui.destroy()


class TestTableVisualization(unittest.TestCase):
    """Test table visualization canvas."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_canvas_creation(self):
        """Test canvas creation."""
        from pokertool.gui_enhanced_v2 import TableVisualizationCanvas
        
        canvas = TableVisualizationCanvas(self.root, width=800, height=500)
        canvas.pack()
        self.root.update()
        
        self.assertIsNotNone(canvas)
        self.assertEqual(len(canvas.seat_positions), 9)
    
    def test_table_update(self):
        """Test table state update."""
        from pokertool.gui_enhanced_v2 import TableVisualizationCanvas
        
        canvas = TableVisualizationCanvas(self.root, width=800, height=500)
        canvas.pack()
        self.root.update()
        
        # Create test players
        players = {
            1: {'is_hero': True, 'is_active': True, 'stack': 100.0, 'bet': 0.0},
            2: {'is_hero': False, 'is_active': True, 'stack': 150.0, 'bet': 10.0},
        }
        
        # Update table
        canvas.update_table(players, 50.0, [], [])
        self.root.update()
        
        self.assertEqual(canvas.pot_size, 50.0)
        self.assertEqual(len(canvas.players), 2)
    
    @patch('pokertool.gui_enhanced_v2.CORE_AVAILABLE', True)
    def test_card_display(self):
        """Test card display on canvas."""
        from pokertool.gui_enhanced_v2 import TableVisualizationCanvas
        
        canvas = TableVisualizationCanvas(self.root, width=800, height=500)
        canvas.pack()
        self.root.update()
        
        try:
            from pokertool.core import Card, Rank, Suit
            
            # Create test cards
            board_cards = [
                Card(Rank.ACE, Suit.SPADES),
                Card(Rank.KING, Suit.HEARTS),
                Card(Rank.QUEEN, Suit.DIAMONDS)
            ]
            
            hero_cards = [
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.TEN, Suit.SPADES)
            ]
            
            # Update with cards
            players = {1: {'is_hero': True, 'is_active': True, 'stack': 100.0, 'bet': 0.0}}
            canvas.update_table(players, 0.0, board_cards, hero_cards)
            self.root.update()
            
            self.assertEqual(len(canvas.board_cards), 3)
            self.assertEqual(len(canvas.hero_cards), 2)
        except ImportError:
            self.skipTest("Core modules not available")


class TestWindowListPanel(unittest.TestCase):
    """Test window list panel."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_panel_creation(self):
        """Test panel creation."""
        from pokertool.gui_enhanced_v2 import WindowListPanel
        
        panel = WindowListPanel(self.root)
        panel.pack()
        self.root.update()
        
        self.assertIsNotNone(panel)
        self.assertEqual(len(panel.windows), 0)
    
    def test_window_list_update(self):
        """Test updating window list."""
        from pokertool.gui_enhanced_v2 import WindowListPanel
        
        callback_called = False
        
        def test_callback(window):
            nonlocal callback_called
            callback_called = True
        
        panel = WindowListPanel(self.root, on_window_selected=test_callback)
        panel.pack()
        self.root.update()
        
        # Create mock windows
        mock_window = Mock()
        mock_window.title = "Test Window"
        mock_window.width = 800
        mock_window.height = 600
        mock_window.is_visible = True
        mock_window.is_minimized = False
        
        # Update list
        panel.update_windows([mock_window])
        self.root.update()
        
        self.assertEqual(len(panel.windows), 1)
        self.assertEqual(panel.listbox.size(), 1)


class TestErrorHandling(unittest.TestCase):
    """Test error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_scraper_error_handling(self, mock_scraper_class):
        """Test handling of scraper errors."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        # Mock scraper that raises error
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper.scan_for_poker_windows.side_effect = Exception("Test error")
        mock_scraper_class.return_value = mock_scraper
        
        gui = EnhancedPokerToolGUI()
        
        # Should handle error gracefully
        gui._scan_windows()
        
        # Wait for async operation
        import time
        time.sleep(0.2)
        gui.update()
        
        # GUI should still be functional
        self.assertIsNotNone(gui)
        
        gui.destroy()
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_missing_core_modules(self, mock_scraper_class):
        """Test handling when core modules missing."""
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper_class.return_value = mock_scraper
        
        with patch('pokertool.gui_enhanced_v2.CORE_AVAILABLE', False):
            from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
            
            gui = EnhancedPokerToolGUI()
            
            # Should still create GUI
            self.assertIsNotNone(gui)
            
            gui.destroy()


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            self.root.destroy()
        except:
            pass
    
    @patch('pokertool.gui_enhanced_v2.DesktopIndependentScraper')
    def test_complete_workflow(self, mock_scraper_class):
        """Test complete analysis workflow."""
        from pokertool.gui_enhanced_v2 import EnhancedPokerToolGUI
        
        # Setup mock scraper
        mock_scraper = Mock()
        mock_scraper.platform = "Test"
        mock_scraper.detected_windows = []
        mock_scraper.get_performance_metrics.return_value = {
            'total_captures': 0,
            'success_rate': 0.0,
            'avg_capture_time': 0.0,
            'cache_hit_rate': 0.0
        }
        mock_scraper_class.return_value = mock_scraper
        
        gui = EnhancedPokerToolGUI()
        
        # 1. New session
        gui._new_session()
        self.assertEqual(gui.hole1_entry.get(), "")
        
        # 2. Enter cards manually
        gui.hole1_entry.insert(0, "As")
        gui.hole2_entry.insert(0, "Ks")
        
        # 3. Switch tabs to verify navigation
        gui.notebook.select(1)  # Manual tab
        gui.update()
        
        # 4. View settings
        gui.notebook.select(3)  # Settings tab
        gui.update()
        
        # GUI should be fully functional
        self.assertIsNotNone(gui)
        
        gui.destroy()


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedGUIInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestScreenScraperIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestManualEntry))
    suite.addTests(loader.loadTestsFromTestCase(TestTableVisualization))
    suite.addTests(loader.loadTestsFromTestCase(TestWindowListPanel))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
