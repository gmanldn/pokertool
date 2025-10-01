"""Tests for the tournament tracker utilities."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.tournament_tracker import (
    TournamentEvent,
    TournamentResult,
    TournamentStructure,
    TournamentTracker,
)


def create_tracker(tmp_path: Path) -> TournamentTracker:
    storage = tmp_path / "tournaments"
    return TournamentTracker(storage_dir=storage)


def build_sample_event(start_time: float) -> TournamentEvent:
    structure = TournamentStructure(
        starting_stack=30000,
        blind_interval_minutes=20,
        average_field_size=550,
        late_reg_minutes=150,
        reentry_allowed=True,
    )
    return TournamentEvent(
        event_id="main_event",
        name="Sunday Major",
        start_time=start_time,
        buy_in=109.0,
        rake=9.0,
        prize_pool=75000.0,
        structure=structure,
        tags=["major", "online"],
    )


def test_scheduler_late_registration_and_alerts(tmp_path):
    tracker = create_tracker(tmp_path)
    start_time = time.time() + 4 * 3600
    event = build_sample_event(start_time)
    tracker.add_event(event)

    upcoming = tracker.upcoming_events(within_hours=5)
    assert upcoming and upcoming[0].event_id == "main_event"

    advice = tracker.late_registration_advice("main_event", current_time=time.time() + 60)
    assert "Late registration open" in advice
    assert "Re-entry" in advice

    alert = tracker.schedule_alert("main_event", minutes_before=120)
    due = tracker.due_alerts(current_time=alert.trigger_time + 1)
    assert any(a.event_id == "main_event" for a in due)
    for a in due:
        tracker.mark_alert_delivered(a)
    assert not tracker.due_alerts(current_time=alert.trigger_time + 120)


def test_roi_and_satellite_tracking(tmp_path):
    tracker = create_tracker(tmp_path)
    start_time = time.time() + 86400
    main_event = build_sample_event(start_time)
    tracker.add_event(main_event)

    tracker.link_satellite("satellite_1", "main_event", seats_awarded=2)
    satellites = tracker.satellites_for_event("main_event")
    assert satellites and satellites[0].satellite_event_id == "satellite_1"

    result = TournamentResult(event_id="main_event", finish_position=1, payout=1500.0, total_entries=600)
    tracker.record_result(result)
    roi = tracker.roi_summary()
    assert roi["events"] == 1
    assert roi["investment"] == 118.0
    assert roi["roi"] > 0
