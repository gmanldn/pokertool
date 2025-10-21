#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Timeout Configuration Module
============================

Centralized timeout configuration for all external operations including
API calls, database queries, ML model inference, and network requests.

Provides consistent timeout handling across the codebase with environment
variable configuration support.

Module: pokertool.timeout_config
Version: 1.0.0
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class TimeoutConfig:
    """
    Centralized timeout configuration.

    All timeout values are in seconds. Environment variables can override defaults.

    Environment Variables:
        POKERTOOL_API_TIMEOUT: Timeout for external API calls (default: 30s)
        POKERTOOL_DB_TIMEOUT: Timeout for database queries (default: 10s)
        POKERTOOL_ML_TIMEOUT: Timeout for ML model inference (default: 60s)
        POKERTOOL_HTTP_TIMEOUT: Timeout for HTTP requests (default: 30s)
        POKERTOOL_HEALTH_CHECK_TIMEOUT: Timeout for health checks (default: 5s)
        POKERTOOL_WEBSOCKET_TIMEOUT: Timeout for WebSocket operations (default: 30s)
        POKERTOOL_FILE_OPERATION_TIMEOUT: Timeout for file I/O (default: 15s)
    """

    # API and HTTP timeouts
    api_timeout: float = 30.0
    http_timeout: float = 30.0
    health_check_timeout: float = 5.0
    websocket_timeout: float = 30.0

    # Database timeouts
    db_query_timeout: float = 10.0
    db_connection_timeout: float = 5.0
    db_transaction_timeout: float = 30.0

    # ML model timeouts
    ml_inference_timeout: float = 60.0
    ml_training_timeout: float = 300.0

    # File and I/O timeouts
    file_operation_timeout: float = 15.0
    screen_capture_timeout: float = 2.0

    # External service timeouts
    external_api_timeout: float = 30.0
    scraper_timeout: float = 5.0

    def __post_init__(self):
        """Load configuration from environment variables."""
        # API timeouts
        self.api_timeout = float(os.getenv('POKERTOOL_API_TIMEOUT', self.api_timeout))
        self.http_timeout = float(os.getenv('POKERTOOL_HTTP_TIMEOUT', self.http_timeout))
        self.health_check_timeout = float(os.getenv('POKERTOOL_HEALTH_CHECK_TIMEOUT', self.health_check_timeout))
        self.websocket_timeout = float(os.getenv('POKERTOOL_WEBSOCKET_TIMEOUT', self.websocket_timeout))

        # Database timeouts
        self.db_query_timeout = float(os.getenv('POKERTOOL_DB_TIMEOUT', self.db_query_timeout))
        self.db_connection_timeout = float(os.getenv('POKERTOOL_DB_CONNECTION_TIMEOUT', self.db_connection_timeout))
        self.db_transaction_timeout = float(os.getenv('POKERTOOL_DB_TRANSACTION_TIMEOUT', self.db_transaction_timeout))

        # ML timeouts
        self.ml_inference_timeout = float(os.getenv('POKERTOOL_ML_TIMEOUT', self.ml_inference_timeout))
        self.ml_training_timeout = float(os.getenv('POKERTOOL_ML_TRAINING_TIMEOUT', self.ml_training_timeout))

        # File and I/O timeouts
        self.file_operation_timeout = float(os.getenv('POKERTOOL_FILE_OPERATION_TIMEOUT', self.file_operation_timeout))
        self.screen_capture_timeout = float(os.getenv('POKERTOOL_SCREEN_CAPTURE_TIMEOUT', self.screen_capture_timeout))

        # External services
        self.external_api_timeout = float(os.getenv('POKERTOOL_EXTERNAL_API_TIMEOUT', self.external_api_timeout))
        self.scraper_timeout = float(os.getenv('POKERTOOL_SCRAPER_TIMEOUT', self.scraper_timeout))


# Global timeout configuration instance
_timeout_config: Optional[TimeoutConfig] = None


def get_timeout_config() -> TimeoutConfig:
    """
    Get the global timeout configuration instance.

    Creates a new instance on first call, then returns the same instance
    for subsequent calls (singleton pattern).

    Returns:
        TimeoutConfig: Global timeout configuration

    Example:
        >>> from pokertool.timeout_config import get_timeout_config
        >>> timeouts = get_timeout_config()
        >>> response = requests.get(url, timeout=timeouts.api_timeout)
    """
    global _timeout_config
    if _timeout_config is None:
        _timeout_config = TimeoutConfig()
    return _timeout_config


def reset_timeout_config() -> None:
    """
    Reset the global timeout configuration.

    This forces a reload from environment variables on the next call
    to get_timeout_config(). Useful for testing.
    """
    global _timeout_config
    _timeout_config = None


# Convenience accessors for common timeout values
def api_timeout() -> float:
    """Get timeout for API calls."""
    return get_timeout_config().api_timeout


def db_timeout() -> float:
    """Get timeout for database queries."""
    return get_timeout_config().db_query_timeout


def ml_timeout() -> float:
    """Get timeout for ML model inference."""
    return get_timeout_config().ml_inference_timeout


def http_timeout() -> float:
    """Get timeout for HTTP requests."""
    return get_timeout_config().http_timeout


def health_check_timeout() -> float:
    """Get timeout for health checks."""
    return get_timeout_config().health_check_timeout


# Pre-configured timeout instances for specific use cases
class TimeoutPresets:
    """Pre-configured timeout values for common scenarios."""

    # Quick operations (health checks, pings)
    QUICK = 2.0

    # Standard operations (API calls, DB queries)
    STANDARD = 10.0

    # Long operations (ML inference, file processing)
    LONG = 60.0

    # Very long operations (ML training, batch processing)
    VERY_LONG = 300.0

    # No timeout (use with caution)
    NONE = None


# Export public API
__all__ = [
    'TimeoutConfig',
    'get_timeout_config',
    'reset_timeout_config',
    'api_timeout',
    'db_timeout',
    'ml_timeout',
    'http_timeout',
    'health_check_timeout',
    'TimeoutPresets',
]
