#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEMPLATE for creating tab builder mixins.

This file shows the pattern to follow when creating new tab builders.
Copy this template and replace TABNAME with your actual tab name.

Steps:
1. Copy this file to the appropriate name (e.g., analytics_tab.py)
2. Replace all TABNAME placeholders with your tab name
3. Extract the relevant _build_*_tab() method from enhanced_gui.py
4. Extract any helper methods used by that tab
5. Update the imports at the top
6. Update __all__ at the bottom
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from ..style import COLORS, FONTS


class TABNAMETabMixin:
    """
    Mixin class providing TABNAME tab building.
    
    This mixin should be inherited by the main application class.
    It provides the _build_TABNAME_tab() method and any supporting methods.
    """
    
    def _build_TABNAME_tab(self, parent: tk.Frame) -> None:
        """
        Build the TABNAME tab.
        
        Args:
            parent: The parent frame (usually from ttk.Notebook)
        """
        # TODO: Extract tab building code from enhanced_gui.py
        pass
    
    # Add any helper methods that are specific to this tab
    # For example:
    
    def _helper_method_for_TABNAME(self) -> None:
        """Helper method specific to TABNAME tab."""
        pass


__all__ = ["TABNAMETabMixin"]


# EXAMPLE: How to use this template for Analytics tab:
# 
# 1. Copy this file to: tabs/analytics_tab.py
# 2. Replace TABNAME with Analytics everywhere
# 3. Extract _build_analytics_tab() from enhanced_gui.py
# 4. Extract supporting methods like:
#    - _refresh_analytics_metrics()
#    - _record_sample_event()
#    - _record_sample_session()
# 5. Make sure to:
#    - Import pokertool.i18n.translate if needed
#    - Import any analytics classes (AnalyticsDashboard, UsageEvent, etc.)
#    - Keep the class as a mixin (inherit from nothing except object)
# 6. Update __all__ = ["AnalyticsTabMixin"]
