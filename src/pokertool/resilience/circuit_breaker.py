"""Circuit Breaker Pattern Implementation (v0.8.0)

Implements the Circuit Breaker pattern to prevent cascading failures
in distributed systems, particularly for database operations.

Circuit States:
- CLOSED: Normal operation, requests go through
- OPEN: Too many failures, requests fail fast
- HALF_OPEN: Testing if service recovered

Reference: https://martinfowler.com/bliki/CircuitBreaker.html
"""

import time
import threading
from enum import Enum
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass, field


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Exception raised when circuit is open."""
    pass


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics."""
    success_count: int = 0
    failure_count: int = 0
    total_calls: int = 0
    last_failure_time: Optional[float] = None
    state: CircuitBreakerState = CircuitBreakerState.CLOSED


class CircuitBreaker:
    """Circuit breaker implementation.

    Prevents cascading failures by failing fast when too many
    errors occur.

    Example:
        cb = CircuitBreaker(failure_threshold=5, timeout=60)

        def risky_operation():
            # Database call that might fail
            return db.query(...)

        try:
            result = cb.call(risky_operation)
        except CircuitBreakerOpenError:
            # Circuit is open, use fallback
            result = get_cached_value()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_max_calls: int = 1,
        state_change_callback: Optional[Callable] = None
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening
            timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls to allow in HALF_OPEN state
            state_change_callback: Called when state changes
        """
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if timeout < 0:
            raise ValueError("timeout cannot be negative")

        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.state_change_callback = state_change_callback

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0  # Consecutive failures (for threshold)
        self.success_count = 0  # Total successes
        self.total_failures = 0  # Total failures (for metrics)
        self.total_calls = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

        self._lock = threading.Lock()

    def can_attempt(self) -> bool:
        """Check if a request can be attempted.

        Returns:
            True if request can be attempted, False otherwise
        """
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True

            if self.state == CircuitBreakerState.OPEN:
                # Check if timeout has elapsed
                if self.opened_at and (time.time() - self.opened_at) >= self.timeout:
                    self._transition_to(CircuitBreakerState.HALF_OPEN)
                    return True
                return False

            if self.state == CircuitBreakerState.HALF_OPEN:
                # Allow limited calls in HALF_OPEN state
                return True

            return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by func
        """
        if not self.can_attempt():
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
            )

        self.total_calls += 1

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def record_success(self):
        """Record a successful operation."""
        with self._lock:
            self.success_count += 1
            self.failure_count = 0  # Reset consecutive failures

            if self.state == CircuitBreakerState.HALF_OPEN:
                self._transition_to(CircuitBreakerState.CLOSED)

    def record_failure(self):
        """Record a failed operation."""
        with self._lock:
            self.failure_count += 1  # Consecutive failures
            self.total_failures += 1  # Total failures
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitBreakerState.OPEN:
                    self.opened_at = time.time()
                    self._transition_to(CircuitBreakerState.OPEN)
            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Failure in HALF_OPEN → reopen circuit
                self.opened_at = time.time()
                self._transition_to(CircuitBreakerState.OPEN)

    def _transition_to(self, new_state: CircuitBreakerState):
        """Transition to a new state.

        Args:
            new_state: Target state
        """
        old_state = self.state
        self.state = new_state

        if old_state == CircuitBreakerState.OPEN and new_state == CircuitBreakerState.HALF_OPEN:
            # Reset failure count when transitioning to HALF_OPEN
            self.failure_count = 0

        if old_state == CircuitBreakerState.HALF_OPEN and new_state == CircuitBreakerState.CLOSED:
            # Full recovery
            self.failure_count = 0
            self.opened_at = None

        # Call state change callback
        if self.state_change_callback:
            try:
                self.state_change_callback(old_state, new_state)
            except Exception:
                # Don't let callback errors affect circuit breaker
                pass

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state.

        Returns:
            Current state
        """
        return self.state

    def get_failure_rate(self) -> float:
        """Get failure rate.

        Returns:
            Failure rate (0.0 to 1.0)
        """
        # Calculate based on total recorded successes and failures
        total_operations = self.success_count + self.total_failures

        if total_operations == 0:
            return 0.0

        return self.total_failures / total_operations

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics.

        Returns:
            Dictionary of metrics
        """
        return {
            'state': self.state,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_calls': self.total_calls,
            'failure_rate': self.get_failure_rate(),
            'last_failure_time': self.last_failure_time,
            'opened_at': self.opened_at,
        }

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.opened_at = None


class DatabaseCircuitBreaker:
    """Circuit breaker specifically for database operations.

    Wraps database queries with circuit breaker protection and
    automatic retry logic.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        retry_count: int = 0
    ):
        """Initialize database circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            timeout: Timeout before attempting recovery
            retry_count: Number of retries for failed operations
        """
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout
        )
        self.retry_count = retry_count

    @property
    def state(self) -> CircuitBreakerState:
        """Get current state."""
        return self.circuit_breaker.state

    def execute_query(
        self,
        query_func: Callable,
        *args,
        retry_count: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Execute a database query with circuit breaker protection.

        Args:
            query_func: Database query function
            *args: Positional arguments
            retry_count: Override default retry count
            **kwargs: Keyword arguments

        Returns:
            Query result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Database exceptions
        """
        retries = retry_count if retry_count is not None else self.retry_count

        last_exception = None

        for attempt in range(retries + 1):
            try:
                return self.circuit_breaker.call(query_func, *args, **kwargs)
            except CircuitBreakerOpenError:
                # Circuit is open, don't retry
                raise
            except Exception as e:
                last_exception = e
                if attempt < retries:
                    # Wait before retry (simple backoff)
                    time.sleep(0.1 * (attempt + 1))
                    continue
                # Final attempt failed, raise
                raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics.

        Returns:
            Dictionary of metrics
        """
        return self.circuit_breaker.get_metrics()

    def reset(self):
        """Reset circuit breaker."""
        self.circuit_breaker.reset()


# Convenience decorator
def circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60
):
    """Decorator to wrap a function with circuit breaker protection.

    Args:
        failure_threshold: Failures before opening
        timeout: Timeout before recovery

    Example:
        @circuit_breaker(failure_threshold=3, timeout=30)
        def get_user(user_id):
            return database.query(user_id)
    """
    cb = CircuitBreaker(failure_threshold=failure_threshold, timeout=timeout)

    def decorator(func):
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator
