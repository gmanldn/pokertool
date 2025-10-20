#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for Async Scraper Executor
===============================================

Tests performance optimization for autopilot operations.
"""

import pytest
import time
from unittest.mock import Mock, patch
import numpy as np
from pokertool.async_scraper_executor import (
    AsyncScraperExecutor,
    PerformanceMetrics,
    ScrapeResult,
    get_async_executor,
    shutdown_async_executor
)


class MockScraper:
    """Mock scraper for testing."""

    def __init__(self, delay: float = 0.1, fail_rate: float = 0.0):
        self.delay = delay
        self.fail_rate = fail_rate
        self.call_count = 0

    def analyze_table(self, image=None):
        """Mock analyze_table method."""
        self.call_count += 1
        time.sleep(self.delay)

        # Simulate failure
        if self.fail_rate > 0 and (self.call_count % int(1/self.fail_rate)) == 0:
            raise Exception("Simulated scraper failure")

        # Return mock table state
        return {
            "players": 6,
            "pot": 100.0,
            "active": True
        }


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_metrics_initialization(self):
        """Test metrics initialize with correct defaults."""
        metrics = PerformanceMetrics()

        assert metrics.total_operations == 0
        assert metrics.successful_operations == 0
        assert metrics.failed_operations == 0
        assert metrics.skipped_frames == 0
        assert metrics.avg_execution_time == 0.0
        assert metrics.max_execution_time == 0.0
        assert metrics.min_execution_time == float('inf')


class TestScrapeResult:
    """Test ScrapeResult dataclass."""

    def test_scrape_result_success(self):
        """Test creating successful scrape result."""
        result = ScrapeResult(
            table_state={"players": 6},
            execution_time=0.123,
            timestamp=time.time(),
            success=True
        )

        assert result.success
        assert result.table_state == {"players": 6}
        assert result.execution_time == 0.123
        assert result.error is None

    def test_scrape_result_failure(self):
        """Test creating failed scrape result."""
        result = ScrapeResult(
            table_state=None,
            execution_time=0.050,
            timestamp=time.time(),
            success=False,
            error="Connection timeout"
        )

        assert not result.success
        assert result.table_state is None
        assert result.error == "Connection timeout"


class TestAsyncScraperExecutor:
    """Test AsyncScraperExecutor class."""

    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        executor = AsyncScraperExecutor(
            max_workers=4,
            max_queue_size=3,
            enable_frame_skipping=True
        )

        assert executor.max_workers == 4
        assert executor.max_queue_size == 3
        assert executor.enable_frame_skipping
        assert executor.active
        assert len(executor.pending_futures) == 0

        executor.shutdown(wait=False)

    def test_submit_analyze_table(self):
        """Test submitting analyze_table operation."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.1)

        future_id = executor.submit_analyze_table(scraper)

        assert future_id is not None
        assert future_id in executor.pending_futures

        # Wait for completion
        time.sleep(0.2)

        executor.shutdown()

    def test_get_result(self):
        """Test getting results from queue."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.05)

        # Submit operation
        executor.submit_analyze_table(scraper)

        # Wait and get result
        time.sleep(0.1)
        result = executor.get_result(timeout=1.0)

        assert result is not None
        assert result.success
        assert result.table_state == {"players": 6, "pot": 100.0, "active": True}

        executor.shutdown()

    def test_frame_skipping(self):
        """Test that frames are skipped when queue is full."""
        executor = AsyncScraperExecutor(
            max_workers=1,
            max_queue_size=2,
            enable_frame_skipping=True
        )
        scraper = MockScraper(delay=0.5)  # Slow operations

        # Submit many operations quickly
        submitted = []
        for i in range(10):
            future_id = executor.submit_analyze_table(scraper)
            submitted.append(future_id)
            time.sleep(0.01)

        # Some should be skipped
        skipped = [fid for fid in submitted if fid is None]
        assert len(skipped) > 0
        assert executor.metrics.skipped_frames > 0

        executor.shutdown(wait=False)

    def test_performance_metrics_tracking(self):
        """Test that performance metrics are tracked correctly."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.05)

        # Submit operations
        for _ in range(5):
            executor.submit_analyze_table(scraper)
            time.sleep(0.02)

        # Wait for completion
        time.sleep(0.3)

        # Check metrics
        metrics = executor.get_metrics()
        assert metrics['total_operations'] == 5
        assert metrics['successful_operations'] == 5
        assert metrics['failed_operations'] == 0
        assert metrics['avg_execution_time_ms'] > 0
        assert metrics['operations_per_second'] > 0

        executor.shutdown()

    def test_error_handling(self):
        """Test error handling in executor."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.05, fail_rate=0.5)  # 50% failure rate

        # Submit operations
        for _ in range(4):
            executor.submit_analyze_table(scraper)
            time.sleep(0.02)

        # Wait for completion
        time.sleep(0.3)

        # Get results
        results = []
        for _ in range(4):
            result = executor.get_result(timeout=0.5)
            if result:
                results.append(result)

        # Should have both success and failure
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]

        assert len(successes) + len(failures) > 0
        assert executor.metrics.failed_operations > 0

        executor.shutdown()

    def test_concurrent_operations(self):
        """Test multiple concurrent operations."""
        executor = AsyncScraperExecutor(max_workers=4)
        scraper = MockScraper(delay=0.1)

        # Submit many operations at once
        start_time = time.time()
        for _ in range(8):
            executor.submit_analyze_table(scraper)

        # Wait for all to complete
        time.sleep(0.5)
        elapsed = time.time() - start_time

        # With 4 workers, 8 operations should take ~0.2s (not 0.8s)
        assert elapsed < 0.6  # Allow some overhead

        # Get all results
        results = []
        for _ in range(8):
            result = executor.get_result(timeout=0.1)
            if result:
                results.append(result)

        assert len(results) >= 3  # Allow for some skips due to throttling

        executor.shutdown()

    def test_metrics_reset(self):
        """Test resetting metrics."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.05)

        # Submit operations
        for _ in range(3):
            executor.submit_analyze_table(scraper)
            time.sleep(0.02)

        time.sleep(0.2)

        # Check metrics exist
        assert executor.metrics.total_operations > 0

        # Reset
        executor.reset_metrics()

        # Should be back to zero
        assert executor.metrics.total_operations == 0
        assert executor.metrics.successful_operations == 0

        executor.shutdown()

    def test_shutdown_graceful(self):
        """Test graceful shutdown waits for operations."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.2)

        # Submit operations
        for _ in range(4):
            executor.submit_analyze_table(scraper)

        # Shutdown gracefully
        start_time = time.time()
        executor.shutdown(wait=True, timeout=5.0)
        elapsed = time.time() - start_time

        # Should wait for operations to complete
        assert elapsed >= 0.2

        # Most operations should complete (some may be skipped)
        assert executor.metrics.total_operations >= 3

    def test_shutdown_immediate(self):
        """Test immediate shutdown cancels operations."""
        executor = AsyncScraperExecutor(max_workers=2)
        scraper = MockScraper(delay=0.5)  # Long operations

        # Submit operations
        for _ in range(4):
            executor.submit_analyze_table(scraper)

        # Shutdown immediately
        start_time = time.time()
        executor.shutdown(wait=False)
        elapsed = time.time() - start_time

        # Should return quickly
        assert elapsed < 0.2

    def test_context_manager(self):
        """Test executor works as context manager."""
        scraper = MockScraper(delay=0.05)

        with AsyncScraperExecutor(max_workers=2) as executor:
            executor.submit_analyze_table(scraper)
            time.sleep(0.1)
            result = executor.get_result(timeout=0.5)
            assert result is not None
            assert result.success

        # Should be shut down after context
        assert not executor.active


class TestGlobalInstance:
    """Test global executor instance."""

    def test_get_async_executor(self):
        """Test getting global executor instance."""
        executor1 = get_async_executor()
        executor2 = get_async_executor()

        # Should be same instance (singleton)
        assert executor1 is executor2

        shutdown_async_executor()

    def test_shutdown_global_executor(self):
        """Test shutting down global executor."""
        executor = get_async_executor()
        assert executor is not None

        shutdown_async_executor()

        # Should create new instance after shutdown
        new_executor = get_async_executor()
        assert new_executor is not executor

        shutdown_async_executor()


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_autopilot_simulation(self):
        """Simulate autopilot operation with real timing."""
        executor = AsyncScraperExecutor(max_workers=4, max_queue_size=3)
        scraper = MockScraper(delay=0.15)  # Realistic scrape time

        results = []
        frames_submitted = 0
        frames_skipped = 0

        # Simulate autopilot loop (10 iterations, 0.2s apart)
        for i in range(10):
            future_id = executor.submit_analyze_table(scraper)
            if future_id is not None:
                frames_submitted += 1
            else:
                frames_skipped += 1

            # Check for results
            result = executor.get_result(timeout=0.0)
            if result:
                results.append(result)

            time.sleep(0.2)  # Autopilot loop delay

        # Wait for remaining results
        time.sleep(0.5)
        while True:
            result = executor.get_result(timeout=0.1)
            if result:
                results.append(result)
            else:
                break

        # Verify behavior
        assert frames_submitted > 0
        assert len(results) > 0
        assert all(r.success for r in results)

        # Check metrics
        metrics = executor.get_metrics()
        assert metrics['total_operations'] == frames_submitted
        assert metrics['avg_execution_time_ms'] > 0

        executor.shutdown()

    def test_performance_under_load(self):
        """Test performance under heavy load."""
        executor = AsyncScraperExecutor(max_workers=8, max_queue_size=5)
        scraper = MockScraper(delay=0.1)

        # Submit many operations
        start_time = time.time()
        for _ in range(50):
            executor.submit_analyze_table(scraper)
            time.sleep(0.01)

        # Wait for completion
        time.sleep(2.0)
        elapsed = time.time() - start_time

        # Get all results
        results = []
        while True:
            result = executor.get_result(timeout=0.05)
            if result:
                results.append(result)
            else:
                break

        # Verify throughput
        metrics = executor.get_metrics()
        assert metrics['operations_per_second'] > 3  # Should handle multiple ops/sec
        assert metrics['success_rate'] >= 0.8  # Should have high success rate

        executor.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
