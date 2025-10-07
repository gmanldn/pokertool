#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analysis tab builder for the integrated poker assistant.
"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from ..style import COLORS, FONTS


class AnalysisTabMixin:
    """Mixin class providing analysis tab building."""
    
    def _build_analysis_tab(self, parent: tk.Frame) -> None:
        """Build analysis and statistics tab."""
        from pokertool.i18n import translate
        
        analysis_label = tk.Label(
            parent,
            text=translate('analysis.title'),
            font=FONTS['title'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary']
        )
        analysis_label.pack(pady=20)
        self._register_widget_translation(analysis_label, 'analysis.title')

        # Analysis output
        analysis_output = tk.Text(
            parent,
            font=FONTS['analysis'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_primary'],
            wrap='word',
            height=20
        )
        analysis_output.pack(fill='both', expand=True, padx=20, pady=20)


__all__ = ["AnalysisTabMixin"]
