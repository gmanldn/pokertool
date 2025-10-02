"""Application performance profiling utilities and alerting."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_PROFILER_DIR = Path.home() / ".pokertool" / "profiler"
DEFAULT_PROFILER_DIR.mkdir(parents=True, exist_ok=True)

try:  # Optional dependency
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except Exception:  # pragma: no cover - psutil might not be present
    psutil = None  # type: ignore
    PSUTIL_AVAILABLE = False


@dataclass
class PerformanceSnapshot:
    """Captured performance metrics at a point in time."""

    timestamp: float
    cpu_percent: float
    memory_mb: float
    thread_count: int
    latency_ms: float
    notes: str = ""


@dataclass
class AlertRule:
    """Alert rule for performance thresholds."""

    metric: str
    threshold: float
    comparison: str  # '>' or '<'
    message: str

    def triggered(self, snapshot: PerformanceSnapshot) -> bool:
        value = getattr(snapshot, self.metric)
        if self.comparison == '>':
            return value > self.threshold
        if self.comparison == '<':
            return value < self.threshold
        raise ValueError(f"Unsupported comparison operator: {self.comparison}")


@dataclass
class OptimizationSuggestion:
    """Suggestion generated from analysis."""

    category: str
    description: str
    severity: str


@dataclass
class ProfilingReport:
    """Summarised profiling report."""

    snapshots: int
    avg_cpu: float
    max_cpu: float
    avg_memory: float
    alerts_triggered: List[str]
    suggestions: List[OptimizationSuggestion]

    def to_dict(self) -> Dict[str, object]:
        return {
            "snapshots": self.snapshots,
            "avg_cpu": self.avg_cpu,
            "max_cpu": self.max_cpu,
            "avg_memory": self.avg_memory,
            "alerts_triggered": list(self.alerts_triggered),
            "suggestions": [suggestion.__dict__ for suggestion in self.suggestions],
        }


class PerformanceProfiler:
    """Collects performance snapshots and produces optimisation insights."""

    def __init__(self, storage_dir: Path = DEFAULT_PROFILER_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots: List[PerformanceSnapshot] = []
        self.alert_rules: List[AlertRule] = []
        self.alert_history: List[str] = []

    # ------------------------------------------------------------------
    # Snapshot collection
    # ------------------------------------------------------------------
    def capture_snapshot(
        self,
        cpu_percent: float,
        memory_mb: float,
        thread_count: int,
        latency_ms: float,
        notes: str = "",
        timestamp: Optional[float] = None
    ) -> PerformanceSnapshot:
        snapshot = PerformanceSnapshot(
            timestamp=timestamp or time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            thread_count=thread_count,
            latency_ms=latency_ms,
            notes=notes,
        )
        self.snapshots.append(snapshot)
        self._evaluate_alerts(snapshot)
        return snapshot

    def capture_current(self, notes: str = "") -> Optional[PerformanceSnapshot]:  # pragma: no cover - depends on psutil
        if not PSUTIL_AVAILABLE:
            return None
        process = psutil.Process()
        cpu = psutil.cpu_percent(interval=0.1)
        memory = process.memory_info().rss / (1024 * 1024)
        threads = process.num_threads()
        latency = 0.0  # Placeholder: integrate with request timing sources if available
        return self.capture_snapshot(cpu, memory, threads, latency, notes=notes)

    # ------------------------------------------------------------------
    # Alerting
    # ------------------------------------------------------------------
    def add_alert_rule(self, rule: AlertRule) -> None:
        self.alert_rules.append(rule)

    def _evaluate_alerts(self, snapshot: PerformanceSnapshot) -> None:
        for rule in self.alert_rules:
            if rule.triggered(snapshot):
                message = f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(snapshot.timestamp))}: {rule.message} (value={getattr(snapshot, rule.metric):.2f})"
                self.alert_history.append(message)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def generate_report(self) -> ProfilingReport:
        if not self.snapshots:
            return ProfilingReport(0, 0.0, 0.0, 0.0, list(self.alert_history), [])
        cpu_values = [snapshot.cpu_percent for snapshot in self.snapshots]
        mem_values = [snapshot.memory_mb for snapshot in self.snapshots]
        avg_cpu = round(statistics.fmean(cpu_values), 2)
        max_cpu = round(max(cpu_values), 2)
        avg_mem = round(statistics.fmean(mem_values), 2)
        suggestions = self._suggest_optimizations(avg_cpu, max_cpu, avg_mem)
        return ProfilingReport(
            snapshots=len(self.snapshots),
            avg_cpu=avg_cpu,
            max_cpu=max_cpu,
            avg_memory=avg_mem,
            alerts_triggered=list(self.alert_history),
            suggestions=suggestions,
        )

    def _suggest_optimizations(self, avg_cpu: float, max_cpu: float, avg_mem: float) -> List[OptimizationSuggestion]:
        suggestions: List[OptimizationSuggestion] = []
        if max_cpu > 85:
            suggestions.append(OptimizationSuggestion(
                category="cpu",
                description="High peak CPU detected; review solver threads and consider lowering concurrency.",
                severity="high",
            ))
        if avg_mem > 800:
            suggestions.append(OptimizationSuggestion(
                category="memory",
                description="Average memory usage approaches 1GB; enable hand history pagination and cache eviction.",
                severity="medium",
            ))
        if avg_cpu < 30 and avg_mem < 500 and not suggestions:
            suggestions.append(OptimizationSuggestion(
                category="baseline",
                description="Performance within targets; maintain current configuration.",
                severity="info",
            ))
        return suggestions

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def export_history(self, filename: Optional[str] = None) -> Path:
        filename = filename or f"profile_{int(time.time())}.json"
        path = self.storage_dir / filename
        payload = {
            "snapshots": [snapshot.__dict__ for snapshot in self.snapshots],
            "alerts": list(self.alert_history),
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def clear(self) -> None:
        self.snapshots.clear()
        self.alert_history.clear()


__all__ = [
    "AlertRule",
    "PerformanceProfiler",
    "PerformanceSnapshot",
    "ProfilingReport",
]
