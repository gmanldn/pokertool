#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance Benchmark Tests
===========================

Benchmark critical performance paths to catch regressions.

Target Performance:
- Hand analysis: <100ms
- Database queries: <50ms
- API endpoints: <200ms

Run with: pytest tests/benchmark/ -v
Fail CI if regressed >20%: pytest tests/benchmark/ --benchmark-only
"""

import pytest
import sys
import time
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pokertool.database import PokerDatabase

# Mark all tests as benchmarks
pytestmark = [pytest.mark.benchmark, pytest.mark.slow]


class TestDatabasePerformance:
    """Benchmark database operations."""

    @pytest.fixture
    def db(self):
        """Provide in-memory database."""
        return PokerDatabase(':memory:')

    def test_get_total_hands_performance(self, db):
        """Benchmark get_total_hands query (<50ms)."""
        start = time.time()
        result = db.get_total_hands()
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert isinstance(result, int)
        assert elapsed < 50, f"get_total_hands took {elapsed:.2f}ms (target: <50ms)"

    def test_database_connection_time(self):
        """Benchmark database connection establishment (<50ms)."""
        start = time.time()
        db = PokerDatabase(':memory:')
        elapsed = (time.time() - start) * 1000

        assert db is not None
        assert elapsed < 50, f"Database connection took {elapsed:.2f}ms (target: <50ms)"


class TestAPIPerformance:
    """Benchmark API endpoint performance."""

    @pytest.fixture
    def api_client(self):
        """Provide API test client."""
        from fastapi.testclient import TestClient
        from pokertool.api import PokerToolAPI
        from unittest.mock import patch

        with patch('pokertool.api.get_production_db'):
            api = PokerToolAPI()
            client = TestClient(api.app)
            return client

    def test_health_endpoint_performance(self, api_client):
        """Benchmark /health endpoint (<200ms)."""
        start = time.time()
        response = api_client.get('/health')
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"Health endpoint took {elapsed:.2f}ms (target: <200ms)"

    def test_system_health_endpoint_performance(self, api_client):
        """Benchmark /api/system/health endpoint (<200ms)."""
        start = time.time()
        response = api_client.get('/api/system/health')
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"System health endpoint took {elapsed:.2f}ms (target: <200ms)"


class TestImportPerformance:
    """Benchmark module import times."""

    def test_api_import_time(self):
        """Benchmark API module import (<1000ms)."""
        start = time.time()
        from pokertool import api
        elapsed = (time.time() - start) * 1000

        assert api is not None
        assert elapsed < 1000, f"API import took {elapsed:.2f}ms (target: <1000ms)"

    def test_database_import_time(self):
        """Benchmark database module import (<500ms)."""
        start = time.time()
        from pokertool import database
        elapsed = (time.time() - start) * 1000

        assert database is not None
        assert elapsed < 500, f"Database import took {elapsed:.2f}ms (target: <500ms)"


class TestComputationPerformance:
    """Benchmark computational tasks."""

    def test_hand_strength_calculation(self):
        """Benchmark hand strength calculation (<100ms)."""
        try:
            from pokertool.equity_calculator import EquityCalculator
        except ImportError:
            pytest.skip("EquityCalculator not available")

        calc = EquityCalculator()

        start = time.time()
        strength = calc.get_hand_strength('AA')
        elapsed = (time.time() - start) * 1000

        assert strength is not None
        assert elapsed < 100, f"Hand strength calc took {elapsed:.2f}ms (target: <100ms)"

    def test_equity_calculation(self):
        """Benchmark equity calculation (<100ms)."""
        try:
            from pokertool.equity_calculator import EquityCalculator
        except ImportError:
            pytest.skip("EquityCalculator not available")

        calc = EquityCalculator()

        start = time.time()
        equity = calc.calculate_hand_vs_hand('AA', 'KK')
        elapsed = (time.time() - start) * 1000

        assert equity is not None
        assert elapsed < 100, f"Equity calc took {elapsed:.2f}ms (target: <100ms)"


class TestMemoryUsage:
    """Benchmark memory usage."""

    def test_database_memory_footprint(self):
        """Ensure database has reasonable memory footprint."""
        import tracemalloc

        tracemalloc.start()
        db = PokerDatabase(':memory:')
        _ = db.get_total_hands()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be < 10MB for basic operations
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 10, f"Database used {peak_mb:.2f}MB peak (target: <10MB)"

    def test_api_memory_footprint(self):
        """Ensure API has reasonable memory footprint."""
        import tracemalloc
        from pokertool.api import PokerToolAPI
        from unittest.mock import patch

        tracemalloc.start()
        with patch('pokertool.api.get_production_db'):
            api = PokerToolAPI()
            _ = api.app
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be < 50MB for API initialization
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 50, f"API used {peak_mb:.2f}MB peak (target: <50MB)"


# Performance regression detection
class TestPerformanceRegression:
    """Detect performance regressions."""

    def test_baseline_performance_metrics(self):
        """Document baseline performance metrics for comparison."""
        from pokertool.database import PokerDatabase

        metrics = {}

        # Database connection
        start = time.time()
        db = PokerDatabase(':memory:')
        metrics['db_connection_ms'] = (time.time() - start) * 1000

        # Simple query
        start = time.time()
        _ = db.get_total_hands()
        metrics['simple_query_ms'] = (time.time() - start) * 1000

        # Log metrics for tracking
        print("\n=== Performance Baseline ===")
        for key, value in metrics.items():
            print(f"{key}: {value:.2f}ms")
        print("=" * 30)

        # All should be reasonable
        assert metrics['db_connection_ms'] < 100
        assert metrics['simple_query_ms'] < 100


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
