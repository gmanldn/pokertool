"""Advanced session tracking, goals, and analytics utilities."""

from __future__ import annotations

import json
import statistics
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SESSION_DIR = Path.home() / ".pokertool" / "sessions"
DEFAULT_SESSION_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> float:
    return time.time()


@dataclass
class SessionGoal:
    """Defines objectives and guardrails for a playing session."""

    hands_target: int = 0
    profit_target: float = 0.0
    break_interval_minutes: int = 45
    max_loss: float = 0.0
    tilt_score_threshold: float = 0.75


@dataclass
class SessionMetrics:
    """Aggregated metrics captured during a session."""

    hands_played: int = 0
    total_profit: float = 0.0
    big_blinds_won: float = 0.0
    minutes_played: float = 0.0
    vpip_count: int = 0
    aggressive_actions: int = 0
    hands_since_break: int = 0
    losses_in_row: int = 0
    tilt_alerts: int = 0

    def winrate_per_100(self) -> float:
        if self.hands_played == 0:
            return 0.0
        return round((self.big_blinds_won / self.hands_played) * 100, 2)

    def hourly_rate(self) -> float:
        hours = self.minutes_played / 60 if self.minutes_played else 0
        if hours <= 0:
            return 0.0
        return round(self.total_profit / hours, 2)


@dataclass
class SessionReview:
    """Structured review generated when a session ends."""

    session_id: str
    goal: SessionGoal
    metrics: SessionMetrics
    notes: List[str]
    achieved_goals: Dict[str, bool]
    recommended_focus: List[str]
    timestamp: float = field(default_factory=_now)


@dataclass
class SessionRecord:
    """Complete session payload persisted to disk."""

    session_id: str
    player_id: str
    start_ts: float
    goal: SessionGoal
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    events: List[Dict[str, float]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    break_history: List[float] = field(default_factory=list)
    completed_ts: Optional[float] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "player_id": self.player_id,
            "start_ts": self.start_ts,
            "goal": self.goal.__dict__,
            "metrics": self.metrics.__dict__,
            "events": self.events,
            "notes": self.notes,
            "break_history": self.break_history,
            "completed_ts": self.completed_ts,
        }


class SessionStorage:
    """Persistence helper for session records."""

    def __init__(self, storage_dir: Path = DEFAULT_SESSION_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "sessions.json"

    def load(self) -> Dict[str, SessionRecord]:
        if not self.storage_file.exists():
            return {}
        try:
            payload = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        records: Dict[str, SessionRecord] = {}
        for session_id, data in payload.items():
            goal = SessionGoal(**data["goal"])
            metrics = SessionMetrics(**data["metrics"])
            record = SessionRecord(
                session_id=session_id,
                player_id=data["player_id"],
                start_ts=data["start_ts"],
                goal=goal,
                metrics=metrics,
                events=data.get("events", []),
                notes=data.get("notes", []),
                break_history=data.get("break_history", []),
                completed_ts=data.get("completed_ts"),
            )
            records[session_id] = record
        return records

    def save(self, records: Dict[str, SessionRecord]) -> None:
        payload = {session_id: record.to_dict() for session_id, record in records.items()}
        tmp_path = self.storage_file.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self.storage_file)


class SessionManager:
    """High-level coordinator for poker session tracking."""

    def __init__(self, storage_dir: Path = DEFAULT_SESSION_DIR):
        self._storage = SessionStorage(storage_dir)
        self._sessions = self._storage.load()

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def start_session(self, player_id: str, goal: Optional[SessionGoal] = None) -> str:
        session_id = uuid.uuid4().hex
        record = SessionRecord(
            session_id=session_id,
            player_id=player_id,
            start_ts=_now(),
            goal=goal or SessionGoal(),
        )
        self._sessions[session_id] = record
        self._persist()
        return session_id

    def record_hand(
        self,
        session_id: str,
        profit: float,
        big_blinds_won: float,
        vpip: bool,
        aggressive: bool,
        duration_seconds: float,
        tilt_score: float = 0.0,
    ) -> SessionMetrics:
        record = self._get_session(session_id)
        metrics = record.metrics
        metrics.hands_played += 1
        metrics.total_profit += profit
        metrics.big_blinds_won += big_blinds_won
        metrics.minutes_played += duration_seconds / 60
        metrics.hands_since_break += 1
        if vpip:
            metrics.vpip_count += 1
        if aggressive:
            metrics.aggressive_actions += 1
        if profit < 0:
            metrics.losses_in_row += 1
        else:
            metrics.losses_in_row = 0

        if tilt_score >= record.goal.tilt_score_threshold:
            metrics.tilt_alerts += 1
            record.notes.append(f"Tilt alert triggered at hand {metrics.hands_played}")

        record.events.append(
            {
                "timestamp": _now(),
                "profit": profit,
                "bb": big_blinds_won,
                "tilt": tilt_score,
            }
        )
        self._persist()
        return metrics

    def record_break(self, session_id: str, note: str = "Scheduled break") -> None:
        record = self._get_session(session_id)
        record.break_history.append(_now())
        record.metrics.hands_since_break = 0
        record.notes.append(note)
        self._persist()

    def complete_session(self, session_id: str, final_note: Optional[str] = None) -> SessionReview:
        record = self._get_session(session_id)
        if final_note:
            record.notes.append(final_note)
        record.completed_ts = _now()
        review = self._build_review(record)
        record.notes.append("SESSION_COMPLETED")
        self._persist()
        return review

    # ------------------------------------------------------------------
    # Monitoring and analytics
    # ------------------------------------------------------------------
    def should_take_break(self, session_id: str) -> bool:
        record = self._get_session(session_id)
        minutes_per_break = record.goal.break_interval_minutes
        if minutes_per_break <= 0:
            return False
        metrics = record.metrics
        if record.goal.hands_target and metrics.hands_played >= record.goal.hands_target and metrics.hands_since_break > 0:
            return True
        time_since_break = self._time_since_break(record)
        return metrics.hands_since_break >= 25 or time_since_break >= minutes_per_break * 60

    def detect_tilt(self, session_id: str) -> bool:
        record = self._get_session(session_id)
        metrics = record.metrics
        if record.goal.max_loss and metrics.total_profit <= -abs(record.goal.max_loss):
            return True
        recent_losses = [event for event in record.events[-10:] if event["profit"] < 0]
        if len(recent_losses) >= 5 and statistics.mean(ev["tilt"] for ev in recent_losses) >= record.goal.tilt_score_threshold:
            return True
        return metrics.losses_in_row >= 4

    def get_session_analytics(self, session_id: str) -> Dict[str, float]:
        record = self._get_session(session_id)
        metrics = record.metrics
        vpip_percent = (metrics.vpip_count / metrics.hands_played * 100) if metrics.hands_played else 0.0
        aggression_percent = (metrics.aggressive_actions / metrics.hands_played * 100) if metrics.hands_played else 0.0
        return {
            "hands_played": metrics.hands_played,
            "total_profit": round(metrics.total_profit, 2),
            "winrate_bb100": metrics.winrate_per_100(),
            "hourly": metrics.hourly_rate(),
            "vpip_percent": round(vpip_percent, 2),
            "aggression_percent": round(aggression_percent, 2),
            "tilt_alerts": metrics.tilt_alerts,
            "breaks_taken": len(record.break_history),
        }

    def get_active_sessions(self) -> List[str]:
        return [session_id for session_id, record in self._sessions.items() if record.completed_ts is None]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_review(self, record: SessionRecord) -> SessionReview:
        metrics = record.metrics
        goal = record.goal
        achieved = {
            "hands_target": goal.hands_target <= 0 or metrics.hands_played >= goal.hands_target,
            "profit_target": goal.profit_target <= 0 or metrics.total_profit >= goal.profit_target,
            "tilt_control": metrics.tilt_alerts == 0,
        }
        focus: List[str] = []
        if not achieved["tilt_control"]:
            focus.append("Improve emotional regulation; review tilt notes.")
        if achieved["hands_target"] and metrics.winrate_per_100() < 0:
            focus.append("Review losing hands despite volume success.")
        if metrics.vpip_count and metrics.vpip_count / max(metrics.hands_played, 1) < 0.18:
            focus.append("Increase selective aggression; VPIP below threshold.")
        return SessionReview(
            session_id=record.session_id,
            goal=goal,
            metrics=metrics,
            notes=list(record.notes),
            achieved_goals=achieved,
            recommended_focus=focus,
        )

    def _get_session(self, session_id: str) -> SessionRecord:
        if session_id not in self._sessions:
            raise KeyError(f"Unknown session id: {session_id}")
        return self._sessions[session_id]

    def _time_since_break(self, record: SessionRecord) -> float:
        if record.break_history:
            last_break = record.break_history[-1]
            return _now() - last_break
        return _now() - record.start_ts

    def _persist(self) -> None:
        self._storage.save(self._sessions)


__all__ = [
    "SessionGoal",
    "SessionMetrics",
    "SessionManager",
    "SessionReview",
]
