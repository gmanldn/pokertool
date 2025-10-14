#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test utilities for PokerTool

Provides utilities to suppress GUI dialogs during testing while still logging errors.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_test_mode() -> bool:
    """Check if running in test mode."""
    return bool(os.environ.get('POKERTOOL_TEST_MODE'))


def safe_messagebox_showerror(title: str, message: str, parent=None):
    """Show error dialog, or just log if in test mode."""
    if is_test_mode():
        logger.error(f"{title}: {message}")
        return

    try:
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=parent)
    except Exception as e:
        logger.error(f"Failed to show error dialog: {e}")
        logger.error(f"{title}: {message}")


def safe_messagebox_showwarning(title: str, message: str, parent=None):
    """Show warning dialog, or just log if in test mode."""
    if is_test_mode():
        logger.warning(f"{title}: {message}")
        return

    try:
        from tkinter import messagebox
        messagebox.showwarning(title, message, parent=parent)
    except Exception as e:
        logger.warning(f"Failed to show warning dialog: {e}")
        logger.warning(f"{title}: {message}")


def safe_messagebox_showinfo(title: str, message: str, parent=None):
    """Show info dialog, or just log if in test mode."""
    if is_test_mode():
        logger.info(f"{title}: {message}")
        return

    try:
        from tkinter import messagebox
        messagebox.showinfo(title, message, parent=parent)
    except Exception as e:
        logger.info(f"Failed to show info dialog: {e}")
        logger.info(f"{title}: {message}")
