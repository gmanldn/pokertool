#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ML Model Lazy Loading and Caching
==================================

Provides lazy-loading and caching for ML models to reduce startup latency
and memory usage.

Module: pokertool.model_cache
Version: 1.0.0
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from functools import wraps
import weakref

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a cached model."""
    name: str
    file_path: Optional[Path] = None
    load_function: Optional[Callable] = None
    loaded_at: float = 0.0
    access_count: int = 0
    last_accessed: float = 0.0
    memory_size_mb: float = 0.0
    warmup_priority: int = 0  # Higher = load first during warmup


class ModelCache:
    """
    Lazy-loading cache for ML models with memory management.

    Features:
    - Lazy loading: Models only loaded when first accessed
    - In-memory caching: Loaded models kept in memory
    - Weak references: Models can be garbage collected under memory pressure
    - Usage tracking: Track access patterns for optimization
    - Warmup support: Pre-load critical models during startup
    - Thread-safe: Safe for concurrent access
    """

    def __init__(
        self,
        max_cache_size_mb: float = 1000.0,
        enable_weak_refs: bool = True,
        track_metrics: bool = True
    ):
        """
        Initialize model cache.

        Args:
            max_cache_size_mb: Maximum cache size in MB (0 = unlimited)
            enable_weak_refs: Use weak references for automatic cleanup
            track_metrics: Track access metrics
        """
        self._cache: Dict[str, Any] = {}
        self._weak_cache: Dict[str, Any] = {} if enable_weak_refs else None
        self._metadata: Dict[str, ModelMetadata] = {}
        self._lock = threading.RLock()
        self._max_cache_size_mb = max_cache_size_mb
        self._enable_weak_refs = enable_weak_refs
        self._track_metrics = track_metrics
        self._total_loads = 0
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info(
            f"ModelCache initialized: max_size={max_cache_size_mb}MB, "
            f"weak_refs={enable_weak_refs}, metrics={track_metrics}"
        )

    def register(
        self,
        name: str,
        load_function: Callable,
        file_path: Optional[Path] = None,
        warmup_priority: int = 0
    ) -> None:
        """
        Register a model for lazy loading.

        Args:
            name: Unique model name
            load_function: Function to call to load the model
            file_path: Optional path to model file
            warmup_priority: Priority for warmup (higher = load first)
        """
        with self._lock:
            self._metadata[name] = ModelMetadata(
                name=name,
                file_path=file_path,
                load_function=load_function,
                warmup_priority=warmup_priority
            )
            logger.debug(f"Registered model: {name} (priority={warmup_priority})")

    def get(self, name: str, force_reload: bool = False) -> Optional[Any]:
        """
        Get a model from cache, loading if necessary.

        Args:
            name: Model name
            force_reload: Force reload even if cached

        Returns:
            Loaded model or None if not found
        """
        with self._lock:
            # Check if registered
            if name not in self._metadata:
                logger.warning(f"Model not registered: {name}")
                return None

            metadata = self._metadata[name]

            # Try to get from strong cache first
            if not force_reload and name in self._cache:
                model = self._cache[name]
                if model is not None:
                    self._record_access(name, hit=True)
                    return model

            # Try weak cache if enabled
            if not force_reload and self._weak_cache and name in self._weak_cache:
                weak_ref = self._weak_cache[name]
                model = weak_ref()  # Dereference weak reference
                if model is not None:
                    # Promote back to strong cache
                    self._cache[name] = model
                    self._record_access(name, hit=True)
                    logger.debug(f"Model promoted from weak cache: {name}")
                    return model

            # Load model
            return self._load_model(name, metadata)

    def _load_model(self, name: str, metadata: ModelMetadata) -> Optional[Any]:
        """Load a model and cache it."""
        if not metadata.load_function:
            logger.error(f"No load function for model: {name}")
            return None

        try:
            start_time = time.time()
            logger.info(f"Loading model: {name}")

            model = metadata.load_function()

            load_time = time.time() - start_time
            metadata.loaded_at = start_time
            metadata.access_count = 1
            metadata.last_accessed = time.time()

            # Store in cache
            self._cache[name] = model

            # Also store weak reference if enabled
            if self._weak_cache is not None:
                self._weak_cache[name] = weakref.ref(model)

            self._total_loads += 1
            self._record_access(name, hit=False)

            logger.info(f"Model loaded successfully: {name} (took {load_time:.2f}s)")
            return model

        except Exception as e:
            logger.error(f"Failed to load model {name}: {e}", exc_info=True)
            return None

    def _record_access(self, name: str, hit: bool):
        """Record model access for metrics."""
        if not self._track_metrics:
            return

        metadata = self._metadata.get(name)
        if metadata:
            metadata.access_count += 1
            metadata.last_accessed = time.time()

        if hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1

    def warmup(self, max_models: Optional[int] = None):
        """
        Pre-load models by priority.

        Args:
            max_models: Maximum number of models to warm up (None = all)
        """
        with self._lock:
            # Sort models by warmup priority (highest first)
            sorted_models = sorted(
                self._metadata.items(),
                key=lambda x: x[1].warmup_priority,
                reverse=True
            )

            if max_models:
                sorted_models = sorted_models[:max_models]

            logger.info(f"Starting model warmup ({len(sorted_models)} models)...")
            start_time = time.time()

            for name, metadata in sorted_models:
                if metadata.warmup_priority > 0:
                    self.get(name)

            warmup_time = time.time() - start_time
            logger.info(f"Model warmup complete ({warmup_time:.2f}s)")

    def clear(self, name: Optional[str] = None):
        """
        Clear cache for specific model or all models.

        Args:
            name: Model name to clear (None = clear all)
        """
        with self._lock:
            if name:
                self._cache.pop(name, None)
                if self._weak_cache:
                    self._weak_cache.pop(name, None)
                logger.info(f"Cleared cache for model: {name}")
            else:
                self._cache.clear()
                if self._weak_cache:
                    self._weak_cache.clear()
                logger.info("Cleared all model cache")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.

        Returns:
            Dict with metrics
        """
        with self._lock:
            total_accesses = self._cache_hits + self._cache_misses
            hit_rate = (
                (self._cache_hits / total_accesses * 100)
                if total_accesses > 0
                else 0.0
            )

            return {
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate_percent": round(hit_rate, 2),
                "total_loads": self._total_loads,
                "cached_models": len(self._cache),
                "registered_models": len(self._metadata),
                "models": {
                    name: {
                        "access_count": meta.access_count,
                        "loaded_at": meta.loaded_at,
                        "last_accessed": meta.last_accessed,
                        "in_cache": name in self._cache,
                    }
                    for name, meta in self._metadata.items()
                },
            }


# Global cache instance
_global_cache: Optional[ModelCache] = None
_cache_lock = threading.Lock()


def get_model_cache() -> ModelCache:
    """Get or create the global model cache instance."""
    global _global_cache
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = ModelCache()
    return _global_cache


def lazy_model(name: str, warmup_priority: int = 0):
    """
    Decorator to make a model loading function use lazy loading.

    Usage:
        @lazy_model("hand_evaluator", warmup_priority=10)
        def load_hand_evaluator():
            return joblib.load("models/hand_evaluator.pkl")

        # Model only loaded on first call
        model = load_hand_evaluator()

    Args:
        name: Unique model name
        warmup_priority: Priority for warmup (0 = not warmed up)
    """
    def decorator(func: Callable) -> Callable:
        # Register the model
        cache = get_model_cache()
        cache.register(name, func, warmup_priority=warmup_priority)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ignore any arguments - lazy models should be parameter-free
            return cache.get(name)

        return wrapper

    return decorator
