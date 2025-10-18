#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Lightweight Tkinter-aware event bus for GUI components."""

from __future__ import annotations

from collections import defaultdict
from queue import Empty, Queue
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Tuple

import threading


class GUIEventBus:
    """Thread-safe event bus that marshals callbacks onto the Tkinter loop."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)
        self._queue: "Queue[Tuple[str, Dict[str, Any]]]" = Queue()
        self._attached_widget = None
        self._polling = False
        self._poll_interval_ms = 16  # ~60fps refresh
        self._lock = threading.RLock()

    def attach(self, widget) -> None:
        """Attach a Tk widget whose event loop will dispatch events."""
        with self._lock:
            self._attached_widget = widget
            if not self._polling and widget is not None:
                self._polling = True
                widget.after(self._poll_interval_ms, self._drain_queue)

    def detach(self, widget) -> None:
        """Detach the current widget to stop polling."""
        with self._lock:
            if self._attached_widget is widget:
                self._attached_widget = None
                self._polling = False

    def subscribe(self, event: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to an event."""
        with self._lock:
            if callback not in self._subscribers[event]:
                self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from an event."""
        with self._lock:
            callbacks = self._subscribers.get(event)
            if not callbacks:
                return
            if callback in callbacks:
                callbacks.remove(callback)
            if not callbacks and event in self._subscribers:
                del self._subscribers[event]

    def emit(self, event: str, payload: Dict[str, Any]) -> None:
        """Queue an event for delivery on the Tk thread."""
        self._queue.put((event, payload))
        with self._lock:
            widget = self._attached_widget
            if widget is not None and not self._polling:
                self._polling = True
                widget.after(self._poll_interval_ms, self._drain_queue)

    def _drain_queue(self) -> None:
        with self._lock:
            widget = self._attached_widget
            if widget is None:
                self._polling = False
                return

        delivered = False
        while True:
            try:
                event, payload = self._queue.get_nowait()
            except Empty:
                break
            delivered = True
            callbacks: Optional[List[Callable[[Dict[str, Any]], None]]]
            with self._lock:
                callbacks = list(self._subscribers.get(event, ()))

            for callback in callbacks:
                try:
                    callback(dict(payload))
                except Exception:  # pragma: no cover - GUI callbacks may raise
                    import logging
                    logging.getLogger(__name__).exception("GUIEventBus callback failed for event %s", event)

        with self._lock:
            widget = self._attached_widget
            if widget is None:
                self._polling = False
                return
            # Continue polling if there were events or if queue still contains items
            if delivered or not self._queue.empty():
                widget.after(self._poll_interval_ms, self._drain_queue)
            else:
                self._polling = False


_GUI_EVENT_BUS: Optional[GUIEventBus] = None


def get_gui_event_bus() -> GUIEventBus:
    """Return singleton GUI event bus."""
    global _GUI_EVENT_BUS
    if _GUI_EVENT_BUS is None:
        _GUI_EVENT_BUS = GUIEventBus()
    return _GUI_EVENT_BUS

