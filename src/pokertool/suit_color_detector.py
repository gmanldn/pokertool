#!/usr/bin/env python3
"""Suit detection fallback using color analysis."""

import numpy as np
from typing import Optional

class SuitColorDetector:
    """Detect card suit by color when OCR fails."""

    def detect_suit_by_color(self, card_image: np.ndarray) -> Optional[str]:
        """
        Detect suit from card color.

        Args:
            card_image: Card image array (RGB)

        Returns:
            's' or 'c' for black suits, 'h' or 'd' for red suits, or None
        """
        if card_image is None or card_image.size == 0:
            return None

        # Get average color
        avg_color = np.mean(card_image, axis=(0, 1))
        r, g, b = avg_color

        # Red suit if red channel dominant
        if r > g + 30 and r > b + 30:
            return 'h'  # Default to hearts for red (could be diamonds)

        # Black suit if red channel low
        if r < 100 and g < 100 and b < 100:
            return 's'  # Default to spades for black (could be clubs)

        return None


_detector_instance: Optional[SuitColorDetector] = None

def get_suit_color_detector() -> SuitColorDetector:
    """Get global suit color detector."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SuitColorDetector()
    return _detector_instance
