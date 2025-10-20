#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Retry Utility Module
====================

Retry logic with exponential backoff for handling transient failures in
external API calls and other operations.

Module: pokertool.retry_util
Version: 1.0.0
"""

import time
import random
import functools
from typing import Callable, Type, Tuple, Optional, Any
import logging


logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Exception raised when all retry attempts fail"""
    def __init__(self, message: str, last_exception: Exception, attempts: int):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    Calculate delay for exponential backoff

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential growth
        jitter: Add random jitter to prevent thundering herd

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)

    if jitter:
        # Add jitter between 0 and 100% of delay
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    jitter: bool = True
):
    """
    Decorator for retrying function with exponential backoff

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential calculation
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function(exception, attempt)
        jitter: Add random jitter to delays

    Example:
        @retry_with_backoff(max_attempts=5, base_delay=2.0)
        def fetch_data_from_api():
            response = requests.get('https://api.example.com/data')
            response.raise_for_status()
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts",
                            last_exception,
                            max_attempts
                        ) from e

                    # Calculate delay
                    delay = exponential_backoff(
                        attempt,
                        base_delay,
                        max_delay,
                        exponential_base,
                        jitter
                    )

                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)

                    time.sleep(delay)

            # Should never reach here, but just in case
            raise RetryError(
                f"Failed after {max_attempts} attempts",
                last_exception,
                max_attempts
            )

        return wrapper
    return decorator


class RetryStrategy:
    """
    Configurable retry strategy for programmatic use
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions
        self.jitter = jitter

    def execute(
        self,
        func: Callable,
        *args,
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Function positional arguments
            on_retry: Optional callback on retry
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryError: If all attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return func(*args, **kwargs)

            except self.exceptions as e:
                last_exception = e

                if attempt == self.max_attempts - 1:
                    raise RetryError(
                        f"Failed after {self.max_attempts} attempts",
                        last_exception,
                        self.max_attempts
                    ) from e

                delay = exponential_backoff(
                    attempt,
                    self.base_delay,
                    self.max_delay,
                    self.exponential_base,
                    self.jitter
                )

                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                if on_retry:
                    on_retry(e, attempt + 1)

                time.sleep(delay)

        raise RetryError(
            f"Failed after {self.max_attempts} attempts",
            last_exception,
            self.max_attempts
        )


# Pre-configured retry strategies
API_RETRY = RetryStrategy(
    max_attempts=5,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)

DATABASE_RETRY = RetryStrategy(
    max_attempts=3,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True
)

NETWORK_RETRY = RetryStrategy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

ML_MODEL_RETRY = RetryStrategy(
    max_attempts=3,
    base_delay=1.0,
    max_delay=20.0,
    exponential_base=2.0,
    jitter=True
)


# Convenience functions for common scenarios
def retry_api_call(func: Callable, *args, **kwargs) -> Any:
    """Retry API call with standard configuration"""
    return API_RETRY.execute(func, *args, **kwargs)


def retry_database_operation(func: Callable, *args, **kwargs) -> Any:
    """Retry database operation with standard configuration"""
    return DATABASE_RETRY.execute(func, *args, **kwargs)


def retry_network_request(func: Callable, *args, **kwargs) -> Any:
    """Retry network request with standard configuration"""
    return NETWORK_RETRY.execute(func, *args, **kwargs)


def retry_ml_prediction(func: Callable, *args, **kwargs) -> Any:
    """Retry ML prediction with standard configuration"""
    return ML_MODEL_RETRY.execute(func, *args, **kwargs)
