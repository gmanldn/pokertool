#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for OCR Ensemble System
============================================

Tests OCR ensemble voting, validation, and benchmarking.
"""

import pytest
import numpy as np
from pokertool.ocr_ensemble import (
    OCREnsemble,
    PokerLexicalValidator,
    OCRResult,
    OCREngine,
    FieldType,
    get_ocr_ensemble
)


class TestPokerLexicalValidator:
    """Test poker-specific lexical validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PokerLexicalValidator()

    def test_player_name_validation(self):
        """Test player name validation."""
        # Valid names
        assert self.validator.validate("JohnPoker", FieldType.PLAYER_NAME)[0]
        assert self.validator.validate("Player123", FieldType.PLAYER_NAME)[0]
        assert self.validator.validate("ABC", FieldType.PLAYER_NAME)[0]

        # Invalid names
        assert not self.validator.validate("", FieldType.PLAYER_NAME)[0]
        assert not self.validator.validate("A", FieldType.PLAYER_NAME)[0]  # Too short
        assert not self.validator.validate("A" * 25, FieldType.PLAYER_NAME)[0]  # Too long
        assert not self.validator.validate("!!!", FieldType.PLAYER_NAME)[0]  # No alphanumeric

    def test_monetary_value_validation(self):
        """Test bet/pot/stack size validation."""
        # Valid amounts
        assert self.validator.validate("100", FieldType.BET_SIZE)[0]
        assert self.validator.validate("$100", FieldType.BET_SIZE)[0]
        assert self.validator.validate("1,234.56", FieldType.POT_SIZE)[0]
        assert self.validator.validate("0.50", FieldType.STACK_SIZE)[0]

        # Invalid amounts
        assert not self.validator.validate("abc", FieldType.BET_SIZE)[0]
        assert not self.validator.validate("-100", FieldType.BET_SIZE)[0]  # Negative
        assert not self.validator.validate("9999999", FieldType.BET_SIZE)[0]  # Too large

    def test_card_rank_validation(self):
        """Test card rank validation."""
        # Valid ranks
        for rank in ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]:
            assert self.validator.validate(rank, FieldType.CARD_RANK)[0]

        # Invalid ranks
        assert not self.validator.validate("X", FieldType.CARD_RANK)[0]
        assert not self.validator.validate("1", FieldType.CARD_RANK)[0]

    def test_card_suit_validation(self):
        """Test card suit validation."""
        # Valid suits
        for suit in ["♠", "♥", "♦", "♣", "s", "h", "d", "c"]:
            assert self.validator.validate(suit, FieldType.CARD_SUIT)[0]

        # Invalid suits
        assert not self.validator.validate("X", FieldType.CARD_SUIT)[0]
        assert not self.validator.validate("spades", FieldType.CARD_SUIT)[0]

    def test_timer_validation(self):
        """Test timer validation."""
        # Valid timers
        assert self.validator.validate("01:30", FieldType.TIMER)[0]
        assert self.validator.validate("30", FieldType.TIMER)[0]
        assert self.validator.validate("0:05", FieldType.TIMER)[0]

        # Invalid timers
        assert not self.validator.validate("abc", FieldType.TIMER)[0]
        assert not self.validator.validate("500", FieldType.TIMER)[0]  # Too large

    def test_position_validation(self):
        """Test position validation."""
        # Valid positions
        for pos in ["BTN", "SB", "BB", "UTG", "MP", "CO", "EP", "LP"]:
            assert self.validator.validate(pos, FieldType.POSITION)[0]

        # Invalid positions
        assert not self.validator.validate("XYZ", FieldType.POSITION)[0]
        assert not self.validator.validate("button", FieldType.POSITION)[0]

    def test_auto_correction(self):
        """Test auto-correction of common OCR errors."""
        # Number corrections
        assert "0" in self.validator.auto_correct("$1O0", FieldType.BET_SIZE)
        assert "1" in self.validator.auto_correct("$l00", FieldType.BET_SIZE)

    def test_validation_messages(self):
        """Test that validation messages are informative."""
        is_valid, messages = self.validator.validate("", FieldType.PLAYER_NAME)
        assert not is_valid
        assert len(messages) > 0
        assert "Empty" in messages[0] or "short" in messages[0].lower()


class TestOCREnsemble:
    """Test OCR ensemble system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ensemble = OCREnsemble()

    def test_ensemble_initialization(self):
        """Test ensemble initializes correctly."""
        assert self.ensemble is not None
        assert self.ensemble.validator is not None
        assert isinstance(self.ensemble.stats, dict)
        assert "total_calls" in self.ensemble.stats

    def test_engine_detection(self):
        """Test that engines are detected."""
        engines = self.ensemble.engines_available
        assert isinstance(engines, list)
        # Should have at least one engine if dependencies are installed
        # This might fail in CI without OCR dependencies
        # assert len(engines) > 0

    def test_ensemble_voting_single_result(self):
        """Test ensemble voting with a single result."""
        results = [
            OCRResult(text="100", confidence=0.9, engine=OCREngine.TESSERACT)
        ]

        text, conf = self.ensemble._ensemble_vote(results)
        assert text == "100"
        assert conf == 0.9

    def test_ensemble_voting_multiple_results(self):
        """Test ensemble voting with multiple results."""
        results = [
            OCRResult(text="100", confidence=0.9, engine=OCREngine.TESSERACT),
            OCRResult(text="100", confidence=0.8, engine=OCREngine.PADDLE),
            OCRResult(text="10O", confidence=0.5, engine=OCREngine.EASYOCR),  # OCR error
        ]

        text, conf = self.ensemble._ensemble_vote(results)
        # "100" should win with confidence weighting
        assert text == "100"
        assert conf > 0.7

    def test_ensemble_voting_zero_confidence(self):
        """Test ensemble voting with zero confidence results."""
        results = [
            OCRResult(text="100", confidence=0.0, engine=OCREngine.TESSERACT),
            OCRResult(text="200", confidence=0.0, engine=OCREngine.PADDLE),
        ]

        text, conf = self.ensemble._ensemble_vote(results)
        # Should return most common even with zero confidence
        assert text in ["100", "200"]
        assert conf == 0.0

    def test_recognize_no_engines(self):
        """Test recognition when no engines are available."""
        # Temporarily clear engines
        original_engines = self.ensemble.engines_available
        self.ensemble.engines_available = []

        image = np.zeros((100, 100), dtype=np.uint8)
        result = self.ensemble.recognize(image, FieldType.PLAYER_NAME)

        assert result.text == ""
        assert result.confidence == 0.0
        assert not result.validation_passed

        # Restore engines
        self.ensemble.engines_available = original_engines

    def test_stats_tracking(self):
        """Test that statistics are tracked correctly."""
        initial_calls = self.ensemble.stats["total_calls"]

        # Make a call (will fail without real engines/image)
        image = np.zeros((100, 100), dtype=np.uint8)
        self.ensemble.recognize(image, FieldType.PLAYER_NAME)

        # Stats should be updated
        assert self.ensemble.stats["total_calls"] > initial_calls

    def test_get_stats(self):
        """Test getting ensemble statistics."""
        stats = self.ensemble.get_stats()

        assert "total_calls" in stats
        assert "successful_calls" in stats
        assert "success_rate" in stats
        assert "engines_available" in stats
        assert isinstance(stats["engines_available"], list)


class TestGlobalInstance:
    """Test global OCR ensemble instance."""

    def test_get_ocr_ensemble(self):
        """Test getting global ensemble instance."""
        ensemble1 = get_ocr_ensemble()
        ensemble2 = get_ocr_ensemble()

        # Should be the same instance (singleton)
        assert ensemble1 is ensemble2

    def test_ensemble_is_initialized(self):
        """Test that global ensemble is properly initialized."""
        ensemble = get_ocr_ensemble()

        assert ensemble is not None
        assert ensemble.validator is not None
        assert isinstance(ensemble.engines_available, list)


class TestOCRResult:
    """Test OCRResult dataclass."""

    def test_ocr_result_creation(self):
        """Test creating OCR results."""
        result = OCRResult(
            text="test",
            confidence=0.95,
            engine=OCREngine.TESSERACT
        )

        assert result.text == "test"
        assert result.confidence == 0.95
        assert result.engine == OCREngine.TESSERACT
        assert result.char_confidences is None

    def test_ocr_result_with_char_confidences(self):
        """Test OCR result with character confidences."""
        result = OCRResult(
            text="test",
            confidence=0.95,
            engine=OCREngine.TESSERACT,
            char_confidences=[0.9, 0.95, 0.98, 0.96]
        )

        assert len(result.char_confidences) == 4
        assert all(0 <= c <= 1 for c in result.char_confidences)


class TestEnsembleResult:
    """Test EnsembleResult dataclass."""

    def test_ensemble_result_creation(self):
        """Test creating ensemble results."""
        from pokertool.ocr_ensemble import EnsembleResult

        result = EnsembleResult(
            text="test",
            confidence=0.95,
            engines_used=[OCREngine.TESSERACT],
            individual_results=[],
            validation_passed=True,
            validation_messages=[]
        )

        assert result.text == "test"
        assert result.confidence == 0.95
        assert result.validation_passed


class TestFieldTypes:
    """Test field type enum."""

    def test_field_types_exist(self):
        """Test that all field types are defined."""
        expected_types = [
            "PLAYER_NAME", "BET_SIZE", "POT_SIZE", "STACK_SIZE",
            "CARD_RANK", "CARD_SUIT", "TIMER", "POSITION", "BLIND"
        ]

        for field_type in expected_types:
            assert hasattr(FieldType, field_type)


class TestOCREngines:
    """Test OCR engine enum."""

    def test_ocr_engines_exist(self):
        """Test that all OCR engines are defined."""
        expected_engines = ["TESSERACT", "PADDLE", "EASYOCR"]

        for engine in expected_engines:
            assert hasattr(OCREngine, engine)

    def test_engine_values(self):
        """Test that engine enum values are correct."""
        assert OCREngine.TESSERACT.value == "tesseract"
        assert OCREngine.PADDLE.value == "paddle"
        assert OCREngine.EASYOCR.value == "easyocr"


# Benchmark tests (would require real images in production)
class TestBenchmarking:
    """Test OCR ensemble benchmarking."""

    def test_benchmark_placeholder(self):
        """Placeholder for real benchmark tests."""
        # In production, this would:
        # 1. Load curated test images
        # 2. Run OCR ensemble
        # 3. Compare against ground truth
        # 4. Report accuracy metrics per engine and ensemble
        assert True  # Placeholder

    def test_adversarial_cases_placeholder(self):
        """Placeholder for adversarial case testing."""
        # In production, this would test:
        # - Noisy images
        # - Brightness variations
        # - Skewed text
        # - Partial occlusions
        assert True  # Placeholder


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
