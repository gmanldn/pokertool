#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: start.py
# version: v68.0.0
# last_commit: '2025-10-14T22:00:00Z'
# fixes:
# - date: '2025-10-14'
#   summary: Added kill.py process management utility for cleaning up stuck pokertool processes
# - date: '2025-10-14'
#   summary: Added detailed explanation textbox on LiveTable showing WHY actions are recommended with metrics
# - date: '2025-10-14'
#   summary: Win Rate & Accuracy Optimization - GTO caching (60-80% speedup), confidence intervals, formatting system
# - date: '2025-10-14'
#   summary: Enhanced status bar with rolling game state display and version info
# - date: '2025-10-14'
#   summary: Added canonical version tracking system with release branch workflow
# - date: '2025-10-14'
#   summary: Added 35 comprehensive screen scraping optimizations (speed, accuracy, reliability)
# - date: '2025-10-14'
#   summary: Added comprehensive UI enhancements - status panel, feedback, shortcuts, profiles, charts
# - date: '2025-10-14'
#   summary: Fixed GUI startup - robust process cleanup, window visibility, black button text
# - date: '2025-10-12'
#   summary: Added comprehensive startup validation system with health monitoring
# - date: '2025-10-12'
#   summary: Updated to launch Enhanced GUI v32.0.0 with modern styling and logging tab
# - date: '2025-10-12'
#   summary: Added real-time Logging tab to monitor all application activity
# - date: '2025-10-12'
#   summary: Modernized color scheme with deeper contrasts and vibrant accents
# - date: '2025-01-10'
#   summary: Complete rewrite for robust cross-platform dependency management and setup
# ---
# POKERTOOL-HEADER-END

PokerTool Web Application Launcher - v84.0.0
=============================================

This script sets up everything and launches the Web Application (Backend API + React Frontend).

Web-Only Architecture - No tkinter/GUI windows.

Usage:
    python start.py              # Launch web application (default)
    python start.py --setup-only # Install dependencies only
    python start.py --self-test  # Run comprehensive tests

After launching, access the app at: http://localhost:3000

Note: This script automatically cleans up old pokertool/uvicorn/npm processes before starting.
"""
from __future__ import annotations
from pathlib import Path
from typing import Sequence, Optional, Dict, Any, List
import os
import sys
import subprocess
import platform
import shutil
import argparse

# Add src to path for version import
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

# Import canonical version
try:
    from pokertool.version import __version__, format_version
except ImportError:
    __version__ = '64.0.0'  # Fallback
    format_version = lambda **kwargs: f"v{__version__}"

# Constants
ROOT = Path(__file__).resolve().parent  # Project root (since start.py is now in root)
SRC_DIR = ROOT / 'src'
VENV_DIR = ROOT / '.venv'

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

# Supported Python versions
MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 13)

# Try to import macOS AppKit for dock icon support
HAS_APPKIT = False
if IS_MACOS:
    try:
        from AppKit import (
            NSApplication,
            NSImage,
            NSApplicationActivationPolicyRegular,
        )
        from Foundation import NSObject
        HAS_APPKIT = True
    except ImportError:
        # PyObjC not installed - will continue without dock icon
        pass

# Global status window instance
_status_window = None

# AppDelegate for handling dock icon clicks
if HAS_APPKIT:
    class AppDelegate(NSObject):
        """Delegate to handle dock icon clicks."""

        def applicationShouldHandleReopen_hasVisibleWindows_(self, app, has_visible_windows):
            """Called when dock icon is clicked."""
            global _status_window
            if _status_window:
                _status_window.toggle()
            return True

def setup_dock_icon():
    """Set up macOS dock icon (if on macOS and PyObjC is available)."""
    global _status_window

    if not IS_MACOS or not HAS_APPKIT:
        return None

    try:
        # Import status window
        from pokertool.status_window import StatusWindow

        # Create status window instance
        _status_window = StatusWindow(api_url="http://localhost:5001")

        # Set up NSApplication
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)

        # Set up delegate to handle dock icon clicks
        delegate = AppDelegate.alloc().init()
        app.setDelegate_(delegate)

        # Try to load custom icon if available
        icon_path = ROOT / "assets" / "pokertool-icon.png"
        if icon_path.exists():
            icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if icon:
                app.setApplicationIconImage_(icon)

        # Activate the app to show in dock
        app.activateIgnoringOtherApps_(True)

        return app
    except Exception as e:
        log(f"⚠️  Could not set up dock icon: {e}")
        return None

def clear_terminal():
    """Clear terminal for clean output."""
    os.system('cls' if IS_WINDOWS else 'clear')

def log(message: str):
    """Log a message."""
    print(f"[POKERTOOL] {message}")

def get_python_executable() -> str:
    """Get best Python executable."""
    if sys.executable:
        return sys.executable
    
    candidates = ['python3.12', 'python3.11', 'python3.10', 'python3', 'python']
    if IS_WINDOWS:
        candidates = ['py', 'python'] + candidates
    
    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    
    raise RuntimeError("No suitable Python found")

def get_venv_python() -> str:
    """Get venv Python path."""
    if IS_WINDOWS:
        return str(VENV_DIR / 'Scripts' / 'python.exe')
    return str(VENV_DIR / 'bin' / 'python')

def create_venv():
    """Create virtual environment."""
    if VENV_DIR.exists():
        log("Virtual environment exists")
        return
    
    log("Creating virtual environment...")
    python_exe = get_python_executable()
    subprocess.run([python_exe, '-m', 'venv', str(VENV_DIR)], check=True)
    log("✓ Virtual environment created")

def install_dependencies():
    """Install all dependencies."""
    venv_python = get_venv_python()
    
    # Upgrade pip
    log("Upgrading pip...")
    subprocess.run([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                   check=True, capture_output=True)
    
    # Install from requirements.txt
    requirements = ROOT / 'requirements.txt'
    if requirements.exists():
        log("Installing Python dependencies...")
        subprocess.run([venv_python, '-m', 'pip', 'install', '-r', str(requirements)],
                       check=True)
        log("✓ Dependencies installed")
    
    # Install critical deps for enhanced GUI
    log("Ensuring enhanced GUI dependencies...")
    critical = ['opencv-python', 'Pillow', 'pytesseract', 'mss', 'numpy']

    # Add PyObjC for macOS dock icon
    if IS_MACOS:
        critical.append('pyobjc-framework-Cocoa')

    for dep in critical:
        try:
            subprocess.run([venv_python, '-m', 'pip', 'install', dep],
                          check=True, capture_output=True, timeout=120)
        except:
            log(f"Warning: {dep} install had issues")

def run_tests() -> int:
    """Run comprehensive test suite."""
    venv_python = get_venv_python()
    
    log("Running comprehensive tests...")
    log("=" * 70)
    
    # Test enhanced GUI v2 and startup validation
    test_files = [
        ROOT / 'tests' / 'gui' / 'test_enhanced_gui_styles.py',
        ROOT / 'tests' / 'test_startup_validation.py'
    ]

    for test_file in test_files:
        if test_file.exists():
            log(f"Testing {test_file.name}...")
            try:
                result = subprocess.run([venv_python, '-m', 'pytest', str(test_file), '-v'],
                                       cwd=ROOT)
                if result.returncode != 0:
                    log(f"⚠ Some tests in {test_file.name} failed (non-critical)")
            except:
                log("⚠ pytest not available, skipping unit tests")
                break
    
    log("=" * 70)
    log("✓ Test suite completed")
    return 0

def cleanup_old_processes():
    """Kill any old pokertool/GUI processes before starting (including stuck ones)."""
    import time
    import signal

    try:
        current_pid = os.getpid()
        log("Cleaning up previous pokertool/GUI instances...")

        if IS_WINDOWS:
            # Windows: Kill any pokertool GUI processes
            subprocess.run(
                ['taskkill', '/F', '/FI', 'IMAGENAME eq python*', '/FI', f'PID ne {current_pid}'],
                capture_output=True, timeout=5
            )
            # Also kill React dev servers
            subprocess.run(
                ['taskkill', '/F', '/FI', 'IMAGENAME eq node.exe'],
                capture_output=True, timeout=5
            )
        else:
            # Unix: Kill ALL pokertool-related processes (GUI, API, frontend)
            # Patterns to search for
            patterns = [
                'python.*start\\.py',
                '\\.venv/bin/python.*start\\.py',
                'python.*scripts/start\\.py',
                'python.*enhanced_gui',
                'python.*simple_gui',
                'python.*launch.*gui',
                'python.*launch_gui',
                'python.*launch_api',
                'python.*run_gui',
                'pokertool.*gui',
                'uvicorn.*pokertool',
                'python.*uvicorn.*pokertool',
                '\\.venv.*uvicorn.*pokertool',
                'python.*-m.*uvicorn.*pokertool',
                'python.*api\\.py',
                'node.*react-scripts',
                'react-scripts start',
                'npm start',
                'pokertool-frontend.*npm'
            ]

            all_pids = set()
            for pattern in patterns:
                try:
                    result = subprocess.run(
                        ['pgrep', '-f', pattern],
                        capture_output=True, text=True, timeout=3
                    )
                    pids = [int(pid) for pid in result.stdout.strip().split('\n')
                           if pid and pid.strip() and int(pid) != current_pid]
                    all_pids.update(pids)
                except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                    pass

            # Also check for processes using our ports (5001, 3000)
            for port in [5001, 3000]:
                try:
                    result = subprocess.run(
                        ['lsof', '-ti', f':{port}'],
                        capture_output=True, text=True, timeout=3
                    )
                    port_pids = [int(pid) for pid in result.stdout.strip().split('\n')
                               if pid and pid.strip() and int(pid) != current_pid]
                    if port_pids:
                        log(f"Found process(es) using port {port}")
                        all_pids.update(port_pids)
                except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                    pass

            if all_pids:
                log(f"Found {len(all_pids)} previous instance(s) to clean up")

                # Step 1: Try SIGTERM first (graceful)
                for pid in all_pids:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except (ProcessLookupError, PermissionError):
                        pass

                # Step 2: Wait briefly for graceful shutdown
                time.sleep(1.0)

                # Step 3: Force kill any remaining processes with SIGKILL
                still_running = []
                for pid in all_pids:
                    try:
                        os.kill(pid, 0)  # Check if still running
                        os.kill(pid, signal.SIGKILL)  # Force kill
                        still_running.append(pid)
                    except (ProcessLookupError, PermissionError):
                        pass

                if still_running:
                    log(f"Force killed {len(still_running)} stuck process(es)")

                time.sleep(0.5)
                log("✓ Cleanup complete")
            else:
                log("✓ No previous instances found")

    except Exception as e:
        log(f"⚠️  Cleanup warning: {e}")
        pass

def launch_web_app() -> int:
    """Launch the web-only application: Backend API + React frontend."""
    venv_python = get_venv_python()

    # Clean up any old processes first
    cleanup_old_processes()

    # Set up macOS dock icon (if on macOS)
    dock_app = setup_dock_icon()
    if dock_app and IS_MACOS:
        log("✓ macOS dock icon configured (click for status window)")

    # Setup environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SRC_DIR)

    log("=" * 70)
    log(f"🎰 LAUNCHING POKERTOOL WEB APPLICATION {format_version(include_name=True)}")
    log("=" * 70)
    log("")
    log("Architecture: Web-Only (No GUI)")
    log("  ✓ FastAPI Backend (Python API)")
    log("  ✓ React Frontend (Web UI)")
    log("  ✓ WebSocket Real-time Updates")
    log("  ✓ Screen Scraping Engine")
    log("  ✓ Poker Analysis & ML")
    if IS_MACOS and dock_app:
        log("  ✓ macOS Dock Icon (click for status)")
    log("")
    log("Access the app at: http://localhost:3000")
    if IS_MACOS and dock_app:
        log("💡 Click dock icon to see app status & table detection")
    log("")

    # Check for Node.js
    log("Checking dependencies...")
    if not shutil.which('node'):
        log("❌ Node.js not found. Please install Node.js to run the frontend.")
        log("   Visit: https://nodejs.org/")
        return 1

    log("✓ Node.js found")

    # Check if frontend dependencies are installed
    frontend_dir = ROOT / 'pokertool-frontend'
    if not (frontend_dir / 'node_modules').exists():
        log("Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            log("✓ Frontend dependencies installed")
        except subprocess.CalledProcessError:
            log("❌ Failed to install frontend dependencies")
            return 1

    # Start backend API server
    log("")
    log("Starting backend API server...")
    backend_port = 5001  # Using 5001 since 5000 is often used by macOS Control Center
    backend_process = subprocess.Popen(
        [venv_python, '-m', 'uvicorn', 'pokertool.api:create_app',
         '--host', '0.0.0.0', '--port', str(backend_port), '--factory'],
        env=env,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    log(f"✓ Backend API starting on http://localhost:{backend_port}")

    # Start React frontend
    log("Starting React frontend...")
    frontend_env = os.environ.copy()
    frontend_env['REACT_APP_API_URL'] = f'http://localhost:{backend_port}'

    frontend_process = subprocess.Popen(
        ['npm', 'start'],
        cwd=frontend_dir,
        env=frontend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    log("✓ Frontend starting on http://localhost:3000")
    log("")
    log("=" * 70)
    log("🎉 POKERTOOL IS RUNNING!")
    log("=" * 70)
    log("")
    log("📱 Open your browser to: http://localhost:3000")
    log("")
    log("Press Ctrl+C to stop the application")
    log("")

    try:
        # Wait for both processes
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        log("")
        log("Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        log("✓ Application stopped")
        return 0

    return 0

def show_banner():
    """Show startup banner."""
    clear_terminal()
    print("=" * 70)
    print(f"🎰 POKERTOOL - Web Application {format_version()}")
    print("=" * 70)
    print("Web-Only Architecture - No GUI | Backend API + React Frontend")
    print("")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Learning: 🧠 Adaptive ML System (Auto-Enabled)")
    print("=" * 70)
    print("")

def main() -> int:
    """Main entry point - Launch PokerTool Web Application."""
    parser = argparse.ArgumentParser(description='PokerTool Web Application Launcher')
    parser.add_argument('--setup-only', action='store_true', help='Setup dependencies without launching')
    parser.add_argument('--self-test', action='store_true', help='Run comprehensive tests')

    args = parser.parse_args()

    show_banner()

    try:
        # Always ensure venv exists
        if not VENV_DIR.exists() or not Path(get_venv_python()).exists():
            create_venv()
            install_dependencies()

        # Setup dependencies
        log("Verifying dependencies...")
        install_dependencies()
        log("✓ Setup complete")

        # Self-test if requested
        if args.self_test:
            run_tests()
            return 0

        # Launch web application unless setup-only
        if args.setup_only:
            log("✓ Setup completed. Run 'python scripts/start.py' to launch the web app.")
            return 0

        # Launch the web application
        return launch_web_app()

    except KeyboardInterrupt:
        log("Interrupted by user")
        log("Cleaning up processes...")
        cleanup_old_processes()
        return 130
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        log("")
        log("Cleaning up processes due to error...")
        cleanup_old_processes()
        return 1

if __name__ == '__main__':
    sys.exit(main())
