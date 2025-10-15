#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPE-017: Smart OCR Result Caching
====================================

Cache OCR results and invalidate only when region changes.
Expected improvement: 2-3x faster for stable elements (player names, blinds).

Module: pokertool.smart_ocr_cache
Version: 1.0.0
Created: 2025-10-15
Author: PokerTool Development Team
License: MIT
"""

__version__ = '1.0.0'

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CachedResult:
    """Cached OCR result."""
    result: Any
    region_hash: str
    timestamp: float
    hit_count: int = 0
    
    def is_expired(self, ttl_seconds: float = 300.0) -> bool:
        """Check if cache entry is expired."""
        return (time.time() - self.timestamp) > ttl_seconds


@dataclass
class CacheMetrics:
    """Metrics for OCR cache."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_invalidations: int = 0
    hit_rate: float = 0.0
    avg_hit_count: float = 0.0
    
    def update_hit(self):
        """Record cache hit."""
        self.total_requests += 1
        self.cache_hits += 1
        self._update_hit_rate()
    
    def update_miss(self):
        """Record cache miss."""
        self.total_requests += 1
        self.cache_misses += 1
        self._update_hit_rate()
    
    def update_invalidation(self):
        """Record cache invalidation."""
        self.cache_invalidations += 1
    
    def _update_hit_rate(self):
        """Update hit rate."""
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests


class SmartOCRCache:
    """
    LRU cache for OCR results with hash-based invalidation.
    
    Caches OCR results keyed by (region_hash, extraction_type).
    Invalidates when region pixels change.
    """
    
    def __init__(self, max_entries: int = 1000, ttl_seconds: float = 300.0):
        """
        Initialize smart OCR cache.
        
        Args:
            max_entries: Maximum number of cache entries (LRU eviction)
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[Tuple[str, str], CachedResult] = OrderedDict()
        self.metrics = CacheMetrics()
        
        logger.info(f"Smart OCR cache initialized (max_entries={max_entries}, ttl={ttl_seconds}s)")
    
    def _compute_region_hash(self, region: np.ndarray) -> str:
        """
        Compute fast, collision-resistant hash for a region.
        
        Args:
            region: Image region (numpy array)
            
        Returns:
            Hash string
        """
        try:
            # Downsample to 16x16 for fast hashing
            try:
                import cv2
                small = cv2.resize(region, (16, 16), interpolation=cv2.INTER_AREA)
            except ImportError:
                from PIL import Image
                pil_img = Image.fromarray(region)
                pil_img = pil_img.resize((16, 16), Image.LANCZOS)
                small = np.array(pil_img)
            
            # Use SHA256 for better collision resistance than MD5
            hash_bytes = small.tobytes()
            return hashlib.sha256(hash_bytes).hexdigest()[:32]
            
        except Exception as e:
            logger.debug(f"Hash computation failed: {e}")
            # Return unique hash based on timestamp to force miss
            return f"error_{time.time()}"
    
    def get(
        self,
        region: np.ndarray,
        extraction_type: str,
        compute_fn: callable = None
    ) -> Tuple[Any, bool]:
        """
        Get cached OCR result or compute if not cached.
        
        Args:
            region: Image region to process
            extraction_type: Type of extraction (e.g., 'player_name', 'pot', 'cards')
            compute_fn: Function to compute result if not cached (takes region as arg)
            
        Returns:
            Tuple of (result, was_cached)
        """
        # Compute hash for this region
        region_hash = self._compute_region_hash(region)
        cache_key = (region_hash, extraction_type)
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            
            # Check if expired
            if cached.is_expired(self.ttl_seconds):
                # Remove expired entry
                del self.cache[cache_key]
                self.metrics.update_invalidation()
                logger.debug(f"Cache entry expired for {extraction_type}")
            else:
                # Cache hit - move to end (most recent)
                self.cache.move_to_end(cache_key)
                cached.hit_count += 1
                self.metrics.update_hit()
                logger.debug(
                    f"Cache HIT for {extraction_type} "
                    f"(hit_count={cached.hit_count}, hit_rate={self.metrics.hit_rate:.1%})"
                )
                return cached.result, True
        
        # Cache miss - compute result
        self.metrics.update_miss()
        
        if compute_fn is None:
            logger.debug(f"Cache MISS for {extraction_type} (no compute function)")
            return None, False
        
        try:
            result = compute_fn(region)
        except Exception as e:
            logger.error(f"OCR computation failed for {extraction_type}: {e}")
            return None, False
        
        # Store in cache
        self.cache[cache_key] = CachedResult(
            result=result,
            region_hash=region_hash,
            timestamp=time.time(),
            hit_count=0
        )
        
        # Evict oldest if over limit
        if len(self.cache) > self.max_entries:
            evicted_key = next(iter(self.cache))
            del self.cache[evicted_key]
            logger.debug(f"Cache evicted entry (size={len(self.cache)})")
        
        logger.debug(
            f"Cache MISS for {extraction_type} "
            f"(computed and cached, hit_rate={self.metrics.hit_rate:.1%})"
        )
        
        return result, False
    
    def invalidate(self, extraction_type: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            extraction_type: If specified, only invalidate this type.
                           If None, invalidate all.
        """
        if extraction_type is None:
            # Invalidate all
            count = len(self.cache)
            self.cache.clear()
            self.metrics.cache_invalidations += count
            logger.info(f"Cache invalidated all {count} entries")
        else:
            # Invalidate specific type
            keys_to_remove = [
                key for key in self.cache.keys()
                if key[1] == extraction_type
            ]
            for key in keys_to_remove:
                del self.cache[key]
                self.metrics.update_invalidation()
            logger.info(f"Cache invalidated {len(keys_to_remove)} entries for {extraction_type}")
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, cached in self.cache.items()
            if cached.is_expired(self.ttl_seconds)
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.metrics.update_invalidation()
        
        if expired_keys:
            logger.debug(f"Cache cleaned up {len(expired_keys)} expired entries")
    
    def get_metrics(self) -> dict:
        """Get cache metrics."""
        if self.cache:
            avg_hit_count = sum(c.hit_count for c in self.cache.values()) / len(self.cache)
        else:
            avg_hit_count = 0.0
        
        return {
            'total_requests': self.metrics.total_requests,
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses,
            'cache_invalidations': self.metrics.cache_invalidations,
            'hit_rate': f"{self.metrics.hit_rate:.1%}",
            'cache_size': len(self.cache),
            'max_entries': self.max_entries,
            'avg_hit_count': f"{avg_hit_count:.1f}",
            'memory_saved_estimate': f"{self.metrics.cache_hits * 0.05:.1f}s"  # Assume 50ms per OCR
        }
    
    def reset(self):
        """Reset cache and metrics."""
        self.cache.clear()
        self.metrics = CacheMetrics()
        logger.info("Smart OCR cache reset")


# Global singleton
_ocr_cache: Optional[SmartOCRCache] = None


def get_ocr_cache(max_entries: int = 1000, ttl_seconds: float = 300.0) -> SmartOCRCache:
    """Get global OCR cache instance."""
    global _ocr_cache
    if _ocr_cache is None:
        _ocr_cache = SmartOCRCache(max_entries=max_entries, ttl_seconds=ttl_seconds)
    return _ocr_cache


def reset_ocr_cache():
    """Reset global OCR cache."""
    global _ocr_cache
    if _ocr_cache:
        _ocr_cache.reset()


if __name__ == '__main__':
    # Test OCR cache
    print("Smart OCR Cache Test")
    
    cache = SmartOCRCache(max_entries=100, ttl_seconds=60)
    
    # Create test regions
    region1 = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)
    region2 = region1.copy()  # Same content
    region3 = np.random.randint(0, 255, (50, 100, 3), dtype=np.uint8)  # Different
    
    # Mock OCR function
    call_count = 0
    def mock_ocr(region):
        nonlocal call_count
        call_count += 1
        return f"Result_{call_count}"
    
    # Test 1: First access (cache miss)
    result1, cached1 = cache.get(region1, 'player_name', mock_ocr)
    print(f"Test 1: result={result1}, cached={cached1}, ocr_calls={call_count}")
    
    # Test 2: Same region (cache hit)
    result2, cached2 = cache.get(region2, 'player_name', mock_ocr)
    print(f"Test 2: result={result2}, cached={cached2}, ocr_calls={call_count}")
    
    # Test 3: Different region (cache miss)
    result3, cached3 = cache.get(region3, 'player_name', mock_ocr)
    print(f"Test 3: result={result3}, cached={cached3}, ocr_calls={call_count}")
    
    # Test 4: First region again (cache hit)
    result4, cached4 = cache.get(region1, 'player_name', mock_ocr)
    print(f"Test 4: result={result4}, cached={cached4}, ocr_calls={call_count}")
    
    # Show metrics
    metrics = cache.get_metrics()
    print(f"\nMetrics:")
    print(f"  Total requests: {metrics['total_requests']}")
    print(f"  Hit rate: {metrics['hit_rate']}")
    print(f"  Cache size: {metrics['cache_size']}")
    print(f"  Memory saved: {metrics['memory_saved_estimate']}")
