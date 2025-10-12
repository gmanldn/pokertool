#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced GUI style constants.

Provides centralized color and font definitions so that individual widgets can
share a consistent visual language without duplicating values.
"""

from __future__ import annotations

COLORS = {
    # Modern dark theme with deeper contrasts
    "bg_dark": "#0f172a",          # Deeper dark blue-gray
    "bg_medium": "#1e293b",        # Medium slate
    "bg_light": "#334155",         # Lighter slate
    "bg_card": "#1e293b",          # Card background

    # Modern vibrant accent colors
    "accent_primary": "#3b82f6",   # Modern blue
    "accent_success": "#10b981",   # Modern green
    "accent_warning": "#f59e0b",   # Modern amber
    "accent_danger": "#ef4444",    # Modern red
    "accent_info": "#06b6d4",      # Modern cyan
    "accent_purple": "#8b5cf6",    # Modern purple

    # Status colors
    "autopilot_active": "#10b981",
    "autopilot_inactive": "#ef4444",
    "autopilot_standby": "#f59e0b",

    # Text colors
    "text_primary": "#f8fafc",     # Near white
    "text_secondary": "#94a3b8",   # Muted blue-gray
    "text_muted": "#64748b",       # Very muted

    # Poker table colors
    "table_felt": "#0d3a26",
    "table_border": "#2a7f5f",
    "dealer_button": "#fbbf24",
    "small_blind": "#f97316",
    "big_blind": "#dc2626",

    # Modern UI elements
    "border": "#334155",           # Border color
    "hover": "#475569",            # Hover state
    "selected": "#3b82f6",         # Selected state
}

FONTS = {
    "title": ("Arial", 28, "bold"),
    "heading": ("Arial", 18, "bold"),
    "subheading": ("Arial", 14, "bold"),
    "body": ("Arial", 14, "bold"),
    "autopilot": ("Arial", 20, "bold"),
    "status": ("Arial", 16, "bold"),
    "analysis": ("Consolas", 12, "bold"),
}

__all__ = ["COLORS", "FONTS"]
