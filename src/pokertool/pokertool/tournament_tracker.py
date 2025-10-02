"""Enhanced tournament tracking with scheduling, ROI analysis, and alerts."""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DEFAULT_TOURNAMENT_DIR = Path.home() / ".pokertool" / "tournaments"
DEFAULT_TOURNAMENT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TournamentStructure:
    """Basic tournament structure information."""

    starting_stack: int
    blind_interval_minutes: int
    average_field_size: int
    late_reg_minutes: int
    reentry_allowed: bool


@dataclass
class TournamentEvent:
    """Scheduled tournament event."""

    event_id: str
    name: str
    start_time: float
    buy_in: float
    rake: float
    prize_pool: float
    structure: TournamentStructure
    tags: List[str] = field(default_factory=list)
    venue: str = "online"

    def late_registration_end(self) -> float:
        return self.start_time + self.structure.late_reg_minutes * 60


@dataclass
class TournamentResult:
    """Recorded tournament outcome for ROI calculation."""

    event_id: str
    finish_position: int
    payout: float
    total_entries: int


@dataclass
class SatelliteLink:
    """Mapping between satellite events and target tournaments."""

    satellite_event_id: str
    target_event_id: str
    seats_awarded: int


@dataclass
class TournamentAlert:
    """Alert scheduled for tournament reminders or updates."""

    event_id: str
    alert_type: str
    message: str
    trigger_time: float
    created_at: float = field(default_factory=time.time)
    delivered: bool = False


class TournamentTracker:
    """High-level manager for tournament schedules and analytics."""

    def __init__(self, storage_dir: Path = DEFAULT_TOURNAMENT_DIR):
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._storage_file = self._storage_dir / "tracker.json"
        self._events: Dict[str, TournamentEvent] = {}
        self._results: Dict[str, TournamentResult] = {}
        self._satellites: List[SatelliteLink] = []
        self._alerts: List[TournamentAlert] = []
        self._load()

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def add_event(self, event: TournamentEvent) -> None:
        self._events[event.event_id] = event
        self._persist()

    def update_event(self, event_id: str, **updates) -> None:
        event = self._events.get(event_id)
        if not event:
            raise KeyError(f"Unknown tournament event: {event_id}")
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)
        self._persist()

    def list_events(self) -> List[TournamentEvent]:
        return sorted(self._events.values(), key=lambda evt: evt.start_time)

    def upcoming_events(self, within_hours: float = 24.0) -> List[TournamentEvent]:
        horizon = time.time() + within_hours * 3600
        return [event for event in self.list_events() if event.start_time <= horizon]

    # ------------------------------------------------------------------
    # Late registration advisor
    # ------------------------------------------------------------------
    def late_registration_advice(self, event_id: str, current_time: Optional[float] = None) -> str:
        event = self._require_event(event_id)
        current_time = current_time or time.time()
        if current_time >= event.late_registration_end():
            return "Late registration closed. Register immediately for next flight."
        remaining_minutes = max(0, (event.late_registration_end() - current_time) / 60)
        field_projection = event.structure.average_field_size
        advice_parts = [
            f"Late registration open for {remaining_minutes:.0f} minutes",
            f"Projected field size {field_projection} entrants",
        ]
        if event.structure.reentry_allowed:
            advice_parts.append("Re-entry available; consider entering with 20-30bb stack.")
        elif remaining_minutes < 20:
            advice_parts.append("Stacks shallow; joining now retains fold equity vs short stacks.")
        else:
            advice_parts.append("Early arrival recommended to leverage deeper stacks.")
        return ". ".join(advice_parts)

    # ------------------------------------------------------------------
    # Satellite tracking
    # ------------------------------------------------------------------
    def link_satellite(self, satellite_event_id: str, target_event_id: str, seats_awarded: int) -> None:
        if target_event_id not in self._events:
            raise KeyError(f"Unknown target tournament: {target_event_id}")
        link = SatelliteLink(satellite_event_id=satellite_event_id, target_event_id=target_event_id, seats_awarded=seats_awarded)
        self._satellites.append(link)
        self._persist()

    def satellites_for_event(self, target_event_id: str) -> List[SatelliteLink]:
        return [link for link in self._satellites if link.target_event_id == target_event_id]

    # ------------------------------------------------------------------
    # ROI and results
    # ------------------------------------------------------------------
    def record_result(self, result: TournamentResult) -> None:
        if result.event_id not in self._events:
            raise KeyError(f"Unknown tournament event: {result.event_id}")
        self._results[result.event_id] = result
        self._persist()

    def roi_summary(self) -> Dict[str, float]:
        if not self._results:
            return {"events": 0, "investment": 0.0, "payout": 0.0, "roi": 0.0}
        total_investment = 0.0
        total_payout = 0.0
        for event_id, result in self._results.items():
            event = self._events.get(event_id)
            if not event:
                continue
            total_investment += event.buy_in + event.rake
            total_payout += result.payout
        roi = (total_payout - total_investment) / total_investment if total_investment else 0.0
        return {
            "events": len(self._results),
            "investment": round(total_investment, 2),
            "payout": round(total_payout, 2),
            "roi": round(roi, 3),
        }

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    def schedule_alert(self, event_id: str, minutes_before: int, message: Optional[str] = None) -> TournamentAlert:
        event = self._require_event(event_id)
        trigger_time = max(time.time(), event.start_time - minutes_before * 60)
        alert = TournamentAlert(
            event_id=event_id,
            alert_type="reminder",
            message=message or f"{event.name} starts in {minutes_before} minutes",
            trigger_time=trigger_time,
        )
        self._alerts.append(alert)
        self._persist()
        return alert

    def due_alerts(self, current_time: Optional[float] = None) -> List[TournamentAlert]:
        current_time = current_time or time.time()
        due = [alert for alert in self._alerts if not alert.delivered and alert.trigger_time <= current_time]
        return due

    def mark_alert_delivered(self, alert: TournamentAlert) -> None:
        alert.delivered = True
        self._persist()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_event(self, event_id: str) -> TournamentEvent:
        event = self._events.get(event_id)
        if not event:
            raise KeyError(f"Unknown tournament event: {event_id}")
        return event

    def _load(self) -> None:
        if not self._storage_file.exists():
            return
        try:
            payload = json.loads(self._storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        for event_payload in payload.get("events", []):
            structure = TournamentStructure(**event_payload["structure"])
            event = TournamentEvent(structure=structure, **{k: v for k, v in event_payload.items() if k != "structure"})
            self._events[event.event_id] = event
        for result_payload in payload.get("results", []):
            result = TournamentResult(**result_payload)
            self._results[result.event_id] = result
        for link_payload in payload.get("satellites", []):
            self._satellites.append(SatelliteLink(**link_payload))
        for alert_payload in payload.get("alerts", []):
            self._alerts.append(TournamentAlert(**alert_payload))

    def _persist(self) -> None:
        payload = {
            "events": [self._serialize_event(event) for event in self._events.values()],
            "results": [asdict(result) for result in self._results.values()],
            "satellites": [asdict(link) for link in self._satellites],
            "alerts": [asdict(alert) for alert in self._alerts],
        }
        tmp = self._storage_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._storage_file)

    @staticmethod
    def _serialize_event(event: TournamentEvent) -> Dict[str, object]:
        data = asdict(event)
        data["structure"] = asdict(event.structure)
        return data


__all__ = [
    "TournamentAlert",
    "TournamentEvent",
    "TournamentResult",
    "TournamentStructure",
    "TournamentTracker",
]
