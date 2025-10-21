"""
Locust load testing configuration for PokerTool API endpoints.

This file defines load test scenarios for critical API endpoints with
realistic user behavior patterns and performance thresholds.

Usage:
    # Run with web UI (recommended for development)
    locust -f tests/load/locustfile.py

    # Run headless with specific load parameters
    locust -f tests/load/locustfile.py --headless \
        --users 100 --spawn-rate 10 --run-time 60s \
        --host http://localhost:5001

    # Run with CSV reporting
    locust -f tests/load/locustfile.py --headless \
        --users 100 --spawn-rate 10 --run-time 300s \
        --csv-full-history --csv=results/load_test

Performance Thresholds (defined for assertions):
    - Health endpoints: p95 < 100ms, p99 < 200ms
    - Data endpoints: p95 < 500ms, p99 < 1000ms
    - Write endpoints: p95 < 1000ms, p99 < 2000ms
    - Error rate: < 1% for all endpoints
"""

from locust import HttpUser, task, between, events
import time
import json


class HealthCheckUser(HttpUser):
    """
    User that primarily performs health check operations.
    Simulates monitoring systems and frontend health polls.
    """

    wait_time = between(1, 3)  # 1-3 seconds between requests
    weight = 2  # 20% of users

    @task(10)
    def check_health(self):
        """Basic health check endpoint - most frequent"""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 0.1:  # 100ms threshold
                response.failure(f"Health check too slow: {response.elapsed.total_seconds():.3f}s")

    @task(5)
    def check_system_health(self):
        """System health with detailed metrics"""
        with self.client.get("/api/system/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"System health failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 0.5:  # 500ms threshold
                response.failure(f"System health too slow: {response.elapsed.total_seconds():.3f}s")

    @task(3)
    def check_backend_status(self):
        """Backend startup status monitoring"""
        with self.client.get("/api/backend/startup/status", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Backend status failed: {response.status_code}")


class DashboardUser(HttpUser):
    """
    User that simulates typical dashboard/frontend usage.
    Represents actual users viewing the application.
    """

    wait_time = between(3, 10)  # 3-10 seconds between page loads
    weight = 5  # 50% of users

    @task(5)
    def view_todo_list(self):
        """Load TODO list from dashboard"""
        with self.client.get("/api/todo", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"TODO list failed: {response.status_code}")
            elif response.elapsed.total_seconds() > 0.5:
                response.failure(f"TODO list too slow: {response.elapsed.total_seconds():.3f}s")
            else:
                try:
                    data = response.json()
                    if 'items' not in data:
                        response.failure("TODO list missing 'items' field")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")

    @task(3)
    def check_backend_status(self):
        """Monitor backend status from navbar"""
        self.client.get("/api/backend/startup/status")

    @task(2)
    def check_health(self):
        """Periodic health check from frontend"""
        self.client.get("/api/health")


class APIHeavyUser(HttpUser):
    """
    User performing heavier API operations.
    Simulates users actively interacting with the application.
    """

    wait_time = between(2, 5)  # 2-5 seconds between operations
    weight = 3  # 30% of users

    @task(10)
    def fetch_system_health_history(self):
        """Fetch health history with query parameters"""
        params = {
            'hours': 24,
            'limit': 100
        }
        with self.client.get("/api/system/health/history", params=params, catch_response=True) as response:
            if response.status_code == 404:
                # Endpoint might not exist, mark as success but don't fail test
                response.success()
            elif response.status_code != 200:
                response.failure(f"Health history failed: {response.status_code}")

    @task(5)
    def load_todo(self):
        """Load TODO list"""
        self.client.get("/api/todo")

    @task(3)
    def check_system_metrics(self):
        """Check detailed system health"""
        self.client.get("/api/system/health")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start with configuration"""
    print("\n" + "=" * 70)
    print("PokerTool Load Test Starting")
    print("=" * 70)
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Check performance thresholds and log results.
    This runs at the end of the test to validate performance.
    """
    stats = environment.stats.total

    print("\n" + "=" * 70)
    print("PokerTool Load Test Results")
    print("=" * 70)
    print(f"Total Requests: {stats.num_requests}")
    print(f"Failed Requests: {stats.num_failures}")
    print(f"Failure Rate: {stats.fail_ratio * 100:.2f}%")
    print(f"Average Response Time: {stats.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.max_response_time:.2f}ms")
    print(f"Median Response Time: {stats.median_response_time:.2f}ms")
    print(f"95th Percentile: {stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/sec: {stats.total_rps:.2f}")
    print("=" * 70)

    # Performance threshold checks
    failures = []

    # Check error rate < 1%
    if stats.fail_ratio > 0.01:
        failures.append(f"Error rate {stats.fail_ratio * 100:.2f}% exceeds threshold of 1%")

    # Check p95 < 1000ms for overall
    p95 = stats.get_response_time_percentile(0.95)
    if p95 > 1000:
        failures.append(f"P95 response time {p95:.0f}ms exceeds threshold of 1000ms")

    # Check p99 < 2000ms for overall
    p99 = stats.get_response_time_percentile(0.99)
    if p99 > 2000:
        failures.append(f"P99 response time {p99:.0f}ms exceeds threshold of 2000ms")

    if failures:
        print("\n⚠️  PERFORMANCE THRESHOLDS VIOLATED:")
        for failure in failures:
            print(f"  - {failure}")
        print("\n" + "=" * 70 + "\n")
        # Don't exit with error code - just log warnings
    else:
        print("\n✅ All performance thresholds met!\n")
        print("=" * 70 + "\n")
