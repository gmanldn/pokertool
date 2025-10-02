#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced GUI style constants.

Provides centralized color and font definitions so that individual widgets can
share a consistent visual language without duplicating values.
"""

from __future__ import annotations

COLORS = {
    "bg_dark": "#1a1f2e",
    "bg_medium": "#2a3142",
    "bg_light": "#3a4152",
    "accent_primary": "#4a9eff",
    "accent_success": "#4ade80",
    "accent_warning": "#fbbf24",
    "accent_danger": "#ef4444",
    "autopilot_active": "#00ff00",
    "autopilot_inactive": "#ff4444",
    "autopilot_standby": "#ffaa00",
    "text_primary": "#ffffff",
    "text_secondary": "#94a3b8",
    "table_felt": "#0d3a26",
    "table_border": "#2a7f5f",
    "dealer_button": "#FFD700",
    "small_blind": "#FFA500",
    "big_blind": "#DC143C",
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
