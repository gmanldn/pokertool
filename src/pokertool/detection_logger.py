"""
Detection-Specific Logger Module
=================================

Separate logger for detection events with daily rotation and
configurable retention.
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional

class DetectionLogger:
    """Specialized logger for poker table detection events."""

    def __init__(self, log_dir: str = "logs", retention_days: int = 30):
        self.log_dir = Path(log_dir)
        self.retention_days = retention_days
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger('pokertool.detection')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.logger.handlers = []

        log_file = self.log_dir / 'detection.log'
        handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=retention_days,
            encoding='utf-8'
        )

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.logger.info(f"Detection logger initialized - retention: {retention_days} days")

    def log_detection(self, detection_type: str, success: bool, confidence: float = 0.0,
                     details: Optional[Dict[str, Any]] = None, duration_ms: float = 0.0):
        """Log a detection event with full details."""
        details = details or {}
        level = logging.ERROR if not success else (
            logging.WARNING if confidence < 0.6 else logging.INFO
        )
        confidence_level = 'HIGH' if confidence >= 0.8 else 'MEDIUM' if confidence >= 0.6 else 'LOW'
        msg = f"{detection_type.upper()} | Success={success} | Confidence={confidence:.2%} ({confidence_level}) | Duration={duration_ms:.1f}ms"
        if details:
            msg += f" | {', '.join([f'{k}={v}' for k, v in details.items()])}"
        self.logger.log(level, msg)

    def log_fps(self, fps: float):
        """Log detection FPS."""
        level = logging.WARNING if fps < 10 else logging.DEBUG
        self.logger.log(level, f"Detection FPS: {fps:.1f} FPS")

_detection_logger: Optional[DetectionLogger] = None

def get_detection_logger() -> DetectionLogger:
    """Get or create the global detection logger."""
    global _detection_logger
    if _detection_logger is None:
        retention_days = int(os.getenv('DETECTION_LOG_RETENTION_DAYS', '30'))
        _detection_logger = DetectionLogger(retention_days=retention_days)
    return _detection_logger
