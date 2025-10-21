#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Centralized Error Handling Middleware
=====================================

Comprehensive error handling middleware for FastAPI that catches all unhandled
exceptions, logs them with context, integrates with Sentry, and returns
user-friendly error responses.

Module: pokertool.error_middleware
Version: 1.0.0
"""

import os
import sys
import traceback
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import logging

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorContext:
    """Container for error context information."""

    def __init__(
        self,
        request: Request,
        error: Exception,
        correlation_id: Optional[str] = None
    ):
        self.request = request
        self.error = error
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow().isoformat()
        self.method = request.method
        self.url = str(request.url)
        self.client_host = request.client.host if request.client else "unknown"
        self.user_agent = request.headers.get("user-agent", "unknown")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "method": self.method,
            "url": self.url,
            "client_host": self.client_host,
            "user_agent": self.user_agent,
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
        }


class ErrorHandler:
    """
    Centralized error handler for all application exceptions.

    Provides consistent error logging, Sentry integration, and user-friendly
    error responses.
    """

    def __init__(self, enable_sentry: bool = True):
        """
        Initialize error handler.

        Args:
            enable_sentry: Whether to enable Sentry integration
        """
        self.enable_sentry = enable_sentry and os.getenv("SENTRY_DSN")
        self.sentry_initialized = False

        if self.enable_sentry:
            self._init_sentry()

    def _init_sentry(self):
        """Initialize Sentry SDK."""
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration

            sentry_dsn = os.getenv("SENTRY_DSN")
            if not sentry_dsn:
                logger.warning("SENTRY_DSN not set, Sentry integration disabled")
                self.enable_sentry = False
                return

            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=os.getenv("ENVIRONMENT", "development"),
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                integrations=[
                    StarletteIntegration(),
                    FastApiIntegration(),
                ],
                # Send PII (Personally Identifiable Information)
                send_default_pii=False,
                # Set release version
                release=os.getenv("APP_VERSION", "unknown"),
            )

            self.sentry_initialized = True
            logger.info("Sentry integration initialized")

        except ImportError:
            logger.warning("sentry-sdk not installed, Sentry integration disabled")
            self.enable_sentry = False
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.enable_sentry = False

    def capture_exception(
        self,
        error: Exception,
        context: ErrorContext,
        level: str = "error"
    ):
        """
        Capture exception with Sentry.

        Args:
            error: The exception to capture
            context: Error context information
            level: Severity level (error, warning, info)
        """
        if not self.sentry_initialized:
            return

        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                # Add context
                scope.set_tag("correlation_id", context.correlation_id)
                scope.set_tag("method", context.method)
                scope.set_tag("url", context.url)
                scope.set_context("request", {
                    "url": context.url,
                    "method": context.method,
                    "client_host": context.client_host,
                    "user_agent": context.user_agent,
                })

                # Set level
                scope.level = level

                # Capture exception
                sentry_sdk.capture_exception(error)

        except Exception as e:
            logger.error(f"Failed to capture exception with Sentry: {e}")

    def log_error(
        self,
        context: ErrorContext,
        include_traceback: bool = True
    ):
        """
        Log error with full context.

        Args:
            context: Error context information
            include_traceback: Whether to include full traceback
        """
        error_data = context.to_dict()

        if include_traceback:
            error_data["traceback"] = traceback.format_exc()

        logger.error(
            f"Unhandled exception in {context.method} {context.url}: "
            f"{type(context.error).__name__}: {context.error}",
            extra=error_data
        )


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler instance."""
    global _error_handler
    if _error_handler is None:
        enable_sentry = os.getenv("ENABLE_SENTRY", "true").lower() == "true"
        _error_handler = ErrorHandler(enable_sentry=enable_sentry)
    return _error_handler


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTPException and return consistent JSON response.

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSON response with error details
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "status_code": exc.status_code,
                "message": exc.detail,
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSON response with validation error details
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else None
    handler = get_error_handler()

    # Log validation error
    context = ErrorContext(request, exc, correlation_id)
    logger.warning(f"Validation error: {exc.errors()}", extra=context.to_dict())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "status_code": 422,
                "message": "Request validation failed",
                "details": exc.errors(),
                "correlation_id": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        JSON response with error details
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else None
    handler = get_error_handler()

    # Create error context
    context = ErrorContext(request, exc, correlation_id)

    # Log error with full context
    handler.log_error(context, include_traceback=True)

    # Capture with Sentry
    handler.capture_exception(exc, context, level="error")

    # Determine if we should show detailed error (development mode)
    show_details = os.getenv("ENVIRONMENT", "production") == "development"

    error_response = {
        "error": {
            "type": "internal_error",
            "status_code": 500,
            "message": "An internal server error occurred",
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }

    if show_details:
        error_response["error"]["details"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc().split("\n"),
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


def register_error_handlers(app):
    """
    Register all error handlers with FastAPI app.

    Args:
        app: FastAPI application instance

    Example:
        from pokertool.error_middleware import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)
    """
    # Initialize error handler
    get_error_handler()

    # Register exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers registered successfully")


# Export public API
__all__ = [
    'ErrorHandler',
    'ErrorContext',
    'get_error_handler',
    'register_error_handlers',
    'http_exception_handler',
    'validation_exception_handler',
    'generic_exception_handler',
]
