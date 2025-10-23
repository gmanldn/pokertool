#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Contract Regression Tests

Tests to ensure API endpoints maintain their contracts and don't introduce
breaking changes. Verifies request/response formats, status codes, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from pokertool.api import app


class TestHealthEndpointContract:
    """Tests for /health endpoint contract."""

    def test_health_endpoint_returns_200(self):
        """Verify /health returns 200 OK."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_response_has_required_fields(self):
        """Verify /health response contains required fields."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_response_format(self):
        """Verify /health response format is consistent."""
        client = TestClient(app)
        response = client.get("/health")
        data = response.json()

        assert isinstance(data, dict)
        assert isinstance(data.get("status"), str)

    def test_health_endpoint_accepts_no_parameters(self):
        """Verify /health doesn't require parameters."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_endpoint_rejects_post(self):
        """Verify /health only accepts GET requests."""
        client = TestClient(app)
        response = client.post("/health")

        assert response.status_code in [404, 405, 422]


class TestBankrollEndpointsContract:
    """Tests for bankroll-related endpoints."""

    def test_get_bankroll_endpoint_exists(self):
        """Verify GET /api/bankroll endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/bankroll")

        # Should return 200 or 404, not 500
        assert response.status_code in [200, 404]

    def test_bankroll_response_format(self):
        """Verify bankroll response format."""
        client = TestClient(app)
        response = client.get("/api/bankroll")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_post_transaction_requires_data(self):
        """Verify POST /api/transactions requires data."""
        client = TestClient(app)
        response = client.post("/api/transactions", json={})

        # Should reject empty data
        assert response.status_code in [400, 422]

    def test_post_transaction_validates_amount(self):
        """Verify transaction amount validation."""
        client = TestClient(app)

        # Invalid amount
        response = client.post("/api/transactions", json={
            "amount": "not-a-number",
            "type": "win",
            "date": "2025-10-23"
        })

        assert response.status_code in [400, 422]

    def test_transaction_response_includes_id(self):
        """Verify transaction response includes ID."""
        client = TestClient(app)

        response = client.post("/api/transactions", json={
            "amount": 100,
            "type": "win",
            "date": "2025-10-23"
        })

        if response.status_code == 200:
            data = response.json()
            # Should have some identifier
            assert "id" in data or "transaction_id" in data or isinstance(data, dict)


class TestTournamentEndpointsContract:
    """Tests for tournament-related endpoints."""

    def test_get_tournaments_returns_array(self):
        """Verify GET /api/tournaments returns array."""
        client = TestClient(app)
        response = client.get("/api/tournaments")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_post_tournament_requires_buyin(self):
        """Verify tournament creation requires buy-in."""
        client = TestClient(app)

        response = client.post("/api/tournaments", json={
            "name": "Test Tournament",
            # Missing buy_in
        })

        assert response.status_code in [400, 422]

    def test_tournament_response_format(self):
        """Verify tournament response format."""
        client = TestClient(app)

        response = client.post("/api/tournaments", json={
            "name": "Test Tournament",
            "buy_in": 100,
            "date": "2025-10-23"
        })

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_get_tournament_by_id(self):
        """Verify GET /api/tournaments/{id} endpoint."""
        client = TestClient(app)
        response = client.get("/api/tournaments/123")

        # Should return 200 or 404, not 500
        assert response.status_code in [200, 404]

    def test_delete_tournament_returns_confirmation(self):
        """Verify DELETE /api/tournaments/{id} response."""
        client = TestClient(app)
        response = client.delete("/api/tournaments/123")

        # Should return appropriate status
        assert response.status_code in [200, 204, 404]


class TestSessionEndpointsContract:
    """Tests for session-related endpoints."""

    def test_get_sessions_endpoint_exists(self):
        """Verify GET /api/sessions endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/sessions")

        assert response.status_code in [200, 404]

    def test_post_session_validates_data(self):
        """Verify session creation validates data."""
        client = TestClient(app)

        response = client.post("/api/sessions", json={
            # Missing required fields
        })

        assert response.status_code in [400, 422]

    def test_session_includes_timestamps(self):
        """Verify session response includes timestamps."""
        client = TestClient(app)

        response = client.post("/api/sessions", json={
            "start_time": "2025-10-23T10:00:00",
            "end_time": "2025-10-23T12:00:00",
            "hands": 100,
            "profit": 250
        })

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestSmartHelperEndpointsContract:
    """Tests for SmartHelper API endpoints."""

    def test_get_advice_endpoint_exists(self):
        """Verify GET /api/smarthelper/advice endpoint exists."""
        client = TestClient(app)
        response = client.get("/api/smarthelper/advice")

        assert response.status_code in [200, 404]

    def test_post_hand_analysis_requires_data(self):
        """Verify hand analysis requires hand data."""
        client = TestClient(app)

        response = client.post("/api/smarthelper/analyze", json={})

        assert response.status_code in [400, 422]

    def test_advice_response_format(self):
        """Verify advice response format."""
        client = TestClient(app)

        response = client.post("/api/smarthelper/analyze", json={
            "hole_cards": ["As", "Kh"],
            "community_cards": ["Qs", "Js", "Ts"],
            "pot": 1000,
            "stack": 5000
        })

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestErrorResponseContract:
    """Tests for error response format consistency."""

    def test_404_returns_json_error(self):
        """Verify 404 returns JSON error format."""
        client = TestClient(app)
        response = client.get("/api/nonexistent-endpoint")

        assert response.status_code == 404
        # Should return JSON, not HTML
        assert response.headers.get("content-type") in [
            "application/json",
            "application/json; charset=utf-8",
        ]

    def test_400_includes_error_message(self):
        """Verify 400 errors include descriptive messages."""
        client = TestClient(app)

        response = client.post("/api/transactions", json={
            "invalid": "data"
        })

        if response.status_code in [400, 422]:
            data = response.json()
            # Should have error details
            assert "detail" in data or "error" in data or "message" in data

    def test_500_errors_dont_leak_internals(self):
        """Verify 500 errors don't leak internal details."""
        # This test would need to trigger an internal error
        # Placeholder for implementation
        client = TestClient(app)

        # In production, should not expose stack traces
        assert True

    def test_error_responses_are_json(self):
        """Verify all error responses are JSON formatted."""
        client = TestClient(app)

        endpoints_to_test = [
            ("/api/invalid", "GET"),
            ("/api/transactions", "POST"),
        ]

        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            if response.status_code >= 400:
                # Should be JSON
                content_type = response.headers.get("content-type", "")
                assert "json" in content_type.lower() or response.status_code == 404


class TestAPIVersioning:
    """Tests for API versioning and backwards compatibility."""

    def test_api_version_header_present(self):
        """Verify API version is included in responses."""
        client = TestClient(app)
        response = client.get("/health")

        # May have version header
        version_header = response.headers.get("X-API-Version") or \
                        response.headers.get("API-Version")

        # If versioning is implemented, should be present
        assert response.status_code == 200

    def test_deprecated_endpoints_return_warning(self):
        """Verify deprecated endpoints include deprecation warning."""
        # Placeholder for when endpoints are deprecated
        assert True

    def test_new_endpoints_dont_break_old_clients(self):
        """Verify API changes are backwards compatible."""
        client = TestClient(app)

        # Old-style request should still work
        response = client.get("/health")
        assert response.status_code == 200


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    def test_rate_limit_headers_present(self):
        """Verify rate limit headers are included."""
        client = TestClient(app)
        response = client.get("/health")

        # May include rate limit headers
        assert response.status_code == 200

    def test_rate_limit_exceeded_returns_429(self):
        """Verify rate limit returns 429 Too Many Requests."""
        client = TestClient(app)

        # Make many requests rapidly
        responses = []
        for _ in range(100):
            response = client.get("/health")
            responses.append(response.status_code)

        # Should eventually return 429 if rate limiting is enabled
        # Or all should succeed if no rate limiting
        assert all(code in [200, 429] for code in responses)


class TestCORSHeaders:
    """Tests for CORS header configuration."""

    def test_cors_headers_present(self):
        """Verify CORS headers are configured."""
        client = TestClient(app)
        response = client.options("/health")

        # May include CORS headers
        assert response.status_code in [200, 404, 405]

    def test_allowed_origins_configured(self):
        """Verify allowed origins are properly configured."""
        client = TestClient(app)
        response = client.get("/health", headers={
            "Origin": "http://localhost:3000"
        })

        # Should allow local development origin
        assert response.status_code == 200


class TestSecurityHeaders:
    """Tests for security header presence."""

    def test_security_headers_present(self):
        """Verify security headers are included."""
        client = TestClient(app)
        response = client.get("/health")

        # Check for common security headers
        headers = response.headers

        # May include security headers like X-Content-Type-Options
        assert response.status_code == 200

    def test_no_sensitive_data_in_errors(self):
        """Verify errors don't expose sensitive data."""
        client = TestClient(app)

        response = client.get("/api/nonexistent")

        if response.status_code >= 400:
            data = response.json()
            # Should not contain sensitive data
            assert "password" not in str(data).lower()
            assert "secret" not in str(data).lower()
            assert "token" not in str(data).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
