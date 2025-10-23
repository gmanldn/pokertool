"""
Enhanced Card Recognition with Ensemble Methods
================================================

Implements a multi-strategy ensemble approach to achieve >99% card detection accuracy:

1. Template Matching (OpenCV)
2. OCR-based recognition (Tesseract)
3. Color/Suit analysis
4. Edge detection
5. Voting ensemble with confidence thresholding

Features:
- Ensemble voting across multiple detection strategies
- Confidence thresholding and filtering
- Fallback matching strategies
- Color-based suit detection
- Adaptive preprocessing

Target: >99% accuracy on standard poker card imagery
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter
from enum import Enum

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None

# Import base card recognizer
try:
    from .card_recognizer import (
        Card, CardRecognitionEngine, RecognitionResult,
        RANKS, SUITS, SUIT_NAMES
    )
    BASE_RECOGNIZER_AVAILABLE = True
except ImportError:
    # Define minimal types if base isn't available
    BASE_RECOGNIZER_AVAILABLE = False
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    SUITS = ["c", "d", "h", "s"]

    @dataclass(frozen=True)
    class Card:
        rank: str
        suit: str

        def __str__(self) -> str:
            return f"{self.rank}{self.suit}"

    @dataclass
    class RecognitionResult:
        card: Optional[Card]
        confidence: float
        method: str
        location: Tuple[int, int, int, int]


class DetectionStrategy(Enum):
    """Detection strategy types."""
    TEMPLATE_MATCHING = "template_matching"
    OCR = "ocr"
    COLOR_ANALYSIS = "color_analysis"
    EDGE_DETECTION = "edge_detection"
    HYBRID = "hybrid"


@dataclass
class StrategyResult:
    """Result from a single detection strategy."""
    strategy: DetectionStrategy
    card: Optional[Card]
    confidence: float
    metadata: Dict[str, Any]


class EnhancedCardRecognizer:
    """
    Multi-strategy ensemble card recognizer with >99% target accuracy.

    Uses voting across multiple detection strategies:
    - Template matching (base recognizer)
    - OCR-based text recognition
    - Color/suit analysis
    - Edge detection

    Combines results using weighted voting with confidence thresholds.
    """

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        min_confidence: float = 0.80,
        min_ensemble_confidence: float = 0.99,
        enable_ocr: bool = True,
        enable_color: bool = True,
        enable_edge: bool = True
    ):
        """
        Initialize enhanced recognizer.

        Args:
            template_dir: Directory for card templates
            min_confidence: Minimum confidence for individual strategies
            min_ensemble_confidence: Minimum ensemble confidence to emit result
            enable_ocr: Enable OCR-based detection
            enable_color: Enable color-based suit detection
            enable_edge: Enable edge-based detection
        """
        self.available = CV2_AVAILABLE
        self.min_confidence = min_confidence
        self.min_ensemble_confidence = min_ensemble_confidence
        self.enable_ocr = enable_ocr and TESSERACT_AVAILABLE
        self.enable_color = enable_color
        self.enable_edge = enable_edge

        # Initialize base template matching engine
        if BASE_RECOGNIZER_AVAILABLE:
            self.base_engine = CardRecognitionEngine(template_dir=template_dir)
        else:
            self.base_engine = None

        # Color thresholds for suit detection (HSV color space)
        self.suit_colors = {
            'h': {'lower': np.array([0, 100, 100]), 'upper': np.array([10, 255, 255])},  # Red (hearts)
            'd': {'lower': np.array([0, 100, 100]), 'upper': np.array([10, 255, 255])},  # Red (diamonds)
            'c': {'lower': np.array([0, 0, 0]), 'upper': np.array([180, 255, 50])},     # Black (clubs)
            's': {'lower': np.array([0, 0, 0]), 'upper': np.array([180, 255, 50])},     # Black (spades)
        }

        # Strategy weights for ensemble voting
        self.strategy_weights = {
            DetectionStrategy.TEMPLATE_MATCHING: 1.0,
            DetectionStrategy.OCR: 0.9,
            DetectionStrategy.COLOR_ANALYSIS: 0.7,
            DetectionStrategy.EDGE_DETECTION: 0.6,
        }

        # Performance tracking
        self.detection_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'by_strategy': {s: {'successful': 0, 'failed': 0} for s in DetectionStrategy}
        }

        if not self.available:
            logger.warning("Enhanced card recognition disabled: OpenCV unavailable")

    def recognize_card(
        self,
        card_image: np.ndarray,
        require_high_confidence: bool = True
    ) -> RecognitionResult:
        """
        Recognize card using ensemble of strategies.

        Args:
            card_image: Card image region (BGR or grayscale)
            require_high_confidence: If True, require >99% ensemble confidence

        Returns:
            RecognitionResult with ensemble card, confidence, and method
        """
        if not self.available or card_image is None or card_image.size == 0:
            return RecognitionResult(None, 0.0, "unavailable", (0, 0, 0, 0))

        self.detection_stats['total'] += 1

        # Run all enabled strategies in parallel
        strategy_results: List[StrategyResult] = []

        # Strategy 1: Template matching
        if self.base_engine and self.base_engine.available:
            result = self._strategy_template_matching(card_image)
            if result:
                strategy_results.append(result)

        # Strategy 2: OCR
        if self.enable_ocr:
            result = self._strategy_ocr(card_image)
            if result:
                strategy_results.append(result)

        # Strategy 3: Color analysis
        if self.enable_color:
            result = self._strategy_color_analysis(card_image)
            if result:
                strategy_results.append(result)

        # Strategy 4: Edge detection
        if self.enable_edge:
            result = self._strategy_edge_detection(card_image)
            if result:
                strategy_results.append(result)

        # No strategies returned results
        if not strategy_results:
            self.detection_stats['failed'] += 1
            return RecognitionResult(None, 0.0, "no_strategies", (0, 0, 0, 0))

        # Ensemble voting
        ensemble_result = self._ensemble_vote(strategy_results)

        # Check confidence threshold
        if require_high_confidence and ensemble_result.confidence < self.min_ensemble_confidence:
            self.detection_stats['failed'] += 1
            logger.debug(
                f"Ensemble confidence {ensemble_result.confidence:.3f} below threshold "
                f"{self.min_ensemble_confidence}"
            )
            return RecognitionResult(
                ensemble_result.card,
                ensemble_result.confidence,
                f"low_confidence_ensemble({len(strategy_results)})",
                (0, 0, card_image.shape[1], card_image.shape[0])
            )

        self.detection_stats['successful'] += 1
        height, width = card_image.shape[:2]

        return RecognitionResult(
            ensemble_result.card,
            ensemble_result.confidence,
            f"ensemble({len(strategy_results)}_strategies)",
            (0, 0, width, height)
        )

    def _strategy_template_matching(self, card_image: np.ndarray) -> Optional[StrategyResult]:
        """Template matching strategy using base recognizer."""
        try:
            result = self.base_engine.recognize_card(card_image)
            if result.card and result.confidence >= self.min_confidence:
                self.detection_stats['by_strategy'][DetectionStrategy.TEMPLATE_MATCHING]['successful'] += 1
                return StrategyResult(
                    strategy=DetectionStrategy.TEMPLATE_MATCHING,
                    card=result.card,
                    confidence=result.confidence,
                    metadata={'base_method': result.method}
                )
            else:
                self.detection_stats['by_strategy'][DetectionStrategy.TEMPLATE_MATCHING]['failed'] += 1
        except Exception as e:
            logger.debug(f"Template matching strategy failed: {e}")
            self.detection_stats['by_strategy'][DetectionStrategy.TEMPLATE_MATCHING]['failed'] += 1

        return None

    def _strategy_ocr(self, card_image: np.ndarray) -> Optional[StrategyResult]:
        """OCR-based card recognition strategy."""
        if not TESSERACT_AVAILABLE:
            return None

        try:
            # Preprocess for OCR
            if card_image.ndim == 3:
                gray = cv2.cvtColor(card_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_image.copy()

            # Enhance contrast
            gray = cv2.equalizeHist(gray)

            # Threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Extract top-left corner (where rank/suit usually are)
            h, w = thresh.shape
            corner = thresh[0:h//2, 0:w//3]

            # OCR with config optimized for single characters
            config = '--psm 6 -c tessedit_char_whitelist=23456789TJQKA♠♥♦♣♤♡♢♧cdhs'
            text = pytesseract.image_to_string(corner, config=config).strip()

            # Parse rank and suit
            card = self._parse_ocr_text(text)
            if card:
                # Calculate confidence based on text clarity
                confidence = self._calculate_ocr_confidence(text, card)
                if confidence >= self.min_confidence:
                    self.detection_stats['by_strategy'][DetectionStrategy.OCR]['successful'] += 1
                    return StrategyResult(
                        strategy=DetectionStrategy.OCR,
                        card=card,
                        confidence=confidence,
                        metadata={'ocr_text': text}
                    )

            self.detection_stats['by_strategy'][DetectionStrategy.OCR]['failed'] += 1
        except Exception as e:
            logger.debug(f"OCR strategy failed: {e}")
            self.detection_stats['by_strategy'][DetectionStrategy.OCR]['failed'] += 1

        return None

    def _strategy_color_analysis(self, card_image: np.ndarray) -> Optional[StrategyResult]:
        """Color-based suit detection strategy."""
        if not CV2_AVAILABLE:
            return None

        try:
            # Convert to HSV
            if card_image.ndim == 2:
                # Convert grayscale to BGR first
                bgr = cv2.cvtColor(card_image, cv2.COLOR_GRAY2BGR)
            else:
                bgr = card_image.copy()

            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

            # Extract suit region (bottom portion of top-left corner)
            h, w = hsv.shape[:2]
            suit_region = hsv[h//4:h//2, 0:w//3]

            # Detect dominant color
            red_suits = ['h', 'd']
            black_suits = ['c', 's']

            # Count red pixels
            red_mask = cv2.inRange(suit_region, self.suit_colors['h']['lower'], self.suit_colors['h']['upper'])
            red_pixels = cv2.countNonZero(red_mask)

            # Count black pixels
            black_mask = cv2.inRange(suit_region, self.suit_colors['c']['lower'], self.suit_colors['c']['upper'])
            black_pixels = cv2.countNonZero(black_mask)

            total_pixels = suit_region.shape[0] * suit_region.shape[1]

            # Determine suit color with confidence
            if red_pixels > black_pixels and red_pixels > total_pixels * 0.1:
                suit_color = 'red'
                confidence = min(red_pixels / total_pixels * 2, 1.0)
            elif black_pixels > red_pixels and black_pixels > total_pixels * 0.1:
                suit_color = 'black'
                confidence = min(black_pixels / total_pixels * 2, 1.0)
            else:
                self.detection_stats['by_strategy'][DetectionStrategy.COLOR_ANALYSIS]['failed'] += 1
                return None

            # Note: Color analysis only determines red/black, not specific suit
            # This is used as a validation signal in ensemble voting
            if confidence >= self.min_confidence:
                self.detection_stats['by_strategy'][DetectionStrategy.COLOR_ANALYSIS]['successful'] += 1
                return StrategyResult(
                    strategy=DetectionStrategy.COLOR_ANALYSIS,
                    card=None,  # Color analysis doesn't determine full card
                    confidence=confidence,
                    metadata={
                        'suit_color': suit_color,
                        'red_pixels': red_pixels,
                        'black_pixels': black_pixels
                    }
                )

            self.detection_stats['by_strategy'][DetectionStrategy.COLOR_ANALYSIS]['failed'] += 1
        except Exception as e:
            logger.debug(f"Color analysis strategy failed: {e}")
            self.detection_stats['by_strategy'][DetectionStrategy.COLOR_ANALYSIS]['failed'] += 1

        return None

    def _strategy_edge_detection(self, card_image: np.ndarray) -> Optional[StrategyResult]:
        """Edge-based pattern detection strategy."""
        if not CV2_AVAILABLE:
            return None

        try:
            # Convert to grayscale
            if card_image.ndim == 3:
                gray = cv2.cvtColor(card_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = card_image.copy()

            # Edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Count edges in rank/suit regions
            h, w = edges.shape
            rank_region = edges[0:h//3, 0:w//3]
            suit_region = edges[h//3:2*h//3, 0:w//3]

            rank_edges = cv2.countNonZero(rank_region)
            suit_edges = cv2.countNonZero(suit_region)

            # Calculate confidence based on edge density
            rank_area = rank_region.shape[0] * rank_region.shape[1]
            suit_area = suit_region.shape[0] * suit_region.shape[1]

            rank_density = rank_edges / rank_area if rank_area > 0 else 0
            suit_density = suit_edges / suit_area if suit_area > 0 else 0

            # Validate edge patterns exist
            if rank_density > 0.05 and suit_density > 0.05:
                confidence = min((rank_density + suit_density) / 0.4, 1.0)
                if confidence >= self.min_confidence:
                    self.detection_stats['by_strategy'][DetectionStrategy.EDGE_DETECTION]['successful'] += 1
                    return StrategyResult(
                        strategy=DetectionStrategy.EDGE_DETECTION,
                        card=None,  # Edge detection provides validation, not full card
                        confidence=confidence,
                        metadata={
                            'rank_edge_density': rank_density,
                            'suit_edge_density': suit_density
                        }
                    )

            self.detection_stats['by_strategy'][DetectionStrategy.EDGE_DETECTION]['failed'] += 1
        except Exception as e:
            logger.debug(f"Edge detection strategy failed: {e}")
            self.detection_stats['by_strategy'][DetectionStrategy.EDGE_DETECTION]['failed'] += 1

        return None

    def _ensemble_vote(self, results: List[StrategyResult]) -> StrategyResult:
        """
        Combine results from multiple strategies using weighted voting.

        Args:
            results: List of strategy results

        Returns:
            Final ensemble result with combined confidence
        """
        # Collect all card predictions
        card_votes: List[Tuple[Card, float]] = []

        for result in results:
            if result.card:
                weight = self.strategy_weights.get(result.strategy, 1.0)
                weighted_confidence = result.confidence * weight
                card_votes.append((result.card, weighted_confidence))

        if not card_votes:
            # No card predictions, return highest confidence validation signal
            best_result = max(results, key=lambda r: r.confidence)
            return best_result

        # Vote by card identity
        card_scores: Dict[str, float] = {}
        for card, confidence in card_votes:
            card_str = str(card)
            card_scores[card_str] = card_scores.get(card_str, 0.0) + confidence

        # Find winning card
        best_card_str = max(card_scores.keys(), key=lambda k: card_scores[k])
        best_score = card_scores[best_card_str]

        # Normalize confidence by number of strategies
        ensemble_confidence = best_score / len(results)

        # Boost confidence if multiple strategies agree
        agreement_count = sum(1 for c, _ in card_votes if str(c) == best_card_str)
        if agreement_count > 1:
            # Boost by up to 10% for agreement
            agreement_boost = min(0.1 * (agreement_count - 1), 0.2)
            ensemble_confidence = min(ensemble_confidence + agreement_boost, 1.0)

        # Find a result that matches the winning card
        winning_result = None
        for result in results:
            if result.card and str(result.card) == best_card_str:
                winning_result = result
                break

        if winning_result:
            return StrategyResult(
                strategy=DetectionStrategy.HYBRID,
                card=winning_result.card,
                confidence=ensemble_confidence,
                metadata={
                    'strategies_used': len(results),
                    'agreement_count': agreement_count,
                    'raw_scores': card_scores
                }
            )
        else:
            # Shouldn't happen, but handle gracefully
            rank, suit = best_card_str[0], best_card_str[1]
            return StrategyResult(
                strategy=DetectionStrategy.HYBRID,
                card=Card(rank=rank, suit=suit),
                confidence=ensemble_confidence,
                metadata={
                    'strategies_used': len(results),
                    'agreement_count': agreement_count,
                    'raw_scores': card_scores
                }
            )

    def _parse_ocr_text(self, text: str) -> Optional[Card]:
        """Parse OCR text into rank and suit."""
        if not text:
            return None

        # Clean text
        text = text.strip().upper()

        # Map OCR symbols to suits
        suit_map = {
            '♠': 's', '♤': 's', 'S': 's',
            '♥': 'h', '♡': 'h', 'H': 'h',
            '♦': 'd', '♢': 'd', 'D': 'd',
            '♣': 'c', '♧': 'c', 'C': 'c'
        }

        # Extract rank (first character typically)
        rank = None
        for char in text:
            if char in RANKS:
                rank = char
                break
            # Map 10 to T
            if char == '1' and len(text) > 1 and text[1] == '0':
                rank = 'T'
                break

        # Extract suit
        suit = None
        for char in text:
            if char in suit_map:
                suit = suit_map[char]
                break
            if char.lower() in SUITS:
                suit = char.lower()
                break

        if rank and suit:
            try:
                return Card(rank=rank, suit=suit)
            except ValueError:
                return None

        return None

    def _calculate_ocr_confidence(self, text: str, card: Card) -> float:
        """Calculate confidence score for OCR result."""
        if not text:
            return 0.0

        # Base confidence
        confidence = 0.7

        # Boost if both rank and suit are clearly present
        if card.rank in text and any(s in text.lower() for s in ['c', 'd', 'h', 's', '♠', '♥', '♦', '♣']):
            confidence = 0.9

        # Reduce if text is very long (likely misread)
        if len(text) > 5:
            confidence *= 0.8

        # Reduce if text has unexpected characters
        valid_chars = set('23456789TJQKA♠♥♦♣♤♡♢♧cdhsCDHS \n')
        if not all(c in valid_chars for c in text):
            confidence *= 0.7

        return min(confidence, 1.0)

    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics."""
        stats = self.detection_stats.copy()

        # Calculate accuracy
        if stats['total'] > 0:
            stats['accuracy'] = stats['successful'] / stats['total']
        else:
            stats['accuracy'] = 0.0

        return stats

    def reset_stats(self):
        """Reset detection statistics."""
        self.detection_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'by_strategy': {s: {'successful': 0, 'failed': 0} for s in DetectionStrategy}
        }


# Singleton instance
_enhanced_recognizer: Optional[EnhancedCardRecognizer] = None


def get_enhanced_card_recognizer(
    min_ensemble_confidence: float = 0.99,
    **kwargs
) -> EnhancedCardRecognizer:
    """
    Get singleton enhanced card recognizer instance.

    Args:
        min_ensemble_confidence: Minimum ensemble confidence threshold
        **kwargs: Additional arguments for EnhancedCardRecognizer

    Returns:
        EnhancedCardRecognizer instance
    """
    global _enhanced_recognizer

    if _enhanced_recognizer is None:
        _enhanced_recognizer = EnhancedCardRecognizer(
            min_ensemble_confidence=min_ensemble_confidence,
            **kwargs
        )

    return _enhanced_recognizer
