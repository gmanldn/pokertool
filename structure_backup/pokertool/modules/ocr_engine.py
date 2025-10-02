# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: ocr_engine.py
# version: v1.0.0
# last_commit: '2025-10-02T23:15:00+00:00'
# fixes:
# - date: '2025-10-02'
#   summary: PHASE 1 - Advanced OCR for pot amounts, stacks, names, time
# - date: '2025-10-02'
#   summary: Preprocessing pipeline optimized for poker UI text
# - date: '2025-10-02'
#   summary: Number extraction with currency symbol handling
# - date: '2025-10-02'
#   summary: Player name extraction with validation
# ---
# POKERTOOL-HEADER-END
__version__ = '1'

"""
Advanced OCR Engine for Poker Tables
=====================================

Phase 1 Implementation:
- Direct pot amount extraction
- Player stack size reading
- Player name detection
- Time bank/timer reading

Features:
- Aggressive preprocessing for poker UI
- Currency symbol handling (£, $, €)
- Number format parsing (1,234.56)
- Confidence scoring
- Result caching
"""

import re
import logging
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import cv2
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OCR dependencies not available: {e}")
    OCR_AVAILABLE = False
    cv2 = None
    pytesseract = None
    Image = None


@dataclass
class OCRResult:
    """Result of OCR operation."""
    text: str
    confidence: float
    preprocessed: bool
    method: str


class PokerOCREngine:
    """
    Advanced OCR engine optimized for poker table text recognition.
    
    Handles:
    - Pot amounts with currency symbols
    - Stack sizes
    - Player names
    - Time remaining
    - Button labels
    """
    
    # Tesseract configurations for different text types
    CONFIGS = {
        'numbers': '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.,£$€',
        'text': '--psm 7 --oem 3',
        'single_word': '--psm 8 --oem 3',
        'sparse': '--psm 11 --oem 3',
    }
    
    # Currency symbols
    CURRENCY_SYMBOLS = ['$', '£', '€', '¢']
    
    def __init__(self):
        """Initialize OCR engine."""
        self.available = OCR_AVAILABLE
        if not self.available:
            logger.warning("OCR engine not available - install pytesseract and tesseract")
    
    def extract_pot_amount(self, image: np.ndarray) -> Tuple[float, float]:
        """
        Extract pot amount from image region.
        
        Args:
            image: Image region containing pot amount
        
        Returns:
            Tuple of (amount, confidence)
        """
        if not self.available:
            return 0.0, 0.0
        
        try:
            # Aggressive preprocessing for pot display
            processed = self._preprocess_for_numbers(image)
            
            # Run OCR with numbers config
            text = pytesseract.image_to_string(
                processed,
                config=self.CONFIGS['numbers']
            )
            
            # Extract number
            amount, confidence = self._parse_currency_amount(text)
            
            if amount > 0:
                logger.debug(f"Extracted pot: ${amount} (conf: {confidence:.2f})")
            
            return amount, confidence
            
        except Exception as e:
            logger.debug(f"Pot extraction error: {e}")
            return 0.0, 0.0
    
    def extract_stack_size(self, image: np.ndarray) -> Tuple[float, float]:
        """
        Extract stack size from image region.
        
        Args:
            image: Image region containing stack size
        
        Returns:
            Tuple of (stack_size, confidence)
        """
        if not self.available:
            return 0.0, 0.0
        
        try:
            # Preprocessing for stack display
            processed = self._preprocess_for_numbers(image, invert=True)
            
            # Run OCR
            text = pytesseract.image_to_string(
                processed,
                config=self.CONFIGS['numbers']
            )
            
            # Parse amount
            amount, confidence = self._parse_currency_amount(text)
            
            if amount > 0:
                logger.debug(f"Extracted stack: ${amount} (conf: {confidence:.2f})")
            
            return amount, confidence
            
        except Exception as e:
            logger.debug(f"Stack extraction error: {e}")
            return 0.0, 0.0
    
    def extract_player_name(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extract player name from image region.
        
        Args:
            image: Image region containing player name
        
        Returns:
            Tuple of (name, confidence)
        """
        if not self.available:
            return "", 0.0
        
        try:
            # Preprocessing for text
            processed = self._preprocess_for_text(image)
            
            # Run OCR with data output for confidence
            data = pytesseract.image_to_data(
                processed,
                config=self.CONFIGS['text'],
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text with highest confidence
            texts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if conf > 0:  # Valid detection
                    text = data['text'][i].strip()
                    if text and len(text) > 1:  # Valid name
                        texts.append(text)
                        confidences.append(float(conf) / 100.0)
            
            if texts:
                # Return highest confidence name
                best_idx = confidences.index(max(confidences))
                name = texts[best_idx]
                confidence = confidences[best_idx]
                
                # Validate name (letters, numbers, spaces, underscores)
                if self._is_valid_player_name(name):
                    logger.debug(f"Extracted name: '{name}' (conf: {confidence:.2f})")
                    return name, confidence
            
            return "", 0.0
            
        except Exception as e:
            logger.debug(f"Name extraction error: {e}")
            return "", 0.0
    
    def extract_time_remaining(self, image: np.ndarray) -> Tuple[float, float]:
        """
        Extract time remaining (in seconds) from timer display.
        
        Args:
            image: Image region containing timer
        
        Returns:
            Tuple of (seconds, confidence)
        """
        if not self.available:
            return 0.0, 0.0
        
        try:
            # Preprocessing for timer display
            processed = self._preprocess_for_numbers(image)
            
            # Run OCR
            text = pytesseract.image_to_string(
                processed,
                config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789:'
            )
            
            # Parse time format (MM:SS or SS)
            seconds, confidence = self._parse_time_string(text)
            
            if seconds > 0:
                logger.debug(f"Extracted time: {seconds}s (conf: {confidence:.2f})")
            
            return seconds, confidence
            
        except Exception as e:
            logger.debug(f"Time extraction error: {e}")
            return 0.0, 0.0
    
    def _preprocess_for_numbers(self, image: np.ndarray, invert: bool = False) -> np.ndarray:
        """
        Preprocess image for number recognition.
        
        Args:
            image: Input image
            invert: If True, invert colors (white text on dark bg)
        
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize if too small
        h, w = gray.shape
        if h < 30 or w < 30:
            scale = max(30 / h, 30 / w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Increase contrast
        gray = cv2.equalizeHist(gray)
        
        # Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        gray = cv2.filter2D(gray, -1, kernel)
        
        # Threshold
        if invert:
            # White text on dark background
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            # Dark text on light background
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = np.ones((2,2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return binary
    
    def _preprocess_for_text(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for text recognition.
        
        Args:
            image: Input image
        
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize if too small
        h, w = gray.shape
        if h < 20 or w < 40:
            scale = max(20 / h, 40 / w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, h=7)
        
        # Adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def _parse_currency_amount(self, text: str) -> Tuple[float, float]:
        """
        Parse currency amount from OCR text.
        
        Args:
            text: OCR text containing amount
        
        Returns:
            Tuple of (amount, confidence)
        """
        try:
            # Remove currency symbols and whitespace
            cleaned = text.strip()
            for symbol in self.CURRENCY_SYMBOLS:
                cleaned = cleaned.replace(symbol, '')
            
            # Remove commas (thousand separators)
            cleaned = cleaned.replace(',', '')
            
            # Extract number using regex
            pattern = r'(\d+\.?\d*)'
            match = re.search(pattern, cleaned)
            
            if match:
                amount = float(match.group(1))
                
                # Confidence based on how much text matched
                confidence = len(match.group(1)) / max(len(cleaned), 1)
                confidence = min(1.0, confidence)
                
                return amount, confidence
            
            return 0.0, 0.0
            
        except Exception as e:
            logger.debug(f"Currency parsing error: {e}")
            return 0.0, 0.0
    
    def _parse_time_string(self, text: str) -> Tuple[float, float]:
        """
        Parse time string (MM:SS or SS).
        
        Args:
            text: OCR text containing time
        
        Returns:
            Tuple of (seconds, confidence)
        """
        try:
            cleaned = text.strip()
            
            # Format: MM:SS
            if ':' in cleaned:
                pattern = r'(\d+):(\d+)'
                match = re.search(pattern, cleaned)
                if match:
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    total = minutes * 60 + seconds
                    confidence = 0.9  # High confidence for proper format
                    return float(total), confidence
            
            # Format: SS (just seconds)
            pattern = r'(\d+)'
            match = re.search(pattern, cleaned)
            if match:
                seconds = int(match.group(1))
                confidence = 0.7  # Medium confidence (ambiguous format)
                return float(seconds), confidence
            
            return 0.0, 0.0
            
        except Exception as e:
            logger.debug(f"Time parsing error: {e}")
            return 0.0, 0.0
    
    def _is_valid_player_name(self, name: str) -> bool:
        """
        Validate player name.
        
        Args:
            name: Candidate player name
        
        Returns:
            True if valid, False otherwise
        """
        # Check length
        if len(name) < 2 or len(name) > 20:
            return False
        
        # Must contain at least one letter or number
        if not re.search(r'[a-zA-Z0-9]', name):
            return False
        
        # Check for valid characters (alphanumeric, space, underscore, hyphen)
        if not re.match(r'^[a-zA-Z0-9 _-]+$', name):
            return False
        
        return True
    
    def batch_extract_numbers(self, images: List[np.ndarray]) -> List[Tuple[float, float]]:
        """
        Extract numbers from multiple images in batch.
        
        Args:
            images: List of image regions
        
        Returns:
            List of (amount, confidence) tuples
        """
        results = []
        for img in images:
            amount, conf = self.extract_pot_amount(img)
            results.append((amount, conf))
        return results
    
    def get_ocr_info(self) -> Dict[str, any]:
        """Get OCR engine information."""
        info = {
            'available': self.available,
            'engine': 'Tesseract' if self.available else 'None',
        }
        
        if self.available:
            try:
                version = pytesseract.get_tesseract_version()
                info['version'] = str(version)
            except Exception:
                info['version'] = 'Unknown'
        
        return info


# Singleton instance
_ocr_engine = None

def get_ocr_engine() -> PokerOCREngine:
    """Get singleton OCR engine instance."""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PokerOCREngine()
    return _ocr_engine


if __name__ == '__main__':
    # Test OCR engine
    print("🔍 Poker OCR Engine Test")
    print("=" * 60)
    
    engine = get_ocr_engine()
    info = engine.get_ocr_info()
    
    print(f"Available: {info['available']}")
    print(f"Engine: {info['engine']}")
    if 'version' in info:
        print(f"Version: {info['version']}")
    
    if not engine.available:
        print("\n❌ OCR not available")
        print("   Install: pip install pytesseract")
        print("   System: brew install tesseract (macOS)")
    else:
        print("\n✅ OCR engine ready")
        
        # Create test image with text
        test_img = np.ones((50, 150, 3), dtype=np.uint8) * 255
        cv2.putText(test_img, "$123.45", (10, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        amount, conf = engine.extract_pot_amount(test_img)
        print(f"\nTest extraction: ${amount} (confidence: {conf:.2f})")
