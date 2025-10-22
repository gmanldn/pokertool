#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crash Reporter Module
=====================

Collects crash dumps and prompts user to submit crash reports.
Privacy-preserving: Only collects stack traces, logs, and system info.

Usage:
    from pokertool.crash_reporter import CrashReporter, report_crash

    # Auto-report on uncaught exceptions
    reporter = CrashReporter()
    reporter.install_handler()

    # Manual crash reporting
    try:
        risky_operation()
    except Exception as e:
        report_crash(e)

Module: pokertool.crash_reporter
Version: 1.0.0
Last Modified: 2025-10-22
"""

import sys
import os
import traceback
import platform
import datetime
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class CrashReporter:
    """
    Collects and reports application crashes.

    Features:
    - Automatic crash detection
    - Stack trace collection
    - System information gathering
    - Privacy-preserving (no user data)
    - Optional user-submitted reports
    """

    def __init__(self, app_name: str = "PokerTool", crash_dir: Optional[Path] = None):
        """
        Initialize crash reporter.

        Args:
            app_name: Application name for crash reports
            crash_dir: Directory to store crash dumps (default: temp dir)
        """
        self.app_name = app_name
        self.crash_dir = crash_dir or Path(tempfile.gettempdir()) / "pokertool_crashes"
        self.crash_dir.mkdir(parents=True, exist_ok=True)

        self._original_excepthook = None

    def install_handler(self) -> None:
        """Install global exception handler for uncaught exceptions."""
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._handle_exception

        logger.info(f"Crash reporter installed (crash dir: {self.crash_dir})")

    def uninstall_handler(self) -> None:
        """Restore original exception handler."""
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook
            logger.info("Crash reporter uninstalled")

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exception."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't report keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Collect crash data
        crash_data = self.collect_crash_data(exc_value, exc_traceback)

        # Save crash dump
        crash_file = self.save_crash_dump(crash_data)

        # Log crash
        logger.critical(f"CRASH DETECTED: {exc_type.__name__}: {exc_value}")
        logger.critical(f"Crash dump saved to: {crash_file}")

        # Prompt user (in real implementation, show dialog)
        self._prompt_user_to_submit(crash_file)

        # Call original handler
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)

    def collect_crash_data(
        self,
        exception: Exception,
        tb: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Collect crash data for reporting.

        Args:
            exception: The exception that was raised
            tb: Traceback object (optional)

        Returns:
            Dictionary with crash data
        """
        crash_data = {
            'app_name': self.app_name,
            'timestamp': datetime.datetime.now().isoformat(),
            'exception': {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': self._format_traceback(tb or exception.__traceback__),
            },
            'system': self._collect_system_info(),
            'environment': self._collect_environment_info(),
        }

        return crash_data

    def _format_traceback(self, tb: Any) -> List[str]:
        """Format traceback as list of strings."""
        if tb is None:
            return []

        formatted = traceback.format_tb(tb)
        return [line.strip() for line in formatted]

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information."""
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'os': {
                'name': os.name,
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
            }
        }

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information (privacy-preserving)."""
        return {
            'python_executable': sys.executable,
            'python_path': sys.path[:3],  # Only first 3 paths
            'cwd': str(Path.cwd()),
            'argv': sys.argv,
        }

    def save_crash_dump(self, crash_data: Dict[str, Any]) -> Path:
        """
        Save crash dump to file.

        Args:
            crash_data: Crash data dictionary

        Returns:
            Path to saved crash dump file
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"crash_{timestamp}.json"
        crash_file = self.crash_dir / filename

        with open(crash_file, 'w') as f:
            json.dump(crash_data, f, indent=2)

        logger.info(f"Crash dump saved: {crash_file}")
        return crash_file

    def _prompt_user_to_submit(self, crash_file: Path) -> None:
        """
        Prompt user to submit crash report.

        In a real implementation, this would show a dialog.
        For now, just print to console.

        Args:
            crash_file: Path to crash dump file
        """
        print("\n" + "=" * 70)
        print("APPLICATION CRASH DETECTED")
        print("=" * 70)
        print(f"\nA crash report has been saved to:")
        print(f"  {crash_file}")
        print("\nYou can help improve PokerTool by submitting this report.")
        print("The report contains:")
        print("  ✓ Stack trace (what went wrong)")
        print("  ✓ System information (OS, Python version)")
        print("  ✓ Environment details (paths, arguments)")
        print("\nThe report does NOT contain:")
        print("  ✗ Your poker hands or statistics")
        print("  ✗ Personal information")
        print("  ✗ Login credentials")
        print("\nTo submit: email the crash dump to support@pokertool.com")
        print("=" * 70 + "\n")

    def get_recent_crashes(self, limit: int = 10) -> List[Path]:
        """
        Get list of recent crash dumps.

        Args:
            limit: Maximum number of crashes to return

        Returns:
            List of crash dump file paths (most recent first)
        """
        crash_files = sorted(
            self.crash_dir.glob("crash_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return crash_files[:limit]

    def cleanup_old_crashes(self, days: int = 30) -> int:
        """
        Delete crash dumps older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of crash dumps deleted
        """
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        deleted = 0

        for crash_file in self.crash_dir.glob("crash_*.json"):
            mtime = datetime.datetime.fromtimestamp(crash_file.stat().st_mtime)
            if mtime < cutoff:
                crash_file.unlink()
                deleted += 1
                logger.debug(f"Deleted old crash dump: {crash_file}")

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old crash dumps")

        return deleted


# Global crash reporter instance
_crash_reporter: Optional[CrashReporter] = None


def get_crash_reporter() -> CrashReporter:
    """Get global crash reporter instance."""
    global _crash_reporter
    if _crash_reporter is None:
        _crash_reporter = CrashReporter()
    return _crash_reporter


def install_crash_handler() -> None:
    """Install global crash handler."""
    reporter = get_crash_reporter()
    reporter.install_handler()


def uninstall_crash_handler() -> None:
    """Uninstall global crash handler."""
    reporter = get_crash_reporter()
    reporter.uninstall_handler()


def report_crash(exception: Exception) -> None:
    """
    Manually report a crash.

    Args:
        exception: The exception to report
    """
    reporter = get_crash_reporter()
    crash_data = reporter.collect_crash_data(exception)
    crash_file = reporter.save_crash_dump(crash_data)
    reporter._prompt_user_to_submit(crash_file)


# Example usage
if __name__ == '__main__':
    # Install crash handler
    install_crash_handler()

    # Simulate a crash
    def buggy_function():
        """Function that will crash."""
        return 1 / 0

    try:
        buggy_function()
    except Exception as e:
        report_crash(e)
        raise
