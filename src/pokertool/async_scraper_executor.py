#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Asynchronous Scraper Executor for PokerTool
============================================

Eliminates GUI freezing by offloading heavy CV/OCR operations to background threads.

Features:
- Thread pool executor for parallel scraping operations
- Non-blocking result retrieval with queue
- Performance monitoring and metrics
- Automatic frame skipping if queue backs up
- Thread-safe operation with proper synchronization

Version: 1.0.0
"""

from __future__ import annotations

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for scraper execution."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    skipped_frames: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    max_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    queue_depth: int = 0
    max_queue_depth: int = 0
    last_operation_time: float = 0.0
    operations_per_second: float = 0.0
    start_time: float = field(default_factory=time.time)


@dataclass
class ScrapeResult:
    """Result of a scraping operation."""
    table_state: Any
    execution_time: float
    timestamp: float
    success: bool
    error: Optional[str] = None


class AsyncScraperExecutor:
    """
    Asynchronous executor for heavy scraping operations.

    Offloads analyze_table() and other CV/OCR operations to background threads
    to prevent GUI freezing.
    """

    def __init__(
        self,
        max_workers: int = 4,
        max_queue_size: int = 3,
        enable_frame_skipping: bool = True
    ):
        """
        Initialize the async scraper executor.

        Args:
            max_workers: Number of worker threads (4-8 recommended)
            max_queue_size: Maximum pending operations before frame skipping
            enable_frame_skipping: Skip frames if queue backs up
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.enable_frame_skipping = enable_frame_skipping

        # Thread pool for scraping operations
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="scraper_worker"
        )

        # Result queue for non-blocking retrieval
        self.result_queue: Queue[ScrapeResult] = Queue(maxsize=max_queue_size * 2)

        # Pending futures
        self.pending_futures: Dict[int, Future] = {}
        self.future_id_counter = 0
        self.future_lock = threading.Lock()

        # Performance metrics
        self.metrics = PerformanceMetrics()
        self.metrics_lock = threading.Lock()

        # Active flag
        self.active = True

        logger.info(f"AsyncScraperExecutor initialized: {max_workers} workers, "
                   f"max queue: {max_queue_size}, frame skipping: {enable_frame_skipping}")

    def submit_analyze_table(
        self,
        scraper: Any,
        image: Optional[np.ndarray] = None
    ) -> Optional[int]:
        """
        Submit an analyze_table operation to the thread pool.

        Args:
            scraper: Screen scraper instance
            image: Optional image to analyze (captures if None)

        Returns:
            Future ID for tracking, or None if skipped
        """
        # Check if we should skip this frame
        if self.enable_frame_skipping:
            with self.metrics_lock:
                current_queue_depth = len(self.pending_futures)
                self.metrics.queue_depth = current_queue_depth
                self.metrics.max_queue_depth = max(
                    self.metrics.max_queue_depth,
                    current_queue_depth
                )

                if current_queue_depth >= self.max_queue_size:
                    self.metrics.skipped_frames += 1
                    logger.debug(f"Frame skipped: queue depth {current_queue_depth}")
                    return None

        # Submit operation
        with self.future_lock:
            future_id = self.future_id_counter
            self.future_id_counter += 1

            future = self.executor.submit(
                self._execute_analyze_table,
                scraper,
                image,
                future_id
            )
            self.pending_futures[future_id] = future

        return future_id

    def _execute_analyze_table(
        self,
        scraper: Any,
        image: Optional[np.ndarray],
        future_id: int
    ) -> None:
        """
        Execute analyze_table in background thread.

        Args:
            scraper: Screen scraper instance
            image: Optional image to analyze
            future_id: ID for tracking this operation
        """
        start_time = time.time()

        try:
            # Execute the heavy operation
            table_state = scraper.analyze_table(image)
            execution_time = time.time() - start_time

            # Create result
            result = ScrapeResult(
                table_state=table_state,
                execution_time=execution_time,
                timestamp=time.time(),
                success=True
            )

            # Update metrics
            self._update_metrics(execution_time, success=True)

            # Put result in queue (non-blocking)
            try:
                self.result_queue.put_nowait(result)
            except:
                logger.warning("Result queue full, dropping result")

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Analyze table failed: {e}", exc_info=True)

            # Create error result
            result = ScrapeResult(
                table_state=None,
                execution_time=execution_time,
                timestamp=time.time(),
                success=False,
                error=str(e)
            )

            # Update metrics
            self._update_metrics(execution_time, success=False)

            # Put error result in queue
            try:
                self.result_queue.put_nowait(result)
            except:
                pass

        finally:
            # Remove from pending futures
            with self.future_lock:
                self.pending_futures.pop(future_id, None)

    def get_result(self, timeout: float = 0.0) -> Optional[ScrapeResult]:
        """
        Get next available result without blocking.

        Args:
            timeout: Maximum time to wait (0 = non-blocking)

        Returns:
            ScrapeResult if available, None otherwise
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except Empty:
            return None

    def _update_metrics(self, execution_time: float, success: bool):
        """Update performance metrics."""
        with self.metrics_lock:
            self.metrics.total_operations += 1

            if success:
                self.metrics.successful_operations += 1
            else:
                self.metrics.failed_operations += 1

            self.metrics.total_execution_time += execution_time
            self.metrics.avg_execution_time = (
                self.metrics.total_execution_time / self.metrics.total_operations
            )
            self.metrics.max_execution_time = max(
                self.metrics.max_execution_time,
                execution_time
            )
            self.metrics.min_execution_time = min(
                self.metrics.min_execution_time,
                execution_time
            )
            self.metrics.last_operation_time = execution_time

            # Calculate operations per second
            elapsed = time.time() - self.metrics.start_time
            if elapsed > 0:
                self.metrics.operations_per_second = (
                    self.metrics.total_operations / elapsed
                )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self.metrics_lock:
            return {
                'total_operations': self.metrics.total_operations,
                'successful_operations': self.metrics.successful_operations,
                'failed_operations': self.metrics.failed_operations,
                'skipped_frames': self.metrics.skipped_frames,
                'success_rate': (
                    self.metrics.successful_operations / max(self.metrics.total_operations, 1)
                ),
                'avg_execution_time_ms': self.metrics.avg_execution_time * 1000,
                'max_execution_time_ms': self.metrics.max_execution_time * 1000,
                'min_execution_time_ms': (
                    self.metrics.min_execution_time * 1000
                    if self.metrics.min_execution_time != float('inf')
                    else 0
                ),
                'last_operation_time_ms': self.metrics.last_operation_time * 1000,
                'queue_depth': self.metrics.queue_depth,
                'max_queue_depth': self.metrics.max_queue_depth,
                'operations_per_second': self.metrics.operations_per_second,
                'uptime_seconds': time.time() - self.metrics.start_time
            }

    def reset_metrics(self):
        """Reset performance metrics."""
        with self.metrics_lock:
            self.metrics = PerformanceMetrics()

    def shutdown(self, wait: bool = True, timeout: float = 5.0):
        """
        Shutdown the executor gracefully.

        Args:
            wait: Wait for pending operations to complete
            timeout: Maximum time to wait for shutdown
        """
        logger.info("Shutting down AsyncScraperExecutor...")
        self.active = False

        if wait:
            self.executor.shutdown(wait=True, cancel_futures=False)
        else:
            # Cancel pending operations
            with self.future_lock:
                for future in self.pending_futures.values():
                    future.cancel()
            self.executor.shutdown(wait=False, cancel_futures=True)

        logger.info("AsyncScraperExecutor shut down complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Global executor instance
_executor: Optional[AsyncScraperExecutor] = None


def get_async_executor(
    max_workers: int = 4,
    max_queue_size: int = 3
) -> AsyncScraperExecutor:
    """Get the global async scraper executor instance."""
    global _executor
    if _executor is None:
        _executor = AsyncScraperExecutor(
            max_workers=max_workers,
            max_queue_size=max_queue_size
        )
    return _executor


def shutdown_async_executor():
    """Shutdown the global async executor."""
    global _executor
    if _executor is not None:
        _executor.shutdown()
        _executor = None


if __name__ == '__main__':
    # Test the async executor
    print("Testing AsyncScraperExecutor...")

    # Mock scraper for testing
    class MockScraper:
        def analyze_table(self, image=None):
            time.sleep(0.1)  # Simulate heavy operation
            return {"players": 6, "pot": 100}

    scraper = MockScraper()
    executor = AsyncScraperExecutor(max_workers=4, max_queue_size=3)

    # Submit operations
    print("\nSubmitting 10 operations...")
    for i in range(10):
        future_id = executor.submit_analyze_table(scraper)
        if future_id is not None:
            print(f"  Operation {i}: submitted (ID: {future_id})")
        else:
            print(f"  Operation {i}: skipped (queue full)")
        time.sleep(0.05)

    # Retrieve results
    print("\nRetrieving results...")
    results_count = 0
    while results_count < 7:  # Some may be skipped
        result = executor.get_result(timeout=1.0)
        if result:
            if result.success:
                print(f"  Result: {result.table_state}, time: {result.execution_time*1000:.1f}ms")
            else:
                print(f"  Error: {result.error}")
            results_count += 1
        else:
            break

    # Print metrics
    print("\nPerformance Metrics:")
    metrics = executor.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    # Shutdown
    executor.shutdown()
    print("\n✓ AsyncScraperExecutor test complete")
