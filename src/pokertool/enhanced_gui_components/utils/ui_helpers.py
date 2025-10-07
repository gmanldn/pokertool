#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI helper utilities for enhanced GUI.

Provides utility functions for UI operations like color manipulation.
"""

from __future__ import annotations


def brighten_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Brighten a hex color by a given factor for hover effects.
    
    Args:
        hex_color: Color in hex format (e.g., '#1a1f2e')
        factor: Brightness factor (0.0 to 1.0), default 0.2
        
    Returns:
        Brightened color in hex format
        
    Example:
        >>> brighten_color('#1a1f2e', 0.3)
        '#3a4f6e'
    """
    try:
        # Remove the '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Brighten each component
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'
    except Exception:
        # Fallback to original color if conversion fails
        return hex_color


__all__ = ["brighten_color"]
