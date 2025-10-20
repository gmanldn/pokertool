# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: detection_events.py
# version: v1.0.0
# last_commit: '2025-10-17T00:00:00+00:00'
# fixes:
# - date: '2025-10-17'
#   summary: Added centralized detection event dispatcher for WebSocket streaming
# ---
# POKERTOOL-HEADER-END

"""
Detection Event Dispatch Utilities
==================================

Provides a thread-safe bridge between synchronous detection code and the
asynchronous WebSocket broadcaster exposed by the API module. Detection
modules call ``emit_detection_event`` to queue events which are later
forwarded to connected clients once the API event loop is registered.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger(__name__)

DetectionEvent = Dict[str, Any]

_event_loop: Optional[asyncio.AbstractEventLoop] = None
_pending_events: Deque[DetectionEvent] = deque(maxlen=256)
_lock = threading.Lock()


def register_detection_event_loop(loop: Optional[asyncio.AbstractEventLoop]) -> None:
    """
    Register the asyncio event loop used to dispatch detection events.

    Args:
        loop: Running asyncio loop for the FastAPI application.
    """
    global _event_loop

    with _lock:
        _event_loop = loop

    if loop and loop.is_running():
        _flush_pending_events(loop)


def emit_detection_event(event_type: str, severity: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """
    Schedule a detection event to be broadcast to connected WebSocket clients.

    This function is safe to call from synchronous code, background threads,
    or within an asyncio event loop. Events are queued until a loop has been
    registered via :func:`register_detection_event_loop`.

    Args:
        event_type: Logical category (player, card, pot, action, system, error).
        severity: Event severity (info, success, warning, error).
        message: Human-readable summary.
        data: Optional structured payload.
    """
    event: DetectionEvent = {
        'type': event_type,
        'severity': severity,
        'message': message,
        'data': data or {},
    }

    loop = _get_or_detect_loop()
    if loop and loop.is_running():
        _dispatch_event(loop, event)
    else:
        _enqueue_event(event)


def clear_detection_event_loop() -> None:
    """Clear the registered event loop (used during application shutdown)."""
    global _event_loop
    with _lock:
        _event_loop = None


def _get_or_detect_loop() -> Optional[asyncio.AbstractEventLoop]:
    """Return the registered loop or attempt to detect the current running loop."""
    loop = _event_loop
    if loop and loop.is_running():
        return loop

    try:
        detected_loop = asyncio.get_running_loop()
    except RuntimeError:
        return loop

    register_detection_event_loop(detected_loop)
    return detected_loop


def _enqueue_event(event: DetectionEvent) -> None:
    """Store an event until a loop is ready to process it."""
    with _lock:
        if len(_pending_events) == _pending_events.maxlen:
            # Drop the oldest event to keep memory bounded
            _pending_events.popleft()
        _pending_events.append(event)


def _flush_pending_events(loop: asyncio.AbstractEventLoop) -> None:
    """Flush any queued events to the provided loop."""
    drained_events = []
    with _lock:
        if not _pending_events:
            return
        drained_events = list(_pending_events)
        _pending_events.clear()

    for event in drained_events:
        _dispatch_event(loop, event)


def _dispatch_event(loop: asyncio.AbstractEventLoop, event: DetectionEvent) -> None:
    """Dispatch a single event on the given loop."""
    try:
        loop.call_soon_threadsafe(_schedule_broadcast, event)
    except RuntimeError:
        # Loop is not running anymore; re-queue and wait for new loop
        _enqueue_event(event)


def _schedule_broadcast(event: DetectionEvent) -> None:
    """Schedule the coroutine that forwards the event to the API broadcaster."""
    try:
        asyncio.create_task(_broadcast_event(event))
    except RuntimeError:
        # No running loop when callback executed (loop shutting down)
        _enqueue_event(event)


async def _broadcast_event(event: DetectionEvent) -> None:
    """Coroutine that forwards the detection event to the API broadcaster."""
    try:
        from .api import broadcast_detection_event
    except Exception as exc:  # pragma: no cover - defensive if API not available
        logger.debug("Detection broadcaster unavailable: %s", exc)
        return

    try:
        await broadcast_detection_event(
            event_type=event['type'],
            severity=event['severity'],
            message=event['message'],
            data=event.get('data', {}),
        )
    except Exception as exc:
        logger.warning("Failed to broadcast detection event: %s", exc, exc_info=True)
