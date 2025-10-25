"""Tests for v0.8.0: Circuit Breaker Pattern

Tests circuit breaker implementation including:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure threshold detection
- Automatic recovery
- Monitoring and alerting
- Database operation wrapping
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.pokertool.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    DatabaseCircuitBreaker,
)


class TestCircuitBreakerStates:
    """Test circuit breaker state management."""

    def test_circuit_breaker_starts_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        assert cb.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        # Simulate 3 failures
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker goes to HALF_OPEN after timeout."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        assert cb.can_attempt() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_breaker_closes_after_success_in_half_open(self):
        """Test circuit breaker closes after success in HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        # Wait for timeout
        time.sleep(1.1)
        cb.can_attempt()  # Transition to HALF_OPEN

        # Record success
        cb.record_success()

        assert cb.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_reopens_on_failure_in_half_open(self):
        """Test circuit breaker reopens on failure in HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        # Wait for timeout
        time.sleep(1.1)
        cb.can_attempt()  # Transition to HALF_OPEN

        # Record failure
        cb.record_failure()

        assert cb.state == CircuitBreakerState.OPEN


class TestCircuitBreakerFailureTracking:
    """Test failure tracking and threshold detection."""

    def test_failure_count_increments(self):
        """Test failure count increments correctly."""
        cb = CircuitBreaker(failure_threshold=5, timeout=60)

        cb.record_failure()
        assert cb.failure_count == 1

        cb.record_failure()
        assert cb.failure_count == 2

    def test_failure_count_resets_on_success(self):
        """Test failure count resets on success."""
        cb = CircuitBreaker(failure_threshold=5, timeout=60)

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0

    def test_custom_failure_threshold(self):
        """Test custom failure threshold."""
        cb = CircuitBreaker(failure_threshold=10, timeout=60)

        # Should not open before threshold
        for _ in range(9):
            cb.record_failure()

        assert cb.state == CircuitBreakerState.CLOSED

        # Should open after threshold
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

    def test_failure_rate_tracking(self):
        """Test failure rate is tracked."""
        cb = CircuitBreaker(failure_threshold=5, timeout=60)

        cb.record_success()
        cb.record_success()
        cb.record_failure()

        # 1 failure out of 3 calls = 33%
        failure_rate = cb.get_failure_rate()
        assert 0.3 <= failure_rate <= 0.4

    def test_consecutive_failures_only(self):
        """Test circuit breaker tracks consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Resets count
        cb.record_failure()

        # Only 1 consecutive failure
        assert cb.state == CircuitBreakerState.CLOSED


class TestCircuitBreakerOperations:
    """Test circuit breaker operation wrapping."""

    def test_call_succeeds_when_closed(self):
        """Test function call succeeds when circuit is closed."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def mock_function():
            return "success"

        result = cb.call(mock_function)
        assert result == "success"

    def test_call_raises_when_open(self):
        """Test function call raises error when circuit is open."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        def mock_function():
            return "success"

        with pytest.raises(CircuitBreakerOpenError):
            cb.call(mock_function)

    def test_call_records_success(self):
        """Test successful call records success."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def mock_function():
            return "success"

        cb.call(mock_function)
        assert cb.success_count == 1

    def test_call_records_failure_on_exception(self):
        """Test failed call records failure."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def mock_function():
            raise Exception("Database error")

        try:
            cb.call(mock_function)
        except Exception:
            pass

        assert cb.failure_count == 1

    def test_call_propagates_exception(self):
        """Test exceptions are propagated to caller."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def mock_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            cb.call(mock_function)


class TestCircuitBreakerMonitoring:
    """Test circuit breaker monitoring and metrics."""

    def test_get_state_returns_current_state(self):
        """Test get_state returns current state."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        assert cb.get_state() == CircuitBreakerState.CLOSED

    def test_get_metrics_returns_stats(self):
        """Test get_metrics returns statistics."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        cb.record_success()
        cb.record_failure()

        metrics = cb.get_metrics()
        assert metrics['success_count'] == 1
        assert metrics['failure_count'] == 1
        assert metrics['state'] == CircuitBreakerState.CLOSED

    def test_state_change_callback(self):
        """Test callback is called on state change."""
        callback = Mock()
        cb = CircuitBreaker(
            failure_threshold=3,
            timeout=60,
            state_change_callback=callback
        )

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        callback.assert_called_once_with(
            CircuitBreakerState.CLOSED,
            CircuitBreakerState.OPEN
        )

    def test_last_failure_time_tracked(self):
        """Test last failure time is tracked."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        before = time.time()
        cb.record_failure()
        after = time.time()

        assert before <= cb.last_failure_time <= after

    def test_total_calls_tracked(self):
        """Test total calls are tracked."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def mock_function():
            return "success"

        cb.call(mock_function)
        cb.call(mock_function)

        try:
            cb.call(lambda: 1/0)
        except:
            pass

        assert cb.total_calls == 3


class TestDatabaseCircuitBreaker:
    """Test database-specific circuit breaker."""

    def test_database_circuit_breaker_initialization(self):
        """Test DatabaseCircuitBreaker can be initialized."""
        db_cb = DatabaseCircuitBreaker()
        assert db_cb is not None

    def test_database_circuit_breaker_wraps_queries(self):
        """Test DatabaseCircuitBreaker wraps database queries."""
        db_cb = DatabaseCircuitBreaker()

        mock_query = Mock(return_value=["result"])

        result = db_cb.execute_query(mock_query)
        assert result == ["result"]

    def test_database_circuit_breaker_handles_connection_errors(self):
        """Test DatabaseCircuitBreaker handles connection errors."""
        db_cb = DatabaseCircuitBreaker(failure_threshold=2)

        def failing_query():
            raise ConnectionError("Database connection failed")

        # First failure
        with pytest.raises(ConnectionError):
            db_cb.execute_query(failing_query)

        # Second failure
        with pytest.raises(ConnectionError):
            db_cb.execute_query(failing_query)

        # Circuit should be open now
        assert db_cb.state == CircuitBreakerState.OPEN

    def test_database_circuit_breaker_retries_safe_operations(self):
        """Test DatabaseCircuitBreaker retries safe operations."""
        db_cb = DatabaseCircuitBreaker()

        mock_query = Mock(side_effect=[Exception("Timeout"), "success"])

        result = db_cb.execute_query(mock_query, retry_count=1)
        assert result == "success"

    def test_database_circuit_breaker_fails_fast_when_open(self):
        """Test DatabaseCircuitBreaker fails fast when open."""
        db_cb = DatabaseCircuitBreaker(failure_threshold=2)

        # Open the circuit
        for _ in range(2):
            try:
                db_cb.execute_query(lambda: 1/0)
            except:
                pass

        # Should fail fast without executing
        with pytest.raises(CircuitBreakerOpenError):
            db_cb.execute_query(lambda: "should not execute")


class TestCircuitBreakerConfiguration:
    """Test circuit breaker configuration."""

    def test_default_configuration(self):
        """Test default configuration values."""
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.timeout == 60

    def test_custom_configuration(self):
        """Test custom configuration."""
        cb = CircuitBreaker(
            failure_threshold=10,
            timeout=120,
            half_open_max_calls=3
        )
        assert cb.failure_threshold == 10
        assert cb.timeout == 120

    def test_invalid_configuration_raises_error(self):
        """Test invalid configuration raises error."""
        with pytest.raises(ValueError):
            CircuitBreaker(failure_threshold=0)

        with pytest.raises(ValueError):
            CircuitBreaker(timeout=-1)


class TestCircuitBreakerRecovery:
    """Test circuit breaker recovery mechanisms."""

    def test_automatic_recovery_after_timeout(self):
        """Test circuit recovers automatically after timeout."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Should allow attempt
        assert cb.can_attempt() is True

    def test_manual_reset(self):
        """Test manual circuit breaker reset."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitBreakerState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_progressive_recovery(self):
        """Test progressive recovery in HALF_OPEN state."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        # Wait for timeout
        time.sleep(1.1)

        # Transition to HALF_OPEN
        cb.can_attempt()

        # One success should close circuit
        cb.record_success()

        assert cb.state == CircuitBreakerState.CLOSED


class TestCircuitBreakerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_circuit_breaker_with_zero_timeout(self):
        """Test circuit breaker with immediate recovery."""
        cb = CircuitBreaker(failure_threshold=3, timeout=0)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        # Should immediately allow retry
        assert cb.can_attempt() is True

    def test_concurrent_access(self):
        """Test circuit breaker handles concurrent access."""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        # Simulate concurrent failures
        for _ in range(5):
            cb.record_failure()

        # Should still work correctly
        assert cb.state == CircuitBreakerState.OPEN

    def test_very_high_failure_threshold(self):
        """Test circuit breaker with very high threshold."""
        cb = CircuitBreaker(failure_threshold=1000, timeout=60)

        # Many failures shouldn't open circuit
        for _ in range(999):
            cb.record_failure()

        assert cb.state == CircuitBreakerState.CLOSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
