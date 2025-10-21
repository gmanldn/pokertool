#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Backend Startup Logger
======================

Thread-safe logging system for tracking backend startup progress with real-time visibility.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Literal
from threading import Lock
from dataclasses import dataclass, asdict
from datetime import datetime

StepStatus = Literal["pending", "in_progress", "success", "failed"]


@dataclass
class StartupStep:
    """Represents a single startup step."""
    number: int
    name: str
    description: str
    status: StepStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        """Calculate step duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d['duration'] = self.duration
        return d


class BackendStartupLogger:
    """Thread-safe singleton logger for backend startup progress."""

    _instance: Optional['BackendStartupLogger'] = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the logger (only once due to singleton pattern)."""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._steps: Dict[str, StartupStep] = {}
        self._step_order: List[str] = []
        self._start_time = time.time()
        self._is_complete = False
        self._data_lock = Lock()

        # Setup log files
        log_dir = Path.home() / '.pokertool' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = log_dir / 'backend_startup.log'
        self._status_file = log_dir / 'backend_startup_status.json'

        # Initialize log file (append mode to preserve logs from parent process)
        if not self._log_file.exists():
            with open(self._log_file, 'w') as f:
                f.write("=== Backend Startup Log ===\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")
        else:
            # Log that a new process instance started
            with open(self._log_file, 'a') as f:
                f.write(f"\n[New process started: {datetime.now().isoformat()}]\n")

        # Initialize status file only if it doesn't exist or is empty
        # This preserves status from parent process (start.py)
        if not self._status_file.exists():
            self._save_status_to_file()
        else:
            # Try to load existing status to populate our state
            try:
                with open(self._status_file, 'r') as f:
                    existing_status = json.load(f)
                    # If there are existing steps, restore them to our instance
                    if existing_status.get('steps'):
                        for step_dict in existing_status['steps']:
                            step_name = step_dict['name']
                            if step_name not in self._steps:
                                step = StartupStep(
                                    number=step_dict['number'],
                                    name=step_dict['name'],
                                    description=step_dict['description'],
                                    status=step_dict['status'],
                                    start_time=step_dict.get('start_time'),
                                    end_time=step_dict.get('end_time')
                                )
                                self._steps[step_name] = step
                                if step_name not in self._step_order:
                                    self._step_order.append(step_name)
            except Exception:
                # If loading fails, initialize with empty status
                self._save_status_to_file()

        self._initialized = True

    def set_total_steps(self, count: int) -> None:
        """Set expected total number of startup steps."""
        # This is a no-op for our implementation - we track steps dynamically
        pass

    def register_steps(self, steps: List[tuple]) -> None:
        """
        Register steps with names and descriptions.

        Args:
            steps: List of (name, description) tuples
        """
        step_names = [name for name, _ in steps]
        with self._data_lock:
            for i, (name, description) in enumerate(steps, start=1):
                if name not in self._steps:
                    step = StartupStep(
                        number=i,
                        name=name,
                        description=description,
                        status="pending"
                    )
                    self._steps[name] = step
                    self._step_order.append(name)

            self._write_to_log(f"Pre-registered {len(steps)} startup steps")
            self._save_status_to_file()

    def pre_register_steps(self, step_names: List[str]) -> None:
        """Pre-register expected startup steps for immediate UI visibility."""
        steps = [(name, name) for name in step_names]
        self.register_steps(steps)

    def log_step(
        self,
        step_name: str,
        status: StepStatus,
        description: Optional[str] = None
    ) -> None:
        """Log a startup step with status update."""
        with self._data_lock:
            current_time = time.time()

            if step_name not in self._steps:
                number = len(self._steps) + 1
                step = StartupStep(
                    number=number,
                    name=step_name,
                    description=description or step_name,
                    status=status
                )
                self._steps[step_name] = step
                self._step_order.append(step_name)
            else:
                step = self._steps[step_name]
                step.status = status
                if description:
                    step.description = description

            # Update timestamps
            if status == "in_progress" and step.start_time is None:
                step.start_time = current_time
            elif status in ("success", "failed"):
                if step.end_time is None:
                    step.end_time = current_time
                if all(s.status in ("success", "failed") for s in self._steps.values()):
                    self._is_complete = True

            # Log to file
            elapsed = current_time - self._start_time
            duration_str = f" ({step.duration:.2f}s)" if step.duration else ""
            log_msg = f"[{elapsed:.1f}s] {step.name}: {status.upper()}{duration_str}"
            self._write_to_log(log_msg)

            # Save status to JSON file for cross-process access
            self._save_status_to_file()

    def get_status(self) -> Dict:
        """Get current startup status."""
        # Try loading from file first (for cross-process access)
        try:
            if hasattr(self, '_status_file') and self._status_file.exists():
                with open(self._status_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass

        # Fallback to in-memory state
        with self._data_lock:
            steps_list = [self._steps[name].to_dict() for name in self._step_order]

            return {
                "elapsed_time": time.time() - self._start_time,
                "current_step": self._get_current_step_number(),
                "total_steps": len(self._steps),
                "steps_completed": sum(1 for s in self._steps.values() if s.status == "success"),
                "steps_in_progress": sum(1 for s in self._steps.values() if s.status == "in_progress"),
                "steps_failed": sum(1 for s in self._steps.values() if s.status == "failed"),
                "steps_pending": sum(1 for s in self._steps.values() if s.status == "pending"),
                "steps_remaining": sum(1 for s in self._steps.values() if s.status in ("pending", "in_progress")),
                "is_complete": self._is_complete,
                "steps": steps_list
            }

    def _save_status_to_file(self) -> None:
        """Save current status to JSON file for cross-process access."""
        try:
            if not hasattr(self, '_status_file'):
                return

            status = {
                "elapsed_time": time.time() - self._start_time if hasattr(self, '_start_time') else 0,
                "current_step": self._get_current_step_number() if self._steps else 0,
                "total_steps": len(self._steps),
                "steps_completed": sum(1 for s in self._steps.values() if s.status == "success"),
                "steps_in_progress": sum(1 for s in self._steps.values() if s.status == "in_progress"),
                "steps_failed": sum(1 for s in self._steps.values() if s.status == "failed"),
                "steps_pending": sum(1 for s in self._steps.values() if s.status == "pending"),
                "steps_remaining": sum(1 for s in self._steps.values() if s.status in ("pending", "in_progress")),
                "is_complete": self._is_complete,
                "steps": [self._steps[name].to_dict() for name in self._step_order]
            }

            with open(self._status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception:
            pass  # Silently fail

    def get_log_lines(self, lines: int = 100) -> List[str]:
        """Get recent log lines from the startup log file."""
        try:
            with open(self._log_file, 'r') as f:
                all_lines = f.readlines()
                return [line.rstrip() for line in all_lines[-lines:]]
        except Exception:
            return []

    def start_step(self, step_name: str, description: str = "") -> str:
        """
        Start a step and mark it as in_progress.

        Args:
            step_name: Name of the step to start
            description: Description of the step

        Returns:
            step_name for use with complete_step()
        """
        self.log_step(step_name, "in_progress", description or None)
        return step_name

    def complete_step(self, step_name: str, success: bool = True, message: str = "") -> None:
        """
        Complete a step and mark it as success or failed.

        Args:
            step_name: Name of the step to complete
            success: Whether the step succeeded
            message: Optional completion message
        """
        status = "success" if success else "failed"
        self.log_step(step_name, status, message or None)

    def log_info(self, message: str) -> None:
        """Log an informational message to the log file."""
        self._write_to_log(f"INFO: {message}")

    def get_log_tail(self, lines: int = 100) -> List[str]:
        """Alias for get_log_lines() to match API expectations."""
        return self.get_log_lines(lines)

    def _get_current_step_number(self) -> int:
        """Get the number of the current step."""
        for name in self._step_order:
            step = self._steps[name]
            if step.status == "in_progress":
                return step.number
            elif step.status == "pending":
                return step.number
        return len(self._steps)

    def _write_to_log(self, message: str) -> None:
        """Write a message to the log file."""
        try:
            with open(self._log_file, 'a') as f:
                f.write(f"{message}\n")
        except Exception:
            pass


def get_startup_logger() -> BackendStartupLogger:
    """Get the global BackendStartupLogger instance."""
    return BackendStartupLogger()
