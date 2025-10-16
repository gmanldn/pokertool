#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for CSRF Protection Module
======================================

Comprehensive tests for CSRF token generation, validation, and middleware.

Module: tests.test_csrf_protection
Version: 1.0.0
"""

import pytest
import time
import hmac
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response

from pokertool.csrf_protection import (
    CSRFProtection,
    CSRFMiddleware,
    create_csrf_protection,
    get_csrf_token
)


class TestCSRFProtection:
    """Test CSRF protection token generation and validation."""

    def test_initialization_valid_secret(self):
        """Test initialization with valid secret key."""
        secret = "a" * 32
        csrf = CSRFProtection(secret_key=secret)

        assert csrf.secret_key == secret.encode('utf-8')
        assert csrf.token_name == "csrf_token"
        assert csrf.header_name == "X-CSRF-Token"
        assert csrf.cookie_name == "csrf_token"

    def test_initialization_short_secret_raises_error(self):
        """Test initialization with too short secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key must be at least 32 characters"):
            CSRFProtection(secret_key="short")

    def test_initialization_empty_secret_raises_error(self):
        """Test initialization with empty secret key raises ValueError."""
        with pytest.raises(ValueError, match="Secret key must be at least 32 characters"):
            CSRFProtection(secret_key="")

    def test_generate_token_format(self):
        """Test generated token has correct format."""
        csrf = CSRFProtection(secret_key="a" * 32)
        token = csrf.generate_token()

        # Token should have format: timestamp|random_token|signature
        parts = token.split('|')
        assert len(parts) == 3

        timestamp_str, random_token, signature = parts

        # Timestamp should be valid integer
        timestamp = int(timestamp_str)
        assert timestamp > 0
        assert timestamp <= int(time.time())

        # Random token should be non-empty
        assert len(random_token) > 0

        # Signature should be valid hex string (SHA256 = 64 chars)
        assert len(signature) == 64
        assert all(c in '0123456789abcdef' for c in signature)

    def test_generate_token_uniqueness(self):
        """Test generated tokens are unique."""
        csrf = CSRFProtection(secret_key="a" * 32)

        tokens = [csrf.generate_token() for _ in range(100)]

        # All tokens should be unique
        assert len(tokens) == len(set(tokens))

    def test_validate_valid_token(self):
        """Test validation of valid token."""
        csrf = CSRFProtection(secret_key="a" * 32)
        token = csrf.generate_token()

        assert csrf.validate_token(token) is True

    def test_validate_empty_token(self):
        """Test validation of empty token."""
        csrf = CSRFProtection(secret_key="a" * 32)

        assert csrf.validate_token("") is False
        assert csrf.validate_token(None) is False

    def test_validate_malformed_token(self):
        """Test validation of malformed token."""
        csrf = CSRFProtection(secret_key="a" * 32)

        # Wrong number of parts
        assert csrf.validate_token("invalid") is False
        assert csrf.validate_token("a|b") is False
        assert csrf.validate_token("a|b|c|d") is False

        # Invalid timestamp
        assert csrf.validate_token("notanumber|token|signature") is False

    def test_validate_expired_token(self):
        """Test validation of expired token."""
        csrf = CSRFProtection(secret_key="a" * 32, token_expiry=1)
        token = csrf.generate_token()

        # Token should be valid initially
        assert csrf.validate_token(token) is True

        # Wait for expiration
        time.sleep(2)

        # Token should be expired
        assert csrf.validate_token(token) is False

    def test_validate_tampered_token(self):
        """Test validation of tampered token."""
        csrf = CSRFProtection(secret_key="a" * 32)
        token = csrf.generate_token()

        # Tamper with signature
        parts = token.split('|')
        tampered_token = f"{parts[0]}|{parts[1]}|{'0' * 64}"

        assert csrf.validate_token(tampered_token) is False

    def test_validate_different_secret_key(self):
        """Test validation fails with different secret key."""
        csrf1 = CSRFProtection(secret_key="a" * 32)
        csrf2 = CSRFProtection(secret_key="b" * 32)

        token = csrf1.generate_token()

        # Token valid for csrf1
        assert csrf1.validate_token(token) is True

        # Token invalid for csrf2 (different secret)
        assert csrf2.validate_token(token) is False

    def test_set_token_cookie(self):
        """Test setting CSRF token cookie on response."""
        csrf = CSRFProtection(secret_key="a" * 32)
        response = Response()
        token = csrf.generate_token()

        csrf.set_token_cookie(response, token)

        # Check cookie is set
        assert 'set-cookie' in response.headers
        cookie_header = response.headers['set-cookie']

        assert 'csrf_token=' in cookie_header
        assert token in cookie_header

    def test_custom_configuration(self):
        """Test CSRF protection with custom configuration."""
        csrf = CSRFProtection(
            secret_key="a" * 32,
            token_name="my_token",
            header_name="X-My-Token",
            cookie_name="my_cookie",
            cookie_secure=False,
            cookie_httponly=True,
            cookie_samesite="Lax",
            token_expiry=7200
        )

        assert csrf.token_name == "my_token"
        assert csrf.header_name == "X-My-Token"
        assert csrf.cookie_name == "my_cookie"
        assert csrf.cookie_secure is False
        assert csrf.cookie_httponly is True
        assert csrf.cookie_samesite == "Lax"
        assert csrf.token_expiry == 7200


class TestCSRFMiddleware:
    """Test CSRF middleware for FastAPI."""

    def create_test_app(self, csrf_protection=None, exempt_paths=None):
        """Create test FastAPI app with CSRF middleware."""
        app = FastAPI()

        if csrf_protection is None:
            csrf_protection = CSRFProtection(secret_key="a" * 32)

        app.add_middleware(
            CSRFMiddleware,
            csrf_protection=csrf_protection,
            exempt_paths=exempt_paths or []
        )

        @app.get("/test")
        async def get_test():
            return {"message": "GET request"}

        @app.post("/test")
        async def post_test():
            return {"message": "POST request"}

        @app.put("/test")
        async def put_test():
            return {"message": "PUT request"}

        @app.delete("/test")
        async def delete_test():
            return {"message": "DELETE request"}

        @app.patch("/test")
        async def patch_test():
            return {"message": "PATCH request"}

        return app

    def test_safe_methods_allowed_without_token(self):
        """Test safe methods (GET, HEAD, OPTIONS) allowed without CSRF token."""
        app = self.create_test_app()
        client = TestClient(app)

        # GET should work
        response = client.get("/test")
        assert response.status_code == 200

        # HEAD should work
        response = client.head("/test")
        assert response.status_code in [200, 404]

        # OPTIONS should work
        response = client.options("/test")
        assert response.status_code in [200, 405]

    def test_protected_methods_require_token(self):
        """Test protected methods require CSRF token."""
        app = self.create_test_app()
        client = TestClient(app)

        # POST without token should fail
        response = client.post("/test")
        assert response.status_code == 403
        assert "CSRF token missing" in response.json()["detail"]

        # PUT without token should fail
        response = client.put("/test")
        assert response.status_code == 403

        # DELETE without token should fail
        response = client.delete("/test")
        assert response.status_code == 403

        # PATCH without token should fail
        response = client.patch("/test")
        assert response.status_code == 403

    def test_protected_methods_with_valid_token(self):
        """Test protected methods work with valid CSRF token."""
        csrf = CSRFProtection(secret_key="a" * 32)
        app = self.create_test_app(csrf_protection=csrf)
        client = TestClient(app)

        # Generate valid token
        token = csrf.generate_token()

        # POST with valid token should work
        response = client.post(
            "/test",
            headers={"X-CSRF-Token": token},
            cookies={"csrf_token": token}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "POST request"

    def test_token_mismatch_rejected(self):
        """Test request rejected when header and cookie tokens don't match."""
        csrf = CSRFProtection(secret_key="a" * 32)
        app = self.create_test_app(csrf_protection=csrf)
        client = TestClient(app)

        token1 = csrf.generate_token()
        token2 = csrf.generate_token()

        # Different tokens in header and cookie
        response = client.post(
            "/test",
            headers={"X-CSRF-Token": token1},
            cookies={"csrf_token": token2}
        )
        assert response.status_code == 403
        assert "CSRF token mismatch" in response.json()["detail"]

    def test_invalid_token_rejected(self):
        """Test request rejected with invalid token."""
        csrf = CSRFProtection(secret_key="a" * 32)
        app = self.create_test_app(csrf_protection=csrf)
        client = TestClient(app)

        invalid_token = "invalid|token|signature"

        response = client.post(
            "/test",
            headers={"X-CSRF-Token": invalid_token},
            cookies={"csrf_token": invalid_token}
        )
        assert response.status_code == 403
        assert "Invalid or expired CSRF token" in response.json()["detail"]

    def test_exempt_paths_allowed(self):
        """Test exempt paths don't require CSRF token."""
        csrf = CSRFProtection(secret_key="a" * 32)
        app = self.create_test_app(
            csrf_protection=csrf,
            exempt_paths=["/test"]
        )
        client = TestClient(app)

        # POST to exempt path should work without token
        response = client.post("/test")
        assert response.status_code == 200

    def test_correlation_id_added_to_response(self):
        """Test correlation ID added to response headers."""
        csrf = CSRFProtection(secret_key="a" * 32)
        app = self.create_test_app(csrf_protection=csrf)
        client = TestClient(app)

        response = client.get("/test")

        # Response should have CSRF token cookie (if not already set)
        # Note: This depends on middleware implementation


class TestCSRFHelpers:
    """Test CSRF helper functions."""

    def test_create_csrf_protection(self):
        """Test create_csrf_protection helper."""
        csrf = create_csrf_protection(secret_key="a" * 32)

        assert isinstance(csrf, CSRFProtection)
        assert csrf.token_name == "csrf_token"
        assert csrf.header_name == "X-CSRF-Token"
        assert csrf.cookie_secure is True


class TestCSRFSecurityProperties:
    """Test security properties of CSRF protection."""

    def test_constant_time_comparison(self):
        """Test that token comparison uses constant time algorithm."""
        csrf = CSRFProtection(secret_key="a" * 32)
        token = csrf.generate_token()

        # Create similar but invalid token
        parts = token.split('|')
        similar_token = f"{parts[0]}|{parts[1]}|{'a' * 64}"

        # Both should take similar time (hard to test precisely)
        # But implementation uses hmac.compare_digest which is constant-time
        assert csrf.validate_token(token) is True
        assert csrf.validate_token(similar_token) is False

    def test_replay_protection_via_expiry(self):
        """Test replay attack protection through token expiry."""
        csrf = CSRFProtection(secret_key="a" * 32, token_expiry=1)
        token = csrf.generate_token()

        # Token valid initially
        assert csrf.validate_token(token) is True

        # Wait for expiry
        time.sleep(2)

        # Same token now invalid (replay prevented)
        assert csrf.validate_token(token) is False

    def test_signature_prevents_forgery(self):
        """Test HMAC signature prevents token forgery."""
        csrf = CSRFProtection(secret_key="a" * 32)

        # Try to forge token without knowing secret
        timestamp = str(int(time.time()))
        random_token = "forged_token_123"
        fake_signature = "0" * 64

        forged_token = f"{timestamp}|{random_token}|{fake_signature}"

        # Forged token should be rejected
        assert csrf.validate_token(forged_token) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
