#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rate Limiting Module
====================

Comprehensive rate limiting for API endpoints to prevent abuse and ensure
fair resource allocation.

Module: pokertool.rate_limiter
Version: 1.0.0
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int          # Maximum requests
    window_seconds: int        # Time window in seconds
    block_duration: int = 300  # Block duration in seconds (5 min default)


@dataclass
class RateLimitRecord:
    """Record of rate limit tracking"""
    requests: list = field(default_factory=list)
    blocked_until: Optional[datetime] = None
    total_blocked: int = 0


class RateLimiter:
    """
    Token bucket rate limiter with configurable limits
    """

    def __init__(self):
        self._limits: Dict[str, RateLimitConfig] = {}
        self._records: Dict[str, Dict[str, RateLimitRecord]] = defaultdict(
            lambda: defaultdict(RateLimitRecord)
        )
        self._lock = threading.Lock()

    def configure(self, endpoint: str, max_requests: int, window_seconds: int, block_duration: int = 300):
        """
        Configure rate limit for an endpoint

        Args:
            endpoint: API endpoint identifier
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            block_duration: Block duration in seconds after limit exceeded
        """
        self._limits[endpoint] = RateLimitConfig(
            max_requests=max_requests,
            window_seconds=window_seconds,
            block_duration=block_duration
        )

    def check_limit(self, endpoint: str, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Check if request is within rate limit

        Args:
            endpoint: API endpoint
            identifier: User/IP identifier

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        if endpoint not in self._limits:
            return True, None

        config = self._limits[endpoint]

        with self._lock:
            record = self._records[endpoint][identifier]
            now = datetime.now()

            # Check if currently blocked
            if record.blocked_until and now < record.blocked_until:
                remaining = (record.blocked_until - now).seconds
                return False, f"Rate limit exceeded. Try again in {remaining} seconds."

            # Remove old requests outside window
            cutoff = now - timedelta(seconds=config.window_seconds)
            record.requests = [req for req in record.requests if req > cutoff]

            # Check if limit exceeded
            if len(record.requests) >= config.max_requests:
                record.blocked_until = now + timedelta(seconds=config.block_duration)
                record.total_blocked += 1
                return False, f"Rate limit exceeded ({config.max_requests} requests per {config.window_seconds}s). Blocked for {config.block_duration}s."

            # Allow request
            record.requests.append(now)
            return True, None

    def get_stats(self, endpoint: Optional[str] = None) -> Dict:
        """
        Get rate limiting statistics

        Args:
            endpoint: Optional specific endpoint, or all if None

        Returns:
            Dictionary of statistics
        """
        with self._lock:
            if endpoint:
                if endpoint not in self._records:
                    return {}

                stats = {
                    "endpoint": endpoint,
                    "config": self._limits.get(endpoint),
                    "users": {}
                }

                for identifier, record in self._records[endpoint].items():
                    stats["users"][identifier] = {
                        "recent_requests": len(record.requests),
                        "blocked_until": record.blocked_until.isoformat() if record.blocked_until else None,
                        "total_blocked": record.total_blocked
                    }

                return stats
            else:
                stats = {}
                for ep in self._records:
                    stats[ep] = self.get_stats(ep)
                return stats

    def reset(self, endpoint: Optional[str] = None, identifier: Optional[str] = None):
        """
        Reset rate limits

        Args:
            endpoint: Optional endpoint to reset (all if None)
            identifier: Optional user/IP to reset (all if None)
        """
        with self._lock:
            if endpoint and identifier:
                if endpoint in self._records:
                    if identifier in self._records[endpoint]:
                        del self._records[endpoint][identifier]
            elif endpoint:
                if endpoint in self._records:
                    self._records[endpoint].clear()
            else:
                self._records.clear()


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on system load
    """

    def __init__(self, base_limiter: RateLimiter):
        self.base_limiter = base_limiter
        self._system_load = 0.0  # 0.0 to 1.0

    def set_system_load(self, load: float):
        """Set current system load (0.0 to 1.0)"""
        self._system_load = max(0.0, min(1.0, load))

    def check_limit(self, endpoint: str, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Check limit with adaptive scaling based on system load

        Higher system load = stricter rate limits
        """
        if endpoint not in self.base_limiter._limits:
            return True, None

        config = self.base_limiter._limits[endpoint]

        # Adjust max_requests based on system load
        # At 0% load: 100% of limit
        # At 50% load: 75% of limit
        # At 100% load: 50% of limit
        scale_factor = 1.0 - (self._system_load * 0.5)
        adjusted_max = int(config.max_requests * scale_factor)

        # Temporarily adjust config
        original_max = config.max_requests
        config.max_requests = max(1, adjusted_max)

        result = self.base_limiter.check_limit(endpoint, identifier)

        # Restore original
        config.max_requests = original_max

        return result


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


def configure_rate_limit(endpoint: str, max_requests: int, window_seconds: int, block_duration: int = 300):
    """Configure global rate limit"""
    _global_rate_limiter.configure(endpoint, max_requests, window_seconds, block_duration)


def check_rate_limit(endpoint: str, identifier: str) -> Tuple[bool, Optional[str]]:
    """Check against global rate limiter"""
    return _global_rate_limiter.check_limit(endpoint, identifier)


def get_rate_limit_stats(endpoint: Optional[str] = None) -> Dict:
    """Get rate limit statistics"""
    return _global_rate_limiter.get_stats(endpoint)


def reset_rate_limits(endpoint: Optional[str] = None, identifier: Optional[str] = None):
    """Reset rate limits"""
    _global_rate_limiter.reset(endpoint, identifier)


# Pre-configured rate limits for common scenarios
RATE_LIMITS = {
    "api_general": RateLimitConfig(max_requests=100, window_seconds=60),      # 100/min
    "api_auth": RateLimitConfig(max_requests=5, window_seconds=60),           # 5/min (stricter)
    "api_analysis": RateLimitConfig(max_requests=30, window_seconds=60),      # 30/min
    "api_ml_prediction": RateLimitConfig(max_requests=20, window_seconds=60), # 20/min
    "api_database": RateLimitConfig(max_requests=50, window_seconds=60),      # 50/min
    "api_websocket": RateLimitConfig(max_requests=200, window_seconds=60),    # 200/min
}


def setup_default_rate_limits():
    """Setup default rate limits"""
    for endpoint, config in RATE_LIMITS.items():
        configure_rate_limit(
            endpoint,
            config.max_requests,
            config.window_seconds,
            config.block_duration
        )
