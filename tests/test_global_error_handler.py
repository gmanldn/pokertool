#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for Global Error Handler
=====================================

Comprehensive tests for centralized error handling with user-friendly messages.

Module: tests.test_global_error_handler
Version: 1.0.0
"""

import pytest
from datetime import datetime

from pokertool.global_error_handler import (
    ErrorCategory,
    ErrorSeverity,
    ErrorResponse,
    GlobalErrorHandler,
    error_handler,
    handle_errors,
    ERROR_MESSAGES,
    ERROR_SUGGESTIONS
)


class TestErrorCategory:
    """Test ErrorCategory enum."""

    def test_error_categories_exist(self):
        """Test all error categories are defined."""
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.DATABASE == "database"
        assert ErrorCategory.NETWORK == "network"
        assert ErrorCategory.AUTHENTICATION == "authentication"
        assert ErrorCategory.AUTHORIZATION == "authorization"
        assert ErrorCategory.NOT_FOUND == "not_found"
        assert ErrorCategory.SYSTEM == "system"


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_severity_levels_exist(self):
        """Test all severity levels are defined."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"


class TestErrorResponse:
    """Test ErrorResponse dataclass."""

    def test_error_response_creation(self):
        """Test creating error response."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test error message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now()
        )

        assert response.error_code == "TEST_ERROR"
        assert response.message == "Test error message"
        assert response.category == ErrorCategory.VALIDATION
        assert response.severity == ErrorSeverity.LOW

    def test_error_response_with_details(self):
        """Test error response with additional details."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            details={"field": "username", "value": "invalid"},
            suggestions=["Check your input", "Try again"],
            technical_message="ValueError: invalid username format"
        )

        assert response.details["field"] == "username"
        assert len(response.suggestions) == 2
        assert response.technical_message is not None

    def test_to_dict_basic(self):
        """Test converting error response to dictionary."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now()
        )

        result_dict = response.to_dict()

        assert result_dict["error_code"] == "TEST_ERROR"
        assert result_dict["message"] == "Test message"
        assert result_dict["category"] == "validation"
        assert result_dict["severity"] == "low"
        assert "timestamp" in result_dict

    def test_to_dict_with_technical_details(self):
        """Test to_dict with include_technical flag."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test message",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            timestamp=datetime.now(),
            technical_message="Detailed technical error",
            traceback="Stack trace here..."
        )

        # Without technical details
        basic_dict = response.to_dict(include_technical=False)
        assert "technical_message" not in basic_dict
        assert "traceback" not in basic_dict

        # With technical details
        full_dict = response.to_dict(include_technical=True)
        assert full_dict["technical_message"] == "Detailed technical error"
        assert full_dict["traceback"] == "Stack trace here..."

    def test_to_dict_with_request_id(self):
        """Test to_dict includes request ID."""
        response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            timestamp=datetime.now(),
            request_id="req-12345"
        )

        result_dict = response.to_dict()
        assert result_dict["request_id"] == "req-12345"


class TestGlobalErrorHandler:
    """Test GlobalErrorHandler class."""

    def test_handler_initialization(self):
        """Test error handler initialization."""
        handler = GlobalErrorHandler(debug_mode=False)
        assert handler.debug_mode is False
        assert len(handler._error_handlers) > 0

    def test_handler_initialization_debug_mode(self):
        """Test error handler initialization with debug mode."""
        handler = GlobalErrorHandler(debug_mode=True)
        assert handler.debug_mode is True

    def test_handle_value_error(self):
        """Test handling ValueError."""
        handler = GlobalErrorHandler()

        try:
            raise ValueError("Invalid value")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "INVALID_INPUT"
        assert error_response.category == ErrorCategory.VALIDATION
        assert error_response.severity == ErrorSeverity.LOW
        assert "Invalid value" in error_response.technical_message

    def test_handle_key_error(self):
        """Test handling KeyError."""
        handler = GlobalErrorHandler()

        try:
            data = {}
            _ = data["missing_key"]
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "MISSING_FIELD"
        assert error_response.category == ErrorCategory.VALIDATION
        assert "missing_key" in str(error_response.details)

    def test_handle_type_error(self):
        """Test handling TypeError."""
        handler = GlobalErrorHandler()

        try:
            _ = "string" + 123
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "INVALID_INPUT"
        assert error_response.category == ErrorCategory.VALIDATION

    def test_handle_file_not_found_error(self):
        """Test handling FileNotFoundError."""
        handler = GlobalErrorHandler()

        try:
            with open("/nonexistent/file.txt"):
                pass
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "RECORD_NOT_FOUND"
        assert error_response.category == ErrorCategory.NOT_FOUND

    def test_handle_permission_error(self):
        """Test handling PermissionError."""
        handler = GlobalErrorHandler()

        try:
            raise PermissionError("Access denied")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "PERMISSION_DENIED"
        assert error_response.category == ErrorCategory.AUTHORIZATION
        assert error_response.severity == ErrorSeverity.MEDIUM

    def test_handle_connection_error(self):
        """Test handling ConnectionError."""
        handler = GlobalErrorHandler()

        try:
            raise ConnectionError("Network unavailable")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "NETWORK_ERROR"
        assert error_response.category == ErrorCategory.NETWORK
        assert error_response.severity == ErrorSeverity.HIGH
        assert error_response.suggestions is not None

    def test_handle_timeout_error(self):
        """Test handling TimeoutError."""
        handler = GlobalErrorHandler()

        try:
            raise TimeoutError("Request timed out")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "TIMEOUT"
        assert error_response.category == ErrorCategory.NETWORK

    def test_handle_generic_error(self):
        """Test handling unknown/generic error."""
        handler = GlobalErrorHandler()

        try:
            raise RuntimeError("Unexpected error")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "INTERNAL_ERROR"
        assert error_response.category == ErrorCategory.SYSTEM
        assert error_response.severity == ErrorSeverity.HIGH

    def test_handle_exception_with_request_id(self):
        """Test handling exception with request ID."""
        handler = GlobalErrorHandler()

        try:
            raise ValueError("Test")
        except Exception as exc:
            error_response = handler.handle_exception(exc, request_id="req-123")

        assert error_response.request_id == "req-123"

    def test_handle_exception_with_context(self):
        """Test handling exception with additional context."""
        handler = GlobalErrorHandler()

        try:
            raise ValueError("Test")
        except Exception as exc:
            error_response = handler.handle_exception(
                exc,
                context={"user_id": "user123", "action": "update_profile"}
            )

        assert error_response.details["user_id"] == "user123"
        assert error_response.details["action"] == "update_profile"

    def test_create_custom_error(self):
        """Test creating custom error."""
        handler = GlobalErrorHandler()

        error_response = handler.create_error(
            error_code="CUSTOM_ERROR",
            message="Custom error message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )

        assert error_response.error_code == "CUSTOM_ERROR"
        assert error_response.message == "Custom error message"
        assert error_response.category == ErrorCategory.VALIDATION

    def test_create_error_uses_default_message(self):
        """Test create_error uses default message if not provided."""
        handler = GlobalErrorHandler()

        error_response = handler.create_error(
            error_code="INVALID_INPUT",
            category=ErrorCategory.VALIDATION
        )

        assert error_response.message == ERROR_MESSAGES["INVALID_INPUT"]

    def test_create_error_uses_default_suggestions(self):
        """Test create_error uses default suggestions if available."""
        handler = GlobalErrorHandler()

        error_response = handler.create_error(
            error_code="RATE_LIMIT_EXCEEDED",
            category=ErrorCategory.RATE_LIMIT
        )

        assert error_response.suggestions == ERROR_SUGGESTIONS["RATE_LIMIT_EXCEEDED"]

    def test_register_custom_handler(self):
        """Test registering custom exception handler."""
        handler = GlobalErrorHandler()

        class CustomException(Exception):
            pass

        def custom_handler(exc):
            return ErrorResponse(
                error_code="CUSTOM_ERROR",
                message="Custom handling",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now()
            )

        handler.register_handler(CustomException, custom_handler)

        try:
            raise CustomException("Test")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.error_code == "CUSTOM_ERROR"
        assert error_response.message == "Custom handling"

    def test_debug_mode_includes_traceback(self):
        """Test debug mode includes traceback."""
        handler = GlobalErrorHandler(debug_mode=True)

        try:
            raise ValueError("Test error")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.traceback is not None
        assert "Traceback" in error_response.traceback

    def test_production_mode_excludes_traceback(self):
        """Test production mode excludes traceback."""
        handler = GlobalErrorHandler(debug_mode=False)

        try:
            raise ValueError("Test error")
        except Exception as exc:
            error_response = handler.handle_exception(exc)

        assert error_response.traceback is None


class TestHandleErrorsDecorator:
    """Test handle_errors decorator."""

    def test_decorator_allows_successful_execution(self):
        """Test decorator allows function to execute successfully."""
        @handle_errors(error_code="TEST_ERROR")
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_handles_exception(self):
        """Test decorator handles exceptions."""
        @handle_errors(error_code="CUSTOM_ERROR", category=ErrorCategory.VALIDATION)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc_info:
            failing_function()

        # Check that error_response was attached
        assert hasattr(exc_info.value, 'error_response')
        assert exc_info.value.error_response.error_code == "CUSTOM_ERROR"

    def test_decorator_with_custom_message(self):
        """Test decorator with custom user message."""
        @handle_errors(
            error_code="CUSTOM_ERROR",
            category=ErrorCategory.VALIDATION,
            user_message="Something went wrong with your input"
        )
        def failing_function():
            raise ValueError("Technical error")

        with pytest.raises(ValueError) as exc_info:
            failing_function()

        assert exc_info.value.error_response.message == "Something went wrong with your input"

    def test_decorator_without_error_code(self):
        """Test decorator without explicit error code uses exception handler."""
        @handle_errors()
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc_info:
            failing_function()

        # Should use default ValueError handler
        assert exc_info.value.error_response.error_code == "INVALID_INPUT"


class TestGlobalErrorHandlerInstance:
    """Test global error_handler instance."""

    def test_global_instance_exists(self):
        """Test global error handler instance exists."""
        assert error_handler is not None
        assert isinstance(error_handler, GlobalErrorHandler)

    def test_global_instance_in_production_mode(self):
        """Test global instance is in production mode."""
        assert error_handler.debug_mode is False


class TestErrorMessages:
    """Test predefined error messages."""

    def test_error_messages_are_user_friendly(self):
        """Test error messages are user-friendly."""
        for error_code, message in ERROR_MESSAGES.items():
            # Should be a string
            assert isinstance(message, str)
            # Should not be empty
            assert len(message) > 0
            # Should not contain technical jargon
            assert "Exception" not in message
            assert "Traceback" not in message

    def test_error_suggestions_exist(self):
        """Test error suggestions are defined."""
        for error_code, suggestions in ERROR_SUGGESTIONS.items():
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0


class TestRealWorldScenarios:
    """Test real-world error handling scenarios."""

    def test_api_validation_error_flow(self):
        """Test typical API validation error flow."""
        handler = GlobalErrorHandler()

        # Simulate API validation error
        try:
            # Invalid card format
            card = "XX"
            if len(card) != 2 or card[0] not in ['A', 'K', 'Q']:
                raise ValueError(f"Invalid card: {card}")
        except Exception as exc:
            error_response = handler.handle_exception(
                exc,
                request_id="api-req-123",
                context={"endpoint": "/api/analyze", "card": "XX"}
            )

        # Should be validation error with user-friendly message
        assert error_response.category == ErrorCategory.VALIDATION
        assert error_response.request_id == "api-req-123"
        assert "endpoint" in error_response.details

        # Convert to API response
        api_response = error_response.to_dict(include_technical=False)
        assert "error_code" in api_response
        assert "message" in api_response
        assert "traceback" not in api_response

    def test_database_error_flow(self):
        """Test database error handling flow."""
        handler = GlobalErrorHandler()

        # Simulate database connection error
        error_response = handler.create_error(
            error_code="DATABASE_CONNECTION",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details={"host": "localhost", "port": 5432}
        )

        assert error_response.message == ERROR_MESSAGES["DATABASE_CONNECTION"]
        assert error_response.suggestions == ERROR_SUGGESTIONS["DATABASE_CONNECTION"]
        assert error_response.severity == ErrorSeverity.HIGH

    def test_rate_limit_error_flow(self):
        """Test rate limiting error flow."""
        handler = GlobalErrorHandler()

        error_response = handler.create_error(
            error_code="RATE_LIMIT_EXCEEDED",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            details={"limit": 100, "window": "1 minute"}
        )

        assert error_response.message == ERROR_MESSAGES["RATE_LIMIT_EXCEEDED"]
        assert error_response.suggestions is not None
        assert "Wait" in error_response.suggestions[0]

    def test_authentication_error_flow(self):
        """Test authentication error flow."""
        handler = GlobalErrorHandler()

        error_response = handler.create_error(
            error_code="TOKEN_EXPIRED",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM
        )

        assert error_response.message == ERROR_MESSAGES["TOKEN_EXPIRED"]
        assert error_response.suggestions is not None
        assert any("login" in s.lower() for s in error_response.suggestions)

    def test_multiple_errors_in_sequence(self):
        """Test handling multiple errors in sequence."""
        handler = GlobalErrorHandler()

        errors = []

        # Simulate multiple errors
        try:
            raise ValueError("First error")
        except Exception as exc:
            errors.append(handler.handle_exception(exc))

        try:
            raise KeyError("missing_field")
        except Exception as exc:
            errors.append(handler.handle_exception(exc))

        try:
            raise ConnectionError("Network failed")
        except Exception as exc:
            errors.append(handler.handle_exception(exc))

        assert len(errors) == 3
        assert errors[0].category == ErrorCategory.VALIDATION
        assert errors[1].category == ErrorCategory.VALIDATION
        assert errors[2].category == ErrorCategory.NETWORK

    def test_error_logging_levels(self):
        """Test different error severity levels result in appropriate logging."""
        handler = GlobalErrorHandler(debug_mode=True)

        # Low severity
        low_error = handler.create_error(
            error_code="TEST_LOW",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW
        )
        assert low_error.severity == ErrorSeverity.LOW

        # Critical severity
        critical_error = handler.create_error(
            error_code="TEST_CRITICAL",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL
        )
        assert critical_error.severity == ErrorSeverity.CRITICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
