#!/usr/bin/env python3
"""Tests for Session Manager"""

import pytest
from datetime import datetime, timedelta
from src.pokertool.session_manager import (
    SessionManager,
    SessionStatus,
    Session,
    PlayerSession
)


class TestSessionManager:
    """Test suite for SessionManager"""

    def test_initialization(self):
        """Test manager initialization"""
        manager = SessionManager()
        assert len(manager.sessions) == 0
        assert manager.active_session is None
        assert manager.session_count == 0

    def test_start_session(self):
        """Test starting a session"""
        manager = SessionManager()
        session = manager.start_session(notes="Test session")

        assert session.session_id == 1
        assert session.status == SessionStatus.ACTIVE
        assert session.notes == "Test session"
        assert manager.active_session == session
        assert len(manager.sessions) == 1

    def test_start_multiple_sessions(self):
        """Test starting multiple sessions ends previous"""
        manager = SessionManager()
        session1 = manager.start_session()
        session2 = manager.start_session()

        assert session1.status == SessionStatus.COMPLETED
        assert session1.end_time is not None
        assert session2.status == SessionStatus.ACTIVE
        assert manager.active_session == session2

    def test_end_session(self):
        """Test ending a session"""
        manager = SessionManager()
        session = manager.start_session()
        ended = manager.end_session()

        assert ended == session
        assert session.status == SessionStatus.COMPLETED
        assert session.end_time is not None
        assert manager.active_session is None

    def test_end_session_no_active(self):
        """Test ending session when none active"""
        manager = SessionManager()
        result = manager.end_session()

        assert result is None

    def test_pause_session(self):
        """Test pausing a session"""
        manager = SessionManager()
        session = manager.start_session()
        paused = manager.pause_session()

        assert paused == session
        assert session.status == SessionStatus.PAUSED

    def test_pause_no_active_session(self):
        """Test pausing when no active session"""
        manager = SessionManager()
        result = manager.pause_session()

        assert result is None

    def test_resume_session(self):
        """Test resuming a paused session"""
        manager = SessionManager()
        session = manager.start_session()
        manager.pause_session()
        resumed = manager.resume_session()

        assert resumed == session
        assert session.status == SessionStatus.ACTIVE

    def test_resume_non_paused_session(self):
        """Test resuming a session that's not paused"""
        manager = SessionManager()
        manager.start_session()
        result = manager.resume_session()

        assert result is None

    def test_add_player(self):
        """Test adding player to session"""
        manager = SessionManager()
        manager.start_session()
        player = manager.add_player("Alice", 100.0)

        assert player is not None
        assert player.player_name == "Alice"
        assert player.buy_in == 100.0
        assert player.current_stack == 100.0
        assert player.hands_played == 0
        assert player.hands_won == 0

    def test_add_player_no_session(self):
        """Test adding player when no session"""
        manager = SessionManager()
        result = manager.add_player("Alice", 100.0)

        assert result is None

    def test_add_duplicate_player(self):
        """Test adding same player twice"""
        manager = SessionManager()
        manager.start_session()
        player1 = manager.add_player("Alice", 100.0)
        player2 = manager.add_player("Alice", 200.0)

        assert player1 == player2
        assert player2.buy_in == 100.0  # Original buy-in unchanged

    def test_update_player_stack(self):
        """Test updating player stack"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        success = manager.update_player_stack("Alice", 150.0)

        assert success is True
        player = manager.active_session.players["Alice"]
        assert player.current_stack == 150.0

    def test_update_player_stack_not_found(self):
        """Test updating stack for non-existent player"""
        manager = SessionManager()
        manager.start_session()
        success = manager.update_player_stack("Alice", 150.0)

        assert success is False

    def test_record_hand_result_win(self):
        """Test recording a hand win"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        success = manager.record_hand_result("Alice", won=True)

        assert success is True
        player = manager.active_session.players["Alice"]
        assert player.hands_played == 1
        assert player.hands_won == 1
        assert manager.active_session.total_hands == 1

    def test_record_hand_result_loss(self):
        """Test recording a hand loss"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        success = manager.record_hand_result("Alice", won=False)

        assert success is True
        player = manager.active_session.players["Alice"]
        assert player.hands_played == 1
        assert player.hands_won == 0

    def test_record_hand_result_no_player(self):
        """Test recording hand for non-existent player"""
        manager = SessionManager()
        manager.start_session()
        success = manager.record_hand_result("Alice", won=True)

        assert success is False

    def test_get_player_profit_positive(self):
        """Test getting positive profit"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 150.0)

        profit = manager.get_player_profit("Alice")
        assert profit == 50.0

    def test_get_player_profit_negative(self):
        """Test getting negative profit (loss)"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 75.0)

        profit = manager.get_player_profit("Alice")
        assert profit == -25.0

    def test_get_player_profit_not_found(self):
        """Test getting profit for non-existent player"""
        manager = SessionManager()
        manager.start_session()

        profit = manager.get_player_profit("Alice")
        assert profit is None

    def test_get_session_duration(self):
        """Test getting session duration"""
        manager = SessionManager()
        session = manager.start_session()

        # Simulate some time passing
        import time
        time.sleep(0.1)

        duration = manager.get_session_duration()
        assert duration is not None
        assert duration.total_seconds() >= 0.1

    def test_get_session_duration_completed(self):
        """Test duration for completed session"""
        manager = SessionManager()
        session = manager.start_session()
        import time
        time.sleep(0.1)
        manager.end_session()

        duration = manager.get_session_duration(session.session_id)
        assert duration is not None
        assert duration.total_seconds() >= 0.1

    def test_get_session_stats(self):
        """Test getting session statistics"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.add_player("Bob", 100.0)
        manager.update_player_stack("Alice", 150.0)
        manager.update_player_stack("Bob", 50.0)
        manager.record_hand_result("Alice", won=True)

        stats = manager.get_session_stats()

        assert stats["session_id"] == 1
        assert stats["status"] == "active"
        assert stats["total_players"] == 2
        assert stats["total_hands"] == 1
        assert stats["total_buy_ins"] == 200.0
        assert stats["total_chips"] == 200.0
        assert stats["biggest_winner"] == "Alice"
        assert stats["biggest_profit"] == 50.0

    def test_get_session_stats_no_session(self):
        """Test getting stats when no session"""
        manager = SessionManager()
        stats = manager.get_session_stats()

        assert stats is None

    def test_get_player_stats(self):
        """Test getting player statistics"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 150.0)
        manager.record_hand_result("Alice", won=True)
        manager.record_hand_result("Alice", won=False)

        stats = manager.get_player_stats("Alice")

        assert stats["player_name"] == "Alice"
        assert stats["buy_in"] == 100.0
        assert stats["current_stack"] == 150.0
        assert stats["profit"] == 50.0
        assert stats["hands_played"] == 2
        assert stats["hands_won"] == 1
        assert stats["win_rate"] == 50.0

    def test_get_player_stats_no_hands(self):
        """Test player stats with no hands played"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)

        stats = manager.get_player_stats("Alice")

        assert stats["hands_played"] == 0
        assert stats["hands_won"] == 0
        assert stats["win_rate"] == 0.0

    def test_get_player_stats_not_found(self):
        """Test getting stats for non-existent player"""
        manager = SessionManager()
        manager.start_session()

        stats = manager.get_player_stats("Alice")
        assert stats is None

    def test_get_all_sessions(self):
        """Test getting all sessions"""
        manager = SessionManager()
        manager.start_session()
        manager.end_session()
        manager.start_session()

        sessions = manager.get_all_sessions()
        assert len(sessions) == 2

    def test_get_session_by_id(self):
        """Test getting session by ID"""
        manager = SessionManager()
        session1 = manager.start_session()
        manager.end_session()
        session2 = manager.start_session()

        found = manager.get_session_by_id(1)
        assert found == session1
        assert found.session_id == 1

    def test_get_session_by_id_not_found(self):
        """Test getting non-existent session"""
        manager = SessionManager()
        found = manager.get_session_by_id(999)

        assert found is None

    def test_get_active_session(self):
        """Test getting active session"""
        manager = SessionManager()
        session = manager.start_session()

        active = manager.get_active_session()
        assert active == session

    def test_get_active_session_none(self):
        """Test getting active session when none"""
        manager = SessionManager()
        active = manager.get_active_session()

        assert active is None

    def test_get_completed_sessions(self):
        """Test getting completed sessions"""
        manager = SessionManager()
        manager.start_session()
        manager.end_session()
        manager.start_session()
        manager.end_session()
        manager.start_session()

        completed = manager.get_completed_sessions()
        assert len(completed) == 2
        assert all(s.status == SessionStatus.COMPLETED for s in completed)

    def test_get_total_profit_all_sessions(self):
        """Test total profit across all sessions"""
        manager = SessionManager()

        # Session 1
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 150.0)
        manager.end_session()

        # Session 2
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 175.0)
        manager.end_session()

        total_profit = manager.get_total_profit_all_sessions("Alice")
        assert total_profit == 125.0  # 50 + 75

    def test_get_total_profit_with_losses(self):
        """Test total profit with winning and losing sessions"""
        manager = SessionManager()

        # Session 1: Win
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 150.0)
        manager.end_session()

        # Session 2: Loss
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.update_player_stack("Alice", 75.0)
        manager.end_session()

        total_profit = manager.get_total_profit_all_sessions("Alice")
        assert total_profit == 25.0  # 50 - 25

    def test_session_id_increment(self):
        """Test session IDs increment correctly"""
        manager = SessionManager()
        s1 = manager.start_session()
        manager.end_session()
        s2 = manager.start_session()
        manager.end_session()
        s3 = manager.start_session()

        assert s1.session_id == 1
        assert s2.session_id == 2
        assert s3.session_id == 3

    def test_multiple_players_session(self):
        """Test session with multiple players"""
        manager = SessionManager()
        manager.start_session()

        manager.add_player("Alice", 100.0)
        manager.add_player("Bob", 100.0)
        manager.add_player("Charlie", 100.0)

        manager.update_player_stack("Alice", 150.0)
        manager.update_player_stack("Bob", 100.0)
        manager.update_player_stack("Charlie", 50.0)

        stats = manager.get_session_stats()
        assert stats["total_players"] == 3
        assert stats["total_buy_ins"] == 300.0
        assert stats["biggest_winner"] == "Alice"

    def test_add_player_to_specific_session(self):
        """Test adding player to specific session by ID"""
        manager = SessionManager()
        session1 = manager.start_session()
        manager.end_session()
        session2 = manager.start_session()

        # Add to old session by ID
        player = manager.add_player("Alice", 100.0, session_id=session1.session_id)

        assert player is not None
        assert "Alice" in session1.players
        assert "Alice" not in session2.players

    def test_reset_functionality(self):
        """Test reset clears all data"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.end_session()

        assert len(manager.sessions) == 1

        manager.reset()

        assert len(manager.sessions) == 0
        assert manager.active_session is None
        assert manager.session_count == 0

    def test_session_with_notes(self):
        """Test session notes are preserved"""
        manager = SessionManager()
        session = manager.start_session(notes="Friday night poker")

        assert session.notes == "Friday night poker"

    def test_player_win_rate_100_percent(self):
        """Test player with 100% win rate"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.record_hand_result("Alice", won=True)
        manager.record_hand_result("Alice", won=True)

        stats = manager.get_player_stats("Alice")
        assert stats["win_rate"] == 100.0

    def test_player_win_rate_0_percent(self):
        """Test player with 0% win rate"""
        manager = SessionManager()
        manager.start_session()
        manager.add_player("Alice", 100.0)
        manager.record_hand_result("Alice", won=False)
        manager.record_hand_result("Alice", won=False)

        stats = manager.get_player_stats("Alice")
        assert stats["win_rate"] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
