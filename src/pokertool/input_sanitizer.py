#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Input Sanitization Module
=========================

Comprehensive input sanitization and validation to prevent XSS, SQL injection,
and other security vulnerabilities.

Module: pokertool.input_sanitizer
Version: 1.0.0
"""

import re
import html
from typing import Any, Optional, Union, List, Dict
from enum import Enum


class SanitizationLevel(Enum):
    """Sanitization strictness levels"""
    BASIC = "basic"           # Remove only dangerous characters
    MODERATE = "moderate"     # HTML entity encoding
    STRICT = "strict"         # Remove all special characters
    PARANOID = "paranoid"     # Allow only alphanumeric


class InputSanitizer:
    """
    Comprehensive input sanitization for security
    """

    # Dangerous patterns to remove/escape
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
    ]

    # SQL injection patterns
    SQL_PATTERNS = [
        r"('\s*(or|and)\s*'?\d+'\s*=\s*'?\d+)",
        r"('\s*(or|and)\s*true\s*)",
        r"('\s*or\s*'1'\s*=\s*'1)",
        r"(;\s*(drop|delete|insert|update|create)\s+)",
        r"(union\s+select)",
        r"(exec\s*\()",
    ]

    @staticmethod
    def sanitize_string(
        value: str,
        level: SanitizationLevel = SanitizationLevel.MODERATE,
        max_length: Optional[int] = None
    ) -> str:
        """
        Sanitize string input

        Args:
            value: Input string to sanitize
            level: Sanitization strictness level
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]

        # Remove null bytes
        value = value.replace('\x00', '')

        if level == SanitizationLevel.PARANOID:
            # Only allow alphanumeric and spaces
            value = re.sub(r'[^a-zA-Z0-9\s]', '', value)

        elif level == SanitizationLevel.STRICT:
            # Remove all HTML tags and special chars
            value = re.sub(r'<[^>]+>', '', value)
            value = re.sub(r'[<>"\']', '', value)

        elif level == SanitizationLevel.MODERATE:
            # HTML entity encoding
            value = html.escape(value)

        elif level == SanitizationLevel.BASIC:
            # Remove only XSS patterns
            for pattern in InputSanitizer.XSS_PATTERNS:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE)

        # Always remove SQL injection patterns
        for pattern in InputSanitizer.SQL_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)

        return value.strip()

    @staticmethod
    def sanitize_dict(
        data: Dict[str, Any],
        level: SanitizationLevel = SanitizationLevel.MODERATE
    ) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values

        Args:
            data: Dictionary to sanitize
            level: Sanitization level

        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            # Sanitize keys too
            safe_key = InputSanitizer.sanitize_string(key, level)

            if isinstance(value, str):
                sanitized[safe_key] = InputSanitizer.sanitize_string(value, level)
            elif isinstance(value, dict):
                sanitized[safe_key] = InputSanitizer.sanitize_dict(value, level)
            elif isinstance(value, list):
                sanitized[safe_key] = InputSanitizer.sanitize_list(value, level)
            else:
                # Numbers, booleans, None - pass through
                sanitized[safe_key] = value

        return sanitized

    @staticmethod
    def sanitize_list(
        data: List[Any],
        level: SanitizationLevel = SanitizationLevel.MODERATE
    ) -> List[Any]:
        """
        Sanitize list of values

        Args:
            data: List to sanitize
            level: Sanitization level

        Returns:
            Sanitized list
        """
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(InputSanitizer.sanitize_string(item, level))
            elif isinstance(item, dict):
                sanitized.append(InputSanitizer.sanitize_dict(item, level))
            elif isinstance(item, list):
                sanitized.append(InputSanitizer.sanitize_list(item, level))
            else:
                sanitized.append(item)

        return sanitized

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username (alphanumeric, underscore, dash)"""
        pattern = r'^[a-zA-Z0-9_-]{3,20}$'
        return bool(re.match(pattern, username))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')

        # Remove parent directory references
        filename = filename.replace('..', '')

        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')

        return filename

    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL to prevent XSS via javascript: protocol

        Args:
            url: URL to sanitize

        Returns:
            Safe URL or empty string if dangerous
        """
        url = url.strip()

        # Disallow dangerous protocols
        dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return ''

        # Allow only http(s) and relative URLs
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
            return ''

        return html.escape(url)

    @staticmethod
    def sanitize_poker_hand(hand: str) -> str:
        """
        Sanitize poker hand notation (specific to poker context)

        Args:
            hand: Poker hand string (e.g., "AhKs")

        Returns:
            Sanitized hand notation
        """
        # Allow only valid poker notation
        # Ranks: A, K, Q, J, T, 9-2
        # Suits: h, d, c, s
        pattern = r'^[AKQJT98765432]{1,2}[hdcs]{1,2}$'

        if re.match(pattern, hand.upper()):
            return hand.upper()
        else:
            return ''

    @staticmethod
    def sanitize_numeric(
        value: Union[str, int, float],
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> Optional[float]:
        """
        Sanitize and validate numeric input

        Args:
            value: Numeric value
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Sanitized numeric value or None if invalid
        """
        try:
            num = float(value)

            if min_val is not None and num < min_val:
                return min_val
            if max_val is not None and num > max_val:
                return max_val

            return num
        except (ValueError, TypeError):
            return None


# Convenience functions
def sanitize(value: Any, level: SanitizationLevel = SanitizationLevel.MODERATE) -> Any:
    """Convenience function for sanitization"""
    if isinstance(value, str):
        return InputSanitizer.sanitize_string(value, level)
    elif isinstance(value, dict):
        return InputSanitizer.sanitize_dict(value, level)
    elif isinstance(value, list):
        return InputSanitizer.sanitize_list(value, level)
    else:
        return value


def sanitize_basic(value: str) -> str:
    """Quick basic sanitization"""
    return InputSanitizer.sanitize_string(value, SanitizationLevel.BASIC)


def sanitize_strict(value: str) -> str:
    """Strict sanitization"""
    return InputSanitizer.sanitize_string(value, SanitizationLevel.STRICT)
