#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Watchdog Timer for Stuck Operations
====================================

Detect and recover from stuck/hung operations to improve reliability.

Features:
- Operation timeout detection
- Automatic recovery actions
- Thread safety
- Configurable timeouts
- Stuck operation logging
- Automatic cleanup

Version: 69.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import time
import threading
import logging
import traceback
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class WatchdogAction(Enum):
    """Action to take when watchdog times out."""
    LOG_WARNING = "log_warning"
    RAISE_EXCEPTION = "raise_exception"
    CALL_HANDLER = "call_handler"


@dataclass
class OperationInfo:
    """Information about a monitored operation."""
    name: str
    start_time: float
    timeout: float
    thread_id: int
    thread_name: str
    action: WatchdogAction
    handler: Optional[Callable] = None


class WatchdogTimeoutError(Exception):
    """Raised when an operation times out."""
    pass


# ============================================================================
# Watchdog Timer
# ============================================================================

class WatchdogTimer:
    """
    Monitor operations and detect when they get stuck.

    Usage:
        watchdog = WatchdogTimer()

        # Use as context manager
        with watchdog.monitor("scrape_table", timeout=5.0):
            result = scrape_table()

        # Or use as decorator
        @watchdog.watch(timeout=3.0)
        def my_function():
            ...
    """

    def __init__(
        self,
        default_timeout: float = 30.0,
        check_interval: float = 1.0
    ):
        """
        Initialize watchdog timer.

        Args:
            default_timeout: Default operation timeout in seconds
            check_interval: How often to check for timeouts
        """
        self.default_timeout = default_timeout
        self.check_interval = check_interval

        # Active operations being monitored
        self.operations: Dict[str, OperationInfo] = {}
        self.lock = threading.RLock()

        # Monitoring thread
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Statistics
        self.total_operations = 0
        self.timeout_count = 0
        self.timeout_operations: Dict[str, int] = {}

        logger.info(f"WatchdogTimer initialized (default timeout: {default_timeout}s)")

    def start_monitoring(self):
        """Start the watchdog monitoring thread."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="WatchdogMonitor"
        )
        self.monitor_thread.start()
        logger.info("Watchdog monitoring started")

    def stop_monitoring(self):
        """Stop the watchdog monitoring thread."""
        if not self.monitoring:
            return

        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Watchdog monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop - checks for timeouts."""
        while self.monitoring:
            try:
                now = time.time()

                with self.lock:
                    # Check each operation for timeout
                    timed_out = []
                    for op_id, op_info in self.operations.items():
                        elapsed = now - op_info.start_time
                        if elapsed > op_info.timeout:
                            timed_out.append((op_id, op_info, elapsed))

                    # Handle timeouts outside the lock
                    for op_id, op_info, elapsed in timed_out:
                        self._handle_timeout(op_id, op_info, elapsed)

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in watchdog monitoring loop: {e}", exc_info=True)
                time.sleep(self.check_interval)

    def _handle_timeout(
        self,
        op_id: str,
        op_info: OperationInfo,
        elapsed: float
    ):
        """
        Handle a timed-out operation.

        Args:
            op_id: Operation ID
            op_info: Operation information
            elapsed: Elapsed time in seconds
        """
        self.timeout_count += 1
        self.timeout_operations[op_info.name] = \
            self.timeout_operations.get(op_info.name, 0) + 1

        logger.error(
            f"⏱️  WATCHDOG TIMEOUT: '{op_info.name}' stuck for {elapsed:.1f}s "
            f"(timeout: {op_info.timeout}s, thread: {op_info.thread_name})"
        )

        # Log stack trace of stuck thread
        try:
            import sys
            frame = sys._current_frames().get(op_info.thread_id)
            if frame:
                stack = ''.join(traceback.format_stack(frame))
                logger.error(f"Stack trace of stuck operation:\n{stack}")
        except Exception as e:
            logger.debug(f"Could not get stack trace: {e}")

        # Take action based on configured action
        if op_info.action == WatchdogAction.RAISE_EXCEPTION:
            # Note: This won't actually raise in the stuck thread
            # but we can mark it for cleanup
            with self.lock:
                if op_id in self.operations:
                    del self.operations[op_id]

        elif op_info.action == WatchdogAction.CALL_HANDLER:
            if op_info.handler:
                try:
                    op_info.handler(op_info)
                except Exception as e:
                    logger.error(f"Watchdog handler failed: {e}")

        elif op_info.action == WatchdogAction.LOG_WARNING:
            # Already logged above
            pass

        # Remove from monitoring
        with self.lock:
            if op_id in self.operations:
                del self.operations[op_id]

    @contextmanager
    def monitor(
        self,
        operation_name: str,
        timeout: Optional[float] = None,
        action: WatchdogAction = WatchdogAction.LOG_WARNING,
        timeout_handler: Optional[Callable] = None
    ):
        """
        Monitor an operation with a timeout.

        Args:
            operation_name: Name of operation
            timeout: Timeout in seconds (default: self.default_timeout)
            action: Action to take on timeout
            timeout_handler: Handler to call on timeout

        Yields:
            None

        Example:
            with watchdog.monitor("scrape", timeout=5.0):
                result = expensive_operation()
        """
        timeout = timeout or self.default_timeout
        thread = threading.current_thread()
        op_id = f"{operation_name}_{thread.ident}_{time.time()}"

        op_info = OperationInfo(
            name=operation_name,
            start_time=time.time(),
            timeout=timeout,
            thread_id=thread.ident,
            thread_name=thread.name,
            action=action,
            handler=timeout_handler
        )

        # Start monitoring if not already running
        if not self.monitoring:
            self.start_monitoring()

        # Register operation
        with self.lock:
            self.operations[op_id] = op_info
            self.total_operations += 1

        try:
            yield

        finally:
            # Unregister operation
            with self.lock:
                if op_id in self.operations:
                    elapsed = time.time() - op_info.start_time
                    logger.debug(
                        f"✓ Operation '{operation_name}' completed in {elapsed:.2f}s"
                    )
                    del self.operations[op_id]

    def watch(
        self,
        timeout: Optional[float] = None,
        operation_name: Optional[str] = None,
        action: WatchdogAction = WatchdogAction.LOG_WARNING
    ):
        """
        Decorator to monitor a function with watchdog.

        Args:
            timeout: Timeout in seconds
            operation_name: Name of operation (default: function name)
            action: Action to take on timeout

        Example:
            @watchdog.watch(timeout=5.0)
            def slow_function():
                ...
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                op_name = operation_name or func.__name__
                with self.monitor(op_name, timeout=timeout, action=action):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def get_active_operations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about currently active operations.

        Returns:
            Dict mapping operation IDs to operation info
        """
        with self.lock:
            now = time.time()
            return {
                op_id: {
                    'name': op_info.name,
                    'elapsed': now - op_info.start_time,
                    'timeout': op_info.timeout,
                    'thread': op_info.thread_name
                }
                for op_id, op_info in self.operations.items()
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get watchdog statistics.

        Returns:
            Dict with statistics
        """
        with self.lock:
            active_count = len(self.operations)
            timeout_rate = (
                self.timeout_count / max(1, self.total_operations)
            )

            return {
                'total_operations': self.total_operations,
                'active_operations': active_count,
                'timeout_count': self.timeout_count,
                'timeout_rate': timeout_rate,
                'timeout_by_operation': self.timeout_operations.copy(),
                'monitoring': self.monitoring
            }

    def clear_stats(self):
        """Clear all statistics."""
        with self.lock:
            self.total_operations = 0
            self.timeout_count = 0
            self.timeout_operations.clear()
        logger.info("Watchdog statistics cleared")


# ============================================================================
# Global Watchdog Instance
# ============================================================================

_global_watchdog: Optional[WatchdogTimer] = None


def get_watchdog() -> WatchdogTimer:
    """
    Get global watchdog instance (singleton).

    Returns:
        WatchdogTimer instance
    """
    global _global_watchdog
    if _global_watchdog is None:
        _global_watchdog = WatchdogTimer()
        _global_watchdog.start_monitoring()
    return _global_watchdog


def watch(
    timeout: Optional[float] = None,
    operation_name: Optional[str] = None
):
    """
    Convenience decorator using global watchdog.

    Args:
        timeout: Timeout in seconds
        operation_name: Name of operation

    Example:
        @watch(timeout=5.0)
        def my_function():
            ...
    """
    return get_watchdog().watch(timeout=timeout, operation_name=operation_name)


@contextmanager
def monitor(
    operation_name: str,
    timeout: Optional[float] = None
):
    """
    Convenience context manager using global watchdog.

    Args:
        operation_name: Name of operation
        timeout: Timeout in seconds

    Example:
        with monitor("expensive_op", timeout=10.0):
            result = expensive_operation()
    """
    with get_watchdog().monitor(operation_name, timeout=timeout):
        yield


# ============================================================================
# Testing
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Watchdog Timer System Test")
    print("=" * 60)

    watchdog = WatchdogTimer(default_timeout=3.0, check_interval=0.5)
    watchdog.start_monitoring()

    # Test 1: Normal operation
    print("\n1. Testing normal operation (should complete):")
    with watchdog.monitor("quick_operation", timeout=5.0):
        time.sleep(1.0)
        print("   ✓ Operation completed normally")

    # Test 2: Timeout detection
    print("\n2. Testing timeout detection (should timeout):")
    try:
        with watchdog.monitor("slow_operation", timeout=2.0):
            time.sleep(4.0)  # This will timeout
            print("   This should not print")
    except Exception as e:
        print(f"   Exception: {e}")

    # Wait for watchdog to detect timeout
    time.sleep(3.0)

    # Test 3: Decorator
    print("\n3. Testing decorator:")

    @watchdog.watch(timeout=2.0)
    def test_function():
        print("   Function executing...")
        time.sleep(0.5)
        return "success"

    result = test_function()
    print(f"   Result: {result}")

    # Test 4: Get statistics
    print("\n4. Watchdog Statistics:")
    stats = watchdog.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Test 5: Active operations
    print("\n5. Testing active operations tracking:")

    def background_task():
        with watchdog.monitor("background_task", timeout=10.0):
            time.sleep(2.0)

    thread = threading.Thread(target=background_task)
    thread.start()

    time.sleep(0.5)
    active = watchdog.get_active_operations()
    print(f"   Active operations: {len(active)}")
    for op_id, info in active.items():
        print(f"   - {info['name']}: {info['elapsed']:.1f}s elapsed")

    thread.join()

    watchdog.stop_monitoring()

    print("\n" + "=" * 60)
    print("Test complete!")
