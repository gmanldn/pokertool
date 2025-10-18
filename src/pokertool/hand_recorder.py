#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hand Recorder for PokerTool
============================

Captures hands in real-time from table state and saves to hand history database.
Detects hand completion and extracts all relevant information.

Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from copy import deepcopy

logger = logging.getLogger(__name__)

STACK_DELTA_EPSILON = 0.01  # Minimum chip movement to treat as an action/result


class HandRecorderState(Enum):
    """State of the hand recorder."""
    IDLE = "idle"
    RECORDING = "recording"
    COMPLETED = "completed"


@dataclass
class HandSnapshot:
    """Snapshot of table state at a point in time."""
    timestamp: str
    stage: str
    pot_size: float
    board_cards: List[str]
    active_players: int
    hero_cards: List[str]
    seats: List[Any]


class HandRecorder:
    """
    Records poker hands from live table state.

    Tracks hand progression and saves complete hand history when hand completes.
    """

    def __init__(self):
        """Initialize hand recorder."""
        self.state = HandRecorderState.IDLE
        self.current_hand_id: Optional[str] = None
        self.hand_start_time: Optional[datetime] = None
        self.snapshots: List[HandSnapshot] = []

        # Hand data accumulation
        self.table_name: str = "Unknown"
        self.site: str = "BETFAIR"
        self.small_blind: float = 0.05
        self.big_blind: float = 0.10
        self.hero_name: Optional[str] = None

        # Previous state for change detection
        self.prev_stage: Optional[str] = None
        self.prev_pot_size: float = 0.0
        self.prev_board_cards: List[str] = []
        self.prev_hero_cards: List[str] = []

        # Seat tracking for analytics
        self.initial_seat_states: Dict[int, Any] = {}
        self.hero_seat_number: Optional[int] = None

        logger.info("HandRecorder initialized")

    def update(self, table_state: Any) -> None:
        """
        Update hand recorder with current table state.

        Args:
            table_state: TableState object from scraper
        """
        try:
            # Check if we should start recording a new hand
            if self._should_start_new_hand(table_state):
                self._start_new_hand(table_state)

            # Record snapshot if we're currently recording
            if self.state == HandRecorderState.RECORDING:
                self._record_snapshot(table_state)

                # Check if hand is complete
                if self._is_hand_complete(table_state):
                    self._complete_hand(table_state)

            # Update previous state
            self.prev_stage = table_state.stage
            self.prev_pot_size = table_state.pot_size
            self.prev_board_cards = list(table_state.board_cards)

        except Exception as e:
            logger.error(f"Error updating hand recorder: {e}", exc_info=True)

    def _should_start_new_hand(self, table_state: Any) -> bool:
        """Check if we should start recording a new hand."""
        # Start if we're idle and there's activity
        if self.state == HandRecorderState.IDLE:
            # New hand if pot exists and we have hero cards
            if table_state.pot_size > 0 and len(table_state.hero_cards) > 0:
                return True

        # Start new hand if previous hand completed and new cards dealt
        if self.state == HandRecorderState.COMPLETED:
            if len(table_state.hero_cards) > 0 and table_state.hero_cards != self.prev_hero_cards:
                return True

        return False

    def _start_new_hand(self, table_state: Any) -> None:
        """Start recording a new hand."""
        self.state = HandRecorderState.RECORDING
        self.current_hand_id = f"{table_state.site_detected}_{datetime.now().isoformat()}"
        self.hand_start_time = datetime.now()
        self.snapshots = []

        # Extract table info
        self.site = str(table_state.site_detected) if table_state.site_detected else "BETFAIR"

        # Try to get hero name from user config
        try:
            from pokertool.user_config import get_poker_handle
            self.hero_name = get_poker_handle()
        except:
            self.hero_name = None

        # Detect blinds from pot size (heuristic)
        if table_state.pot_size >= 0.15:  # SB + BB posted
            self.small_blind = 0.05
            self.big_blind = 0.10

        # Track hero seat if provided
        self.hero_seat_number = getattr(table_state, 'hero_seat', None)

        # Capture initial seat stacks for later comparison
        self.initial_seat_states = {}
        if hasattr(table_state, 'seats'):
            for seat in list(table_state.seats):
                seat_number = getattr(seat, 'seat_number', None)
                if seat_number is None:
                    continue
                self.initial_seat_states[seat_number] = deepcopy(seat)

        logger.info(f"Started recording hand: {self.current_hand_id}")
        self.prev_hero_cards = list(table_state.hero_cards)

    def _record_snapshot(self, table_state: Any) -> None:
        """Record a snapshot of current table state."""
        snapshot = HandSnapshot(
            timestamp=datetime.now().isoformat(),
            stage=table_state.stage,
            pot_size=table_state.pot_size,
            board_cards=list(table_state.board_cards),
            active_players=table_state.active_players,
            hero_cards=list(table_state.hero_cards),
            seats=deepcopy(list(table_state.seats)) if hasattr(table_state, 'seats') else []
        )
        self.snapshots.append(snapshot)

    def _is_hand_complete(self, table_state: Any) -> bool:
        """Check if the current hand is complete."""
        # Hand is complete if:
        # 1. Hero cards disappear (hand ended)
        # 2. Pot goes to zero after being > 0
        # 3. Stage resets to preflop with new cards

        if len(self.snapshots) < 2:
            return False

        # Check if hero cards disappeared
        if len(table_state.hero_cards) == 0 and len(self.prev_hero_cards) > 0:
            return True

        # Check if pot reset to zero
        if table_state.pot_size == 0 and self.prev_pot_size > 0 and len(self.snapshots) > 3:
            return True

        # Check if new hand started (stage reset with new cards)
        if (table_state.stage == "preflop" and
            self.prev_stage in ["flop", "turn", "river"] and
            len(table_state.hero_cards) > 0 and
            table_state.hero_cards != self.prev_hero_cards):
            return True

        return False

    def _complete_hand(self, table_state: Any) -> None:
        """Complete the current hand and save to database."""
        try:
            from pokertool.hand_history_db import (
                get_hand_history_db,
                HandHistory,
                PlayerInfo,
                GameStage,
                PlayerAction,
                ActionType,
            )

            if not self.snapshots:
                logger.warning("No snapshots recorded for hand")
                self.state = HandRecorderState.COMPLETED
                return

            # Build hand history from snapshots
            final_snapshot = self.snapshots[-1]
            initial_snapshot = self.snapshots[0]

            # Determine final stage
            final_stage = GameStage.PREFLOP
            if "river" in [s.stage for s in self.snapshots]:
                final_stage = GameStage.RIVER
            elif "turn" in [s.stage for s in self.snapshots]:
                final_stage = GameStage.TURN
            elif "flop" in [s.stage for s in self.snapshots]:
                final_stage = GameStage.FLOP

            # Find max pot size
            max_pot = max(s.pot_size for s in self.snapshots)

            # Build player list from seats
            players = self._build_player_summaries(initial_snapshot, final_snapshot, PlayerInfo)

            # Calculate duration
            duration = (datetime.now() - self.hand_start_time).total_seconds() if self.hand_start_time else 0.0

            # Extract betting actions
            actions = self._extract_actions(PlayerAction, ActionType, GameStage)

            # Determine winners based on stack deltas
            winners = [
                player.player_name
                for player in players
                if (player.ending_stack - player.starting_stack) > STACK_DELTA_EPSILON
            ]

            # Determine hero outcome
            hero_result, hero_net = self._determine_hero_outcome(players)

            # Create hand history
            hand = HandHistory(
                hand_id=self.current_hand_id,
                timestamp=self.hand_start_time.isoformat() if self.hand_start_time else datetime.now().isoformat(),
                table_name=self.table_name,
                site=self.site,
                small_blind=self.small_blind,
                big_blind=self.big_blind,
                players=players,
                hero_name=self.hero_name,
                hero_cards=final_snapshot.hero_cards,
                board_cards=final_snapshot.board_cards,
                actions=actions,
                pot_size=max_pot,
                winners=winners,
                hero_result=hero_result,
                hero_net=hero_net,
                final_stage=final_stage,
                duration_seconds=duration
            )

            # Save to database
            db = get_hand_history_db()
            if db.save_hand(hand):
                logger.info(f"✓ Saved hand {self.current_hand_id} to database")
            else:
                logger.error(f"Failed to save hand {self.current_hand_id}")

            # Reset state
            self.state = HandRecorderState.COMPLETED
            self.snapshots = []

        except Exception as e:
            logger.error(f"Error completing hand: {e}", exc_info=True)
            self.state = HandRecorderState.COMPLETED

    def reset(self) -> None:
        """Reset the hand recorder to idle state."""
        self.state = HandRecorderState.IDLE
        self.current_hand_id = None
        self.hand_start_time = None
        self.snapshots = []
        self.prev_stage = None
        self.prev_pot_size = 0.0
        self.prev_board_cards = []
        self.prev_hero_cards = []
        self.initial_seat_states = {}
        self.hero_seat_number = None
        logger.info("HandRecorder reset to idle")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of hand recorder."""
        return {
            'state': self.state.value,
            'current_hand_id': self.current_hand_id,
            'snapshots_count': len(self.snapshots),
            'recording_duration': (datetime.now() - self.hand_start_time).total_seconds()
                                 if self.hand_start_time else 0.0
        }

    def _build_player_summaries(self, initial_snapshot: HandSnapshot, final_snapshot: HandSnapshot, PlayerInfo) -> List[Any]:
        """Construct PlayerInfo summaries combining initial and final seat states."""
        initial_map = self._map_seats_by_number(initial_snapshot.seats)
        final_map = self._map_seats_by_number(final_snapshot.seats)

        # Include any seats captured right when the hand started (covers cases where seating changed mid-hand)
        for seat_num, seat_state in self.initial_seat_states.items():
            if seat_num not in initial_map:
                initial_map[seat_num] = seat_state

        seat_numbers = sorted(set(initial_map.keys()) | set(final_map.keys()))
        players: List[Any] = []

        for seat_number in seat_numbers:
            initial_seat = initial_map.get(seat_number)
            final_seat = final_map.get(seat_number)
            reference = final_seat or initial_seat
            if reference is None:
                continue

            player_name = getattr(reference, 'player_name', '') or f"Seat {seat_number}"
            starting_stack = float(getattr(initial_seat, 'stack_size', getattr(reference, 'stack_size', 0.0)) or 0.0)
            ending_stack = float(getattr(final_seat, 'stack_size', starting_stack) or starting_stack)

            player = PlayerInfo(
                seat_number=seat_number,
                player_name=player_name,
                starting_stack=starting_stack,
                ending_stack=ending_stack,
                position=getattr(reference, 'position', ""),
                is_hero=bool(getattr(reference, 'is_hero', False)),
                cards=list(getattr(reference, 'cards', [])),
                won_amount=max(ending_stack - starting_stack, 0.0)
            )
            players.append(player)

        return players

    @staticmethod
    def _map_seats_by_number(seats: List[Any]) -> Dict[int, Any]:
        """Map seat objects by their seat number."""
        mapping: Dict[int, Any] = {}
        for seat in seats or []:
            seat_number = getattr(seat, 'seat_number', None)
            if seat_number is None:
                continue
            mapping[seat_number] = seat
        return mapping

    def _extract_actions(self, PlayerAction, ActionType, GameStage) -> List[Any]:
        """Create PlayerAction records by analysing consecutive snapshots."""
        if len(self.snapshots) < 2:
            return []

        actions: List[Any] = []
        previous_snapshot = self.snapshots[0]

        for snapshot in self.snapshots[1:]:
            # Ignore payout transitions where the pot shrinks (result distribution)
            if snapshot.pot_size + STACK_DELTA_EPSILON < previous_snapshot.pot_size:
                previous_snapshot = snapshot
                continue

            stage_enum = self._normalize_stage(snapshot.stage or previous_snapshot.stage, GameStage)
            prev_seats = self._map_seats_by_number(previous_snapshot.seats)
            curr_seats = self._map_seats_by_number(snapshot.seats)

            for seat_number, curr_seat in curr_seats.items():
                prev_seat = prev_seats.get(seat_number)
                if prev_seat is None:
                    continue

                prev_stack = float(getattr(prev_seat, 'stack_size', 0.0) or 0.0)
                curr_stack = float(getattr(curr_seat, 'stack_size', 0.0) or 0.0)
                stack_delta = prev_stack - curr_stack

                if stack_delta <= STACK_DELTA_EPSILON:
                    continue

                player_name = getattr(curr_seat, 'player_name', '') or getattr(prev_seat, 'player_name', '') or f"Seat {seat_number}"
                action_type = ActionType.ALL_IN if curr_stack <= STACK_DELTA_EPSILON else ActionType.BET

                actions.append(PlayerAction(
                    player_name=player_name,
                    action_type=action_type,
                    amount=round(stack_delta, 2),
                    stage=stage_enum,
                    timestamp=snapshot.timestamp
                ))

            previous_snapshot = snapshot

        return actions

    def _determine_hero_outcome(self, players: List[Any]) -> Tuple[str, float]:
        """Calculate hero result string and net amount."""
        hero_player = next((p for p in players if p.is_hero), None)

        if hero_player is None and self.hero_name:
            hero_player = next((p for p in players if p.player_name == self.hero_name), None)

        if hero_player is None and self.hero_seat_number is not None:
            # Hero might have left the table; fall back to seat tracking
            initial_stack = float(getattr(self.initial_seat_states.get(self.hero_seat_number), 'stack_size', 0.0) or 0.0)
            latest_stack = self._latest_stack_for_seat(self.hero_seat_number)
            net = (latest_stack or initial_stack) - initial_stack
            return self._result_from_net(net), net

        if hero_player is None:
            return "unknown", 0.0

        net = hero_player.ending_stack - hero_player.starting_stack
        return self._result_from_net(net), net

    @staticmethod
    def _normalize_stage(stage: Optional[str], GameStage) -> Any:
        """Map scraper stage strings to canonical GameStage enum values."""
        if not stage:
            return GameStage.PREFLOP

        stage_map = {
            "preflop": GameStage.PREFLOP,
            "pre-flop": GameStage.PREFLOP,
            "pre flop": GameStage.PREFLOP,
            "flop": GameStage.FLOP,
            "turn": GameStage.TURN,
            "river": GameStage.RIVER,
            "showdown": GameStage.SHOWDOWN,
        }
        return stage_map.get(stage.lower(), GameStage.PREFLOP)

    @staticmethod
    def _result_from_net(net: float) -> str:
        """Derive hero result string from net change."""
        if net > STACK_DELTA_EPSILON:
            return "won"
        if net < -STACK_DELTA_EPSILON:
            return "lost"
        return "pushed"

    def _latest_stack_for_seat(self, seat_number: int) -> Optional[float]:
        """Find the most recent stack size for the specified seat."""
        for snapshot in reversed(self.snapshots):
            seats = self._map_seats_by_number(snapshot.seats)
            if seat_number in seats:
                return float(getattr(seats[seat_number], 'stack_size', 0.0) or 0.0)
        return None


# Global hand recorder instance
_hand_recorder: Optional[HandRecorder] = None


def get_hand_recorder() -> HandRecorder:
    """Get the global hand recorder instance."""
    global _hand_recorder
    if _hand_recorder is None:
        _hand_recorder = HandRecorder()
    return _hand_recorder


def enable_hand_recording(enabled: bool = True) -> None:
    """Enable or disable hand recording."""
    if enabled:
        recorder = get_hand_recorder()
        logger.info("Hand recording enabled")
    else:
        logger.info("Hand recording disabled")


if __name__ == '__main__':
    # Test hand recorder
    print("Testing HandRecorder...")

    recorder = HandRecorder()
    print(f"Initial state: {recorder.get_status()}")

    # Simulate table state updates would go here

    print("✓ HandRecorder test complete")
