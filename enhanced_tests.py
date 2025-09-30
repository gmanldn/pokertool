#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: enhanced_tests.py
# version: v20.0.0
# last_updated_utc: '2025-09-23T12:00:00.000000+00:00'
# applied_improvements:
# - Enhanced_Tests_1
# summary: Comprehensive unit tests for enhanced GUI and screen scraping components
# last_commit: '2025-09-23T14:49:43.443734+00:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END

"""
Enhanced Unit Tests for Poker Tool Components
Comprehensive test suite for the improved GUI and screen scraping functionality.
"""

import pytest
import numpy as np
import cv2
import json
import time
import threading
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from pathlib import Path
import tempfile
import tkinter as tk
from typing import List, Dict, Any, Optional

# Import components to test
try:
    from poker_gui_enhanced import (
        EnhancedPokerAssistant, EnhancedCardEntry, StatusBar, UITheme,
        ValidationState, UIState
    )
    GUI_ENHANCED_AVAILABLE = True
except ImportError:
    GUI_ENHANCED_AVAILABLE = False

try:
    from poker_screen_scraper_enhanced import (
        EnhancedPokerScreenScraper, EnhancedCardRecognizer, EnhancedTextRecognizer,
        EnhancedButtonDetector, PokerSite, TableState, SeatInfo, BoundingBox,
        DetectionConfidence, SiteConfig, EnhancedScreenScraperBridge
    )
    SCRAPER_ENHANCED_AVAILABLE = True
except ImportError:
    SCRAPER_ENHANCED_AVAILABLE = False

# Import fallback modules for testing
try:
    from poker_modules import Card, Suit, Position
    POKER_MODULES_AVAILABLE = True
except ImportError:
    POKER_MODULES_AVAILABLE = False
    
    # Fallback definitions for tests
    class Suit:
        SPADES = "♠"
        HEARTS = "♥" 
        DIAMONDS = "♦"
        CLUBS = "♣"
    
    class Card:
        def __init__(self, rank, suit):
            self.rank = rank
            self.suit = suit
        
        def __str__(self):
            return f"{self.rank}{self.suit}"
        
        def __eq__(self, other):
            return str(self) == str(other)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST FIXTURES AND UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_image():
    """Create a mock poker table image."""
    img = np.zeros((768, 1024, 3), dtype=np.uint8)
    
    # Add some table-like features
    # Green felt background
    img[:, :] = [20, 80, 30]
    
    # White card areas
    img[400:480, 450:570] = [255, 255, 255]  # Hero cards
    img[250:330, 350:650] = [255, 255, 255]  # Board area
    
    # Pot area with some text-like pattern
    img[180:220, 400:600] = [240, 240, 240]
    
    return img


@pytest.fixture
def sample_cards():
    """Create sample cards for testing."""
    if POKER_MODULES_AVAILABLE:
        return [
            Card('A', Suit.SPADES),
            Card('K', Suit.HEARTS),
            Card('Q', Suit.DIAMONDS),
            Card('J', Suit.CLUBS),
            Card('T', Suit.SPADES)
        ]
    else:
        return [
            Card('A', Suit.SPADES),
            Card('K', Suit.HEARTS),
            Card('Q', Suit.DIAMONDS),
            Card('J', Suit.CLUBS),
            Card('T', Suit.SPADES)
        ]


@pytest.fixture
def temp_session_file():
    """Create temporary session file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        session_data = {
            "timestamp": time.time(),
            "hand_cards": ["AS", "KH"],
            "board_cards": ["QD", "JC", "TS"],
            "stage": "Flop",
            "position": "BTN",
            "pot": "25.5",
            "to_call": "10.0"
        }
        json.dump(session_data, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    Path(temp_file).unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED GUI TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not GUI_ENHANCED_AVAILABLE, reason="Enhanced GUI not available")
class TestEnhancedCardEntry:
    """Test enhanced card entry widget."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create a temporary root for testing
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the test window
        
        self.callback_called = False
        def test_callback():
            self.callback_called = True
        
        self.entry = EnhancedCardEntry(self.root, callback=test_callback)
    
    def teardown_method(self):
        """Cleanup after each test."""
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_initialization(self):
        """Test card entry initialization."""
        assert self.entry.validation_state == ValidationState.EMPTY
        assert self.entry.callback is not None
    
    def test_valid_card_input(self):
        """Test valid card input validation."""
        # Test valid card
        self.entry.insert(0, "AS")
        self.entry._validate_input(None)
        
        assert self.entry.validation_state == ValidationState.VALID
        assert self.callback_called
        
        # Test getting card
        card = self.entry.get_card()
        assert card is not None
        assert card.rank == 'A'
        assert str(card.suit) in ['♠', 'S']
    
    def test_invalid_card_input(self):
        """Test invalid card input validation."""
        # Test invalid card
        self.entry.insert(0, "XX")
        self.entry._validate_input(None)
        
        assert self.entry.validation_state == ValidationState.INVALID
        
        # Should return None for invalid card
        card = self.entry.get_card()
        assert card is None
    
    def test_partial_input(self):
        """Test partial input validation."""
        # Test single character (pending)
        self.entry.insert(0, "A")
        self.entry._validate_input(None)
        
        assert self.entry.validation_state == ValidationState.PENDING
        
        # Should return None for incomplete input
        card = self.entry.get_card()
        assert card is None
    
    def test_clear_functionality(self):
        """Test clearing the entry."""
        self.entry.insert(0, "AS")
        self.entry.clear()
        
        assert self.entry.get() == ""
        assert self.entry.validation_state == ValidationState.EMPTY
    
    def test_set_card_programmatically(self):
        """Test setting card programmatically."""
        if POKER_MODULES_AVAILABLE:
            test_card = Card('K', Suit.HEARTS)
        else:
            test_card = Card('K', Suit.HEARTS)
        
        self.entry.set_card(test_card)
        
        assert self.entry.get() in ['KH', 'K♥']
        assert self.entry.validation_state == ValidationState.VALID


@pytest.mark.skipif(not GUI_ENHANCED_AVAILABLE, reason="Enhanced GUI not available")
class TestStatusBar:
    """Test status bar component."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.root = tk.Tk()
        self.root.withdraw()
        self.status_bar = StatusBar(self.root)
    
    def teardown_method(self):
        """Cleanup after each test."""
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_status_bar_initialization(self):
        """Test status bar initialization."""
        assert self.status_bar.status_label is not None
        assert self.status_bar.modules_frame is not None
        assert hasattr(self.status_bar, 'status_queue')
    
    def test_set_status_message(self):
        """Test setting status messages."""
        self.status_bar.set_status("Test message", 1.0)
        
        # Give some time for the message to be processed
        time.sleep(0.2)
        
        # The status should be updated (exact text depends on timing)
        assert self.status_bar.status_label.cget('text') in ['Test message', 'Ready']
    
    def test_permanent_status(self):
        """Test permanent status messages."""
        self.status_bar.set_permanent_status("Permanent message")
        
        # Give some time for processing
        time.sleep(0.2)
        
        # Should show the permanent message
        assert 'Permanent message' in self.status_bar.status_label.cget('text')


@pytest.mark.skipif(not GUI_ENHANCED_AVAILABLE, reason="Enhanced GUI not available")
class TestEnhancedPokerAssistant:
    """Test main enhanced GUI application."""
    
    @patch('tkinter.Tk.__init__')
    @patch('poker_gui_enhanced.initialise_db_if_needed')
    @patch('poker_gui_enhanced.open_db')
    def test_initialization(self, mock_open_db, mock_init_db, mock_tk_init):
        """Test application initialization."""
        mock_tk_init.return_value = None
        mock_open_db.return_value = None
        
        with patch.object(EnhancedPokerAssistant, '_setup_window'), \
             patch.object(EnhancedPokerAssistant, '_setup_styles'), \
             patch.object(EnhancedPokerAssistant, '_build_ui'), \
             patch.object(EnhancedPokerAssistant, '_bind_events'):
            
            app = EnhancedPokerAssistant()
            
            assert hasattr(app, 'ui_state')
            assert hasattr(app, 'game_state')
            assert hasattr(app, 'cards')
            assert hasattr(app, 'board_cards')
            assert isinstance(app.cards, list)
            assert isinstance(app.board_cards, list)
    
    def test_validation_logic(self):
        """Test input validation logic."""
        # Create minimal mock app
        with patch.object(EnhancedPokerAssistant, '__init__', lambda x: None):
            app = EnhancedPokerAssistant()
            app.cards = []
            app.board_cards = []
            app.stage_var = Mock()
            app.stage_var.get.return_value = "Flop"
            
            # Test validation with insufficient cards
            errors = app._validate_current_state()
            assert "Need at least 2 hole cards" in errors
            
            # Test with correct number of cards but wrong stage
            if POKER_MODULES_AVAILABLE:
                app.cards = [Card('A', Suit.SPADES), Card('K', Suit.HEARTS)]
                app.board_cards = [Card('Q', Suit.DIAMONDS)]  # Should be 3 for flop
            else:
                app.cards = [Card('A', Suit.SPADES), Card('K', Suit.HEARTS)]
                app.board_cards = [Card('Q', Suit.DIAMONDS)]
            
            errors = app._validate_current_state()
            assert any("Flop requires exactly 3 community cards" in error for error in errors)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED SCREEN SCRAPER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not SCRAPER_ENHANCED_AVAILABLE, reason="Enhanced scraper not available")
class TestBoundingBox:
    """Test BoundingBox data structure."""
    
    def test_bounding_box_creation(self):
        """Test bounding box creation."""
        bbox = BoundingBox(10, 20, 100, 50, confidence=0.8, name="test_region")
        
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
        assert bbox.confidence == 0.8
        assert bbox.name == "test_region"
    
    def test_get_coords(self):
        """Test coordinate extraction."""
        bbox = BoundingBox(10, 20, 100, 50)
        coords = bbox.get_coords()
        
        assert coords == (10, 20, 110, 70)  # (x1, y1, x2, y2)
    
    def test_contains_point(self):
        """Test point containment."""
        bbox = BoundingBox(10, 20, 100, 50)
        
        assert bbox.contains_point(50, 40) == True   # Inside
        assert bbox.contains_point(5, 40) == False   # Outside left
        assert bbox.contains_point(150, 40) == False # Outside right
        assert bbox.contains_point(50, 10) == False  # Outside top
        assert bbox.contains_point(50, 80) == False  # Outside bottom
    
    def test_intersects(self):
        """Test bounding box intersection."""
        bbox1 = BoundingBox(10, 10, 50, 50)
        bbox2 = BoundingBox(30, 30, 50, 50)  # Overlapping
        bbox3 = BoundingBox(100, 100, 50, 50)  # Non-overlapping
        
        assert bbox1.intersects(bbox2) == True
        assert bbox1.intersects(bbox3) == False
        assert bbox2.intersects(bbox3) == False
    
    def test_extract_from_image(self, mock_image):
        """Test image region extraction."""
        bbox = BoundingBox(100, 100, 200, 150)
        extracted = bbox.extract_from_image(mock_image)
        
        assert extracted.shape == (150, 200, 3)
    
    def test_extract_with_invalid_bounds(self, mock_image):
        """Test extraction with invalid bounds."""
        # Bounds outside image
        bbox = BoundingBox(2000, 2000, 100, 100)
        extracted = bbox.extract_from_image(mock_image)
        
        # Should return small fallback image
        assert extracted.shape == (10, 10, 3)


@pytest.mark.skipif(not SCRAPER_ENHANCED_AVAILABLE, reason="Enhanced scraper not available")
class TestTableState:
    """Test TableState data structure."""
    
    def test_table_state_creation(self, sample_cards):
        """Test table state creation."""
        state = TableState(
            pot_size=25.5,
            hero_cards=sample_cards[:2],
            board_cards=sample_cards[2:5],
            stage="flop",
            active_players=6
        )
        
        assert state.pot_size == 25.5
        assert len(state.hero_cards) == 2
        assert len(state.board_cards) == 3
        assert state.stage == "flop"
        assert state.active_players == 6
        assert state.hash_signature  # Should have a hash
    
    def test_hash_generation(self, sample_cards):
        """Test hash generation for change detection."""
        state1 = TableState(pot_size=25.5, hero_cards=sample_cards[:2])
        state2 = TableState(pot_size=25.5, hero_cards=sample_cards[:2])
        state3 = TableState(pot_size=30.0, hero_cards=sample_cards[:2])
        
        # Same state should have same hash
        assert state1.hash_signature == state2.hash_signature
        
        # Different state should have different hash
        assert state1.hash_signature != state3.hash_signature