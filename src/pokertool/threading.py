"""
Multi-threading and Async Support Module
Provides thread pool management, async operations, and concurrent processing
for performance-critical operations in the poker tool.
"""

import asyncio
import threading
import queue
import time
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable, TypeVar, Generic
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import multiprocessing
import functools
import weakref

logger = logging.getLogger(__name__)

T = TypeVar('T')

class TaskPriority(Enum):
    """Task priority levels for the thread pool."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TaskResult:
    """Result container for threaded tasks."""
    task_id: str
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    completed_at: float = field(default_factory=time.time)

@dataclass
class ThreadPoolConfig:
    """Configuration for thread pool management."""
    max_workers: int = None  # None = CPU count
    max_queue_size: int = 1000
    thread_name_prefix: str = 'PokerTool'
    daemon_threads: bool = True
    monitor_interval: float = 5.0

    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = min(32, (multiprocessing.cpu_count() or 1) + 4)

class ThreadSafeCounter:
    """Thread-safe counter for monitoring."""

    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self) -> int:
        """Increment counter and return new value."""
        with self._lock:
            self._value += 1
            return self._value

    def decrement(self) -> int:
        """Decrement counter and return new value."""
        with self._lock:
            self._value -= 1
            return self._value

    @property
    def value(self) -> int:
        """Get current value."""
        with self._lock:
            return self._value

class ThreadSafeDict(Generic[T]):
    """Thread-safe dictionary implementation."""

    def __init__(self):
        self._data: Dict[str, T] = {}
        self._lock = threading.RLock()

    def get(self, key: str, default: T = None) -> T:
        """Get value by key."""
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: T) -> None:
        """Set value by key."""
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> bool:
        """Delete key and return success."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def keys(self) -> List[str]:
        """Get all keys."""
        with self._lock:
            return list(self._data.keys())

    def values(self) -> List[T]:
        """Get all values."""
        with self._lock:
            return list(self._data.values())

    def items(self) -> List[tuple]:
        """Get all items."""
        with self._lock:
            return list(self._data.items())

    def clear(self) -> None:
        """Clear all data."""
        with self._lock:
            self._data.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

class TaskQueue:
    """Priority-based task queue for threading operations."""

    def __init__(self, maxsize: int = 0):
        self._queues = {
            TaskPriority.CRITICAL: queue.Queue(maxsize),
            TaskPriority.HIGH: queue.Queue(maxsize),
            TaskPriority.NORMAL: queue.Queue(maxsize),
            TaskPriority.LOW: queue.Queue(maxsize)
        }
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._task_count = ThreadSafeCounter()

    def put(self, item: Any, priority: TaskPriority = TaskPriority.NORMAL) -> None:
        """Add item to queue with specified priority."""
        with self._not_empty:
            self._queues[priority].put(item)
            self._task_count.increment()
            self._not_empty.notify()

    def get(self, timeout: Optional[float] = None) -> Any:
        """Get highest priority item from queue."""
        with self._not_empty:
            end_time = time.time() + timeout if timeout else None

            while True:
                # Check queues in priority order
                for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                               TaskPriority.NORMAL, TaskPriority.LOW]:
                    try:
                        item = self._queues[priority].get_nowait()
                        self._task_count.decrement()
                        return item
                    except queue.Empty:
                        continue

                # No items available, wait
                if timeout is not None and time.time() >= end_time:
                    raise queue.Empty

                self._not_empty.wait(timeout=0.1)

    def qsize(self) -> int:
        """Get total queue size across all priorities."""
        return self._task_count.value

    def empty(self) -> bool:
        """Check if all queues are empty."""
        return self._task_count.value == 0

class PokerThreadPool:
    """
    Advanced thread pool manager for poker tool operations.
    Supports priority queuing, monitoring, and resource management.
    """

    def __init__(self, config: Optional[ThreadPoolConfig] = None):
        self.config = config or ThreadPoolConfig()
        self.executor = None
        self.process_pool = None
        self._task_queue = TaskQueue(self.config.max_queue_size)
        self._active_tasks = ThreadSafeDict[Future]()
        self._completed_tasks = ThreadSafeDict[TaskResult]()
        self._worker_threads = []
        self._shutdown = threading.Event()
        self._monitor_thread = None
        self._stats = {
            'tasks_submitted': ThreadSafeCounter(),
            'tasks_completed': ThreadSafeCounter(),
            'tasks_failed': ThreadSafeCounter(),
            'total_execution_time': 0.0
        }

        self._initialize_pools()

    def _initialize_pools(self):
        """Initialize thread and process pools."""
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix=self.config.thread_name_prefix
        )

        # Process pool for CPU-intensive tasks
        self.process_pool = ProcessPoolExecutor(
            max_workers=min(4, multiprocessing.cpu_count() or 1)
        )

        # Start worker threads for priority queue
        for i in range(self.config.max_workers // 2):  # Use half for priority queue
            worker = threading.Thread(
                target=self._priority_worker,
                name=f"{self.config.thread_name_prefix}-PriorityWorker-{i}",
                daemon=self.config.daemon_threads
            )
            worker.start()
            self._worker_threads.append(worker)

        # Start monitoring thread
        if self.config.monitor_interval > 0:
            self._monitor_thread = threading.Thread(
                target=self._monitor_worker,
                name=f'{self.config.thread_name_prefix}-Monitor',
                daemon=True
            )
            self._monitor_thread.start()

        logger.info(f"Thread pool initialized: {self.config.max_workers} threads")

    def _priority_worker(self):
        """Worker thread for priority task queue."""
        while not self._shutdown.is_set():
            try:
                task_func, args, kwargs, task_id = self._task_queue.get(timeout=1.0)

                start_time = time.time()
                try:
                    result = task_func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    self._completed_tasks.set(task_id, TaskResult(
                        task_id=task_id,
                        result=result,
                        execution_time=execution_time
                    ))

                    self._stats['tasks_completed'].increment()
                    self._stats['total_execution_time'] += execution_time

                except Exception as e:
                    execution_time = time.time() - start_time
                    self._completed_tasks.set(task_id, TaskResult(
                        task_id=task_id,
                        error=e,
                        execution_time=execution_time
                    ))

                    self._stats['tasks_failed'].increment()
                    logger.error(f'Task {task_id} failed: {e}')

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f'Priority worker error: {e}')

    def _monitor_worker(self):
        """Monitor thread for performance metrics."""
        while not self._shutdown.is_set():
            try:
                stats = self.get_stats()
                logger.debug(f'Thread pool stats: {stats}')

                # Clean up old completed tasks (keep last 1000)
                completed_keys = self._completed_tasks.keys()
                if len(completed_keys) > 1000:
                    # Remove oldest 200 tasks
                    for key in completed_keys[:200]:
                        self._completed_tasks.delete(key)

                self._shutdown.wait(self.config.monitor_interval)

            except Exception as e:
                logger.error(f'Monitor worker error: {e}')

    def submit_priority_task(self, func: Callable, *args, 
                           priority: TaskPriority = TaskPriority.NORMAL, **kwargs) -> str:
        """Submit a task to the priority queue."""
        task_id = f"task_{int(time.time() * 1000000)}_{threading.get_ident()}"

        self._task_queue.put((func, args, kwargs, task_id), priority)
        self._stats['tasks_submitted'].increment()

        return task_id

    def submit_thread_task(self, func: Callable, *args, **kwargs) -> Future:
        """Submit a task to the regular thread pool."""
        future = self.executor.submit(func, *args, **kwargs)
        self._active_tasks.set(id(future), future)
        self._stats['tasks_submitted'].increment()
        return future

    def submit_process_task(self, func: Callable, *args, **kwargs) -> Future:
        """Submit a CPU-intensive task to the process pool."""
        future = self.process_pool.submit(func, *args, **kwargs)
        self._active_tasks.set(id(future), future)
        self._stats['tasks_submitted'].increment()
        return future

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """Get result of a priority task."""
        end_time = time.time() + timeout if timeout else None

        while True:
            result = self._completed_tasks.get(task_id)
            if result:
                return result

            if timeout and time.time() >= end_time:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")

            time.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics."""
        return {
            'submitted': self._stats['tasks_submitted'].value,
            'completed': self._stats['tasks_completed'].value,
            'failed': self._stats['tasks_failed'].value,
            'active_tasks': len(self._active_tasks),
            'queue_size': self._task_queue.qsize(),
            'avg_execution_time': (
                self._stats['total_execution_time'] / max(1, self._stats['tasks_completed'].value)
            ),
            'worker_threads': len(self._worker_threads),
            'max_workers': self.config.max_workers
        }

    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool."""
        logger.info('Shutting down thread pool...')

        self._shutdown.set()

        if wait:
            # Wait for priority workers to finish
            for worker in self._worker_threads:
                worker.join(timeout=2.0)

        # Shutdown executors
        self.executor.shutdown(wait=wait)
        self.process_pool.shutdown(wait=wait)

        logger.info('Thread pool shutdown complete')

# Global instances
_global_thread_pool: Optional[PokerThreadPool] = None

def get_thread_pool() -> PokerThreadPool:
    """Get the global thread pool instance."""
    global _global_thread_pool
    if _global_thread_pool is None:
        _global_thread_pool = PokerThreadPool()
    return _global_thread_pool

# Decorators for threading support
def threaded(priority: TaskPriority = TaskPriority.NORMAL):
    """Decorator to run function in thread pool with priority."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            thread_pool = get_thread_pool()
            task_id = thread_pool.submit_priority_task(func, *args, priority=priority, **kwargs)
            return thread_pool.get_task_result(task_id)
        return wrapper
    return decorator

def cpu_intensive(func: Callable) -> Callable:
    """Decorator for CPU-intensive functions to use process pool."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread_pool = get_thread_pool()
        future = thread_pool.submit_process_task(func, *args, **kwargs)
        return future.result()
    return wrapper
