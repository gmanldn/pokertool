"""
Multi-Template Card Matching System
====================================

Supports multiple card deck styles with intelligent template matching and voting:

1. Classic deck style (traditional designs)
2. Modern deck style (contemporary designs)
3. Large-pip deck style (visibility-optimized)
4. Four-color deck style (red, blue, green, black suits)

Features:
- Multiple template libraries for different deck styles
- Automatic deck style detection
- Voting system for ambiguous matches
- Template confidence scoring
- Adaptive template selection

Target: Support all major online poker deck styles with >99% accuracy
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import Counter

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    from .card_recognizer import Card, RecognitionResult, RANKS, SUITS
    BASE_RECOGNIZER_AVAILABLE = True
except ImportError:
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


class DeckStyle(Enum):
    """Supported deck styles."""
    CLASSIC = "classic"
    MODERN = "modern"
    LARGE_PIP = "large_pip"
    FOUR_COLOR = "four_color"
    AUTO = "auto"  # Automatic detection


@dataclass
class TemplateMatch:
    """Single template match result."""
    card: Card
    confidence: float
    deck_style: DeckStyle
    scale: float
    location: Tuple[int, int, int, int]


@dataclass
class CardTemplate:
    """Card template for a specific deck style."""
    rank: str
    suit: str
    deck_style: DeckStyle
    template_image: np.ndarray
    width: int
    height: int


class MultiTemplateMatcher:
    """
    Multi-template card matching system with support for multiple deck styles.

    Uses template voting across deck styles to handle various poker client designs.
    """

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        enabled_styles: Optional[List[DeckStyle]] = None,
        min_confidence: float = 0.85,
        auto_detect_style: bool = True
    ):
        """
        Initialize multi-template matcher.

        Args:
            template_dir: Directory containing template images
            enabled_styles: List of enabled deck styles (None = all)
            min_confidence: Minimum match confidence threshold
            auto_detect_style: Automatically detect deck style
        """
        self.available = CV2_AVAILABLE
        self.template_dir = template_dir or Path(__file__).parent / "card_templates" / "multi_style"
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Enabled deck styles
        if enabled_styles is None:
            self.enabled_styles = [
                DeckStyle.CLASSIC,
                DeckStyle.MODERN,
                DeckStyle.LARGE_PIP,
                DeckStyle.FOUR_COLOR
            ]
        else:
            self.enabled_styles = enabled_styles

        self.min_confidence = min_confidence
        self.auto_detect_style = auto_detect_style
        self.detected_style: Optional[DeckStyle] = None

        # Template library: {deck_style: {card_str: [templates]}}
        self.template_library: Dict[DeckStyle, Dict[str, List[CardTemplate]]] = {
            style: {} for style in self.enabled_styles
        }

        # Scales for multi-scale template matching
        self.scales = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]

        # Statistics
        self.match_stats = {
            'total_matches': 0,
            'by_style': {style: 0 for style in DeckStyle if style != DeckStyle.AUTO},
            'style_detection_accuracy': 0.0
        }

        if not self.available:
            logger.warning("Multi-template matcher unavailable: OpenCV not installed")

        # Load templates if available
        self._load_template_library()

    def match_card(
        self,
        card_image: np.ndarray,
        deck_style: Optional[DeckStyle] = None
    ) -> RecognitionResult:
        """
        Match card against template library.

        Args:
            card_image: Card image region
            deck_style: Specific deck style to match (None = use all/auto-detect)

        Returns:
            RecognitionResult with best match
        """
        if not self.available or card_image is None or card_image.size == 0:
            return RecognitionResult(None, 0.0, "unavailable", (0, 0, 0, 0))

        self.match_stats['total_matches'] += 1

        # Determine which styles to try
        styles_to_try = self._get_styles_to_try(deck_style)

        # Match against each style
        all_matches: List[TemplateMatch] = []
        for style in styles_to_try:
            matches = self._match_against_style(card_image, style)
            all_matches.extend(matches)

        if not all_matches:
            return RecognitionResult(None, 0.0, "no_templates", (0, 0, 0, 0))

        # Vote on best match
        best_match = self._vote_on_matches(all_matches)

        # Update detected style if auto-detecting
        if self.auto_detect_style and best_match:
            self.detected_style = best_match.deck_style
            self.match_stats['by_style'][best_match.deck_style] += 1

        if not best_match or best_match.confidence < self.min_confidence:
            return RecognitionResult(
                best_match.card if best_match else None,
                best_match.confidence if best_match else 0.0,
                f"low_confidence_multi_template",
                (0, 0, card_image.shape[1], card_image.shape[0])
            )

        return RecognitionResult(
            best_match.card,
            best_match.confidence,
            f"multi_template_{best_match.deck_style.value}",
            best_match.location
        )

    def add_template(
        self,
        card: Card,
        template_image: np.ndarray,
        deck_style: DeckStyle
    ) -> None:
        """
        Add a new template to the library.

        Args:
            card: Card identity
            template_image: Template image
            deck_style: Deck style for this template
        """
        if not self.available or template_image is None or template_image.size == 0:
            return

        # Preprocess template
        processed = self._preprocess_template(template_image)

        # Create template object
        template = CardTemplate(
            rank=card.rank,
            suit=card.suit,
            deck_style=deck_style,
            template_image=processed,
            width=processed.shape[1],
            height=processed.shape[0]
        )

        # Add to library
        card_str = str(card)
        if card_str not in self.template_library[deck_style]:
            self.template_library[deck_style][card_str] = []

        self.template_library[deck_style][card_str].append(template)
        logger.info(f"Added template for {card} in {deck_style.value} style")

    def get_detected_style(self) -> Optional[DeckStyle]:
        """Get currently detected deck style."""
        return self.detected_style

    def set_deck_style(self, style: DeckStyle) -> None:
        """Manually set deck style (disables auto-detection)."""
        self.detected_style = style
        self.auto_detect_style = False
        logger.info(f"Deck style manually set to {style.value}")

    def _get_styles_to_try(self, specified_style: Optional[DeckStyle]) -> List[DeckStyle]:
        """Determine which deck styles to try for matching."""
        if specified_style and specified_style != DeckStyle.AUTO:
            return [specified_style]

        if self.detected_style and not self.auto_detect_style:
            return [self.detected_style]

        # Try all enabled styles
        return self.enabled_styles

    def _match_against_style(
        self,
        card_image: np.ndarray,
        deck_style: DeckStyle
    ) -> List[TemplateMatch]:
        """Match card image against all templates of a specific style."""
        if deck_style not in self.template_library:
            return []

        preprocessed_image = self._preprocess_template(card_image)
        matches: List[TemplateMatch] = []

        # Match against all templates for this style
        for card_str, templates in self.template_library[deck_style].items():
            for template in templates:
                best_conf, best_scale, best_loc = self._multi_scale_match(
                    preprocessed_image, template.template_image
                )

                if best_conf >= self.min_confidence * 0.8:  # Lower threshold for voting
                    card = Card(rank=template.rank, suit=template.suit)
                    matches.append(TemplateMatch(
                        card=card,
                        confidence=best_conf,
                        deck_style=deck_style,
                        scale=best_scale,
                        location=best_loc
                    ))

        return matches

    def _multi_scale_match(
        self,
        image: np.ndarray,
        template: np.ndarray
    ) -> Tuple[float, float, Tuple[int, int, int, int]]:
        """
        Multi-scale template matching.

        Returns:
            (best_confidence, best_scale, best_location)
        """
        best_conf = 0.0
        best_scale = 1.0
        best_loc = (0, 0, 0, 0)

        for scale in self.scales:
            # Scale template
            new_w = max(int(template.shape[1] * scale), 1)
            new_h = max(int(template.shape[0] * scale), 1)

            if new_w > image.shape[1] or new_h > image.shape[0]:
                continue

            scaled_template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Match
            result = cv2.matchTemplate(image, scaled_template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_conf:
                best_conf = float(max_val)
                best_scale = scale
                x, y = max_loc
                best_loc = (x, y, new_w, new_h)

        return best_conf, best_scale, best_loc

    def _vote_on_matches(self, matches: List[TemplateMatch]) -> Optional[TemplateMatch]:
        """
        Vote on best match from multiple templates.

        Uses weighted voting based on confidence and deck style consistency.
        """
        if not matches:
            return None

        # Group matches by card
        card_groups: Dict[str, List[TemplateMatch]] = {}
        for match in matches:
            card_str = str(match.card)
            if card_str not in card_groups:
                card_groups[card_str] = []
            card_groups[card_str].append(match)

        # Score each card by summing confidences
        card_scores: Dict[str, float] = {}
        for card_str, group in card_groups.items():
            # Sum confidences with style consistency bonus
            total_confidence = sum(m.confidence for m in group)

            # Bonus if multiple matches from same style (consistency)
            styles = [m.deck_style for m in group]
            if len(set(styles)) < len(styles):  # Duplicate styles
                total_confidence *= 1.1

            card_scores[card_str] = total_confidence

        # Find best card
        best_card_str = max(card_scores.keys(), key=lambda k: card_scores[k])

        # Return highest confidence match for best card
        best_card_matches = card_groups[best_card_str]
        return max(best_card_matches, key=lambda m: m.confidence)

    def _preprocess_template(self, image: np.ndarray) -> np.ndarray:
        """Preprocess template/image for matching."""
        if image is None or image.size == 0:
            raise ValueError("Image is empty")

        # Convert to grayscale
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Normalize size (100px height)
        target_h = 100
        if gray.shape[0] != target_h:
            scale = target_h / gray.shape[0]
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        # Enhance
        gray = cv2.equalizeHist(gray)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        return gray

    def _load_template_library(self) -> None:
        """Load templates from disk if available."""
        # This would load pre-saved templates from template_dir
        # For now, it's a placeholder for future template persistence
        for style in self.enabled_styles:
            style_dir = self.template_dir / style.value
            if style_dir.exists():
                # Load templates from style_dir
                # Implementation would scan for .png/.jpg files and load them
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Get matching statistics."""
        stats = self.match_stats.copy()

        # Calculate style distribution
        total_style_matches = sum(self.match_stats['by_style'].values())
        if total_style_matches > 0:
            style_distribution = {
                style.value: count / total_style_matches
                for style, count in self.match_stats['by_style'].items()
                if count > 0
            }
            stats['style_distribution'] = style_distribution

        return stats


# Singleton
_multi_matcher: Optional[MultiTemplateMatcher] = None


def get_multi_template_matcher(
    enabled_styles: Optional[List[DeckStyle]] = None,
    **kwargs
) -> MultiTemplateMatcher:
    """
    Get singleton multi-template matcher.

    Args:
        enabled_styles: List of enabled deck styles
        **kwargs: Additional arguments

    Returns:
        MultiTemplateMatcher instance
    """
    global _multi_matcher

    if _multi_matcher is None:
        _multi_matcher = MultiTemplateMatcher(
            enabled_styles=enabled_styles,
            **kwargs
        )

    return _multi_matcher
