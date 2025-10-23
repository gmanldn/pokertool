#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Response Caching Layer
===========================

Redis-based caching for expensive API endpoints with automatic cache
invalidation and configurable TTLs.

Features:
- Redis caching for expensive endpoints (/api/stats/*, /api/ml/*)
- Configurable TTL per endpoint pattern (5-60s)
- Automatic cache invalidation on data updates
- Cache key generation with request parameters
- Fallback to in-memory cache when Redis unavailable
- Cache hit/miss metrics
- Decorator-based caching for FastAPI endpoints

Module: pokertool.api_cache
Version: 1.0.0
"""

import os
import json
import hashlib
import logging
import time
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import threading

try:
    import redis
    from redis import Redis, ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    Redis = None
    ConnectionPool = None

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Cache configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
CACHE_KEY_PREFIX = os.getenv("CACHE_KEY_PREFIX", "pokertool:api:")
ENABLE_CACHING = os.getenv("ENABLE_API_CACHING", "true").lower() == "true"

# Default TTLs for different endpoint patterns (seconds)
DEFAULT_TTL_MAP = {
    "/api/stats/": 30,  # Stats endpoints: 30s TTL
    "/api/ml/": 60,  # ML inference endpoints: 60s TTL
    "/api/analysis/": 20,  # Analysis endpoints: 20s TTL
    "/api/dashboard/": 10,  # Dashboard endpoints: 10s TTL
    "/api/health": 5,  # Health check: 5s TTL
}


@dataclass
class CacheEntry:
    """Cached response entry."""
    key: str
    value: str  # JSON-encoded response
    created_at: float
    ttl: int
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return time.time() > (self.created_at + self.ttl)

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0
    errors: int = 0
    redis_available: bool = False

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "invalidations": self.invalidations,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 3),
            "redis_available": self.redis_available,
        }


class InMemoryCache:
    """
    Fallback in-memory cache when Redis is unavailable.

    Thread-safe implementation with LRU eviction.
    """

    def __init__(self, max_entries: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_entries = max_entries
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired:
                del self._cache[key]
                return None

            entry.hit_count += 1
            return entry.value

    def set(self, key: str, value: str, ttl: int):
        """Set value in cache."""
        with self._lock:
            # LRU eviction if cache is full
            if len(self._cache) >= self._max_entries:
                # Remove oldest entry
                oldest_key = min(self._cache.items(), key=lambda x: x[1].created_at)[0]
                del self._cache[oldest_key]

            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl
            )

    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get number of entries in cache."""
        with self._lock:
            return len(self._cache)


class APICache:
    """
    Redis-based API response cache with fallback to in-memory cache.

    Usage:
        cache = APICache()

        # Cache a response
        cache.set("/api/stats/summary", response_data, ttl=30)

        # Get cached response
        cached = cache.get("/api/stats/summary")

        # Invalidate cache pattern
        cache.invalidate_pattern("/api/stats/*")

        # Get metrics
        metrics = cache.get_metrics()
    """

    def __init__(self):
        self.metrics = CacheMetrics()
        self._memory_cache = InMemoryCache()
        self._redis_client: Optional[Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None

        if REDIS_AVAILABLE and ENABLE_CACHING:
            self._init_redis()
        else:
            logger.info("Redis not available or caching disabled, using in-memory cache")

    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self._connection_pool = ConnectionPool(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=2,
                socket_timeout=2,
            )

            self._redis_client = Redis(connection_pool=self._connection_pool)

            # Test connection
            self._redis_client.ping()
            self.metrics.redis_available = True
            logger.info(f"Redis cache connected: {REDIS_HOST}:{REDIS_PORT}")

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
            self._redis_client = None
            self.metrics.redis_available = False

    def _generate_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        Generate cache key from endpoint and parameters.

        Args:
            endpoint: API endpoint path
            params: Query parameters and request data

        Returns:
            Cache key string
        """
        key_parts = [CACHE_KEY_PREFIX, endpoint]

        if params:
            # Sort params for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            key_parts.append(param_hash)

        return ":".join(key_parts)

    def _get_ttl_for_endpoint(self, endpoint: str) -> int:
        """Get TTL for endpoint based on pattern matching."""
        for pattern, ttl in DEFAULT_TTL_MAP.items():
            if endpoint.startswith(pattern):
                return ttl
        return 15  # Default TTL

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Get cached response.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Cached response data or None if not found/expired
        """
        if not ENABLE_CACHING:
            return None

        key = self._generate_cache_key(endpoint, params)

        try:
            # Try Redis first
            if self._redis_client:
                value = self._redis_client.get(key)
                if value:
                    self.metrics.hits += 1
                    return json.loads(value)
            else:
                # Fallback to in-memory cache
                value = self._memory_cache.get(key)
                if value:
                    self.metrics.hits += 1
                    return json.loads(value)

            self.metrics.misses += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.metrics.errors += 1
            return None

    def set(
        self,
        endpoint: str,
        data: Dict,
        ttl: Optional[int] = None,
        params: Optional[Dict] = None
    ):
        """
        Set cached response.

        Args:
            endpoint: API endpoint path
            data: Response data to cache
            ttl: Time-to-live in seconds (defaults to endpoint-based TTL)
            params: Query parameters
        """
        if not ENABLE_CACHING:
            return

        key = self._generate_cache_key(endpoint, params)
        if ttl is None:
            ttl = self._get_ttl_for_endpoint(endpoint)

        try:
            value = json.dumps(data)

            # Try Redis first
            if self._redis_client:
                self._redis_client.setex(key, ttl, value)
            else:
                # Fallback to in-memory cache
                self._memory_cache.set(key, value, ttl)

            self.metrics.sets += 1

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.metrics.errors += 1

    def delete(self, endpoint: str, params: Optional[Dict] = None):
        """
        Delete specific cached response.

        Args:
            endpoint: API endpoint path
            params: Query parameters
        """
        key = self._generate_cache_key(endpoint, params)

        try:
            if self._redis_client:
                self._redis_client.delete(key)
            else:
                self._memory_cache.delete(key)

            self.metrics.invalidations += 1

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.metrics.errors += 1

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "/api/stats/*")

        Example:
            cache.invalidate_pattern("/api/stats/*")  # Invalidate all stats endpoints
        """
        try:
            if self._redis_client:
                # Redis SCAN for pattern matching
                search_pattern = self._generate_cache_key(pattern, None).replace("*", "*")
                cursor = 0
                count = 0

                while True:
                    cursor, keys = self._redis_client.scan(cursor, match=search_pattern, count=100)
                    if keys:
                        self._redis_client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break

                logger.info(f"Invalidated {count} cache entries matching {pattern}")
                self.metrics.invalidations += count

            else:
                # In-memory cache: clear all (no pattern matching)
                self._memory_cache.clear()
                logger.info("Cleared in-memory cache (no pattern matching)")
                self.metrics.invalidations += 1

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            self.metrics.errors += 1

    def clear(self):
        """Clear all cache entries."""
        try:
            if self._redis_client:
                # Only clear keys with our prefix
                cursor = 0
                while True:
                    cursor, keys = self._redis_client.scan(
                        cursor, match=f"{CACHE_KEY_PREFIX}*", count=1000
                    )
                    if keys:
                        self._redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                self._memory_cache.clear()

            logger.info("Cache cleared")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.metrics.errors += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache metrics."""
        metrics_dict = self.metrics.to_dict()

        # Add cache size
        try:
            if self._redis_client:
                # Approximate size for Redis
                cursor, keys = self._redis_client.scan(0, match=f"{CACHE_KEY_PREFIX}*", count=1000)
                metrics_dict["cache_size"] = len(keys)
            else:
                metrics_dict["cache_size"] = self._memory_cache.size()
        except Exception:
            metrics_dict["cache_size"] = 0

        return metrics_dict


# Global cache instance
_api_cache: Optional[APICache] = None


def get_api_cache() -> APICache:
    """Get or create global API cache instance."""
    global _api_cache
    if _api_cache is None:
        _api_cache = APICache()
    return _api_cache


def cached_endpoint(
    ttl: Optional[int] = None,
    invalidate_on: Optional[List[str]] = None
):
    """
    Decorator for caching FastAPI endpoint responses.

    Args:
        ttl: Cache TTL in seconds (None = use endpoint default)
        invalidate_on: List of endpoint patterns to invalidate this cache

    Usage:
        @router.get("/api/stats/summary")
        @cached_endpoint(ttl=30)
        async def get_stats_summary():
            # Expensive computation
            return {"stats": ...}

    Example with invalidation:
        @router.post("/api/hands/new")
        @cached_endpoint(invalidate_on=["/api/stats/*", "/api/dashboard/*"])
        async def create_hand(hand_data):
            # Create new hand
            # This will invalidate stats and dashboard caches
            return {"id": ...}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_api_cache()

            # Extract request from args/kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            # Generate cache key from endpoint path and query params
            if request:
                endpoint = str(request.url.path)
                params = dict(request.query_params)

                # Try to get from cache
                cached_response = cache.get(endpoint, params)
                if cached_response is not None:
                    logger.debug(f"Cache hit for {endpoint}")
                    return JSONResponse(content=cached_response)

            # Call original function
            response = await func(*args, **kwargs)

            # Cache the response
            if request:
                # Extract response data
                if isinstance(response, JSONResponse):
                    response_data = response.body.decode() if hasattr(response.body, 'decode') else response.body
                    cache.set(endpoint, json.loads(response_data), ttl, params)
                elif isinstance(response, dict):
                    cache.set(endpoint, response, ttl, params)

            # Invalidate related caches if specified
            if invalidate_on:
                for pattern in invalidate_on:
                    cache.invalidate_pattern(pattern)
                    logger.debug(f"Invalidated cache pattern: {pattern}")

            return response

        return wrapper
    return decorator


# Export public API
__all__ = [
    'APICache',
    'CacheMetrics',
    'get_api_cache',
    'cached_endpoint',
    'ENABLE_CACHING',
]
