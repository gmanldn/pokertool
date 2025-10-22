#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crash Reporter Tests
====================

Tests for crash reporting functionality.
"""

import pytest
import sys
import tempfile
import json
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from pokertool.crash_reporter import CrashReporter, get_crash_reporter, report_crash


class TestCrashReporter:
    """Tests for CrashReporter class."""

    @pytest.fixture
    def temp_crash_dir(self, tmp_path):
        """Provide temporary directory for crash dumps."""
        return tmp_path / "crashes"

    @pytest.fixture
    def reporter(self, temp_crash_dir):
        """Provide CrashReporter instance with temp directory."""
        return CrashReporter(crash_dir=temp_crash_dir)

    def test_crash_reporter_initialization(self, reporter, temp_crash_dir):
        """Test crash reporter initializes correctly."""
        assert reporter.app_name == "PokerTool"
        assert reporter.crash_dir == temp_crash_dir
        assert temp_crash_dir.exists()

    def test_collect_crash_data(self, reporter):
        """Test crash data collection."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            crash_data = reporter.collect_crash_data(e)

            assert crash_data['app_name'] == "PokerTool"
            assert 'timestamp' in crash_data
            assert crash_data['exception']['type'] == 'ValueError'
            assert crash_data['exception']['message'] == 'Test error'
            assert 'traceback' in crash_data['exception']
            assert 'system' in crash_data
            assert 'environment' in crash_data

    def test_save_crash_dump(self, reporter, temp_crash_dir):
        """Test crash dump is saved correctly."""
        crash_data = {
            'app_name': 'PokerTool',
            'timestamp': '2025-10-22T12:00:00',
            'exception': {
                'type': 'TestError',
                'message': 'Test crash',
            }
        }

        crash_file = reporter.save_crash_dump(crash_data)

        assert crash_file.exists()
        assert crash_file.parent == temp_crash_dir
        assert crash_file.name.startswith('crash_')
        assert crash_file.suffix == '.json'

        # Verify content
        with open(crash_file) as f:
            loaded_data = json.load(f)
            assert loaded_data == crash_data

    def test_install_uninstall_handler(self, reporter):
        """Test installing and uninstalling exception handler."""
        original_hook = sys.excepthook

        reporter.install_handler()
        assert sys.excepthook != original_hook

        reporter.uninstall_handler()
        assert sys.excepthook == original_hook

    def test_get_recent_crashes(self, reporter, temp_crash_dir):
        """Test getting recent crash dumps."""
        # Create some crash dumps
        for i in range(5):
            crash_data = {'crash_num': i}
            reporter.save_crash_dump(crash_data)

        recent = reporter.get_recent_crashes(limit=3)

        assert len(recent) == 3
        assert all(isinstance(p, Path) for p in recent)
        assert all(p.name.startswith('crash_') for p in recent)

    def test_cleanup_old_crashes(self, reporter, temp_crash_dir):
        """Test cleaning up old crash dumps."""
        # Create crash dumps
        for i in range(3):
            crash_data = {'crash_num': i}
            crash_file = reporter.save_crash_dump(crash_data)

            # Make one file old by modifying mtime
            if i == 0:
                import os
                import time
                old_time = time.time() - (31 * 24 * 60 * 60)  # 31 days ago
                os.utime(crash_file, (old_time, old_time))

        # Cleanup old crashes (>30 days)
        deleted = reporter.cleanup_old_crashes(days=30)

        assert deleted == 1
        remaining = list(temp_crash_dir.glob("crash_*.json"))
        assert len(remaining) == 2

    def test_manual_crash_reporting(self, reporter):
        """Test manual crash reporting."""
        try:
            raise RuntimeError("Manual crash test")
        except RuntimeError as e:
            crash_data = reporter.collect_crash_data(e)
            crash_file = reporter.save_crash_dump(crash_data)

            assert crash_file.exists()

            # Verify crash data
            with open(crash_file) as f:
                loaded = json.load(f)
                assert loaded['exception']['type'] == 'RuntimeError'
                assert loaded['exception']['message'] == 'Manual crash test'

    def test_system_info_collection(self, reporter):
        """Test system information is collected."""
        try:
            raise Exception("Test")
        except Exception as e:
            crash_data = reporter.collect_crash_data(e)

            system = crash_data['system']
            assert 'platform' in system
            assert 'python_version' in system
            assert 'machine' in system
            assert 'os' in system
            assert system['os']['name'] is not None

    def test_privacy_preserving(self, reporter):
        """Test crash reports don't contain sensitive data."""
        try:
            api_key = "SECRET_KEY_123"
            password = "mypassword"
            raise ValueError(f"Error with {api_key}")
        except ValueError as e:
            crash_data = reporter.collect_crash_data(e)

            # Convert to string to search
            crash_str = json.dumps(crash_data)

            # Should contain exception message (we can't avoid this completely)
            # but should NOT contain other sensitive patterns
            assert 'password' not in crash_str.lower()


class TestGlobalCrashReporter:
    """Tests for global crash reporter functions."""

    def test_get_crash_reporter_singleton(self):
        """Test global crash reporter is a singleton."""
        reporter1 = get_crash_reporter()
        reporter2 = get_crash_reporter()

        assert reporter1 is reporter2

    def test_report_crash_function(self, tmp_path):
        """Test report_crash convenience function."""
        # Override crash dir for test
        reporter = get_crash_reporter()
        original_dir = reporter.crash_dir
        reporter.crash_dir = tmp_path / "test_crashes"
        reporter.crash_dir.mkdir(parents=True, exist_ok=True)

        try:
            try:
                raise ValueError("Test error for reporting")
            except ValueError as e:
                report_crash(e)

            # Verify crash dump was created
            crashes = list(reporter.crash_dir.glob("crash_*.json"))
            assert len(crashes) > 0

        finally:
            # Restore original dir
            reporter.crash_dir = original_dir


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
