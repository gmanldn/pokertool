#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Frontend Error Monitor
======================

Monitors frontend compilation output for blocking errors, logs them,
adds them to TODO.md, and triggers graceful shutdown.

This prevents the application from running with a broken frontend.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import threading


class FrontendErrorMonitor:
    """Monitors frontend process output for compile errors."""

    def __init__(self, log_dir: str = "logs", root_dir: Optional[Path] = None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.root_dir = root_dir or Path(__file__).parent.parent.parent
        self.compile_errors: List[Dict] = []
        self.lock = threading.Lock()
        self.error_detected = False

        # Error patterns that indicate blocking compile errors
        self.blocking_patterns = [
            r"Failed to compile",
            r"Module not found",
            r"Cannot find module",
            r"Attempted import error",
            r"SyntaxError:",
            r"TypeError:",
            r"ReferenceError:",
            r"Compilation failed",
            r"Error: ",
            r"ERROR in ",
        ]

    def process_line(self, line: str) -> bool:
        """
        Process a line of frontend output.

        Returns:
            True if a blocking error was detected, False otherwise.
        """
        with self.lock:
            # Check for blocking error patterns
            for pattern in self.blocking_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self._record_error(line)
                    return True
            return False

    def _record_error(self, line: str):
        """Record a compile error."""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'line': line.strip(),
            'type': self._classify_error(line),
        }
        self.compile_errors.append(error_info)
        self.error_detected = True

    def _classify_error(self, line: str) -> str:
        """Classify the type of error."""
        if 'Module not found' in line or 'Cannot find module' in line:
            return 'MODULE_NOT_FOUND'
        elif 'Attempted import error' in line:
            return 'IMPORT_ERROR'
        elif 'SyntaxError' in line:
            return 'SYNTAX_ERROR'
        elif 'TypeError' in line:
            return 'TYPE_ERROR'
        elif 'Failed to compile' in line:
            return 'COMPILATION_FAILED'
        else:
            return 'UNKNOWN_ERROR'

    def get_errors(self) -> List[Dict]:
        """Get all recorded errors."""
        with self.lock:
            return self.compile_errors.copy()

    def has_errors(self) -> bool:
        """Check if any blocking errors were detected."""
        with self.lock:
            return self.error_detected

    def write_to_log(self):
        """Write errors to log file."""
        if not self.compile_errors:
            return

        log_file = self.log_dir / "frontend_compile_errors.log"

        with open(log_file, 'a') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Frontend Compile Errors - {datetime.now().isoformat()}\n")
            f.write(f"{'='*70}\n\n")

            for error in self.compile_errors:
                f.write(f"[{error['timestamp']}] {error['type']}\n")
                f.write(f"  {error['line']}\n\n")

    def add_to_todo(self):
        """Add errors to docs/TODO.md as P0 tasks."""
        if not self.compile_errors:
            return

        todo_file = self.root_dir / 'docs' / 'TODO.md'

        if not todo_file.exists():
            print(f"Warning: TODO.md not found at {todo_file}")
            return

        # Read existing TODO content
        content = todo_file.read_text()

        # Find the "## Now (P0: highest ROI)" section
        lines = content.split('\n')
        insert_index = None

        for i, line in enumerate(lines):
            if line.strip() == '## Now (P0: highest ROI)':
                # Insert after this line (skip the blank line too)
                insert_index = i + 2
                break

        if insert_index is None:
            print("Warning: Could not find P0 section in TODO.md")
            return

        # Create TODO entries for each unique error type
        error_types = {}
        for error in self.compile_errors:
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error['line'])

        # Build TODO entries
        timestamp = datetime.now().strftime('%Y-%m-%d')
        new_entries = []

        for error_type, error_lines in error_types.items():
            # Take first error line as example
            example_error = error_lines[0][:150]  # Truncate if too long

            todo_entry = f"- [ ] [P0][S] Fix frontend {error_type.lower().replace('_', ' ')} — " \
                        f"Frontend compilation blocked. Error: {example_error}. " \
                        f"Detected on {timestamp}. Check logs/frontend_compile_errors.log " \
                        f"for full details. Application auto-shutdown due to blocking error. " \
                        f"Total occurrences: {len(error_lines)}."

            new_entries.append(todo_entry)

        # Insert new entries
        for entry in reversed(new_entries):
            lines.insert(insert_index, entry)

        # Write back to file
        todo_file.write_text('\n'.join(lines))

        print(f"Added {len(new_entries)} error(s) to TODO.md as P0 tasks")

    def shutdown_with_errors(self):
        """
        Handle shutdown due to compile errors.

        This method:
        1. Writes errors to log file
        2. Adds errors to TODO.md
        3. Prints error summary
        """
        print("\n" + "="*70)
        print("FRONTEND COMPILE ERROR DETECTED")
        print("="*70)
        print(f"\nDetected {len(self.compile_errors)} blocking error(s) in frontend compilation.")
        print("\nActions taken:")

        # Write to log
        self.write_to_log()
        print(f"  ✓ Errors logged to {self.log_dir / 'frontend_compile_errors.log'}")

        # Add to TODO
        self.add_to_todo()
        print(f"  ✓ Added P0 tasks to docs/TODO.md")

        print("\nError summary:")
        for i, error in enumerate(self.compile_errors[:5], 1):  # Show first 5
            print(f"  {i}. [{error['type']}] {error['line'][:80]}")

        if len(self.compile_errors) > 5:
            print(f"  ... and {len(self.compile_errors) - 5} more error(s)")

        print("\nApplication will now shut down gracefully.")
        print("Please fix the errors listed in docs/TODO.md before restarting.")
        print("="*70 + "\n")


# Global monitor instance
_monitor = None


def get_frontend_error_monitor() -> FrontendErrorMonitor:
    """Get global frontend error monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = FrontendErrorMonitor()
    return _monitor
