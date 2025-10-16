#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Ocr Recognition Module
==================================

This module provides functionality for ocr recognition operations
within the PokerTool application ecosystem.

Module: pokertool.ocr_recognition
Version: 20.0.0
Last Modified: 2025-09-29
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import os
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pathlib import Path

# Try to import OCR dependencies
try:
    import cv2
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    # EasyOCR is optional - pytesseract provides sufficient OCR capability
    # Silently handle missing dependencies as they're checked before use
    cv2 = None
    pytesseract = None
    Image = None
    ImageEnhance = None
    ImageFilter = None
    easyocr = None
    OCR_AVAILABLE = False

from .core import Card, Rank, Suit, parse_card
from .error_handling import retry_on_failure

logger = logging.getLogger(__name__)

class RecognitionMethod(Enum):
    """OCR recognition methods available."""
    TESSERACT = 'tesseract'
    EASYOCR = 'easyocr'
    TEMPLATE_MATCHING = 'template'
    HYBRID = 'hybrid'

@dataclass
class CardRegion:
    """Defines a region where a card should be detected."""
    x: int
    y: int
    width: int
    height: int
    card_type: str  # 'hole', 'board', 'opponent'
    confidence: float = 0.0

@dataclass
class RecognitionResult:
    """Result of OCR card recognition."""
    cards: List[str]
    confidence: float
    method_used: RecognitionMethod
    processing_time: float
    raw_text: str = ""
    debug_info: Dict[str, Any] = None

class CardTemplateManager:
    """Manages card template images for template matching."""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / "card_templates"
        self.templates = {}
        self.suits_unicode = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
        self.ranks_map = {
            'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': 'T',
            '10': 'T', '9': '9', '8': '8', '7': '7', '6': '6',
            '5': '5', '4': '4', '3': '3', '2': '2'
        }
        
        if OCR_AVAILABLE:
            self._load_templates()
    
    def _load_templates(self):
        """Load card template images."""
        if not self.template_dir.exists():
            logger.debug(f"Template directory not found: {self.template_dir} (using EasyOCR fallback)")
            return
        
        try:
            for template_file in self.template_dir.glob("*.png"):
                template_name = template_file.stem
                template_img = cv2.imread(str(template_file), cv2.IMREAD_GRAYSCALE)
                if template_img is not None:
                    self.templates[template_name] = template_img
                    logger.debug(f"Loaded template: {template_name}")
            
            logger.info(f"Loaded {len(self.templates)} card templates")
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
    
    def match_template(self, image: np.ndarray, threshold: float = 0.8) -> List[Tuple[str, float, Tuple[int, int]]]:
        """Match card templates against an image region."""
        if not self.templates:
            return []
        
        matches = []
        for template_name, template in self.templates.items():
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                matches.append((template_name, max_val, max_loc))
        
        # Sort by confidence and return best matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]  # Return top 5 matches

class PokerOCR:
    """
    Advanced OCR system for poker table recognition.
    Supports multiple recognition methods and adaptive preprocessing.
    """
    
    def __init__(self, method: RecognitionMethod = RecognitionMethod.HYBRID):
        if not OCR_AVAILABLE:
            raise RuntimeError("OCR dependencies not available. Install opencv-python, pytesseract, pillow, easyocr")
        
        self.method = method
        self.template_manager = CardTemplateManager()
        self.easyocr_reader = None
        
        # Initialize EasyOCR if available
        if easyocr:
            try:
                self.easyocr_reader = easyocr.Reader(['en'], gpu=False)  # CPU only for compatibility
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
        
        # Configure Tesseract
        self._configure_tesseract()
        
        logger.info(f"PokerOCR initialized with method: {method.value}")
    
    def _configure_tesseract(self):
        """Configure Tesseract OCR settings."""
        if not pytesseract:
            return
        
        # Try to find tesseract executable
        tesseract_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            'C:\\Users\\{}\\AppData\\Local\\Tesseract-OCR\\tesseract.exe'.format(os.getenv('USERNAME', 'user'))
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Tesseract found at: {path}")
                break
        else:
            logger.warning("Tesseract executable not found in standard locations")
    
    def preprocess_image(self, image: np.ndarray, enhance_for: str = 'cards') -> np.ndarray:
        """
        Preprocess image for better OCR recognition.
        
        Args:
            image: Input image as numpy array
            enhance_for: What to optimize for ('cards', 'text', 'numbers')
        """
        try:
            # Convert to PIL Image for advanced processing
            if len(image.shape) == 3:
                pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_img = Image.fromarray(image)
            
            if enhance_for == 'cards':
                # Enhance for card recognition
                pil_img = pil_img.convert('L')  # Grayscale
                
                # Increase contrast
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(2.0)
                
                # Increase sharpness
                enhancer = ImageEnhance.Sharpness(pil_img)
                pil_img = enhancer.enhance(1.5)
                
                # Apply filter to reduce noise
                pil_img = pil_img.filter(ImageFilter.MedianFilter())
                
            elif enhance_for == 'text':
                # Enhance for text recognition
                pil_img = pil_img.convert('L')
                
                # High contrast for text
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(3.0)
                
                # Apply threshold
                threshold = 128
                pil_img = pil_img.point(lambda x: 255 if x > threshold else 0, mode='1')
            
            elif enhance_for == 'numbers':
                # Enhance for number recognition (pot sizes, bets)
                pil_img = pil_img.convert('L')
                
                # Medium contrast
                enhancer = ImageEnhance.Contrast(pil_img)
                pil_img = enhancer.enhance(2.5)
                
                # Slight blur to connect broken characters
                pil_img = pil_img.filter(ImageFilter.GaussianBlur(0.5))
            
            # Convert back to numpy array
            return np.array(pil_img)
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return image
    
    def recognize_cards_tesseract(self, image: np.ndarray) -> List[str]:
        """Recognize cards using Tesseract OCR."""
        if not pytesseract:
            return []
        
        try:
            # Preprocess for card recognition
            processed_img = self.preprocess_image(image, 'cards')
            
            # Custom OCR configuration for cards
            custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=AKQJT23456789♠♥♦♣shdc'
            
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            cards = self._parse_card_text(text)
            
            logger.debug(f"Tesseract recognized: '{text}' -> {cards}")
            return cards
            
        except Exception as e:
            logger.error(f"Tesseract recognition failed: {e}")
            return []
    
    def recognize_cards_easyocr(self, image: np.ndarray) -> List[str]:
        """Recognize cards using EasyOCR."""
        if not self.easyocr_reader:
            return []
        
        try:
            processed_img = self.preprocess_image(image, 'cards')
            
            # EasyOCR recognition
            results = self.easyocr_reader.readtext(processed_img)
            
            cards = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:
                    parsed_cards = self._parse_card_text(text)
                    cards.extend(parsed_cards)
            
            logger.debug(f"EasyOCR recognized cards: {cards}")
            return cards
            
        except Exception as e:
            logger.error(f"EasyOCR recognition failed: {e}")
            return []
    
    def recognize_cards_template(self, image: np.ndarray) -> List[str]:
        """Recognize cards using template matching."""
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            matches = self.template_manager.match_template(gray, threshold=0.75)
            
            cards = []
            for template_name, confidence, location in matches[:2]:  # Max 2 cards per region
                # Template names should be in format like "As", "Kh", etc.
                if len(template_name) == 2 and template_name[0] in 'AKQJT23456789' and template_name[1] in 'shdc':
                    cards.append(template_name)
            
            logger.debug(f"Template matching found cards: {cards}")
            return cards
            
        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            return []
    
    def _parse_card_text(self, text: str) -> List[str]:
        """Parse OCR text to extract valid card representations."""
        cards = []
        text = text.strip().upper()
        
        # Clean up common OCR errors
        replacements = {
            '0': 'O', 'I': '1', 'L': '1', 'S': '5', 'O': '0',
            '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Look for card patterns (rank + suit)
        # Pattern for cards like "AS", "KH", "10D", etc.
        card_pattern = r'([AKQJT2-9]|10)([SHDC])'
        matches = re.findall(card_pattern, text)
        
        for rank, suit in matches:
            # Normalize rank
            if rank == '10':
                rank = 'T'
            
            # Normalize suit
            suit_map = {'S': 's', 'H': 'h', 'D': 'd', 'C': 'c'}
            suit = suit_map.get(suit, suit.lower())
            
            card_str = f"{rank}{suit}"
            
            # Validate card
            try:
                parse_card(card_str)  # This will raise if invalid
                cards.append(card_str)
            except ValueError:
                logger.debug(f"Invalid card parsed: {card_str}")
                continue
        
        return cards[:2]  # Maximum 2 cards per region
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def recognize_cards(self, image: np.ndarray, region: CardRegion) -> RecognitionResult:
        """
        Main card recognition function.
        
        Args:
            image: Full table image
            region: Card region to analyze
            
        Returns:
            RecognitionResult with recognized cards and confidence
        """
        import time
        start_time = time.time()
        
        try:
            # Extract region from image
            y1, y2 = region.y, region.y + region.height
            x1, x2 = region.x, region.x + region.width
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return RecognitionResult([], 0.0, self.method, time.time() - start_time)
            
            all_cards = []
            method_used = self.method
            
            if self.method == RecognitionMethod.HYBRID:
                # Try multiple methods and take best result
                tesseract_cards = self.recognize_cards_tesseract(roi)
                easyocr_cards = self.recognize_cards_easyocr(roi)
                template_cards = self.recognize_cards_template(roi)
                
                # Choose best result based on number of valid cards found
                candidates = [
                    (tesseract_cards, RecognitionMethod.TESSERACT),
                    (easyocr_cards, RecognitionMethod.EASYOCR),
                    (template_cards, RecognitionMethod.TEMPLATE_MATCHING)
                ]
                
                candidates = [(cards, method) for cards, method in candidates if cards]
                if candidates:
                    # Prefer template matching if it finds cards, otherwise use longest result
                    for cards, method in candidates:
                        if method == RecognitionMethod.TEMPLATE_MATCHING:
                            all_cards = cards
                            method_used = method
                            break
                    else:
                        all_cards, method_used = max(candidates, key=lambda x: len(x[0]))
                
            elif self.method == RecognitionMethod.TESSERACT:
                all_cards = self.recognize_cards_tesseract(roi)
                method_used = RecognitionMethod.TESSERACT
                
            elif self.method == RecognitionMethod.EASYOCR:
                all_cards = self.recognize_cards_easyocr(roi)
                method_used = RecognitionMethod.EASYOCR
                
            elif self.method == RecognitionMethod.TEMPLATE_MATCHING:
                all_cards = self.recognize_cards_template(roi)
                method_used = RecognitionMethod.TEMPLATE_MATCHING
            
            # Calculate confidence based on number of cards found and expected
            expected_cards = 2 if region.card_type in ['hole', 'opponent'] else 5
            confidence = min(len(all_cards) / expected_cards, 1.0) * 0.8  # Max 80% confidence
            
            processing_time = time.time() - start_time
            
            result = RecognitionResult(
                cards=all_cards[:expected_cards],  # Limit to expected number
                confidence=confidence,
                method_used=method_used,
                processing_time=processing_time,
                debug_info={
                    'region_type': region.card_type,
                    'roi_size': roi.shape,
                    'expected_cards': expected_cards
                }
            )
            
            logger.debug(f"Card recognition completed: {result.cards} (confidence: {result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Card recognition failed: {e}")
            return RecognitionResult([], 0.0, self.method, time.time() - start_time, debug_info={'error': str(e)})
    
    def recognize_betting_amounts(self, image: np.ndarray, regions: List[CardRegion]) -> Dict[str, float]:
        """Recognize betting amounts and pot sizes."""
        amounts = {}
        
        for region in regions:
            try:
                # Extract region
                y1, y2 = region.y, region.y + region.height
                x1, x2 = region.x, region.x + region.width
                roi = image[y1:y2, x1:x2]
                
                if roi.size == 0:
                    continue
                
                # Preprocess for number recognition
                processed = self.preprocess_image(roi, 'numbers')
                
                # OCR configuration for numbers and currency
                # Include comma for European decimal format (0,01) and cent symbol
                config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789.,€$£¢'
                
                tess_amount = 0.0
                tess_text = ""
                if pytesseract:
                    tess_text = pytesseract.image_to_string(processed, config=config)
                    tess_amount = self._parse_amount(tess_text)
                
                easy_amount = 0.0
                easy_confidence = 0.0
                easy_text = ""
                if self.easyocr_reader:
                    easy_amount, easy_confidence, easy_text = self._recognize_amount_easyocr(roi)
                
                chosen_amount = 0.0
                chosen_source = None
                
                if tess_amount > 0:
                    chosen_amount = tess_amount
                    chosen_source = "tesseract"
                
                if easy_amount > 0:
                    if chosen_source is None:
                        chosen_amount = easy_amount
                        chosen_source = "easyocr"
                    else:
                        if self._should_prefer_easyocr(
                            tess_amount,
                            easy_amount,
                            tess_text,
                            easy_text,
                            easy_confidence
                        ):
                            chosen_amount = easy_amount
                            chosen_source = "easyocr"
                
                if chosen_source:
                    amounts[region.card_type] = chosen_amount
                    logger.debug(
                        "Amount recognized for %s: %.2f using %s (tess='%s', easy='%s', easy_conf=%.2f)",
                        region.card_type,
                        chosen_amount,
                        chosen_source,
                        tess_text.strip(),
                        easy_text.strip(),
                        easy_confidence
                    )
                        
            except Exception as e:
                logger.error(f"Amount recognition failed for {region.card_type}: {e}")
                continue
        
        return amounts

    def _should_prefer_easyocr(
        self,
        tess_amount: float,
        easy_amount: float,
        tess_text: str,
        easy_text: str,
        easy_confidence: float
    ) -> bool:
        """Decide if EasyOCR result should replace Tesseract."""
        if easy_confidence >= 0.85 and abs(easy_amount - tess_amount) > 1e-3:
            return True
        
        if tess_amount <= 0:
            return easy_amount > 0
        
        # Prefer EasyOCR when Tesseract result looks suspicious (missing separator on large number)
        if self._is_amount_suspicious(tess_amount, tess_text) and easy_amount > 0:
            return True
        
        # If EasyOCR detects a small amount but Tesseract is orders of magnitude larger, prefer EasyOCR
        if easy_amount > 0 and easy_amount <= 100 and tess_amount > easy_amount * 5:
            return True
        
        # If EasyOCR captured decimal separators but Tesseract did not, prefer EasyOCR
        tess_has_decimal = '.' in tess_text or ',' in tess_text
        easy_has_decimal = '.' in easy_text or ',' in easy_text
        if easy_has_decimal and not tess_has_decimal and easy_amount > 0:
            return True
        
        return False

    def _recognize_amount_easyocr(self, roi: np.ndarray) -> Tuple[float, float, str]:
        """Recognize amount using EasyOCR."""
        if not self.easyocr_reader:
            return 0.0, 0.0, ""
        
        try:
            processed = self.preprocess_image(roi, 'numbers')
            if len(processed.shape) == 2:
                processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
            
            results = self.easyocr_reader.readtext(processed, detail=1, paragraph=False)
            
            best_amount = 0.0
            best_confidence = 0.0
            best_text = ""
            
            for _, text, confidence in results:
                amount = self._parse_amount(text)
                if amount > 0 and confidence >= best_confidence:
                    best_amount = amount
                    best_confidence = confidence
                    best_text = text
            
            return best_amount, best_confidence, best_text
        
        except Exception as e:
            logger.error(f"EasyOCR amount recognition failed: {e}")
            return 0.0, 0.0, ""

    def _is_amount_suspicious(self, amount: float, raw_text: str) -> bool:
        """Determine if an amount is likely misread by Tesseract."""
        if amount <= 0:
            return True
        
        raw_text = raw_text or ""
        digits_only = re.sub(r'\D', '', raw_text)
        
        if amount >= 1000 and len(digits_only) <= 4:
            return True
        
        if amount >= 100 and '.' not in raw_text and ',' not in raw_text:
            return True
        
        return False
    
    def _parse_amount(self, text: str) -> float:
        """Parse text to extract monetary amount.

        Supports both US format (1,234.56) and European format (1.234,56).
        Handles small stakes like 0.01, 0.02, 0,01, 0,02 etc.
        """
        # Clean text - remove currency symbols
        text = text.strip().replace('$', '').replace('€', '').replace('£', '').replace('¢', '')

        # Detect format: if comma is followed by 2 digits at end, it's European decimal
        # Examples: "0,01" "12,50" "1.234,56"
        european_decimal_pattern = r',\d{2}(?:\D|$)'
        is_european = bool(re.search(european_decimal_pattern, text))

        if is_european:
            # European format: comma is decimal, period is thousands separator
            # First remove thousands separators (periods)
            text = text.replace('.', '')
            # Then replace decimal comma with period for float conversion
            text = text.replace(',', '.')
        else:
            # US format: comma is thousands separator, period is decimal
            # Remove thousands separators (commas)
            text = text.replace(',', '')

        # Handle OCR confusion: O → 0, l → 1, S → 5
        text = text.replace('O', '0').replace('o', '0').replace('l', '1').replace('S', '5')

        # Find number patterns (now normalized to use . for decimal)
        number_pattern = r'(\d+\.?\d*)'
        matches = re.findall(number_pattern, text)

        if matches:
            try:
                amount = float(matches[0])
                # Sanity check: if amount is suspiciously large, might be OCR error
                # Most poker pots are under $1,000,000
                if amount > 1000000:
                    logger.warning(f"Suspiciously large amount detected: {amount} from text '{text}'")
                return amount
            except ValueError:
                return 0.0

        return 0.0

# Global OCR instance
_ocr_instance: Optional[PokerOCR] = None

def get_poker_ocr() -> PokerOCR:
    """Get the global poker OCR instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PokerOCR()
    return _ocr_instance

def create_card_regions(table_layout: str = 'standard') -> List[CardRegion]:
    """Create standard card regions for different table layouts."""
    regions = []
    
    if table_layout == 'standard':
        # Standard 9-seat table layout (approximate coordinates)
        regions.extend([
            # Hero cards (bottom center)
            CardRegion(400, 500, 120, 80, 'hole'),
            
            # Board cards (center)
            CardRegion(300, 250, 200, 80, 'board'),
            
            # Opponent positions (clockwise from top)
            CardRegion(400, 50, 80, 60, 'opponent'),   # Seat 1
            CardRegion(550, 80, 80, 60, 'opponent'),   # Seat 2
            CardRegion(650, 150, 80, 60, 'opponent'),  # Seat 3
            CardRegion(650, 300, 80, 60, 'opponent'),  # Seat 4
            CardRegion(550, 400, 80, 60, 'opponent'),  # Seat 5
            CardRegion(250, 400, 80, 60, 'opponent'),  # Seat 6
            CardRegion(150, 300, 80, 60, 'opponent'),  # Seat 7
            CardRegion(150, 150, 80, 60, 'opponent'),  # Seat 8
            CardRegion(250, 80, 80, 60, 'opponent'),   # Seat 9
            
            # Betting areas
            CardRegion(350, 200, 100, 30, 'pot'),
            CardRegion(400, 450, 80, 25, 'hero_bet'),
        ])
    
    return regions

if __name__ == '__main__':
    # Test OCR functionality
    if OCR_AVAILABLE:
        ocr = get_poker_ocr()
        print(f"OCR initialized with method: {ocr.method.value}")
        print(f"Templates loaded: {len(ocr.template_manager.templates)}")
        
        # Create test regions
        regions = create_card_regions()
        print(f"Created {len(regions)} card regions")
        
        print("OCR module ready for integration")
    else:
        print("OCR dependencies not available. Install required packages:")
        print("pip install opencv-python pytesseract pillow easyocr")
