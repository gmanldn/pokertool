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
    """Log error message (GUI dialogs removed in web-only architecture)."""
    logger.error(f"{title}: {message}")


def safe_messagebox_showwarning(title: str, message: str, parent=None):
    """Log warning message (GUI dialogs removed in web-only architecture)."""
    logger.warning(f"{title}: {message}")


def safe_messagebox_showinfo(title: str, message: str, parent=None):
    """Log info message (GUI dialogs removed in web-only architecture)."""
    logger.info(f"{title}: {message}")
