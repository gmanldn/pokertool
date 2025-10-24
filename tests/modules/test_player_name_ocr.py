"""Tests for enhanced player name OCR."""

import pytest
import numpy as np
import cv2
from pokertool.player_name_ocr import PlayerNameOCR


class TestPlayerNameOCR:
    """Test player name OCR functionality."""

    def mock_ocr(self, image):
        """Mock OCR function for testing."""
        return "Player123"

    def test_extract_player_name_basic(self):
        """Test basic player name extraction."""
        ocr = PlayerNameOCR()
        image = np.zeros((50, 200, 3), dtype=np.uint8)
        image[:] = (255, 255, 255)

        name, conf = ocr.extract_player_name(image, self.mock_ocr)
        assert name == "Player123"
        assert conf >= 0.95

    def test_clean_name_special_chars(self):
        """Test cleaning special characters."""
        ocr = PlayerNameOCR()
        cleaned = ocr._clean_name("P!@#layer$%^123&*(")
        assert cleaned == "Player123"

    def test_clean_name_whitespace(self):
        """Test cleaning extra whitespace."""
        ocr = PlayerNameOCR()
        cleaned = ocr._clean_name("  Player   123  ")
        assert cleaned == "Player 123"

    def test_confidence_calculation_valid_name(self):
        """Test confidence for valid name."""
        ocr = PlayerNameOCR()
        conf = ocr._calculate_confidence("Player123")
        assert conf >= 0.95

    def test_confidence_calculation_short_name(self):
        """Test confidence for short name."""
        ocr = PlayerNameOCR()
        conf = ocr._calculate_confidence("AB")
        assert conf < 0.95

    def test_confidence_calculation_empty(self):
        """Test confidence for empty name."""
        ocr = PlayerNameOCR()
        conf = ocr._calculate_confidence("")
        assert conf == 0.0

    def test_preprocess_adaptive(self):
        """Test adaptive preprocessing."""
        ocr = PlayerNameOCR()
        image = np.random.randint(0, 255, (50, 200, 3), dtype=np.uint8)
        result = ocr._preprocess_adaptive(image)
        assert result.shape == (50, 200)

    def test_preprocess_contrast(self):
        """Test contrast preprocessing."""
        ocr = PlayerNameOCR()
        image = np.random.randint(0, 255, (50, 200, 3), dtype=np.uint8)
        result = ocr._preprocess_contrast(image)
        assert result.shape == (50, 200)

    def test_preprocess_denoise(self):
        """Test denoise preprocessing."""
        ocr = PlayerNameOCR()
        image = np.random.randint(0, 255, (50, 200, 3), dtype=np.uint8)
        result = ocr._preprocess_denoise(image)
        assert result.shape == (50, 200)

    def test_extract_with_roi(self):
        """Test extraction with ROI."""
        ocr = PlayerNameOCR()
        image = np.zeros((200, 400, 3), dtype=np.uint8)
        roi = (50, 50, 150, 100)

        name, conf = ocr.extract_player_name(image, self.mock_ocr, roi=roi)
        assert isinstance(name, str)
        assert 0.0 <= conf <= 1.0
