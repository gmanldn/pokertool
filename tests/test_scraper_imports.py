#!/usr/bin/env python3
"""Test suite for screen scraper import functionality."""

import pytest
import sys


class TestScraperImports:
    """Tests for screen scraper module imports and basic functionality."""

    def test_numpy_import(self):
        """Test that numpy can be imported successfully."""
        try:
            import numpy as np
            assert np is not None
            assert hasattr(np, '__version__')
        except ImportError as e:
            pytest.fail(f"Failed to import numpy: {e}")

    def test_scraper_module_import(self):
        """Test that screen scraper modules can be imported."""
        try:
            from pokertool.modules.poker_screen_scraper import (
                PokerScreenScraper,
                PokerSite,
                TableState,
                create_scraper,
            )
            assert PokerScreenScraper is not None
            assert PokerSite is not None
            assert TableState is not None
            assert create_scraper is not None
        except ImportError as e:
            pytest.fail(f"Failed to import screen scraper modules: {e}")

    @pytest.mark.xfail(
        reason="Scraper creation requires tesseract and other dependencies that may not be installed",
        strict=False
    )
    def test_scraper_creation(self):
        """Test that a scraper instance can be created.

        This test is marked as xfail because it requires tesseract and other
        dependencies that may not be available in all environments.
        """
        from pokertool.modules.poker_screen_scraper import create_scraper

        try:
            scraper = create_scraper('BETFAIR')
            assert scraper is not None
            assert hasattr(scraper, 'capture_table')
            assert hasattr(scraper, 'analyze_table')
        except RuntimeError as e:
            if "dependencies not available" in str(e):
                pytest.skip(f"Skipping due to missing dependencies: {e}")
            else:
                raise
