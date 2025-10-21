#!/usr/bin/env python3
"""
Backend Startup Logger
=====================

Logs all backend startup steps with timestamps and progress tracking.
Creates a rolling log file in logs/backend_startup.log for monitoring.
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import threading

class BackendStartupLogger:
    """Tracks and logs backend startup progress."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "backend_startup.log"
        self.start_time = time.time()
        self.current_step = 0
        self.total_steps = 0
        self.steps: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

        # Initialize log file
        self._write_header()

    def _write_header(self):
        """Write log file header."""
        with open(self.log_file, 'w') as f:
            f.write(f"=== Backend Startup Log ===" "\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write(f"=" * 70 + "\n\n")

    def set_total_steps(self, total: int):
        """Set total number of startup steps."""
        with self.lock:
            self.total_steps = total
            self._log(f"Total startup steps: {total}")

    def start_step(self, step_name: str, description: str = ""):
        """Start a new startup step."""
        with self.lock:
            self.current_step += 1
            elapsed = time.time() - self.start_time

            step_info = {
                'number': self.current_step,
                'name': step_name,
                'description': description,
                'start_time': time.time(),
                'elapsed_at_start': elapsed,
                'status': 'in_progress'
            }
            self.steps.append(step_info)

            progress = f"[{self.current_step}/{self.total_steps}]" if self.total_steps > 0 else f"[{self.current_step}]"
            msg = f"{progress} {step_name}"
            if description:
                msg += f": {description}"
            msg += f" (elapsed: {elapsed:.1f}s)"

            self._log(msg)
            return len(self.steps) - 1  # Return step index

    def complete_step(self, step_index: int = -1, success: bool = True, message: str = ""):
        """Mark a step as complete."""
        with self.lock:
            if step_index == -1:
                step_index = len(self.steps) - 1

            if 0 <= step_index < len(self.steps):
                step = self.steps[step_index]
                step['status'] = 'success' if success else 'failed'
                step['end_time'] = time.time()
                step['duration'] = step['end_time'] - step['start_time']

                status_icon = "✓" if success else "✗"
                msg = f"  {status_icon} {step['name']} completed in {step['duration']:.2f}s"
                if message:
                    msg += f" - {message}"

                self._log(msg)

    def log_info(self, message: str):
        """Log an informational message."""
        with self.lock:
            self._log(f"  ℹ {message}")

    def log_warning(self, message: str):
        """Log a warning message."""
        with self.lock:
            self._log(f"  ⚠ WARNING: {message}")

    def log_error(self, message: str):
        """Log an error message."""
        with self.lock:
            self._log(f"  ✗ ERROR: {message}")

    def _log(self, message: str):
        """Write message to log file."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = time.time() - self.start_time
        log_line = f"[{timestamp}] [+{elapsed:7.2f}s] {message}\n"

        with open(self.log_file, 'a') as f:
            f.write(log_line)

    def get_status(self) -> Dict[str, Any]:
        """Get current startup status."""
        with self.lock:
            elapsed = time.time() - self.start_time
            in_progress = sum(1 for s in self.steps if s['status'] == 'in_progress')
            completed = sum(1 for s in self.steps if s['status'] in ['success', 'failed'])
            failed = sum(1 for s in self.steps if s['status'] == 'failed')

            return {
                'elapsed_time': elapsed,
                'current_step': self.current_step,
                'total_steps': self.total_steps,
                'steps_completed': completed,
                'steps_in_progress': in_progress,
                'steps_failed': failed,
                'steps_remaining': max(0, self.total_steps - self.current_step),
                'steps': self.steps.copy(),
                'is_complete': self.current_step >= self.total_steps and in_progress == 0,
            }

    def get_log_tail(self, lines: int = 100) -> List[str]:
        """Get last N lines from log file."""
        try:
            with open(self.log_file, 'r') as f:
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception:
            return []

# Global logger instance
_startup_logger = None

def get_startup_logger() -> BackendStartupLogger:
    """Get global startup logger instance."""
    global _startup_logger
    if _startup_logger is None:
        _startup_logger = BackendStartupLogger()
    return _startup_logger
