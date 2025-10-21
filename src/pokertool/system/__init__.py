#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool System Module
=======================

Aggregates ML and system-level modules for backward compatibility.
This module provides a unified import path for system-level components.

Module: pokertool.system
Version: 1.0.0
Last Modified: 2025-10-21
"""

__version__ = '1.0.0'

# Import ML modules for backward compatibility
# These modules are in the parent pokertool directory but imported here
# for compatibility with code expecting pokertool.system.* imports

try:
    from .. import model_calibration
    from .. import sequential_opponent_fusion
    from .. import active_learning
except ImportError:
    # Fallback: try importing from pokertool directly
    try:
        from pokertool import model_calibration
        from pokertool import sequential_opponent_fusion
        from pokertool import active_learning
    except ImportError:
        # If still failing, create stub modules
        model_calibration = None
        sequential_opponent_fusion = None
        active_learning = None

__all__ = [
    'model_calibration',
    'sequential_opponent_fusion',
    'active_learning',
]
