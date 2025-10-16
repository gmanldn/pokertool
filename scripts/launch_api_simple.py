#!/usr/bin/env python3
"""
Launch the PokerTool API server with a simple macOS dock presence.

This creates a minimal macOS application that shows in the dock while
the API server is running.
"""

import os
import sys
import subprocess
import signal
import time
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
    )
except ImportError:
    print("PyObjC not installed. Install with: pip install pyobjc-framework-Cocoa")
    sys.exit(1)


def setup_dock_icon():
    """Set up a basic dock presence."""
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

    # Load icon if available
    icon_path = project_root / "assets" / "pokertool-icon.png"
    if icon_path.exists():
        icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
        if icon:
            app.setApplicationIconImage_(icon)

    # Activate the app to show in dock
    app.activateIgnoringOtherApps_(True)

    return app


def start_api_server():
    """Start the API server as a subprocess."""
    print("Starting PokerTool API server with dock icon...")

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

    process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print(f"✓ API server started with PID {process.pid}")
    print(f"✓ Server running at http://localhost:5001")
    print(f"✓ Dock icon visible")
    print("\nPress Ctrl+C to stop the server\n")

    return process


def print_output(process):
    """Print the server output."""
    try:
        for line in process.stdout:
            print(line, end='')
    except KeyboardInterrupt:
        pass


def cleanup(process):
    """Clean up on exit."""
    if process:
        print("\n\nStopping API server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✓ API server stopped cleanly")
        except subprocess.TimeoutExpired:
            process.kill()
            print("✓ API server killed")


def main():
    """Main entry point."""
    # Set up dock icon first
    app = setup_dock_icon()

    # Start API server
    process = start_api_server()

    # Set up signal handler
    def signal_handler(signum, frame):
        cleanup(process)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Print output from server
    try:
        print_output(process)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup(process)


if __name__ == "__main__":
    main()
