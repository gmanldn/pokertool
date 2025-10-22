#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detection State Change Dispatcher
==================================

Provides comprehensive event emission for all poker table state changes.
Wraps structured event emission functions and tracks state to emit events
only when actual changes occur.

This module serves as the central dispatcher for all detection events,
ensuring comprehensive coverage of:
- Pot changes (size, side pots)
- Card detections (hero, board, opponent)
- Player state (stacks, position, active status)
- Player actions (fold, check, call, bet, raise, all-in)
- Game state transitions (hand start/end, street changes)
- Performance metrics (FPS, latency, memory)
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .detection_events import (
    emit_pot_event,
    emit_card_event,
    emit_player_event,
    emit_action_event,
    emit_state_change_event,
    emit_performance_event,
    DetectionEventType,
    EventSeverity,
)

logger = logging.getLogger(__name__)


@dataclass
class TableState:
    """Tracks current table state for change detection."""
    # Pot state
    pot_size: float = 0.0
    side_pots: List[float] = field(default_factory=list)

    # Board state
    board_cards: List[Dict[str, str]] = field(default_factory=list)

    # Hero cards
    hero_cards: List[Dict[str, str]] = field(default_factory=list)

    # Player states (keyed by seat number)
    player_stacks: Dict[int, float] = field(default_factory=dict)
    player_names: Dict[int, str] = field(default_factory=dict)
    player_positions: Dict[int, str] = field(default_factory=dict)
    player_active: Dict[int, bool] = field(default_factory=dict)

    # Game state
    current_street: str = "preflop"
    hand_id: Optional[str] = None
    button_position: Optional[int] = None

    # Performance state
    last_fps: Optional[float] = None
    last_frame_time_ms: Optional[float] = None

    # Timing
    last_update: float = field(default_factory=time.time)


class DetectionStateDispatcher:
    """
    Central dispatcher for all detection state change events.

    Tracks table state and emits events only when actual changes occur.
    Provides correlation IDs for related events.
    """

    def __init__(self):
        """Initialize dispatcher with empty state."""
        self.state = TableState()
        self._current_correlation_id: Optional[str] = None
        self._event_count = 0

    def begin_frame(self) -> str:
        """
        Begin a new detection frame.

        Returns:
            Correlation ID for this frame's events.
        """
        self._current_correlation_id = f"frame_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}"
        return self._current_correlation_id

    def end_frame(self):
        """End the current detection frame."""
        self._current_correlation_id = None

    def update_pot(
        self,
        pot_size: float,
        side_pots: Optional[List[float]] = None,
        confidence: float = 1.0
    ) -> bool:
        """
        Update pot size and emit event if changed.

        Args:
            pot_size: Current pot size.
            side_pots: List of side pot amounts.
            confidence: Detection confidence.

        Returns:
            True if pot changed and event was emitted.
        """
        side_pots = side_pots or []

        # Check if pot changed (allow 0.01 tolerance for float comparison)
        pot_changed = abs(pot_size - self.state.pot_size) > 0.01
        side_pots_changed = side_pots != self.state.side_pots

        if pot_changed or side_pots_changed:
            previous_pot = self.state.pot_size

            emit_pot_event(
                pot_size=pot_size,
                previous_pot_size=previous_pot,
                confidence=confidence,
                side_pots=side_pots,
                correlation_id=self._current_correlation_id
            )

            self.state.pot_size = pot_size
            self.state.side_pots = side_pots
            self._event_count += 1

            logger.debug(f"Pot changed: ${previous_pot:.2f} → ${pot_size:.2f}")
            return True

        return False

    def update_board_cards(
        self,
        cards: List[Dict[str, str]],
        confidence: float = 1.0
    ) -> bool:
        """
        Update board cards and emit event if changed.

        Args:
            cards: List of card dicts with 'rank' and 'suit'.
            confidence: Detection confidence.

        Returns:
            True if board changed and event was emitted.
        """
        if cards != self.state.board_cards:
            # Detect street change
            previous_count = len(self.state.board_cards)
            new_count = len(cards)

            if previous_count < new_count:
                # Street transition
                if new_count == 3:
                    self._emit_street_change("preflop", "flop")
                elif new_count == 4:
                    self._emit_street_change("flop", "turn")
                elif new_count == 5:
                    self._emit_street_change("turn", "river")

            emit_card_event(
                cards=cards,
                card_type="board",
                confidence=confidence,
                correlation_id=self._current_correlation_id
            )

            self.state.board_cards = cards
            self._event_count += 1

            logger.debug(f"Board cards changed: {len(cards)} cards")
            return True

        return False

    def update_hero_cards(
        self,
        cards: List[Dict[str, str]],
        confidence: float = 1.0
    ) -> bool:
        """
        Update hero cards and emit event if changed.

        Args:
            cards: List of card dicts with 'rank' and 'suit'.
            confidence: Detection confidence.

        Returns:
            True if hero cards changed and event was emitted.
        """
        if cards != self.state.hero_cards:
            emit_card_event(
                cards=cards,
                card_type="hero",
                confidence=confidence,
                correlation_id=self._current_correlation_id
            )

            # New hero cards often means new hand
            if len(cards) == 2 and len(self.state.hero_cards) == 0:
                self._emit_hand_start()

            self.state.hero_cards = cards
            self._event_count += 1

            logger.debug(f"Hero cards changed: {len(cards)} cards")
            return True

        return False

    def update_player(
        self,
        seat_number: int,
        stack_size: Optional[float] = None,
        player_name: Optional[str] = None,
        position: Optional[str] = None,
        is_active: bool = True,
        confidence: float = 1.0
    ) -> bool:
        """
        Update player state and emit event if changed.

        Args:
            seat_number: Player's seat number.
            stack_size: Current stack size.
            player_name: Player name if detected.
            position: Player position (BTN, SB, BB, etc.).
            is_active: Whether player is active.
            confidence: Detection confidence.

        Returns:
            True if player state changed and event was emitted.
        """
        changed = False
        previous_stack = self.state.player_stacks.get(seat_number)

        # Check what changed
        if stack_size is not None and stack_size != previous_stack:
            changed = True
        if player_name is not None and player_name != self.state.player_names.get(seat_number):
            changed = True
        if position is not None and position != self.state.player_positions.get(seat_number):
            changed = True
        if is_active != self.state.player_active.get(seat_number, True):
            changed = True

        if changed:
            emit_player_event(
                seat_number=seat_number,
                player_name=player_name,
                stack_size=stack_size,
                previous_stack=previous_stack,
                position=position,
                is_active=is_active,
                confidence=confidence,
                correlation_id=self._current_correlation_id
            )

            # Update state
            if stack_size is not None:
                self.state.player_stacks[seat_number] = stack_size
            if player_name is not None:
                self.state.player_names[seat_number] = player_name
            if position is not None:
                self.state.player_positions[seat_number] = position
            self.state.player_active[seat_number] = is_active

            self._event_count += 1

            logger.debug(f"Player {seat_number} state changed")
            return True

        return False

    def emit_player_action(
        self,
        seat_number: int,
        action: str,
        amount: float = 0.0,
        confidence: float = 1.0
    ) -> None:
        """
        Emit player action event.

        Args:
            seat_number: Player's seat number.
            action: Action type (fold, check, call, bet, raise, all_in).
            amount: Action amount.
            confidence: Detection confidence.
        """
        player_name = self.state.player_names.get(seat_number)

        emit_action_event(
            seat_number=seat_number,
            action=action,
            amount=amount,
            player_name=player_name,
            confidence=confidence,
            correlation_id=self._current_correlation_id
        )

        self._event_count += 1
        logger.debug(f"Player {seat_number} action: {action} ${amount:.2f}")

    def update_performance(
        self,
        fps: Optional[float] = None,
        avg_frame_time_ms: Optional[float] = None,
        memory_mb: Optional[float] = None,
        cpu_percent: Optional[float] = None
    ) -> bool:
        """
        Update performance metrics and emit event if changed significantly.

        Args:
            fps: Current frames per second.
            avg_frame_time_ms: Average frame processing time.
            memory_mb: Memory usage in MB.
            cpu_percent: CPU usage percentage.

        Returns:
            True if performance metrics changed significantly.
        """
        # Only emit if FPS changed by >5% or frame time changed by >10ms
        fps_changed = False
        if fps is not None and self.state.last_fps is not None:
            fps_changed = abs(fps - self.state.last_fps) / self.state.last_fps > 0.05
        elif fps is not None:
            fps_changed = True

        frame_time_changed = False
        if avg_frame_time_ms is not None and self.state.last_frame_time_ms is not None:
            frame_time_changed = abs(avg_frame_time_ms - self.state.last_frame_time_ms) > 10
        elif avg_frame_time_ms is not None:
            frame_time_changed = True

        if fps_changed or frame_time_changed:
            emit_performance_event(
                fps=fps,
                avg_frame_time_ms=avg_frame_time_ms,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                correlation_id=self._current_correlation_id
            )

            if fps is not None:
                self.state.last_fps = fps
            if avg_frame_time_ms is not None:
                self.state.last_frame_time_ms = avg_frame_time_ms

            self._event_count += 1
            return True

        return False

    def reset_hand(self):
        """Reset state for a new hand."""
        # Generate new hand ID
        old_hand_id = self.state.hand_id
        self.state.hand_id = f"hand_{uuid.uuid4().hex[:12]}"

        # Emit hand end for previous hand
        if old_hand_id is not None:
            self._emit_hand_end()

        # Reset hand-specific state
        self.state.pot_size = 0.0
        self.state.side_pots = []
        self.state.board_cards = []
        self.state.hero_cards = []
        self.state.current_street = "preflop"

        logger.info(f"New hand: {self.state.hand_id}")

    def _emit_street_change(self, previous_street: str, new_street: str):
        """Emit street change event."""
        emit_state_change_event(
            previous_state=previous_street,
            new_state=new_street,
            reason="Board cards changed",
            correlation_id=self._current_correlation_id
        )

        self.state.current_street = new_street
        self._event_count += 1
        logger.info(f"Street change: {previous_street} → {new_street}")

    def _emit_hand_start(self):
        """Emit hand start event."""
        emit_state_change_event(
            previous_state="no_hand",
            new_state="hand_active",
            reason="Hero cards detected",
            correlation_id=self._current_correlation_id
        )

        self._event_count += 1
        logger.info("Hand started")

    def _emit_hand_end(self):
        """Emit hand end event."""
        emit_state_change_event(
            previous_state="hand_active",
            new_state="hand_complete",
            reason="Hand completed",
            correlation_id=self._current_correlation_id
        )

        self._event_count += 1
        logger.info("Hand ended")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get dispatcher statistics.

        Returns:
            Dictionary with event counts and state info.
        """
        return {
            'total_events_emitted': self._event_count,
            'current_hand_id': self.state.hand_id,
            'current_street': self.state.current_street,
            'pot_size': self.state.pot_size,
            'board_card_count': len(self.state.board_cards),
            'hero_card_count': len(self.state.hero_cards),
            'active_players': sum(1 for active in self.state.player_active.values() if active),
            'correlation_id': self._current_correlation_id,
        }


# Global dispatcher instance
_dispatcher: Optional[DetectionStateDispatcher] = None


def get_dispatcher() -> DetectionStateDispatcher:
    """
    Get the global detection state dispatcher.

    Returns:
        Global DetectionStateDispatcher instance.
    """
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = DetectionStateDispatcher()
    return _dispatcher


def reset_dispatcher():
    """Reset the global dispatcher (useful for testing)."""
    global _dispatcher
    _dispatcher = None
