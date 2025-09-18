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
    thread_name_prefix: str = "PokerTool"
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
        with self._lock:
            self._value += 1
            return self._value
    
    def decrement(self) -> int:
        with self._lock:
            self._value -= 1
            return self._value
    
    @property
    def value(self) -> int:
        with self._lock:
            return self._value

class ThreadSafeDict(Generic[T]):
    """Thread-safe dictionary implementation."""
    
    def __init__(self):
        self._data: Dict[str, T] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str, default: T = None) -> T:
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._data[key] = value
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def keys(self) -> List[str]:
        with self._lock:
            return list(self._data.keys())
    
    def values(self) -> List[T]:
        with self._lock:
            return list(self._data.values())
    
    def items(self) -> List[tuple]:
        with self._lock:
            return list(self._data.items())
    
    def clear(self) -> None:
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
                name=f"{self.config.thread_name_prefix}-Monitor",
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
                    logger.error(f"Task {task_id} failed: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Priority worker error: {e}")
    
    def _monitor_worker(self):
        """Monitor thread for performance metrics."""
        while not self._shutdown.is_set():
            try:
                stats = self.get_stats()
                logger.debug(f"Thread pool stats: {stats}")
                
                # Clean up old completed tasks (keep last 1000)
                completed_keys = self._completed_tasks.keys()
                if len(completed_keys) > 1000:
                    # Remove oldest 200 tasks
                    for key in completed_keys[:200]:
                        self._completed_tasks.delete(key)
                
                self._shutdown.wait(self.config.monitor_interval)
                
            except Exception as e:
                logger.error(f"Monitor worker error: {e}")
    
    def submit_priority_task(self, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL, **kwargs) -> str:
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
    
    def wait_for_tasks(self, timeout: Optional[float] = None) -> bool:
        """Wait for all active tasks to complete."""
        active_futures = list(self._active_tasks.values())
        
        if not active_futures:
            return True
        
        try:
            completed_futures = as_completed(active_futures, timeout=timeout)
            for _ in completed_futures:
                pass
            return True
        except TimeoutError:
            return False
    
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
        logger.info("Shutting down thread pool...")
        
        self._shutdown.set()
        
        if wait:
            # Wait for priority workers to finish
            for worker in self._worker_threads:
                worker.join(timeout=2.0)
        
        # Shutdown executors
        self.executor.shutdown(wait=wait)
        self.process_pool.shutdown(wait=wait)
        
        logger.info("Thread pool shutdown complete")

class AsyncManager:
    """Async operation manager for I/O intensive tasks."""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._shutdown = threading.Event()
        self._start_event = threading.Event()
    
    def start(self):
        """Start the async manager in a separate thread."""
        if self._thread is not None:
            return
        
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        self._start_event.wait(timeout=5.0)  # Wait for loop to start
    
    def _run_event_loop(self):
        """Run the event loop in a separate thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._start_event.set()
        
        try:
            self._loop.run_until_complete(self._async_worker())
        except Exception as e:
            logger.error(f"Async manager error: {e}")
        finally:
            self._loop.close()
    
    async def _async_worker(self):
        """Main async worker loop."""
        while not self._shutdown.is_set():
            try:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
    
    def run_coroutine(self, coro: Awaitable[T], timeout: Optional[float] = None) -> T:
        """Run a coroutine and return the result."""
        if self._loop is None:
            raise RuntimeError("Async manager not started")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)
    
    def shutdown(self):
        """Shutdown the async manager."""
        if self._loop is not None:
            self._shutdown.set()
            
            # Cancel all pending tasks
            if self._loop.is_running():
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
            
            if self._thread is not None:
                self._thread.join(timeout=2.0)

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

def async_threaded(func: Callable) -> Callable:
    """Decorator to run function asynchronously."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper

def cpu_intensive(func: Callable) -> Callable:
    """Decorator for CPU-intensive functions to use process pool."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread_pool = get_thread_pool()
        future = thread_pool.submit_process_task(func, *args, **kwargs)
        return future.result()
    return wrapper

# Parallel processing utilities

def parallel_map(func: Callable, iterable: List[Any], max_workers: Optional[int] = None) -> List[Any]:
    """Apply function to iterable in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(func, item) for item in iterable]
        return [future.result() for future in as_completed(futures)]

def parallel_equity_calculation(hands: List[str], board: str, num_simulations: int = 10000) -> List[float]:
    """Calculate equity for multiple hands in parallel."""
    @cpu_intensive
    def calculate_single_equity(hand: str) -> float:
        # Simplified equity calculation - would use proper poker evaluation
        import random
        random.seed(hash(hand + board))
        return random.uniform(0.0, 1.0)  # Placeholder
    
    return parallel_map(calculate_single_equity, hands)

# Global instances
_global_thread_pool: Optional[PokerThreadPool] = None
_global_async_manager: Optional[AsyncManager] = None

def get_thread_pool() -> PokerThreadPool:
    """Get the global thread pool instance."""
    global _global_thread_pool
    if _global_thread_pool is None:
        _global_thread_pool = PokerThreadPool()
    return _global_thread_pool

def get_async_manager() -> AsyncManager:
    """Get the global async manager instance."""
    global _global_async_manager
    if _global_async_manager is None:
        _global_async_manager = AsyncManager()
        _global_async_manager.start()
    return _global_async_manager

@contextmanager
def thread_pool_context(config: Optional[ThreadPoolConfig] = None):
    """Context manager for temporary thread pool."""
    pool = PokerThreadPool(config)
    try:
        yield pool
    finally:
        pool.shutdown()

# Shutdown hook
import atexit

def _cleanup():
    """Cleanup function called on exit."""
    global _global_thread_pool, _global_async_manager
    
    if _global_thread_pool is not None:
        _global_thread_pool.shutdown(wait=False)
        _global_thread_pool = None
    
    if _global_async_manager is not None:
        _global_async_manager.shutdown()
        _global_async_manager = None

atexit.register(_cleanup)

# Example usage and testing
if __name__ == '__main__':
    # Test thread pool functionality
    thread_pool = get_thread_pool()
    
    def test_task(n: int) -> int:
        time.sleep(0.1)  # Simulate work
        return n * n
    
    # Submit some priority tasks
    task_ids = []
    for i in range(10):
        priority = TaskPriority.HIGH if i % 2 == 0 else TaskPriority.NORMAL
        task_id = thread_pool.submit_priority_task(test_task, i, priority=priority)
        task_ids.append(task_id)
    
    # Get results
    results = []
    for task_id in task_ids:
        result = thread_pool.get_task_result(task_id, timeout=5.0)
        results.append(result.result)
        print(f"Task {task_id}: {result.result} (took {result.execution_time:.3f}s)")
    
    # Show stats
    stats = thread_pool.get_stats()
    print(f"Thread pool stats: {stats}")
    
    # Test parallel equity calculation
    test_hands = ['AsKh', 'QdQc', 'JhTs', 'AcKd', '8h8s']
    equities = parallel_equity_calculation(test_hands, 'AdKcQh')
    print(f"Equities: {equities}")
