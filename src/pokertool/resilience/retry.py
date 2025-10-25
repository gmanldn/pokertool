"""Retry Logic with Exponential Backoff (v0.9.0)

Implements retry mechanism with:
- Exponential backoff
- Jitter to prevent thundering herd
- Deadline handling
- Configurable retry policies
- Exception filtering
- Metrics tracking

Reference: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
"""

import time
import random
import functools
from typing import Any, Callable, Optional, Tuple, Type, Dict
from dataclasses import dataclass


class RetryExhaustedError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    def __init__(self, message, metrics=None):
        super().__init__(message)
        self.metrics = metrics


class DeadlineExceededError(Exception):
    """Exception raised when deadline is exceeded."""
    def __init__(self, message, metrics=None):
        super().__init__(message)
        self.metrics = metrics


@dataclass
class RetryPolicy:
    """Retry policy configuration.

    Attributes:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for first retry
        multiplier: Exponential backoff multiplier
        max_delay: Maximum delay between retries
        jitter: Whether to add random jitter
        retry_on: Tuple of exception types to retry on (None = all)
    """
    max_attempts: int = 3
    base_delay: float = 1.0
    multiplier: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True
    retry_on: Optional[Tuple[Type[Exception], ...]] = None

    def __post_init__(self):
        """Validate policy parameters."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay cannot be negative")
        if self.multiplier < 1.0:
            raise ValueError("multiplier must be at least 1.0")


def calculate_backoff(
    attempt: int,
    base: float = 1.0,
    multiplier: float = 2.0,
    max_delay: Optional[float] = None,
    jitter: bool = True
) -> float:
    """Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        base: Base delay in seconds
        multiplier: Exponential multiplier
        max_delay: Maximum delay cap
        jitter: Add random jitter (±50%)

    Returns:
        Delay in seconds
    """
    # Calculate exponential delay: base * (multiplier ^ attempt)
    delay = base * (multiplier ** attempt)

    # Cap at max_delay if specified
    if max_delay is not None:
        delay = min(delay, max_delay)

    # Add jitter to prevent thundering herd
    if jitter:
        # Random jitter: ±50% of calculated delay
        jitter_factor = random.uniform(0.5, 1.5)
        delay = delay * jitter_factor

    return delay


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """Calculate and sleep for exponential backoff.

    Args:
        attempt: Current attempt number
        base_delay: Base delay
        multiplier: Exponential multiplier
        max_delay: Maximum delay
        jitter: Add jitter

    Returns:
        Actual delay slept
    """
    delay = calculate_backoff(
        attempt,
        base=base_delay,
        multiplier=multiplier,
        max_delay=max_delay,
        jitter=jitter
    )

    time.sleep(delay)
    return delay


def retry_with_backoff(
    func: Optional[Callable] = None,
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    deadline: Optional[float] = None,
    policy: Optional[RetryPolicy] = None,
    return_metrics: bool = False,
    **kwargs
) -> Any:
    """Execute function with exponential backoff retry.

    Can be used as a decorator or called directly.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        multiplier: Exponential multiplier
        max_delay: Maximum delay cap
        jitter: Add random jitter
        retry_on: Tuple of exception types to retry on
        deadline: Maximum total time in seconds
        policy: RetryPolicy object (overrides other params)
        return_metrics: Return (result, metrics) tuple
        **kwargs: Keyword arguments for func

    Returns:
        Result from func, or (result, metrics) if return_metrics=True

    Raises:
        RetryExhaustedError: If all attempts fail
        DeadlineExceededError: If deadline is exceeded
        Exception: Original exception if not retryable

    Examples:
        # Direct call
        result = retry_with_backoff(risky_function, arg1, arg2)

        # As decorator
        @retry_with_backoff(max_attempts=5)
        def fetch_data():
            return requests.get(url)
    """
    # If used as decorator without arguments
    if func is None:
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*inner_args, **inner_kwargs):
                return retry_with_backoff(
                    f,
                    *inner_args,
                    max_attempts=max_attempts,
                    base_delay=base_delay,
                    multiplier=multiplier,
                    max_delay=max_delay,
                    jitter=jitter,
                    retry_on=retry_on,
                    deadline=deadline,
                    policy=policy,
                    return_metrics=return_metrics,
                    **inner_kwargs
                )
            return wrapper
        return decorator

    # Use policy if provided
    if policy:
        max_attempts = policy.max_attempts
        base_delay = policy.base_delay
        multiplier = policy.multiplier
        max_delay = policy.max_delay
        jitter = policy.jitter
        retry_on = policy.retry_on

    # Metrics tracking
    metrics = {
        'attempts': 0,
        'success': False,
        'total_time': 0.0,
        'delays': []
    }

    start_time = time.time()
    last_exception = None

    for attempt in range(max_attempts):
        metrics['attempts'] = attempt + 1

        # Check deadline BEFORE executing
        if deadline is not None:
            elapsed = time.time() - start_time
            if elapsed >= deadline:
                metrics['total_time'] = elapsed
                exc = DeadlineExceededError(
                    f"Deadline of {deadline}s exceeded after {elapsed:.2f}s",
                    metrics=metrics if return_metrics else None
                )
                raise exc

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Success!
            metrics['success'] = True
            metrics['total_time'] = time.time() - start_time

            if return_metrics:
                return result, metrics
            return result

        except Exception as e:
            last_exception = e

            # Check if we should retry this exception type
            if retry_on is not None:
                if not isinstance(e, retry_on):
                    # Not a retryable exception, raise immediately
                    raise

            # Last attempt, don't wait
            if attempt >= max_attempts - 1:
                break

            # Calculate backoff delay
            delay = calculate_backoff(
                attempt,
                base=base_delay,
                multiplier=multiplier,
                max_delay=max_delay,
                jitter=jitter
            )

            metrics['delays'].append(delay)

            # Check if delay would exceed deadline
            if deadline is not None:
                elapsed = time.time() - start_time
                remaining = deadline - elapsed

                if delay >= remaining:
                    metrics['total_time'] = elapsed
                    exc = DeadlineExceededError(
                        f"Next retry would exceed deadline (need {delay:.2f}s, have {remaining:.2f}s)",
                        metrics=metrics if return_metrics else None
                    )
                    raise exc

            # Wait before retry
            time.sleep(delay)

    # All attempts exhausted
    metrics['total_time'] = time.time() - start_time

    exc = RetryExhaustedError(
        f"Failed after {max_attempts} attempts. Last error: {last_exception}",
        metrics=metrics if return_metrics else None
    )
    raise exc


class RetryContext:
    """Context manager for retry operations.

    Example:
        with RetryContext(max_attempts=3) as retry:
            result = risky_operation()
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        multiplier: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """Initialize retry context.

        Args:
            max_attempts: Maximum retry attempts
            base_delay: Base delay
            multiplier: Exponential multiplier
            max_delay: Maximum delay
            jitter: Add jitter
            retry_on: Exception types to retry on
        """
        self.policy = RetryPolicy(
            max_attempts=max_attempts,
            base_delay=base_delay,
            multiplier=multiplier,
            max_delay=max_delay,
            jitter=jitter,
            retry_on=retry_on
        )
        self.attempt = 0
        self.last_exception = None

    def __enter__(self):
        """Enter retry context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit retry context."""
        if exc_type is None:
            # Success, no exception
            return True

        # Check if retryable
        if self.policy.retry_on is not None:
            if not issubclass(exc_type, self.policy.retry_on):
                # Not retryable
                return False

        self.last_exception = exc_val
        self.attempt += 1

        if self.attempt >= self.policy.max_attempts:
            # Exhausted retries
            return False

        # Calculate and apply backoff
        delay = calculate_backoff(
            self.attempt - 1,
            base=self.policy.base_delay,
            multiplier=self.policy.multiplier,
            max_delay=self.policy.max_delay,
            jitter=self.policy.jitter
        )

        time.sleep(delay)

        # Suppress exception to retry
        return True


# Convenience function for database operations
def retry_database_operation(
    operation: Callable,
    *args,
    max_attempts: int = 3,
    **kwargs
) -> Any:
    """Retry database operation with sensible defaults.

    Args:
        operation: Database operation to execute
        *args: Positional arguments
        max_attempts: Maximum attempts
        **kwargs: Keyword arguments

    Returns:
        Operation result
    """
    return retry_with_backoff(
        operation,
        *args,
        max_attempts=max_attempts,
        base_delay=0.5,
        multiplier=2.0,
        max_delay=10.0,
        jitter=True,
        retry_on=(ConnectionError, TimeoutError),
        **kwargs
    )


# Convenience function for API calls
def retry_api_call(
    api_func: Callable,
    *args,
    max_attempts: int = 5,
    deadline: Optional[float] = None,
    **kwargs
) -> Any:
    """Retry API call with sensible defaults.

    Args:
        api_func: API function to call
        *args: Positional arguments
        max_attempts: Maximum attempts
        deadline: Optional deadline
        **kwargs: Keyword arguments

    Returns:
        API response
    """
    return retry_with_backoff(
        api_func,
        *args,
        max_attempts=max_attempts,
        base_delay=1.0,
        multiplier=2.0,
        max_delay=30.0,
        jitter=True,
        deadline=deadline,
        **kwargs
    )
