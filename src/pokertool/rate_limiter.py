"""
Rate Limiter for AI Provider API Calls

Prevents API quota exhaustion with configurable rate limits,
token bucket algorithm, and per-provider tracking.
"""

import time
from threading import Lock
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int = 10


class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_time(self, tokens: int = 1) -> float:
        with self.lock:
            if self.tokens >= tokens:
                return 0.0
            return (tokens - self.tokens) / self.rate


class RateLimiter:
    """Rate limiter for AI provider API calls"""

    DEFAULT_LIMITS = {
        "claude-code": RateLimitConfig(50, 1000, 10000, 10),
        "anthropic": RateLimitConfig(50, 1000, 10000, 10),
        "openrouter": RateLimitConfig(60, 3000, 50000, 20),
        "openai": RateLimitConfig(60, 3500, 10000, 15),
    }

    def __init__(self):
        self.buckets: Dict[str, Dict[str, TokenBucket]] = {}
        self.lock = Lock()

    def _get_bucket(self, provider: str, window: str) -> TokenBucket:
        if provider not in self.buckets:
            self.buckets[provider] = {}
        if window not in self.buckets[provider]:
            config = self.DEFAULT_LIMITS.get(provider, self.DEFAULT_LIMITS["anthropic"])
            if window == "minute":
                rate, capacity = config.requests_per_minute / 60.0, config.burst_size
            elif window == "hour":
                rate, capacity = config.requests_per_hour / 3600.0, config.requests_per_hour
            else:
                rate, capacity = config.requests_per_day / 86400.0, config.requests_per_day
            self.buckets[provider][window] = TokenBucket(rate, int(capacity))
        return self.buckets[provider][window]

    def check_limit(self, provider: str) -> tuple:
        with self.lock:
            for window in ["minute", "hour", "day"]:
                bucket = self._get_bucket(provider, window)
                if not bucket.consume(1):
                    return False, f"Rate limit exceeded for {window}. Wait {bucket.wait_time(1):.1f}s"
            return True, None

    def wait_if_needed(self, provider: str, max_wait: float = 60.0) -> bool:
        allowed, _ = self.check_limit(provider)
        if allowed:
            return True
        max_wait_time = max(self._get_bucket(provider, w).wait_time(1) for w in ["minute", "hour", "day"])
        if max_wait_time > max_wait:
            return False
        time.sleep(max_wait_time)
        return True

    def get_remaining_requests(self, provider: str) -> Dict[str, int]:
        return {window: int(self._get_bucket(provider, window).tokens) for window in ["minute", "hour", "day"]}

    def reset_provider(self, provider: str):
        with self.lock:
            if provider in self.buckets:
                del self.buckets[provider]

    def get_stats(self) -> Dict:
        stats = {}
        for provider in self.buckets:
            config = self.DEFAULT_LIMITS.get(provider, self.DEFAULT_LIMITS["anthropic"])
            stats[provider] = {
                "remaining": self.get_remaining_requests(provider),
                "limits": {"minute": config.requests_per_minute, "hour": config.requests_per_hour, "day": config.requests_per_day}
            }
        return stats


_global_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter
