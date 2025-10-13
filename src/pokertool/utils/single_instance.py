#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility helpers to ensure only one PokerTool GUI instance runs at a time.

These helpers manage a PID lock file in the user's home directory and expose
simple acquire/release functions that work across platforms.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

_LOCK_TEMPLATE = ".{name}.lock"
_DEFAULT_APP_NAME = "pokertool"


def _sanitize_app_name(app_name: str) -> str:
    """Return a filesystem-friendly lock file stem."""
    sanitized = "".join(
        ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in app_name.strip().lower()
    )
    return sanitized or _DEFAULT_APP_NAME


def _lock_path(app_name: str) -> Path:
    """Compute the absolute lock file path for the given app name."""
    return Path.home() / _LOCK_TEMPLATE.format(name=_sanitize_app_name(app_name))


def _pid_is_running(pid: int) -> bool:
    """Check whether a PID is alive without terminating it."""
    if pid <= 0:
        return False

    try:
        os.kill(pid, 0)  # Signal 0 only checks for existence.
    except ProcessLookupError:
        return False
    except PermissionError:
        # On Windows this is raised if the process exists but cannot be signalled.
        return True
    except OSError:
        # Any other OS error still indicates the PID likely exists.
        return True
    else:
        return True


def acquire_lock(app_name: str = _DEFAULT_APP_NAME, force_cleanup: bool = True) -> Tuple[Optional[Path], Optional[int]]:
    """
    Attempt to acquire the single-instance lock.

    Args:
        app_name: Application name for the lock file
        force_cleanup: If True, forcefully kill any previous instance to ensure only newest runs

    Returns a tuple of (lock_path, existing_pid). If lock_path is None and
    existing_pid is not None, another process already holds the lock. If both
    values are None, an unexpected filesystem error occurred.
    """
    import signal
    import time

    lock_path = _lock_path(app_name)

    try:
        if lock_path.exists():
            try:
                stored_pid = int(lock_path.read_text().strip())
            except (OSError, ValueError):
                stored_pid = None

            if stored_pid and _pid_is_running(stored_pid):
                if force_cleanup:
                    # Newest instance wins - forcefully clean up the old one
                    print(f"[POKERTOOL] Found previous instance (PID {stored_pid}), cleaning up...")

                    try:
                        # Step 1: Try graceful termination (SIGTERM)
                        os.kill(stored_pid, signal.SIGTERM)
                        time.sleep(0.5)

                        # Step 2: Check if still running, use SIGKILL if needed
                        if _pid_is_running(stored_pid):
                            print(f"[POKERTOOL] Force killing stuck process PID {stored_pid}")
                            os.kill(stored_pid, signal.SIGKILL)
                            time.sleep(0.3)
                        else:
                            print(f"[POKERTOOL] ✓ Previous instance terminated gracefully")

                    except ProcessLookupError:
                        pass  # Process already gone
                    except PermissionError:
                        print(f"⚠️  Cannot terminate PID {stored_pid} (permission denied)")
                        return None, stored_pid
                    except Exception as e:
                        print(f"⚠️  Error terminating PID {stored_pid}: {e}")
                        return None, stored_pid
                else:
                    # Original behavior - don't force cleanup
                    return None, stored_pid

            # Remove stale or cleaned-up lock file
            try:
                lock_path.unlink()
            except OSError:
                pass

        # Acquire lock for this instance
        lock_path.write_text(str(os.getpid()))
        return lock_path, None
    except OSError as exc:
        print(f"⚠️  Could not manage lock file {lock_path}: {exc}")
        return None, None


def release_lock(lock_path: Optional[Path]) -> None:
    """Remove the lock file if it still exists."""
    if not lock_path:
        return

    try:
        if lock_path.exists():
            lock_path.unlink()
    except OSError as exc:
        print(f"⚠️  Could not remove lock file {lock_path}: {exc}")


__all__ = ["acquire_lock", "release_lock"]
