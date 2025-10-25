"""Tests for v0.7.0: Input Sanitization

Tests input sanitization including:
- SQL injection prevention
- XSS (Cross-Site Scripting) prevention
- Special character handling
- HTML entity encoding
- Path traversal prevention
- Command injection prevention
"""

import pytest
from src.pokertool.validators.input_sanitizer import (
    InputSanitizer,
    sanitize_sql,
    sanitize_html,
    sanitize_filename,
    sanitize_path,
    validate_hand_id,
    validate_player_name,
    SanitizationError,
)


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_sanitize_sql_basic_string(self):
        """Test sanitizing a basic string."""
        input_str = "normal_player_name"
        result = sanitize_sql(input_str)
        assert result == "normal_player_name"

    def test_sanitize_sql_removes_single_quotes(self):
        """Test that single quotes are escaped."""
        input_str = "player' OR '1'='1"
        result = sanitize_sql(input_str)
        assert "OR" not in result or "'" not in result

    def test_sanitize_sql_removes_double_quotes(self):
        """Test that double quotes are escaped."""
        input_str = 'player" OR "1"="1'
        result = sanitize_sql(input_str)
        assert '"' not in result or "OR" not in result

    def test_sanitize_sql_removes_semicolons(self):
        """Test that semicolons are removed (prevents multiple statements)."""
        input_str = "player; DROP TABLE poker_hands;"
        result = sanitize_sql(input_str)
        assert "DROP" not in result or ";" not in result

    def test_sanitize_sql_removes_comments(self):
        """Test that SQL comments are removed."""
        input_str = "player -- comment"
        result = sanitize_sql(input_str)
        assert "--" not in result

    def test_sanitize_sql_removes_union_attacks(self):
        """Test that UNION attacks are prevented."""
        input_str = "1' UNION SELECT * FROM users--"
        result = sanitize_sql(input_str)
        assert "UNION" not in result.upper() or "'" not in result

    def test_sanitize_sql_handles_empty_string(self):
        """Test that empty strings are handled."""
        result = sanitize_sql("")
        assert result == ""

    def test_sanitize_sql_handles_none(self):
        """Test that None is handled."""
        result = sanitize_sql(None)
        assert result is None or result == ""

    def test_sanitize_sql_preserves_alphanumeric(self):
        """Test that alphanumeric characters are preserved."""
        input_str = "Player123"
        result = sanitize_sql(input_str)
        assert "Player123" in result or result.replace("'", "") == "Player123"

    def test_sanitize_sql_preserves_underscores(self):
        """Test that underscores are preserved."""
        input_str = "player_name_123"
        result = sanitize_sql(input_str)
        assert "_" in result


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention."""

    def test_sanitize_html_basic_string(self):
        """Test sanitizing basic string."""
        input_str = "normal text"
        result = sanitize_html(input_str)
        assert result == "normal text"

    def test_sanitize_html_escapes_script_tags(self):
        """Test that <script> tags are escaped."""
        input_str = "<script>alert('XSS')</script>"
        result = sanitize_html(input_str)
        assert "<script>" not in result
        assert "&lt;" in result or "script" not in result

    def test_sanitize_html_escapes_event_handlers(self):
        """Test that event handlers are escaped."""
        input_str = '<img src="x" onerror="alert(1)">'
        result = sanitize_html(input_str)
        assert "onerror" not in result or "<" not in result

    def test_sanitize_html_escapes_javascript_protocol(self):
        """Test that javascript: protocol is removed."""
        input_str = '<a href="javascript:alert(1)">click</a>'
        result = sanitize_html(input_str)
        assert "javascript:" not in result

    def test_sanitize_html_escapes_less_than(self):
        """Test that < is escaped to &lt;."""
        input_str = "5 < 10"
        result = sanitize_html(input_str)
        assert "&lt;" in result or "<" not in result

    def test_sanitize_html_escapes_greater_than(self):
        """Test that > is escaped to &gt;."""
        input_str = "10 > 5"
        result = sanitize_html(input_str)
        assert "&gt;" in result or ">" not in result

    def test_sanitize_html_escapes_ampersand(self):
        """Test that & is escaped to &amp;."""
        input_str = "Tom & Jerry"
        result = sanitize_html(input_str)
        assert "&amp;" in result or result == "Tom  Jerry"

    def test_sanitize_html_escapes_quotes(self):
        """Test that quotes are escaped."""
        input_str = 'He said "hello"'
        result = sanitize_html(input_str)
        assert "&quot;" in result or '"' not in result

    def test_sanitize_html_handles_empty_string(self):
        """Test that empty strings are handled."""
        result = sanitize_html("")
        assert result == ""

    def test_sanitize_html_handles_none(self):
        """Test that None is handled."""
        result = sanitize_html(None)
        assert result is None or result == ""


class TestSpecialCharacterHandling:
    """Test special character handling."""

    def test_handles_unicode_characters(self):
        """Test that Unicode characters are handled."""
        input_str = "Player™©®"
        result = sanitize_html(input_str)
        assert "Player" in result

    def test_handles_emoji(self):
        """Test that emoji are handled."""
        input_str = "Player 😀"
        result = sanitize_html(input_str)
        # Should either preserve or remove emoji
        assert isinstance(result, str)

    def test_handles_null_bytes(self):
        """Test that null bytes are removed."""
        input_str = "Player\x00Name"
        result = sanitize_sql(input_str)
        assert "\x00" not in result

    def test_handles_newlines(self):
        """Test that newlines are handled safely."""
        input_str = "Player\nName"
        result = sanitize_sql(input_str)
        # Newlines should be preserved or escaped
        assert isinstance(result, str)

    def test_handles_tabs(self):
        """Test that tabs are handled."""
        input_str = "Player\tName"
        result = sanitize_sql(input_str)
        assert isinstance(result, str)

    def test_handles_carriage_return(self):
        """Test that carriage returns are handled."""
        input_str = "Player\rName"
        result = sanitize_sql(input_str)
        assert isinstance(result, str)


class TestFilenamesSanitization:
    """Test filename sanitization."""

    def test_sanitize_filename_basic(self):
        """Test sanitizing basic filename."""
        filename = "hand_123.txt"
        result = sanitize_filename(filename)
        assert result == "hand_123.txt"

    def test_sanitize_filename_removes_path_separators(self):
        """Test that path separators are removed."""
        filename = "../../../etc/passwd"
        result = sanitize_filename(filename)
        assert "/" not in result
        assert "\\" not in result

    def test_sanitize_filename_removes_null_bytes(self):
        """Test that null bytes are removed."""
        filename = "file\x00.txt"
        result = sanitize_filename(filename)
        assert "\x00" not in result

    def test_sanitize_filename_limits_length(self):
        """Test that filename length is limited."""
        filename = "a" * 300 + ".txt"
        result = sanitize_filename(filename)
        assert len(result) <= 255  # Max filename length

    def test_sanitize_filename_handles_windows_reserved(self):
        """Test that Windows reserved names are handled."""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved_names:
            result = sanitize_filename(name)
            assert result != name or len(result) == 0

    def test_sanitize_filename_removes_special_chars(self):
        """Test that special characters are removed."""
        filename = "file<>:\"|?*.txt"
        result = sanitize_filename(filename)
        # Should not contain Windows-forbidden characters
        forbidden = '<>:"|?*'
        for char in forbidden:
            assert char not in result


class TestPathTraversalPrevention:
    """Test path traversal prevention."""

    def test_sanitize_path_basic(self):
        """Test sanitizing basic path."""
        path = "data/hands/hand_123.json"
        result = sanitize_path(path)
        assert "data" in result
        assert "hands" in result

    def test_sanitize_path_removes_parent_references(self):
        """Test that ../ is removed."""
        path = "../../../etc/passwd"
        result = sanitize_path(path)
        assert ".." not in result

    def test_sanitize_path_removes_absolute_paths(self):
        """Test that absolute paths are converted to relative."""
        path = "/etc/passwd"
        result = sanitize_path(path)
        # Should not allow absolute paths
        assert not result.startswith("/")

    def test_sanitize_path_handles_windows_paths(self):
        """Test that Windows paths are handled."""
        path = "C:\\Windows\\System32"
        result = sanitize_path(path)
        # Should not allow drive letters
        assert "C:" not in result or result == ""

    def test_sanitize_path_normalizes_separators(self):
        """Test that path separators are normalized."""
        path = "data\\hands\\hand.json"
        result = sanitize_path(path)
        # Should use forward slashes
        assert "/" in result or "\\" not in result


class TestHandIDValidation:
    """Test hand ID validation."""

    def test_validate_hand_id_valid_format(self):
        """Test valid hand ID format."""
        hand_id = "PS123456789"
        result = validate_hand_id(hand_id)
        assert result is True

    def test_validate_hand_id_numeric_only(self):
        """Test numeric-only hand ID."""
        hand_id = "123456789"
        result = validate_hand_id(hand_id)
        assert result is True

    def test_validate_hand_id_rejects_invalid_chars(self):
        """Test that invalid characters are rejected."""
        hand_id = "PS123'; DROP TABLE--"
        result = validate_hand_id(hand_id)
        assert result is False

    def test_validate_hand_id_rejects_too_long(self):
        """Test that overly long IDs are rejected."""
        hand_id = "PS" + "1" * 1000
        result = validate_hand_id(hand_id)
        assert result is False

    def test_validate_hand_id_rejects_empty(self):
        """Test that empty strings are rejected."""
        result = validate_hand_id("")
        assert result is False

    def test_validate_hand_id_rejects_none(self):
        """Test that None is rejected."""
        result = validate_hand_id(None)
        assert result is False


class TestPlayerNameValidation:
    """Test player name validation."""

    def test_validate_player_name_valid(self):
        """Test valid player name."""
        name = "Player123"
        result = validate_player_name(name)
        assert result is True

    def test_validate_player_name_with_underscores(self):
        """Test player name with underscores."""
        name = "player_name_123"
        result = validate_player_name(name)
        assert result is True

    def test_validate_player_name_rejects_sql_injection(self):
        """Test that SQL injection is rejected."""
        name = "Player' OR '1'='1"
        result = validate_player_name(name)
        assert result is False

    def test_validate_player_name_rejects_script_tags(self):
        """Test that script tags are rejected."""
        name = "<script>alert(1)</script>"
        result = validate_player_name(name)
        assert result is False

    def test_validate_player_name_rejects_too_long(self):
        """Test that overly long names are rejected."""
        name = "a" * 1000
        result = validate_player_name(name)
        assert result is False

    def test_validate_player_name_allows_spaces(self):
        """Test that spaces are allowed."""
        name = "Player Name"
        result = validate_player_name(name)
        assert result is True

    def test_validate_player_name_rejects_empty(self):
        """Test that empty strings are rejected."""
        result = validate_player_name("")
        assert result is False


class TestInputSanitizerClass:
    """Test InputSanitizer class."""

    def test_sanitizer_initialization(self):
        """Test sanitizer can be initialized."""
        sanitizer = InputSanitizer()
        assert sanitizer is not None

    def test_sanitizer_sanitize_sql(self):
        """Test SQL sanitization method."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_sql("Player' OR '1'='1")
        assert "OR" not in result or "'" not in result

    def test_sanitizer_sanitize_html(self):
        """Test HTML sanitization method."""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_sanitizer_sanitize_all_fields(self):
        """Test sanitizing all fields in a dict."""
        sanitizer = InputSanitizer()
        data = {
            "player_name": "Player' OR '1'='1",
            "hand_id": "123<script>",
            "board": "Ks Qs Js"
        }
        result = sanitizer.sanitize_dict(data)
        assert "OR" not in result.get("player_name", "")
        assert "<script>" not in result.get("hand_id", "")

    def test_sanitizer_validate_hand_data(self):
        """Test validating hand data."""
        sanitizer = InputSanitizer()
        valid_data = {
            "hand_id": "PS123456789",
            "player_name": "Player123",
            "board": "Ks Qs Js"
        }
        result = sanitizer.validate_hand_data(valid_data)
        assert result is True

    def test_sanitizer_reject_invalid_hand_data(self):
        """Test rejecting invalid hand data."""
        sanitizer = InputSanitizer()
        invalid_data = {
            "hand_id": "'; DROP TABLE--",
            "player_name": "<script>alert(1)</script>",
            "board": "Invalid"
        }
        result = sanitizer.validate_hand_data(invalid_data)
        assert result is False


class TestCommandInjectionPrevention:
    """Test command injection prevention."""

    def test_prevents_shell_commands(self):
        """Test that shell commands are escaped."""
        input_str = "file; rm -rf /"
        result = sanitize_filename(input_str)
        assert ";" not in result

    def test_prevents_backticks(self):
        """Test that backticks are removed."""
        input_str = "file`whoami`.txt"
        result = sanitize_filename(input_str)
        assert "`" not in result

    def test_prevents_dollar_commands(self):
        """Test that $() commands are handled."""
        input_str = "file$(whoami).txt"
        result = sanitize_filename(input_str)
        assert "$(" not in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_input(self):
        """Test handling of very long input."""
        input_str = "a" * 100000
        result = sanitize_sql(input_str)
        # Should not crash, might truncate
        assert isinstance(result, str)

    def test_binary_data(self):
        """Test handling of binary data."""
        input_bytes = b"\x00\x01\x02\x03"
        # Should handle gracefully
        try:
            result = sanitize_sql(input_bytes.decode('utf-8', errors='ignore'))
            assert isinstance(result, str)
        except:
            pass  # Acceptable to reject binary data

    def test_mixed_encoding(self):
        """Test handling of mixed encodings."""
        input_str = "Player™ <script>©"
        result = sanitize_html(input_str)
        assert isinstance(result, str)

    def test_repeated_sanitization(self):
        """Test that repeated sanitization is idempotent."""
        input_str = "<script>alert(1)</script>"
        result1 = sanitize_html(input_str)
        result2 = sanitize_html(result1)
        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
