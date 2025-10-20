#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSRF Protection Middleware
===========================

Provides Cross-Site Request Forgery (CSRF) protection for state-changing operations.

CSRF attacks trick authenticated users into performing unwanted actions on web applications.
This module implements token-based CSRF protection following OWASP best practices.

Module: pokertool.csrf_protection
Version: 1.0.0
"""

import secrets
import hmac
import hashlib
from typing import Optional, List, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time


class CSRFProtection:
    """
    CSRF protection implementation with token generation and validation.

    Features:
    - Secure token generation using secrets module
    - HMAC-based token validation
    - Configurable token expiration
    - Support for SameSite cookie attribute
    - Double-submit cookie pattern
    """

    def __init__(
        self,
        secret_key: str,
        token_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token",
        cookie_secure: bool = True,
        cookie_httponly: bool = False,  # Must be False so JS can read it
        cookie_samesite: str = "Strict",
        token_expiry: int = 3600,  # 1 hour in seconds
    ):
        """
        Initialize CSRF protection.

        Args:
            secret_key: Secret key for token generation (should be from env)
            token_name: Form field name for CSRF token
            header_name: HTTP header name for CSRF token
            cookie_name: Cookie name for CSRF token
            cookie_secure: Whether to use Secure cookie attribute
            cookie_httponly: Whether to use HttpOnly cookie attribute
            cookie_samesite: SameSite cookie attribute (Strict/Lax/None)
            token_expiry: Token expiration time in seconds
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.secret_key = secret_key.encode('utf-8')
        self.token_name = token_name
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.token_expiry = token_expiry

    def generate_token(self) -> str:
        """
        Generate a cryptographically secure CSRF token.

        Returns:
            Base64-encoded CSRF token with timestamp
        """
        # Generate random token
        random_token = secrets.token_urlsafe(32)
        timestamp = str(int(time.time()))

        # Create message: timestamp|random_token
        message = f"{timestamp}|{random_token}"

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key,
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Final token: timestamp|random_token|signature
        token = f"{timestamp}|{random_token}|{signature}"

        return token

    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.

        Args:
            token: CSRF token to validate

        Returns:
            True if valid, False otherwise
        """
        if not token:
            return False

        try:
            # Parse token
            parts = token.split('|')
            if len(parts) != 3:
                return False

            timestamp_str, random_token, provided_signature = parts
            timestamp = int(timestamp_str)

            # Check expiration
            current_time = int(time.time())
            if current_time - timestamp > self.token_expiry:
                return False

            # Recreate signature
            message = f"{timestamp_str}|{random_token}"
            expected_signature = hmac.new(
                self.secret_key,
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(provided_signature, expected_signature)

        except (ValueError, IndexError):
            return False

    def set_token_cookie(self, response: Response, token: str) -> None:
        """
        Set CSRF token cookie on response.

        Args:
            response: Response object to set cookie on
            token: CSRF token to set
        """
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=self.token_expiry,
            secure=self.cookie_secure,
            httponly=self.cookie_httponly,
            samesite=self.cookie_samesite
        )


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for CSRF protection.

    Protects state-changing operations (POST, PUT, DELETE, PATCH) with CSRF tokens.
    Safe methods (GET, HEAD, OPTIONS) are not protected.
    """

    # HTTP methods that are protected by CSRF
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    # HTTP methods that are safe and don't need CSRF protection
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(
        self,
        app: ASGIApp,
        csrf_protection: CSRFProtection,
        exempt_paths: Optional[List[str]] = None
    ):
        """
        Initialize CSRF middleware.

        Args:
            app: ASGI application
            csrf_protection: CSRFProtection instance
            exempt_paths: List of paths exempt from CSRF protection
        """
        super().__init__(app)
        self.csrf = csrf_protection
        self.exempt_paths = exempt_paths or []

    def is_path_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with CSRF protection.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response

        Raises:
            HTTPException: If CSRF validation fails
        """
        # Skip CSRF check for safe methods
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            return response

        # Skip CSRF check for exempt paths
        if self.is_path_exempt(request.url.path):
            response = await call_next(request)
            return response

        # For protected methods, validate CSRF token
        if request.method in self.PROTECTED_METHODS:
            # Get token from header
            token_from_header = request.headers.get(self.csrf.header_name)

            # Get token from cookie
            token_from_cookie = request.cookies.get(self.csrf.cookie_name)

            # Validate token (double-submit cookie pattern)
            if not token_from_header or not token_from_cookie:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token missing"
                )

            # Both tokens must match
            if not hmac.compare_digest(token_from_header, token_from_cookie):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token mismatch"
                )

            # Validate token signature and expiration
            if not self.csrf.validate_token(token_from_header):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired CSRF token"
                )

        # Process request
        response = await call_next(request)

        # Generate new token for response if needed
        if not request.cookies.get(self.csrf.cookie_name):
            new_token = self.csrf.generate_token()
            self.csrf.set_token_cookie(response, new_token)

        return response


# Dependency for routes that need CSRF token
def get_csrf_token(request: Request, csrf: CSRFProtection) -> str:
    """
    Dependency to get or generate CSRF token for route.

    Usage:
        @app.get("/form")
        def get_form(csrf_token: str = Depends(get_csrf_token)):
            return {"csrf_token": csrf_token}

    Args:
        request: Current request
        csrf: CSRFProtection instance

    Returns:
        CSRF token string
    """
    # Check if token exists in cookie
    existing_token = request.cookies.get(csrf.cookie_name)

    if existing_token and csrf.validate_token(existing_token):
        return existing_token

    # Generate new token
    return csrf.generate_token()


# Example configuration
def create_csrf_protection(secret_key: str) -> CSRFProtection:
    """
    Create configured CSRF protection instance.

    Args:
        secret_key: Secret key from environment

    Returns:
        Configured CSRFProtection instance
    """
    return CSRFProtection(
        secret_key=secret_key,
        token_name="csrf_token",
        header_name="X-CSRF-Token",
        cookie_name="csrf_token",
        cookie_secure=True,  # Set to False for development
        cookie_httponly=False,  # Must be False so JS can read it
        cookie_samesite="Strict",
        token_expiry=3600
    )
