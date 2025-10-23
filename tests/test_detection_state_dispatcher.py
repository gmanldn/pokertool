#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for Detection State Dispatcher
=====================================

Tests comprehensive event emission for all state changes.
"""

import pytest
from unittest.mock import patch, call

from pokertool.detection_state_dispatcher import (
    DetectionStateDispatcher,
    TableState,
    get_dispatcher,
    reset_dispatcher,
)


@pytest.fixture
def dispatcher():
    """Create fresh dispatcher for each test."""
    reset_dispatcher()
    return DetectionStateDispatcher()


class TestPotUpdates:
    """Test pot update event emission."""

    @patch('pokertool.detection_state_dispatcher.emit_pot_event')
    def test_pot_change_emits_event(self, mock_emit, dispatcher):
        """Test that pot changes emit events."""
        dispatcher.begin_frame()

        # First pot update
        changed = dispatcher.update_pot(100.0, confidence=0.95)

        assert changed is True
        assert mock_emit.call_count == 1
        assert dispatcher.state.pot_size == 100.0

        # Same pot should not emit
        changed = dispatcher.update_pot(100.0, confidence=0.95)
        assert changed is False
        assert mock_emit.call_count == 1

        # Changed pot should emit
        changed = dispatcher.update_pot(150.0, confidence=0.98)
        assert changed is True
        assert mock_emit.call_count == 2

    @patch('pokertool.detection_state_dispatcher.emit_pot_event')
    def test_side_pots_tracked(self, mock_emit, dispatcher):
        """Test side pot tracking."""
        dispatcher.begin_frame()

        changed = dispatcher.update_pot(100.0, side_pots=[25.0, 15.0], confidence=0.92)

        assert changed is True
        assert dispatcher.state.side_pots == [25.0, 15.0]
        mock_emit.assert_called_once()

        # Check call arguments
        call_args = mock_emit.call_args
        assert call_args[1]['pot_size'] == 100.0
        assert call_args[1]['side_pots'] == [25.0, 15.0]


class TestBoardCardUpdates:
    """Test board card update events."""

    @patch('pokertool.detection_state_dispatcher.emit_card_event')
    @patch('pokertool.detection_state_dispatcher.emit_state_change_event')
    def test_board_change_emits_event(self, mock_state_change, mock_card_event, dispatcher):
        """Test that board changes emit card events."""
        dispatcher.begin_frame()

        # Flop
        flop = [
            {'rank': 'A', 'suit': 'h'},
            {'rank': 'K', 'suit': 'h'},
            {'rank': 'Q', 'suit': 'h'}
        ]
        changed = dispatcher.update_board_cards(flop, confidence=0.96)

        assert changed is True
        assert len(dispatcher.state.board_cards) == 3
        mock_card_event.assert_called_once()

        # Should also emit street change (preflop -> flop)
        mock_state_change.assert_called_once()
        assert mock_state_change.call_args[1]['previous_state'] == 'preflop'
        assert mock_state_change.call_args[1]['new_state'] == 'flop'

    @patch('pokertool.detection_state_dispatcher.emit_card_event')
    @patch('pokertool.detection_state_dispatcher.emit_state_change_event')
    def test_street_transitions(self, mock_state_change, mock_card_event, dispatcher):
        """Test street transitions emit proper events."""
        dispatcher.begin_frame()

        # Flop
        flop = [{'rank': 'A', 'suit': 'h'}, {'rank': 'K', 'suit': 'h'}, {'rank': 'Q', 'suit': 'h'}]
        dispatcher.update_board_cards(flop)
        assert mock_state_change.call_count == 1

        # Turn
        turn = flop + [{'rank': 'J', 'suit': 'h'}]
        dispatcher.update_board_cards(turn)
        assert mock_state_change.call_count == 2
        assert mock_state_change.call_args[1]['previous_state'] == 'flop'
        assert mock_state_change.call_args[1]['new_state'] == 'turn'

        # River
        river = turn + [{'rank': 'T', 'suit': 'h'}]
        dispatcher.update_board_cards(river)
        assert mock_state_change.call_count == 3
        assert mock_state_change.call_args[1]['previous_state'] == 'turn'
        assert mock_state_change.call_args[1]['new_state'] == 'river'


class TestHeroCardUpdates:
    """Test hero card update events."""

    @patch('pokertool.detection_state_dispatcher.emit_card_event')
    @patch('pokertool.detection_state_dispatcher.emit_state_change_event')
    def test_hero_cards_emit_event(self, mock_state_change, mock_card_event, dispatcher):
        """Test that hero card changes emit events."""
        dispatcher.begin_frame()

        hero_cards = [{'rank': 'A', 'suit': 's'}, {'rank': 'K', 'suit': 's'}]
        changed = dispatcher.update_hero_cards(hero_cards, confidence=0.99)

        assert changed is True
        assert len(dispatcher.state.hero_cards) == 2
        mock_card_event.assert_called_once()

        # Should also emit hand start
        mock_state_change.assert_called_once()
        assert mock_state_change.call_args[1]['previous_state'] == 'no_hand'
        assert mock_state_change.call_args[1]['new_state'] == 'hand_active'


class TestPlayerUpdates:
    """Test player state update events."""

    @patch('pokertool.detection_state_dispatcher.emit_player_event')
    def test_player_stack_change(self, mock_emit, dispatcher):
        """Test player stack changes emit events."""
        dispatcher.begin_frame()

        # Initial stack
        changed = dispatcher.update_player(
            seat_number=1,
            stack_size=1000.0,
            player_name="Hero",
            position="BTN",
            confidence=0.97
        )

        assert changed is True
        assert dispatcher.state.player_stacks[1] == 1000.0
        mock_emit.assert_called_once()

        # Same stack should not emit
        changed = dispatcher.update_player(seat_number=1, stack_size=1000.0)
        assert changed is False
        assert mock_emit.call_count == 1

        # Stack change should emit
        changed = dispatcher.update_player(seat_number=1, stack_size=950.0)
        assert changed is True
        assert mock_emit.call_count == 2

    @patch('pokertool.detection_state_dispatcher.emit_player_event')
    def test_player_position_tracked(self, mock_emit, dispatcher):
        """Test player position is tracked."""
        dispatcher.begin_frame()

        dispatcher.update_player(
            seat_number=2,
            position="SB",
            stack_size=500.0
        )

        assert dispatcher.state.player_positions[2] == "SB"
        mock_emit.assert_called_once()


class TestPlayerActions:
    """Test player action events."""

    @patch('pokertool.detection_state_dispatcher.emit_action_event')
    def test_action_emission(self, mock_emit, dispatcher):
        """Test player actions emit events."""
        dispatcher.begin_frame()

        # Setup player first
        dispatcher.state.player_names[3] = "Villain"

        # Emit action
        dispatcher.emit_player_action(
            seat_number=3,
            action="raise",
            amount=50.0,
            confidence=0.94
        )

        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        assert call_args[1]['seat_number'] == 3
        assert call_args[1]['action'] == "raise"
        assert call_args[1]['amount'] == 50.0
        assert call_args[1]['player_name'] == "Villain"


class TestPerformanceUpdates:
    """Test performance metric updates."""

    @patch('pokertool.detection_state_dispatcher.emit_performance_event')
    def test_fps_change_emits(self, mock_emit, dispatcher):
        """Test FPS changes emit events."""
        dispatcher.begin_frame()

        # Initial FPS
        changed = dispatcher.update_performance(fps=30.0)
        assert changed is True
        mock_emit.assert_called_once()

        # Small change should not emit (need >5%)
        changed = dispatcher.update_performance(fps=30.5)
        assert changed is False
        assert mock_emit.call_count == 1

        # Large change should emit
        changed = dispatcher.update_performance(fps=20.0)
        assert changed is True
        assert mock_emit.call_count == 2


class TestHandManagement:
    """Test hand lifecycle management."""

    @patch('pokertool.detection_state_dispatcher.emit_state_change_event')
    def test_hand_reset(self, mock_emit, dispatcher):
        """Test hand reset clears state."""
        # Setup initial hand state
        dispatcher.state.pot_size = 100.0
        dispatcher.state.board_cards = [{'rank': 'A', 'suit': 's'}]
        dispatcher.state.hero_cards = [{'rank': 'K', 'suit': 's'}, {'rank': 'Q', 'suit': 's'}]
        dispatcher.state.hand_id = "hand_123"

        # Reset hand
        dispatcher.reset_hand()

        # Hand end event should be emitted
        assert mock_emit.call_count == 1
        assert mock_emit.call_args[1]['previous_state'] == 'hand_active'

        # State should be reset
        assert dispatcher.state.pot_size == 0.0
        assert len(dispatcher.state.board_cards) == 0
        assert len(dispatcher.state.hero_cards) == 0
        assert dispatcher.state.current_street == "preflop"
        assert dispatcher.state.hand_id is not None
        assert dispatcher.state.hand_id != "hand_123"


class TestFrameCorrelation:
    """Test frame correlation IDs."""

    def test_frame_correlation(self, dispatcher):
        """Test correlation IDs are set during frames."""
        # No correlation ID initially
        assert dispatcher._current_correlation_id is None

        # Begin frame sets correlation ID
        corr_id = dispatcher.begin_frame()
        assert corr_id is not None
        assert dispatcher._current_correlation_id == corr_id

        # End frame clears it
        dispatcher.end_frame()
        assert dispatcher._current_correlation_id is None


class TestDispatcherStats:
    """Test dispatcher statistics."""

    def test_stats_tracking(self, dispatcher):
        """Test dispatcher tracks statistics."""
        stats = dispatcher.get_stats()

        assert 'total_events_emitted' in stats
        assert 'current_hand_id' in stats
        assert 'current_street' in stats
        assert 'pot_size' in stats

        # Initially no events
        assert stats['total_events_emitted'] == 0

        # Emit some events
        with patch('pokertool.detection_state_dispatcher.emit_pot_event'):
            dispatcher.update_pot(100.0)
            dispatcher.update_pot(150.0)

        stats = dispatcher.get_stats()
        assert stats['total_events_emitted'] == 2
        assert stats['pot_size'] == 150.0


class TestGlobalDispatcher:
    """Test global dispatcher singleton."""

    def test_get_dispatcher_singleton(self):
        """Test get_dispatcher returns singleton."""
        reset_dispatcher()

        d1 = get_dispatcher()
        d2 = get_dispatcher()

        assert d1 is d2

    def test_reset_dispatcher(self):
        """Test reset_dispatcher creates new instance."""
        d1 = get_dispatcher()
        reset_dispatcher()
        d2 = get_dispatcher()

        assert d1 is not d2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
