"""
Threading utilities for PokerTool.
Provides thread-safe utilities and helpers for concurrent operations.
"""

import threading
import time
import logging
from typing import Any, Callable, Optional, Dict, List, Enum
from concurrent.futures import ThreadPoolExecutor, Future
import functools
import weakref

# Configure logging
logger = logging.getLogger(__name__)

# Global thread pool for PokerTool operations
_thread_pool: Optional[ThreadPoolExecutor] = None
_thread_pool_lock = threading.Lock()

# Thread-local storage for PokerTool state
_local = threading.local()

class ThreadSafeDict:
    """A thread-safe dictionary implementation."""
    
    def __init__(self):
        self._dict = {}
        self._lock = threading.RLock()
    
    def __getitem__(self, key):
        with self._lock:
            return self._dict[key]
    
    def __setitem__(self, key, value):
        with self._lock:
            self._dict[key] = value
    
    def __delitem__(self, key):
        with self._lock:
            del self._dict[key]
    
    def __contains__(self, key):
        with self._lock:
            return key in self._dict
    
    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)
    
    def keys(self):
        with self._lock:
            return list(self._dict.keys())
    
    def values(self):
        with self._lock:
            return list(self._dict.values())
    
    def items(self):
        with self._lock:
            return list(self._dict.items())
    
    def clear(self):
        with self._lock:
            self._dict.clear()

class ThreadSafeCounter:
    """A thread-safe counter."""
    
    def __init__(self, initial_value=0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, amount=1):
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount=1):
        with self._lock:
            self._value -= amount
            return self._value
    
    @property
    def value(self):
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
                max_workers=max_workers,
                thread_name_prefix="PokerTool"
            )
            logger.debug(f"Created thread pool with {max_workers} workers")
    
    return _thread_pool

def shutdown_thread_pool(wait: bool = True) -> None:
    """Shutdown the global thread pool."""
    global _thread_pool
    
    with _thread_pool_lock:
        if _thread_pool is not None:
            _thread_pool.shutdown(wait=wait)
            _thread_pool = None
            logger.debug("Thread pool shut down")

def run_in_thread(func: Callable, *args, **kwargs) -> Future:
    """Run a function in the thread pool."""
    pool = get_thread_pool()
    return pool.submit(func, *args, **kwargs)

def thread_safe(func: Callable) -> Callable:
    """Decorator to make a function thread-safe using a lock."""
    lock = threading.RLock()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)
    
    return wrapper

def with_timeout(timeout: float):
    """Decorator to add timeout to a function."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            if thread.is_alive():
                logger.warning(f"Function {func.__name__} timed out after {timeout}s")
                raise TimeoutError(f"Function timed out after {timeout} seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator

class AsyncCallback:
    """Manages asynchronous callbacks."""
    
    def __init__(self):
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
    
    def trigger(self, event: str, *args, **kwargs) -> List[Future]:
        """Trigger all callbacks for an event asynchronously."""
        futures = []
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    future = run_in_thread(callback, *args, **kwargs)
                    futures.append(future)
                except Exception as e:
                    logger.error(f"Error triggering callback: {e}")
        return futures

# Global callback manager
_callback_manager = AsyncCallback()

def register_callback(event: str, callback: Callable) -> None:
    """Register a global callback."""
    _callback_manager.register(event, callback)

def trigger_callbacks(event: str, *args, **kwargs) -> List[Future]:
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

# Cleanup function
def cleanup_threading() -> None:
    """Clean up threading resources."""
    shutdown_thread_pool()
    clear_thread_local()

# Export commonly used items
__all__ = [
    'TaskPriority',
    'ThreadSafeDict',
    'ThreadSafeCounter', 
    'get_thread_pool',
    'shutdown_thread_pool',
    'run_in_thread',
    'thread_safe',
    'with_timeout',
    'AsyncCallback',
    'register_callback',
    'trigger_callbacks',
    'get_thread_local',
    'set_thread_local',
    'clear_thread_local',
    'cleanup_threading'
]
