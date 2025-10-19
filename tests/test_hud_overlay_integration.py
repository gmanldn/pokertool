#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HUD Overlay Integration Tests
==============================

Integration tests for HUD overlay with prerecorded screenshots.
Tests on-table updates, profile switching, and stat rendering.

These tests verify:
- HUD initialization and configuration
- Game state updates and rendering
- Profile loading and switching
- Stat display and color conditions
- Opponent popup functionality
- Display scaling and positioning
"""

import pytest
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test fixtures directory
TEST_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "hud_overlay"

# Mock tkinter if not available
try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    pytest.skip("GUI not available for HUD tests", allow_module_level=True)

from pokertool.hud_overlay import (
    HUDOverlay,
    HUDConfig,
    PlayerHUDStats,
    update_hud_state,
    start_hud_overlay,
    stop_hud_overlay,
)


@pytest.fixture
def hud_config():
    """Create default HUD configuration for testing."""
    return HUDConfig(
        position=(100, 100),
        size=(400, 300),
        opacity=0.9,
        show_hole_cards=True,
        show_board_cards=True,
        show_opponent_stats=True,
        enabled_stats=['vpip', 'pfr', 'aggression'],
        update_interval=0.1,  # Fast updates for testing
    )


@pytest.fixture
def mock_gto_solver():
    """Mock GTO solver to avoid dependencies."""
    with patch('pokertool.hud_overlay.get_gto_solver') as mock:
        solver = Mock()
        mock.return_value = solver
        yield solver


@pytest.fixture
def mock_ml_system():
    """Mock ML opponent modeling system."""
    with patch('pokertool.hud_overlay.get_opponent_modeling_system') as mock:
        ml_system = Mock()
        ml_system.get_player_profile.return_value = {
            'name': 'Player1',
            'hands_observed': 100,
            'vpip': 0.25,
            'pfr': 0.18,
            'aggression_factor': 2.5,
            'notes': ['Aggressive player', 'Likes to bluff']
        }
        mock.return_value = ml_system
        yield ml_system


@pytest.fixture
def mock_db():
    """Mock database."""
    with patch('pokertool.hud_overlay.get_secure_db') as mock:
        db = Mock()
        mock.return_value = db
        yield db


@pytest.fixture
def sample_game_state():
    """Create sample game state for testing."""
    return {
        'hole_cards': ['As', 'Kh'],
        'hole_cards_ocr': ['As', 'Kh'],
        'board_cards': ['Js', '9d', '2c'],
        'board_cards_ocr': ['Js', '9d', '2c'],
        'position': 'BTN',
        'pot': 150,
        'to_call': 30,
        'num_players': 6,
        'hole_confidence': 0.95,
        'timestamp': datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_game_states():
    """Create multiple game states for sequential testing."""
    return [
        {
            'hole_cards_ocr': ['As', 'Kh'],
            'board_cards_ocr': [],
            'position': 'BTN',
            'pot': 50,
            'to_call': 10,
            'hole_confidence': 0.98,
        },
        {
            'hole_cards_ocr': ['As', 'Kh'],
            'board_cards_ocr': ['Js', '9d', '2c'],
            'position': 'BTN',
            'pot': 150,
            'to_call': 30,
            'hole_confidence': 0.95,
        },
        {
            'hole_cards_ocr': ['As', 'Kh'],
            'board_cards_ocr': ['Js', '9d', '2c', 'Ah'],
            'position': 'BTN',
            'pot': 400,
            'to_call': 75,
            'hole_confidence': 0.92,
        },
    ]


class TestHUDInitialization:
    """Test HUD overlay initialization."""

    def test_hud_creation(self, hud_config, mock_gto_solver, mock_ml_system, mock_db):
        """Test HUD overlay can be created with configuration."""
        hud = HUDOverlay(hud_config)
        assert hud.config == hud_config
        assert not hud.running
        assert hud.current_state is None

    def test_hud_initialize(self, hud_config, mock_gto_solver, mock_ml_system, mock_db):
        """Test HUD initialization creates GUI components."""
        hud = HUDOverlay(hud_config)
        
        # Mock root window to avoid actually creating GUI
        with patch.object(tk, 'Tk') as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root
            
            result = hud.initialize()
            
            assert result is True
            assert hud.root is not None
            mock_root.title.assert_called_once_with("Poker HUD")

    def test_hud_config_validation(self):
        """Test HUD config validates parameters."""
        # Valid config
        config = HUDConfig(opacity=0.8, font_size=12)
        assert config.opacity == 0.8
        assert config.font_size == 12
        
        # Config with all defaults
        config = HUDConfig()
        assert 0.0 <= config.opacity <= 1.0
        assert config.font_size > 0


class TestGameStateUpdates:
    """Test HUD updates with game state changes."""

    def test_update_game_state(self, hud_config, sample_game_state, 
                               mock_gto_solver, mock_ml_system, mock_db):
        """Test HUD receives and processes game state updates."""
        hud = HUDOverlay(hud_config)
        hud.update_game_state(sample_game_state)
        
        assert hud.current_state == sample_game_state
        assert hud.current_state['hole_cards_ocr'] == ['As', 'Kh']
        assert hud.current_state['position'] == 'BTN'

    def test_sequential_state_updates(self, hud_config, sample_game_states,
                                     mock_gto_solver, mock_ml_system, mock_db):
        """Test HUD handles sequential state updates correctly."""
        hud = HUDOverlay(hud_config)
        
        for state in sample_game_states:
            hud.update_game_state(state)
            assert hud.current_state == state
            time.sleep(0.01)  # Small delay between updates

    def test_state_callback_triggering(self, hud_config, sample_game_state,
                                       mock_gto_solver, mock_ml_system, mock_db):
        """Test state callbacks are triggered on updates."""
        hud = HUDOverlay(hud_config)
        
        callback_called = []
        
        def state_callback(state):
            callback_called.append(state)
        
        hud.register_state_callback(state_callback)
        hud.update_game_state(sample_game_state)
        
        assert len(callback_called) == 1
        assert callback_called[0] == sample_game_state


class TestDisplayRendering:
    """Test HUD display rendering with mocked GUI."""

    def test_display_update_with_cards(self, hud_config, sample_game_state,
                                       mock_gto_solver, mock_ml_system, mock_db):
        """Test display updates when cards are present."""
        hud = HUDOverlay(hud_config)
        hud.current_state = sample_game_state
        
        # Mock widgets
        hud.widgets = {
            'hero_cards': Mock(),
            'board_cards': Mock(),
            'position': Mock(),
            'status': Mock(),
        }
        
        hud._update_display()
        
        # Verify widgets were updated
        hud.widgets['hero_cards'].config.assert_called()
        hud.widgets['board_cards'].config.assert_called()
        hud.widgets['position'].config.assert_called()

    def test_opponent_stats_rendering(self, hud_config, mock_gto_solver, 
                                      mock_ml_system, mock_db):
        """Test opponent statistics are rendered correctly."""
        hud = HUDOverlay(hud_config)
        
        # Mock opponent stats widget
        mock_text_widget = Mock(spec=tk.Text)
        hud.widgets['opponent_stats'] = mock_text_widget
        
        # Set up ML system to return player data
        mock_ml_system.get_player_profile.return_value = {
            'name': 'Villain1',
            'hands_observed': 150,
            'vpip': 0.28,
            'pfr': 0.20,
            'aggression_factor': 3.2,
        }
        
        hud._update_opponent_stats()
        
        # Verify text widget was updated
        assert mock_text_widget.configure.called
        assert mock_text_widget.insert.called

    def test_color_conditions_applied(self, hud_config, mock_gto_solver, 
                                     mock_ml_system, mock_db):
        """Test stat color conditions are applied correctly."""
        # Configure color conditions
        hud_config.stat_color_conditions = {
            'vpip': [
                {'operator': '>=', 'threshold': 40, 'color': '#f97316', 'label': 'Loose'},
                {'operator': '<=', 'threshold': 15, 'color': '#22d3ee', 'label': 'Nit'}
            ]
        }
        
        hud = HUDOverlay(hud_config)
        
        # Test color resolution
        color, label = hud._resolve_stat_color('vpip', '45')
        assert color == '#f97316'
        assert label == 'Loose'
        
        color, label = hud._resolve_stat_color('vpip', '12')
        assert color == '#22d3ee'
        assert label == 'Nit'


class TestProfileSwitching:
    """Test HUD profile loading and switching."""

    def test_load_profile(self, hud_config, mock_gto_solver, mock_ml_system, mock_db):
        """Test loading a HUD profile updates configuration."""
        hud = HUDOverlay(hud_config)
        
        # Mock profile data
        with patch('pokertool.hud_overlay.load_hud_profile') as mock_load:
            mock_load.return_value = {
                'opacity': 0.7,
                'font_size': 14,
                'enabled_stats': ['vpip', 'pfr', 'three_bet'],
            }
            
            # Mock profile var and rebuild
            hud.profile_var = Mock()
            hud.profile_var.get.return_value = 'TestProfile'
            
            with patch.object(hud, '_rebuild_widgets'):
                hud._on_profile_selected()
            
            # Config should be updated
            assert hud.config.opacity == 0.7
            assert hud.config.font_size == 14

    def test_save_profile(self, hud_config, mock_gto_solver, mock_ml_system, mock_db):
        """Test saving current HUD configuration as profile."""
        hud = HUDOverlay(hud_config)
        
        with patch('pokertool.hud_overlay.save_hud_profile') as mock_save:
            hud.profile_var = Mock()
            hud.profile_var.get.return_value = 'MyProfile'
            
            hud._save_current_profile()
            
            # Verify save was called
            assert mock_save.called
            saved_data = mock_save.call_args[0][1]
            assert saved_data['profile_name'] == 'MyProfile'


class TestDisplayScaling:
    """Test HUD display scaling and positioning."""

    def test_display_metrics_update(self, hud_config, mock_gto_solver, 
                                    mock_ml_system, mock_db):
        """Test display metrics updates trigger scaling."""
        hud = HUDOverlay(hud_config)
        original_size = hud.config.size
        
        # Update display metrics with 2x scaling
        metrics = {
            'scale_x': 2.0,
            'scale_y': 2.0,
            'width': 3840,
            'height': 2160,
        }
        
        hud._update_display_metrics(metrics)
        
        # Size should be scaled
        assert hud.config.size[0] > original_size[0]
        assert hud.config.size[1] > original_size[1]

    def test_scaling_preserves_design_dimensions(self, hud_config, 
                                                 mock_gto_solver, mock_ml_system, mock_db):
        """Test scaling maintains original design dimensions."""
        hud = HUDOverlay(hud_config)
        original_design_size = hud._design_size
        
        # Apply scaling
        metrics = {'scale_x': 1.5, 'scale_y': 1.5}
        hud._update_display_metrics(metrics)
        
        # Design size should remain unchanged
        assert hud._design_size == original_design_size


class TestOpponentPopup:
    """Test opponent popup functionality."""

    def test_popup_creation(self, hud_config, mock_gto_solver, 
                           mock_ml_system, mock_db):
        """Test opponent popup window is created."""
        hud_config.popup_enabled = True
        hud = HUDOverlay(hud_config)
        
        player_profile = {
            'name': 'TestPlayer',
            'vpip': 0.30,
            'pfr': 0.22,
            'hands_observed': 200,
            'notes': ['Plays tight early', 'Loosens up late']
        }
        
        # Mock root and popup window
        hud.root = Mock()
        mock_popup = Mock()
        
        with patch.object(tk, 'Toplevel', return_value=mock_popup):
            hud._show_popup(player_profile)
            
            # Popup should be created
            assert mock_popup.title.called
            assert mock_popup.configure.called


class TestHUDLifecycle:
    """Test HUD start/stop lifecycle."""

    def test_start_stop_hud(self, hud_config, mock_gto_solver, 
                           mock_ml_system, mock_db):
        """Test starting and stopping HUD."""
        hud = HUDOverlay(hud_config)
        
        # Mock GUI components
        hud.root = Mock()
        
        with patch.object(hud, '_run_gui'):
            result = hud.start()
            assert result is True
            assert hud.running is True
            
            hud.stop()
            assert hud.running is False


class TestIntegrationWithFixtures:
    """Integration tests using prerecorded screenshot fixtures."""

    @pytest.fixture
    def fixture_states(self):
        """Load fixture game states if available."""
        fixture_file = TEST_FIXTURES_DIR / "game_states.json"
        
        if not fixture_file.exists():
            # Create sample fixtures
            TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
            sample_fixtures = [
                {
                    'name': 'preflop_premium',
                    'hole_cards_ocr': ['Ah', 'Ad'],
                    'board_cards_ocr': [],
                    'position': 'BTN',
                    'pot': 30,
                    'to_call': 10,
                },
                {
                    'name': 'flop_top_pair',
                    'hole_cards_ocr': ['As', 'Kh'],
                    'board_cards_ocr': ['Ah', '9d', '2c'],
                    'position': 'BTN',
                    'pot': 150,
                    'to_call': 40,
                },
            ]
            
            with open(fixture_file, 'w') as f:
                json.dump(sample_fixtures, f, indent=2)
            
            return sample_fixtures
        
        with open(fixture_file) as f:
            return json.load(f)

    def test_fixture_based_updates(self, hud_config, fixture_states,
                                   mock_gto_solver, mock_ml_system, mock_db):
        """Test HUD updates using fixture game states."""
        hud = HUDOverlay(hud_config)
        
        for fixture in fixture_states:
            hud.update_game_state(fixture)
            assert hud.current_state['hole_cards_ocr'] == fixture['hole_cards_ocr']
            
            # Mock widgets and test display update
            hud.widgets = {
                'hero_cards': Mock(),
                'board_cards': Mock(),
                'position': Mock(),
            }
            
            hud._update_display()
            
            # Widgets should be updated
            assert hud.widgets['hero_cards'].config.called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])