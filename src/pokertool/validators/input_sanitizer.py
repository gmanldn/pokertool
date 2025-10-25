"""Input Sanitization Module (v0.7.0)

Provides comprehensive input sanitization to prevent:
- SQL injection attacks
- XSS (Cross-Site Scripting) attacks
- Path traversal attacks
- Command injection attacks
- Special character exploits
"""

import re
import html
from typing import Any, Dict, Optional
from pathlib import Path


class SanitizationError(Exception):
    """Exception raised when sanitization fails."""
    pass


# SQL Injection Prevention
SQL_DANGEROUS_PATTERNS = [
    r"(\b(OR|AND)\b.*['\"].*=.*['\"])",  # OR '1'='1'
    r"(;.*DROP)",  # ; DROP TABLE
    r"(;.*DELETE)",  # ; DELETE FROM
    r"(;.*UPDATE)",  # ; UPDATE
    r"(;.*INSERT)",  # ; INSERT INTO
    r"(UNION.*SELECT)",  # UNION SELECT
    r"(--)",  # SQL comments
    r"(/\*|\*/)",  # Block comments
]

def sanitize_sql(input_str: Optional[str]) -> Optional[str]:
    """Sanitize input to prevent SQL injection.

    Args:
        input_str: Input string to sanitize

    Returns:
        Sanitized string safe for SQL queries
    """
    if input_str is None:
        return None

    if not isinstance(input_str, str):
        input_str = str(input_str)

    if not input_str:
        return ""

    # Remove null bytes
    sanitized = input_str.replace('\x00', '')

    # Escape single quotes (double them for SQL)
    sanitized = sanitized.replace("'", "''")

    # Check for dangerous patterns
    for pattern in SQL_DANGEROUS_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            # Remove dangerous content
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    # Remove semicolons (prevent multiple statements)
    sanitized = sanitized.replace(';', '')

    # Remove SQL comments
    sanitized = re.sub(r'--.*$', '', sanitized)
    sanitized = re.sub(r'/\*.*?\*/', '', sanitized)

    return sanitized.strip()


# XSS Prevention
def sanitize_html(input_str: Optional[str]) -> Optional[str]:
    """Sanitize input to prevent XSS attacks.

    Args:
        input_str: Input string to sanitize

    Returns:
        HTML-escaped string safe for display
    """
    if input_str is None:
        return None

    if not isinstance(input_str, str):
        input_str = str(input_str)

    if not input_str:
        return ""

    # Check if already escaped (make idempotent)
    if '&lt;' in input_str or '&gt;' in input_str or '&amp;' in input_str:
        # Already escaped, don't double-escape
        sanitized = input_str
    else:
        # HTML escape
        sanitized = html.escape(input_str, quote=True)

    # Remove javascript: protocol
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)

    # Remove event handlers
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)

    return sanitized


# Filename Sanitization
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent security issues.

    Args:
        filename: Filename to sanitize

    Returns:
        Safe filename
    """
    if not filename:
        return ""

    # Remove null bytes
    sanitized = filename.replace('\x00', '')

    # Remove path separators
    sanitized = sanitized.replace('/', '').replace('\\', '')

    # Remove Windows-forbidden characters: < > : " | ? *
    forbidden_chars = '<>:"|?*'
    for char in forbidden_chars:
        sanitized = sanitized.replace(char, '')

    # Remove shell metacharacters
    sanitized = sanitized.replace(';', '').replace('`', '').replace('$', '')
    sanitized = sanitized.replace('&', '').replace('|', '').replace('>', '')

    # Check for Windows reserved names
    name_without_ext = sanitized.split('.')[0].upper()
    if name_without_ext in WINDOWS_RESERVED_NAMES:
        sanitized = '_' + sanitized

    # Limit length (max filename length is 255 bytes)
    if len(sanitized) > 255:
        # Keep extension if present
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            sanitized = name[:250] + '.' + ext
        else:
            sanitized = sanitized[:255]

    return sanitized


# Path Traversal Prevention
def sanitize_path(path: str) -> str:
    """Sanitize file path to prevent path traversal attacks.

    Args:
        path: File path to sanitize

    Returns:
        Safe relative path
    """
    if not path:
        return ""

    # Remove null bytes
    sanitized = path.replace('\x00', '')

    # Remove parent directory references
    sanitized = sanitized.replace('..', '')

    # Remove absolute path indicators
    sanitized = sanitized.lstrip('/')
    sanitized = re.sub(r'^[A-Za-z]:', '', sanitized)  # Remove Windows drive letters

    # Normalize path separators
    sanitized = sanitized.replace('\\', '/')

    # Remove multiple slashes
    sanitized = re.sub(r'/+', '/', sanitized)

    # Ensure it's a relative path
    path_obj = Path(sanitized)
    try:
        # Resolve to ensure no traversal
        resolved = path_obj.resolve()
        # Return normalized relative path
        return str(path_obj).replace('\\', '/')
    except:
        return sanitized


# Hand ID Validation
def validate_hand_id(hand_id: Optional[str]) -> bool:
    """Validate hand ID format.

    Args:
        hand_id: Hand ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not hand_id:
        return False

    if not isinstance(hand_id, str):
        return False

    # Max length check
    if len(hand_id) > 100:
        return False

    # Must be alphanumeric (allow prefixes like PS, GG, etc.)
    if not re.match(r'^[A-Za-z0-9_-]+$', hand_id):
        return False

    return True


# Player Name Validation
def validate_player_name(name: Optional[str]) -> bool:
    """Validate player name.

    Args:
        name: Player name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False

    if not isinstance(name, str):
        return False

    # Max length check
    if len(name) > 50:
        return False

    # Check for dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '&', '|', '`', '$']
    for char in dangerous_chars:
        if char in name:
            return False

    # Check for script tags
    if '<script' in name.lower():
        return False

    # Check for SQL keywords
    sql_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'UNION', 'SELECT']
    name_upper = name.upper()
    for keyword in sql_keywords:
        if keyword in name_upper:
            return False

    return True


class InputSanitizer:
    """Input sanitization class."""

    def __init__(self):
        """Initialize the sanitizer."""
        pass

    def sanitize_sql(self, input_str: str) -> str:
        """Sanitize SQL input.

        Args:
            input_str: Input to sanitize

        Returns:
            Sanitized string
        """
        return sanitize_sql(input_str) or ""

    def sanitize_html(self, input_str: str) -> str:
        """Sanitize HTML input.

        Args:
            input_str: Input to sanitize

        Returns:
            Sanitized string
        """
        return sanitize_html(input_str) or ""

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        return sanitize_filename(filename)

    def sanitize_path(self, path: str) -> str:
        """Sanitize file path.

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path
        """
        return sanitize_path(path)

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all string fields in a dictionary.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Sanitize both SQL and HTML
                sanitized[key] = self.sanitize_html(self.sanitize_sql(value))
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_html(self.sanitize_sql(item)) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def validate_hand_data(self, data: Dict[str, Any]) -> bool:
        """Validate hand data.

        Args:
            data: Hand data to validate

        Returns:
            True if valid, False otherwise
        """
        # Check hand_id
        if 'hand_id' in data:
            if not validate_hand_id(data['hand_id']):
                return False

        # Check player_name
        if 'player_name' in data:
            if not validate_player_name(data['player_name']):
                return False

        # Check board format (if present)
        if 'board' in data:
            from src.pokertool.validators.board_format_validator import validate_board_format
            if not validate_board_format(data['board']):
                return False

        return True


# Convenience functions for common use cases
def sanitize_for_database(input_str: str) -> str:
    """Sanitize input for database storage.

    Args:
        input_str: Input to sanitize

    Returns:
        Sanitized string
    """
    return sanitize_sql(input_str) or ""


def sanitize_for_display(input_str: str) -> str:
    """Sanitize input for HTML display.

    Args:
        input_str: Input to sanitize

    Returns:
        Sanitized string
    """
    return sanitize_html(input_str) or ""


def sanitize_user_input(input_str: str) -> str:
    """Sanitize general user input (both SQL and HTML).

    Args:
        input_str: Input to sanitize

    Returns:
        Sanitized string
    """
    return sanitize_html(sanitize_sql(input_str) or "") or ""
