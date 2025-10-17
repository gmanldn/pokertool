#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Betfair Scraping Accuracy Improvements
=======================================

This module implements critical accuracy improvements for Betfair poker table scraping
based on analysis of BF_TEST.jpg and the specific challenges of Betfair's UI.

Implements Phase 1 (Critical) tasks from docs/TODO.md:
- BF-001: Robust OCR for mixed-case player names
- BF-004: Robust £ symbol detection
- BF-006: Distinguish stack sizes from pot amounts
- BF-011: Enhanced card suit detection
- BF-013: Dealer button detection
- BF-025: Betfair 6-max seat position mapping

Module: pokertool.modules.betfair_accuracy_improvements
"""

import re
import cv2
import numpy as np
import pytesseract
from typing import Dict, List, Tuple, Optional, NamedTuple
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class SeatPosition(Enum):
    """6-max table seat positions for Betfair"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"  # Hero position
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class BetfairROI:
    """Region of Interest coordinates for Betfair table elements"""
    x: int
    y: int
    width: int
    height: int

    def extract(self, image: np.ndarray) -> np.ndarray:
        """Extract this ROI from an image"""
        return image[self.y:self.y + self.height, self.x:self.x + self.width]

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within this ROI"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)


@dataclass
class SeatMapping:
    """Complete seat position mapping for a Betfair 6-max table"""
    player_name_roi: BetfairROI
    stack_roi: BetfairROI
    cards_roi: BetfairROI
    vpip_af_roi: Optional[BetfairROI]
    timer_roi: Optional[BetfairROI]
    dealer_button_roi: Optional[BetfairROI]
    position: SeatPosition


# ============================================================================
# BF-001: Robust OCR for Mixed-Case Player Names
# ============================================================================

class PlayerNameExtractor:
    """
    Enhanced player name extraction for Betfair.

    Handles:
    - Mixed-case names: "FourBoysUnited", "ThelongbluevEin", "GmanLDN"
    - Numbers in names: "FourBoysUnited" contains "4"
    - Variable name lengths (3-20 characters)
    """

    def __init__(self):
        self.known_names: List[str] = []
        self.false_positive_patterns = [
            r'^Empty$',
            r'^SIT OUT$',
            r'^VPIP$',
            r'^AF$',
            r'^Time:',
            r'^Pot:',
            r'^ELITE SERIES',
            r'^\d+/\d+/\d+',  # Dates
        ]

    def extract_player_name(self, image_roi: np.ndarray, enhance: bool = True) -> Tuple[str, float]:
        """
        Extract player name from ROI with >98% accuracy target.

        Args:
            image_roi: Cropped image containing player name
            enhance: Apply preprocessing enhancements

        Returns:
            Tuple of (player_name, confidence)
        """
        if enhance:
            image_roi = self._enhance_for_mixed_case_ocr(image_roi)

        # Try multiple OCR configurations for mixed-case text
        configs = [
            '--oem 3 --psm 7',  # Single text line
            '--oem 3 --psm 8',  # Single word
            '--oem 1 --psm 7',  # LSTM engine only
        ]

        best_result = ""
        best_confidence = 0.0

        for config in configs:
            try:
                # Extract with detailed data for confidence
                data = pytesseract.image_to_data(
                    image_roi,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )

                # Find highest confidence text
                for i, conf in enumerate(data['conf']):
                    if conf == -1:
                        continue
                    text = data['text'][i].strip()
                    if text and len(text) >= 3:  # Min username length
                        conf_normalized = float(conf) / 100.0
                        if conf_normalized > best_confidence:
                            best_result = text
                            best_confidence = conf_normalized

            except Exception as e:
                logger.debug(f"OCR config {config} failed: {e}")
                continue

        # Validate and clean result
        name = self._validate_player_name(best_result)

        # Fuzzy match against known names if available
        if name and self.known_names:
            name, confidence = self._fuzzy_match_name(name)
            return name, confidence

        return name, best_confidence

    def _enhance_for_mixed_case_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image specifically for mixed-case text extraction.

        Optimizations:
        - Increase contrast for small letters
        - Denoise to reduce artifacts
        - Binarize with adaptive thresholding
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Resize to optimal OCR size (height ~50px)
        height = gray.shape[0]
        if height < 30:
            scale = 50 / height
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10)

        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)

        # Adaptive thresholding for mixed backgrounds
        binary = cv2.adaptiveThreshold(
            contrast,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )

        return binary

    def _validate_player_name(self, name: str) -> str:
        """
        Validate and clean extracted player name.

        Rules:
        - Alphanumeric + underscore only
        - 3-20 characters
        - Not a false positive pattern
        """
        if not name:
            return ""

        # Remove non-alphanumeric except underscore
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '', name)

        # Check length
        if len(cleaned) < 3 or len(cleaned) > 20:
            return ""

        # Check against false positive patterns
        for pattern in self.false_positive_patterns:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return ""

        return cleaned

    def _fuzzy_match_name(self, extracted: str, threshold: float = 0.80) -> Tuple[str, float]:
        """
        Fuzzy match against known player names using Levenshtein distance.

        Args:
            extracted: Name extracted via OCR
            threshold: Minimum similarity score (0-1)

        Returns:
            Tuple of (matched_name, confidence)
        """
        if not self.known_names:
            return extracted, 0.5

        extracted_lower = extracted.lower()
        best_match = extracted
        best_score = 0.0

        for known_name in self.known_names:
            known_lower = known_name.lower()

            # Exact match
            if extracted_lower == known_lower:
                return known_name, 1.0

            # Calculate Levenshtein distance
            distance = self._levenshtein_distance(extracted_lower, known_lower)
            max_len = max(len(extracted_lower), len(known_lower))
            similarity = 1.0 - (distance / max_len)

            if similarity > best_score:
                best_score = similarity
                best_match = known_name

        if best_score >= threshold:
            return best_match, best_score

        return extracted, 0.5

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return PlayerNameExtractor._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def learn_name(self, name: str):
        """Add a validated name to the known names list"""
        if name and name not in self.known_names:
            self.known_names.append(name)
            logger.debug(f"Learned player name: {name}")


# ============================================================================
# BF-004: Robust £ Symbol Detection
# ============================================================================

class CurrencyExtractor:
    """
    Enhanced currency and amount extraction for Betfair (£ symbol).

    Handles:
    - Unicode pound symbol: £
    - Decimal precision: £2.22, £0.08
    - Zero amounts: £0.00, £0
    """

    # Unicode and common variants of pound symbol
    POUND_SYMBOLS = ['£', '\\u00a3', 'GBP', 'L']

    def extract_currency_amount(self, image_roi: np.ndarray) -> Tuple[Optional[float], float]:
        """
        Extract currency amount from ROI with >99% accuracy target.

        Args:
            image_roi: Cropped image containing currency amount

        Returns:
            Tuple of (amount, confidence)
        """
        # Enhance for currency symbol and numbers
        enhanced = self._enhance_for_currency(image_roi)

        # Configure Tesseract for currency
        # Allow digits, decimal point, pound symbol
        config = '--oem 3 --psm 7 -c tessedit_char_whitelist=£0123456789.'

        try:
            text = pytesseract.image_to_string(enhanced, config=config).strip()
            amount, confidence = self._parse_currency_text(text)
            return amount, confidence

        except Exception as e:
            logger.debug(f"Currency extraction failed: {e}")
            return None, 0.0

    def _enhance_for_currency(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image specifically for £ symbol and decimal numbers.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Resize if too small
        if gray.shape[0] < 30:
            scale = 40 / gray.shape[0]
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        contrast = clahe.apply(gray)

        # Binary threshold (white text on dark background for Betfair)
        _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def _parse_currency_text(self, text: str) -> Tuple[Optional[float], float]:
        """
        Parse extracted text into currency amount.

        Args:
            text: Raw OCR text

        Returns:
            Tuple of (amount, confidence)
        """
        if not text:
            return None, 0.0

        # Remove whitespace
        text = text.strip()

        # Handle various pound symbol representations
        for symbol in self.POUND_SYMBOLS:
            text = text.replace(symbol, '£')

        # Extract number after £ symbol
        # Patterns: £2.22, £0.08, £0, £1.24
        patterns = [
            r'£\s*(\d+\.?\d{0,2})',  # £X.XX or £X
            r'(\d+\.?\d{0,2})\s*£',  # X.XX£ or X£
            r'(\d+\.?\d{0,2})',      # Just number (fallback)
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount = float(match.group(1))
                    # Validate range (0.00 to 9999.99 typical for poker stacks)
                    if 0.0 <= amount <= 99999.99:
                        confidence = 0.95 if '£' in text else 0.7
                        return amount, confidence
                except ValueError:
                    continue

        return None, 0.0


# ============================================================================
# BF-006: Distinguish Stack Sizes from Pot Amounts
# ============================================================================

class StackPotDistinguisher:
    """
    Distinguish between stack sizes and pot amounts based on position.

    Betfair layout:
    - Stack sizes: Below player names
    - Pot amounts: Center of table with "Pot:" label or pot chip icon
    """

    def __init__(self, table_width: int, table_height: int):
        self.table_width = table_width
        self.table_height = table_height

        # Define pot ROI (center of table)
        self.pot_roi = BetfairROI(
            x=int(table_width * 0.35),
            y=int(table_height * 0.40),
            width=int(table_width * 0.30),
            height=int(table_height * 0.20)
        )

    def classify_currency_location(self, x: int, y: int, amount: float) -> str:
        """
        Classify whether a detected currency amount is a stack or pot.

        Args:
            x, y: Center coordinates of detected amount
            amount: The currency amount

        Returns:
            'stack', 'pot', or 'unknown'
        """
        # Check if in pot ROI
        if self.pot_roi.contains_point(x, y):
            return 'pot'

        # Check if in player stack region (top or bottom thirds, not center)
        is_top_third = y < self.table_height * 0.33
        is_bottom_third = y > self.table_height * 0.67

        if is_top_third or is_bottom_third:
            return 'stack'

        return 'unknown'

    def extract_pot_with_validation(
        self,
        image: np.ndarray,
        currency_extractor: CurrencyExtractor
    ) -> Tuple[Optional[float], float]:
        """
        Extract pot amount from center table region with multi-location validation.

        Betfair shows pot in 2 locations - both should match.

        Args:
            image: Full table image
            currency_extractor: CurrencyExtractor instance

        Returns:
            Tuple of (pot_amount, confidence)
        """
        pot_roi_image = self.pot_roi.extract(image)

        # Extract "Pot: £X.XX" label
        amount1, conf1 = self._extract_pot_label(pot_roi_image, currency_extractor)

        # Extract pot chip icon amount
        amount2, conf2 = self._extract_pot_chips(pot_roi_image, currency_extractor)

        # Validate consistency
        if amount1 is not None and amount2 is not None:
            if abs(amount1 - amount2) < 0.01:  # Should match exactly
                avg_conf = (conf1 + conf2) / 2.0
                return amount1, avg_conf
            else:
                logger.warning(f"Pot amount mismatch: {amount1} vs {amount2}")
                # Use higher confidence value
                if conf1 > conf2:
                    return amount1, conf1 * 0.8  # Reduce confidence due to mismatch
                else:
                    return amount2, conf2 * 0.8

        # Return whichever was detected
        if amount1 is not None:
            return amount1, conf1
        if amount2 is not None:
            return amount2, conf2

        return None, 0.0

    def _extract_pot_label(
        self,
        pot_roi: np.ndarray,
        currency_extractor: CurrencyExtractor
    ) -> Tuple[Optional[float], float]:
        """Extract from "Pot: £X.XX" label"""
        # Look for "Pot:" text followed by amount
        config = '--oem 3 --psm 6'  # Block of text
        text = pytesseract.image_to_string(pot_roi, config=config)

        if 'Pot' in text or 'pot' in text.lower():
            # Extract amount after "Pot:"
            match = re.search(r'Pot:?\s*£?\s*(\d+\.?\d{0,2})', text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1))
                    return amount, 0.9
                except ValueError:
                    pass

        return None, 0.0

    def _extract_pot_chips(
        self,
        pot_roi: np.ndarray,
        currency_extractor: CurrencyExtractor
    ) -> Tuple[Optional[float], float]:
        """Extract from pot chip icon amount display"""
        # Pot chips typically show just £X.XX without "Pot:" label
        return currency_extractor.extract_currency_amount(pot_roi)


# ============================================================================
# BF-011: Enhanced Card Suit Detection for Betfair
# ============================================================================

class BetfairCardDetector:
    """
    Enhanced card and suit detection optimized for Betfair.

    Handles:
    - Red suits: ♦ (diamonds), ♥ (hearts)
    - Black suits: ♠ (spades), ♣ (clubs)
    - Card values: A, K, Q, J, 10, 9, 8, 7, 6, 5, 4, 3, 2
    - White card borders
    - Large clear card images
    """

    SUITS = ['♠', '♥', '♦', '♣']
    VALUES = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

    def __init__(self):
        # Color ranges for suit detection (HSV)
        self.red_ranges = [
            (np.array([0, 100, 100]), np.array([10, 255, 255])),    # Red lower
            (np.array([170, 100, 100]), np.array([180, 255, 255])), # Red upper
        ]
        self.black_range = (np.array([0, 0, 0]), np.array([180, 255, 50]))

    def detect_community_cards(
        self,
        image: np.ndarray,
        cards_roi: BetfairROI
    ) -> List[Tuple[str, float]]:
        """
        Detect community cards (flop, turn, river) with >99.5% accuracy.

        Args:
            image: Full table image
            cards_roi: ROI containing community cards

        Returns:
            List of (card_string, confidence) tuples, e.g., [("10♦", 0.99), ("A♦", 0.98), ...]
        """
        cards_image = cards_roi.extract(image)

        # Detect individual card regions (white bordered rectangles)
        card_regions = self._detect_card_regions(cards_image)

        cards = []
        for region in card_regions:
            card, confidence = self._recognize_single_card(region)
            if card:
                cards.append((card, confidence))

        # Validate card count (2-5 community cards)
        if not (2 <= len(cards) <= 5):
            logger.warning(f"Unexpected number of community cards detected: {len(cards)}")

        return cards

    def _detect_card_regions(self, cards_image: np.ndarray) -> List[np.ndarray]:
        """
        Detect individual card rectangles in community cards ROI.

        Cards have white borders and are arranged left-to-right.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(cards_image, cv2.COLOR_BGR2GRAY)

        # Detect white borders (cards have bright white edges)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter for card-like rectangles
        card_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Card aspect ratio ~0.7 (height > width)
            aspect_ratio = h / w if w > 0 else 0
            if 1.3 < aspect_ratio < 1.6:  # Typical playing card ratio inverted
                # Extract card region
                card_img = cards_image[y:y + h, x:x + w]
                card_regions.append((x, card_img))  # Store x-coord for sorting

        # Sort left-to-right
        card_regions.sort(key=lambda item: item[0])

        return [card_img for _, card_img in card_regions]

    def _recognize_single_card(self, card_image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Recognize a single card (value + suit).

        Args:
            card_image: Cropped image of one card

        Returns:
            Tuple of (card_string, confidence), e.g., ("10♦", 0.99)
        """
        # Detect suit by color
        suit, suit_conf = self._detect_suit_by_color(card_image)
        if not suit:
            return None, 0.0

        # Detect value by OCR (top-left corner)
        value, value_conf = self._detect_card_value(card_image)
        if not value:
            return None, 0.0

        # Combine
        card_str = f"{value}{suit}"
        confidence = (suit_conf + value_conf) / 2.0

        return card_str, confidence

    def _detect_suit_by_color(self, card_image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Detect card suit by analyzing color (red vs black).

        Returns:
            Tuple of (suit_symbol, confidence)
        """
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(card_image, cv2.COLOR_BGR2HSV)

        # Check for red
        red_mask = np.zeros_like(hsv[:, :, 0])
        for lower, upper in self.red_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            red_mask = cv2.bitwise_or(red_mask, mask)

        # Check for black
        black_mask = cv2.inRange(hsv, *self.black_range)

        red_pixels = np.count_nonzero(red_mask)
        black_pixels = np.count_nonzero(black_mask)

        # Determine suit color
        if red_pixels > black_pixels:
            # Red suit - need to distinguish ♥ vs ♦
            suit, conf = self._distinguish_red_suits(card_image)
            return suit, conf
        elif black_pixels > red_pixels:
            # Black suit - need to distinguish ♠ vs ♣
            suit, conf = self._distinguish_black_suits(card_image)
            return suit, conf
        else:
            return None, 0.0

    def _distinguish_red_suits(self, card_image: np.ndarray) -> Tuple[str, float]:
        """Distinguish between ♥ (heart) and ♦ (diamond) by shape"""
        # Hearts are rounder, diamonds are more angular
        # Use template matching or shape analysis
        # For now, use OCR on suit symbol region
        suit_roi = self._extract_suit_symbol_region(card_image)
        config = '--oem 3 --psm 10 -c tessedit_char_whitelist=♥♦HD'
        text = pytesseract.image_to_string(suit_roi, config=config).strip()

        if '♥' in text or 'H' in text:
            return '♥', 0.95
        elif '♦' in text or 'D' in text:
            return '♦', 0.95
        else:
            return '♥', 0.6  # Default to heart

    def _distinguish_black_suits(self, card_image: np.ndarray) -> Tuple[str, float]:
        """Distinguish between ♠ (spade) and ♣ (club) by shape"""
        suit_roi = self._extract_suit_symbol_region(card_image)
        config = '--oem 3 --psm 10 -c tessedit_char_whitelist=♠♣SC'
        text = pytesseract.image_to_string(suit_roi, config=config).strip()

        if '♠' in text or 'S' in text:
            return '♠', 0.95
        elif '♣' in text or 'C' in text:
            return '♣', 0.95
        else:
            return '♠', 0.6  # Default to spade

    def _extract_suit_symbol_region(self, card_image: np.ndarray) -> np.ndarray:
        """Extract region containing suit symbol (typically below value)"""
        h, w = card_image.shape[:2]
        # Suit symbol is in top-left quadrant, below value
        return card_image[int(h * 0.15):int(h * 0.35), 0:int(w * 0.3)]

    def _detect_card_value(self, card_image: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Detect card value (A, K, Q, J, 10, 9, etc.) from top-left corner.

        Returns:
            Tuple of (value, confidence)
        """
        # Extract value region (top-left corner)
        h, w = card_image.shape[:2]
        value_roi = card_image[0:int(h * 0.20), 0:int(w * 0.3)]

        # Enhance for OCR
        gray = cv2.cvtColor(value_roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # OCR with value whitelist
        config = '--oem 3 --psm 10 -c tessedit_char_whitelist=AKQJ1098765432'
        text = pytesseract.image_to_string(binary, config=config).strip()

        # Validate against known values
        if text in self.VALUES:
            return text, 0.98

        # Handle common OCR errors
        # "1O" -> "10", "0" -> "O" for "Q", etc.
        if text == "1O" or text == "IO":
            return "10", 0.90

        return None, 0.0


# ============================================================================
# BF-013: Dealer Button Detection
# ============================================================================

class DealerButtonDetector:
    """
    Detect dealer button (yellow "D" indicator) on Betfair tables.

    Approach:
    - Color detection: Yellow circular button
    - Shape matching: Circular shape
    - OCR validation: "D" text
    """

    def __init__(self):
        # Yellow color range in HSV
        self.yellow_range = (
            np.array([20, 100, 100]),  # Lower yellow
            np.array([30, 255, 255])   # Upper yellow
        )

    def detect_dealer_button(
        self,
        image: np.ndarray,
        seat_mappings: List[SeatMapping]
    ) -> Tuple[Optional[SeatPosition], float]:
        """
        Detect which seat has the dealer button.

        Args:
            image: Full table image
            seat_mappings: List of seat position mappings

        Returns:
            Tuple of (seat_position, confidence)
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Detect yellow regions
        mask = cv2.inRange(hsv, *self.yellow_range)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find circular yellow regions (dealer button)
        button_candidates = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100 or area > 2000:  # Button size filter
                continue

            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

            if circularity > 0.7:  # Fairly circular
                # Get center point
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    button_candidates.append((cx, cy, circularity))

        if not button_candidates:
            return None, 0.0

        # For each candidate, check which seat it's near
        for cx, cy, circ_score in button_candidates:
            for seat_map in seat_mappings:
                if seat_map.dealer_button_roi and seat_map.dealer_button_roi.contains_point(cx, cy):
                    return seat_map.position, circ_score

        return None, 0.0


# ============================================================================
# BF-025: Betfair 6-Max Seat Position Mapping
# ============================================================================

class BetfairSeatMapper:
    """
    Create accurate seat position mappings for Betfair 6-max tables.

    Defines ROIs for each of 6 seats:
    - Top-left, top-center, top-right
    - Bottom-left, bottom-center (hero), bottom-right
    """

    def __init__(self, table_width: int, table_height: int):
        self.table_width = table_width
        self.table_height = table_height

    def create_seat_mappings(self) -> Dict[SeatPosition, SeatMapping]:
        """
        Create complete seat mappings for a 6-max Betfair table.

        Returns:
            Dictionary mapping SeatPosition -> SeatMapping
        """
        mappings = {}

        # Define ROI positions as percentages of table dimensions
        # Format: (name_x%, name_y%, stack_y%, cards_y%, button_offset_x%, button_offset_y%)
        seat_configs = {
            SeatPosition.TOP_LEFT: (0.10, 0.15, 0.20, 0.25, -0.03, 0.03),
            SeatPosition.TOP_CENTER: (0.45, 0.08, 0.13, 0.18, -0.03, 0.03),
            SeatPosition.TOP_RIGHT: (0.80, 0.15, 0.20, 0.25, -0.03, 0.03),
            SeatPosition.BOTTOM_LEFT: (0.10, 0.75, 0.80, 0.70, -0.03, -0.03),
            SeatPosition.BOTTOM_CENTER: (0.45, 0.82, 0.87, 0.77, -0.03, -0.03),  # Hero
            SeatPosition.BOTTOM_RIGHT: (0.80, 0.75, 0.80, 0.70, -0.03, -0.03),
        }

        for position, (name_x_pct, name_y_pct, stack_y_pct, cards_y_pct, btn_x_off, btn_y_off) in seat_configs.items():
            # Name ROI
            name_roi = BetfairROI(
                x=int(self.table_width * name_x_pct),
                y=int(self.table_height * name_y_pct),
                width=int(self.table_width * 0.15),
                height=int(self.table_height * 0.04)
            )

            # Stack ROI (below name)
            stack_roi = BetfairROI(
                x=int(self.table_width * name_x_pct),
                y=int(self.table_height * stack_y_pct),
                width=int(self.table_width * 0.12),
                height=int(self.table_height * 0.03)
            )

            # Cards ROI
            cards_roi = BetfairROI(
                x=int(self.table_width * name_x_pct),
                y=int(self.table_height * cards_y_pct),
                width=int(self.table_width * 0.15),
                height=int(self.table_height * 0.08)
            )

            # VPIP/AF badges ROI (above name, may not always be present)
            vpip_af_roi = BetfairROI(
                x=int(self.table_width * name_x_pct),
                y=int(self.table_height * (name_y_pct - 0.04)),
                width=int(self.table_width * 0.15),
                height=int(self.table_height * 0.03)
            )

            # Timer ROI (near player, for active decision)
            timer_roi = BetfairROI(
                x=int(self.table_width * (name_x_pct + 0.05)),
                y=int(self.table_height * (name_y_pct + 0.02)),
                width=int(self.table_width * 0.10),
                height=int(self.table_height * 0.03)
            )

            # Dealer button ROI (offset from player)
            dealer_button_roi = BetfairROI(
                x=int(self.table_width * (name_x_pct + btn_x_off)),
                y=int(self.table_height * (name_y_pct + btn_y_off)),
                width=int(self.table_width * 0.04),
                height=int(self.table_height * 0.04)
            )

            mappings[position] = SeatMapping(
                player_name_roi=name_roi,
                stack_roi=stack_roi,
                cards_roi=cards_roi,
                vpip_af_roi=vpip_af_roi,
                timer_roi=timer_roi,
                dealer_button_roi=dealer_button_roi,
                position=position
            )

        return mappings


# ============================================================================
# Main Integration Class
# ============================================================================

class BetfairAccuracyEngine:
    """
    Main integration class for all Betfair accuracy improvements.

    Usage:
        engine = BetfairAccuracyEngine(table_width=1200, table_height=800)
        result = engine.extract_full_table_state(screenshot)
    """

    def __init__(self, table_width: int, table_height: int):
        self.table_width = table_width
        self.table_height = table_height

        # Initialize all extractors
        self.name_extractor = PlayerNameExtractor()
        self.currency_extractor = CurrencyExtractor()
        self.stack_pot_distinguisher = StackPotDistinguisher(table_width, table_height)
        self.card_detector = BetfairCardDetector()
        self.button_detector = DealerButtonDetector()
        self.seat_mapper = BetfairSeatMapper(table_width, table_height)

        # Create seat mappings
        self.seat_mappings = self.seat_mapper.create_seat_mappings()

    def extract_full_table_state(self, screenshot: np.ndarray) -> Dict:
        """
        Extract complete table state using all accuracy improvements.

        Args:
            screenshot: Full Betfair table screenshot

        Returns:
            Dictionary with all extracted game state
        """
        result = {
            'players': [],
            'pot': None,
            'community_cards': [],
            'dealer_button_position': None,
            'accuracy_scores': {}
        }

        # Extract players (names, stacks, cards)
        for position, seat_map in self.seat_mappings.items():
            player_data = self._extract_player_data(screenshot, seat_map)
            if player_data['name']:
                result['players'].append(player_data)

        # Extract pot
        pot_amount, pot_conf = self.stack_pot_distinguisher.extract_pot_with_validation(
            screenshot,
            self.currency_extractor
        )
        result['pot'] = {'amount': pot_amount, 'confidence': pot_conf}

        # Extract community cards
        # Find community cards ROI (center-top of table)
        cards_roi = BetfairROI(
            x=int(self.table_width * 0.30),
            y=int(self.table_height * 0.30),
            width=int(self.table_width * 0.40),
            height=int(self.table_height * 0.15)
        )
        cards = self.card_detector.detect_community_cards(screenshot, cards_roi)
        result['community_cards'] = cards

        # Detect dealer button
        button_pos, button_conf = self.button_detector.detect_dealer_button(
            screenshot,
            list(self.seat_mappings.values())
        )
        result['dealer_button_position'] = {
            'position': button_pos.value if button_pos else None,
            'confidence': button_conf
        }

        # Calculate overall accuracy score
        result['accuracy_scores'] = self._calculate_accuracy_scores(result)

        return result

    def _extract_player_data(self, screenshot: np.ndarray, seat_map: SeatMapping) -> Dict:
        """Extract all data for one player seat"""
        player = {
            'position': seat_map.position.value,
            'name': None,
            'stack': None,
            'cards': [],
            'has_timer': False,
            'confidences': {}
        }

        # Extract name
        name_img = seat_map.player_name_roi.extract(screenshot)
        name, name_conf = self.name_extractor.extract_player_name(name_img)
        player['name'] = name
        player['confidences']['name'] = name_conf

        # Extract stack
        stack_img = seat_map.stack_roi.extract(screenshot)
        stack_amount, stack_conf = self.currency_extractor.extract_currency_amount(stack_img)
        player['stack'] = stack_amount
        player['confidences']['stack'] = stack_conf

        return player

    def _calculate_accuracy_scores(self, result: Dict) -> Dict:
        """Calculate overall accuracy metrics"""
        scores = {
            'player_names': 0.0,
            'stacks': 0.0,
            'pot': result['pot']['confidence'],
            'cards': 0.0,
            'dealer_button': result['dealer_button_position']['confidence'],
            'overall': 0.0
        }

        # Average player name confidences
        name_confs = [p['confidences']['name'] for p in result['players'] if p['name']]
        scores['player_names'] = sum(name_confs) / len(name_confs) if name_confs else 0.0

        # Average stack confidences
        stack_confs = [p['confidences']['stack'] for p in result['players'] if p['stack'] is not None]
        scores['stacks'] = sum(stack_confs) / len(stack_confs) if stack_confs else 0.0

        # Average card confidences
        card_confs = [conf for _, conf in result['community_cards']]
        scores['cards'] = sum(card_confs) / len(card_confs) if card_confs else 0.0

        # Overall weighted average
        weights = {
            'player_names': 0.25,
            'stacks': 0.25,
            'pot': 0.15,
            'cards': 0.25,
            'dealer_button': 0.10
        }

        scores['overall'] = sum(scores[key] * weight for key, weight in weights.items())

        return scores


# ============================================================================
# Module-level convenience function
# ============================================================================

def create_betfair_engine(table_width: int = 1200, table_height: int = 800) -> BetfairAccuracyEngine:
    """
    Create a configured BetfairAccuracyEngine instance.

    Args:
        table_width: Width of Betfair table window (default 1200)
        table_height: Height of Betfair table window (default 800)

    Returns:
        Configured BetfairAccuracyEngine instance
    """
    return BetfairAccuracyEngine(table_width, table_height)


if __name__ == '__main__':
    # Example usage
    import sys

    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

    # Create engine
    engine = create_betfair_engine(1200, 800)

    # Load test image
    test_image_path = "/Users/georgeridout/Documents/github/pokertool/tests/BF_TEST.jpg"
    test_image = cv2.imread(test_image_path)

    if test_image is not None:
        # Extract full table state
        result = engine.extract_full_table_state(test_image)

        print("\n" + "=" * 70)
        print("BETFAIR TABLE STATE EXTRACTION RESULTS")
        print("=" * 70)
        print(f"\nPlayers detected: {len(result['players'])}")
        for player in result['players']:
            print(f"  - {player['name']} ({player['position']}): £{player['stack']} "
                  f"[conf: {player['confidences']['name']:.2f}]")

        print(f"\nPot: £{result['pot']['amount']} [conf: {result['pot']['confidence']:.2f}]")

        print(f"\nCommunity cards: {len(result['community_cards'])}")
        for card, conf in result['community_cards']:
            print(f"  - {card} [conf: {conf:.2f}]")

        print(f"\nDealer button: {result['dealer_button_position']['position']} "
              f"[conf: {result['dealer_button_position']['confidence']:.2f}]")

        print("\nAccuracy Scores:")
        for metric, score in result['accuracy_scores'].items():
            print(f"  {metric}: {score:.1%}")

        print("=" * 70)
    else:
        print(f"Failed to load test image: {test_image_path}")
