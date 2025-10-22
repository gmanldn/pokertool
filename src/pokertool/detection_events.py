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

Enhanced with event type enums, validation, and comprehensive event schemas.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, Optional, List
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# Event Type Enumerations
class DetectionEventType(str, Enum):
    """Types of detection events."""
    # Core detections
    POT = "pot"
    CARD = "card"
    PLAYER = "player"
    ACTION = "action"
    BOARD = "board"
    BUTTON = "button"
    BLIND = "blind"

    # State changes
    STATE_CHANGE = "state_change"
    HAND_START = "hand_start"
    HAND_END = "hand_end"
    STREET_CHANGE = "street_change"  # preflop -> flop -> turn -> river

    # System events
    SYSTEM = "system"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    # Performance events
    PERFORMANCE = "performance"
    FPS = "fps"
    LATENCY = "latency"


class EventSeverity(str, Enum):
    """Severity levels for detection events."""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DetectionEventData:
    """Base class for detection event data with common fields."""
    timestamp: float = field(default_factory=time.time)
    confidence: Optional[float] = None
    confidence_level: Optional[str] = None  # 'low', 'medium', 'high'
    detection_method: Optional[str] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PotEventData(DetectionEventData):
    """Data for pot detection events."""
    pot_size: float = 0.0
    previous_pot_size: float = 0.0
    pot_change: float = 0.0
    pot_changed: bool = False
    side_pots: List[float] = field(default_factory=list)
    side_pot_count: int = 0
    total_pot: float = 0.0


@dataclass
class CardEventData(DetectionEventData):
    """Data for card detection events."""
    card_count: int = 0
    cards: List[Dict[str, str]] = field(default_factory=list)  # [{'rank': 'A', 'suit': 's'}, ...]
    card_type: str = ""  # 'hero', 'board', 'opponent'


@dataclass
class PlayerEventData(DetectionEventData):
    """Data for player detection events."""
    seat_number: Optional[int] = None
    player_name: Optional[str] = None
    stack_size: Optional[float] = None
    previous_stack: Optional[float] = None
    stack_change: Optional[float] = None
    position: Optional[str] = None
    is_active: bool = True


@dataclass
class ActionEventData(DetectionEventData):
    """Data for player action events."""
    seat_number: int = 0
    action: str = ""  # fold, check, call, bet, raise, all_in
    amount: float = 0.0
    player_name: Optional[str] = None


@dataclass
class StateChangeEventData(DetectionEventData):
    """Data for state change events."""
    previous_state: str = ""
    new_state: str = ""
    reason: Optional[str] = None


@dataclass
class PerformanceEventData(DetectionEventData):
    """Data for performance events."""
    fps: Optional[float] = None
    avg_frame_time_ms: Optional[float] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


@dataclass
class DetectionEventSchema:
    """Complete schema for a detection event."""
    type: DetectionEventType
    severity: EventSeverity
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.type.value if isinstance(self.type, Enum) else self.type,
            'severity': self.severity.value if isinstance(self.severity, Enum) else self.severity,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp,
            'event_id': self.event_id,
            'correlation_id': self.correlation_id,
        }

    def validate(self) -> bool:
        """Validate event schema."""
        if not self.message:
            logger.warning("Detection event missing message")
            return False

        if not isinstance(self.data, dict):
            logger.warning(f"Detection event data must be dict, got {type(self.data)}")
            return False

        return True

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
