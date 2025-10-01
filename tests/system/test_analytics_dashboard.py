"""Tests for the analytics dashboard module."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.analytics_dashboard import AnalyticsDashboard, PrivacySettings, UsageEvent


def create_dashboard(tmp_path: Path) -> AnalyticsDashboard:
    storage = tmp_path / "analytics"
    return AnalyticsDashboard(storage_dir=storage, privacy=PrivacySettings(anonymize_user_ids=True, collect_detailed_events=True, data_retention_days=60))


def test_event_tracking_and_metrics(tmp_path):
    dashboard = create_dashboard(tmp_path)
    dashboard.track_event(UsageEvent(event_id="e1", user_id="userA", action="login", metadata={"device": "mac"}))
    dashboard.track_event(UsageEvent(event_id="e2", user_id="userA", action="analyze_hand", metadata={"hand_id": "h1"}))
    dashboard.track_event(UsageEvent(event_id="e3", user_id="userB", action="export_report", metadata={}))

    dashboard.track_session("userA", 45.0)
    dashboard.track_session("userB", 30.0)

    metrics = dashboard.generate_metrics()
    assert metrics.total_events == 3
    assert metrics.active_users == 2
    assert metrics.most_common_actions[0] in {"login", "analyze_hand", "export_report"}
    assert metrics.avg_session_length_minutes > 0

    report_path = dashboard.export_report("usage.json")
    assert report_path.exists()


def test_privacy_controls_skip_detailed_events(tmp_path):
    dashboard = AnalyticsDashboard(storage_dir=tmp_path / "analytics2", privacy=PrivacySettings(anonymize_user_ids=False, collect_detailed_events=False))
    dashboard.track_event(UsageEvent(event_id="e1", user_id="userA", action="login", metadata={}))
    dashboard.track_event(UsageEvent(event_id="e2", user_id="userA", action="analyze_hand", metadata={}))

    metrics = dashboard.generate_metrics()
    assert metrics.total_events == 1
    assert metrics.active_users == 1
