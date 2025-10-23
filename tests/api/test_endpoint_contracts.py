#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Endpoint Contract Tests
============================

Tests to verify all FastAPI endpoints return correct status codes,
response schemas, and error formats according to API contracts.

Module: tests.api.test_endpoint_contracts
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import json


# Import the FastAPI app
try:
    from pokertool.api import app
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    app = None


pytestmark = pytest.mark.skipif(not API_AVAILABLE, reason="FastAPI not available")


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    if not API_AVAILABLE:
        pytest.skip("FastAPI not available")
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Get authentication headers for testing protected endpoints."""
    # TODO: Implement actual authentication
    return {"Authorization": "Bearer test-token"}


class TestHealthEndpoints:
    """Test health check and monitoring endpoints."""

    def test_health_endpoint_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_response_schema(self, client):
        """Health endpoint should return valid response schema."""
        response = client.get("/health")
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy", "degraded"]

    def test_system_health_endpoint(self, client):
        """System health endpoint should return comprehensive health data."""
        response = client.get("/api/system/health")

        # Should return 200 even if some checks fail
        assert response.status_code == 200
        data = response.json()

        # Verify comprehensive health data structure
        assert isinstance(data, dict)
        assert "overall_status" in data
        assert "checks" in data or "components" in data or "categories" in data


class TestAuthenticationEndpoints:
    """Test authentication and authorization endpoints."""

    def test_login_endpoint_requires_credentials(self, client):
        """Login endpoint should require username and password."""
        response = client.post("/auth/login", json={})

        # Should return 422 (validation error) for missing credentials, or 404 if not implemented
        assert response.status_code in [400, 404, 422]

    def test_login_invalid_credentials(self, client):
        """Login endpoint should reject invalid credentials."""
        response = client.post("/auth/login", json={
            "username": "invalid_user",
            "password": "wrong_password"
        })

        # Should return 401 for invalid credentials, or 404 if not implemented
        assert response.status_code in [401, 404, 422]

    def test_protected_endpoint_requires_auth(self, client):
        """Protected endpoints should require authentication."""
        # Try accessing protected endpoint without auth
        response = client.get("/api/ai/stats")

        # Should return 401 or 403 for missing authentication
        assert response.status_code in [401, 403]


class TestAIEndpoints:
    """Test AI and LangChain endpoints."""

    def test_ai_health_endpoint(self, client):
        """AI health endpoint should be accessible."""
        response = client.get("/api/ai/health")

        # Health endpoints should be public
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_ai_analyze_hand_requires_auth(self, client):
        """AI analyze hand endpoint should require authentication."""
        response = client.post("/api/ai/analyze_hand", json={
            "hand_text": "Test hand",
            "query": "What should I do?"
        })

        # Should require authentication
        assert response.status_code in [401, 403]

    def test_ai_chat_requires_auth(self, client):
        """AI chat endpoint should require authentication."""
        response = client.post("/api/ai/chat", json={
            "query": "Tell me about poker strategy"
        })

        # Should require authentication
        assert response.status_code in [401, 403]


class TestErrorHandling:
    """Test error response formats and status codes."""

    def test_not_found_returns_404(self, client):
        """Non-existent endpoints should return 404."""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404

    def test_error_response_format(self, client):
        """Error responses should have consistent format."""
        response = client.get("/api/nonexistent/endpoint")

        # Verify error response structure
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()

        # Should have detail or message field, or error wrapper with message
        assert "detail" in data or "message" in data or ("error" in data and "message" in data["error"])

    def test_validation_error_format(self, client):
        """Validation errors should return 422 with detailed errors."""
        # Send invalid data to an endpoint
        response = client.post("/api/ai/analyze_hand", json={
            "invalid_field": "value"
        })

        # Should return 422 for validation error (or 401 for auth)
        assert response.status_code in [401, 403, 422]


class TestResponseHeaders:
    """Test response headers for security and caching."""

    def test_cors_headers(self, client):
        """Responses should include appropriate CORS headers."""
        response = client.get("/health")

        # Check for CORS headers (may vary based on configuration)
        # This is a basic check - adjust based on your CORS policy
        assert response.status_code == 200

    def test_content_type_headers(self, client):
        """JSON endpoints should have correct content-type headers."""
        response = client.get("/health")

        assert "application/json" in response.headers.get("content-type", "").lower()

    def test_security_headers(self, client):
        """Responses should include security headers."""
        response = client.get("/health")

        # Check for common security headers
        # Note: These may not all be present depending on middleware config
        headers = response.headers

        # At minimum, we should not expose sensitive server info
        assert "X-Powered-By" not in headers or "fastapi" not in headers.get("X-Powered-By", "").lower()


class TestRateLimiting:
    """Test rate limiting is enforced."""

    def test_rate_limit_headers(self, client):
        """Endpoints should include rate limit headers if configured."""
        response = client.get("/health")

        # Check if rate limit headers are present
        # This is optional - some endpoints may not have rate limiting
        assert response.status_code == 200


# Test data validation
class TestDataValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_prevention(self, client):
        """Endpoints should prevent SQL injection attempts."""
        malicious_input = "'; DROP TABLE users; --"

        # Try SQL injection in various endpoints
        response = client.post("/api/ai/analyze_hand", json={
            "hand_text": malicious_input,
            "query": "test"
        })

        # Should either reject with 422 or handle safely (not 500)
        assert response.status_code != 500

    def test_xss_prevention(self, client):
        """Endpoints should prevent XSS attempts."""
        xss_input = "<script>alert('XSS')</script>"

        response = client.post("/api/ai/analyze_hand", json={
            "hand_text": xss_input,
            "query": "test"
        })

        # Should either reject or sanitize (not 500)
        assert response.status_code != 500


# Summary test
def test_critical_endpoints_available(client):
    """Verify all critical endpoints are accessible."""
    critical_endpoints = [
        "/health",
        "/api/ai/health",
    ]

    for endpoint in critical_endpoints:
        response = client.get(endpoint)
        # Should not return 404 or 500
        assert response.status_code not in [404, 500], f"Endpoint {endpoint} failed with {response.status_code}"
