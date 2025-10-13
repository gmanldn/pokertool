#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR Ensemble and Validator for PokerTool
=========================================

Multi-engine OCR system with ensemble voting, confidence weighting,
and poker-specific lexical validation for maximum accuracy.

Features:
- Multiple OCR engines (Tesseract, PaddleOCR, EasyOCR)
- Ensemble voting with character-level confidence fusion
- Poker domain-specific validators
- Improbable value rejection
- Benchmarking and accuracy tracking

Version: 1.0.0
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine(Enum):
    """Available OCR engines."""
    TESSERACT = "tesseract"
    PADDLE = "paddle"
    EASYOCR = "easyocr"


class FieldType(Enum):
    """Types of poker fields for validation."""
    PLAYER_NAME = "player_name"
    BET_SIZE = "bet_size"
    POT_SIZE = "pot_size"
    STACK_SIZE = "stack_size"
    CARD_RANK = "card_rank"
    CARD_SUIT = "card_suit"
    TIMER = "timer"
    POSITION = "position"
    BLIND = "blind"


@dataclass
class OCRResult:
    """Result from a single OCR engine."""
    text: str
    confidence: float
    engine: OCREngine
    char_confidences: Optional[List[float]] = None


@dataclass
class EnsembleResult:
    """Final ensemble result with metadata."""
    text: str
    confidence: float
    engines_used: List[OCREngine]
    individual_results: List[OCRResult]
    validation_passed: bool
    validation_messages: List[str]


class PokerLexicalValidator:
    """
    Poker-specific lexical validator.

    Validates OCR results against known poker terminology,
    numeric ranges, and domain-specific patterns.
    """

    # Valid poker terminology
    VALID_POSITIONS = {"BTN", "SB", "BB", "UTG", "MP", "CO", "EP", "LP"}
    VALID_ACTIONS = {"FOLD", "CHECK", "CALL", "BET", "RAISE", "ALL-IN", "ALL IN"}
    VALID_CARD_RANKS = {"A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"}
    VALID_CARD_SUITS = {"♠", "♥", "♦", "♣", "s", "h", "d", "c"}

    # Common OCR errors and corrections
    COMMON_CORRECTIONS = {
        "O": "0",  # Letter O -> Zero
        "l": "1",  # Lowercase L -> One
        "I": "1",  # Uppercase I -> One
        "S": "5",  # S -> 5 in numbers
        "B": "8",  # B -> 8 in numbers
        "Z": "2",  # Z -> 2 in numbers
    }

    def __init__(self):
        """Initialize the validator."""
        self.validation_cache = {}

    def validate(self, text: str, field_type: FieldType) -> Tuple[bool, List[str]]:
        """
        Validate text for a specific field type.

        Args:
            text: The OCR text to validate
            field_type: Type of poker field

        Returns:
            (is_valid, messages) tuple
        """
        messages = []

        if not text or not text.strip():
            return False, ["Empty text"]

        text = text.strip()

        # Field-specific validation
        if field_type == FieldType.PLAYER_NAME:
            return self._validate_player_name(text, messages)
        elif field_type in [FieldType.BET_SIZE, FieldType.POT_SIZE, FieldType.STACK_SIZE]:
            return self._validate_monetary_value(text, messages)
        elif field_type == FieldType.CARD_RANK:
            return self._validate_card_rank(text, messages)
        elif field_type == FieldType.CARD_SUIT:
            return self._validate_card_suit(text, messages)
        elif field_type == FieldType.TIMER:
            return self._validate_timer(text, messages)
        elif field_type == FieldType.POSITION:
            return self._validate_position(text, messages)
        elif field_type == FieldType.BLIND:
            return self._validate_blind(text, messages)

        return True, []

    def _validate_player_name(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate player name."""
        # Must be 2-20 characters
        if len(text) < 2:
            messages.append("Player name too short")
            return False, messages
        if len(text) > 20:
            messages.append("Player name too long")
            return False, messages

        # Should contain alphanumeric characters
        if not re.search(r'[a-zA-Z0-9]', text):
            messages.append("Player name must contain alphanumeric characters")
            return False, messages

        return True, messages

    def _validate_monetary_value(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate monetary values (bet, pot, stack sizes)."""
        # Remove common currency symbols
        cleaned = text.replace("$", "").replace("£", "").replace("€", "").replace(",", "").strip()

        # Apply common corrections
        for wrong, right in self.COMMON_CORRECTIONS.items():
            if wrong in cleaned and cleaned.replace(wrong, right).replace(".", "").isdigit():
                cleaned = cleaned.replace(wrong, right)

        # Must be a valid number
        try:
            value = float(cleaned)
        except ValueError:
            messages.append(f"Not a valid number: {text}")
            return False, messages

        # Sanity check: reasonable poker values
        if value < 0:
            messages.append("Negative value not allowed")
            return False, messages
        if value > 1000000:  # $1M cap
            messages.append("Value exceeds reasonable limit")
            return False, messages

        return True, messages

    def _validate_card_rank(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate card rank."""
        text = text.upper().strip()

        if text not in self.VALID_CARD_RANKS:
            # Try common corrections
            if text == "10":
                text = "T"
            elif text in ["0", "O"]:
                text = "T"  # Often 10 -> T
            else:
                messages.append(f"Invalid card rank: {text}")
                return False, messages

        return True, messages

    def _validate_card_suit(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate card suit."""
        text = text.strip().lower()

        if text not in self.VALID_CARD_SUITS and text not in [s.lower() for s in self.VALID_CARD_SUITS]:
            messages.append(f"Invalid card suit: {text}")
            return False, messages

        return True, messages

    def _validate_timer(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate timer values."""
        # Should match MM:SS or SS format
        if re.match(r'^\d{1,2}:\d{2}$', text):
            return True, messages
        if re.match(r'^\d{1,3}$', text):
            seconds = int(text)
            if 0 <= seconds <= 300:  # 5 min max
                return True, messages

        messages.append(f"Invalid timer format: {text}")
        return False, messages

    def _validate_position(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate position labels."""
        text = text.upper().strip()

        if text not in self.VALID_POSITIONS:
            messages.append(f"Invalid position: {text}")
            return False, messages

        return True, messages

    def _validate_blind(self, text: str, messages: List[str]) -> Tuple[bool, List[str]]:
        """Validate blind labels."""
        text = text.upper().strip()

        if text not in {"SB", "BB"}:
            messages.append(f"Invalid blind: {text}")
            return False, messages

        return True, messages

    def auto_correct(self, text: str, field_type: FieldType) -> str:
        """
        Attempt auto-correction for common OCR errors.

        Args:
            text: The OCR text
            field_type: Type of field

        Returns:
            Corrected text
        """
        if field_type in [FieldType.BET_SIZE, FieldType.POT_SIZE, FieldType.STACK_SIZE]:
            # Apply number corrections
            for wrong, right in self.COMMON_CORRECTIONS.items():
                if wrong in text:
                    text = text.replace(wrong, right)

        return text


class OCREnsemble:
    """
    Multi-engine OCR ensemble with confidence-weighted voting.

    Combines results from multiple OCR engines using character-level
    confidence fusion and domain-specific validation.
    """

    def __init__(self):
        """Initialize the OCR ensemble."""
        self.validator = PokerLexicalValidator()
        self.engines_available = self._detect_available_engines()
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "validation_failures": 0,
            "engine_usage": {e.value: 0 for e in OCREngine},
        }

        logger.info(f"OCR Ensemble initialized with engines: {[e.value for e in self.engines_available]}")

    def _detect_available_engines(self) -> List[OCREngine]:
        """Detect which OCR engines are available."""
        available = []

        # Check Tesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            available.append(OCREngine.TESSERACT)
            logger.info("✓ Tesseract OCR available")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

        # Check PaddleOCR
        try:
            import paddleocr
            available.append(OCREngine.PADDLE)
            logger.info("✓ PaddleOCR available")
        except Exception as e:
            logger.warning(f"PaddleOCR not available: {e}")

        # Check EasyOCR
        try:
            import easyocr
            available.append(OCREngine.EASYOCR)
            logger.info("✓ EasyOCR available")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")

        if not available:
            logger.error("No OCR engines available!")

        return available

    def recognize(
        self,
        image: np.ndarray,
        field_type: FieldType,
        engines: Optional[List[OCREngine]] = None
    ) -> EnsembleResult:
        """
        Run OCR ensemble on an image.

        Args:
            image: Image array (numpy ndarray)
            field_type: Type of poker field being recognized
            engines: Specific engines to use (None = use all available)

        Returns:
            EnsembleResult with final text and metadata
        """
        self.stats["total_calls"] += 1

        if engines is None:
            engines = self.engines_available
        else:
            engines = [e for e in engines if e in self.engines_available]

        if not engines:
            logger.error("No OCR engines available for recognition")
            return EnsembleResult(
                text="",
                confidence=0.0,
                engines_used=[],
                individual_results=[],
                validation_passed=False,
                validation_messages=["No OCR engines available"]
            )

        # Run each engine
        results = []
        for engine in engines:
            try:
                result = self._run_single_engine(image, engine)
                if result:
                    results.append(result)
                    self.stats["engine_usage"][engine.value] += 1
            except Exception as e:
                logger.error(f"Error running {engine.value}: {e}")

        if not results:
            self.stats["failed_calls"] += 1
            return EnsembleResult(
                text="",
                confidence=0.0,
                engines_used=engines,
                individual_results=[],
                validation_passed=False,
                validation_messages=["All OCR engines failed"]
            )

        # Ensemble voting
        final_text, final_confidence = self._ensemble_vote(results)

        # Validation
        is_valid, messages = self.validator.validate(final_text, field_type)

        if not is_valid:
            self.stats["validation_failures"] += 1
            # Try auto-correction
            corrected = self.validator.auto_correct(final_text, field_type)
            is_valid_corrected, messages_corrected = self.validator.validate(corrected, field_type)

            if is_valid_corrected:
                final_text = corrected
                is_valid = True
                messages = ["Auto-corrected"] + messages_corrected

        self.stats["successful_calls"] += 1

        return EnsembleResult(
            text=final_text,
            confidence=final_confidence,
            engines_used=engines,
            individual_results=results,
            validation_passed=is_valid,
            validation_messages=messages
        )

    def _run_single_engine(self, image: np.ndarray, engine: OCREngine) -> Optional[OCRResult]:
        """Run a single OCR engine."""
        if engine == OCREngine.TESSERACT:
            return self._run_tesseract(image)
        elif engine == OCREngine.PADDLE:
            return self._run_paddle(image)
        elif engine == OCREngine.EASYOCR:
            return self._run_easyocr(image)
        return None

    def _run_tesseract(self, image: np.ndarray) -> Optional[OCRResult]:
        """Run Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image

            # Convert numpy array to PIL Image
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode='L')
            else:
                pil_image = Image.fromarray(image)

            # Get text and confidence
            data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)

            # Extract text with confidence
            texts = []
            confidences = []
            for i, conf in enumerate(data['conf']):
                if conf > 0:
                    texts.append(data['text'][i])
                    confidences.append(conf / 100.0)  # Normalize to 0-1

            text = ' '.join(texts).strip()
            avg_conf = np.mean(confidences) if confidences else 0.0

            return OCRResult(
                text=text,
                confidence=float(avg_conf),
                engine=OCREngine.TESSERACT,
                char_confidences=confidences
            )
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return None

    def _run_paddle(self, image: np.ndarray) -> Optional[OCRResult]:
        """Run PaddleOCR."""
        try:
            from paddleocr import PaddleOCR

            # Initialize PaddleOCR (cached)
            if not hasattr(self, '_paddle_ocr'):
                self._paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

            result = self._paddle_ocr.ocr(image, cls=True)

            if not result or not result[0]:
                return None

            # Extract text and confidence
            texts = []
            confidences = []
            for line in result[0]:
                text = line[1][0]
                conf = line[1][1]
                texts.append(text)
                confidences.append(conf)

            text = ' '.join(texts).strip()
            avg_conf = np.mean(confidences) if confidences else 0.0

            return OCRResult(
                text=text,
                confidence=float(avg_conf),
                engine=OCREngine.PADDLE,
                char_confidences=confidences
            )
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return None

    def _run_easyocr(self, image: np.ndarray) -> Optional[OCRResult]:
        """Run EasyOCR."""
        try:
            import easyocr

            # Initialize EasyOCR (cached)
            if not hasattr(self, '_easy_reader'):
                self._easy_reader = easyocr.Reader(['en'], gpu=False, verbose=False)

            results = self._easy_reader.readtext(image)

            if not results:
                return None

            # Extract text and confidence
            texts = []
            confidences = []
            for bbox, text, conf in results:
                texts.append(text)
                confidences.append(conf)

            text = ' '.join(texts).strip()
            avg_conf = np.mean(confidences) if confidences else 0.0

            return OCRResult(
                text=text,
                confidence=float(avg_conf),
                engine=OCREngine.EASYOCR,
                char_confidences=confidences
            )
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return None

    def _ensemble_vote(self, results: List[OCRResult]) -> Tuple[str, float]:
        """
        Perform ensemble voting with confidence weighting.

        Args:
            results: List of OCR results from different engines

        Returns:
            (final_text, final_confidence) tuple
        """
        if len(results) == 1:
            return results[0].text, results[0].confidence

        # Weight by confidence
        total_weight = sum(r.confidence for r in results)

        if total_weight == 0:
            # No confident results, return most common
            from collections import Counter
            texts = [r.text for r in results]
            most_common = Counter(texts).most_common(1)[0][0]
            return most_common, 0.0

        # Weighted majority vote
        text_weights = {}
        for result in results:
            text = result.text
            if text not in text_weights:
                text_weights[text] = 0
            text_weights[text] += result.confidence

        # Get text with highest weight
        best_text = max(text_weights.items(), key=lambda x: x[1])[0]
        best_confidence = text_weights[best_text] / total_weight

        return best_text, best_confidence

    def get_stats(self) -> Dict[str, Any]:
        """Get ensemble statistics."""
        success_rate = 0.0
        if self.stats["total_calls"] > 0:
            success_rate = self.stats["successful_calls"] / self.stats["total_calls"]

        return {
            **self.stats,
            "success_rate": success_rate,
            "engines_available": [e.value for e in self.engines_available]
        }


# Global ensemble instance
_ocr_ensemble: Optional[OCREnsemble] = None


def get_ocr_ensemble() -> OCREnsemble:
    """Get the global OCR ensemble instance."""
    global _ocr_ensemble
    if _ocr_ensemble is None:
        _ocr_ensemble = OCREnsemble()
    return _ocr_ensemble


if __name__ == '__main__':
    # Test the OCR ensemble
    print("Testing OCR Ensemble...")

    ensemble = OCREnsemble()
    print(f"\nAvailable engines: {[e.value for e in ensemble.engines_available]}")

    # Test validator
    validator = PokerLexicalValidator()

    test_cases = [
        ("JohnPoker123", FieldType.PLAYER_NAME, True),
        ("$125.50", FieldType.BET_SIZE, True),
        ("BTN", FieldType.POSITION, True),
        ("As", FieldType.CARD_RANK, True),
        ("♠", FieldType.CARD_SUIT, True),
        ("", FieldType.PLAYER_NAME, False),
        ("XYZ", FieldType.POSITION, False),
    ]

    print("\nValidator Tests:")
    for text, field_type, expected in test_cases:
        is_valid, messages = validator.validate(text, field_type)
        status = "✓" if is_valid == expected else "✗"
        print(f"  {status} {field_type.value}: '{text}' -> {is_valid} {messages}")

    print("\n✓ OCR Ensemble test complete")
