#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for OCRPostProcessor.clean_amount handling of micro-stakes formats.

Focuses on ensuring European decimal commas are normalized correctly so that
€0,01 and €0,02 tables do not appear as €1.00 or €2.00 stacks.
"""

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pokertool.scraping_accuracy_system import OCRPostProcessor  # noqa: E402


class TestOCRPostProcessorAmountCleaning(unittest.TestCase):
    """Verify amount cleaning for various currency formats."""

    def setUp(self):
        self.processor = OCRPostProcessor()

    def test_micro_stakes_decimal_comma(self):
        """Ensure €0,02 normalizes to 0.02 rather than 2.00."""
        self.assertEqual(self.processor.clean_amount("€0,02"), "0.02")
        self.assertEqual(self.processor.clean_amount("0,01€"), "0.01")

    def test_large_european_amount(self):
        """European thousand separators should be removed safely."""
        self.assertEqual(self.processor.clean_amount("1.234,56€"), "1234.56")

    def test_us_format_amount(self):
        """Standard US formatted amounts should remain unchanged."""
        self.assertEqual(self.processor.clean_amount("$1,234.50"), "1234.50")

    def test_noise_and_ocr_errors(self):
        """OCR artifacts like O for 0 should be corrected."""
        self.assertEqual(self.processor.clean_amount("$SO.OO"), "50.00")
        self.assertEqual(self.processor.clean_amount("  o,50  "), "0.50")


if __name__ == "__main__":
    unittest.main()
