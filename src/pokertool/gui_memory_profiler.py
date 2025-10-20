#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI Memory Profiler
===================

Background profiler for long-running GUI sessions. Periodically samples
Python heap allocations using ``tracemalloc`` and writes structured JSON
records so we can spot widget/thread leaks during endurance testing.

Usage:
    profiler = GuiMemoryProfiler(sample_interval=60.0)
    profiler.start()
    ...
    profiler.stop()
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional
import json
import logging
import threading
import time
import tracemalloc


logger = logging.getLogger(__name__)


def _format_traceback(frames: Iterable[str]) -> List[str]:
    """Return traceback frames as a list of strings without newlines."""
    return [frame.strip() for frame in frames]


@dataclass
class MemorySample:
    """Structured memory sample written to disk."""

    timestamp: str
    current_kb: float
    peak_kb: float
    thread_count: int
    top_allocations: List[dict]

    def to_json(self) -> str:
        return json.dumps({
            'timestamp': self.timestamp,
            'current_kb': self.current_kb,
            'peak_kb': self.peak_kb,
            'thread_count': self.thread_count,
            'top_allocations': self.top_allocations,
        })


class GuiMemoryProfiler:
    """
    Periodically capture ``tracemalloc`` snapshots for the GUI.

    The profiler writes JSONL formatted records to ``logs/memory/gui_memory.jsonl``.
    Each record includes current/peak memory, active thread counts, and the
    heaviest allocation sites compared against the previous snapshot.
    """

    def __init__(
        self,
        sample_interval: float = 60.0,
        report_limit: int = 15,
        output_dir: Optional[Path] = None,
    ) -> None:
        if sample_interval <= 0:
            raise ValueError("sample_interval must be positive")
        if report_limit <= 0:
            raise ValueError("report_limit must be positive")

        self.sample_interval = sample_interval
        self.report_limit = report_limit
        self.output_dir = (output_dir or (Path.cwd() / 'logs' / 'memory'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / 'gui_memory.jsonl'

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._owns_tracemalloc = False
        self._previous_snapshot: Optional[tracemalloc.Snapshot] = None
        self._started = False

    def start(self) -> None:
        """Start background sampling."""
        if self._started:
            logger.debug("GuiMemoryProfiler already running")
            return

        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._owns_tracemalloc = True
            logger.info("Started tracemalloc for GUI memory profiling")
        else:
            logger.info("Reusing existing tracemalloc session for GUI profiling")

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name='GuiMemoryProfiler',
            daemon=True,
        )
        self._thread.start()
        self._started = True
        logger.info(
            "GuiMemoryProfiler started: interval=%ss report_limit=%s output=%s",
            self.sample_interval,
            self.report_limit,
            self.output_file,
        )

    def stop(self) -> None:
        """Stop background sampling."""
        if not self._started:
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.sample_interval * 2)
        if self._owns_tracemalloc:
            tracemalloc.stop()
        self._started = False
        self._previous_snapshot = None
        logger.info("GuiMemoryProfiler stopped")

    def _run(self) -> None:
        """Background thread loop."""
        while not self._stop_event.wait(self.sample_interval):
            try:
                self._capture_sample()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("GuiMemoryProfiler capture failed: %s", exc)

    def _capture_sample(self) -> None:
        """Capture a tracemalloc snapshot and write to disk."""
        snapshot = tracemalloc.take_snapshot()
        stats = (
            snapshot.compare_to(self._previous_snapshot, 'lineno')
            if self._previous_snapshot is not None
            else snapshot.statistics('lineno')
        )
        top_stats = stats[: self.report_limit]

        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        sample = MemorySample(
            timestamp=datetime.now(timezone.utc).isoformat(),
            current_kb=round(current_bytes / 1024, 2),
            peak_kb=round(peak_bytes / 1024, 2),
            thread_count=threading.active_count(),
            top_allocations=[
                {
                    'location': f"{stat.traceback[0].filename}:{stat.traceback[0].lineno}"
                    if stat.traceback
                    else 'unknown',
                    'size_kb': round(stat.size / 1024, 2),
                    'count': stat.count,
                    'traceback': _format_traceback(stat.traceback.format()) if stat.traceback else [],
                }
                for stat in top_stats
            ],
        )

        with self.output_file.open('a', encoding='utf-8') as handle:
            handle.write(sample.to_json() + '\n')

        self._previous_snapshot = snapshot
        logger.debug(
            "Captured GUI memory sample: current=%.2fKB peak=%.2fKB entries=%s",
            sample.current_kb,
            sample.peak_kb,
            len(sample.top_allocations),
        )

    def __enter__(self) -> 'GuiMemoryProfiler':
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
