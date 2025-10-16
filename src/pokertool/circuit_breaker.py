#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Circuit Breaker Pattern Implementation
=================================================

Implements the circuit breaker pattern for fault tolerance and graceful degradation
when calling external services or unreliable dependencies.

Module: pokertool.circuit_breaker
Version: 1.0.0
Author: PokerTool Development Team
License: MIT

Features:
    - Automatic circuit breaking on repeated failures
    - Configurable failure thresholds
    - Exponential backoff for recovery attempts
    - Health check support
    - Metrics collection
    - Thread-safe implementation

States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures exceeded threshold, requests fail fast
    - HALF_OPEN: Testing if service recovered
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    timeout: float = 60.0  # Seconds before attempting half-open
    expected_exception: type = Exception  # Exception type to catch
    name: str = "unnamed"  # Circuit breaker name for logging


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0  # Rejected while open
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_consecutive_failures: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.
    
    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            name="external_api"
        )
        
        @breaker
        def call_external_api():
            # Your API call here
            pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "unnamed"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting half-open
            expected_exception: Exception type to catch
            name: Name for logging and identification
        """
        self.config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
            name=name
        )
        
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.last_failure_time: Optional[float] = None
        self._lock = threading.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized with threshold={failure_threshold}, timeout={timeout}s")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        with self._lock:
            self.metrics.total_requests += 1
            
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker '{self.config.name}' attempting half-open state")
                    self.state = CircuitState.HALF_OPEN
                    self.metrics.state_changes += 1
                else:
                    self.metrics.rejected_requests += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.config.name}' is OPEN. "
                        f"Service unavailable. Will retry after {self.config.timeout}s."
                    )
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self.metrics.successful_requests += 1
            self.metrics.last_success_time = datetime.utcnow()
            self.metrics.current_consecutive_failures = 0
            
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit breaker '{self.config.name}' recovered, closing circuit")
                self.state = CircuitState.CLOSED
                self.metrics.state_changes += 1
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.metrics.failed_requests += 1
            self.metrics.current_consecutive_failures += 1
            self.metrics.last_failure_time = datetime.utcnow()
            self.last_failure_time = time.time()
            
            if self.metrics.current_consecutive_failures >= self.config.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.warning(
                        f"Circuit breaker '{self.config.name}' threshold exceeded "
                        f"({self.metrics.current_consecutive_failures}/{self.config.failure_threshold}), "
                        f"opening circuit"
                    )
                    self.state = CircuitState.OPEN
                    self.metrics.state_changes += 1
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.config.timeout
    
    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            logger.info(f"Circuit breaker '{self.config.name}' manually reset")
            self.state = CircuitState.CLOSED
            self.metrics.current_consecutive_failures = 0
            self.last_failure_time = None
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get circuit breaker metrics."""
        return self.metrics
    
    def is_healthy(self) -> bool:
        """Check if circuit is healthy (closed or half-open)."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: float = 60.0,
    expected_exception: type = Exception
) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        timeout: Seconds before attempting half-open
        expected_exception: Exception type to catch
        
    Returns:
        CircuitBreaker instance
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                timeout=timeout,
                expected_exception=expected_exception,
                name=name
            )
        return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    with _registry_lock:
        return _circuit_breakers.copy()


def reset_all_circuit_breakers():
    """Reset all circuit breakers to closed state."""
    with _registry_lock:
        for breaker in _circuit_breakers.values():
            breaker.reset()
    logger.info(f"Reset {len(_circuit_breakers)} circuit breakers")


if __name__ == "__main__":
    # Example usage
    import random
    
    @CircuitBreaker(failure_threshold=3, timeout=5, name="test_service")
    def unreliable_service():
        if random.random() < 0.5:
            raise Exception("Service failed")
        return "Success"
    
    # Test circuit breaker
    for i in range(10):
        try:
            result = unreliable_service()
            print(f"Call {i+1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"Call {i+1}: Circuit OPEN - {e}")
        except Exception as e:
            print(f"Call {i+1}: Failed - {e}")
        time.sleep(1)
