"""Real User Monitoring (RUM) metrics ingestion and aggregation."""

from __future__ import annotations

import json
import math
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DEFAULT_RUM_DIR = Path.cwd() / "logs" / "rum"
DEFAULT_RUM_DIR.mkdir(parents=True, exist_ok=True)

VALID_RATINGS = {"good", "needs-improvement", "poor"}


def _parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    candidate = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(tz=None).replace(tzinfo=None)
    return dt


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rank = (len(values) - 1) * (percentile / 100.0)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(values[int(rank)])
    lower_value = values[int(lower)]
    upper_value = values[int(upper)]
    return float(lower_value + (upper_value - lower_value) * (rank - lower))


class RUMMetricsStore:
    """Lightweight append-only store for frontend RUM metrics."""

    def __init__(self, storage_dir: Path = DEFAULT_RUM_DIR, retention_days: int = 7, trim_threshold: int = 500):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "rum_metrics.jsonl"
        self.retention_days = retention_days
        self.trim_threshold = max(50, trim_threshold)
        self._lock = threading.Lock()
        self._write_count = 0

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def record_metric(self, metric: Dict[str, Any]) -> None:
        """Persist a single metric entry."""
        record = self._sanitise_metric(metric)
        if not record.get("received_at"):
            record["received_at"] = datetime.utcnow().isoformat()

        with self._lock:
            with self.storage_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n")
            self._write_count += 1
            if self._write_count >= self.trim_threshold:
                self._write_count = 0
                self._trim_old_entries()

    def load_recent(self, hours: int) -> List[Dict[str, Any]]:
        """Load metrics recorded within the last `hours` hours."""
        cutoff = datetime.utcnow() - timedelta(hours=max(1, hours))
        if not self.storage_file.exists():
            return []

        recent: List[Dict[str, Any]] = []
        with self.storage_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = _parse_iso_timestamp(entry.get("received_at"))
                if ts and ts >= cutoff:
                    recent.append(entry)
        return recent

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    def summarise(self, hours: int = 24) -> Dict[str, Any]:
        """Return aggregated statistics for the requested time window."""
        window_hours = max(1, min(hours, 168))
        samples = self.load_recent(window_hours)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        pages: Dict[str, int] = {}
        navigation_types: Dict[str, int] = {}

        for sample in samples:
            metric_name = sample.get("metric", "unknown")
            grouped.setdefault(metric_name, []).append(sample)
            page = sample.get("page") or "unknown"
            pages[page] = pages.get(page, 0) + 1
            nav = sample.get("navigation_type") or "unknown"
            navigation_types[nav] = navigation_types.get(nav, 0) + 1

        metric_summaries = [
            self._build_metric_summary(name, items)
            for name, items in grouped.items()
        ]
        metric_summaries.sort(key=lambda item: item["metric"])

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "window_hours": window_hours,
            "total_samples": len(samples),
            "metrics": metric_summaries,
            "pages": pages,
            "navigation_types": navigation_types,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _sanitise_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        metric_name = str(metric.get("metric", "UNKNOWN")).strip()[:32] or "UNKNOWN"
        value = self._coerce_float(metric.get("value"), default=0.0)
        delta = self._coerce_float(metric.get("delta"))
        rating = str(metric.get("rating", "")).lower()
        if rating not in VALID_RATINGS:
            rating = None

        session_id = self._coerce_str(metric.get("session_id"), max_len=64)
        navigation_type = self._coerce_str(metric.get("navigation_type"), max_len=32)
        page = self._coerce_str(metric.get("page"), max_len=256)
        app_version = self._coerce_str(metric.get("app_version"), max_len=32)
        client_timestamp = self._coerce_str(metric.get("client_timestamp"), max_len=64)
        trace_id = self._coerce_str(metric.get("trace_id"), max_len=64)
        span_id = self._coerce_str(metric.get("span_id"), max_len=64)
        client_ip = self._coerce_str(metric.get("client_ip"), max_len=64)
        user_agent = self._coerce_str(metric.get("user_agent"), max_len=256)

        attribution = self._filter_mapping(metric.get("attribution"), allowed_keys={
            "largestShiftValue",
            "largestShiftTarget",
            "largestContentfulPaintElement",
            "timeToFirstByte",
            "interactionTarget",
            "interactionTime",
            "eventTarget",
        })
        environment = self._filter_mapping(metric.get("environment"), allowed_keys={
            "environment",
            "release",
            "build",
            "platform",
            "device",
        })

        received = metric.get("received_at")
        received_iso = (
            self._coerce_str(received, max_len=64)
            if _parse_iso_timestamp(self._coerce_str(received, max_len=64))
            else None
        )

        return {
            "metric": metric_name,
            "value": value,
            "delta": delta,
            "rating": rating,
            "session_id": session_id,
            "navigation_type": navigation_type,
            "page": page,
            "app_version": app_version,
            "client_timestamp": client_timestamp,
            "trace_id": trace_id,
            "span_id": span_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "attribution": attribution,
            "environment": environment,
            "received_at": received_iso or "",
        }

    def _build_metric_summary(self, metric_name: str, samples: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        values = sorted(self._coerce_float(item.get("value"), default=0.0) for item in samples)
        ratings: Dict[str, int] = {"good": 0, "needs-improvement": 0, "poor": 0, "unknown": 0}
        latest_sample_ts: Optional[str] = None

        for item in samples:
            rating = item.get("rating")
            if rating in VALID_RATINGS:
                ratings[rating] += 1
            else:
                ratings["unknown"] += 1
            ts = item.get("received_at")
            if ts and (latest_sample_ts is None or ts > latest_sample_ts):
                latest_sample_ts = ts

        count = len(values)
        average = sum(values) / count if count else 0.0

        return {
            "metric": metric_name,
            "samples": count,
            "average": round(average, 2),
            "p50": round(_percentile(values, 50), 2),
            "p75": round(_percentile(values, 75), 2),
            "p95": round(_percentile(values, 95), 2),
            "max": round(values[-1], 2) if values else 0.0,
            "ratings": ratings,
            "last_sample_at": latest_sample_ts,
        }

    def _trim_old_entries(self) -> None:
        """Remove metrics older than the retention window."""
        cutoff = datetime.utcnow() - timedelta(days=max(1, self.retention_days))
        entries: List[str] = []

        if not self.storage_file.exists():
            return

        with self.storage_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                timestamp = _parse_iso_timestamp(data.get("received_at"))
                if timestamp and timestamp >= cutoff:
                    entries.append(json.dumps(data, ensure_ascii=True, separators=(",", ":")))

        with self.storage_file.open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(entry + "\n")

    @staticmethod
    def _coerce_float(value: Any, default: Optional[float] = None) -> Optional[float]:
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_str(value: Any, max_len: int) -> Optional[str]:
        if value is None:
            return None
        stringified = str(value).strip()
        return stringified[:max_len] if stringified else None

    @staticmethod
    def _filter_mapping(value: Any, *, allowed_keys: Iterable[str]) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        allowed = set(allowed_keys)
        filtered = {str(key): value[key] for key in value if key in allowed}
        return filtered


__all__ = ["RUMMetricsStore"]
