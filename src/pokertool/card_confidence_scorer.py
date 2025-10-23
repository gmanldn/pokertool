"""
Card Detection Confidence Scoring
==================================

Calculate confidence scores for card detections based on multiple factors:
- OCR confidence from Tesseract
- Template matching score
- Image quality metrics
- Historical accuracy
"""

import logging
from typing import Tuple, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class CardConfidenceScore:
    """Confidence score breakdown for a card detection."""
    overall: float  # 0-1
    ocr_confidence: float
    template_match_score: float
    image_quality_score: float
    rank_confidence: float
    suit_confidence: float
    
    def to_dict(self):
        return {
            'overall': self.overall,
            'ocr_confidence': self.ocr_confidence,
            'template_match': self.template_match_score,
            'image_quality': self.image_quality_score,
            'rank_confidence': self.rank_confidence,
            'suit_confidence': self.suit_confidence
        }

class CardConfidenceScorer:
    """
    Calculate multi-factor confidence scores for card detections.
    
    Combines multiple signals:
    1. OCR confidence from Tesseract
    2. Template matching score
    3. Image quality (sharpness, contrast)
    4. Historical accuracy for similar detections
    """
    
    def __init__(self):
        self.min_ocr_confidence = 0.6
        self.min_template_score = 0.7
        self.min_quality_score = 0.5
        
        # Weights for combining scores
        self.weights = {
            'ocr': 0.4,
            'template': 0.3,
            'quality': 0.2,
            'history': 0.1
        }
    
    def calculate_confidence(
        self,
        ocr_text: str,
        ocr_confidence: float,
        template_score: float,
        image_quality: float,
        historical_accuracy: float = 0.95
    ) -> CardConfidenceScore:
        """
        Calculate overall confidence score from multiple factors.
        
        Args:
            ocr_text: Detected text (e.g., "As", "Kh")
            ocr_confidence: OCR engine confidence (0-1)
            template_score: Template matching score (0-1)
            image_quality: Image quality metric (0-1)
            historical_accuracy: Historical accuracy for this card type
            
        Returns:
            CardConfidenceScore with breakdown
        """
        # Validate OCR text format
        rank_valid = self._validate_rank(ocr_text)
        suit_valid = self._validate_suit(ocr_text)
        
        # Calculate rank and suit confidences
        rank_confidence = ocr_confidence if rank_valid else 0.0
        suit_confidence = ocr_confidence if suit_valid else 0.0
        
        # Combine scores with weights
        overall = (
            self.weights['ocr'] * ocr_confidence +
            self.weights['template'] * template_score +
            self.weights['quality'] * image_quality +
            self.weights['history'] * historical_accuracy
        )
        
        # Apply penalties for invalid format
        if not rank_valid or not suit_valid:
            overall *= 0.5
        
        return CardConfidenceScore(
            overall=overall,
            ocr_confidence=ocr_confidence,
            template_match_score=template_score,
            image_quality_score=image_quality,
            rank_confidence=rank_confidence,
            suit_confidence=suit_confidence
        )
    
    def _validate_rank(self, text: str) -> bool:
        """Validate card rank is valid."""
        if len(text) < 1:
            return False
        rank = text[0].upper()
        return rank in 'AKQJT23456789'
    
    def _validate_suit(self, text: str) -> bool:
        """Validate card suit is valid."""
        if len(text) < 2:
            return False
        suit = text[1].lower()
        return suit in 'shdc'
    
    def calculate_image_quality(self, image: np.ndarray) -> float:
        """
        Calculate image quality score based on sharpness and contrast.
        
        Args:
            image: Card image region (grayscale or color)
            
        Returns:
            Quality score 0-1
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = np.dot(image[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)
            else:
                gray = image
            
            # Calculate sharpness using Laplacian variance
            laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
            convolved = np.abs(np.convolve(gray.flatten(), laplacian.flatten(), mode='same'))
            sharpness = np.var(convolved)
            
            # Normalize sharpness (empirical values)
            sharpness_score = min(sharpness / 1000.0, 1.0)
            
            # Calculate contrast
            contrast = gray.std() / 128.0  # Normalize to 0-1
            
            # Combine sharpness and contrast
            quality = (sharpness_score * 0.6 + contrast * 0.4)
            
            return min(quality, 1.0)
        except Exception as e:
            logger.error(f"Error calculating image quality: {e}")
            return 0.5  # Default medium quality
    
    def is_high_confidence(self, score: CardConfidenceScore) -> bool:
        """Check if score is high enough for reliable detection."""
        return (
            score.overall >= 0.8 and
            score.rank_confidence >= self.min_ocr_confidence and
            score.suit_confidence >= self.min_ocr_confidence
        )

# Global scorer instance
_card_scorer: Optional[CardConfidenceScorer] = None

def get_card_scorer() -> CardConfidenceScorer:
    """Get or create global card confidence scorer."""
    global _card_scorer
    if _card_scorer is None:
        _card_scorer = CardConfidenceScorer()
    return _card_scorer
