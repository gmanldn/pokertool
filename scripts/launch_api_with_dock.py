#!/usr/bin/env python3
"""
Launch the PokerTool API server with a macOS dock icon.

This script creates a proper macOS application that appears in the dock
with an icon when the API server is running.
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from AppKit import (
        NSApplication,
        NSApp,
        NSImage,
        NSApplicationActivationPolicyRegular,
        NSMenu,
        NSMenuItem,
        NSStatusBar,
    )
    from PyObjCTools import AppHelper
except ImportError:
    print("Error: PyObjC not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyobjc-framework-Cocoa"], check=True)
    from AppKit import (
        NSApplication,
        NSApp,
        NSImage,
        NSApplicationActivationPolicyRegular,
        NSMenu,
        NSMenuItem,
        NSStatusBar,
    )
    from PyObjCTools import AppHelper


class PokerToolAPIApp:
    """macOS application wrapper for the PokerTool API server."""

    def __init__(self):
        self.api_process = None
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

        # Set up menu bar
        self.setup_menu()

        # Set dock icon
        self.setup_dock_icon()

        # Start API server
        self.start_api_server()

    def setup_menu(self):
        """Create the application menu."""
        menubar = NSMenu.alloc().init()
        app_menu_item = NSMenuItem.alloc().init()
        menubar.addItem_(app_menu_item)
        self.app.setMainMenu_(menubar)

        app_menu = NSMenu.alloc().init()

        # Quit menu item
        quit_title = "Quit PokerTool API"
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            quit_title, "terminate:", "q"
        )
        app_menu.addItem_(quit_item)

        app_menu_item.setSubmenu_(app_menu)

    def setup_dock_icon(self):
        """Set up the dock icon for the application."""
        # Try to find an icon file, or create a default one
        icon_path = project_root / "assets" / "pokertool-icon.png"

        if icon_path.exists():
            icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if icon:
                self.app.setApplicationIconImage_(icon)

    def start_api_server(self):
        """Start the API server as a subprocess."""
        print("Starting PokerTool API server...")

        # Set up environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root / "src")

        # Start uvicorn
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "pokertool.api:create_app",
            "--host", "0.0.0.0",
            "--port", "5001",
            "--factory"
        ]

        self.api_process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Print output in a separate thread
        import threading
        def print_output():
            for line in self.api_process.stdout:
                print(line, end='')

        output_thread = threading.Thread(target=print_output, daemon=True)
        output_thread.start()

        print(f"API server started with PID {self.api_process.pid}")
        print("Server running at http://localhost:5001")

    def stop_api_server(self):
        """Stop the API server."""
        if self.api_process:
            print("\nStopping API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
            print("API server stopped")

    def run(self):
        """Run the application."""
        try:
            # Activate the application
            self.app.activateIgnoringOtherApps_(True)

            # Run the event loop
            AppHelper.runEventLoop()
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        finally:
            self.stop_api_server()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\nReceived signal {signum}")
    AppHelper.stopEventLoop()
    sys.exit(0)


def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run the application
    app = PokerToolAPIApp()
    app.run()


if __name__ == "__main__":
    main()
