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


def acquire_lock(app_name: str = _DEFAULT_APP_NAME) -> Tuple[Optional[Path], Optional[int]]:
    """
    Attempt to acquire the single-instance lock.

    Returns a tuple of (lock_path, existing_pid). If lock_path is None and
    existing_pid is not None, another process already holds the lock. If both
    values are None, an unexpected filesystem error occurred.
    """
    lock_path = _lock_path(app_name)

    try:
        if lock_path.exists():
            try:
                stored_pid = int(lock_path.read_text().strip())
            except (OSError, ValueError):
                stored_pid = None

            if stored_pid and _pid_is_running(stored_pid):
                return None, stored_pid

            try:
                lock_path.unlink()
            except OSError:
                pass

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
