#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detection Logger Module
=======================

Specialized logger for poker table detection events with:
- Daily log rotation (30-day retention)
- Detection confidence tracking
- Performance metrics logging
- Error categorization and tracking
- State snapshots for debugging

Usage:
    from pokertool.detection_logger import (
        get_detection_logger,
        log_detection,
        log_detection_error,
        save_detection_snapshot
    )

    logger = get_detection_logger()
    log_detection('card', 'hero_cards', ['As', 'Kh'], confidence=0.95)
    log_detection_error('OCR_FAILURE', 'Failed to read pot size', screenshot_path='/path/to/screenshot.png')
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime, timedelta
from enum import Enum

# Detection event types
class DetectionType(str, Enum):
    """Types of poker table detections."""
    CARD = "card"
    POT = "pot"
    PLAYER = "player"
    BUTTON = "button"
    BOARD = "board"
    BET = "bet"
    STACK = "stack"
    ACTION = "action"
    POSITION = "position"


class ErrorCategory(str, Enum):
    """Categories of detection errors."""
    OCR_FAILURE = "ocr_failure"
    TIMEOUT = "timeout"
    LOW_CONFIDENCE = "low_confidence"
    VALIDATION_FAILED = "validation_failed"
    TEMPLATE_MISMATCH = "template_mismatch"
    REGION_NOT_FOUND = "region_not_found"
    ANIMATION_DETECTED = "animation_detected"
    UNKNOWN = "unknown"


# Global detection logger instance
_detection_logger: Optional[logging.Logger] = None
_detection_log_dir = Path.home() / ".pokertool" / "logs" / "detection"
_snapshot_dir = Path.home() / ".pokertool" / "logs" / "detection_snapshots"

# Performance tracking
_performance_metrics: Dict[str, List[float]] = {}
_error_counts: Dict[str, int] = {}


def init_detection_logger() -> logging.Logger:
    """
    Initialize detection logger with file rotation.

    Returns:
        Configured detection logger
    """
    global _detection_logger

    if _detection_logger is not None:
        return _detection_logger

    # Create log directory
    _detection_log_dir.mkdir(parents=True, exist_ok=True)
    _snapshot_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger("pokertool.detection")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Don't propagate to root logger

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Daily rotating file handler for all detection events
    detection_log_path = _detection_log_dir / "detection.log"
    file_handler = TimedRotatingFileHandler(
        str(detection_log_path),
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Separate handler for errors only
    error_log_path = _detection_log_dir / "detection_errors.log"
    error_handler = RotatingFileHandler(
        str(error_log_path),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)

    # Performance metrics handler
    perf_log_path = _detection_log_dir / "detection_performance.log"
    perf_handler = TimedRotatingFileHandler(
        str(perf_log_path),
        when='midnight',
        interval=1,
        backupCount=7,  # Keep 7 days
        encoding='utf-8'
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.addFilter(lambda record: 'performance' in record.msg.lower())

    # JSON formatter for structured logging
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(name)s", "message": %(message)s}'
    )
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    perf_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(perf_handler)

    _detection_logger = logger
    logger.info(json.dumps({
        "event": "logger_initialized",
        "log_dir": str(_detection_log_dir),
        "retention_days": 30
    }))

    return logger


def get_detection_logger() -> logging.Logger:
    """Get or create detection logger."""
    if _detection_logger is None:
        return init_detection_logger()
    return _detection_logger


def log_detection(
    detection_type: str,
    operation: str,
    value: Any,
    *,
    confidence: Optional[float] = None,
    duration_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a successful detection event.

    Args:
        detection_type: Type of detection (card, pot, player, etc.)
        operation: Specific operation (e.g., 'hero_cards', 'pot_size')
        value: Detected value
        confidence: Detection confidence (0.0-1.0)
        duration_ms: Time taken for detection in milliseconds
        metadata: Additional context data
    """
    logger = get_detection_logger()

    log_data = {
        "event": "detection",
        "type": detection_type,
        "operation": operation,
        "value": str(value)[:200],  # Limit value length
        "confidence": confidence,
        "duration_ms": duration_ms,
        "timestamp": time.time(),
    }

    if metadata:
        log_data["metadata"] = metadata

    # Track performance if duration provided
    if duration_ms is not None:
        _track_performance(detection_type, duration_ms)

    # Log with appropriate level based on confidence
    if confidence is not None and confidence < 0.8:
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))


def log_detection_error(
    error_category: str,
    message: str,
    *,
    detection_type: Optional[str] = None,
    operation: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a detection error.

    Args:
        error_category: Category of error (OCR_FAILURE, TIMEOUT, etc.)
        message: Error message
        detection_type: Type of detection that failed
        operation: Specific operation that failed
        screenshot_path: Path to screenshot of failed detection
        metadata: Additional context data
    """
    logger = get_detection_logger()

    log_data = {
        "event": "detection_error",
        "error_category": error_category,
        "message": message,
        "type": detection_type,
        "operation": operation,
        "screenshot": screenshot_path,
        "timestamp": time.time(),
    }

    if metadata:
        log_data["metadata"] = metadata

    # Track error counts
    _track_error(error_category)

    logger.error(json.dumps(log_data))

    # Alert if error rate is high
    if _should_alert_error_rate(error_category):
        logger.critical(json.dumps({
            "event": "high_error_rate_alert",
            "error_category": error_category,
            "count": _error_counts[error_category],
            "threshold": 10
        }))


def save_detection_snapshot(
    state_data: Dict[str, Any],
    *,
    snapshot_name: Optional[str] = None
) -> Path:
    """
    Save complete detection state snapshot for debugging.

    Args:
        state_data: Complete state to save
        snapshot_name: Optional name for snapshot (defaults to timestamp)

    Returns:
        Path to saved snapshot file
    """
    logger = get_detection_logger()

    if snapshot_name is None:
        snapshot_name = datetime.now().strftime("%Y%m%d_%H%M%S")

    snapshot_path = _snapshot_dir / f"snapshot_{snapshot_name}.json"

    snapshot = {
        "timestamp": time.time(),
        "datetime": datetime.now().isoformat(),
        "state": state_data
    }

    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2)

    logger.info(json.dumps({
        "event": "snapshot_saved",
        "path": str(snapshot_path),
        "size_bytes": snapshot_path.stat().st_size
    }))

    # Cleanup old snapshots (keep last 50)
    _cleanup_old_snapshots()

    return snapshot_path


def log_performance_metrics(
    fps: Optional[float] = None,
    avg_latency_ms: Optional[float] = None,
    memory_mb: Optional[float] = None,
    cpu_percent: Optional[float] = None
) -> None:
    """
    Log detection system performance metrics.

    Args:
        fps: Frames per second
        avg_latency_ms: Average detection latency
        memory_mb: Memory usage in MB
        cpu_percent: CPU usage percentage
    """
    logger = get_detection_logger()

    log_data = {
        "event": "performance_metrics",
        "fps": fps,
        "avg_latency_ms": avg_latency_ms,
        "memory_mb": memory_mb,
        "cpu_percent": cpu_percent,
        "timestamp": time.time()
    }

    logger.info(json.dumps(log_data))

    # Alert on performance regression
    if avg_latency_ms is not None and avg_latency_ms > 100:
        logger.warning(json.dumps({
            "event": "performance_regression",
            "avg_latency_ms": avg_latency_ms,
            "threshold_ms": 100
        }))


def get_error_statistics() -> Dict[str, int]:
    """Get error counts by category."""
    return _error_counts.copy()


def get_performance_statistics() -> Dict[str, Dict[str, float]]:
    """
    Get performance statistics by detection type.

    Returns:
        Dict mapping detection type to stats (avg, min, max, p95)
    """
    stats = {}

    for detection_type, durations in _performance_metrics.items():
        if not durations:
            continue

        sorted_durations = sorted(durations)
        stats[detection_type] = {
            "count": len(durations),
            "avg_ms": sum(durations) / len(durations),
            "min_ms": sorted_durations[0],
            "max_ms": sorted_durations[-1],
            "p50_ms": sorted_durations[len(durations) // 2],
            "p95_ms": sorted_durations[int(len(durations) * 0.95)] if len(durations) > 20 else sorted_durations[-1]
        }

    return stats


def reset_metrics() -> None:
    """Reset performance and error tracking metrics."""
    global _performance_metrics, _error_counts
    _performance_metrics.clear()
    _error_counts.clear()


# Internal helper functions

def _track_performance(detection_type: str, duration_ms: float) -> None:
    """Track performance metric."""
    if detection_type not in _performance_metrics:
        _performance_metrics[detection_type] = []

    _performance_metrics[detection_type].append(duration_ms)

    # Keep last 1000 samples per type
    if len(_performance_metrics[detection_type]) > 1000:
        _performance_metrics[detection_type] = _performance_metrics[detection_type][-1000:]


def _track_error(error_category: str) -> None:
    """Track error count."""
    _error_counts[error_category] = _error_counts.get(error_category, 0) + 1


def _should_alert_error_rate(error_category: str) -> bool:
    """Check if error rate warrants an alert."""
    # Alert if more than 10 errors of same category
    return _error_counts.get(error_category, 0) > 10


def _cleanup_old_snapshots(max_snapshots: int = 50) -> None:
    """
    Delete old snapshots, keeping only the most recent ones.

    Args:
        max_snapshots: Maximum number of snapshots to keep
    """
    snapshots = sorted(_snapshot_dir.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime)

    # Delete oldest snapshots if over limit
    if len(snapshots) > max_snapshots:
        for snapshot in snapshots[:-max_snapshots]:
            snapshot.unlink()


__all__ = [
    'DetectionType',
    'ErrorCategory',
    'init_detection_logger',
    'get_detection_logger',
    'log_detection',
    'log_detection_error',
    'save_detection_snapshot',
    'log_performance_metrics',
    'get_error_statistics',
    'get_performance_statistics',
    'reset_metrics',
]
