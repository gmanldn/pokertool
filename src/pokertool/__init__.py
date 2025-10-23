#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool   Init   Module
===========================

This module provides functionality for   init   operations
within the PokerTool application ecosystem.

Module: pokertool.__init__
Version: 101.0.0
Last Modified: 2025-10-23
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v101.0.0 (2025-10-23): Program History Database & Regression Prevention System
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '102.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/__init__.py
# version: v101.0.0
# last_commit: '2025-10-23T00:00:00+01:00'
# fixes:
# - date: '2025-10-23'
#   summary: Program History Database and comprehensive Regression Prevention System
# ---
# POKERTOOL-HEADER-END
"""
pokertool package — stable API surface.
"""
# Re-export commonly-used symbols if present in core.
try:
    from .core import analyse_hand, Card  # type: ignore[attr-defined]
except Exception:
    # If not present, expose nothing; users / tests can still import .core directly.
    pass
