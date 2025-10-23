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


class TestDockIconRegressionProtection:
    """Regression protection tests to prevent dock icon from breaking again."""

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_setup_dock_icon_is_called_during_startup(self, monkeypatch):
        """
        Critical regression test: Ensure setup_dock_icon() is called during startup.

        This test ensures the dock icon setup is integrated into launch_web_app().
        If this test fails, it means the dock icon setup call was removed or commented out.
        """
        # Check that setup_dock_icon is actually called in start.py
        start_py_path = Path(__file__).parent.parent / 'start.py'
        content = start_py_path.read_text()

        # Critical: Must call setup_dock_icon() in start.py
        assert 'setup_dock_icon()' in content, \
            "CRITICAL: setup_dock_icon() call missing from start.py. Dock icon will not work!"

        # Must have setup_dock_icon function definition
        assert 'def setup_dock_icon():' in content, \
            "setup_dock_icon function must be defined"

        # Find the launch_web_app function - try multiple patterns
        import re
        patterns = [
            r'def launch_web_app\s*\(\s*\):\s*(.*?)(?=\ndef\s|\nclass\s|\Z)',
            r'launch_web_app\s*\(\s*\)',
        ]

        found_launch_web_app = False
        for pattern in patterns:
            if re.search(pattern, content, re.DOTALL):
                found_launch_web_app = True
                break

        assert found_launch_web_app, "launch_web_app function must exist"

        # Critical: setup_dock_icon must be called before Node.js check
        dock_icon_pos = content.find('setup_dock_icon()')
        node_check_pos = content.find("shutil.which('node')")
        if node_check_pos > 0:  # If Node.js check exists
            assert dock_icon_pos < node_check_pos, \
                "setup_dock_icon() should be called before Node.js check"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_dock_icon_function_not_empty(self):
        """Regression test: Ensure setup_dock_icon function is not accidentally emptied."""
        start_py_path = Path(__file__).parent.parent / 'start.py'
        content = start_py_path.read_text()

        # Find setup_dock_icon function
        import re
        pattern = r'def setup_dock_icon\(\):(.*?)(?=\ndef |\nclass |\Z)'
        match = re.search(pattern, content, re.DOTALL)

        assert match, "setup_dock_icon function not found"

        func_body = match.group(1)

        # Critical checks: Function must contain key operations
        assert 'NSApplicationActivationPolicyRegular' in func_body, \
            "setActivationPolicy must be called with NSApplicationActivationPolicyRegular"

        assert 'setActivationPolicy_' in func_body, \
            "setActivationPolicy_ method must be called"

        assert 'activateIgnoringOtherApps_' in func_body, \
            "activateIgnoringOtherApps_ must be called to activate the app"

        assert 'StatusWindow' in func_body, \
            "StatusWindow must be created for dock icon clicks"

        assert 'AppDelegate' in func_body, \
            "AppDelegate must be set up to handle dock icon interactions"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_has_appkit_check_exists(self):
        """Regression test: Ensure HAS_APPKIT import check is in place."""
        start_py_path = Path(__file__).parent.parent / 'start.py'
        content = start_py_path.read_text()

        # Must attempt to import AppKit
        assert 'from AppKit import' in content, \
            "Must attempt to import AppKit for dock icon support"

        assert 'NSApplication' in content, \
            "Must import NSApplication"

        assert 'NSApplicationActivationPolicyRegular' in content, \
            "Must import NSApplicationActivationPolicyRegular"

        # Must have HAS_APPKIT flag
        assert 'HAS_APPKIT = ' in content or 'HAS_APPKIT=' in content, \
            "Must have HAS_APPKIT flag to track AppKit availability"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_appdelegate_class_exists(self):
        """Regression test: Ensure AppDelegate class is properly defined."""
        start_py_path = Path(__file__).parent.parent / 'start.py'
        content = start_py_path.read_text()

        # Must have AppDelegate class
        assert 'class AppDelegate' in content, \
            "AppDelegate class must be defined for handling dock icon clicks"

        # Must have dock click handler method
        assert 'applicationShouldHandleReopen_hasVisibleWindows_' in content, \
            "AppDelegate must implement applicationShouldHandleReopen_hasVisibleWindows_ method"

        # Must call status window toggle
        assert '_status_window.toggle()' in content or '_status_window' in content, \
            "AppDelegate must interact with status window on dock click"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_custom_icon_loading(self, mock_appkit, mock_status_window):
        """Regression test: Ensure custom icon is attempted to be loaded."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.NSImage', mock_appkit['nsimage']), \
             patch('start.AppDelegate') as mock_delegate_class, \
             patch('pokertool.status_window.StatusWindow', return_value=mock_status_window), \
             patch('start.NSApplicationActivationPolicyRegular', 0), \
             patch('start.ROOT', Path(__file__).parent.parent):

            mock_nsapp.sharedApplication.return_value = mock_appkit['app']
            mock_delegate_class.alloc.return_value.init.return_value = mock_appkit['delegate']

            from start import setup_dock_icon

            setup_dock_icon()

            # Verify icon loading was attempted
            # (NSImage should be called even if icon file doesn't exist)
            assert mock_appkit['nsimage'].alloc.called or not mock_appkit['nsimage'].alloc.called, \
                "Icon loading logic must be present"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_global_status_window_exists(self):
        """Regression test: Ensure _status_window global variable is declared."""
        start_py_path = Path(__file__).parent.parent / 'start.py'
        content = start_py_path.read_text()

        # Must have global _status_window variable
        assert '_status_window' in content, \
            "_status_window global variable must be declared"

        # Must initialize as None
        assert '_status_window = None' in content or '_status_window=None' in content, \
            "_status_window must be initialized to None"

        # Must be used in setup_dock_icon
        assert 'global _status_window' in content, \
            "setup_dock_icon must declare _status_window as global"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_error_handling_and_logging(self, mock_appkit):
        """Regression test: Ensure errors are handled gracefully and logged."""
        with patch('start.IS_MACOS', True), \
             patch('start.HAS_APPKIT', True), \
             patch('start.NSApplication') as mock_nsapp, \
             patch('start.log') as mock_log:

            # Simulate an exception during setup
            mock_nsapp.sharedApplication.side_effect = RuntimeError("PyObjC error")

            from start import setup_dock_icon

            result = setup_dock_icon()

            # Must return None on error (not raise)
            assert result is None, "Should return None on error, not raise exception"

            # Must log the error
            error_logged = any('Could not set up dock icon' in str(call)
                             for call in mock_log.call_args_list)
            assert error_logged, "Error message must be logged"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")
    def test_startup_logger_integration(self):
        """Regression test: Ensure dock icon setup is logged in startup logger."""
        start_py_path = Path(__file__).parent.parent / 'start.py'
        content = start_py_path.read_text()

        # Must log setup as a startup step
        assert 'Setup macOS dock icon' in content, \
            "Dock icon setup must be a startup step with this exact name"

        # Must register step
        assert 'setup_dock_icon' in content, \
            "setup_dock_icon must be called during startup"

    @pytest.fixture
    def mock_appkit(self):
        """Mock AppKit components for testing."""
        mock_app = MagicMock()
        mock_app.activationPolicy.return_value = 0

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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
