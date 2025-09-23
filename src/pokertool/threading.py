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

# Async support for I/O operations
class AsyncManager:
    """Manager for async I/O operations in poker tool."""
    
    def __init__(self):
        self._loop = None
        self._executor = None
        self._db_semaphore = None
        self._api_semaphore = None
        
    async def initialize(self):
        """Initialize async manager."""
        self._loop = asyncio.get_running_loop()
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix='AsyncIO')
        self._db_semaphore = asyncio.Semaphore(5)  # Limit concurrent DB operations
        self._api_semaphore = asyncio.Semaphore(3)  # Limit concurrent API calls
        
    async def run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """Run blocking function in executor."""
        if kwargs:
            partial_func = functools.partial(func, **kwargs)
            return await self._loop.run_in_executor(self._executor, partial_func, *args)
        else:
            return await self._loop.run_in_executor(self._executor, func, *args)
    
    async def concurrent_database_ops(self, operations: List[Callable]) -> List[Any]:
        """Execute database operations concurrently with semaphore control."""
        async def _db_operation(op):
            async with self._db_semaphore:
                return await self.run_in_executor(op)
        
        tasks = [_db_operation(op) for op in operations]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def concurrent_api_calls(self, calls: List[Callable]) -> List[Any]:
        """Execute API calls concurrently with rate limiting."""
        async def _api_call(call):
            async with self._api_semaphore:
                # Add delay to prevent rate limiting
                await asyncio.sleep(0.1)
                return await self.run_in_executor(call)
        
        tasks = [_api_call(call) for call in calls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def batch_process(self, items: List[Any], processor: Callable, 
                           batch_size: int = 10) -> List[Any]:
        """Process items in batches asynchronously."""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [self.run_in_executor(processor, item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches to prevent overload
            if i + batch_size < len(items):
                await asyncio.sleep(0.05)
        
        return results
    
    def close(self):
        """Clean up async manager resources."""
        if self._executor:
            self._executor.shutdown(wait=False)

# Poker-specific concurrent operations
class PokerConcurrencyManager:
    """Specialized concurrency manager for poker operations."""
    
    def __init__(self):
        self.thread_pool = get_thread_pool()
        self.async_manager = AsyncManager()
        
    async def parallel_equity_calculation(self, scenarios: List[Dict[str, Any]], 
                                        iterations: int = 100000) -> List[float]:
        """Calculate equity for multiple scenarios in parallel."""
        try:
            from .gto_solver import EquityCalculator
            calc = EquityCalculator()
            
            def calculate_scenario_equity(scenario):
                hands = scenario.get('hands', [])
                board = scenario.get('board', [])
                return calc.calculate_equity(hands, board, iterations // 10)  # Reduced iterations per worker
            
            # Submit to process pool for CPU-intensive calculation
            futures = []
            for scenario in scenarios:
                future = self.thread_pool.submit_process_task(calculate_scenario_equity, scenario)
                futures.append(future)
            
            # Collect results
            results = []
            for future in as_completed(futures):
                try:
                    equity_results = future.result(timeout=30)
                    results.extend(equity_results if isinstance(equity_results, list) else [equity_results])
                except Exception as e:
                    logger.error(f"Equity calculation failed: {e}")
                    results.append(0.0)
            
            return results
            
        except ImportError:
            logger.warning("GTO solver not available for equity calculations")
            return [0.0] * len(scenarios)
    
    async def concurrent_hand_analysis(self, hands: List[Dict[str, Any]]) -> List[Any]:
        """Analyze multiple hands concurrently."""
        try:
            from .core import analyse_hand, parse_card
            
            def analyze_single_hand(hand_data):
                try:
                    hole_cards = [parse_card(card) for card in hand_data.get('hole_cards', [])]
                    board_cards = [parse_card(card) for card in hand_data.get('board_cards', [])] if hand_data.get('board_cards') else None
                    
                    return analyse_hand(
                        hole_cards,
                        board_cards,
                        position=hand_data.get('position'),
                        pot=hand_data.get('pot', 0),
                        to_call=hand_data.get('to_call', 0)
                    )
                except Exception as e:
                    logger.error(f"Hand analysis failed: {e}")
                    return None
            
            # Process in batches to avoid overwhelming the system
            return await self.async_manager.batch_process(hands, analyze_single_hand, batch_size=20)
            
        except ImportError:
            logger.warning("Core analysis functions not available")
            return [None] * len(hands)
    
    async def parallel_opponent_modeling(self, player_data: List[Dict[str, Any]]) -> List[Any]:
        """Update opponent models concurrently."""
        try:
            from .ml_opponent_modeling import get_opponent_modeling_system
            
            ml_system = get_opponent_modeling_system()
            
            def update_player_model(player_info):
                try:
                    player_id = player_info.get('player_id')
                    hand_history = player_info.get('hand_history')
                    if player_id and hand_history:
                        return ml_system.observe_hand(hand_history)
                    return False
                except Exception as e:
                    logger.error(f"Player model update failed: {e}")
                    return False
            
            # Use thread pool for ML operations (not process pool due to model state)
            futures = []
            for player_info in player_data:
                future = self.thread_pool.submit_thread_task(update_player_model, player_info)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Opponent modeling task failed: {e}")
                    results.append(False)
            
            return results
            
        except ImportError:
            logger.warning("ML opponent modeling not available")
            return [False] * len(player_data)
    
    async def concurrent_database_operations(self, operations: List[Callable]) -> List[Any]:
        """Execute database operations concurrently."""
        return await self.async_manager.concurrent_database_ops(operations)
    
    async def parallel_gto_solving(self, game_states: List[Any]) -> List[Any]:
        """Solve multiple GTO spots in parallel."""
        try:
            from .gto_solver import get_gto_solver, create_standard_ranges
            
            gto_solver = get_gto_solver()
            standard_ranges = create_standard_ranges()
            
            def solve_game_state(game_state):
                try:
                    return gto_solver.solve(
                        game_state, 
                        standard_ranges,
                        max_iterations=1000  # Reduced iterations for parallel processing
                    )
                except Exception as e:
                    logger.error(f"GTO solving failed: {e}")
                    return None
            
            # Use process pool for CPU-intensive GTO calculations
            futures = []
            for game_state in game_states:
                future = self.thread_pool.submit_process_task(solve_game_state, game_state)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                try:
                    solution = future.result(timeout=60)  # GTO solving can take time
                    results.append(solution)
                except Exception as e:
                    logger.error(f"GTO solving task failed: {e}")
                    results.append(None)
            
            return results
            
        except ImportError:
            logger.warning("GTO solver not available")
            return [None] * len(game_states)

# Global instances
_async_manager: Optional[AsyncManager] = None
_poker_concurrency_manager: Optional[PokerConcurrencyManager] = None

def get_async_manager() -> AsyncManager:
    """Get the global async manager instance."""
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncManager()
    return _async_manager

def get_poker_concurrency_manager() -> PokerConcurrencyManager:
    """Get the global poker concurrency manager instance."""
    global _poker_concurrency_manager
    if _poker_concurrency_manager is None:
        _poker_concurrency_manager = PokerConcurrencyManager()
    return _poker_concurrency_manager

# Context managers for resource management
@contextmanager
def managed_thread_pool(config: Optional[ThreadPoolConfig] = None):
    """Context manager for thread pool with automatic cleanup."""
    pool = PokerThreadPool(config)
    try:
        yield pool
    finally:
        pool.shutdown(wait=True)

@contextmanager 
def async_context():
    """Context manager for async operations."""
    manager = get_async_manager()
    try:
        yield manager
    finally:
        manager.close()

# Utility functions for common concurrent operations
async def run_concurrent_tasks(tasks: List[Awaitable[T]], max_concurrent: int = 10) -> List[T]:
    """Run multiple async tasks with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _limited_task(task):
        async with semaphore:
            return await task
    
    limited_tasks = [_limited_task(task) for task in tasks]
    return await asyncio.gather(*limited_tasks, return_exceptions=True)

def parallel_map(func: Callable, items: List[Any], max_workers: int = None) -> List[Any]:
    """Parallel map function using thread pool."""
    thread_pool = get_thread_pool()
    
    futures = []
    for item in items:
        future = thread_pool.submit_thread_task(func, item)
        futures.append(future)
    
    results = []
    for future in as_completed(futures):
        try:
            result = future.result(timeout=30)
            results.append(result)
        except Exception as e:
            logger.error(f"Parallel map task failed: {e}")
            results.append(None)
    
    return results

# Performance monitoring decorator
def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Log slow operations
                logger.info(f"Slow operation: {func.__name__} took {execution_time:.2f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    
    return wrapper

if __name__ == '__main__':
    # Test threading functionality
    import time
    
    def test_function(n):
        time.sleep(0.1)  # Simulate work
        return n * 2
    
    # Test thread pool
    print("Testing thread pool...")
    pool = get_thread_pool()
    
    # Test priority tasks
    task_id = pool.submit_priority_task(test_function, 5, priority=TaskPriority.HIGH)
    result = pool.get_task_result(task_id)
    print(f"Priority task result: {result.result}")
    
    # Test regular thread pool
    future = pool.submit_thread_task(test_function, 10)
    print(f"Thread task result: {future.result()}")
    
    # Test parallel processing
    items = list(range(10))
    results = parallel_map(test_function, items)
    print(f"Parallel map results: {results}")
    
    # Print stats
    stats = pool.get_stats()
    print(f"Thread pool stats: {stats}")
    
    print("Threading tests completed!")
