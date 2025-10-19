#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Concurrency Regression Tests for Threading Module
==================================================

Tests for race conditions, resource leaks, and thread pool safety
in src/pokertool/threading.py.

These tests verify:
- Thread pool initialization and cleanup
- Concurrent task execution without race conditions
- Resource leak detection (threads, futures)
- Thread safety of shared data structures
- Proper shutdown behavior
"""

import pytest
import threading
import time
import gc
import weakref
from concurrent.futures import Future
from typing import List, Set

from pokertool.threading import (
    get_thread_pool,
    shutdown_thread_pool,
    run_in_thread,
    ThreadSafeDict,
    ThreadSafeCounter,
    register_callback,
    trigger_callbacks,
    cleanup_threading,
    get_thread_local,
    set_thread_local,
    clear_thread_local,
)


class TestThreadPoolConcurrency:
    """Test thread pool for race conditions and resource leaks."""

    def setup_method(self):
        """Reset thread pool before each test."""
        shutdown_thread_pool(wait=True)
        clear_thread_local()
        gc.collect()

    def teardown_method(self):
        """Clean up after each test."""
        shutdown_thread_pool(wait=True)
        cleanup_threading()
        gc.collect()

    def test_thread_pool_singleton(self):
        """Verify thread pool is a singleton."""
        pool1 = get_thread_pool()
        pool2 = get_thread_pool()
        assert pool1 is pool2, "Thread pool should be singleton"

    def test_concurrent_pool_access(self):
        """Test thread pool access from multiple threads doesn't cause races."""
        pools = []
        barrier = threading.Barrier(10)
        
        def get_pool():
            barrier.wait()  # Synchronize all threads
            pool = get_thread_pool()
            pools.append(pool)
        
        threads = [threading.Thread(target=get_pool) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should get the same pool instance
        assert len(set(id(p) for p in pools)) == 1, "All threads should get same pool"

    def test_concurrent_task_submission(self):
        """Test submitting many tasks concurrently doesn't cause races."""
        pool = get_thread_pool(max_workers=4)
        counter = ThreadSafeCounter(0)
        num_tasks = 100
        
        def increment_task():
            time.sleep(0.001)  # Simulate work
            counter.increment()
            return counter.value
        
        # Submit all tasks concurrently
        futures = [run_in_thread(increment_task) for _ in range(num_tasks)]
        
        # Wait for all to complete
        results = [f.result() for f in futures]
        
        # Counter should reach exactly num_tasks
        assert counter.value == num_tasks, f"Expected {num_tasks}, got {counter.value}"
        assert all(isinstance(r, int) for r in results), "All results should be integers"

    def test_no_thread_leak(self):
        """Verify threads are properly cleaned up after tasks complete."""
        initial_count = threading.active_count()
        pool = get_thread_pool(max_workers=4)
        
        # Submit tasks and wait
        futures = [run_in_thread(lambda: time.sleep(0.01)) for _ in range(20)]
        for f in futures:
            f.result()
        
        # Wait a bit for threads to return to pool
        time.sleep(0.1)
        
        # Thread count should be close to initial (allowing for pool threads)
        final_count = threading.active_count()
        # Allow up to 4 extra threads for the pool workers
        assert final_count <= initial_count + 4, f"Thread leak detected: {initial_count} -> {final_count}"

    def test_no_future_leak(self):
        """Verify futures are garbage collected after completion."""
        pool = get_thread_pool(max_workers=2)
        weak_refs = []
        
        # Create futures with weak references
        for _ in range(10):
            future = run_in_thread(lambda: time.sleep(0.001))
            weak_refs.append(weakref.ref(future))
            future.result()  # Complete the future
            del future  # Remove strong reference
        
        # Force garbage collection
        gc.collect()
        
        # Most futures should be garbage collected
        alive = sum(1 for ref in weak_refs if ref() is not None)
        assert alive <= 2, f"Future leak detected: {alive} futures still alive"

    def test_shutdown_waits_for_tasks(self):
        """Verify shutdown waits for running tasks to complete."""
        pool = get_thread_pool(max_workers=2)
        completed = []
        
        def long_task(task_id):
            time.sleep(0.2)
            completed.append(task_id)
        
        # Submit tasks
        futures = [run_in_thread(long_task, i) for i in range(4)]
        
        # Shutdown and wait
        start = time.time()
        shutdown_thread_pool(wait=True)
        duration = time.time() - start
        
        # Should have waited for tasks
        assert duration >= 0.2, "Shutdown should wait for tasks"
        assert len(completed) == 4, "All tasks should complete"

    def test_shutdown_no_wait(self):
        """Verify shutdown without waiting doesn't block."""
        pool = get_thread_pool(max_workers=2)
        
        # Submit long-running tasks
        futures = [run_in_thread(lambda: time.sleep(1)) for _ in range(4)]
        
        # Shutdown without waiting should return quickly
        start = time.time()
        shutdown_thread_pool(wait=False)
        duration = time.time() - start
        
        assert duration < 0.5, "Shutdown without wait should be fast"


class TestThreadSafeDataStructures:
    """Test thread-safe data structures for race conditions."""

    def test_threadsafe_dict_concurrent_writes(self):
        """Test ThreadSafeDict handles concurrent writes correctly."""
        d = ThreadSafeDict()
        num_threads = 10
        num_ops = 100
        
        def writer(thread_id):
            for i in range(num_ops):
                d[f"key_{thread_id}_{i}"] = thread_id
        
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have all keys
        expected_keys = num_threads * num_ops
        assert len(d.keys()) == expected_keys, f"Expected {expected_keys} keys, got {len(d.keys())}"

    def test_threadsafe_dict_concurrent_read_write(self):
        """Test ThreadSafeDict handles concurrent reads and writes."""
        d = ThreadSafeDict()
        d["counter"] = 0
        errors = []
        
        def reader():
            try:
                for _ in range(100):
                    value = d.get("counter", 0)
                    assert isinstance(value, int), "Value should always be int"
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def writer():
            try:
                for _ in range(100):
                    current = d.get("counter", 0)
                    d["counter"] = current + 1
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        threads = []
        threads.extend([threading.Thread(target=reader) for _ in range(3)])
        threads.extend([threading.Thread(target=writer) for _ in range(3)])
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Race condition errors: {errors}"
        assert isinstance(d["counter"], int), "Counter should be integer"

    def test_threadsafe_counter_concurrent_increments(self):
        """Test ThreadSafeCounter increments are atomic."""
        counter = ThreadSafeCounter(0)
        num_threads = 20
        num_increments = 100
        
        def incrementer():
            for _ in range(num_increments):
                counter.increment()
        
        threads = [threading.Thread(target=incrementer) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        expected = num_threads * num_increments
        assert counter.value == expected, f"Expected {expected}, got {counter.value}"

    def test_threadsafe_counter_concurrent_mixed_ops(self):
        """Test ThreadSafeCounter with mixed increment/decrement operations."""
        counter = ThreadSafeCounter(1000)
        
        def incrementer():
            for _ in range(100):
                counter.increment()
        
        def decrementer():
            for _ in range(100):
                counter.decrement()
        
        threads = []
        threads.extend([threading.Thread(target=incrementer) for _ in range(5)])
        threads.extend([threading.Thread(target=decrementer) for _ in range(5)])
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should be back to 1000 (5*100 increments - 5*100 decrements)
        assert counter.value == 1000, f"Expected 1000, got {counter.value}"


class TestCallbackSystem:
    """Test callback system for race conditions."""

    def test_concurrent_callback_registration(self):
        """Test registering callbacks from multiple threads."""
        callbacks_registered = []
        
        def callback_func():
            pass
        
        def register():
            register_callback("test_event", callback_func)
            callbacks_registered.append(1)
        
        threads = [threading.Thread(target=register) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(callbacks_registered) == 10, "All registrations should succeed"

    def test_concurrent_callback_triggering(self):
        """Test triggering callbacks from multiple threads."""
        call_count = ThreadSafeCounter(0)
        
        def callback():
            call_count.increment()
            time.sleep(0.01)
        
        # Register callback
        register_callback("test_event", callback)
        
        # Trigger from multiple threads
        def trigger():
            trigger_callbacks("test_event")
        
        threads = [threading.Thread(target=trigger) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Wait for all callbacks to complete
        time.sleep(0.2)
        
        # Should have been called 5 times
        assert call_count.value == 5, f"Expected 5 calls, got {call_count.value}"


class TestThreadLocalStorage:
    """Test thread-local storage isolation."""

    def test_thread_local_isolation(self):
        """Verify thread-local values are isolated between threads."""
        results = {}
        barrier = threading.Barrier(5)
        
        def worker(thread_id):
            set_thread_local("id", thread_id)
            barrier.wait()  # Ensure all threads have set their values
            time.sleep(0.01)  # Let other threads potentially corrupt data
            value = get_thread_local("id")
            results[thread_id] = value
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Each thread should have its own value
        for i in range(5):
            assert results[i] == i, f"Thread {i} got wrong value: {results[i]}"

    def test_thread_local_cleanup(self):
        """Verify thread-local storage can be cleared."""
        set_thread_local("test_key", "test_value")
        assert get_thread_local("test_key") == "test_value"
        
        clear_thread_local()
        assert get_thread_local("test_key") is None


class TestResourceLeakDetection:
    """High-level tests for resource leaks under load."""

    def test_sustained_load_no_leaks(self):
        """Run sustained load and verify no resource leaks."""
        initial_threads = threading.active_count()
        pool = get_thread_pool(max_workers=4)
        
        def task():
            time.sleep(0.001)
            return threading.current_thread().ident
        
        # Run multiple rounds of tasks
        for round_num in range(10):
            futures = [run_in_thread(task) for _ in range(50)]
            results = [f.result() for f in futures]
            assert len(results) == 50, f"Round {round_num}: wrong result count"
            
            # Check thread count hasn't grown
            current_threads = threading.active_count()
            assert current_threads <= initial_threads + 4, \
                f"Thread leak in round {round_num}: {current_threads} threads"

    def test_cleanup_releases_resources(self):
        """Verify cleanup_threading releases all resources."""
        pool = get_thread_pool(max_workers=4)
        
        # Submit and complete some tasks
        futures = [run_in_thread(lambda: time.sleep(0.01)) for _ in range(10)]
        for f in futures:
            f.result()
        
        # Cleanup
        cleanup_threading()
        
        # Pool should be gone
        # Get a new pool (which recreates it)
        new_pool = get_thread_pool()
        assert new_pool is not pool, "Cleanup should have released old pool"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])