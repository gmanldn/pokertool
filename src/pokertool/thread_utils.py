"""
Threading utilities for PokerTool.
Provides thread-safe utilities and helpers for concurrent operations.
"""

from __future__ import annotations

import functools
import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Global thread pool for PokerTool operations
_thread_pool: Optional[ThreadPoolExecutor] = None
_thread_pool_lock = threading.Lock()

# Thread-local storage for PokerTool state
_local = threading.local()


class ThreadSafeDict:
    """A thread-safe dictionary implementation."""

    def __init__(self) -> None:
        self._dict: Dict[Any, Any] = {}
        self._lock = threading.RLock()

    def __getitem__(self, key: Any) -> Any:
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key: Any) -> None:
        with self._lock:
            del self._dict[key]

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            return key in self._dict

    def get(self, key: Any, default: Any = None) -> Any:
        with self._lock:
            return self._dict.get(key, default)

    def keys(self) -> List[Any]:
        with self._lock:
            return list(self._dict.keys())

    def values(self) -> List[Any]:
        with self._lock:
            return list(self._dict.values())

    def items(self) -> List[Any]:
        with self._lock:
            return list(self._dict.items())

    def clear(self) -> None:
        with self._lock:
            self._dict.clear()


class ThreadSafeCounter:
    """A thread-safe counter."""

    def __init__(self, initial_value: int = 0) -> None:
        self._value = initial_value
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> int:
        with self._lock:
            self._value += amount
            return self._value

    def decrement(self, amount: int = 1) -> int:
        with self._lock:
            self._value -= amount
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


class TaskPriority(Enum):
    """Task priority levels for the thread pool."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


def get_thread_pool(max_workers: int = 4) -> ThreadPoolExecutor:
    """Get or create the global thread pool."""
    global _thread_pool

    with _thread_pool_lock:
        if _thread_pool is None:
            _thread_pool = ThreadPoolExecutor(
                max_workers=max_workers, thread_name_prefix="PokerTool"
            )
            logger.debug("Created thread pool with %d workers", max_workers)

    return _thread_pool


def shutdown_thread_pool(wait: bool = True) -> None:
    """Shutdown the global thread pool."""
    global _thread_pool

    with _thread_pool_lock:
        if _thread_pool is not None:
            _thread_pool.shutdown(wait=wait)
            _thread_pool = None
            logger.debug("Thread pool shut down")


def run_in_thread(func: Callable, *args: Any, **kwargs: Any) -> Future:
    """Run a function in the thread pool."""
    pool = get_thread_pool()
    return pool.submit(func, *args, **kwargs)


def thread_safe(func: Callable) -> Callable:
    """Decorator to make a function thread-safe using a lock."""
    lock = threading.RLock()

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with lock:
            return func(*args, **kwargs)

    return wrapper


def with_timeout(timeout: float) -> Callable:
    """Decorator to add timeout to a function."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result: List[Any] = [None]
            exception: List[Optional[BaseException]] = [None]

            def target() -> None:
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - defensive logging
                    exception[0] = exc

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                logger.warning("Function %s timed out after %ss", func.__name__, timeout)
                raise TimeoutError(f"Function timed out after {timeout} seconds")

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper

    return decorator


class AsyncCallback:
    """Manages asynchronous callbacks."""

    def __init__(self) -> None:
        self._callbacks: Dict[str, List[Callable]] = ThreadSafeDict()

    def register(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def unregister(self, event: str, callback: Callable) -> None:
        """Unregister a callback for an event."""
        if event in self._callbacks:
            try:
                self._callbacks[event].remove(callback)
            except ValueError:
                pass

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> List[Future]:
        """Trigger all callbacks for an event asynchronously."""
        futures: List[Future] = []
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    future = run_in_thread(callback, *args, **kwargs)
                    futures.append(future)
                except Exception as exc:
                    logger.error("Error triggering callback: %s", exc)
        return futures


# Global callback manager
_callback_manager = AsyncCallback()


def register_callback(event: str, callback: Callable) -> None:
    """Register a global callback."""
    _callback_manager.register(event, callback)


def trigger_callbacks(event: str, *args: Any, **kwargs: Any) -> List[Future]:
    """Trigger global callbacks."""
    return _callback_manager.trigger(event, *args, **kwargs)


# Thread-local storage helpers
def get_thread_local(key: str, default: Any = None) -> Any:
    """Get a value from thread-local storage."""
    return getattr(_local, key, default)


def set_thread_local(key: str, value: Any) -> None:
    """Set a value in thread-local storage."""
    setattr(_local, key, value)


def clear_thread_local() -> None:
    """Clear all thread-local storage."""
    for attr in list(vars(_local).keys()):
        delattr(_local, attr)


def cleanup_threading() -> None:
    """Clean up threading resources."""
    shutdown_thread_pool()
    clear_thread_local()


__all__ = [
    "TaskPriority",
    "ThreadSafeDict",
    "ThreadSafeCounter",
    "get_thread_pool",
    "shutdown_thread_pool",
    "run_in_thread",
    "thread_safe",
    "with_timeout",
    "AsyncCallback",
    "register_callback",
    "trigger_callbacks",
    "get_thread_local",
    "set_thread_local",
    "clear_thread_local",
    "cleanup_threading",
]
