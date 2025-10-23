#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for PokerTool thread management and cleanup.

Tests ensure that thread management is robust and prevents regressions.
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from pokertool.thread_manager import (
    ThreadManager,
    get_thread_manager,
    shutdown_thread_manager,
    start_thread,
    stop_thread,
    get_active_threads,
    cleanup_dead_threads,
)

from pokertool.thread_cleanup import (
    ThreadCleanupManager,
    get_cleanup_manager,
    register_thread,
    unregister_thread,
    cleanup_on_startup,
    get_all_threads,
)

from pokertool.threading_utils import (
    get_thread_pool,
    shutdown_thread_pool,
    cleanup_threading,
)


class TestThreadManager:
    """Tests for ThreadManager class."""

    def test_thread_manager_initialization(self):
        """Test that ThreadManager initializes correctly."""
        manager = ThreadManager(max_workers=5)
        assert manager.max_workers == 5
        assert isinstance(manager.executor, ThreadPoolExecutor)
        assert len(manager.active_threads) == 0
        manager.shutdown(wait=False)

    def test_start_and_stop_thread(self):
        """Test starting and stopping a thread."""
        manager = ThreadManager()
        stop_event = threading.Event()
        ran = threading.Event()

        def worker():
            ran.set()
            stop_event.wait(timeout=10)

        # Start thread
        thread = manager.start_thread("test_worker", worker, stop_event)
        assert thread.is_alive()
        assert "test_worker" in manager.active_threads

        # Wait for thread to start
        assert ran.wait(timeout=2)

        # Stop thread
        success = manager.stop_thread("test_worker", timeout=2.0)
        assert success
        assert "test_worker" not in manager.active_threads

        manager.shutdown(wait=False)

    def test_start_thread_with_same_name_stops_old(self):
        """Test that starting a thread with existing name stops the old one."""
        manager = ThreadManager()
        stop_event1 = threading.Event()
        stop_event2 = threading.Event()

        def worker1():
            stop_event1.wait(timeout=10)

        def worker2():
            stop_event2.wait(timeout=10)

        # Start first thread
        thread1 = manager.start_thread("duplicate", worker1, stop_event1)
        assert thread1.is_alive()

        # Start second thread with same name
        thread2 = manager.start_thread("duplicate", worker2, stop_event2)
        assert thread2.is_alive()
        assert thread1 != thread2

        # Stop and cleanup
        manager.stop_thread("duplicate", timeout=2.0)
        manager.shutdown(wait=False)

    def test_cleanup_dead_threads(self):
        """Test cleaning up dead threads."""
        manager = ThreadManager()

        def quick_worker():
            time.sleep(0.1)

        # Start thread that will finish quickly
        thread = manager.start_thread("quick", quick_worker)
        thread.join(timeout=2.0)

        # Thread should be dead but still registered
        assert not thread.is_alive()
        assert "quick" in manager.active_threads

        # Clean up dead threads
        count = manager.cleanup_dead_threads()
        assert count == 1
        assert "quick" not in manager.active_threads

        manager.shutdown(wait=False)

    def test_stop_all_threads(self):
        """Test stopping all threads at once."""
        manager = ThreadManager()
        events = [threading.Event() for _ in range(3)]

        def worker(event):
            event.wait(timeout=10)

        # Start multiple threads
        for i, event in enumerate(events):
            manager.start_thread(f"worker_{i}", worker, event, event)

        assert len(manager.active_threads) == 3

        # Stop all threads
        failed = manager.stop_all_threads(timeout=2.0)
        assert failed == 0
        assert len(manager.active_threads) == 0

        manager.shutdown(wait=False)

    def test_shutdown_prevents_new_threads(self):
        """Test that shutdown prevents starting new threads."""
        manager = ThreadManager()
        manager._shutdown_requested = True

        with pytest.raises(RuntimeError, match="shutting down"):
            manager.start_thread("after_shutdown", lambda: None)

    def test_get_stats(self):
        """Test getting thread statistics."""
        manager = ThreadManager()
        stop_event = threading.Event()

        def worker():
            stop_event.wait(timeout=10)

        manager.start_thread("stats_test", worker, stop_event)
        stats = manager.get_stats()

        assert 'active_threads_count' in stats
        assert 'active_thread_names' in stats
        assert stats['active_threads_count'] == 1
        assert 'stats_test' in stats['active_thread_names']

        manager.stop_thread("stats_test", timeout=2.0)
        manager.shutdown(wait=False)


class TestThreadCleanupManager:
    """Tests for ThreadCleanupManager."""

    def test_cleanup_manager_initialization(self):
        """Test ThreadCleanupManager initialization."""
        manager = ThreadCleanupManager()
        assert len(manager._registered_threads) == 0
        assert len(manager._cleanup_handlers) == 0

    def test_register_and_unregister_thread(self):
        """Test registering and unregistering threads."""
        manager = ThreadCleanupManager()

        manager.register_thread("test_thread")
        assert "test_thread" in manager._registered_threads

        manager.unregister_thread("test_thread")
        assert "test_thread" not in manager._registered_threads

    def test_register_cleanup_handler(self):
        """Test registering cleanup handlers."""
        manager = ThreadCleanupManager()
        called = threading.Event()

        def handler():
            called.set()

        manager.register_cleanup_handler(handler)
        assert len(manager._cleanup_handlers) == 1

        # Trigger shutdown
        manager.shutdown_all(timeout=1.0)
        assert called.is_set()

    def test_get_all_threads(self):
        """Test getting all thread information."""
        manager = ThreadCleanupManager()
        threads = manager.get_all_threads()

        assert len(threads) > 0
        assert all(hasattr(t, 'name') for t in threads)
        assert all(hasattr(t, 'daemon') for t in threads)
        assert all(hasattr(t, 'is_alive') for t in threads)

    def test_get_non_daemon_threads(self):
        """Test getting non-daemon threads."""
        manager = ThreadCleanupManager()

        # Create a non-daemon thread
        event = threading.Event()

        def worker():
            event.wait(timeout=10)

        thread = threading.Thread(target=worker, daemon=False, name="test_non_daemon")
        thread.start()

        try:
            non_daemon = manager.get_non_daemon_threads(exclude_main=True)
            names = [t.name for t in non_daemon]
            assert "test_non_daemon" in names
        finally:
            event.set()
            thread.join(timeout=2.0)

    def test_get_pokertool_threads(self):
        """Test getting PokerTool-specific threads."""
        manager = ThreadCleanupManager()
        event = threading.Event()

        def worker():
            event.wait(timeout=10)

        thread = threading.Thread(target=worker, daemon=True, name="PokerTool-TestThread")
        thread.start()

        try:
            pokertool_threads = manager.get_pokertool_threads()
            names = [t.name for t in pokertool_threads]
            assert "PokerTool-TestThread" in names
        finally:
            event.set()
            thread.join(timeout=2.0)

    def test_cleanup_dead_threads(self):
        """Test cleanup of dead thread references."""
        manager = ThreadCleanupManager()

        # Register a thread that doesn't exist
        manager.register_thread("ghost_thread")
        assert "ghost_thread" in manager._registered_threads

        # Clean up dead threads
        count = manager.cleanup_dead_threads()
        assert count == 1
        assert "ghost_thread" not in manager._registered_threads

    def test_get_report(self):
        """Test getting thread report."""
        manager = ThreadCleanupManager()
        report = manager.get_report()

        assert "THREAD MANAGER REPORT" in report
        assert "Total threads:" in report
        assert isinstance(report, str)


class TestThreadingUtils:
    """Tests for threading_utils module."""

    def test_get_thread_pool(self):
        """Test getting the global thread pool."""
        pool = get_thread_pool(max_workers=4)
        assert isinstance(pool, ThreadPoolExecutor)

    def test_shutdown_thread_pool(self):
        """Test shutting down the thread pool."""
        pool = get_thread_pool(max_workers=2)

        # Submit a quick task
        future = pool.submit(lambda: 42)
        assert future.result(timeout=2.0) == 42

        # Shutdown
        shutdown_thread_pool(wait=True)

    def test_cleanup_threading(self):
        """Test complete threading cleanup."""
        # Import and reset the shutdown flag first
        import pokertool.threading_utils as tu
        tu._shutdown_initiated = False

        # Get pool to ensure it's created
        pool = get_thread_pool(max_workers=2)

        # Cleanup
        cleanup_threading()


class TestGlobalFunctions:
    """Tests for global thread management functions."""

    def test_global_thread_manager(self):
        """Test global thread manager functions."""
        manager = get_thread_manager()
        assert isinstance(manager, ThreadManager)

    def test_start_and_stop_global_thread(self):
        """Test starting and stopping threads via global functions."""
        stop_event = threading.Event()
        ran = threading.Event()

        def worker():
            ran.set()
            stop_event.wait(timeout=10)

        # Start thread
        thread = start_thread("global_test", worker, stop_event)
        assert thread.is_alive()
        assert ran.wait(timeout=2)

        # Stop thread
        success = stop_thread("global_test", timeout=2.0)
        assert success

    def test_get_active_threads_global(self):
        """Test getting active threads via global function."""
        stop_event = threading.Event()

        def worker():
            stop_event.wait(timeout=10)

        start_thread("active_test", worker, stop_event)
        active = get_active_threads()

        assert "active_test" in active
        stop_thread("active_test", timeout=2.0)

    def test_cleanup_dead_threads_global(self):
        """Test cleanup via global function."""
        def quick_worker():
            time.sleep(0.1)

        thread = start_thread("quick_global", quick_worker)
        thread.join(timeout=2.0)

        # Clean up
        count = cleanup_dead_threads()
        assert count >= 0


class TestThreadCleanupGlobal:
    """Tests for global thread cleanup functions."""

    def test_get_global_cleanup_manager(self):
        """Test getting global cleanup manager."""
        manager = get_cleanup_manager()
        assert isinstance(manager, ThreadCleanupManager)

    def test_register_thread_global(self):
        """Test registering threads via global function."""
        register_thread("global_registered")
        manager = get_cleanup_manager()
        assert "global_registered" in manager._registered_threads

        unregister_thread("global_registered")
        assert "global_registered" not in manager._registered_threads

    def test_cleanup_on_startup(self):
        """Test startup cleanup."""
        stats = cleanup_on_startup()

        assert 'total_threads' in stats
        assert 'non_daemon_threads' in stats
        assert 'pokertool_threads' in stats
        assert 'dead_threads_cleaned' in stats
        assert isinstance(stats['total_threads'], int)

    def test_get_all_threads_global(self):
        """Test getting all threads via global function."""
        threads = get_all_threads()
        assert len(threads) > 0
        assert all(hasattr(t, 'name') for t in threads)


class TestConcurrentOperations:
    """Tests for concurrent thread operations."""

    def test_multiple_threads_concurrent(self):
        """Test managing multiple threads concurrently."""
        manager = ThreadManager()
        events = []
        num_threads = 5

        def worker(thread_id, event):
            event.wait(timeout=10)

        # Start multiple threads
        for i in range(num_threads):
            event = threading.Event()
            events.append(event)
            manager.start_thread(f"concurrent_{i}", worker, event, i, event)

        assert len(manager.active_threads) == num_threads

        # Stop all
        for i, event in enumerate(events):
            manager.stop_thread(f"concurrent_{i}", timeout=2.0)

        assert len(manager.active_threads) == 0
        manager.shutdown(wait=False)

    def test_thread_pool_concurrent_tasks(self):
        """Test submitting concurrent tasks to thread pool."""
        manager = ThreadManager(max_workers=3)
        results = []

        def task(x):
            time.sleep(0.1)
            return x * 2

        # Submit multiple tasks
        futures = [manager.submit_task(task, i) for i in range(10)]

        # Wait for results
        for future in futures:
            results.append(future.result(timeout=5.0))

        assert len(results) == 10
        assert results == [i * 2 for i in range(10)]
        manager.shutdown(wait=True)


class TestErrorHandling:
    """Tests for error handling in thread management."""

    def test_stop_nonexistent_thread(self):
        """Test stopping a thread that doesn't exist."""
        manager = ThreadManager()
        result = manager.stop_thread("nonexistent", timeout=1.0)
        assert result is True  # Returns True if thread doesn't exist
        manager.shutdown(wait=False)

    def test_thread_exception_handling(self):
        """Test that thread exceptions don't crash the manager."""
        manager = ThreadManager()

        def failing_worker():
            raise ValueError("Intentional test error")

        # Start thread that will fail
        thread = manager.start_thread("failing", failing_worker)
        thread.join(timeout=2.0)

        # Thread should be dead
        assert not thread.is_alive()

        # Cleanup should work
        count = manager.cleanup_dead_threads()
        assert count == 1
        manager.shutdown(wait=False)

    def test_shutdown_idempotent(self):
        """Test that shutdown can be called multiple times safely."""
        manager = ThreadManager()
        manager.shutdown(wait=False)
        manager.shutdown(wait=False)  # Should not raise


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
