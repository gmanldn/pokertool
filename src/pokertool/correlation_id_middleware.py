#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Correlation ID Middleware
==========================

Provides correlation ID generation and propagation for request tracing across services.

Correlation IDs allow tracking a single request across multiple services, microservices,
and asynchronous operations, making debugging and performance analysis much easier.

Module: pokertool.correlation_id_middleware
Version: 1.0.0
"""

import uuid
import contextvars
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

# Context variable for storing correlation ID
correlation_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'correlation_id',
    default=None
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs for request tracing.

    Features:
    - Accepts correlation ID from incoming requests (X-Correlation-ID header)
    - Generates new correlation ID if not provided
    - Adds correlation ID to response headers
    - Stores correlation ID in context for access throughout request lifecycle
    - Automatically includes correlation ID in structured logs
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Correlation-ID",
        generator: Optional[Callable[[], str]] = None
    ):
        """
        Initialize correlation ID middleware.

        Args:
            app: ASGI application
            header_name: HTTP header name for correlation ID
            generator: Optional function to generate correlation IDs
        """
        super().__init__(app)
        self.header_name = header_name
        self.generator = generator or self._default_generator

    @staticmethod
    def _default_generator() -> str:
        """Generate a new correlation ID using UUID4."""
        return str(uuid.uuid4())

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add correlation ID.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with correlation ID header
        """
        # Try to get correlation ID from incoming request
        correlation_id = request.headers.get(self.header_name)

        # Generate new ID if not provided
        if not correlation_id:
            correlation_id = self.generator()

        # Store in context for access throughout request
        correlation_id_context.set(correlation_id)

        # Add to request state for easy access
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id

        return response


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        Current correlation ID or None if not set
    """
    return correlation_id_context.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in context (for testing or manual use).

    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_context.set(correlation_id)


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.

    Usage:
        logger = logging.getLogger()
        logger.addFilter(CorrelationIdFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        record.correlation_id = get_correlation_id() or "N/A"
        return True


# Convenience decorator for functions that should propagate correlation ID
def with_correlation_id(func: Callable) -> Callable:
    """
    Decorator to ensure function has access to current correlation ID.

    Usage:
        @with_correlation_id
        async def process_data():
            corr_id = get_correlation_id()
            # Use correlation ID...
    """
    async def wrapper(*args, **kwargs):
        # Correlation ID is automatically available from context
        return await func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# Example integration with structured logger
def get_logger_with_correlation_id(name: str) -> logging.Logger:
    """
    Get a logger that automatically includes correlation ID in logs.

    Args:
        name: Logger name

    Returns:
        Configured logger with correlation ID filter
    """
    logger = logging.getLogger(name)
    logger.addFilter(CorrelationIdFilter())
    return logger


# Example usage for external service calls
class CorrelationIdPropagator:
    """
    Helper class for propagating correlation ID to external services.

    Usage:
        headers = CorrelationIdPropagator.get_headers()
        response = requests.get(url, headers=headers)
    """

    @staticmethod
    def get_headers(additional_headers: Optional[dict] = None) -> dict:
        """
        Get headers dict with correlation ID for external requests.

        Args:
            additional_headers: Optional additional headers to include

        Returns:
            Headers dict with correlation ID
        """
        headers = additional_headers or {}
        correlation_id = get_correlation_id()

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        return headers

    @staticmethod
    async def call_service(
        client_method: Callable,
        url: str,
        **kwargs
    ):
        """
        Make external service call with correlation ID propagation.

        Args:
            client_method: HTTP client method (e.g., httpx.get)
            url: Service URL
            **kwargs: Additional arguments for client method

        Returns:
            Response from external service
        """
        # Get existing headers
        headers = kwargs.get('headers', {})

        # Add correlation ID
        headers = CorrelationIdPropagator.get_headers(headers)

        # Update kwargs
        kwargs['headers'] = headers

        # Make request
        return await client_method(url, **kwargs)


# Example: Integration with database queries
class DatabaseQueryTracer:
    """
    Example helper for tracing database queries with correlation ID.
    """

    @staticmethod
    def trace_query(query: str, params: Optional[dict] = None) -> dict:
        """
        Add correlation ID to query metadata for tracing.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query metadata with correlation ID
        """
        return {
            "query": query,
            "params": params,
            "correlation_id": get_correlation_id(),
            "timestamp": uuid.uuid1().hex
        }


# Integration with OpenTelemetry tracing
def add_correlation_to_span():
    """
    Add current correlation ID to OpenTelemetry span if tracing is enabled.

    This automatically integrates correlation IDs with distributed tracing.
    """
    try:
        from pokertool.tracing import set_span_attribute
        correlation_id = get_correlation_id()
        if correlation_id:
            set_span_attribute("correlation_id", correlation_id)
    except ImportError:
        # Tracing module not available
        pass
