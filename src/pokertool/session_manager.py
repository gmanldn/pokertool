#!/usr/bin/env python3
"""
Session Manager
==============

Manages poker playing sessions with tracking and statistics.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


@dataclass
class PlayerSession:
    """Player's session data"""
    player_name: str
    buy_in: float
    current_stack: float
    hands_played: int = 0
    hands_won: int = 0


@dataclass
class Session:
    """Poker session"""
    session_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SessionStatus = SessionStatus.ACTIVE
    players: Dict[str, PlayerSession] = field(default_factory=dict)
    total_hands: int = 0
    notes: str = ""


class SessionManager:
    """Manages poker playing sessions."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: List[Session] = []
        self.active_session: Optional[Session] = None
        self.session_count = 0

    def start_session(self, notes: str = "") -> Session:
        """
        Start a new session.

        Args:
            notes: Optional session notes

        Returns:
            Created Session object
        """
        if self.active_session:
            logger.warning("Already have active session, ending it first")
            self.end_session()

        self.session_count += 1
        session = Session(
            session_id=self.session_count,
            start_time=datetime.now(),
            notes=notes
        )
        self.active_session = session
        self.sessions.append(session)

        logger.info(f"Started session {session.session_id}")
        return session

    def end_session(self) -> Optional[Session]:
        """
        End the active session.

        Returns:
            Ended session, or None if no active session
        """
        if not self.active_session:
            logger.warning("No active session to end")
            return None

        self.active_session.end_time = datetime.now()
        self.active_session.status = SessionStatus.COMPLETED

        ended_session = self.active_session
        self.active_session = None

        logger.info(f"Ended session {ended_session.session_id}")
        return ended_session

    def pause_session(self) -> Optional[Session]:
        """
        Pause the active session.

        Returns:
            Paused session, or None if no active session
        """
        if not self.active_session:
            logger.warning("No active session to pause")
            return None

        self.active_session.status = SessionStatus.PAUSED
        logger.info(f"Paused session {self.active_session.session_id}")
        return self.active_session

    def resume_session(self) -> Optional[Session]:
        """
        Resume a paused session.

        Returns:
            Resumed session, or None if no paused session
        """
        if not self.active_session:
            logger.warning("No session to resume")
            return None

        if self.active_session.status != SessionStatus.PAUSED:
            logger.warning("Active session is not paused")
            return None

        self.active_session.status = SessionStatus.ACTIVE
        logger.info(f"Resumed session {self.active_session.session_id}")
        return self.active_session

    def add_player(
        self,
        player_name: str,
        buy_in: float,
        session_id: Optional[int] = None
    ) -> Optional[PlayerSession]:
        """
        Add player to session.

        Args:
            player_name: Player identifier
            buy_in: Initial buy-in amount
            session_id: Session ID (uses active session if None)

        Returns:
            PlayerSession object, or None if session not found
        """
        session = self._get_session(session_id)
        if not session:
            logger.warning("No session found to add player")
            return None

        if player_name in session.players:
            logger.warning(f"Player {player_name} already in session")
            return session.players[player_name]

        player_session = PlayerSession(
            player_name=player_name,
            buy_in=buy_in,
            current_stack=buy_in
        )
        session.players[player_name] = player_session

        logger.info(f"Added {player_name} to session {session.session_id}")
        return player_session

    def update_player_stack(
        self,
        player_name: str,
        new_stack: float,
        session_id: Optional[int] = None
    ) -> bool:
        """
        Update player's stack size.

        Args:
            player_name: Player identifier
            new_stack: New stack amount
            session_id: Session ID (uses active session if None)

        Returns:
            True if updated, False otherwise
        """
        session = self._get_session(session_id)
        if not session or player_name not in session.players:
            logger.warning(f"Player {player_name} not found in session")
            return False

        session.players[player_name].current_stack = new_stack
        return True

    def record_hand_result(
        self,
        player_name: str,
        won: bool,
        session_id: Optional[int] = None
    ) -> bool:
        """
        Record hand result for player.

        Args:
            player_name: Player identifier
            won: Whether player won the hand
            session_id: Session ID (uses active session if None)

        Returns:
            True if recorded, False otherwise
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if player_name not in session.players:
            logger.warning(f"Player {player_name} not in session")
            return False

        player = session.players[player_name]
        player.hands_played += 1
        if won:
            player.hands_won += 1

        session.total_hands += 1
        return True

    def get_player_profit(
        self,
        player_name: str,
        session_id: Optional[int] = None
    ) -> Optional[float]:
        """
        Get player's profit/loss.

        Args:
            player_name: Player identifier
            session_id: Session ID (uses active session if None)

        Returns:
            Profit amount (negative for loss), or None if not found
        """
        session = self._get_session(session_id)
        if not session or player_name not in session.players:
            return None

        player = session.players[player_name]
        profit = player.current_stack - player.buy_in
        return round(profit, 2)

    def get_session_duration(self, session_id: Optional[int] = None) -> Optional[timedelta]:
        """
        Get session duration.

        Args:
            session_id: Session ID (uses active session if None)

        Returns:
            Duration as timedelta, or None if session not found
        """
        session = self._get_session(session_id)
        if not session:
            return None

        end_time = session.end_time or datetime.now()
        return end_time - session.start_time

    def get_session_stats(self, session_id: Optional[int] = None) -> Optional[Dict[str, any]]:
        """
        Get comprehensive session statistics.

        Args:
            session_id: Session ID (uses active session if None)

        Returns:
            Statistics dictionary, or None if session not found
        """
        session = self._get_session(session_id)
        if not session:
            return None

        duration = self.get_session_duration(session_id)
        total_buy_ins = sum(p.buy_in for p in session.players.values())
        total_stacks = sum(p.current_stack for p in session.players.values())

        # Find biggest winner
        biggest_winner = None
        biggest_profit = float('-inf')
        for player_name in session.players:
            profit = self.get_player_profit(player_name, session_id)
            if profit and profit > biggest_profit:
                biggest_profit = profit
                biggest_winner = player_name

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "duration_minutes": int(duration.total_seconds() / 60) if duration else 0,
            "total_players": len(session.players),
            "total_hands": session.total_hands,
            "total_buy_ins": round(total_buy_ins, 2),
            "total_chips": round(total_stacks, 2),
            "biggest_winner": biggest_winner,
            "biggest_profit": round(biggest_profit, 2) if biggest_profit != float('-inf') else 0.0
        }

    def get_player_stats(
        self,
        player_name: str,
        session_id: Optional[int] = None
    ) -> Optional[Dict[str, any]]:
        """
        Get player statistics for a session.

        Args:
            player_name: Player identifier
            session_id: Session ID (uses active session if None)

        Returns:
            Player statistics dictionary, or None if not found
        """
        session = self._get_session(session_id)
        if not session or player_name not in session.players:
            return None

        player = session.players[player_name]
        profit = self.get_player_profit(player_name, session_id)
        win_rate = (player.hands_won / player.hands_played * 100) if player.hands_played > 0 else 0.0

        return {
            "player_name": player.player_name,
            "buy_in": player.buy_in,
            "current_stack": player.current_stack,
            "profit": profit,
            "hands_played": player.hands_played,
            "hands_won": player.hands_won,
            "win_rate": round(win_rate, 2)
        }

    def get_all_sessions(self) -> List[Session]:
        """Get all sessions."""
        return self.sessions

    def get_session_by_id(self, session_id: int) -> Optional[Session]:
        """Get session by ID."""
        for session in self.sessions:
            if session.session_id == session_id:
                return session
        return None

    def get_active_session(self) -> Optional[Session]:
        """Get currently active session."""
        return self.active_session

    def get_completed_sessions(self) -> List[Session]:
        """Get all completed sessions."""
        return [s for s in self.sessions if s.status == SessionStatus.COMPLETED]

    def get_total_profit_all_sessions(self, player_name: str) -> float:
        """
        Get player's total profit across all sessions.

        Args:
            player_name: Player identifier

        Returns:
            Total profit across all sessions
        """
        total = 0.0
        for session in self.sessions:
            if player_name in session.players:
                profit = self.get_player_profit(player_name, session.session_id)
                if profit:
                    total += profit

        return round(total, 2)

    def reset(self):
        """Reset manager."""
        self.sessions.clear()
        self.active_session = None
        self.session_count = 0

    def _get_session(self, session_id: Optional[int] = None) -> Optional[Session]:
        """Get session by ID or active session."""
        if session_id is not None:
            return self.get_session_by_id(session_id)
        return self.active_session


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    manager = SessionManager()

    # Start session
    session = manager.start_session(notes="Friday night game")

    # Add players
    manager.add_player("Alice", 100.0)
    manager.add_player("Bob", 100.0)

    # Play some hands
    manager.record_hand_result("Alice", won=True)
    manager.update_player_stack("Alice", 150.0)
    manager.record_hand_result("Bob", won=False)
    manager.update_player_stack("Bob", 50.0)

    # Get stats
    alice_stats = manager.get_player_stats("Alice")
    print(f"\nAlice's stats:")
    print(f"  Profit: ${alice_stats['profit']}")
    print(f"  Win rate: {alice_stats['win_rate']}%")

    session_stats = manager.get_session_stats()
    print(f"\nSession stats:")
    print(f"  Duration: {session_stats['duration_minutes']} minutes")
    print(f"  Biggest winner: {session_stats['biggest_winner']}")

    manager.end_session()
