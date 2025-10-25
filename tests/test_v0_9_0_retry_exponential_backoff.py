"""Tests for v0.9.0: Retry Logic with Exponential Backoff

Tests retry mechanism including:
- Exponential backoff timing
- Jitter to prevent thundering herd
- Deadline handling
- Max retry attempts
- Retry on specific exceptions
- Integration with circuit breaker
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.pokertool.resilience.retry import (
    RetryPolicy,
    RetryExhaustedError,
    DeadlineExceededError,
    retry_with_backoff,
    exponential_backoff,
    calculate_backoff,
)


class TestExponentialBackoff:
    """Test exponential backoff calculation."""

    def test_backoff_increases_exponentially(self):
        """Test backoff time increases exponentially."""
        backoffs = [calculate_backoff(attempt, base=1.0, multiplier=2.0)
                   for attempt in range(5)]

        # Should be: 1, 2, 4, 8, 16 (without jitter)
        assert backoffs[0] >= 0.5 and backoffs[0] <= 1.5  # ~1s with jitter
        assert backoffs[1] >= 1.0 and backoffs[1] <= 3.0  # ~2s with jitter
        assert backoffs[2] >= 2.0 and backoffs[2] <= 6.0  # ~4s with jitter

    def test_backoff_with_custom_base(self):
        """Test custom base delay."""
        backoff = calculate_backoff(0, base=2.0, multiplier=2.0, jitter=False)
        assert backoff == 2.0

    def test_backoff_with_custom_multiplier(self):
        """Test custom multiplier."""
        backoff1 = calculate_backoff(1, base=1.0, multiplier=3.0, jitter=False)
        assert backoff1 == 3.0

    def test_backoff_with_max_delay(self):
        """Test backoff is capped at max_delay."""
        backoff = calculate_backoff(10, base=1.0, multiplier=2.0, max_delay=10.0, jitter=False)
        assert backoff <= 10.0

    def test_backoff_with_jitter(self):
        """Test jitter adds randomness."""
        backoffs = [calculate_backoff(1, base=1.0, multiplier=2.0, jitter=True)
                   for _ in range(10)]

        # With jitter, values should vary
        assert len(set(backoffs)) > 1

    def test_backoff_without_jitter(self):
        """Test backoff without jitter is deterministic."""
        backoff1 = calculate_backoff(2, base=1.0, multiplier=2.0, jitter=False)
        backoff2 = calculate_backoff(2, base=1.0, multiplier=2.0, jitter=False)
        assert backoff1 == backoff2


class TestRetryPolicy:
    """Test retry policy configuration."""

    def test_default_policy(self):
        """Test default retry policy."""
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.base_delay == 1.0
        assert policy.multiplier == 2.0
        assert policy.max_delay == 60.0
        assert policy.jitter is True

    def test_custom_policy(self):
        """Test custom retry policy."""
        policy = RetryPolicy(
            max_attempts=5,
            base_delay=2.0,
            multiplier=3.0,
            max_delay=120.0,
            jitter=False
        )
        assert policy.max_attempts == 5
        assert policy.base_delay == 2.0
        assert policy.multiplier == 3.0
        assert policy.max_delay == 120.0
        assert policy.jitter is False

    def test_invalid_max_attempts(self):
        """Test invalid max_attempts raises error."""
        with pytest.raises(ValueError):
            RetryPolicy(max_attempts=0)

    def test_invalid_base_delay(self):
        """Test invalid base_delay raises error."""
        with pytest.raises(ValueError):
            RetryPolicy(base_delay=-1)

    def test_invalid_multiplier(self):
        """Test invalid multiplier raises error."""
        with pytest.raises(ValueError):
            RetryPolicy(multiplier=0.5)


class TestRetryMechanism:
    """Test retry mechanism."""

    def test_succeeds_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        mock_func = Mock(return_value="success")

        result = retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_succeeds_after_retries(self):
        """Test function succeeds after some retries."""
        mock_func = Mock(side_effect=[
            Exception("error 1"),
            Exception("error 2"),
            "success"
        ])

        result = retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_fails_after_max_attempts(self):
        """Test function fails after max attempts."""
        mock_func = Mock(side_effect=Exception("persistent error"))

        with pytest.raises(RetryExhaustedError) as exc_info:
            retry_with_backoff(mock_func, max_attempts=3, base_delay=0.01)

        assert "persistent error" in str(exc_info.value)
        assert mock_func.call_count == 3

    def test_retry_counts_correctly(self):
        """Test retry attempts are counted correctly."""
        attempts = []

        def mock_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("retry")
            return "success"

        result = retry_with_backoff(mock_func, max_attempts=5, base_delay=0.01)

        assert result == "success"
        assert len(attempts) == 3

    def test_retry_with_args_and_kwargs(self):
        """Test retry with function arguments."""
        mock_func = Mock(side_effect=[Exception("error"), "success"])

        result = retry_with_backoff(
            mock_func,
            "arg1", "arg2",
            kwarg1="value1",
            max_attempts=3,
            base_delay=0.01
        )

        assert result == "success"
        mock_func.assert_called_with("arg1", "arg2", kwarg1="value1")


class TestDeadlineHandling:
    """Test deadline enforcement."""

    def test_deadline_exceeded(self):
        """Test operation fails when deadline is exceeded."""
        attempts = []

        def slow_func():
            attempts.append(1)
            time.sleep(0.5)
            raise Exception("retry")

        # With retries and backoff, should exceed 1.0s deadline
        with pytest.raises(DeadlineExceededError):
            retry_with_backoff(
                slow_func,
                deadline=1.0,
                max_attempts=10,
                base_delay=0.3
            )

    def test_deadline_not_exceeded(self):
        """Test operation succeeds within deadline."""
        def fast_func():
            return "success"

        result = retry_with_backoff(fast_func, deadline=5.0)
        assert result == "success"

    def test_deadline_prevents_unnecessary_retries(self):
        """Test deadline prevents retries that would exceed it."""
        attempts = []

        def mock_func():
            attempts.append(time.time())
            raise Exception("error")

        start = time.time()

        with pytest.raises(DeadlineExceededError):
            retry_with_backoff(
                mock_func,
                max_attempts=10,
                base_delay=1.0,
                deadline=2.0
            )

        elapsed = time.time() - start

        # Should stop before deadline
        assert elapsed < 3.0
        # Should not attempt all 10 retries
        assert len(attempts) < 10


class TestRetryOnSpecificExceptions:
    """Test retry on specific exception types."""

    def test_retry_on_specific_exception(self):
        """Test retry only on specific exception types."""
        mock_func = Mock(side_effect=[
            ConnectionError("connection failed"),
            "success"
        ])

        result = retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=0.01,
            retry_on=(ConnectionError,)
        )

        assert result == "success"
        assert mock_func.call_count == 2

    def test_no_retry_on_other_exceptions(self):
        """Test no retry on other exception types."""
        mock_func = Mock(side_effect=ValueError("value error"))

        with pytest.raises(ValueError):
            retry_with_backoff(
                mock_func,
                max_attempts=3,
                base_delay=0.01,
                retry_on=(ConnectionError,)
            )

        # Should fail immediately without retry
        assert mock_func.call_count == 1

    def test_retry_on_multiple_exception_types(self):
        """Test retry on multiple exception types."""
        mock_func = Mock(side_effect=[
            ConnectionError("connection error"),
            TimeoutError("timeout"),
            "success"
        ])

        result = retry_with_backoff(
            mock_func,
            max_attempts=5,
            base_delay=0.01,
            retry_on=(ConnectionError, TimeoutError)
        )

        assert result == "success"
        assert mock_func.call_count == 3


class TestBackoffTiming:
    """Test exponential backoff timing."""

    def test_backoff_timing_increases(self):
        """Test backoff time increases between retries."""
        attempts = []

        def mock_func():
            attempts.append(time.time())
            if len(attempts) < 4:
                raise Exception("retry")
            return "success"

        retry_with_backoff(
            mock_func,
            max_attempts=5,
            base_delay=0.1,
            multiplier=2.0,
            jitter=False
        )

        # Calculate delays between attempts
        delays = [attempts[i+1] - attempts[i] for i in range(len(attempts)-1)]

        # Each delay should be approximately double the previous
        # (with some tolerance for timing precision)
        assert delays[0] >= 0.08  # ~0.1s
        assert delays[1] >= 0.18  # ~0.2s
        assert delays[2] >= 0.38  # ~0.4s

    def test_backoff_respects_max_delay(self):
        """Test backoff doesn't exceed max_delay."""
        attempts = []

        def mock_func():
            attempts.append(time.time())
            if len(attempts) < 5:
                raise Exception("retry")
            return "success"

        retry_with_backoff(
            mock_func,
            max_attempts=6,
            base_delay=1.0,
            multiplier=2.0,
            max_delay=2.0,
            jitter=False
        )

        # Calculate delays between attempts
        delays = [attempts[i+1] - attempts[i] for i in range(len(attempts)-1)]

        # No delay should exceed max_delay
        assert all(delay <= 2.5 for delay in delays)


class TestJitterBehavior:
    """Test jitter prevents thundering herd."""

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to backoff."""
        delays = []

        for _ in range(10):
            delay = calculate_backoff(3, base=1.0, multiplier=2.0, jitter=True)
            delays.append(delay)

        # Delays should vary (not all the same)
        assert len(set(delays)) > 5

    def test_jitter_stays_within_bounds(self):
        """Test jitter keeps delays within reasonable bounds."""
        for _ in range(100):
            delay = calculate_backoff(
                3,
                base=1.0,
                multiplier=2.0,
                jitter=True
            )

            # Expected: 2^3 * 1.0 = 8.0
            # With jitter: 0.5 * 8.0 to 1.5 * 8.0
            assert 4.0 <= delay <= 12.0


class TestRetryDecorator:
    """Test retry decorator."""

    def test_decorator_basic(self):
        """Test retry decorator on function."""
        attempts = []

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky_function():
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("retry")
            return "success"

        result = flaky_function()

        assert result == "success"
        assert len(attempts) == 3

    def test_decorator_with_policy(self):
        """Test retry decorator with policy."""
        policy = RetryPolicy(max_attempts=4, base_delay=0.01)
        attempts = []

        @retry_with_backoff(policy=policy)
        def flaky_function():
            attempts.append(1)
            if len(attempts) < 2:
                raise Exception("retry")
            return "success"

        result = flaky_function()

        assert result == "success"
        assert len(attempts) == 2


class TestRetryMetrics:
    """Test retry metrics tracking."""

    def test_metrics_track_attempts(self):
        """Test metrics track number of attempts."""
        mock_func = Mock(side_effect=[
            Exception("error 1"),
            Exception("error 2"),
            "success"
        ])

        result, metrics = retry_with_backoff(
            mock_func,
            max_attempts=5,
            base_delay=0.01,
            return_metrics=True
        )

        assert result == "success"
        assert metrics['attempts'] == 3
        assert metrics['success'] is True

    def test_metrics_track_failures(self):
        """Test metrics track failures."""
        mock_func = Mock(side_effect=Exception("persistent error"))

        with pytest.raises(RetryExhaustedError) as exc_info:
            result, metrics = retry_with_backoff(
                mock_func,
                max_attempts=3,
                base_delay=0.01,
                return_metrics=True
            )

        # Metrics should be available on exception
        metrics = exc_info.value.metrics
        assert metrics['attempts'] == 3
        assert metrics['success'] is False

    def test_metrics_track_total_time(self):
        """Test metrics track total elapsed time."""
        def slow_func():
            time.sleep(0.1)
            return "success"

        result, metrics = retry_with_backoff(
            slow_func,
            max_attempts=3,
            base_delay=0.01,
            return_metrics=True
        )

        assert metrics['total_time'] >= 0.1
        assert metrics['total_time'] < 1.0


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_delay(self):
        """Test retry with zero delay."""
        mock_func = Mock(side_effect=[Exception("error"), "success"])

        result = retry_with_backoff(
            mock_func,
            max_attempts=3,
            base_delay=0.0
        )

        assert result == "success"

    def test_single_attempt(self):
        """Test with max_attempts=1."""
        mock_func = Mock(side_effect=Exception("error"))

        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(mock_func, max_attempts=1)

        assert mock_func.call_count == 1

    def test_very_high_max_attempts(self):
        """Test with very high max_attempts."""
        mock_func = Mock(side_effect=[Exception("error")] * 99 + ["success"])

        result = retry_with_backoff(
            mock_func,
            max_attempts=100,
            base_delay=0.001
        )

        assert result == "success"
        assert mock_func.call_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
