#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update Manager for PokerTool

Handles graceful shutdown, code updates, and restart of the application.
Preserves state during updates and ensures reliable update process.

Usage:
    python scripts/update_manager.py quiesce    # Gracefully stop the app
    python scripts/update_manager.py update     # Pull changes and rebuild frontend
    python scripts/update_manager.py restart    # Restart the app
    python scripts/update_manager.py status     # Check app status
    python scripts/update_manager.py full       # Complete update cycle (quiesce -> update -> restart)
"""

import os
import sys
import json
import time
import signal
import subprocess
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_FILE = PROJECT_ROOT / ".update_state.json"
PID_FILE = PROJECT_ROOT / ".pokertool.pid"
LOG_FILE = PROJECT_ROOT / "logs" / "update_manager.log"


class UpdateManager:
    """Manages application updates with graceful shutdown and restart."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.state_file = STATE_FILE
        self.pid_file = PID_FILE
        self.log_file = LOG_FILE

        # Ensure log directory exists
        self.log_file.parent.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log a message to both console and log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        print(log_entry)

        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

    def save_state(self, state: Dict[str, Any]):
        """Save application state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
            self.log(f"State saved to {self.state_file}")
        except Exception as e:
            self.log(f"Failed to save state: {e}", "ERROR")

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load application state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                self.log(f"State loaded from {self.state_file}")
                return state
        except Exception as e:
            self.log(f"Failed to load state: {e}", "ERROR")
        return None

    def get_app_pid(self) -> Optional[int]:
        """Get the PID of the running PokerTool application."""
        # Try PID file first
        if self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        return pid
            except Exception:
                pass

        # Search for running process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'start.py' in ' '.join(cmdline):
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    def is_app_running(self) -> bool:
        """Check if the application is currently running."""
        return self.get_app_pid() is not None

    def get_app_status(self) -> Dict[str, Any]:
        """Get detailed application status."""
        pid = self.get_app_pid()

        status = {
            "running": pid is not None,
            "pid": pid,
            "timestamp": datetime.now().isoformat(),
        }

        if pid:
            try:
                process = psutil.Process(pid)
                status.update({
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "num_threads": process.num_threads(),
                    "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                })
            except Exception as e:
                self.log(f"Failed to get process details: {e}", "WARN")

        return status

    def quiesce(self) -> bool:
        """Gracefully stop the application, preserving state."""
        self.log("=" * 60)
        self.log("QUIESCE: Initiating graceful shutdown")
        self.log("=" * 60)

        pid = self.get_app_pid()

        if not pid:
            self.log("Application is not running", "WARN")
            return True

        try:
            process = psutil.Process(pid)

            # Save current state
            state = {
                "pid": pid,
                "shutdown_time": datetime.now().isoformat(),
                "reason": "manual_quiesce",
            }
            self.save_state(state)

            # Send SIGTERM for graceful shutdown
            self.log(f"Sending SIGTERM to process {pid}")
            process.send_signal(signal.SIGTERM)

            # Wait for process to terminate gracefully
            self.log("Waiting for graceful shutdown (max 30 seconds)...")
            try:
                process.wait(timeout=30)
                self.log("✓ Application stopped gracefully")

                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()

                return True

            except psutil.TimeoutExpired:
                self.log("Graceful shutdown timeout, forcing termination", "WARN")
                process.kill()
                process.wait(timeout=5)
                self.log("✓ Application forcefully terminated")

                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()

                return True

        except Exception as e:
            self.log(f"Failed to stop application: {e}", "ERROR")
            return False

    def update_code(self) -> bool:
        """Pull latest code changes and rebuild frontend."""
        self.log("=" * 60)
        self.log("UPDATE: Pulling latest changes and rebuilding")
        self.log("=" * 60)

        try:
            # Pull latest changes
            self.log("Pulling latest changes from git...")
            result = subprocess.run(
                ["git", "pull"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.log(f"Git pull failed: {result.stderr}", "ERROR")
                return False

            self.log(result.stdout)

            # Check if frontend needs rebuild
            frontend_dir = self.project_root / "pokertool-frontend"
            if frontend_dir.exists():
                self.log("Checking for frontend changes...")

                # Install/update npm dependencies
                self.log("Installing npm dependencies...")
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode != 0:
                    self.log(f"npm install failed: {result.stderr}", "ERROR")
                    return False

                # Build frontend
                self.log("Building frontend...")
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode != 0:
                    self.log(f"Frontend build failed: {result.stderr}", "ERROR")
                    return False

                self.log("✓ Frontend built successfully")

            # Update Python dependencies
            self.log("Updating Python dependencies...")
            result = subprocess.run(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                self.log(f"pip install failed: {result.stderr}", "WARN")
                # Don't fail on pip errors - some dependencies might be optional

            self.log("✓ Code update completed successfully")
            return True

        except subprocess.TimeoutExpired:
            self.log("Update process timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Update failed: {e}", "ERROR")
            return False

    def restart(self) -> bool:
        """Restart the application."""
        self.log("=" * 60)
        self.log("RESTART: Starting application")
        self.log("=" * 60)

        if self.is_app_running():
            self.log("Application is already running", "WARN")
            return False

        try:
            # Start the application in background
            start_script = self.project_root / "start.py"

            self.log(f"Starting {start_script}...")

            # Start process in background
            process = subprocess.Popen(
                [sys.executable, str(start_script)],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # Wait a moment to ensure it starts
            time.sleep(2)

            # Check if process is still running
            if process.poll() is None:
                # Save PID
                with open(self.pid_file, "w") as f:
                    f.write(str(process.pid))

                self.log(f"✓ Application started successfully (PID: {process.pid})")

                # Wait a bit more and check status
                time.sleep(3)
                status = self.get_app_status()
                if status["running"]:
                    self.log(f"✓ Application is healthy")
                    self.log(f"  - CPU: {status.get('cpu_percent', 0):.1f}%")
                    self.log(f"  - Memory: {status.get('memory_mb', 0):.1f} MB")
                    return True
                else:
                    self.log("Application started but then stopped", "ERROR")
                    return False
            else:
                self.log(f"Application failed to start (exit code: {process.returncode})", "ERROR")
                return False

        except Exception as e:
            self.log(f"Failed to restart application: {e}", "ERROR")
            return False

    def status(self):
        """Display application status."""
        self.log("=" * 60)
        self.log("STATUS: Application Status")
        self.log("=" * 60)

        status = self.get_app_status()

        if status["running"]:
            self.log(f"✓ Application is RUNNING")
            self.log(f"  - PID: {status['pid']}")
            self.log(f"  - CPU: {status.get('cpu_percent', 0):.1f}%")
            self.log(f"  - Memory: {status.get('memory_mb', 0):.1f} MB")
            self.log(f"  - Threads: {status.get('num_threads', 0)}")
            self.log(f"  - Started: {status.get('create_time', 'unknown')}")
        else:
            self.log("✗ Application is NOT RUNNING")

        # Check for saved state
        saved_state = self.load_state()
        if saved_state:
            self.log("\nSaved state found:")
            self.log(f"  - Shutdown time: {saved_state.get('shutdown_time', 'unknown')}")
            self.log(f"  - Reason: {saved_state.get('reason', 'unknown')}")

    def full_update(self) -> bool:
        """Perform complete update cycle: quiesce -> update -> restart."""
        self.log("=" * 60)
        self.log("FULL UPDATE: Starting complete update cycle")
        self.log("=" * 60)

        # Step 1: Quiesce
        if not self.quiesce():
            self.log("Failed to quiesce application", "ERROR")
            return False

        time.sleep(2)

        # Step 2: Update
        if not self.update_code():
            self.log("Failed to update code", "ERROR")
            self.log("Application remains stopped. Manual intervention required.", "ERROR")
            return False

        time.sleep(2)

        # Step 3: Restart
        if not self.restart():
            self.log("Failed to restart application", "ERROR")
            return False

        self.log("=" * 60)
        self.log("✓ FULL UPDATE COMPLETED SUCCESSFULLY")
        self.log("=" * 60)
        return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()
    manager = UpdateManager()

    try:
        if command == "quiesce":
            success = manager.quiesce()
        elif command == "update":
            success = manager.update_code()
        elif command == "restart":
            success = manager.restart()
        elif command == "status":
            manager.status()
            success = True
        elif command == "full":
            success = manager.full_update()
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        manager.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
