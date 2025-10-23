#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Blind and Ante Detection Module

Detects small blind, big blind, and ante amounts from poker table UI.
"""

import re
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BlindAnteDetector:
    """Detects blind and ante amounts from table UI text."""

    def __init__(self):
        """Initialize detector with common patterns."""
        # Patterns to match blind/ante text
        self.blind_patterns = [
            r'(?:SB|Small Blind)[\s:]*\$?(\d+(?:\.\d{2})?)',
            r'(?:BB|Big Blind)[\s:]*\$?(\d+(?:\.\d{2})?)',
            r'Blinds[\s:]*\$?(\d+(?:\.\d{2})?)[\s/]+\$?(\d+(?:\.\d{2})?)',
        ]
        self.ante_patterns = [
            r'Ante[\s:]*\$?(\d+(?:\.\d{2})?)',
            r'A[\s:]*\$?(\d+(?:\.\d{2})?)',
        ]

    def detect_blinds(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Detect small blind and big blind from text.

        Args:
            text: UI text containing blind information

        Returns:
            Tuple of (small_blind, big_blind) or None if not detected
        """
        text = text.strip()

        # Try "Blinds: $1/$2" format
        match = re.search(r'Blinds[\s:]*\$?(\d+(?:\.\d{2})?)[\s/]+\$?(\d+(?:\.\d{2})?)', text, re.IGNORECASE)
        if match:
            sb = float(match.group(1))
            bb = float(match.group(2))
            logger.debug(f"Detected blinds: SB=${sb}, BB=${bb}")
            return (sb, bb)

        # Try separate SB/BB detection
        sb_match = re.search(r'(?:SB|Small Blind)[\s:]*\$?(\d+(?:\.\d{2})?)', text, re.IGNORECASE)
        bb_match = re.search(r'(?:BB|Big Blind)[\s:]*\$?(\d+(?:\.\d{2})?)', text, re.IGNORECASE)

        if sb_match and bb_match:
            sb = float(sb_match.group(1))
            bb = float(bb_match.group(1))
            logger.debug(f"Detected blinds: SB=${sb}, BB=${bb}")
            return (sb, bb)

        logger.debug("No blinds detected in text")
        return None

    def detect_ante(self, text: str) -> Optional[float]:
        """
        Detect ante amount from text.

        Args:
            text: UI text containing ante information

        Returns:
            Ante amount or None if not detected
        """
        text = text.strip()

        for pattern in self.ante_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                ante = float(match.group(1))
                logger.debug(f"Detected ante: ${ante}")
                return ante

        logger.debug("No ante detected in text")
        return None

    def detect_all(self, text: str) -> Dict[str, Any]:
        """
        Detect all blind and ante information from text.

        Args:
            text: UI text containing game information

        Returns:
            Dict with keys: small_blind, big_blind, ante (values or None)
        """
        blinds = self.detect_blinds(text)
        ante = self.detect_ante(text)

        result = {
            'small_blind': blinds[0] if blinds else None,
            'big_blind': blinds[1] if blinds else None,
            'ante': ante
        }

        logger.info(f"Detection result: {result}")
        return result

    def get_stake_level(self, small_blind: float, big_blind: float) -> str:
        """
        Get human-readable stake level.

        Args:
            small_blind: Small blind amount
            big_blind: Big blind amount

        Returns:
            Stake level string (e.g., "$1/$2", "$0.50/$1")
        """
        return f"${small_blind:.2f}/${big_blind:.2f}".replace('.00', '')


# Global detector instance
_detector_instance: Optional[BlindAnteDetector] = None


def get_blind_ante_detector() -> BlindAnteDetector:
    """Get or create global blind/ante detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = BlindAnteDetector()
    return _detector_instance


__all__ = ['BlindAnteDetector', 'get_blind_ante_detector']
