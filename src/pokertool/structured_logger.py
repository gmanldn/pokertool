#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Structured Logging Module
==========================

JSON-based structured logging for better log parsing, analysis, and monitoring.

Module: pokertool.structured_logger
Version: 1.0.0
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import os


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """

    def __init__(self, service_name: str = "pokertool", include_trace: bool = True):
        super().__init__()
        self.service_name = service_name
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info and self.include_trace:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add stack trace for errors if available
        if record.levelno >= logging.ERROR and record.stack_info:
            log_data["stack_trace"] = record.stack_info

        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger with JSON output and contextual information
    """

    def __init__(
        self,
        name: str,
        service_name: str = "pokertool",
        level: LogLevel = LogLevel.INFO,
        output_file: Optional[str] = None
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        self.context: Dict[str, Any] = {}

        # Console handler with JSON format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter(service_name))
        self.logger.addHandler(console_handler)

        # File handler if specified
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setFormatter(JSONFormatter(service_name))
            self.logger.addHandler(file_handler)

    def add_context(self, **kwargs):
        """Add persistent context to all future log messages"""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear all context"""
        self.context = {}

    def _log_with_context(self, level: int, message: str, **kwargs):
        """Internal method to log with context"""
        # Merge context with kwargs
        extra_fields = {**self.context, **kwargs}

        # Create log record with extra fields
        self.logger.log(
            level,
            message,
            extra={"extra_fields": extra_fields}
        )

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        if exc_info:
            self.logger.error(
                message,
                exc_info=True,
                extra={"extra_fields": {**self.context, **kwargs}}
            )
        else:
            self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message"""
        if exc_info:
            self.logger.critical(
                message,
                exc_info=True,
                extra={"extra_fields": {**self.context, **kwargs}}
            )
        else:
            self._log_with_context(logging.CRITICAL, message, **kwargs)

    def log_event(
        self,
        event_type: str,
        event_name: str,
        level: LogLevel = LogLevel.INFO,
        **kwargs
    ):
        """
        Log a structured event with metadata

        Args:
            event_type: Type of event (e.g., "api_request", "ml_prediction")
            event_name: Specific event name
            level: Log level
            **kwargs: Additional event metadata
        """
        event_data = {
            "event_type": event_type,
            "event_name": event_name,
            **kwargs
        }

        self._log_with_context(
            getattr(logging, level.value),
            f"{event_type}: {event_name}",
            **event_data
        )

    def log_metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """
        Log a metric value

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement
            **kwargs: Additional metric metadata
        """
        metric_data = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "metric_type": "gauge",
            **kwargs
        }

        self._log_with_context(
            logging.INFO,
            f"Metric: {metric_name} = {value}{unit}",
            **metric_data
        )

    def log_duration(self, operation: str, duration_ms: float, **kwargs):
        """
        Log operation duration

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            **kwargs: Additional metadata
        """
        self.log_metric(
            f"{operation}_duration",
            duration_ms,
            "ms",
            operation=operation,
            metric_type="timing",
            **kwargs
        )


# Global logger instance
_global_logger: Optional[StructuredLogger] = None


def get_logger(
    name: str = "pokertool",
    service_name: str = "pokertool",
    level: LogLevel = LogLevel.INFO
) -> StructuredLogger:
    """Get or create structured logger"""
    global _global_logger

    if _global_logger is None:
        # Create log directory if it doesn't exist
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"{service_name}.log")

        _global_logger = StructuredLogger(
            name=name,
            service_name=service_name,
            level=level,
            output_file=log_file
        )

    return _global_logger


def setup_logging(
    service_name: str = "pokertool",
    level: LogLevel = LogLevel.INFO,
    log_file: Optional[str] = None
):
    """
    Setup global structured logging

    Args:
        service_name: Name of the service
        level: Default log level
        log_file: Optional log file path
    """
    global _global_logger

    _global_logger = StructuredLogger(
        name=service_name,
        service_name=service_name,
        level=level,
        output_file=log_file
    )

    return _global_logger


# Convenience functions
def log_api_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    **kwargs
):
    """Log API request"""
    logger = get_logger()
    logger.log_event(
        "api_request",
        endpoint,
        level=LogLevel.INFO if status_code < 400 else LogLevel.ERROR,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_ml_prediction(
    model_name: str,
    prediction_time_ms: float,
    confidence: float,
    **kwargs
):
    """Log ML prediction"""
    logger = get_logger()
    logger.log_event(
        "ml_prediction",
        model_name,
        level=LogLevel.INFO,
        prediction_time_ms=prediction_time_ms,
        confidence=confidence,
        **kwargs
    )


def log_error(message: str, error: Exception, **kwargs):
    """Log error with exception info"""
    logger = get_logger()
    logger.error(
        message,
        exc_info=True,
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs
    )
