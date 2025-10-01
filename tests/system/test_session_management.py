"""Tests for the session management utilities."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.session_management import SessionGoal, SessionManager


def create_manager(tmp_path: Path) -> SessionManager:
    storage = tmp_path / "sessions"
    return SessionManager(storage_dir=storage)


def test_session_lifecycle_with_goals_and_breaks(tmp_path):
    manager = create_manager(tmp_path)
    goal = SessionGoal(hands_target=3, profit_target=50, break_interval_minutes=10, max_loss=100, tilt_score_threshold=0.7)
    session_id = manager.start_session("hero", goal)

    metrics = manager.record_hand(session_id, profit=20.0, big_blinds_won=40.0, vpip=True, aggressive=True, duration_seconds=120, tilt_score=0.4)
    assert metrics.hands_played == 1
    assert metrics.total_profit == 20.0

    metrics = manager.record_hand(session_id, profit=-30.0, big_blinds_won=-60.0, vpip=False, aggressive=False, duration_seconds=90, tilt_score=0.8)
    assert metrics.tilt_alerts == 1
    assert manager.detect_tilt(session_id) is False

    metrics = manager.record_hand(session_id, profit=70.0, big_blinds_won=140.0, vpip=True, aggressive=True, duration_seconds=150, tilt_score=0.3)
    assert metrics.hands_played == 3
    assert metrics.total_profit == 60.0

    assert manager.should_take_break(session_id) is True
    manager.record_break(session_id, note="Hydration break")
    assert manager.should_take_break(session_id) is False

    review = manager.complete_session(session_id, final_note="Solid session")
    assert review.achieved_goals["hands_target"] is True
    assert review.achieved_goals["profit_target"] is True
    assert review.metrics.winrate_per_100() > 0


def test_tilt_detection_and_analytics(tmp_path):
    manager = create_manager(tmp_path)
    goal = SessionGoal(hands_target=0, profit_target=0, break_interval_minutes=5, max_loss=50, tilt_score_threshold=0.6)
    session_id = manager.start_session("hero", goal)

    # Simulate consecutive losing hands with high tilt score.
    for _ in range(4):
        manager.record_hand(session_id, profit=-15.0, big_blinds_won=-30.0, vpip=True, aggressive=False, duration_seconds=60, tilt_score=0.9)

    assert manager.detect_tilt(session_id) is True

    analytics = manager.get_session_analytics(session_id)
    assert analytics["hands_played"] == 4
    assert analytics["total_profit"] == -60.0
    assert analytics["tilt_alerts"] >= 1

    active_sessions = manager.get_active_sessions()
    assert session_id in active_sessions
