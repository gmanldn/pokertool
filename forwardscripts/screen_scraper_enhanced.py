#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: screen_scraper_enhanced.py
# version: v28.0.0
# last_updated_utc: '2025-09-23T12:00:00.000000+00:00'
# applied_improvements:
# - ScreenScraper_Enhancement_1
# summary: Enhanced screen scraping with robust error handling, multi-site support,
#   and calibration
# last_commit: '2025-09-23T14:50:05.220270+00:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END

"""
Enhanced Poker Screen Scraper - Robust Multi-Site Support
Advanced screen scraping with improved accuracy, error handling, and calibration.
"""

import cv2
import numpy as np
import pytesseract
import re
import json
import time
import threading
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional, Dict, Any, Callable
from enum import Enum
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Event, Lock
import hashlib
import pickle
from datetime import datetime, timezone

# Safe imports
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    logging.warning("mss not available - screenshot functionality disabled")

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - image processing limited")

try:
    from poker_modules import Card, Suit, Position
    POKER_MODULES_AVAILABLE = True
except ImportError:
    POKER_MODULES_AVAILABLE = False
    logging.warning("Poker modules not available - using fallbacks")
    
    class Suit(Enum):
        SPADES = "♠"
        HEARTS = "♥"
        DIAMONDS = "♦"
        CLUBS = "♣"
    
    class Position(Enum):
        SB = "SB"
        BB = "BB"
        UTG = "UTG"
        MP = "MP"
        CO = "CO"
        BTN = "BTN"
    
    @dataclass
    class Card:
        rank: str
        suit: Suit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class PokerSite(Enum):
    """Supported poker sites with specific configurations."""
    GENERIC = "generic"
    POKERSTARS = "pokerstars"
    GGPOKER = "ggpoker"
    PARTYPOKER = "partypoker"
    BETMGM = "betmgm"
    WSOP = "wsop"


class DetectionConfidence(Enum):
    """Detection confidence levels."""
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    VERY_LOW = 0.2


@dataclass
class BoundingBox:
    """Enhanced bounding box with confidence."""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0
    name: str = ""
    
    def get_coords(self) -> Tuple[int, int, int, int]:
        """Get coordinates as (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def extract_from_image(self, img: np.ndarray) -> np.ndarray:
        """Extract region from image with bounds checking."""
        h, w = img.shape[:2]
        
        # Ensure bounds are within image
        x1 = max(0, min(self.x, w-1))
        y1 = max(0, min(self.y, h-1))
        x2 = max(0, min(self.x + self.width, w))
        y2 = max(0, min(self.y + self.height, h))
        
        if x2 <= x1 or y2 <= y1:
            logger.warning(f"Invalid region bounds: {self.name}")
            return np.zeros((10, 10, 3), dtype=np.uint8)
        
        return img[y1:y2, x1:x2]
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within bounding box."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this box intersects with another."""
        return not (self.x + self.width < other.x or 
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or 
                   other.y + other.height < self.y)


@dataclass
class SeatInfo:
    """Enhanced seat information."""
    seat_number: int
    is_active: bool = False
    is_hero: bool = False
    player_name: str = ""
    stack_size: Optional[float] = None
    cards: List[Card] = field(default_factory=list)
    action: Optional[str] = None
    bet_amount: Optional[float] = None
    position: Optional[Position] = None
    has_dealer_button: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TableState:
    """Enhanced table state with validation."""
    pot_size: float = 0.0
    current_bet: float = 0.0
    big_blind: float = 0.0
    small_blind: float = 0.0
    hero_cards: List[Card] = field(default_factory=list)
    board_cards: List[Card] = field(default_factory=list)
    seats: List[SeatInfo] = field(default_factory=list)
    stage: str = "preflop"
    hero_seat: Optional[int] = None
    dealer_seat: Optional[int] = None
    active_players: int = 0
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0
    hash_signature: str = ""
    
    def __post_init__(self):
        """Generate hash signature for change detection."""
        self.hash_signature = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate hash for detecting state changes."""
        data = {
            'pot': self.pot_size,
            'bet': self.current_bet,
            'hero_cards': [str(card) for card in self.hero_cards],
            'board_cards': [str(card) for card in self.board_cards],
            'stage': self.stage,
            'dealer_seat': self.dealer_seat,
            'active_seats': [s.seat_number for s in self.seats if s.is_active]
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def has_changed(self, other: 'TableState') -> bool:
        """Check if state has significantly changed."""
        return self.hash_signature != other.hash_signature
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            'hero_cards': [str(card) for card in self.hero_cards],
            'board_cards': [str(card) for card in self.board_cards],
            'seats': [seat.to_dict() for seat in self.seats]
        }
    
    def validate(self) -> List[str]:
        """Validate table state for inconsistencies."""
        errors = []
        
        # Check for duplicate hero cards and board cards
        all_cards = self.hero_cards + self.board_cards
        card_strs = [str(card) for card in all_cards]
        if len(card_strs) != len(set(card_strs)):
            errors.append("Duplicate cards detected")
        
        # Check stage consistency
        expected_board_cards = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}
        expected_count = expected_board_cards.get(self.stage, 0)
        if len(self.board_cards) != expected_count:
            errors.append(f"Board cards inconsistent with stage {self.stage}")
        
        # Check hero seat
        if self.hero_seat and self.hero_seat not in [s.seat_number for s in self.seats if s.is_hero]:
            errors.append("Hero seat mismatch")
        
        return errors


# ═══════════════════════════════════════════════════════════════════════════════
# SITE-SPECIFIC CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class SiteConfig:
    """Base configuration for poker site recognition."""
    
    def __init__(self, site: PokerSite):
        self.site = site
        self.regions = self._get_default_regions()
        self.colors = self._get_color_thresholds()
        self.text_config = self._get_text_recognition_config()
        self.card_templates = self._get_card_templates()
    
    def _get_default_regions(self) -> Dict[str, BoundingBox]:
        """Get default region mappings."""
        return {
            'pot': BoundingBox(400, 200, 200, 50, name='pot'),
            'hero_cards': BoundingBox(450, 500, 120, 80, name='hero_cards'),
            'board': BoundingBox(350, 300, 300, 80, name='board'),
            'hero_stack': BoundingBox(450, 580, 120, 30, name='hero_stack'),
            'dealer_button': BoundingBox(0, 0, 1920, 1080, name='dealer_button'),
            # Seat positions (6-max table)
            'seat_1': BoundingBox(450, 450, 120, 120, name='seat_1'),  # Hero
            'seat_2': BoundingBox(200, 400, 120, 120, name='seat_2'),  # Left
            'seat_3': BoundingBox(150, 200, 120, 120, name='seat_3'),  # Top-left
            'seat_4': BoundingBox(400, 150, 120, 120, name='seat_4'),  # Top
            'seat_5': BoundingBox(650, 200, 120, 120, name='seat_5'),  # Top-right
            'seat_6': BoundingBox(700, 400, 120, 120, name='seat_6'),  # Right
        }
    
    def _get_color_thresholds(self) -> Dict[str, Dict]:
        """Get color recognition thresholds."""
        return {
            'card_background': {'lower': np.array([200, 200, 200]), 'upper': np.array([255, 255, 255])},
            'button_colors': {'dealer': np.array([255, 255, 0]), 'sb': np.array([255, 165, 0]), 'bb': np.array([255, 0, 0])},
            'text_color': {'lower': np.array([0, 0, 0]), 'upper': np.array([100, 100, 100])},
            'chip_colors': {'white': np.array([240, 240, 240]), 'red': np.array([200, 50, 50]), 'green': np.array([50, 200, 50])},
        }
    
    def _get_text_recognition_config(self) -> Dict:
        """Get OCR configuration."""
        return {
            'tesseract_config': '--psm 7 -c tessedit_char_whitelist=0123456789.,KQJATkqjat',
            'preprocessing': ['resize', 'threshold', 'denoise'],
            'min_confidence': 0.5,
            'languages': ['eng']
        }
    
    def _get_card_templates(self) -> Dict:
        """Get card recognition templates."""
        return {
            'ranks': ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'],
            'suits': ['♠', '♥', '♦', '♣'],
            'template_size': (40, 60),
            'match_threshold': 0.8
        }


class PokerStarsConfig(SiteConfig):
    """PokerStars-specific configuration."""
    
    def _get_default_regions(self) -> Dict[str, BoundingBox]:
        """PokerStars-specific regions."""
        regions = super()._get_default_regions()
        
        # Override with PokerStars-specific positions
        regions.update({
            'pot': BoundingBox(480, 240, 160, 40, name='pot'),
            'hero_cards': BoundingBox(465, 485, 110, 75, name='hero_cards'),
            'board': BoundingBox(385, 310, 270, 75, name='board'),
            'hero_stack': BoundingBox(465, 565, 110, 25, name='hero_stack'),
            'table_name': BoundingBox(10, 10, 300, 30, name='table_name'),
            'blinds_info': BoundingBox(10, 50, 200, 30, name='blinds_info'),
        })
        
        return regions
    
    def _get_color_thresholds(self) -> Dict[str, Dict]:
        """PokerStars-specific colors."""
        colors = super()._get_color_thresholds()
        
        colors.update({
            'table_felt': {'lower': np.array([10, 60, 20]), 'upper': np.array([30, 100, 40])},
            'card_background': {'lower': np.array([240, 240, 240]), 'upper': np.array([255, 255, 255])},
            'dealer_button': {'lower': np.array([200, 180, 0]), 'upper': np.array([255, 220, 50])},
        })
        
        return colors


class GGPokerConfig(SiteConfig):
    """GGPoker-specific configuration."""
    
    def _get_default_regions(self) -> Dict[str, BoundingBox]:
        """GGPoker-specific regions."""
        regions = super()._get_default_regions()
        
        regions.update({
            'pot': BoundingBox(460, 220, 180, 45, name='pot'),
            'hero_cards': BoundingBox(450, 470, 120, 80, name='hero_cards'),
            'board': BoundingBox(370, 295, 290, 80, name='board'),
        })
        
        return regions


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED RECOGNITION COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedCardRecognizer:
    """Enhanced card recognition with template matching and ML fallbacks."""
    
    def __init__(self, config: SiteConfig):
        self.config = config
        self.templates = self._load_card_templates()
        self.recognition_cache = {}
        self.confidence_threshold = DetectionConfidence.MEDIUM.value
    
    def _load_card_templates(self) -> Dict:
        """Load card templates for template matching."""
        templates = {}
        
        # In a real implementation, load actual card templates
        # For now, create placeholder structure
        for rank in self.config.card_templates['ranks']:
            for suit in self.config.card_templates['suits']:
                templates[f"{rank}{suit}"] = {
                    'template': np.zeros((60, 40, 3), dtype=np.uint8),  # Placeholder
                    'mask': np.ones((60, 40), dtype=np.uint8) * 255
                }
        
        return templates
    
    def recognize_card(self, card_img: np.ndarray, use_cache: bool = True) -> Optional[Card]:
        """Enhanced card recognition with multiple methods."""
        if card_img is None or card_img.size == 0:
            return None
        
        # Generate cache key
        img_hash = hashlib.md5(card_img.tobytes()).hexdigest()[:16]
        if use_cache and img_hash in self.recognition_cache:
            return self.recognition_cache[img_hash]
        
        try:
            # Method 1: Template matching
            card = self._recognize_by_template(card_img)
            if card and self._validate_card_recognition(card, card_img):
                if use_cache:
                    self.recognition_cache[img_hash] = card
                return card
            
            # Method 2: OCR-based recognition
            card = self._recognize_by_ocr(card_img)
            if card and self._validate_card_recognition(card, card_img):
                if use_cache:
                    self.recognition_cache[img_hash] = card
                return card
            
            # Method 3: Color-based recognition (fallback)
            card = self._recognize_by_color(card_img)
            if card:
                if use_cache:
                    self.recognition_cache[img_hash] = card
                return card
            
            return None
            
        except Exception as e:
            logger.error(f"Card recognition error: {e}")
            return None
    
    def _recognize_by_template(self, card_img: np.ndarray) -> Optional[Card]:
        """Template matching recognition."""
        best_match = None
        best_confidence = 0.0
        
        # Preprocess image
        processed_img = self._preprocess_card_image(card_img)
        
        for card_str, template_data in self.templates.items():
            template = template_data['template']
            mask = template_data.get('mask')
            
            # Resize template to match card image
            h, w = processed_img.shape[:2]
            template_resized = cv2.resize(template, (w, h))
            
            # Template matching
            if len(processed_img.shape) == 3:
                result = cv2.matchTemplate(processed_img, template_resized, cv2.TM_CCOEFF_NORMED, mask=mask)
            else:
                result = cv2.matchTemplate(processed_img, cv2.cvtColor(template_resized, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)
            
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_match = card_str
        
        if best_confidence > self.confidence_threshold:
            rank, suit_char = best_match[0], best_match[1]
            suit_map = {'♠': Suit.SPADES, '♥': Suit.HEARTS, '♦': Suit.DIAMONDS, '♣': Suit.CLUBS}
            suit = suit_map.get(suit_char)
            if suit:
                return Card(rank, suit)
        
        return None
    
    def _recognize_by_ocr(self, card_img: np.ndarray) -> Optional[Card]:
        """OCR-based card recognition."""
        try:
            # Preprocess for OCR
            processed = self._preprocess_for_ocr(card_img)
            
            # Extract text
            config = self.config.text_config['tesseract_config']
            text = pytesseract.image_to_string(processed, config=config).strip().upper()
            
            # Parse card from text
            return self._parse_card_from_text(text)
            
        except Exception as e:
            logger.debug(f"OCR recognition failed: {e}")
            return None
    
    def _recognize_by_color(self, card_img: np.ndarray) -> Optional[Card]:
        """Color-based recognition fallback."""
        try:
            # Analyze color distribution for suit detection
            hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
            
            # Red suits (hearts, diamonds)
            red_mask = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
            red_ratio = np.sum(red_mask > 0) / red_mask.size
            
            # Black suits (spades, clubs) - detect by lack of color
            gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
            black_mask = cv2.inRange(gray, 0, 100)
            black_ratio = np.sum(black_mask > 0) / black_mask.size
            
            # Simple heuristic - this would need more sophisticated logic
            if red_ratio > 0.1:
                # Red suit detected - would need more logic to distinguish hearts vs diamonds
                return Card('?', Suit.HEARTS)  # Placeholder
            elif black_ratio > 0.2:
                # Black suit detected
                return Card('?', Suit.SPADES)  # Placeholder
            
            return None
            
        except Exception as e:
            logger.debug(f"Color recognition failed: {e}")
            return None
    
    def _preprocess_card_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess card image for recognition."""
        if img is None or img.size == 0:
            return img
        
        try:
            # Resize to standard size
            target_size = self.config.card_templates['template_size']
            resized = cv2.resize(img, target_size)
            
            # Enhance contrast
            if len(resized.shape) == 3:
                lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
                lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0).apply(lab[:, :, 0])
                resized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Denoise
            denoised = cv2.bilateralFilter(resized, 9, 75, 75)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return img
    
    def _preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image specifically for OCR."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Resize for better OCR
            scale_factor = 3
            height, width = gray.shape
            resized = cv2.resize(gray, (width * scale_factor, height * scale_factor))
            
            # Threshold
            _, thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"OCR preprocessing error: {e}")
            return img
    
    def _parse_card_from_text(self, text: str) -> Optional[Card]:
        """Parse card from OCR text."""
        if len(text) < 2:
            return None
        
        # Extract rank and suit
        rank_chars = 'AKQJT98765432'
        suit_chars = 'SHDC'
        
        rank = None
        suit_char = None
        
        for char in text:
            if char in rank_chars and rank is None:
                rank = char
            elif char in suit_chars and suit_char is None:
                suit_char = char
        
        if rank and suit_char:
            suit_map = {'S': Suit.SPADES, 'H': Suit.HEARTS, 'D': Suit.DIAMONDS, 'C': Suit.CLUBS}
            suit = suit_map.get(suit_char)
            if suit:
                return Card(rank, suit)
        
        return None
    
    def _validate_card_recognition(self, card: Card, original_img: np.ndarray) -> bool:
        """Validate recognized card against original image."""
        # Placeholder validation logic
        # In practice, this could re-analyze the image to confirm the recognition
        return True


class EnhancedTextRecognizer:
    """Enhanced text recognition for pot sizes, bets, etc."""
    
    def __init__(self, config: SiteConfig):
        self.config = config
        self.number_pattern = re.compile(r'[\d,]+\.?\d*')
        self.cache = {}
    
    def extract_number(self, img: np.ndarray, region_name: str = "") -> Optional[float]:
        """Extract numeric value from image region."""
        if img is None or img.size == 0:
            return None
        
        try:
            # Preprocess image for OCR
            processed = self._preprocess_for_numbers(img)
            
            # Extract text
            config = self.config.text_config['tesseract_config']
            text = pytesseract.image_to_string(processed, config=config).strip()
            
            # Extract numbers
            numbers = self._extract_numbers_from_text(text)
            
            if numbers:
                return max(numbers)  # Return largest number found
            
            return None
            
        except Exception as e:
            logger.debug(f"Number extraction error for {region_name}: {e}")
            return None
    
    def _preprocess_for_numbers(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for number recognition."""
        try:
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img.copy()
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Scale up for better OCR
            height, width = enhanced.shape
            scaled = cv2.resize(enhanced, (width * 2, height * 2))
            
            # Threshold
            _, thresh = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Clean up with morphology
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Number preprocessing error: {e}")
            return img
    
    def _extract_numbers_from_text(self, text: str) -> List[float]:
        """Extract all numbers from text."""
        numbers = []
        
        matches = self.number_pattern.findall(text)
        for match in matches:
            try:
                # Remove commas and convert to float
                clean_num = match.replace(',', '')
                numbers.append(float(clean_num))
            except ValueError:
                continue
            
            seat_region = self.config.regions[seat_key]
            seat_center_x = seat_region.x + seat_region.width // 2
            seat_center_y = seat_region.y + seat_region.height // 2
            
            distance = np.sqrt((x - seat_center_x)**2 + (y - seat_center_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_seat = seat_num
        
        # Only return if reasonably close (within 100 pixels)
        return closest_seat if min_distance < 100 else None
    
    def _update_performance_stats(self, processing_time: float, success: bool):
        """Update performance statistics."""
        if success:
            self.performance_stats['successful_analyses'] += 1
        else:
            self.performance_stats['errors'] += 1
        
        # Update rolling average processing time
        total_analyses = self.performance_stats['successful_analyses'] + self.performance_stats['errors']
        if total_analyses > 0:
            current_avg = self.performance_stats['avg_processing_time']
            new_avg = ((current_avg * (total_analyses - 1)) + processing_time) / total_analyses
            self.performance_stats['avg_processing_time'] = new_avg
    
    def calibrate(self, reference_img: Optional[np.ndarray] = None, 
                 interactive: bool = False) -> bool:
        """Enhanced calibration process."""
        try:
            logger.info("Starting calibration process...")
            
            # Capture reference image
            if reference_img is None:
                reference_img = self.capture_table()
                if reference_img is None:
                    logger.error("Could not capture reference image for calibration")
                    return False
            
            # Store reference data
            self.calibration_data = {
                'reference_image': reference_img.copy(),
                'timestamp': time.time(),
                'image_hash': hashlib.md5(reference_img.tobytes()).hexdigest()[:16]
            }
            
            # Test key components
            calibration_results = {}
            
            # Test pot extraction
            pot_size = self._extract_pot_size(reference_img)
            calibration_results['pot_extraction'] = pot_size is not None
            
            # Test card recognition
            hero_cards = self._extract_hero_cards(reference_img)
            calibration_results['hero_cards'] = len(hero_cards) > 0
            
            # Test seat detection
            seats = self._extract_seat_info(reference_img)
            active_seats = [s for s in seats if s.is_active]
            calibration_results['seat_detection'] = len(active_seats) >= 2
            
            # Test dealer button detection
            button_pos = self.button_detector.find_dealer_button(reference_img)
            calibration_results['button_detection'] = button_pos is not None
            
            # Calculate overall calibration score
            successful_tests = sum(calibration_results.values())
            total_tests = len(calibration_results)
            calibration_score = successful_tests / total_tests
            
            # Store calibration results
            self.calibration_data['results'] = calibration_results
            self.calibration_data['score'] = calibration_score
            
            # Set calibration status
            self.calibrated = calibration_score >= 0.5
            
            if self.calibrated:
                logger.info(f"Calibration successful! Score: {calibration_score:.2f}")
            else:
                logger.warning(f"Calibration failed. Score: {calibration_score:.2f}")
                logger.warning(f"Failed tests: {[k for k, v in calibration_results.items() if not v]}")
            
            return self.calibrated
            
        except Exception as e:
            logger.error(f"Calibration error: {e}")
            return False
    
    def start_continuous_capture(self, interval: float = 1.0, 
                               callback: Optional[Callable] = None):
        """Start continuous table monitoring."""
        if self.capture_thread and self.capture_thread.is_alive():
            logger.warning("Continuous capture already running")
            return
        
        self.stop_event.clear()
        
        def capture_loop():
            logger.info(f"Starting continuous capture (interval: {interval}s)")
            
            while not self.stop_event.is_set():
                try:
                    # Capture and analyze
                    state = self.analyze_table_state()
                    
                    if state:
                        # Check for significant changes
                        if self._has_significant_change(state):
                            with self.lock:
                                self.last_state = state
                                self.state_history.append(state)
                                
                                # Keep history manageable
                                if len(self.state_history) > 100:
                                    self.state_history = self.state_history[-50:]
                            
                            # Add to queue for external consumers
                            try:
                                self.state_queue.put(state, block=False)
                            except:
                                pass  # Queue full, skip
                            
                            # Call callback if provided
                            if callback:
                                try:
                                    callback(state)
                                except Exception as e:
                                    logger.error(f"Callback error: {e}")
                    
                    # Wait for next interval
                    self.stop_event.wait(interval)
                    
                except Exception as e:
                    logger.error(f"Capture loop error: {e}")
                    self.stop_event.wait(min(interval, 5.0))  # Wait before retrying
            
            logger.info("Continuous capture stopped")
        
        self.capture_thread = Thread(target=capture_loop, daemon=True)
        self.capture_thread.start()
    
    def stop_continuous_capture(self):
        """Stop continuous capture."""
        if self.capture_thread:
            self.stop_event.set()
            self.capture_thread.join(timeout=5.0)
            logger.info("Stopped continuous capture")
    
    def _has_significant_change(self, state: TableState) -> bool:
        """Check if state has changed significantly."""
        if not self.last_state:
            return True
        
        return state.has_changed(self.last_state)
    
    def get_latest_state(self) -> Optional[TableState]:
        """Get the most recent table state."""
        with self.lock:
            return self.last_state
    
    def get_state_updates(self, timeout: float = 0.1) -> Optional[TableState]:
        """Get state updates from queue."""
        try:
            return self.state_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def save_debug_image(self, img: Optional[np.ndarray] = None, 
                        filename: Optional[str] = None) -> Optional[str]:
        """Save annotated debug image."""
        try:
            if img is None:
                img = self.capture_table()
                if img is None:
                    return None
            
            # Create debug image with annotations
            debug_img = img.copy()
            
            # Draw all regions
            for name, region in self.config.regions.items():
                x1, y1, x2, y2 = region.get_coords()
                
                # Choose color based on region type
                if 'seat' in name:
                    color = (0, 255, 0)  # Green for seats
                elif name in ['pot', 'hero_stack']:
                    color = (255, 0, 0)  # Red for money regions
                elif name in ['hero_cards', 'board']:
                    color = (0, 0, 255)  # Blue for card regions
                else:
                    color = (128, 128, 128)  # Gray for others
                
                # Draw rectangle
                cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
                
                # Add label
                label_y = max(y1 - 10, 20)
                cv2.putText(debug_img, name, (x1, label_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
            
            # Add performance info
            stats_text = [
                f"Captures: {self.performance_stats['captures']}",
                f"Success: {self.performance_stats['successful_analyses']}",
                f"Errors: {self.performance_stats['errors']}",
                f"Avg Time: {self.performance_stats['avg_processing_time']:.3f}s",
                f"Calibrated: {'Yes' if self.calibrated else 'No'}"
            ]
            
            for i, text in enumerate(stats_text):
                cv2.putText(debug_img, text, (10, 30 + i * 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"debug_capture_{timestamp}.png"
            
            # Save image
            cv2.imwrite(filename, debug_img)
            logger.info(f"Debug image saved: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"Debug image save error: {e}")
            return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        stats = self.performance_stats.copy()
        
        # Add additional metrics
        if stats['captures'] > 0:
            stats['success_rate'] = stats['successful_analyses'] / stats['captures']
            stats['error_rate'] = stats['errors'] / stats['captures']
        else:
            stats['success_rate'] = 0.0
            stats['error_rate'] = 0.0
        
        stats['calibrated'] = self.calibrated
        stats['calibration_score'] = self.calibration_data.get('score', 0.0)
        
        return stats
    
    def reset_performance_stats(self):
        """Reset performance statistics."""
        self.performance_stats = {
            'captures': 0,
            'successful_analyses': 0,
            'errors': 0,
            'avg_processing_time': 0.0
        }
        logger.info("Performance statistics reset")


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED INTEGRATION BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedScreenScraperBridge:
    """Enhanced bridge between screen scraper and poker assistant."""
    
    def __init__(self, scraper: EnhancedPokerScreenScraper):
        self.scraper = scraper
        self.subscribers = []
        self.state_filter = None
        self.running = False
        
    def subscribe(self, callback: Callable[[TableState], None], 
                 state_filter: Optional[Callable[[TableState], bool]] = None):
        """Subscribe to state updates with optional filtering."""
        self.subscribers.append({
            'callback': callback,
            'filter': state_filter
        })
    
    def unsubscribe(self, callback: Callable):
        """Remove a subscriber."""
        self.subscribers = [s for s in self.subscribers if s['callback'] != callback]
    
    def start_monitoring(self, interval: float = 1.0):
        """Start monitoring and broadcasting state changes."""
        if self.running:
            return
        
        self.running = True
        
        def broadcast_callback(state: TableState):
            """Broadcast state to all subscribers."""
            for subscriber in self.subscribers:
                try:
                    # Apply filter if present
                    if subscriber['filter'] and not subscriber['filter'](state):
                        continue
                    
                    # Call subscriber callback
                    subscriber['callback'](state)
                    
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")
        
        self.scraper.start_continuous_capture(interval, broadcast_callback)
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.running = False
        self.scraper.stop_continuous_capture()
    
    def get_current_state(self) -> Optional[TableState]:
        """Get current table state."""
        return self.scraper.get_latest_state()
    
    def force_update(self) -> Optional[TableState]:
        """Force immediate state update."""
        return self.scraper.analyze_table_state()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS AND TESTING
# ═══════════════════════════════════════════════════════════════════════════════

def test_screen_scraper(site: PokerSite = PokerSite.GENERIC) -> bool:
    """Test screen scraper functionality."""
    logger.info(f"Testing screen scraper for {site.value}")
    
    try:
        # Create scraper
        scraper = EnhancedPokerScreenScraper(site)
        
        # Test screenshot capture
        img = scraper.capture_table()
        if img is None:
            logger.error("Screenshot capture failed")
            return False
        
        logger.info(f"Screenshot captured: {img.shape}")
        
        # Test calibration
        calibrated = scraper.calibrate(img)
        logger.info(f"Calibration {'successful' if calibrated else 'failed'}")
        
        # Test analysis
        state = scraper.analyze_table_state(img)
        if state:
            logger.info(f"Analysis successful: {len(state.hero_cards)} hero cards, "
                       f"{len(state.board_cards)} board cards, "
                       f"{state.active_players} active players")
        else:
            logger.warning("Analysis failed")
        
        # Save debug image
        debug_file = scraper.save_debug_image(img)
        if debug_file:
            logger.info(f"Debug image saved: {debug_file}")
        
        # Print performance stats
        stats = scraper.get_performance_stats()
        logger.info(f"Performance stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run basic test
    test_screen_scraper()

        
        return numbers


class EnhancedButtonDetector:
    """Enhanced detection for dealer button, blinds, etc."""
    
    def __init__(self, config: SiteConfig):
        self.config = config
        self.button_templates = self._load_button_templates()
    
    def _load_button_templates(self) -> Dict:
        """Load button templates."""
        # Placeholder - in practice, load actual button images
        return {
            'dealer': np.zeros((30, 30, 3), dtype=np.uint8),
            'small_blind': np.zeros((20, 20, 3), dtype=np.uint8),
            'big_blind': np.zeros((20, 20, 3), dtype=np.uint8),
        }
    
    def find_dealer_button(self, img: np.ndarray) -> Optional[Tuple[int, int]]:
        """Find dealer button position."""
        try:
            # Color-based detection for dealer button
            colors = self.config.colors['button_colors']
            dealer_color = colors.get('dealer')
            
            if dealer_color is not None:
                # Convert color to HSV for better detection
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                
                # Create mask for dealer button color
                lower_bound = np.array([20, 100, 100])  # Yellow-ish in HSV
                upper_bound = np.array([30, 255, 255])
                mask = cv2.inRange(hsv, lower_bound, upper_bound)
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Find largest circular contour
                for contour in sorted(contours, key=cv2.contourArea, reverse=True):
                    area = cv2.contourArea(contour)
                    if area > 100:  # Minimum size threshold
                        # Check if roughly circular
                        perimeter = cv2.arcLength(contour, True)
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        
                        if circularity > 0.5:  # Reasonably circular
                            M = cv2.moments(contour)
                            if M["m00"] != 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int M["m01"] / M["m00"])
                                return (cx, cy)
            
            return None
            
        except Exception as e:
            logger.error(f"Dealer button detection error: {e}")
            return None
    
    def detect_blinds(self, img: np.ndarray) -> Dict[str, Optional[Tuple[int, int]]]:
        """Detect small blind and big blind positions."""
        # Placeholder implementation
        return {'small_blind': None, 'big_blind': None}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENHANCED SCREEN SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedPokerScreenScraper:
    """Enhanced poker screen scraper with robust error handling."""
    
    def __init__(self, site: PokerSite = PokerSite.GENERIC):
        self.site = site
        self.config = self._get_site_config(site)
        
        # Initialize recognition components
        self.card_recognizer = EnhancedCardRecognizer(self.config)
        self.text_recognizer = EnhancedTextRecognizer(self.config)
        self.button_detector = EnhancedButtonDetector(self.config)
        
        # State management
        self.last_state = None
        self.state_history = []
        self.calibrated = False
        self.calibration_data = {}
        
        # Threading
        self.capture_thread = None
        self.stop_event = Event()
        self.state_queue = Queue()
        self.lock = Lock()
        
        # Performance tracking
        self.performance_stats = {
            'captures': 0,
            'successful_analyses': 0,
            'errors': 0,
            'avg_processing_time': 0.0
        }
        
        # Screenshot handler
        if MSS_AVAILABLE:
            self.sct = mss.mss()
        else:
            self.sct = None
            logger.warning("Screenshot functionality not available")
    
    def _get_site_config(self, site: PokerSite) -> SiteConfig:
        """Get configuration for specific poker site."""
        config_map = {
            PokerSite.POKERSTARS: PokerStarsConfig,
            PokerSite.GGPOKER: GGPokerConfig,
            PokerSite.GENERIC: SiteConfig,
        }
        
        config_class = config_map.get(site, SiteConfig)
        return config_class(site)
    
    def find_poker_window(self) -> Optional[Dict]:
        """Enhanced poker window detection."""
        if not self.sct:
            return None
        
        try:
            # For now, use primary monitor
            # In production, implement window enumeration by title/class
            monitor = self.sct.monitors[1] if len(self.sct.monitors) > 1 else self.sct.monitors[0]
            
            return {
                "top": monitor["top"],
                "left": monitor["left"],
                "width": monitor["width"],
                "height": monitor["height"]
            }
            
        except Exception as e:
            logger.error(f"Window detection error: {e}")
            return None
    
    def capture_table(self, window_bounds: Optional[Dict] = None) -> Optional[np.ndarray]:
        """Enhanced table capture with error handling."""
        if not self.sct:
            logger.error("Screenshot functionality not available")
            return None
        
        try:
            # Get window bounds
            bounds = window_bounds or self.find_poker_window()
            if not bounds:
                logger.error("Could not find poker window")
                return None
            
            # Capture screenshot
            screenshot = self.sct.grab(bounds)
            
            # Convert to numpy array
            img = np.array(screenshot)
            
            # Convert BGRA to BGR
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Update performance stats
            self.performance_stats['captures'] += 1
            
            return img
            
        except Exception as e:
            logger.error(f"Screenshot capture error: {e}")
            self.performance_stats['errors'] += 1
            return None
    
    def analyze_table_state(self, img: Optional[np.ndarray] = None, 
                          validate: bool = True) -> Optional[TableState]:
        """Comprehensive table state analysis."""
        start_time = time.time()
        
        try:
            # Capture image if not provided
            if img is None:
                img = self.capture_table()
                if img is None:
                    return None
            
            # Initialize state
            state = TableState()
            
            # Extract different components
            state.pot_size = self._extract_pot_size(img)
            state.current_bet = self._extract_current_bet(img)
            state.hero_cards = self._extract_hero_cards(img)
            state.board_cards = self._extract_board_cards(img)
            state.stage = self._detect_game_stage(state.board_cards)
            state.seats = self._extract_seat_info(img)
            
            # Detect button and blinds
            button_pos = self.button_detector.find_dealer_button(img)
            if button_pos:
                state.dealer_seat = self._position_to_seat(button_pos)
            
            # Calculate derived values
            state.active_players = sum(1 for seat in state.seats if seat.is_active)
            state.hero_seat = next((seat.seat_number for seat in state.seats if seat.is_hero), None)
            
            # Validate if requested
            if validate:
                validation_errors = state.validate()
                if validation_errors:
                    logger.warning(f"State validation errors: {validation_errors}")
                    state.confidence = max(0.0, state.confidence - 0.2 * len(validation_errors))
            
            # Update performance stats
            processing_time = time.time() - start_time
            self._update_performance_stats(processing_time, True)
            
            return state
            
        except Exception as e:
            logger.error(f"Table analysis error: {e}")
            processing_time = time.time() - start_time
            self._update_performance_stats(processing_time, False)
            return None
    
    def _extract_pot_size(self, img: np.ndarray) -> float:
        """Extract pot size from image."""
        pot_region = self.config.regions['pot']
        pot_img = pot_region.extract_from_image(img)
        
        pot_size = self.text_recognizer.extract_number(pot_img, "pot")
        return pot_size if pot_size else 0.0
    
    def _extract_current_bet(self, img: np.ndarray) -> float:
        """Extract current bet amount."""
        # This would need a specific region for current bet
        # For now, return 0 as placeholder
        return 0.0
    
    def _extract_hero_cards(self, img: np.ndarray) -> List[Card]:
        """Extract hero's hole cards."""
        hero_region = self.config.regions['hero_cards']
        hero_img = hero_region.extract_from_image(img)
        
        if hero_img.size == 0:
            return []
        
        # Split into two cards (assuming side-by-side layout)
        h, w = hero_img.shape[:2]
        card_width = w // 2
        
        cards = []
        for i in range(2):
            x_start = i * card_width
            x_end = (i + 1) * card_width
            card_img = hero_img[:, x_start:x_end]
            
            card = self.card_recognizer.recognize_card(card_img)
            if card:
                cards.append(card)
        
        return cards
    
    def _extract_board_cards(self, img: np.ndarray) -> List[Card]:
        """Extract community cards from board."""
        board_region = self.config.regions['board']
        board_img = board_region.extract_from_image(img)
        
        if board_img.size == 0:
            return []
        
        # Split into up to 5 cards
        h, w = board_img.shape[:2]
        card_width = w // 5
        
        cards = []
        for i in range(5):
            x_start = i * card_width
            x_end = (i + 1) * card_width
            card_img = board_img[:, x_start:x_end]
            
            card = self.card_recognizer.recognize_card(card_img)
            if card:
                cards.append(card)
        
        return cards
    
    def _extract_seat_info(self, img: np.ndarray) -> List[SeatInfo]:
        """Extract information about all seats."""
        seats = []
        
        for seat_num in range(1, 7):  # 6-max table
            seat_key = f'seat_{seat_num}'
            if seat_key not in self.config.regions:
                continue
            
            seat_region = self.config.regions[seat_key]
            seat_img = seat_region.extract_from_image(img)
            
            if seat_img.size == 0:
                continue
            
            # Analyze seat
            seat_info = SeatInfo(seat_number=seat_num)
            seat_info.is_active = self._is_seat_active(seat_img)
            seat_info.is_hero = (seat_num == 1)  # Assume seat 1 is hero
            
            if seat_info.is_active:
                seat_info.stack_size = self._extract_stack_size(seat_img)
                seat_info.player_name = self._extract_player_name(seat_img)
            
            seats.append(seat_info)
        
        return seats
    
    def _is_seat_active(self, seat_img: np.ndarray) -> bool:
        """Determine if a seat is active (has a player)."""
        # Simple approach: check if there's enough variation in the image
        if seat_img.size == 0:
            return False
        
        gray = cv2.cvtColor(seat_img, cv2.COLOR_BGR2GRAY)
        variance = np.var(gray)
        
        # If variance is above threshold, likely has a player
        return variance > 100  # Threshold to be tuned
    
    def _extract_stack_size(self, seat_img: np.ndarray) -> Optional[float]:
        """Extract stack size from seat image."""
        # This would need to identify the stack size text region within the seat
        return self.text_recognizer.extract_number(seat_img, "stack")
    
    def _extract_player_name(self, seat_img: np.ndarray) -> str:
        """Extract player name from seat image."""
        # Placeholder - would need OCR for text
        return "Player"
    
    def _detect_game_stage(self, board_cards: List[Card]) -> str:
        """Detect game stage based on board cards."""
        num_cards = len(board_cards)
        
        if num_cards == 0:
            return "preflop"
        elif num_cards == 3:
            return "flop"
        elif num_cards == 4:
            return "turn"
        elif num_cards == 5:
            return "river"
        else:
            return "unknown"
    
    def _position_to_seat(self, position: Tuple[int, int]) -> Optional[int]:
        """Convert pixel position to seat number."""
        x, y = position
        
        # Find closest seat region
        min_distance = float('inf')
        closest_seat = None
        
        for seat_num in range(1, 7):
            seat_key = f'seat_{seat_num}'
            if seat_key not in self.config.regions:
                