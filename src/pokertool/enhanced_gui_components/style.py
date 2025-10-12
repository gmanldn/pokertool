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

    # Button colors
    "button_bg": "#3b82f6",        # Button background (primary blue)
    "button_fg": "#f8fafc",        # Button text (near white)
    "button_active": "#2563eb",    # Button active state (darker blue)

    # Semantic colors (aliases for convenience)
    "accent": "#3b82f6",           # Primary accent (blue)
    "success": "#10b981",          # Success (green)
    "danger": "#ef4444",           # Danger (red)
}

FONTS = {
    "title": ("Arial", 22, "bold"),         # Reduced from 28
    "heading": ("Arial", 14, "bold"),       # Reduced from 18
    "subheading": ("Arial", 11, "bold"),    # Reduced from 14
    "section": ("Arial", 13, "bold"),       # Reduced from 16
    "body": ("Arial", 11, "bold"),          # Reduced from 14
    "button": ("Arial", 10, "bold"),        # Reduced from 12
    "small": ("Arial", 9),                  # Reduced from 11
    "autopilot": ("Arial", 16, "bold"),     # Reduced from 20
    "status": ("Arial", 13, "bold"),        # Reduced from 16
    "analysis": ("Consolas", 10, "bold"),   # Reduced from 12
    "mono": ("Courier New", 9),             # Reduced from 11
}

__all__ = ["COLORS", "FONTS"]
