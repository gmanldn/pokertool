#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input Validation and Sanitization Library
==========================================

Provides validators and sanitizers for all user inputs to prevent:
- Path traversal attacks
- SQL injection
- XSS (Cross-Site Scripting)
- Command injection
- Prototype pollution
- LDAP injection

Usage:
    from pokertool.input_validator import (
        sanitize_input,
        validate_file_path,
        validate_player_name,
        validate_api_parameter
    )

    # Sanitize general input
    clean_input = sanitize_input(user_input, max_length=100)

    # Validate file path
    safe_path = validate_file_path(file_path, base_dir="/app/data")

    # Validate player name
    player = validate_player_name(name)
"""

from __future__ import annotations

import re
import html
import unicodedata
from pathlib import Path
from typing import Optional, List, Any
from urllib.parse import quote, unquote


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


# Security patterns
DANGEROUS_PATTERNS = [
    r'<script',  # XSS
    r'javascript:',  # XSS
    r'on\w+\s*=',  # Event handlers
    r'\.\./',  # Path traversal
    r'\.\.\\',  # Path traversal (Windows)
    r'\.\.',  # Path traversal
    r'[;<>&|`$]',  # Command injection
    r'union.*select',  # SQL injection
    r'drop\s+table',  # SQL injection
    r'exec\(',  # Code injection
    r'eval\(',  # Code injection
    r'__proto__',  # Prototype pollution
    r'constructor',  # Prototype pollution
]

DANGEROUS_REGEX = re.compile('|'.join(DANGEROUS_PATTERNS), re.IGNORECASE)


def sanitize_input(
    value: str,
    *,
    max_length: int = 1000,
    allow_html: bool = False,
    strip: bool = True
) -> str:
    """
    Sanitize general user input.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        strip: Whether to strip whitespace

    Returns:
        Sanitized string

    Raises:
        ValidationError: If input is invalid or dangerous
    """
    if not isinstance(value, str):
        value = str(value)

    # Strip whitespace
    if strip:
        value = value.strip()

    # Check length
    if len(value) > max_length:
        raise ValidationError(f"Input too long: {len(value)} > {max_length}")

    # Check for dangerous patterns
    if DANGEROUS_REGEX.search(value):
        raise ValidationError("Input contains potentially dangerous patterns")

    # HTML escape if not allowing HTML
    if not allow_html:
        value = html.escape(value)

    # Normalize unicode
    value = unicodedata.normalize('NFKC', value)

    return value


def validate_file_path(
    file_path: str,
    *,
    base_dir: Optional[str] = None,
    must_exist: bool = False,
    allowed_extensions: Optional[List[str]] = None
) -> Path:
    """
    Validate and sanitize file paths to prevent path traversal.

    Args:
        file_path: File path to validate
        base_dir: Base directory (paths must be within this)
        must_exist: Whether file must already exist
        allowed_extensions: List of allowed file extensions (e.g., ['.txt', '.json'])

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path is invalid or dangerous
    """
    # Convert to Path
    try:
        path = Path(file_path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(f"Invalid file path: {e}")

    # Check for path traversal
    if '..' in file_path or '~' in file_path:
        raise ValidationError("Path traversal detected")

    # Check base directory
    if base_dir:
        base = Path(base_dir).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            raise ValidationError(f"Path must be within {base_dir}")

    # Check existence
    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {file_path}")

    # Check extension
    if allowed_extensions and path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
        raise ValidationError(f"File extension not allowed: {path.suffix}")

    return path


def validate_player_name(name: str, *, max_length: int = 50) -> str:
    """
    Validate player name.

    Args:
        name: Player name to validate
        max_length: Maximum name length

    Returns:
        Validated name

    Raises:
        ValidationError: If name is invalid
    """
    # Sanitize
    name = sanitize_input(name, max_length=max_length, allow_html=False)

    # Check format (alphanumeric, spaces, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
        raise ValidationError("Player name contains invalid characters")

    # Check minimum length
    if len(name) < 2:
        raise ValidationError("Player name too short (minimum 2 characters)")

    return name


def validate_api_parameter(
    param: Any,
    param_type: type,
    *,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    allowed_values: Optional[List[Any]] = None
) -> Any:
    """
    Validate API request parameters.

    Args:
        param: Parameter value
        param_type: Expected type
        min_value: Minimum value (for numeric types)
        max_value: Maximum value (for numeric types)
        allowed_values: List of allowed values

    Returns:
        Validated parameter

    Raises:
        ValidationError: If parameter is invalid
    """
    # Type check
    if not isinstance(param, param_type):
        try:
            param = param_type(param)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid parameter type: expected {param_type.__name__}, got {type(param).__name__}")

    # Range check for numeric types
    if isinstance(param, (int, float)):
        if min_value is not None and param < min_value:
            raise ValidationError(f"Parameter value {param} < minimum {min_value}")
        if max_value is not None and param > max_value:
            raise ValidationError(f"Parameter value {param} > maximum {max_value}")

    # Allowed values check
    if allowed_values is not None and param not in allowed_values:
        raise ValidationError(f"Parameter value {param} not in allowed values: {allowed_values}")

    return param


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifiers (table names, column names).
    Use this for dynamic SQL construction.

    Args:
        identifier: SQL identifier to sanitize

    Returns:
        Sanitized identifier

    Raises:
        ValidationError: If identifier is invalid
    """
    # Only allow alphanumeric and underscores
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValidationError(f"Invalid SQL identifier: {identifier}")

    # Check length
    if len(identifier) > 64:
        raise ValidationError(f"SQL identifier too long: {len(identifier)}")

    # Check for SQL keywords (basic list)
    sql_keywords = {
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'table', 'from', 'where', 'join', 'union', 'exec', 'execute'
    }
    if identifier.lower() in sql_keywords:
        raise ValidationError(f"SQL identifier is a reserved keyword: {identifier}")

    return identifier


def sanitize_url(url: str, *, allowed_schemes: List[str] = None) -> str:
    """
    Sanitize URL to prevent SSRF and other attacks.

    Args:
        url: URL to sanitize
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

    Returns:
        Sanitized URL

    Raises:
        ValidationError: If URL is invalid or dangerous
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    # Check for dangerous patterns
    if DANGEROUS_REGEX.search(url):
        raise ValidationError("URL contains dangerous patterns")

    # Parse scheme
    if '://' not in url:
        raise ValidationError("URL missing scheme")

    scheme = url.split('://')[0].lower()
    if scheme not in allowed_schemes:
        raise ValidationError(f"URL scheme '{scheme}' not allowed")

    # Check for localhost/internal IPs (prevent SSRF)
    dangerous_hosts = [
        'localhost', '127.0.0.1', '0.0.0.0', '[::]',
        '169.254.', '10.', '172.16.', '192.168.'
    ]
    for host in dangerous_hosts:
        if host in url.lower():
            raise ValidationError("URL points to internal/local resource")

    # URL encode
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        # Reconstruct with proper encoding
        sanitized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            quote(unquote(parsed.path)),
            parsed.params,
            quote(unquote(parsed.query), safe='&='),
            quote(unquote(parsed.fragment))
        ))
        return sanitized
    except Exception as e:
        raise ValidationError(f"Invalid URL: {e}")


def validate_card(card: str) -> str:
    """
    Validate poker card notation.

    Args:
        card: Card string (e.g., 'As', 'Kh', '2d')

    Returns:
        Validated card string

    Raises:
        ValidationError: If card format is invalid
    """
    # Valid ranks and suits
    valid_ranks = set('23456789TJQKA')
    valid_suits = set('shdc')  # spades, hearts, diamonds, clubs

    card = card.strip()

    # Check format
    if len(card) != 2:
        raise ValidationError(f"Invalid card format: {card} (expected 2 characters)")

    rank, suit = card[0].upper(), card[1].lower()

    if rank not in valid_ranks:
        raise ValidationError(f"Invalid card rank: {rank}")

    if suit not in valid_suits:
        raise ValidationError(f"Invalid card suit: {suit}")

    return f"{rank}{suit}"


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Validated email

    Raises:
        ValidationError: If email format is invalid
    """
    # Basic email regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    email = email.strip().lower()

    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email format: {email}")

    if len(email) > 254:  # RFC 5321
        raise ValidationError("Email address too long")

    return email


# Convenience functions for common validations
def is_safe_string(value: str) -> bool:
    """Check if string is safe (no dangerous patterns)."""
    try:
        sanitize_input(value)
        return True
    except ValidationError:
        return False


def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
    """Check if file path is safe."""
    try:
        validate_file_path(path, base_dir=base_dir)
        return True
    except ValidationError:
        return False
