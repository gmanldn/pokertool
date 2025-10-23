#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Global Error Handler with User-Friendly Messages
=================================================

Provides centralized error handling with user-friendly messages,
detailed logging, and structured error responses.

Features:
- User-friendly error messages
- Detailed logging for developers
- Structured error responses
- Error categorization
- Automatic error reporting
- Recovery suggestions

Version: 86.5.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import sys
import traceback
import logging
from typing import Dict, Any, Optional, Type, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# Error Categories
# ============================================================================

class ErrorCategory(str, Enum):
    """Error categories for better organization."""
    VALIDATION = "validation"  # Input validation errors
    DATABASE = "database"  # Database-related errors
    NETWORK = "network"  # Network/API errors
    AUTHENTICATION = "authentication"  # Auth errors
    AUTHORIZATION = "authorization"  # Permission errors
    NOT_FOUND = "not_found"  # Resource not found
    CONFIGURATION = "configuration"  # Configuration errors
    SYSTEM = "system"  # System/internal errors
    EXTERNAL = "external"  # External service errors
    RATE_LIMIT = "rate_limit"  # Rate limiting errors
    UNKNOWN = "unknown"  # Uncategorized errors


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"  # Minor issues, recoverable
    MEDIUM = "medium"  # Important but not critical
    HIGH = "high"  # Critical issues
    CRITICAL = "critical"  # System-breaking issues


# ============================================================================
# Error Response Model
# ============================================================================

@dataclass
class ErrorResponse:
    """Structured error response."""
    error_code: str
    message: str  # User-friendly message
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[list[str]] = None
    technical_message: Optional[str] = None  # For developers
    traceback: Optional[str] = None  # For debugging
    request_id: Optional[str] = None  # For tracking

    def to_dict(self, include_technical: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        response = {
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.details:
            response["details"] = self.details

        if self.suggestions:
            response["suggestions"] = self.suggestions

        if self.request_id:
            response["request_id"] = self.request_id

        # Include technical details only in development/debug mode
        if include_technical:
            if self.technical_message:
                response["technical_message"] = self.technical_message
            if self.traceback:
                response["traceback"] = self.traceback

        return response


# ============================================================================
# User-Friendly Error Messages
# ============================================================================

ERROR_MESSAGES = {
    # Validation errors
    "INVALID_INPUT": "The information you provided isn't quite right. Please check and try again.",
    "MISSING_FIELD": "Some required information is missing. Please fill in all required fields.",
    "INVALID_CARD": "The card format doesn't look right. Cards should be like 'As' (Ace of spades) or 'Kh' (King of hearts).",
    "INVALID_BET": "The bet amount doesn't seem valid. Please enter a positive number.",
    "INVALID_RANGE": "The hand range format isn't recognized. Try something like 'AA,KK,QQ' or '22+'.",

    # Database errors
    "DATABASE_ERROR": "We're having trouble accessing the database right now. Please try again in a moment.",
    "DATABASE_CONNECTION": "Can't connect to the database. Please check your connection settings.",
    "RECORD_NOT_FOUND": "We couldn't find what you're looking for. It may have been deleted or doesn't exist.",
    "DUPLICATE_ENTRY": "This already exists in our records. Please try something different.",

    # Network errors
    "NETWORK_ERROR": "We're having trouble connecting. Please check your internet connection.",
    "TIMEOUT": "The request took too long. Please try again.",
    "SERVICE_UNAVAILABLE": "This service is temporarily unavailable. We're working on it!",

    # Authentication errors
    "INVALID_CREDENTIALS": "The username or password isn't correct. Please try again.",
    "TOKEN_EXPIRED": "Your session has expired. Please log in again.",
    "INVALID_TOKEN": "Your session is invalid. Please log in again.",

    # Authorization errors
    "PERMISSION_DENIED": "You don't have permission to do that.",
    "UNAUTHORIZED": "You need to be logged in to do that.",

    # Configuration errors
    "MISSING_CONFIG": "Some configuration is missing. Please check your settings.",
    "INVALID_CONFIG": "The configuration isn't set up correctly. Please check your settings.",

    # System errors
    "INTERNAL_ERROR": "Something went wrong on our end. We've been notified and are looking into it.",
    "NOT_IMPLEMENTED": "This feature isn't available yet. Stay tuned!",

    # External service errors
    "EXTERNAL_SERVICE_ERROR": "We're having trouble connecting to an external service. Please try again later.",

    # Rate limiting
    "RATE_LIMIT_EXCEEDED": "You're making requests too quickly. Please slow down and try again in a moment.",
}

# Recovery suggestions
ERROR_SUGGESTIONS = {
    "DATABASE_CONNECTION": [
        "Check if the database is running",
        "Verify your connection settings in the configuration",
        "Make sure the database credentials are correct"
    ],
    "NETWORK_ERROR": [
        "Check your internet connection",
        "Try refreshing the page",
        "Wait a moment and try again"
    ],
    "TOKEN_EXPIRED": [
        "Click the login button to sign in again",
        "Your session automatically expires after a period of inactivity"
    ],
    "RATE_LIMIT_EXCEEDED": [
        "Wait a few seconds before trying again",
        "Slow down your requests",
        "Contact support if you need higher limits"
    ],
    "INVALID_CARD": [
        "Use format like 'As' for Ace of spades",
        "Valid ranks: A, K, Q, J, T, 9-2",
        "Valid suits: s (spades), h (hearts), d (diamonds), c (clubs)"
    ],
}


# ============================================================================
# Global Error Handler
# ============================================================================

class GlobalErrorHandler:
    """
    Centralized error handling with user-friendly messages.

    Usage:
        handler = GlobalErrorHandler()

        # Handle exception
        error_response = handler.handle_exception(exception)

        # Create custom error
        error = handler.create_error(
            error_code="CUSTOM_ERROR",
            message="Something went wrong",
            category=ErrorCategory.VALIDATION
        )
    """

    def __init__(self, debug_mode: bool = False):
        """
        Initialize error handler.

        Args:
            debug_mode: Include technical details in responses
        """
        self.debug_mode = debug_mode
        self._error_handlers: Dict[Type[Exception], Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default exception handlers."""
        # Built-in exceptions
        self._error_handlers[ValueError] = self._handle_value_error
        self._error_handlers[KeyError] = self._handle_key_error
        self._error_handlers[TypeError] = self._handle_type_error
        self._error_handlers[FileNotFoundError] = self._handle_file_not_found
        self._error_handlers[PermissionError] = self._handle_permission_error
        self._error_handlers[ConnectionError] = self._handle_connection_error
        self._error_handlers[TimeoutError] = self._handle_timeout_error

    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable[[Exception], ErrorResponse]
    ):
        """
        Register a custom exception handler.

        Args:
            exception_type: The exception class to handle
            handler: Function that converts exception to ErrorResponse
        """
        self._error_handlers[exception_type] = handler

    def handle_exception(
        self,
        exception: Exception,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorResponse:
        """
        Handle an exception and return user-friendly error response.

        Args:
            exception: The exception to handle
            request_id: Optional request ID for tracking
            context: Additional context about the error

        Returns:
            ErrorResponse with user-friendly message
        """
        # Find appropriate handler
        handler = None
        for exc_type, exc_handler in self._error_handlers.items():
            if isinstance(exception, exc_type):
                handler = exc_handler
                break

        # Use specific handler or fall back to generic
        if handler:
            error_response = handler(exception)
        else:
            error_response = self._handle_generic_error(exception)

        # Add request ID and context
        error_response.request_id = request_id
        if context:
            if error_response.details is None:
                error_response.details = {}
            error_response.details.update(context)

        # Log the error
        self._log_error(error_response, exception)

        return error_response

    def create_error(
        self,
        error_code: str,
        message: Optional[str] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
        technical_message: Optional[str] = None
    ) -> ErrorResponse:
        """
        Create a custom error response.

        Args:
            error_code: Error code identifier
            message: User-friendly message (uses default if not provided)
            category: Error category
            severity: Error severity
            details: Additional details
            suggestions: Recovery suggestions
            technical_message: Technical message for developers

        Returns:
            ErrorResponse
        """
        # Use default message if not provided
        if message is None:
            message = ERROR_MESSAGES.get(error_code, "An error occurred.")

        # Use default suggestions if not provided
        if suggestions is None:
            suggestions = ERROR_SUGGESTIONS.get(error_code)

        return ErrorResponse(
            error_code=error_code,
            message=message,
            category=category,
            severity=severity,
            timestamp=datetime.now(),
            details=details,
            suggestions=suggestions,
            technical_message=technical_message
        )

    # ========================================================================
    # Default Exception Handlers
    # ========================================================================

    def _handle_value_error(self, exc: ValueError) -> ErrorResponse:
        """Handle ValueError."""
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message=ERROR_MESSAGES["INVALID_INPUT"],
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            technical_message=str(exc),
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_key_error(self, exc: KeyError) -> ErrorResponse:
        """Handle KeyError."""
        return ErrorResponse(
            error_code="MISSING_FIELD",
            message=ERROR_MESSAGES["MISSING_FIELD"],
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            details={"missing_key": str(exc)},
            technical_message=f"Missing key: {exc}",
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_type_error(self, exc: TypeError) -> ErrorResponse:
        """Handle TypeError."""
        return ErrorResponse(
            error_code="INVALID_INPUT",
            message="The data type isn't correct. Please check your input.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            technical_message=str(exc),
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_file_not_found(self, exc: FileNotFoundError) -> ErrorResponse:
        """Handle FileNotFoundError."""
        return ErrorResponse(
            error_code="RECORD_NOT_FOUND",
            message=ERROR_MESSAGES["RECORD_NOT_FOUND"],
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            details={"path": str(exc.filename) if hasattr(exc, 'filename') else None},
            technical_message=str(exc),
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_permission_error(self, exc: PermissionError) -> ErrorResponse:
        """Handle PermissionError."""
        return ErrorResponse(
            error_code="PERMISSION_DENIED",
            message=ERROR_MESSAGES["PERMISSION_DENIED"],
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            technical_message=str(exc),
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_connection_error(self, exc: ConnectionError) -> ErrorResponse:
        """Handle ConnectionError."""
        return ErrorResponse(
            error_code="NETWORK_ERROR",
            message=ERROR_MESSAGES["NETWORK_ERROR"],
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            suggestions=ERROR_SUGGESTIONS["NETWORK_ERROR"],
            technical_message=str(exc),
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_timeout_error(self, exc: TimeoutError) -> ErrorResponse:
        """Handle TimeoutError."""
        return ErrorResponse(
            error_code="TIMEOUT",
            message=ERROR_MESSAGES["TIMEOUT"],
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            timestamp=datetime.now(),
            technical_message=str(exc),
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _handle_generic_error(self, exc: Exception) -> ErrorResponse:
        """Handle generic/unknown exceptions."""
        return ErrorResponse(
            error_code="INTERNAL_ERROR",
            message=ERROR_MESSAGES["INTERNAL_ERROR"],
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            technical_message=f"{exc.__class__.__name__}: {str(exc)}",
            traceback=traceback.format_exc() if self.debug_mode else None
        )

    def _log_error(self, error_response: ErrorResponse, exception: Exception):
        """Log error with appropriate severity."""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_response.severity, logging.ERROR)

        log_message = (
            f"Error [{error_response.error_code}]: {error_response.message}\n"
            f"Category: {error_response.category.value}\n"
            f"Technical: {error_response.technical_message or 'N/A'}"
        )

        logger.log(log_level, log_message, exc_info=exception if self.debug_mode else None)


# ============================================================================
# Global Instance
# ============================================================================

# Create global error handler instance
error_handler = GlobalErrorHandler(debug_mode=False)


# ============================================================================
# Decorator for Error Handling
# ============================================================================

def handle_errors(
    error_code: Optional[str] = None,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    user_message: Optional[str] = None
) -> Callable:
    """
    Decorator to handle errors in functions.

    Args:
        error_code: Custom error code
        category: Error category
        user_message: Custom user-friendly message

    Example:
        @handle_errors(error_code="POKER_ERROR", category=ErrorCategory.VALIDATION)
        def analyze_hand(cards):
            # Function logic
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if error_code:
                    error = error_handler.create_error(
                        error_code=error_code,
                        message=user_message,
                        category=category,
                        technical_message=str(exc)
                    )
                else:
                    error = error_handler.handle_exception(exc)

                # Re-raise with error response attached
                exc.error_response = error
                raise

        return wrapper
    return decorator


# ============================================================================
# Testing
# ============================================================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Global Error Handler Test")
    print("=" * 60)

    handler = GlobalErrorHandler(debug_mode=True)

    # Test various exceptions
    print("\n1. Testing ValueError:")
    try:
        raise ValueError("Invalid card format")
    except Exception as e:
        error = handler.handle_exception(e, request_id="test-123")
        print(f"User message: {error.message}")
        print(f"Category: {error.category.value}")

    print("\n2. Testing KeyError:")
    try:
        data = {}
        _ = data["missing_key"]
    except Exception as e:
        error = handler.handle_exception(e)
        print(f"User message: {error.message}")

    print("\n3. Testing custom error:")
    error = handler.create_error(
        error_code="RATE_LIMIT_EXCEEDED",
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.MEDIUM
    )
    print(f"User message: {error.message}")
    print(f"Suggestions: {error.suggestions}")

    print("\n4. Testing error response dictionary:")
    error_dict = error.to_dict(include_technical=False)
    print(f"Response: {error_dict}")

    print("\n" + "=" * 60)
