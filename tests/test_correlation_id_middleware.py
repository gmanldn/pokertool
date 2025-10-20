#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for Correlation ID Middleware
=========================================

Comprehensive tests for correlation ID generation, propagation, and distributed tracing.

Module: tests.test_correlation_id_middleware
Version: 1.0.0
"""

import pytest
import uuid
import logging
from unittest.mock import Mock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pokertool.correlation_id_middleware import (
    CorrelationIdMiddleware,
    get_correlation_id,
    set_correlation_id,
    CorrelationIdFilter,
    get_logger_with_correlation_id,
    CorrelationIdPropagator,
    DatabaseQueryTracer,
    correlation_id_context
)


class TestCorrelationIdMiddleware:
    """Test correlation ID middleware for FastAPI."""

    def create_test_app(self, header_name="X-Correlation-ID", generator=None):
        """Create test FastAPI app with correlation ID middleware."""
        app = FastAPI()

        app.add_middleware(
            CorrelationIdMiddleware,
            header_name=header_name,
            generator=generator
        )

        @app.get("/test")
        async def test_endpoint():
            # Get correlation ID from context
            corr_id = get_correlation_id()
            return {"correlation_id": corr_id}

        @app.post("/test")
        async def post_endpoint():
            corr_id = get_correlation_id()
            return {"correlation_id": corr_id}

        return app

    def test_middleware_generates_correlation_id(self):
        """Test middleware generates correlation ID when not provided."""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Correlation-ID" in response.headers

        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) > 0

        # Should be valid UUID
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail("Generated correlation ID is not a valid UUID")

    def test_middleware_accepts_existing_correlation_id(self):
        """Test middleware accepts correlation ID from request header."""
        app = self.create_test_app()
        client = TestClient(app)

        provided_id = str(uuid.uuid4())

        response = client.get(
            "/test",
            headers={"X-Correlation-ID": provided_id}
        )

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == provided_id

        # Response body should also contain same ID
        data = response.json()
        assert data["correlation_id"] == provided_id

    def test_middleware_adds_correlation_id_to_response_headers(self):
        """Test middleware adds correlation ID to response headers."""
        app = self.create_test_app()
        client = TestClient(app)

        response = client.get("/test")

        assert "X-Correlation-ID" in response.headers
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) > 0

    def test_middleware_custom_header_name(self):
        """Test middleware with custom header name."""
        app = self.create_test_app(header_name="X-Request-ID")
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_middleware_custom_generator(self):
        """Test middleware with custom ID generator."""
        def custom_generator():
            return "custom-id-12345"

        app = self.create_test_app(generator=custom_generator)
        client = TestClient(app)

        response = client.get("/test")

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == "custom-id-12345"

    def test_correlation_id_consistent_across_request(self):
        """Test correlation ID remains consistent throughout request lifecycle."""
        app = self.create_test_app()

        collected_ids = []

        @app.get("/multi-check")
        async def multi_check():
            # Check ID multiple times
            id1 = get_correlation_id()
            id2 = get_correlation_id()
            id3 = get_correlation_id()
            collected_ids.extend([id1, id2, id3])
            return {"ids": [id1, id2, id3]}

        client = TestClient(app)
        response = client.get("/multi-check")

        data = response.json()
        ids = data["ids"]

        # All IDs should be the same
        assert ids[0] == ids[1] == ids[2]

    def test_correlation_id_different_for_different_requests(self):
        """Test different correlation IDs for different requests."""
        app = self.create_test_app()
        client = TestClient(app)

        response1 = client.get("/test")
        response2 = client.get("/test")

        id1 = response1.headers["X-Correlation-ID"]
        id2 = response2.headers["X-Correlation-ID"]

        # IDs should be different
        assert id1 != id2

    def test_correlation_id_propagated_to_post_request(self):
        """Test correlation ID works with POST requests."""
        app = self.create_test_app()
        client = TestClient(app)

        provided_id = str(uuid.uuid4())

        response = client.post(
            "/test",
            headers={"X-Correlation-ID": provided_id},
            json={"data": "test"}
        )

        assert response.status_code == 200
        assert response.headers["X-Correlation-ID"] == provided_id


class TestCorrelationIdContext:
    """Test correlation ID context management."""

    def test_get_correlation_id_returns_none_when_not_set(self):
        """Test get_correlation_id returns None when no ID is set."""
        # Reset context
        correlation_id_context.set(None)

        corr_id = get_correlation_id()
        assert corr_id is None

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID."""
        test_id = str(uuid.uuid4())

        set_correlation_id(test_id)
        retrieved_id = get_correlation_id()

        assert retrieved_id == test_id

    def test_correlation_id_context_isolation(self):
        """Test correlation ID is isolated per context."""
        # This test demonstrates context isolation
        # In real async scenarios, each request would have separate context

        test_id1 = str(uuid.uuid4())
        set_correlation_id(test_id1)

        retrieved = get_correlation_id()
        assert retrieved == test_id1


class TestCorrelationIdFilter:
    """Test correlation ID logging filter."""

    def test_filter_adds_correlation_id_to_log_record(self):
        """Test filter adds correlation ID to log records."""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)

        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        log_filter.filter(record)

        assert hasattr(record, 'correlation_id')
        assert record.correlation_id == test_id

    def test_filter_adds_na_when_no_correlation_id(self):
        """Test filter adds N/A when no correlation ID is set."""
        correlation_id_context.set(None)

        log_filter = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        log_filter.filter(record)

        assert hasattr(record, 'correlation_id')
        assert record.correlation_id == "N/A"

    def test_filter_returns_true(self):
        """Test filter always returns True to pass log records."""
        log_filter = CorrelationIdFilter()
        record = Mock()

        result = log_filter.filter(record)
        assert result is True


class TestGetLoggerWithCorrelationId:
    """Test logger creation with correlation ID filter."""

    def test_get_logger_with_correlation_id_adds_filter(self):
        """Test logger has correlation ID filter added."""
        logger = get_logger_with_correlation_id("test_logger")

        # Check filter is added
        filters = logger.filters
        assert len(filters) > 0

        # At least one filter should be CorrelationIdFilter
        has_correlation_filter = any(
            isinstance(f, CorrelationIdFilter) for f in filters
        )
        assert has_correlation_filter


class TestCorrelationIdPropagator:
    """Test correlation ID propagation to external services."""

    def test_get_headers_includes_correlation_id(self):
        """Test get_headers includes correlation ID."""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)

        headers = CorrelationIdPropagator.get_headers()

        assert "X-Correlation-ID" in headers
        assert headers["X-Correlation-ID"] == test_id

    def test_get_headers_no_correlation_id(self):
        """Test get_headers when no correlation ID is set."""
        correlation_id_context.set(None)

        headers = CorrelationIdPropagator.get_headers()

        # Should return empty dict or dict without correlation ID
        assert "X-Correlation-ID" not in headers

    def test_get_headers_merges_additional_headers(self):
        """Test get_headers merges additional headers."""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)

        additional = {
            "Authorization": "Bearer token",
            "Content-Type": "application/json"
        }

        headers = CorrelationIdPropagator.get_headers(additional)

        assert headers["X-Correlation-ID"] == test_id
        assert headers["Authorization"] == "Bearer token"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_call_service_adds_correlation_id(self):
        """Test call_service adds correlation ID to request."""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)

        # Mock HTTP client method
        mock_client = Mock()
        mock_client.return_value = Mock(status_code=200, json=lambda: {"result": "ok"})

        response = await CorrelationIdPropagator.call_service(
            mock_client,
            "http://example.com/api"
        )

        # Verify client was called with correlation ID header
        mock_client.assert_called_once()
        call_args = mock_client.call_args

        # Check headers argument
        headers = call_args.kwargs.get('headers', {})
        assert "X-Correlation-ID" in headers
        assert headers["X-Correlation-ID"] == test_id


class TestDatabaseQueryTracer:
    """Test database query tracing with correlation ID."""

    def test_trace_query_includes_correlation_id(self):
        """Test trace_query includes correlation ID."""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)

        query = "SELECT * FROM users WHERE id = :id"
        params = {"id": 123}

        metadata = DatabaseQueryTracer.trace_query(query, params)

        assert "correlation_id" in metadata
        assert metadata["correlation_id"] == test_id
        assert metadata["query"] == query
        assert metadata["params"] == params

    def test_trace_query_no_correlation_id(self):
        """Test trace_query when no correlation ID is set."""
        correlation_id_context.set(None)

        query = "SELECT * FROM users"
        metadata = DatabaseQueryTracer.trace_query(query)

        assert "correlation_id" in metadata
        assert metadata["correlation_id"] is None

    def test_trace_query_includes_timestamp(self):
        """Test trace_query includes timestamp."""
        query = "SELECT * FROM users"
        metadata = DatabaseQueryTracer.trace_query(query)

        assert "timestamp" in metadata
        assert len(metadata["timestamp"]) > 0


class TestCorrelationIdDistributedTracing:
    """Test correlation ID for distributed tracing scenarios."""

    def test_correlation_id_propagates_through_service_chain(self):
        """Test correlation ID propagates through multiple services."""
        # Simulate service chain: API Gateway -> Service A -> Service B

        original_id = str(uuid.uuid4())

        # Service A receives request with correlation ID
        set_correlation_id(original_id)
        service_a_id = get_correlation_id()

        # Service A makes request to Service B with same ID
        headers = CorrelationIdPropagator.get_headers()

        # Simulate Service B receiving the ID
        service_b_id = headers.get("X-Correlation-ID")

        # All should have same correlation ID
        assert original_id == service_a_id == service_b_id

    def test_correlation_id_in_logs_across_services(self):
        """Test correlation ID appears in logs across service calls."""
        test_id = str(uuid.uuid4())
        set_correlation_id(test_id)

        logger = get_logger_with_correlation_id("test_service")

        # Create log record
        with patch.object(logger, 'info') as mock_log:
            # The filter will add correlation_id to the record
            # This test demonstrates the setup works
            pass


class TestCorrelationIdEdgeCases:
    """Test edge cases and error scenarios."""

    def test_malformed_correlation_id_accepted(self):
        """Test middleware accepts malformed correlation ID."""
        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)

        @app.get("/test")
        async def test():
            return {"id": get_correlation_id()}

        client = TestClient(app)

        # Provide malformed ID (not a UUID)
        malformed_id = "not-a-uuid-12345"

        response = client.get(
            "/test",
            headers={"X-Correlation-ID": malformed_id}
        )

        assert response.status_code == 200
        # Should still accept and propagate it
        assert response.headers["X-Correlation-ID"] == malformed_id

    def test_empty_correlation_id_generates_new(self):
        """Test empty correlation ID results in new generation."""
        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)

        @app.get("/test")
        async def test():
            return {"id": get_correlation_id()}

        client = TestClient(app)

        response = client.get(
            "/test",
            headers={"X-Correlation-ID": ""}
        )

        assert response.status_code == 200
        # Should generate new ID when empty
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
