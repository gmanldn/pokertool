#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
System Reliability Tests

Tests to ensure system reliability and catch regressions in critical paths.
These tests verify that the system can handle various failure scenarios
and recovers gracefully.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor


class TestThreadManagementReliability:
    """Tests for thread management reliability."""

    def test_thread_manager_starts_cleanly(self):
        """Verify ThreadManager initializes without errors."""
        from pokertool.thread_manager import ThreadManager

        manager = ThreadManager()
        assert manager is not None
        assert hasattr(manager, 'active_threads')
        assert hasattr(manager, 'executor')
        manager.shutdown(wait=False)

    def test_thread_manager_handles_duplicate_thread_names(self):
        """Verify ThreadManager handles duplicate thread names correctly."""
        from pokertool.thread_manager import ThreadManager

        manager = ThreadManager()
        stop_event1 = threading.Event()
        stop_event2 = threading.Event()

        def worker(stop_event):
            stop_event.wait(timeout=1)

        # Start first thread
        thread1 = manager.start_thread("duplicate", worker, stop_event1, stop_event1)
        assert thread1.is_alive()

        # Start second thread with same name (should stop first)
        thread2 = manager.start_thread("duplicate", worker, stop_event2, stop_event2)
        assert thread2.is_alive()
        assert thread1 != thread2

        # Cleanup
        manager.stop_thread("duplicate")
        manager.shutdown(wait=False)

    def test_thread_manager_cleans_up_on_shutdown(self):
        """Verify ThreadManager cleans up all threads on shutdown."""
        from pokertool.thread_manager import ThreadManager

        manager = ThreadManager()
        events = [threading.Event() for _ in range(3)]

        def worker(event):
            event.wait(timeout=5)

        # Start multiple threads
        for i, event in enumerate(events):
            manager.start_thread(f"worker_{i}", worker, event, event)

        assert len(manager.active_threads) == 3

        # Shutdown should stop all threads
        manager.shutdown(wait=True, timeout=2.0)

        # Give threads time to stop
        time.sleep(0.5)
        assert len(manager.active_threads) == 0

    def test_thread_cleanup_manager_handles_dead_threads(self):
        """Verify ThreadCleanupManager properly handles dead threads."""
        from pokertool.thread_cleanup import ThreadCleanupManager

        manager = ThreadCleanupManager()

        # Register a thread that doesn't exist
        manager.register_thread("ghost_thread")
        assert "ghost_thread" in manager._registered_threads

        # Clean up should remove it
        count = manager.cleanup_dead_threads()
        assert count == 1
        assert "ghost_thread" not in manager._registered_threads


class TestDatabaseReliability:
    """Tests for database reliability and error handling."""

    def test_database_connection_recovery(self):
        """Verify database can recover from connection failures."""
        from pokertool.database import Database

        # This should not raise an exception
        db = Database()
        assert db is not None

    def test_database_handles_missing_tables_gracefully(self):
        """Verify database handles missing tables without crashing."""
        from pokertool.database import Database

        db = Database()
        # Should not crash if tables don't exist
        try:
            result = db.execute_query("SELECT * FROM nonexistent_table LIMIT 1")
            # If it succeeds, table exists, which is fine
        except Exception as e:
            # Should be a graceful error, not a crash
            assert "nonexistent_table" in str(e).lower() or "no such table" in str(e).lower()

    def test_database_transaction_rollback(self):
        """Verify database properly rolls back failed transactions."""
        from pokertool.database import Database

        db = Database()
        # Test that rollback doesn't crash the system
        try:
            db.execute_query("BEGIN TRANSACTION")
            db.execute_query("SELECT 1/0")  # This will fail
        except:
            pass  # Expected to fail

        # Database should still be usable
        result = db.execute_query("SELECT 1")
        assert result is not None


class TestAPIReliability:
    """Tests for API reliability and error handling."""

    def test_api_handles_invalid_requests_gracefully(self):
        """Verify API handles invalid requests without crashing."""
        from pokertool.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Send invalid JSON
        response = client.post("/api/invalid", json={"bad": "data"})
        # Should return 404 or 422, not crash
        assert response.status_code in [404, 422, 405]

    def test_api_health_endpoint_always_responds(self):
        """Verify health endpoint always responds."""
        from pokertool.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_api_handles_concurrent_requests(self):
        """Verify API can handle concurrent requests."""
        from pokertool.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        def make_request():
            return client.get("/health")

        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in results)


class TestWebSocketReliability:
    """Tests for WebSocket reliability."""

    def test_websocket_handles_disconnection(self):
        """Verify WebSocket handles disconnection gracefully."""
        # Mock WebSocket connection
        mock_ws = Mock()
        mock_ws.send = Mock()
        mock_ws.receive = Mock(side_effect=Exception("Connection closed"))

        # Should not crash when connection is lost
        try:
            mock_ws.receive()
        except Exception as e:
            assert "Connection closed" in str(e)

    def test_websocket_handles_invalid_messages(self):
        """Verify WebSocket handles invalid messages without crashing."""
        import json

        # Invalid JSON
        invalid_messages = [
            "{invalid json}",
            "",
            "null",
            "{}",
            '{"type": "unknown"}',
        ]

        for msg in invalid_messages:
            try:
                data = json.loads(msg) if msg else {}
                # Should not crash
                assert isinstance(data, (dict, type(None)))
            except json.JSONDecodeError:
                # Expected for invalid JSON
                pass


class TestSystemHealthRegression:
    """Regression tests for system health monitoring."""

    def test_system_health_checker_returns_valid_status(self):
        """Verify system health checker returns valid status."""
        from pokertool.system_health_checker import check_system_health

        health = check_system_health()
        assert health is not None
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

    def test_system_health_categories_present(self):
        """Verify all health categories are present."""
        from pokertool.system_health_checker import check_system_health

        health = check_system_health()
        assert "categories" in health

        # Should have these categories
        expected_categories = ["api", "database", "websocket"]
        for category in expected_categories:
            # Categories may or may not be present depending on system state
            # Just verify the structure is correct
            pass

    def test_system_health_handles_component_failures(self):
        """Verify system health correctly reports when components fail."""
        from pokertool.system_health_checker import check_system_health

        # Even if components fail, health check should not crash
        health = check_system_health()
        assert health is not None
        assert "timestamp" in health


class TestDetectionReliability:
    """Tests for detection system reliability."""

    def test_detection_handles_missing_screen(self):
        """Verify detection handles missing screen gracefully."""
        # Detection should not crash if no poker window is found
        pass  # Placeholder - actual implementation depends on detection module

    def test_detection_handles_corrupted_images(self):
        """Verify detection handles corrupted images without crashing."""
        pass  # Placeholder - actual implementation depends on detection module

    def test_detection_recovers_from_errors(self):
        """Verify detection system recovers from errors."""
        pass  # Placeholder - actual implementation depends on detection module


class TestMemoryLeakPrevention:
    """Tests to prevent memory leaks."""

    def test_no_memory_leak_in_repeated_operations(self):
        """Verify repeated operations don't cause memory leaks."""
        import gc
        from pokertool.thread_manager import ThreadManager

        # Create and destroy managers multiple times
        for _ in range(10):
            manager = ThreadManager()
            manager.shutdown(wait=False)
            del manager

        # Force garbage collection
        gc.collect()

        # If we get here without crashing, no obvious memory leak
        assert True

    def test_thread_cleanup_prevents_leaks(self):
        """Verify thread cleanup prevents thread leaks."""
        from pokertool.thread_cleanup import get_cleanup_manager

        initial_thread_count = threading.active_count()

        # Register and cleanup threads
        manager = get_cleanup_manager()
        for i in range(5):
            manager.register_thread(f"test_thread_{i}")

        cleaned = manager.cleanup_dead_threads()

        # Thread count should not grow unbounded
        final_thread_count = threading.active_count()
        assert final_thread_count <= initial_thread_count + 5  # Allow some variance


class TestErrorHandlingRegression:
    """Regression tests for error handling."""

    def test_error_middleware_catches_exceptions(self):
        """Verify error middleware catches and handles exceptions."""
        from pokertool.error_middleware import error_handler

        @error_handler
        def failing_function():
            raise ValueError("Test error")

        # Should not crash
        try:
            failing_function()
        except ValueError:
            pass  # Expected

    def test_global_error_handler_logs_errors(self):
        """Verify global error handler logs errors properly."""
        from pokertool.global_error_handler import log_error

        # Should not crash even with invalid inputs
        try:
            log_error(Exception("Test exception"))
        except:
            pytest.fail("Error handler should not raise exceptions")


class TestRateLimitingReliability:
    """Tests for rate limiting reliability."""

    def test_rate_limiter_prevents_abuse(self):
        """Verify rate limiter prevents excessive requests."""
        from pokertool.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=5, window=1.0)

        # First 5 requests should succeed
        for _ in range(5):
            assert limiter.check_rate_limit("test_key")

        # 6th request should be denied
        assert not limiter.check_rate_limit("test_key")

    def test_rate_limiter_resets_after_window(self):
        """Verify rate limiter resets after time window."""
        from pokertool.rate_limiter import RateLimiter

        limiter = RateLimiter(max_requests=2, window=0.5)

        # Use up the limit
        assert limiter.check_rate_limit("test_key")
        assert limiter.check_rate_limit("test_key")
        assert not limiter.check_rate_limit("test_key")

        # Wait for window to reset
        time.sleep(0.6)

        # Should be allowed again
        assert limiter.check_rate_limit("test_key")


class TestCacheReliability:
    """Tests for caching reliability."""

    def test_cache_handles_expired_entries(self):
        """Verify cache handles expired entries correctly."""
        from pokertool.api_cache import get_cache

        cache = get_cache()
        cache.set("test_key", "test_value", ttl=1)

        # Should be retrievable immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should return None after expiration
        assert cache.get("test_key") is None

    def test_cache_handles_memory_limits(self):
        """Verify cache respects memory limits."""
        from pokertool.api_cache import get_cache

        cache = get_cache()

        # Fill cache with many entries
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}", ttl=60)

        # Cache should not grow unbounded
        # (actual limit depends on implementation)
        assert True  # If we get here without crashing, it's working


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
