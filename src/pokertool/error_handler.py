#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Global Error Handler Module
============================

Comprehensive error handling system with detailed logging, user-friendly
messages, and error categorization for the PokerTool application.

Module: pokertool.error_handler
Version: 1.0.0
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, Type
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """Error severity levels for categorization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    ML_MODEL = "ml_model"
    SCREEN_SCRAPING = "screen_scraping"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error"""
    timestamp: datetime
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: str
    stack_trace: Optional[str]
    additional_data: Dict[str, Any]


class PokerToolError(Exception):
    """Base exception for PokerTool application"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        **kwargs
    ):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or self._get_default_user_message()
        self.category = category
        self.severity = severity
        self.additional_data = kwargs

    def _get_default_user_message(self) -> str:
        """Get default user-friendly message"""
        return "An error occurred while processing your request. Please try again."


class SystemError(PokerToolError):
    """System-level errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="A system error occurred. Our team has been notified.",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class NetworkError(PokerToolError):
    """Network-related errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Network connection issue. Please check your connection.",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class DatabaseError(PokerToolError):
    """Database operation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Database operation failed. Please try again later.",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class MLModelError(PokerToolError):
    """Machine learning model errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="AI analysis temporarily unavailable. Using fallback strategy.",
            category=ErrorCategory.ML_MODEL,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ScrapingError(PokerToolError):
    """Screen scraping errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Unable to read game screen. Please ensure poker table is visible.",
            category=ErrorCategory.SCREEN_SCRAPING,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ValidationError(PokerToolError):
    """Input validation errors"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message="Invalid input provided. Please check your data.",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )


class GlobalErrorHandler:
    """
    Global error handler with logging and user-friendly messaging
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._error_count = 0
        self._error_history = []

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        Handle an error with logging and context tracking

        Args:
            error: The exception to handle
            context: Additional context information

        Returns:
            ErrorContext with full error details
        """
        self._error_count += 1
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d')}-{self._error_count:04d}"

        # Determine error category and severity
        if isinstance(error, PokerToolError):
            category = error.category
            severity = error.severity
            user_message = error.user_message
            technical_message = error.message
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.MEDIUM
            user_message = "An unexpected error occurred. Please try again."
            technical_message = str(error)

        # Get stack trace
        stack_trace = ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))

        # Create error context
        error_ctx = ErrorContext(
            timestamp=datetime.now(),
            error_id=error_id,
            category=category,
            severity=severity,
            message=technical_message,
            user_message=user_message,
            technical_details=f"{type(error).__name__}: {technical_message}",
            stack_trace=stack_trace,
            additional_data=context or {}
        )

        # Log error with appropriate level
        self._log_error(error_ctx)

        # Store in history (keep last 100)
        self._error_history.append(error_ctx)
        if len(self._error_history) > 100:
            self._error_history.pop(0)

        return error_ctx

    def _log_error(self, ctx: ErrorContext) -> None:
        """Log error with appropriate severity"""
        log_message = (
            f"[{ctx.error_id}] {ctx.category.value.upper()}: {ctx.message}\n"
            f"Severity: {ctx.severity.value}\n"
            f"Timestamp: {ctx.timestamp.isoformat()}\n"
        )

        if ctx.additional_data:
            log_message += f"Context: {ctx.additional_data}\n"

        if ctx.stack_trace:
            log_message += f"Stack Trace:\n{ctx.stack_trace}"

        # Log based on severity
        if ctx.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif ctx.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif ctx.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        category_counts = {}
        severity_counts = {}

        for error in self._error_history:
            cat = error.category.value
            sev = error.severity.value

            category_counts[cat] = category_counts.get(cat, 0) + 1
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "total_errors": self._error_count,
            "recent_errors": len(self._error_history),
            "by_category": category_counts,
            "by_severity": severity_counts
        }

    def clear_history(self) -> None:
        """Clear error history"""
        self._error_history = []


# Global instance
_global_error_handler = GlobalErrorHandler()


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """Convenience function to use global error handler"""
    return _global_error_handler.handle_error(error, context)


def get_error_stats() -> Dict[str, Any]:
    """Get global error statistics"""
    return _global_error_handler.get_error_stats()


def setup_error_handler(logger: logging.Logger) -> GlobalErrorHandler:
    """Setup global error handler with custom logger"""
    global _global_error_handler
    _global_error_handler = GlobalErrorHandler(logger)
    return _global_error_handler
