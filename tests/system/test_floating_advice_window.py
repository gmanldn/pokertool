#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for Floating Advice Window
===============================================

Tests UI components, advice display, and integration.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pokertool.floating_advice_window import (
    FloatingAdviceWindow,
    Advice,
    ActionType,
    ConfidenceLevel
)


class TestActionType:
    """Test ActionType enum."""

    def test_action_types_exist(self):
        """Test all action types are defined."""
        assert ActionType.FOLD.value == "FOLD"
        assert ActionType.CALL.value == "CALL"
        assert ActionType.RAISE.value == "RAISE"
        assert ActionType.CHECK.value == "CHECK"
        assert ActionType.ALL_IN.value == "ALL-IN"


class TestConfidenceLevel:
    """Test ConfidenceLevel enum."""

    def test_confidence_levels_exist(self):
        """Test all confidence levels are defined."""
        assert ConfidenceLevel.VERY_HIGH.label == "VERY HIGH"
        assert ConfidenceLevel.HIGH.label == "HIGH"
        assert ConfidenceLevel.MEDIUM.label == "MEDIUM"
        assert ConfidenceLevel.LOW.label == "LOW"
        assert ConfidenceLevel.VERY_LOW.label == "VERY LOW"

    def test_confidence_colors(self):
        """Test confidence level colors."""
        assert ConfidenceLevel.VERY_HIGH.color == "#00C853"  # Green
        assert ConfidenceLevel.VERY_LOW.color == "#DD2C00"   # Red

    def test_from_confidence(self):
        """Test getting confidence level from numeric value."""
        assert ConfidenceLevel.from_confidence(0.95) == ConfidenceLevel.VERY_HIGH
        assert ConfidenceLevel.from_confidence(0.80) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_confidence(0.65) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_confidence(0.50) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_confidence(0.30) == ConfidenceLevel.VERY_LOW


class TestAdvice:
    """Test Advice dataclass."""

    def test_advice_creation_minimal(self):
        """Test creating advice with minimal fields."""
        advice = Advice(
            action=ActionType.FOLD,
            confidence=0.85
        )

        assert advice.action == ActionType.FOLD
        assert advice.confidence == 0.85
        assert advice.amount is None
        assert advice.ev is None

    def test_advice_creation_full(self):
        """Test creating advice with all fields."""
        advice = Advice(
            action=ActionType.RAISE,
            confidence=0.92,
            amount=50.0,
            ev=25.5,
            pot_odds=0.33,
            hand_strength=0.78,
            reasoning="Strong hand with good pot odds",
            timestamp=time.time()
        )

        assert advice.action == ActionType.RAISE
        assert advice.confidence == 0.92
        assert advice.amount == 50.0
        assert advice.ev == 25.5
        assert advice.pot_odds == 0.33
        assert advice.hand_strength == 0.78
        assert "Strong hand" in advice.reasoning


class TestFloatingAdviceWindow:
    """Test FloatingAdviceWindow class."""

    @pytest.fixture
    def window(self):
        """Create a test window."""
        # Mock tkinter to avoid actual window creation in tests
        with patch('pokertool.floating_advice_window.tk.Tk') as mock_tk, \
             patch('pokertool.floating_advice_window.tk.Toplevel') as mock_toplevel:

            mock_root = MagicMock()
            mock_tk.return_value = mock_root

            window = FloatingAdviceWindow(parent=None)
            yield window

            # Cleanup
            try:
                window.destroy()
            except:
                pass

    def test_window_initialization(self, window):
        """Test window initializes correctly."""
        assert window is not None
        assert window.current_advice is None
        assert window.last_update_time == 0.0
        assert window.update_throttle == 0.5

    def test_update_advice_fold(self, window):
        """Test updating advice with FOLD action."""
        advice = Advice(
            action=ActionType.FOLD,
            confidence=0.85,
            ev=-15.0,
            pot_odds=0.25,
            hand_strength=0.30,
            reasoning="Weak hand, fold to save chips"
        )

        window.update_advice(advice)

        assert window.current_advice == advice
        assert window.last_update_time > 0

    def test_update_advice_raise(self, window):
        """Test updating advice with RAISE action."""
        advice = Advice(
            action=ActionType.RAISE,
            confidence=0.90,
            amount=75.0,
            ev=35.5,
            pot_odds=0.40,
            hand_strength=0.85,
            reasoning="Strong hand, raise for value"
        )

        window.update_advice(advice)

        assert window.current_advice.action == ActionType.RAISE
        assert window.current_advice.amount == 75.0

    def test_update_throttling(self, window):
        """Test that updates are throttled."""
        advice1 = Advice(action=ActionType.FOLD, confidence=0.8)
        advice2 = Advice(action=ActionType.RAISE, confidence=0.9, amount=50.0)

        # First update
        window.update_advice(advice1)
        first_time = window.last_update_time

        # Immediate second update (should be throttled)
        window.update_advice(advice2)
        second_time = window.last_update_time

        # Times should be the same (throttled)
        assert second_time == first_time
        assert window.current_advice.action == ActionType.FOLD  # Still first advice

        # Wait for throttle period
        time.sleep(0.6)

        # Third update (should work)
        window.update_advice(advice2)
        third_time = window.last_update_time

        assert third_time > first_time
        assert window.current_advice.action == ActionType.RAISE

    def test_clear_advice(self, window):
        """Test clearing advice."""
        # Set some advice
        advice = Advice(
            action=ActionType.RAISE,
            confidence=0.90,
            amount=75.0
        )
        window.update_advice(advice)

        # Clear it
        window.clear_advice()

        # Current advice should still be stored but UI cleared
        # (We can't test UI directly in unit tests without real tk window)
        assert window.current_advice is not None  # Still stored

    def test_show_hide(self, window):
        """Test showing and hiding window."""
        # These methods should exist and be callable
        window.show()
        window.hide()

    def test_confidence_display_mapping(self, window):
        """Test that confidence levels map correctly to display."""
        test_cases = [
            (0.95, ConfidenceLevel.VERY_HIGH),
            (0.80, ConfidenceLevel.HIGH),
            (0.65, ConfidenceLevel.MEDIUM),
            (0.50, ConfidenceLevel.LOW),
            (0.30, ConfidenceLevel.VERY_LOW),
        ]

        for confidence, expected_level in test_cases:
            advice = Advice(action=ActionType.CALL, confidence=confidence)
            window.update_advice(advice)

            actual_level = ConfidenceLevel.from_confidence(confidence)
            assert actual_level == expected_level


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.fixture
    def window(self):
        """Create a test window."""
        with patch('pokertool.floating_advice_window.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root

            window = FloatingAdviceWindow(parent=None)
            yield window

            try:
                window.destroy()
            except:
                pass

    def test_fold_scenario(self, window):
        """Test complete FOLD scenario."""
        advice = Advice(
            action=ActionType.FOLD,
            confidence=0.88,
            ev=-20.0,
            pot_odds=0.20,
            hand_strength=0.25,
            reasoning="Weak hand, poor pot odds. Opponent likely has better hand."
        )

        window.update_advice(advice)

        assert window.current_advice.action == ActionType.FOLD
        assert window.current_advice.confidence == 0.88
        assert window.current_advice.ev < 0

    def test_call_scenario(self, window):
        """Test complete CALL scenario."""
        advice = Advice(
            action=ActionType.CALL,
            confidence=0.72,
            ev=5.5,
            pot_odds=0.35,
            hand_strength=0.60,
            reasoning="Reasonable hand, good pot odds. Call to see next card."
        )

        window.update_advice(advice)

        assert window.current_advice.action == ActionType.CALL
        assert window.current_advice.confidence == 0.72
        assert window.current_advice.ev > 0

    def test_raise_scenario(self, window):
        """Test complete RAISE scenario."""
        advice = Advice(
            action=ActionType.RAISE,
            confidence=0.93,
            amount=100.0,
            ev=45.0,
            pot_odds=0.45,
            hand_strength=0.92,
            reasoning="Very strong hand. Raise for value and to build pot."
        )

        window.update_advice(advice)

        assert window.current_advice.action == ActionType.RAISE
        assert window.current_advice.amount == 100.0
        assert window.current_advice.confidence > 0.9

    def test_sequence_of_updates(self, window):
        """Test sequence of advice updates."""
        scenarios = [
            Advice(ActionType.CALL, 0.65, reasoning="Pre-flop call"),
            Advice(ActionType.RAISE, 0.85, amount=50.0, reasoning="Flop raise"),
            Advice(ActionType.FOLD, 0.90, reasoning="Turn fold"),
        ]

        for i, advice in enumerate(scenarios):
            if i > 0:
                time.sleep(0.6)  # Wait for throttle

            window.update_advice(advice)
            assert window.current_advice.action == advice.action

    def test_high_confidence_all_in(self, window):
        """Test high confidence ALL-IN recommendation."""
        advice = Advice(
            action=ActionType.ALL_IN,
            confidence=0.97,
            amount=500.0,
            ev=150.0,
            pot_odds=0.50,
            hand_strength=0.98,
            reasoning="Absolute premium hand. All-in to maximize value."
        )

        window.update_advice(advice)

        assert window.current_advice.action == ActionType.ALL_IN
        assert window.current_advice.confidence >= 0.95
        assert ConfidenceLevel.from_confidence(0.97) == ConfidenceLevel.VERY_HIGH

    def test_marginal_decision(self, window):
        """Test marginal decision with low confidence."""
        advice = Advice(
            action=ActionType.CALL,
            confidence=0.45,
            ev=2.0,
            pot_odds=0.30,
            hand_strength=0.48,
            reasoning="Marginal situation. Slightly positive EV but low confidence."
        )

        window.update_advice(advice)

        assert window.current_advice.confidence < 0.5
        assert ConfidenceLevel.from_confidence(0.45) == ConfidenceLevel.LOW


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def window(self):
        """Create a test window."""
        with patch('pokertool.floating_advice_window.tk.Tk') as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root

            window = FloatingAdviceWindow(parent=None)
            yield window

            try:
                window.destroy()
            except:
                pass

    def test_minimum_confidence(self, window):
        """Test advice with minimum confidence."""
        advice = Advice(
            action=ActionType.FOLD,
            confidence=0.0
        )

        window.update_advice(advice)
        assert window.current_advice.confidence == 0.0

    def test_maximum_confidence(self, window):
        """Test advice with maximum confidence."""
        advice = Advice(
            action=ActionType.RAISE,
            confidence=1.0,
            amount=100.0
        )

        window.update_advice(advice)
        assert window.current_advice.confidence == 1.0

    def test_negative_ev(self, window):
        """Test advice with negative EV."""
        advice = Advice(
            action=ActionType.FOLD,
            confidence=0.85,
            ev=-50.0
        )

        window.update_advice(advice)
        assert window.current_advice.ev < 0

    def test_zero_amount(self, window):
        """Test raise with zero amount (CHECK scenario)."""
        advice = Advice(
            action=ActionType.CHECK,
            confidence=0.70,
            amount=0.0
        )

        window.update_advice(advice)
        assert window.current_advice.action == ActionType.CHECK

    def test_no_optional_fields(self, window):
        """Test advice with no optional fields."""
        advice = Advice(
            action=ActionType.CALL,
            confidence=0.75
        )

        window.update_advice(advice)

        assert window.current_advice.ev is None
        assert window.current_advice.pot_odds is None
        assert window.current_advice.hand_strength is None

    def test_empty_reasoning(self, window):
        """Test advice with empty reasoning."""
        advice = Advice(
            action=ActionType.FOLD,
            confidence=0.80,
            reasoning=""
        )

        window.update_advice(advice)
        assert window.current_advice.reasoning == ""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
