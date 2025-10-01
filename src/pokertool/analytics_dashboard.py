"""Usage analytics collection and dashboard summarisation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_ANALYTICS_DIR = Path.home() / ".pokertool" / "analytics"
DEFAULT_ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class UsageEvent:
    """Single usage event for analytics tracking."""

    event_id: str
    user_id: str
    action: str
    metadata: Dict[str, str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class PrivacySettings:
    """Privacy controls for analytics."""

    anonymize_user_ids: bool = True
    collect_detailed_events: bool = True
    data_retention_days: int = 30


@dataclass
class DashboardMetrics:
    """Aggregated analytics metrics."""

    total_events: int
    active_users: int
    actions_per_user: Dict[str, int]
    most_common_actions: List[str]
    avg_session_length_minutes: float


class AnalyticsDashboard:
    """Collects usage events and produces dashboard reports."""

    def __init__(self, storage_dir: Path = DEFAULT_ANALYTICS_DIR, privacy: Optional[PrivacySettings] = None):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.privacy = privacy or PrivacySettings()
        self.events: List[UsageEvent] = []
        self.session_lengths: Dict[str, List[float]] = {}
        self._data_file = self.storage_dir / 'analytics_data.json'
        self._load_history()

    # ------------------------------------------------------------------
    # Event capture
    # ------------------------------------------------------------------
    def track_event(self, event: UsageEvent) -> None:
        if not self.privacy.collect_detailed_events and event.action not in {"login", "logout"}:
            return
        if self.privacy.anonymize_user_ids:
            event.user_id = self._anonymize(event.user_id)
        self.events.append(event)
        self._persist()

    def track_session(self, user_id: str, session_minutes: float) -> None:
        user_id = self._anonymize(user_id) if self.privacy.anonymize_user_ids else user_id
        self.session_lengths.setdefault(user_id, []).append(session_minutes)
        self._persist()

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def generate_metrics(self) -> DashboardMetrics:
        total_events = len(self.events)
        users = {event.user_id for event in self.events}
        actions_per_user: Dict[str, int] = {}
        action_counts: Dict[str, int] = {}
        for event in self.events:
            actions_per_user[event.user_id] = actions_per_user.get(event.user_id, 0) + 1
            action_counts[event.action] = action_counts.get(event.action, 0) + 1
        common_actions = sorted(action_counts, key=action_counts.get, reverse=True)[:5]
        avg_session = self._average_session_length()
        return DashboardMetrics(
            total_events=total_events,
            active_users=len(users),
            actions_per_user=actions_per_user,
            most_common_actions=common_actions,
            avg_session_length_minutes=avg_session,
        )

    def export_report(self, filename: str = "usage_report.json") -> Path:
        path = self.storage_dir / filename
        metrics = self.generate_metrics()
        payload = {
            "metrics": {
                "total_events": metrics.total_events,
                "active_users": metrics.active_users,
                "most_common_actions": metrics.most_common_actions,
                "avg_session_length_minutes": metrics.avg_session_length_minutes,
            },
            "privacy": self.privacy.__dict__,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _average_session_length(self) -> float:
        if not self.session_lengths:
            return 0.0
        lengths = [length for sessions in self.session_lengths.values() for length in sessions]
        return round(sum(lengths) / len(lengths), 2) if lengths else 0.0

    @staticmethod
    def _anonymize(user_id: str) -> str:
        return f"user_{abs(hash(user_id)) % 10_000}"

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_history(self) -> None:
        if not self._data_file.exists():
            return
        try:
            raw = json.loads(self._data_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return
        events = raw.get('events', [])
        sessions = raw.get('sessions', {})
        self.events = [UsageEvent(**event) for event in events]
        self.session_lengths = {user: list(lengths) for user, lengths in sessions.items()}

    def _persist(self) -> None:
        payload = {
            'events': [event.__dict__ for event in self.events],
            'sessions': self.session_lengths,
        }
        tmp = self._data_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
        tmp.replace(self._data_file)


__all__ = [
    "AnalyticsDashboard",
    "DashboardMetrics",
    "PrivacySettings",
    "UsageEvent",
]
