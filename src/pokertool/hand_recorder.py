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
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


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
            seats=list(table_state.seats) if hasattr(table_state, 'seats') else []
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
            from pokertool.hand_history_db import get_hand_history_db, HandHistory, PlayerInfo, GameStage

            if not self.snapshots:
                logger.warning("No snapshots recorded for hand")
                self.state = HandRecorderState.COMPLETED
                return

            # Build hand history from snapshots
            final_snapshot = self.snapshots[-1]

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
            players = []
            if final_snapshot.seats:
                for seat in final_snapshot.seats:
                    player = PlayerInfo(
                        seat_number=seat.seat_number if hasattr(seat, 'seat_number') else 0,
                        player_name=seat.player_name if hasattr(seat, 'player_name') else "Unknown",
                        starting_stack=seat.stack_size if hasattr(seat, 'stack_size') else 0.0,
                        ending_stack=seat.stack_size if hasattr(seat, 'stack_size') else 0.0,
                        position=seat.position if hasattr(seat, 'position') else "",
                        is_hero=seat.is_hero if hasattr(seat, 'is_hero') else False,
                        cards=[],
                        won_amount=0.0
                    )
                    players.append(player)

            # Calculate duration
            duration = (datetime.now() - self.hand_start_time).total_seconds() if self.hand_start_time else 0.0

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
                actions=[],  # TODO: Track actions in future enhancement
                pot_size=max_pot,
                winners=[],  # TODO: Detect winners in future enhancement
                hero_result="unknown",  # TODO: Calculate result
                hero_net=0.0,  # TODO: Calculate net
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
