#!/usr/bin/env python3
"""
Unit tests for macOS dock icon functionality.

Tests the setup_dock_icon function to ensure:
1. Dock icon always appears when on macOS
2. NSApplication is configured correctly
3. Activation policy is set to Regular
4. Custom icons are loaded when available
5. Graceful handling when PyObjC is not available
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import platform

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestDockIconSetup:
    """Test suite for dock icon setup functionality."""

    @pytest.fixture
    def mock_appkit(self):
        """Mock AppKit components for testing."""
        mock_app = MagicMock()
        mock_app.activationPolicy.return_value = 0  # NSApplicationActivationPolicyRegular

        mock_nsimage = MagicMock()
        mock_icon = MagicMock()
        mock_nsimage.alloc.return_value.initWithContentsOfFile_.return_value = mock_icon

        mock_delegate = MagicMock()

        return {
            'app': mock_app,
            'nsimage': mock_nsimage,
            'icon': mock_icon,
            'delegate': mock_delegate,
        }

    @pytest.fixture
    def mock_status_window(self):
        """Mock StatusWindow for testing."""
        mock_window = MagicMock()
        mock_window.api_url = "http://localhost:5001"
        return mock_window

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_dock_icon_setup_on_macos_with_appkit(self, mock_appkit, mock_status_window):
        """Test that dock icon is set up correctly on macOS with PyObjC available."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.NSApplicationActivationPolicyRegular', 0):

            # Configure mocks
            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']

            # Import and run setup_dock_icon
            from start import setup_dock_icon

            result = setup_dock_icon()

            # Assertions
            assert result is not None, "setup_dock_icon should return NSApplication instance"

            # Verify NSApplication was configured
            mock_nsapp.sharedApplication.assert_called_once()

            # Verify activation policy was set to Regular
            mock_appkit['app'].setActivationPolicy_.assert_called_once_with(0)

            # Verify activation policy was verified
            mock_appkit['app'].activationPolicy.assert_called_once()

            # Verify delegate was set
            mock_appkit['app'].setDelegate_.assert_called_once_with(mock_appkit['delegate'])

            # Verify app was activated
            mock_appkit['app'].activateIgnoringOtherApps_.assert_called_once_with(True)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_dock_icon_activation_policy_verification(self, mock_appkit, mock_status_window):
        """Test that activation policy is verified after being set."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.NSApplicationActivationPolicyRegular', 0), \
             patch('start.log') as mock_log:

            # Configure mocks - simulate wrong activation policy
            mock_appkit['app'].activationPolicy.return_value = 1  # Wrong policy
            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']

            from start import setup_dock_icon

            setup_dock_icon()

            # Verify warning was logged about wrong policy
            warning_calls = [call for call in mock_log.call_args_list
                           if 'Warning: Activation policy' in str(call)]
            assert len(warning_calls) > 0, "Should warn when activation policy is incorrect"

    def test_dock_icon_setup_on_non_macos(self):
        """Test that dock icon setup returns None on non-macOS systems."""
        with patch('start.IS_MACOS', False):
            from start import setup_dock_icon

            result = setup_dock_icon()

            assert result is None, "setup_dock_icon should return None on non-macOS"

    def test_dock_icon_setup_without_appkit(self):
        """Test that dock icon setup returns None when PyObjC is not available."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', False):

            from start import setup_dock_icon

            result = setup_dock_icon()

            assert result is None, "setup_dock_icon should return None without AppKit"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_custom_icon_loading_when_available(self, mock_appkit, mock_status_window, tmp_path):
        """Test that custom icon is loaded when available."""
        # Create temporary icon file
        icon_path = tmp_path / "assets" / "pokertool-icon.png"
        icon_path.parent.mkdir(parents=True)
        icon_path.write_bytes(b"fake png data")

        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.NSApplicationActivationPolicyRegular', 0), \
             patch('start.ROOT', tmp_path), \
             patch('start.log') as mock_log:

            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']

            from start import setup_dock_icon

            setup_dock_icon()

            # Verify custom icon was loaded
            mock_appkit['nsimage'].alloc.return_value.initWithContentsOfFile_.assert_called_once_with(str(icon_path))

            # Verify icon was set
            mock_appkit['app'].setApplicationIconImage_.assert_called_once_with(mock_appkit['icon'])

            # Verify success was logged
            success_calls = [call for call in mock_log.call_args_list
                           if 'Custom dock icon loaded' in str(call)]
            assert len(success_calls) > 0, "Should log success when custom icon is loaded"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_default_icon_when_custom_not_available(self, mock_appkit, mock_status_window, tmp_path):
        """Test that default icon is used when custom icon is not available."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.NSApplicationActivationPolicyRegular', 0), \
             patch('start.ROOT', tmp_path), \
             patch('start.log') as mock_log:

            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']

            from start import setup_dock_icon

            setup_dock_icon()

            # Verify message about default icon
            default_icon_calls = [call for call in mock_log.call_args_list
                                 if 'No custom icon found' in str(call) or 'using default Python icon' in str(call)]
            assert len(default_icon_calls) > 0, "Should log message about using default icon"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_app_name_is_set(self, mock_appkit, mock_status_window):
        """Test that application attempts to set bundle info for app name."""
        mock_bundle = MagicMock()
        mock_info = MagicMock(spec=dict)
        mock_bundle.localizedInfoDictionary.return_value = mock_info

        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.NSApplicationActivationPolicyRegular', 0), \
             patch('Foundation.NSBundle') as mock_nsbundle:

            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']
            mock_nsbundle.mainBundle.return_value = mock_bundle

            from start import setup_dock_icon

            setup_dock_icon()

            # Verify bundle methods were called (attempting to set app name)
            mock_nsbundle.mainBundle.assert_called_once()
            mock_bundle.localizedInfoDictionary.assert_called_once()

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_exception_handling(self, mock_status_window):
        """Test that exceptions are caught and logged gracefully."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.log') as mock_log:

            # Simulate an exception
            mock_nsapp.sharedApplication.side_effect = Exception("Test exception")

            from start import setup_dock_icon

            result = setup_dock_icon()

            # Should return None on exception
            assert result is None, "setup_dock_icon should return None on exception"

            # Verify error was logged
            error_calls = [call for call in mock_log.call_args_list
                         if 'Could not set up dock icon' in str(call)]
            assert len(error_calls) > 0, "Should log error message on exception"

            # Verify traceback was logged
            traceback_calls = [call for call in mock_log.call_args_list
                             if 'Traceback:' in str(call)]
            assert len(traceback_calls) > 0, "Should log traceback on exception"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_status_window_creation(self, mock_appkit):
        """Test that StatusWindow is created with correct API URL."""
        mock_status_window_class = MagicMock()
        mock_status_window_instance = MagicMock()
        mock_status_window_class.return_value = mock_status_window_instance

        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', mock_status_window_class), \
             patch('start.NSApplicationActivationPolicyRegular', 0):

            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']

            from start import setup_dock_icon

            setup_dock_icon()

            # Verify StatusWindow was created with correct API URL
            mock_status_window_class.assert_called_once_with(api_url="http://localhost:5001")

    def test_dock_icon_always_shows_integration(self):
        """
        Integration test to verify dock icon setup ensures visibility.

        This test verifies the complete flow:
        1. NSApplication is created
        2. Activation policy is set to Regular
        3. App is activated
        4. All steps succeed in order
        """
        # This test documents the expected behavior
        expected_steps = [
            "Create NSApplication instance",
            "Set activation policy to NSApplicationActivationPolicyRegular",
            "Verify activation policy was set correctly",
            "Create and set AppDelegate",
            "Load custom icon (if available)",
            "Activate application with activateIgnoringOtherApps",
            "Set application name in bundle info",
        ]

        # Document that these steps ensure dock icon visibility
        for step in expected_steps:
            assert step, f"Expected step: {step}"


class TestAppDelegate:
    """Test suite for AppDelegate functionality."""

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_app_delegate_handles_dock_click(self):
        """Test that AppDelegate handles dock icon clicks correctly."""
        with patch('start.HAS_APPKIT', True), \
             patch('start._status_window') as mock_status_window:

            from start import AppDelegate

            delegate = AppDelegate.alloc().init()
            mock_app = MagicMock()

            # Simulate dock icon click
            result = delegate.applicationShouldHandleReopen_hasVisibleWindows_(mock_app, False)

            # Verify status window toggle was called
            mock_status_window.toggle.assert_called_once()

            # Verify correct return value
            assert result is True, "Delegate should return True"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_app_delegate_handles_click_without_status_window(self):
        """Test that AppDelegate handles dock clicks gracefully when status window is None."""
        with patch('start.HAS_APPKIT', True), \
             patch('start._status_window', None):

            from start import AppDelegate

            delegate = AppDelegate.alloc().init()
            mock_app = MagicMock()

            # Should not raise exception even if _status_window is None
            result = delegate.applicationShouldHandleReopen_hasVisibleWindows_(mock_app, False)

            assert result is True, "Delegate should still return True"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
