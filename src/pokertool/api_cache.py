#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Query Result Caching
=========================

Provides intelligent caching for database query results.

Features:
- In-memory LRU cache with TTL
- Automatic cache invalidation
- Query result caching with configurable TTL
- Cache statistics and monitoring
- Thread-safe operations
"""

from __future__ import annotations

import logging
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    ttl_seconds: int
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self):
        """Update last accessed time and increment hit count."""
        self.last_accessed = time.time()
        self.hit_count += 1


class QueryCache:
    """
    Thread-safe LRU cache with TTL for database query results.

    Example:
        cache = QueryCache(max_size=1000, default_ttl=300)

        # Cache a query result
        result = cache.get_or_compute(
            "recent_hands_limit_10",
            lambda: database.get_recent_hands(limit=10),
            ttl=60
        )
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300  # 5 minutes
    ):
        """Initialize cache."""
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            entry.touch()
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            entry = CacheEntry(key=key, value=value, created_at=time.time(), ttl_seconds=ttl)
            self._cache[key] = entry
            self._cache.move_to_end(key)
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """Get from cache or compute."""
        value = self.get(key)
        if value is not None:
            return value
        value = compute_fn()
        self.set(key, value, ttl=ttl)
        return value

    def invalidate(self, key: str) -> bool:
        """Invalidate cache entry."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': hit_rate,
            }

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Create cache key from arguments."""
        key_data = {'args': args, 'kwargs': kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
_global_cache: Optional[QueryCache] = None


def get_global_cache() -> QueryCache:
    """Get global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = QueryCache()
    return _global_cache
