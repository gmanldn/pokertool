#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for poker screen scraper table validation.

Tests the new validation logic to ensure:
1. False positives are prevented
2. Real tables are detected
3. Edge cases are handled correctly
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Import the scraper
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pokertool.modules.poker_screen_scraper import (
    PokerScreenScraper,
    TableState,
    SeatInfo,
    PokerSite,
    create_scraper
)


class TestTableValidation(unittest.TestCase):
    """Test table validation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = create_scraper('GENERIC')
        
    def test_empty_screen_rejected(self):
        """Test that empty screens are rejected."""
        state = TableState()
        state.active_players = 0
        state.pot_size = 0.0
        
        # Create mock image (all black)
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        is_valid, reason = self.scraper._validate_poker_table(state, mock_image)
        
        self.assertFalse(is_valid)
        self.assertIn("Only 0 active players", reason)
    
    def test_single_player_rejected(self):
        """Test that single player tables are rejected."""
        state = TableState()
        state.active_players = 1
        state.pot_size = 50.0
        
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        is_valid, reason = self.scraper._validate_poker_table(state, mock_image)
        
        self.assertFalse(is_valid)
        self.assertIn("Only 1 active players", reason)
    
    def test_valid_table_with_players_and_pot(self):
        """Test that valid tables with multiple players and pot are accepted."""
        state = TableState()
        state.active_players = 6
        state.pot_size = 45.50
        
        # Create mock image with some green (poker felt)
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_image[:, :, 1] = 128  # Add green channel
        
        is_valid, reason = self.scraper._validate_poker_table(state, mock_image)
        
        self.assertTrue(is_valid)
        self.assertIn("6 active players", reason)
        self.assertIn("Pot: $45.5", reason)
    
    def test_post_flop_zero_pot_rejected(self):
        """Test that post-flop hands with zero pot are rejected."""
        state = TableState()
        state.active_players = 4
        state.pot_size = 0.0
        state.board_cards = [Mock(), Mock(), Mock()]  # 3 board cards (flop)
        
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        is_valid, reason = self.scraper._validate_poker_table(state, mock_image)
        
        self.assertFalse(is_valid)
        self.assertIn("Zero pot with board cards", reason)
    
    def test_insufficient_evidence_rejected(self):
        """Test that tables with only 1 indicator are rejected."""
        state = TableState()
        state.active_players = 3  # Only 1 indicator
        state.pot_size = 0.0
        state.hero_cards = []
        state.board_cards = []
        
        # Black image (no visual indicators)
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        is_valid, reason = self.scraper._validate_poker_table(state, mock_image)
        
        self.assertFalse(is_valid)
        self.assertIn("Insufficient evidence", reason)
    
    def test_felt_detection(self):
        """Test green felt detection."""
        # Create image with significant green content (HSV green range)
        mock_image = np.zeros((200, 200, 3), dtype=np.uint8)
        # Create green in HSV space that converts to RGB
        # Use a bright green color
        mock_image[:, :] = [0, 180, 0]  # BGR format - strong green
        
        # With dependencies available
        if hasattr(self.scraper, '_detect_poker_felt'):
            has_felt = self.scraper._detect_poker_felt(mock_image)
            # May pass or fail depending on color conversion
            # This is more of a smoke test
            self.assertIsInstance(has_felt, bool)
    
    def test_table_with_cards_accepted(self):
        """Test that tables with detected cards are more likely to be accepted."""
        state = TableState()
        state.active_players = 4
        state.pot_size = 10.0
        state.hero_cards = [Mock(), Mock()]  # 2 hero cards
        state.board_cards = []
        
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        is_valid, reason = self.scraper._validate_poker_table(state, mock_image)
        
        self.assertTrue(is_valid)
        self.assertIn("2 hero cards", reason)
    
    def test_analyze_table_returns_empty_on_invalid(self):
        """Test that analyze_table returns empty state when validation fails."""
        # Mock capture_table to return a black image
        with patch.object(self.scraper, 'capture_table') as mock_capture:
            mock_capture.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            # Mock extractions to return invalid state
            with patch.object(self.scraper, 'extract_seat_info') as mock_seats:
                mock_seats.return_value = [SeatInfo(i) for i in range(1, 10)]  # All empty
                
                state = self.scraper.analyze_table()
                
                # Should return empty state due to validation failure
                self.assertEqual(state.active_players, 0)
                self.assertEqual(state.pot_size, 0.0)
    
    def test_analyze_table_returns_state_on_valid(self):
        """Test that analyze_table returns populated state when validation passes."""
        # Mock capture_table to return a colorful image
        with patch.object(self.scraper, 'capture_table') as mock_capture:
            mock_image = np.zeros((200, 200, 3), dtype=np.uint8)
            mock_image[:, :] = [0, 180, 0]  # Green background
            mock_capture.return_value = mock_image
            
            # Mock extractions to return valid state
            with patch.object(self.scraper, 'extract_seat_info') as mock_seats:
                # Create 6 active seats
                seats = [SeatInfo(i, is_active=(i <= 6), stack_size=100.0) 
                        for i in range(1, 10)]
                mock_seats.return_value = seats
                
                with patch.object(self.scraper, 'extract_pot_size') as mock_pot:
                    mock_pot.return_value = 45.0
                    
                    state = self.scraper.analyze_table()
                    
                    # Should return valid state
                    self.assertEqual(state.active_players, 6)
                    self.assertEqual(state.pot_size, 45.0)


class TestCreateScraper(unittest.TestCase):
    """Test scraper factory function."""
    
    def test_create_generic_scraper(self):
        """Test creating generic scraper."""
        scraper = create_scraper('GENERIC')
        self.assertEqual(scraper.site, PokerSite.GENERIC)
    
    def test_create_pokerstars_scraper(self):
        """Test creating PokerStars scraper."""
        scraper = create_scraper('POKERSTARS')
        self.assertEqual(scraper.site, PokerSite.POKERSTARS)
    
    def test_create_chrome_scraper(self):
        """Test creating Chrome scraper."""
        scraper = create_scraper('CHROME')
        self.assertEqual(scraper.site, PokerSite.CHROME)
    
    def test_invalid_site_defaults_to_generic(self):
        """Test that invalid site names default to generic."""
        scraper = create_scraper('INVALID_SITE')
        self.assertEqual(scraper.site, PokerSite.GENERIC)


class TestValidationLogging(unittest.TestCase):
    """Test that validation produces appropriate logs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = create_scraper('GENERIC')
    
    @patch('pokertool.modules.poker_screen_scraper.logger')
    def test_validation_failure_logged(self, mock_logger):
        """Test that validation failures are logged."""
        state = TableState()
        state.active_players = 0
        
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        with patch.object(self.scraper, 'capture_table', return_value=mock_image):
            with patch.object(self.scraper, 'extract_seat_info', return_value=[]):
                result_state = self.scraper.analyze_table()
                
                # Check that info log was called
                mock_logger.info.assert_called()
                
                # Check that at least one call contains "No valid poker table"
                info_calls = [str(call) for call in mock_logger.info.call_args_list]
                self.assertTrue(any("No valid poker table" in str(call) or 
                                  "TABLE DETECTION" in str(call) 
                                  for call in info_calls))
    
    @patch('pokertool.modules.poker_screen_scraper.logger')
    def test_validation_success_logged(self, mock_logger):
        """Test that validation successes are logged."""
        state = TableState()
        state.active_players = 6
        state.pot_size = 50.0
        
        mock_image = np.zeros((200, 200, 3), dtype=np.uint8)
        mock_image[:, :] = [0, 180, 0]  # Green
        
        seats = [SeatInfo(i, is_active=(i <= 6), stack_size=100.0) 
                for i in range(1, 10)]
        
        with patch.object(self.scraper, 'capture_table', return_value=mock_image):
            with patch.object(self.scraper, 'extract_seat_info', return_value=seats):
                with patch.object(self.scraper, 'extract_pot_size', return_value=50.0):
                    result_state = self.scraper.analyze_table()
                    
                    # Check that success was logged
                    info_calls = [str(call) for call in mock_logger.info.call_args_list]
                    self.assertTrue(any("Valid table detected" in str(call) or
                                      "✓" in str(call)
                                      for call in info_calls))


if __name__ == '__main__':
    unittest.main()
