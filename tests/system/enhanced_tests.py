#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: enhanced_tests.py
# version: v28.0.0
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
import json
import time
import threading
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from pathlib import Path
import tempfile
# Tkinter removed - web-only architecture
TK_AVAILABLE = False
tk = None
from typing import List, Dict, Any, Optional

# Import components to test
try:
    from pokertool.modules.poker_gui_enhanced import (
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
# GUI TESTS REMOVED - WEB-ONLY ARCHITECTURE
# All GUI-related tests have been removed as part of the tkinter removal initiative.
# The application now uses a web-based interface exclusively.
# ═══════════════════════════════════════════════════════════════════════════════

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
            active_players=6,
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
