#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PokerOCR amount selection heuristics.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pokertool.ocr_recognition import PokerOCR  # noqa: E402


class PokerOCRAmountSelectionTests(unittest.TestCase):
    """Validate heuristics that choose between Tesseract and EasyOCR amounts."""

    def setUp(self):
        # Bypass heavy initialization (cv2/easyocr) by constructing without __init__
        self.ocr = PokerOCR.__new__(PokerOCR)

    def test_is_amount_suspicious_detects_missing_decimal(self):
        self.assertTrue(self.ocr._is_amount_suspicious(276, "276"))

    def test_is_amount_suspicious_accepts_decimal_amount(self):
        self.assertFalse(self.ocr._is_amount_suspicious(2.76, "€2.76"))

    def test_prefer_easyocr_when_orders_of_magnitude_apart(self):
        should_switch = self.ocr._should_prefer_easyocr(
            tess_amount=276.0,
            easy_amount=2.76,
            tess_text="276",
            easy_text="€2,76",
            easy_confidence=0.80,
        )
        self.assertTrue(should_switch)

    def test_retain_tesseract_when_amounts_match(self):
        should_switch = self.ocr._should_prefer_easyocr(
            tess_amount=15.25,
            easy_amount=15.25,
            tess_text="15.25",
            easy_text="15.25",
            easy_confidence=0.90,
        )
        self.assertFalse(should_switch)


if __name__ == "__main__":
    unittest.main()
