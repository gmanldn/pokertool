"""Tests for MasterLogger exception() method."""

import sys
import pytest
from src.pokertool.master_logging import MasterLogger, LogLevel
from src.pokertool.modules.logger import MasterLogger as FallbackLogger


class TestMasterLoggerException:
    """Test MasterLogger.exception() method."""

    def test_exception_method_exists(self):
        """Test that exception() method exists on MasterLogger."""
        logger = MasterLogger.get_instance()
        assert hasattr(logger, 'exception')
        assert callable(logger.exception)

    def test_exception_captures_current_exception(self):
        """Test that exception() captures current exception info."""
        logger = MasterLogger.get_instance()

        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should not raise
            logger.exception("An error occurred")

    def test_exception_with_no_active_exception(self):
        """Test exception() handles case with no active exception."""
        logger = MasterLogger.get_instance()

        # Should not raise even when no exception is active
        logger.exception("No exception context")

    def test_exception_with_message(self):
        """Test exception() logs with provided message."""
        logger = MasterLogger.get_instance()

        try:
            raise RuntimeError("Test runtime error")
        except RuntimeError:
            logger.exception("Caught runtime error")

    def test_exception_accepts_kwargs(self):
        """Test exception() accepts additional kwargs."""
        logger = MasterLogger.get_instance()

        try:
            raise KeyError("Missing key")
        except KeyError:
            logger.exception("Key error occurred", extra_info="custom_data")


class TestFallbackLoggerException:
    """Test fallback MasterLogger.exception() method."""

    def test_fallback_exception_method_exists(self):
        """Test that exception() method exists on fallback logger."""
        logger = FallbackLogger()
        assert hasattr(logger, 'exception')
        assert callable(logger.exception)

    def test_fallback_exception_captures_current_exception(self):
        """Test that fallback exception() captures current exception info."""
        logger = FallbackLogger()

        try:
            raise ValueError("Test exception")
        except ValueError:
            # Should not raise
            logger.exception("An error occurred")

    def test_fallback_exception_with_no_active_exception(self):
        """Test fallback exception() handles case with no active exception."""
        logger = FallbackLogger()

        # Should not raise even when no exception is active
        logger.exception("No exception context")

    def test_fallback_exception_accepts_kwargs(self):
        """Test fallback exception() accepts additional kwargs."""
        logger = FallbackLogger()

        try:
            raise TypeError("Type error")
        except TypeError:
            logger.exception("Caught type error", extra="data")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
