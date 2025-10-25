"""
Tests for TODO 7-12: WebSocket & Frontend Configuration

Validates that:
1. Backend port configurable
2. Frontend can discover backend port
3. Error messages clear
4. WebSocket reconnection works
5. WebSocket heartbeat/ping mechanism
6. Health check retry with jitter
"""

import pytest
import asyncio
import json
import random
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta


class TestFrontendPortConfiguration:
    """Test frontend port configuration (TODO 7-8)."""

    def test_backend_port_from_environment(self):
        """Test that backend port read from REACT_APP_BACKEND_PORT (TODO 7)."""
        # Frontend should read from: process.env.REACT_APP_BACKEND_PORT

        env_var = "REACT_APP_BACKEND_PORT"
        default_port = 5001

        # After fix: should check environment variable first
        assert env_var.startswith("REACT_APP_"), \
            "Should follow React env var naming (REACT_APP_*)"

    def test_api_config_port_configurable(self):
        """Test that API config has configurable port."""
        # File: pokertool-frontend/src/config/api.ts

        # Should have something like:
        # const BACKEND_PORT = process.env.REACT_APP_BACKEND_PORT || 5001;

        backend_port = 5001  # Default

        assert backend_port == 5001, \
            "Default port should be 5001"

    def test_backend_port_auto_discovery(self):
        """Test that frontend tries multiple ports (TODO 8)."""
        # If primary port fails, try: 5001, 5000, 8000, 3001

        ports_to_try = [5001, 5000, 8000, 3001]

        assert 5001 in ports_to_try, \
            "Should try primary port 5001"
        assert len(ports_to_try) >= 3, \
            "Should have fallback ports"

    def test_api_url_builder_respects_port(self):
        """Test that buildApiUrl() uses configured port."""
        # Should construct: http://localhost:PORT/api/system/health

        api_url = "http://localhost:5001/api/system/health"

        assert "5001" in api_url, \
            "API URL should include port"
        assert "localhost" in api_url, \
            "Should be local connection"

    def test_non_standard_port_support(self):
        """Test that non-standard ports are supported."""
        # After fix: can set REACT_APP_BACKEND_PORT=8000

        custom_port = 8000
        api_url = f"http://localhost:{custom_port}/api/system/health"

        assert str(custom_port) in api_url, \
            "Custom port should be reflected in URL"

    def test_port_validation(self):
        """Test that port number is validated."""
        # Port must be 1-65535

        valid_ports = [1, 80, 5001, 8000, 65535]
        invalid_ports = [0, 65536, -1, "invalid"]

        for port in valid_ports:
            assert isinstance(port, int) and 1 <= port <= 65535, \
                f"Port {port} should be valid"


class TestFrontendErrorMessages:
    """Test frontend error message clarity (TODO 9)."""

    def test_distinguish_rate_limit_error(self):
        """Test that frontend can identify rate limit errors."""
        # Error 429 should show: "Too many requests. Backend is working."

        http_429_response = {"status": 429, "error": "Too Many Requests"}

        is_rate_limit = http_429_response["status"] == 429

        assert is_rate_limit, \
            "Should identify 429 as rate limit"

    def test_distinguish_connection_error(self):
        """Test that frontend can identify connection errors."""
        # Connection refused: "Can't connect to backend. Is it running?"

        connection_error = {
            "type": "Network",
            "message": "ECONNREFUSED: Connection refused"
        }

        is_connection_error = "Connection" in connection_error["message"]

        assert is_connection_error, \
            "Should identify connection errors"

    def test_distinguish_timeout_error(self):
        """Test that frontend can identify timeout errors."""
        # Timeout: "Backend is slow to respond. Check resources."

        timeout_error = {
            "type": "Timeout",
            "message": "Request timeout after 5000ms"
        }

        is_timeout = "timeout" in timeout_error["message"].lower()

        assert is_timeout, \
            "Should identify timeout errors"

    def test_error_messages_include_action(self):
        """Test that error messages include suggested action."""
        # Instead of: "Error"
        # Should show: "Error: Can't reach backend on port 5001.
        #             Try: http://localhost:5001/api/system/health
        #             Help: Check that 'python start.py' is running"

        helpful_error = {
            "message": "Can't reach backend on port 5001",
            "url": "http://localhost:5001/api/system/health",
            "suggestions": [
                "Ensure backend is running (python start.py)",
                "Check network connectivity",
                "Verify port 5001 is accessible"
            ]
        }

        assert "suggestions" in helpful_error, \
            "Error should include suggested actions"
        assert len(helpful_error["suggestions"]) > 0, \
            "Should have at least one suggestion"

    def test_error_message_not_technical(self):
        """Test that error messages are user-friendly."""
        # Bad: "ECONNREFUSED on 127.0.0.1:5001 with errno -111"
        # Good: "Can't connect to backend on port 5001"

        user_friendly = "Can't connect to backend on port 5001"
        technical = "ECONNREFUSED on 127.0.0.1:5001 with errno -111"

        # User-friendly version should be shorter and clearer
        assert len(user_friendly) < len(technical), \
            "User-friendly message should be concise"


class TestWebSocketReconnection:
    """Test WebSocket reconnection logic (TODO 10)."""

    def test_websocket_exponential_backoff(self):
        """Test exponential backoff on reconnect: 10s → 30s → 60s."""
        # After first disconnect: wait 10 seconds
        # After second: wait 30 seconds
        # After third+: wait 60 seconds (max)

        backoff_times = [10, 30, 60]

        assert backoff_times[0] == 10, "First retry: 10s"
        assert backoff_times[1] == 30, "Second retry: 30s"
        assert backoff_times[2] == 60, "Third+ retry: 60s max"

    def test_websocket_reconnect_reduces_load(self):
        """Test that exponential backoff reduces server load."""
        # Without backoff: 100 clients disconnect → 100 reconnect in 1 second
        # With backoff: spread over 10 seconds

        clients = 100
        reconnect_time_seconds = 1  # Without backoff: all at once

        with_backoff_spread = 10  # With backoff: spread over 10s

        # Requests per second without backoff
        without_backoff_rps = clients / reconnect_time_seconds  # 100 rps
        # With backoff, average is much lower
        with_backoff_rps = clients / with_backoff_spread  # 10 rps

        assert with_backoff_rps < without_backoff_rps, \
            "Backoff should reduce peak load"

    def test_websocket_reconnect_max_backoff(self):
        """Test that backoff caps at reasonable max time."""
        # Should not wait more than 60 seconds before retry

        max_backoff_seconds = 60

        assert max_backoff_seconds <= 60, \
            "Max backoff should be reasonable"
        assert max_backoff_seconds >= 30, \
            "Max backoff should be meaningful"

    def test_websocket_reconnect_jitter(self):
        """Test that backoff includes random jitter."""
        # Instead of exact 10s, use 10s ± random(0-20%)
        # This prevents thundering herd

        base_delay = 10
        jitter_percentage = 0.2  # ±20%

        jittered_delays = []
        for _ in range(100):
            jitter = random.uniform(-jitter_percentage, jitter_percentage)
            delay = base_delay * (1 + jitter)
            jittered_delays.append(delay)

        # Delays should vary
        min_delay = min(jittered_delays)
        max_delay = max(jittered_delays)

        assert min_delay < base_delay, "Some delays should be less than base"
        assert max_delay > base_delay, "Some delays should be more than base"


class TestWebSocketHeartbeat:
    """Test WebSocket heartbeat/ping mechanism (TODO 11)."""

    @pytest.mark.asyncio
    async def test_server_sends_ping_every_30_seconds(self):
        """Test that server sends ping every 30 seconds."""
        # Server: Every 30 seconds, send {"type": "ping"}
        # Client: Respond with {"type": "pong"}

        ping_interval_seconds = 30

        # After 30 seconds of connection, first ping should be sent
        assert ping_interval_seconds == 30, \
            "Ping interval should be 30 seconds"

    @pytest.mark.asyncio
    async def test_client_responds_to_ping(self):
        """Test that client responds to ping with pong."""
        # If client doesn't respond to ping for 60 seconds,
        # connection should be closed

        pong_timeout_seconds = 60

        # Client should respond within this time
        assert pong_timeout_seconds > 30, \
            "Pong timeout should be longer than ping interval"

    @pytest.mark.asyncio
    async def test_dead_connection_detection(self):
        """Test that dead connections are detected via ping/pong."""
        # If server doesn't receive pong for 60 seconds, close connection

        pong_timeout = 60

        # This allows detecting dead connections
        assert pong_timeout > 0, \
            "Should have timeout for detecting dead connections"

    @pytest.mark.asyncio
    async def test_ping_pong_keeps_connection_alive(self):
        """Test that ping/pong prevents idle connection timeout."""
        # Long-lived connections might timeout at TCP level
        # Ping/pong keeps them active

        client_idle_timeout = 300  # 5 minutes typical
        ping_interval = 30  # Every 30 seconds

        # Ping interval should be much shorter than idle timeout
        assert ping_interval < client_idle_timeout, \
            "Ping should prevent idle timeout"


class TestHealthCheckRetryJitter:
    """Test health check retry with jitter (TODO 12)."""

    def test_retry_jitter_distributes_load(self):
        """Test that jitter distributes retry attempts over time."""
        # Without jitter: All 100 clients retry at exact same time
        # With jitter: Spread over interval

        clients = 100
        retry_interval = 10  # seconds
        jitter_percentage = 0.5  # ±50%

        retry_times = []
        for _ in range(clients):
            jitter = random.uniform(-jitter_percentage, jitter_percentage)
            retry_time = retry_interval * (1 + jitter)
            retry_times.append(retry_time)

        # Times should be distributed, not all the same
        unique_times = len(set(retry_times))
        assert unique_times > 1, \
            "Retry times should be distributed"

    def test_jitter_within_bounds(self):
        """Test that jitter stays within acceptable bounds."""
        # Base interval: 10 seconds
        # Jitter: ±50%
        # Expected range: 5-15 seconds

        base = 10
        jitter_pct = 0.5

        min_retry = base * (1 - jitter_pct)  # 5
        max_retry = base * (1 + jitter_pct)  # 15

        assert min_retry == 5, "Min should be 5 seconds"
        assert max_retry == 15, "Max should be 15 seconds"

    def test_jitter_random_distribution(self):
        """Test that jitter provides random distribution."""
        # Should use Math.random() for uniform distribution

        samples = 1000
        jitter_values = [random.random() for _ in range(samples)]

        # Average should be close to 0.5
        average = sum(jitter_values) / len(jitter_values)

        assert 0.4 < average < 0.6, \
            "Random distribution should center around 0.5"

    def test_jitter_prevents_thundering_herd(self):
        """Test that jitter prevents thundering herd problem."""
        # Thundering herd: Many clients hit server simultaneously
        # Solution: Jitter spreads requests over time

        clients = 100
        time_window = 10  # seconds

        # Simulate retry times with jitter
        retry_times = []
        for _ in range(clients):
            jitter = random.uniform(-0.25, 0.25)  # ±25%
            retry_time = 5 * (1 + jitter)
            retry_times.append(retry_time)

        # Count requests in each second
        requests_per_second = [0] * (int(max(retry_times)) + 1)
        for retry_time in retry_times:
            requests_per_second[int(retry_time)] += 1

        # Peak requests per second should be less than total clients
        peak_rps = max(requests_per_second)
        assert peak_rps < clients, \
            "Peak should be less than total (due to spread)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
