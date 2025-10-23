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


def emit_detection_event(
    event_type: str,
    severity: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    event_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Schedule a detection event to be broadcast to connected WebSocket clients.

    This function is safe to call from synchronous code, background threads,
    or within an asyncio event loop. Events are queued until a loop has been
    registered via :func:`register_detection_event_loop`.

    Args:
        event_type: Logical category (player, card, pot, action, system, error).
        severity: Event severity (info, success, warning, error).
        message: Human-readable summary.
        data: Optional structured payload with full context.
        event_id: Optional unique event identifier.
        correlation_id: Optional correlation ID for event chains.
    """
    event: DetectionEvent = {
        'type': event_type,
        'severity': severity,
        'message': message,
        'data': data or {},
        'timestamp': time.time(),
        'event_id': event_id,
        'correlation_id': correlation_id,
    }

    loop = _get_or_detect_loop()
    if loop and loop.is_running():
        _dispatch_event(loop, event)
    else:
        _enqueue_event(event)


def emit_structured_event(schema: DetectionEventSchema) -> None:
    """
    Emit a detection event using a structured schema.

    Args:
        schema: DetectionEventSchema with full event details.
    """
    if not schema.validate():
        logger.warning("Invalid event schema, skipping emission")
        return

    emit_detection_event(
        event_type=schema.type.value if isinstance(schema.type, Enum) else schema.type,
        severity=schema.severity.value if isinstance(schema.severity, Enum) else schema.severity,
        message=schema.message,
        data=schema.data,
        event_id=schema.event_id,
        correlation_id=schema.correlation_id
    )


def emit_pot_event(
    pot_size: float,
    previous_pot_size: float = 0.0,
    confidence: float = 1.0,
    side_pots: Optional[List[float]] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Emit a structured pot detection event.

    Args:
        pot_size: Current pot size.
        previous_pot_size: Previous pot size.
        confidence: Detection confidence (0.0-1.0).
        side_pots: List of side pot amounts.
        correlation_id: Optional correlation ID.
    """
    pot_change = pot_size - previous_pot_size
    data = PotEventData(
        pot_size=pot_size,
        previous_pot_size=previous_pot_size,
        pot_change=pot_change,
        pot_changed=abs(pot_change) > 0.01,
        side_pots=side_pots or [],
        side_pot_count=len(side_pots) if side_pots else 0,
        total_pot=pot_size + sum(side_pots or []),
        confidence=confidence,
        confidence_level='high' if confidence >= 0.9 else 'medium' if confidence >= 0.7 else 'low'
    )

    message = f"Pot: ${pot_size:.2f}"
    if pot_change > 0:
        message += f" (+${pot_change:.2f})"
    elif pot_change < 0:
        message += f" (-${abs(pot_change):.2f})"

    schema = DetectionEventSchema(
        type=DetectionEventType.POT,
        severity=EventSeverity.INFO,
        message=message,
        data=data.to_dict(),
        correlation_id=correlation_id
    )
    emit_structured_event(schema)


def emit_card_event(
    cards: List[Dict[str, str]],
    card_type: str,
    confidence: float = 1.0,
    correlation_id: Optional[str] = None
) -> None:
    """
    Emit a structured card detection event.

    Args:
        cards: List of card dicts with 'rank' and 'suit'.
        card_type: Type of cards (hero, board, opponent).
        confidence: Detection confidence.
        correlation_id: Optional correlation ID.
    """
    data = CardEventData(
        card_count=len(cards),
        cards=cards,
        card_type=card_type,
        confidence=confidence,
        confidence_level='high' if confidence >= 0.9 else 'medium' if confidence >= 0.7 else 'low'
    )

    card_str = ', '.join(f"{c['rank']}{c['suit']}" for c in cards)
    message = f"{card_type.capitalize()} cards: {card_str}"

    schema = DetectionEventSchema(
        type=DetectionEventType.CARD,
        severity=EventSeverity.INFO,
        message=message,
        data=data.to_dict(),
        correlation_id=correlation_id
    )
    emit_structured_event(schema)


def emit_player_event(
    seat_number: int,
    player_name: Optional[str] = None,
    stack_size: Optional[float] = None,
    previous_stack: Optional[float] = None,
    position: Optional[str] = None,
    is_active: bool = True,
    confidence: float = 1.0,
    correlation_id: Optional[str] = None
) -> None:
    """
    Emit a structured player detection event.

    Args:
        seat_number: Player's seat number.
        player_name: Player name if detected.
        stack_size: Current stack size.
        previous_stack: Previous stack size.
        position: Player position (BTN, SB, BB, etc.).
        is_active: Whether player is active.
        confidence: Detection confidence.
        correlation_id: Optional correlation ID.
    """
    stack_change = None
    if stack_size is not None and previous_stack is not None:
        stack_change = stack_size - previous_stack

    data = PlayerEventData(
        seat_number=seat_number,
        player_name=player_name,
        stack_size=stack_size,
        previous_stack=previous_stack,
        stack_change=stack_change,
        position=position,
        is_active=is_active,
        confidence=confidence,
        confidence_level='high' if confidence >= 0.9 else 'medium' if confidence >= 0.7 else 'low'
    )

    message = f"Player {seat_number}"
    if player_name:
        message = f"Player {player_name} (seat {seat_number})"
    if position:
        message += f" [{position}]"
    if stack_size is not None:
        message += f": ${stack_size:.2f}"
        if stack_change and abs(stack_change) > 0.01:
            message += f" ({'+' if stack_change > 0 else ''}{stack_change:.2f})"

    schema = DetectionEventSchema(
        type=DetectionEventType.PLAYER,
        severity=EventSeverity.INFO,
        message=message,
        data=data.to_dict(),
        correlation_id=correlation_id
    )
    emit_structured_event(schema)


def emit_action_event(
    seat_number: int,
    action: str,
    amount: float = 0.0,
    player_name: Optional[str] = None,
    confidence: float = 1.0,
    correlation_id: Optional[str] = None
) -> None:
    """
    Emit a structured player action event.

    Args:
        seat_number: Player's seat number.
        action: Action type (fold, check, call, bet, raise, all_in).
        amount: Action amount.
        player_name: Player name if known.
        confidence: Detection confidence.
        correlation_id: Optional correlation ID.
    """
    data = ActionEventData(
        seat_number=seat_number,
        action=action,
        amount=amount,
        player_name=player_name,
        confidence=confidence,
        confidence_level='high' if confidence >= 0.9 else 'medium' if confidence >= 0.7 else 'low'
    )

    player_desc = player_name or f"Seat {seat_number}"
    message = f"{player_desc}: {action.upper()}"
    if amount > 0:
        message += f" ${amount:.2f}"

    schema = DetectionEventSchema(
        type=DetectionEventType.ACTION,
        severity=EventSeverity.INFO,
        message=message,
        data=data.to_dict(),
        correlation_id=correlation_id
    )
    emit_structured_event(schema)


def emit_state_change_event(
    previous_state: str,
    new_state: str,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Emit a structured state change event.

    Args:
        previous_state: Previous state.
        new_state: New state.
        reason: Optional reason for state change.
        correlation_id: Optional correlation ID.
    """
    data = StateChangeEventData(
        previous_state=previous_state,
        new_state=new_state,
        reason=reason
    )

    message = f"State change: {previous_state} → {new_state}"
    if reason:
        message += f" ({reason})"

    schema = DetectionEventSchema(
        type=DetectionEventType.STATE_CHANGE,
        severity=EventSeverity.INFO,
        message=message,
        data=data.to_dict(),
        correlation_id=correlation_id
    )
    emit_structured_event(schema)


def emit_performance_event(
    fps: Optional[float] = None,
    avg_frame_time_ms: Optional[float] = None,
    memory_mb: Optional[float] = None,
    cpu_percent: Optional[float] = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Emit a structured performance event.

    Args:
        fps: Current frames per second.
        avg_frame_time_ms: Average frame processing time.
        memory_mb: Memory usage in MB.
        cpu_percent: CPU usage percentage.
        correlation_id: Optional correlation ID.
    """
    data = PerformanceEventData(
        fps=fps,
        avg_frame_time_ms=avg_frame_time_ms,
        memory_mb=memory_mb,
        cpu_percent=cpu_percent
    )

    message_parts = []
    if fps is not None:
        message_parts.append(f"{fps:.1f} FPS")
    if avg_frame_time_ms is not None:
        message_parts.append(f"{avg_frame_time_ms:.1f}ms/frame")
    if memory_mb is not None:
        message_parts.append(f"{memory_mb:.0f}MB")
    if cpu_percent is not None:
        message_parts.append(f"{cpu_percent:.1f}% CPU")

    message = "Performance: " + ", ".join(message_parts) if message_parts else "Performance update"

    schema = DetectionEventSchema(
        type=DetectionEventType.PERFORMANCE,
        severity=EventSeverity.DEBUG,
        message=message,
        data=data.to_dict(),
        correlation_id=correlation_id
    )
    emit_structured_event(schema)


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
