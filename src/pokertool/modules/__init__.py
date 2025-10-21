#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Modules Package
==========================

Contains various poker-related modules and utilities.
This package aggregates poker screen scrapers, analyzers, and other tools.

Module: pokertool.modules
Version: 1.0.0
Last Modified: 2025-10-21
"""

__version__ = '1.0.0'

# Import nash_solver from parent package for backward compatibility
try:
    from .. import nash_solver
except ImportError:
    try:
        from pokertool import nash_solver
    except ImportError:
        nash_solver = None

__all__ = [
    'nash_solver',
]
