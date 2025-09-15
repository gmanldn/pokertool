#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool/poker_screen_scraper.py
# version: '20'
# last_commit: '2025-09-09T15:38:42+00:00'
# fixes: []
# ---
# POKERTOOL-HEADER-END
"""
Poker Screen Scraper Module
Captures and analyzes poker table screenshots to extract game state.
Modular design for integration with existing Poker Assistant.
"""

import cv2
import numpy as np
import pytesseract
import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import logging
from pathlib import Path
import json
import time
from threading import Thread, Event, Lock
from queue import Queue
import mss
from PIL import Image
import hashlib

# Import poker modules for data structures
from poker_modules import Card, Suit, Position

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class TableRegion:
    """Defines a region on the poker table."""
    x: int
    y: int
    width: int
    height: int
    name: str
    
    def get_coords(self) -> Tuple[int, int, int, int]:
        """Get coordinates as (x1, y1, x2, y2)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def extract_from_image(self, img: np.ndarray) -> np.ndarray:
        """Extract this region from an image."""
        return img[self.y:self.y+self.height, self.x:self.x+self.width]


@dataclass
class SeatInfo:
    """Information about a seat at the table."""
    seat_number: int
    is_active: bool = False
    is_hero: bool = False
    has_dealer_button: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    stack_size: Optional[float] = None
    cards: List[Card] = field(default_factory=list)
    action: Optional[str] = None
    bet_amount: Optional[float] = None
    position: Optional[Position] = None


@dataclass
class TableState:
    """Complete state of the poker table."""
    pot_size: float = 0.0
    current_bet: float = 0.0
    hero_cards: List[Card] = field(default_factory=list)
    board_cards: List[Card] = field(default_factory=list)
    seats: List[SeatInfo] = field(default_factory=list)
    stage: str = "preflop"
    hero_seat: Optional[int] = None
    dealer_seat: Optional[int] = None
    active_players: int = 0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'pot_size': self.pot_size,
            'current_bet': self.current_bet,
            'hero_cards': [str(c) for c in self.hero_cards],
            'board_cards': [str(c) for c in self.board_cards],
            'stage': self.stage,
            'hero_seat': self.hero_seat,
            'dealer_seat': self.dealer_seat,
            'active_players': self.active_players,
            'timestamp': self.timestamp
        }


class PokerSite(Enum):
    """Supported poker sites with their configurations."""
    POKERSTARS = "PokerStars"
    GG_POKER = "GGPoker"
    PARTYPOKER = "partypoker"
    WSOP = "WSOP"
    GENERIC = "Generic"


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class TableConfig:
    """Configuration for different poker table layouts."""
    
    CONFIGS = {
        PokerSite.GENERIC: {
            'window_title_pattern': r'.*[Pp]oker.*',
            'table_size': (1024, 768),
            'regions': {
                'pot': TableRegion(400, 250, 224, 40, 'pot'),
                'board': TableRegion(330, 320, 364, 80, 'board'),
                'hero_cards': TableRegion(430, 480, 164, 80, 'hero_cards'),
                'seat_1': TableRegion(462, 550, 100, 60, 'seat_1'),
                'seat_2': TableRegion(250, 500, 100, 60, 'seat_2'),
                'seat_3': TableRegion(100, 400, 100, 60, 'seat_3'),
                'seat_4': TableRegion(100, 250, 100, 60, 'seat_4'),
                'seat_5': TableRegion(250, 150, 100, 60, 'seat_5'),
                'seat_6': TableRegion(462, 100, 100, 60, 'seat_6'),
                'seat_7': TableRegion(674, 150, 100, 60, 'seat_7'),
                'seat_8': TableRegion(824, 250, 100, 60, 'seat_8'),
                'seat_9': TableRegion(824, 400, 100, 60, 'seat_9'),
            },
            'card_size': (71, 96),
            'card_spacing': 10,
            'colors': {
                'background': (35, 95, 63),
                'card_back': (150, 0, 0),
                'text': (255, 255, 255),
                'button': (255, 215, 0),
                'chips': (100, 100, 255)
            }
        },
        PokerSite.POKERSTARS: {
            'window_title_pattern': r'.*PokerStars.*',
            'table_size': (1024, 768),
            'regions': {
                'pot': TableRegion(380, 240, 264, 45, 'pot'),
                'board': TableRegion(310, 310, 404, 90, 'board'),
                'hero_cards': TableRegion(420, 470, 184, 90, 'hero_cards'),
                # PokerStars specific seat positions
                'seat_1': TableRegion(462, 540, 110, 65, 'seat_1'),
                'seat_2': TableRegion(240, 490, 110, 65, 'seat_2'),
                'seat_3': TableRegion(90, 390, 110, 65, 'seat_3'),
                'seat_4': TableRegion(90, 240, 110, 65, 'seat_4'),
                'seat_5': TableRegion(240, 140, 110, 65, 'seat_5'),
                'seat_6': TableRegion(462, 90, 110, 65, 'seat_6'),
                'seat_7': TableRegion(684, 140, 110, 65, 'seat_7'),
                'seat_8': TableRegion(834, 240, 110, 65, 'seat_8'),
                'seat_9': TableRegion(834, 390, 110, 65, 'seat_9'),
            },
            'card_size': (71, 96),
            'card_spacing': 8,
            'colors': {
                'background': (19, 43, 33),
                'card_back': (130, 0, 0),
                'text': (255, 255, 255),
                'button': (255, 215, 0),
                'chips': (100, 150, 255)
            }
        }
    }
    
    @classmethod
    def get_config(cls, site: PokerSite) -> Dict:
        """Get configuration for a specific poker site."""
        return cls.CONFIGS.get(site, cls.CONFIGS[PokerSite.GENERIC])


# ═══════════════════════════════════════════════════════════════════════════════
# CARD RECOGNITION
# ═══════════════════════════════════════════════════════════════════════════════

class CardRecognizer:
    """Recognizes playing cards from images using template matching and OCR."""
    
    def __init__(self, templates_path: Optional[Path] = None):
        self.templates_path = templates_path or Path("card_templates")
        self.templates = {}
        self.suit_templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load card templates if available."""
        if not self.templates_path.exists():
            logger.warning(f"Templates path {self.templates_path} not found. Using OCR fallback.")
            return
        
        # Load rank templates
        for rank in ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']:
            rank_path = self.templates_path / f"rank_{rank}.png"
            if rank_path.exists():
                self.templates[rank] = cv2.imread(str(rank_path), cv2.IMREAD_GRAYSCALE)
        
        # Load suit templates
        suit_map = {'spade': Suit.SPADE, 'heart': Suit.HEART, 
                   'diamond': Suit.DIAMOND, 'club': Suit.CLUB}
        for suit_name, suit_enum in suit_map.items():
            suit_path = self.templates_path / f"suit_{suit_name}.png"
            if suit_path.exists():
                self.suit_templates[suit_enum] = cv2.imread(str(suit_path), cv2.IMREAD_GRAYSCALE)
    
    def recognize_card(self, card_img: np.ndarray) -> Optional[Card]:
        """Recognize a single card from an image."""
        if card_img is None or card_img.size == 0:
            return None
        
        # Convert to grayscale if needed
        if len(card_img.shape) == 3:
            gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = card_img
        
        # Try template matching first
        if self.templates:
            card = self._recognize_by_template(gray)
            if card:
                return card
        
        # Fallback to OCR
        return self._recognize_by_ocr(gray)
    
    def _recognize_by_template(self, gray_img: np.ndarray) -> Optional[Card]:
        """Recognize card using template matching."""
        best_rank = None
        best_rank_score = 0
        
        # Match rank templates
        for rank, template in self.templates.items():
            result = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > best_rank_score:
                best_rank_score = max_val
                best_rank = rank
        
        if best_rank_score < 0.7:  # Threshold for match confidence
            return None
        
        best_suit = None
        best_suit_score = 0
        
        # Match suit templates
        for suit, template in self.suit_templates.items():
            result = cv2.matchTemplate(gray_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > best_suit_score:
                best_suit_score = max_val
                best_suit = suit
        
        if best_suit_score < 0.7:
            return None
        
        return Card(best_rank, best_suit)
    
    def _recognize_by_ocr(self, gray_img: np.ndarray) -> Optional[Card]:
        """Recognize card using OCR as fallback."""
        try:
            # Preprocess for OCR
            _, binary = cv2.threshold(gray_img, 127, 255, cv2.THRESH_BINARY)
            
            # Extract text
            text = pytesseract.image_to_string(binary, config='--psm 8 -c tessedit_char_whitelist=23456789TJQKA♠♥♦♣')
            text = text.strip().upper()
            
            # Parse rank and suit
            rank_match = re.search(r'[23456789TJQKA]', text)
            if not rank_match:
                return None
            
            rank = rank_match.group()
            
            # Detect suit by color analysis
            suit = self._detect_suit_by_color(gray_img)
            
            if suit:
                return Card(rank, suit)
            
        except Exception as e:
            logger.debug(f"OCR failed: {e}")
        
        return None
    
    def _detect_suit_by_color(self, img: np.ndarray) -> Optional[Suit]:
        """Detect suit by analyzing color in the image."""
        if len(img.shape) == 2:  # Grayscale
            return None
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for suits
        red_lower = np.array([0, 120, 70])
        red_upper = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        
        black_lower = np.array([0, 0, 0])
        black_upper = np.array([180, 255, 30])
        black_mask = cv2.inRange(hsv, black_lower, black_upper)
        
        red_pixels = cv2.countNonZero(red_mask)
        black_pixels = cv2.countNonZero(black_mask)
        
        if red_pixels > black_pixels * 1.5:
            # More red, likely hearts or diamonds
            # Could use shape detection to distinguish
            return Suit.HEART  # Simplified
        else:
            # More black, likely spades or clubs
            return Suit.SPADE  # Simplified
    
    def recognize_cards(self, img: np.ndarray, regions: List[Tuple[int, int, int, int]]) -> List[Card]:
        """Recognize multiple cards from an image given their regions."""
        cards = []
        for x1, y1, x2, y2 in regions:
            card_img = img[y1:y2, x1:x2]
            card = self.recognize_card(card_img)
            if card:
                cards.append(card)
        return cards


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT RECOGNITION
# ═══════════════════════════════════════════════════════════════════════════════

class TextRecognizer:
    """Recognizes text and numbers from poker table screenshots."""
    
    @staticmethod
    def extract_number(img: np.ndarray, preprocess: bool = True) -> Optional[float]:
        """Extract a number from an image region."""
        if img is None or img.size == 0:
            return None
        
        try:
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            if preprocess:
                # Enhance contrast
                gray = cv2.equalizeHist(gray)
                
                # Apply threshold
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Denoise
                binary = cv2.medianBlur(binary, 3)
            else:
                binary = gray
            
            # OCR configuration for numbers
            config = '--psm 7 -c tessedit_char_whitelist=0123456789.,$ '
            text = pytesseract.image_to_string(binary, config=config)
            
            # Clean and parse
            text = text.strip()
            text = re.sub(r'[^0-9.,]', '', text)
            text = text.replace(',', '')
            
            if text:
                return float(text)
        
        except Exception as e:
            logger.debug(f"Number extraction failed: {e}")
        
        return None
    
    @staticmethod
    def extract_text(img: np.ndarray, whitelist: str = None) -> str:
        """Extract text from an image region."""
        if img is None or img.size == 0:
            return ""
        
        try:
            # Convert to grayscale
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Preprocess
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # OCR configuration
            config = '--psm 8'
            if whitelist:
                config += f' -c tessedit_char_whitelist={whitelist}'
            
            text = pytesseract.image_to_string(binary, config=config)
            return text.strip()
        
        except Exception as e:
            logger.debug(f"Text extraction failed: {e}")
            return ""


# ═══════════════════════════════════════════════════════════════════════════════
# BUTTON AND CHIP DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

class ButtonDetector:
    """Detects dealer button and blind positions."""
    
    @staticmethod
    def detect_dealer_button(img: np.ndarray, seat_regions: Dict[int, TableRegion]) -> Optional[int]:
        """Detect which seat has the dealer button."""
        # Convert to HSV for color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define yellow color range for dealer button
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        
        # Find contours
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find circular contours (dealer button is typically circular)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:  # Too small
                continue
            
            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            if circularity > 0.7:  # Reasonably circular
                # Get center of contour
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # Check which seat region contains this point
                    for seat_num, region in seat_regions.items():
                        x1, y1, x2, y2 = region.get_coords()
                        if x1 <= cx <= x2 and y1 <= cy <= y2:
                            return seat_num
        
        return None
    
    @staticmethod
    def detect_blinds(img: np.ndarray, dealer_seat: int, active_seats: List[int]) -> Tuple[Optional[int], Optional[int]]:
        """Detect small blind and big blind positions based on dealer position."""
        if not dealer_seat or not active_seats:
            return None, None
        
        # Sort seats in clockwise order
        sorted_seats = sorted(active_seats)
        
        # Find dealer index
        try:
            dealer_idx = sorted_seats.index(dealer_seat)
        except ValueError:
            return None, None
        
        # Small blind is next active seat after dealer
        sb_idx = (dealer_idx + 1) % len(sorted_seats)
        sb_seat = sorted_seats[sb_idx]
        
        # Big blind is next active seat after small blind
        bb_idx = (dealer_idx + 2) % len(sorted_seats)
        bb_seat = sorted_seats[bb_idx]
        
        return sb_seat, bb_seat


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCREEN SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class PokerScreenScraper:
    """Main screen scraping engine for poker tables."""
    
    def __init__(self, site: PokerSite = PokerSite.GENERIC):
        self.site = site
        self.config = TableConfig.get_config(site)
        self.card_recognizer = CardRecognizer()
        self.text_recognizer = TextRecognizer()
        self.button_detector = ButtonDetector()
        
        # State tracking
        self.last_state = None
        self.state_history = []
        self.calibrated = False
        
        # Screenshot handler
        self.sct = mss.mss()
        
        # Threading for continuous capture
        self.capture_thread = None
        self.stop_event = Event()
        self.state_queue = Queue()
        self.lock = Lock()
    
    def find_poker_window(self) -> Optional[Dict]:
        """Find the poker table window."""
        # This would use platform-specific window enumeration
        # For now, we'll capture the primary monitor
        # In production, you'd use win32gui on Windows, etc.
        monitor = self.sct.monitors[1]  # Primary monitor
        return {
            "top": monitor["top"],
            "left": monitor["left"],
            "width": monitor["width"],
            "height": monitor["height"]
        }
    
    def capture_table(self) -> np.ndarray:
        """Capture the current poker table."""
        window = self.find_poker_window()
        if not window:
            raise RuntimeError("Poker window not found")
        
        # Capture screenshot
        screenshot = self.sct.grab(window)
        
        # Convert to numpy array
        img = np.array(screenshot)
        
        # Convert from BGRA to BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img
    
    def extract_pot_size(self, img: np.ndarray) -> float:
        """Extract pot size from the table."""
        pot_region = self.config['regions']['pot']
        pot_img = pot_region.extract_from_image(img)
        
        pot_size = self.text_recognizer.extract_number(pot_img)
        return pot_size if pot_size else 0.0
    
    def extract_hero_cards(self, img: np.ndarray) -> List[Card]:
        """Extract hero's hole cards."""
        hero_region = self.config['regions']['hero_cards']
        hero_img = hero_region.extract_from_image(img)
        
        # Split into two cards
        h, w = hero_img.shape[:2]
        card_width = w // 2
        
        cards = []
        for i in range(2):
            card_img = hero_img[:, i*card_width:(i+1)*card_width]
            card = self.card_recognizer.recognize_card(card_img)
            if card:
                cards.append(card)
        
        return cards
    
    def extract_board_cards(self, img: np.ndarray) -> List[Card]:
        """Extract community cards from the board."""
        board_region = self.config['regions']['board']
        board_img = board_region.extract_from_image(img)
        
        # Detect up to 5 cards
        h, w = board_img.shape[:2]
        card_width = w // 5
        
        cards = []
        for i in range(5):
            card_img = board_img[:, i*card_width:(i+1)*card_width]
            
            # Check if this region contains a card
            if self._is_card_present(card_img):
                card = self.card_recognizer.recognize_card(card_img)
                if card:
                    cards.append(card)
        
        return cards
    
    def _is_card_present(self, img: np.ndarray) -> bool:
        """Check if an image region contains a card."""
        if img is None or img.size == 0:
            return False
        
        # Check for card-like features (white background, etc.)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Cards typically have high contrast
        std_dev = np.std(gray)
        return std_dev > 30  # Threshold for card presence
    
    def extract_seat_info(self, img: np.ndarray) -> List[SeatInfo]:
        """Extract information for all seats."""
        seats = []
        
        for i in range(1, 10):  # 9-max table
            seat_key = f'seat_{i}'
            if seat_key not in self.config['regions']:
                continue
            
            region = self.config['regions'][seat_key]
            seat_img = region.extract_from_image(img)
            
            seat_info = SeatInfo(seat_number=i)
            
            # Check if seat is occupied
            if self._is_seat_active(seat_img):
                seat_info.is_active = True
                
                # Extract stack size
                stack_size = self.text_recognizer.extract_number(seat_img)
                if stack_size:
                    seat_info.stack_size = stack_size
            
            seats.append(seat_info)
        
        return seats
    
    def _is_seat_active(self, img: np.ndarray) -> bool:
        """Check if a seat is occupied by a player."""
        if img is None or img.size == 0:
            return False
        
        # Active seats typically have text (username, stack size)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Check for text presence
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        white_pixels = cv2.countNonZero(binary)
        
        # If there's significant white content, seat is likely active
        return white_pixels > (img.size * 0.1)
    
    def detect_game_stage(self, board_cards: List[Card]) -> str:
        """Determine the current game stage based on board cards."""
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
    
    def analyze_table(self, img: Optional[np.ndarray] = None) -> TableState:
        """Analyze the complete table state from an image."""
        if img is None:
            img = self.capture_table()
        
        state = TableState()
        
        # Extract pot size
        state.pot_size = self.extract_pot_size(img)
        
        # Extract hero cards
        state.hero_cards = self.extract_hero_cards(img)
        
        # Extract board cards
        state.board_cards = self.extract_board_cards(img)
        
        # Determine game stage
        state.stage = self.detect_game_stage(state.board_cards)
        
        # Extract seat information
        state.seats = self.extract_seat_info(img)
        
        # Count active players
        state.active_players = sum(1 for seat in state.seats if seat.is_active)
        
        # Detect dealer button
        seat_regions = {}
        for i in range(1, 10):
            seat_key = f'seat_{i}'
            if seat_key in self.config['regions']:
                seat_regions[i] = self.config['regions'][seat_key]
        
        state.dealer_seat = self.button_detector.detect_dealer_button(img, seat_regions)
        
        # Detect blinds
        if state.dealer_seat:
            active_seats = [s.seat_number for s in state.seats if s.is_active]
            sb_seat, bb_seat = self.button_detector.detect_blinds(img, state.dealer_seat, active_seats)
            
            for seat in state.seats:
                if seat.seat_number == sb_seat:
                    seat.is_small_blind = True
                elif seat.seat_number == bb_seat:
                    seat.is_big_blind = True
        
        # Identify hero seat (seat with visible cards)
        if state.hero_cards:
            # Hero is typically in a specific position (varies by site)
            # For now, assume seat 1 is hero
            state.hero_seat = 1
            for seat in state.seats:
                if seat.seat_number == 1:
                    seat.is_hero = True
                    seat.cards = state.hero_cards
        
        # Determine positions
        if state.dealer_seat and state.hero_seat:
            self._assign_positions(state)
        
        # Update state history
        with self.lock:
            self.last_state = state
            self.state_history.append(state)
            if len(self.state_history) > 100:
                self.state_history.pop(0)
        
        return state
    
    def _assign_positions(self, state: TableState):
        """Assign positions to all active seats."""
        if not state.dealer_seat:
            return
        
        active_seats = [s for s in state.seats if s.is_active]
        num_active = len(active_seats)
        
        if num_active < 2:
            return
        
        # Sort seats clockwise from dealer
        dealer_idx = next((i for i, s in enumerate(active_seats) if s.seat_number == state.dealer_seat), 0)
        
        # Position assignment based on number of players
        if num_active == 2:  # Heads up
            positions = [Position.BTN, Position.BB]
        elif num_active == 3:
            positions = [Position.BTN, Position.SB, Position.BB]
        elif num_active == 4:
            positions = [Position.BTN, Position.SB, Position.BB, Position.UTG]
        elif num_active == 5:
            positions = [Position.BTN, Position.SB, Position.BB, Position.UTG, Position.CO]
        elif num_active == 6:
            positions = [Position.BTN, Position.SB, Position.BB, Position.UTG, Position.MP1, Position.CO]
        else:  # 7-9 players
            positions = [Position.BTN, Position.SB, Position.BB, Position.UTG, Position.UTG1, 
                        Position.MP1, Position.MP2, Position.HJ, Position.CO][:num_active]
        
        # Assign positions
        for i, pos in enumerate(positions):
            seat_idx = (dealer_idx + i) % num_active
            active_seats[seat_idx].position = pos
    
    def start_continuous_capture(self, interval: float = 1.0):
        """Start continuous screen capture in background thread."""
        if self.capture_thread and self.capture_thread.is_alive():
            logger.warning("Capture already running")
            return
        
        self.stop_event.clear()
        self.capture_thread = Thread(target=self._capture_loop, args=(interval,))
        self.capture_thread.daemon = True
        self.capture_thread.start()
        logger.info("Started continuous capture")
    
    def _capture_loop(self, interval: float):
        """Background capture loop."""
        while not self.stop_event.is_set():
            try:
                state = self.analyze_table()
                self.state_queue.put(state)
                
                # Log significant changes
                if self._has_significant_change(state):
                    logger.info(f"Table update: Pot={state.pot_size}, Stage={state.stage}")
                
            except Exception as e:
                logger.error(f"Capture error: {e}")
            
            time.sleep(interval)
    
    def _has_significant_change(self, state: TableState) -> bool:
        """Check if state has changed significantly from last state."""
        if not self.last_state:
            return True
        
        # Check for stage change
        if state.stage != self.last_state.stage:
            return True
        
        # Check for new cards
        if len(state.board_cards) != len(self.last_state.board_cards):
            return True
        
        # Check for pot change
        if abs(state.pot_size - self.last_state.pot_size) > 1.0:
            return True
        
        return False
    
    def stop_continuous_capture(self):
        """Stop continuous capture."""
        if self.capture_thread:
            self.stop_event.set()
            self.capture_thread.join(timeout=2.0)
            logger.info("Stopped continuous capture")
    
    def get_latest_state(self) -> Optional[TableState]:
        """Get the most recent table state."""
        with self.lock:
            return self.last_state
    
    def get_state_updates(self, timeout: float = 0.1) -> Optional[TableState]:
        """Get state updates from the queue."""
        try:
            return self.state_queue.get(timeout=timeout)
        except:
            return None
    
    def calibrate(self, reference_img: Optional[np.ndarray] = None) -> bool:
        """Calibrate the scraper with a reference image."""
        if reference_img is None:
            reference_img = self.capture_table()
        
        # Verify we can detect key elements
        try:
            pot_size = self.extract_pot_size(reference_img)
            seats = self.extract_seat_info(reference_img)
            active_count = sum(1 for s in seats if s.is_active)
            
            if active_count >= 2:
                self.calibrated = True
                logger.info(f"Calibration successful: {active_count} active seats detected")
                return True
            else:
                logger.warning("Calibration failed: Not enough active seats")
                return False
                
        except Exception as e:
            logger.error(f"Calibration error: {e}")
            return False
    
    def save_debug_image(self, img: np.ndarray, filename: str = "debug_capture.png"):
        """Save annotated image for debugging."""
        debug_img = img.copy()
        
        # Draw regions
        for name, region in self.config['regions'].items():
            x1, y1, x2, y2 = region.get_coords()
            color = (0, 255, 0) if 'seat' in name else (255, 0, 0)
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(debug_img, name, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        cv2.imwrite(filename, debug_img)
        logger.info(f"Debug image saved to {filename}")


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION BRIDGE
# ═══════════════════════════════════════════════════════════════════════════════

class ScreenScraperBridge:
    """Bridge between screen scraper and poker assistant."""
    
    def __init__(self, scraper: PokerScreenScraper):
        self.scraper = scraper
        self.callbacks = []
    
    def register_callback(self, callback):
        """Register a callback for state updates."""
        self.callbacks.append(callback)
    
    def convert_to_game_state(self, table_state: TableState) -> Dict[str, Any]:
        """Convert table state to format expected by poker assistant."""
        hero_position = None
        if table_state.hero_seat:
            hero_seat_info = next((s for s in table_state.seats if s.seat_number == table_state.hero_seat), None)
            if hero_seat_info:
                hero_position = hero_seat_info.position
        
        # Calculate to_call (simplified - would need more logic for actual betting)
        to_call = 0.0
        if table_state.current_bet > 0:
            to_call = table_state.current_bet
        
        return {
            'hole_cards': table_state.hero_cards,
            'board_cards': table_state.board_cards,
            'position': hero_position,
            'pot': table_state.pot_size,
            'to_call': to_call,
            'num_players': table_state.active_players,
            'stage': table_state.stage,
            'dealer_seat': table_state.dealer_seat,
            'hero_seat': table_state.hero_seat
        }
    
    def process_update(self, table_state: TableState):
        """Process a table state update."""
        game_state = self.convert_to_game_state(table_state)
        
        # Notify all callbacks
        for callback in self.callbacks:
            try:
                callback(game_state)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING AND DEBUGGING
# ═══════════════════════════════════════════════════════════════════════════════

def test_screen_scraper():
    """Test the screen scraper functionality."""
    logger.info("Testing Poker Screen Scraper...")
    
    # Initialize scraper
    scraper = PokerScreenScraper(PokerSite.GENERIC)
    
    # Try to calibrate
    if not scraper.calibrate():
        logger.warning("Calibration failed, continuing anyway...")
    
    # Capture and analyze
    try:
        state = scraper.analyze_table()
        
        print("\n" + "="*60)
        print("TABLE STATE ANALYSIS")
        print("="*60)
        print(f"Pot Size: ${state.pot_size:.2f}")
        print(f"Stage: {state.stage}")
        print(f"Active Players: {state.active_players}")
        print(f"Hero Cards: {state.hero_cards}")
        print(f"Board Cards: {state.board_cards}")
        print(f"Dealer Seat: {state.dealer_seat}")
        
        print("\nSeat Information:")
        for seat in state.seats:
            if seat.is_active:
                print(f"  Seat {seat.seat_number}: "
                      f"{'HERO' if seat.is_hero else 'Player'} "
                      f"(Stack: ${seat.stack_size:.2f if seat.stack_size else 0:.2f}) "
                      f"{'[D]' if seat.has_dealer_button else ''}"
                      f"{'[SB]' if seat.is_small_blind else ''}"
                      f"{'[BB]' if seat.is_big_blind else ''}")
        
        # Save debug image
        img = scraper.capture_table()
        scraper.save_debug_image(img)
        
        print("\nDebug image saved to debug_capture.png")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_screen_scraper()
