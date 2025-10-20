"""
Card recognition utilities backed by OpenCV template matching.

The implementation intentionally keeps the public API small and defensive so
that downstream modules can depend on predictable behaviour even when the
runtime environment does not provide OpenCV or previously learned templates.
"""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2

    CARD_RECOGNITION_AVAILABLE = True
except Exception:  # pragma: no cover - OpenCV is an optional dependency
    CARD_RECOGNITION_AVAILABLE = False
    cv2 = None  # type: ignore[assignment]


RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS = ["c", "d", "h", "s"]
SUIT_NAMES = {"c": "clubs", "d": "diamonds", "h": "hearts", "s": "spades"}


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    def __post_init__(self) -> None:
        if self.rank not in RANKS:
            raise ValueError(f"Unsupported rank '{self.rank}'")
        if self.suit not in SUITS:
            raise ValueError(f"Unsupported suit '{self.suit}'")

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card({self.rank}{self.suit})"

    @property
    def suit_name(self) -> str:
        return SUIT_NAMES.get(self.suit, self.suit)


@dataclass
class CardTemplate:
    """Serialized representation of a learned card or card component."""

    rank: str
    suit: str
    template: np.ndarray
    width: int
    height: int
    method: str  # 'rank', 'suit', or 'full'


@dataclass
class RecognitionResult:
    """Information returned by card recognition."""

    card: Optional[Card]
    confidence: float
    method: str
    location: Tuple[int, int, int, int]


class CardRecognitionEngine:
    """
    Card recognition orchestrator built on top of OpenCV template matching.

    The engine supports learning card templates on the fly and persists them
    to disk so that subsequent runs can reuse the information.
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        self.available = CARD_RECOGNITION_AVAILABLE
        self.templates: Dict[str, List[CardTemplate]] = {
            "ranks": [],
            "suits": [],
            "full_cards": [],
        }

        self.template_dir = template_dir or Path(__file__).parent / "card_templates"
        self.template_dir.mkdir(parents=True, exist_ok=True)

        self.min_confidence = 0.70
        self.scales = [0.8, 0.9, 1.0, 1.1, 1.2]

        if not self.available:
            logger.warning("Card recognition disabled: OpenCV is unavailable.")
            return

        self._load_templates()

    # ------------------------------------------------------------------ public
    def recognize_card(self, card_image: np.ndarray) -> RecognitionResult:
        """Recognize a single card from an image region."""
        if not self.available:
            return RecognitionResult(None, 0.0, "unavailable", (0, 0, 0, 0))

        if card_image is None or not hasattr(card_image, "shape") or card_image.size == 0:
            return RecognitionResult(None, 0.0, "invalid_image", (0, 0, 0, 0))

        try:
            processed = self._preprocess_card_image(card_image)
        except Exception as exc:
            logger.debug("Card preprocessing failed: %s", exc)
            return RecognitionResult(None, 0.0, "preprocess_error", (0, 0, 0, 0))

        if self.templates["full_cards"]:
            result = self._match_full_card(processed, card_image.shape)
            if result.card is not None:
                return result

        rank, rank_conf = self._match_rank(processed)
        suit, suit_conf = self._match_suit(processed)

        if rank and suit and (rank_conf + suit_conf) / 2 >= self.min_confidence:
            card = Card(rank=rank, suit=suit)
            confidence = (rank_conf + suit_conf) / 2
            height, width = card_image.shape[:2]
            return RecognitionResult(card, confidence, "rank_suit", (0, 0, width, height))

        return RecognitionResult(None, 0.0, "no_match", (0, 0, 0, 0))

    def recognize_multiple_cards(
        self,
        table_image: np.ndarray,
        card_regions: List[Tuple[int, int, int, int]],
    ) -> List[RecognitionResult]:
        """Recognize a batch of card regions within a table image."""
        results: List[RecognitionResult] = []

        if not self.available or table_image is None:
            for region in card_regions:
                results.append(RecognitionResult(None, 0.0, "unavailable", region))
            return results

        for x, y, w, h in card_regions:
            card_img = table_image[y : y + h, x : x + w]
            result = self.recognize_card(card_img)
            result.location = (x, y, w, h)
            results.append(result)

        return results

    def learn_card_from_image(self, card_image: np.ndarray, rank: str, suit: str) -> None:
        """Learn a new card template from a supplied image."""
        if not self.available:
            logger.debug("Skipping card learning because OpenCV is unavailable.")
            return

        try:
            processed = self._preprocess_card_image(card_image)
        except Exception as exc:
            logger.error("Failed to preprocess card for learning: %s", exc)
            return

        if processed.size == 0:
            logger.error("Cannot learn card template from an empty image.")
            return

        height, width = processed.shape[:2]
        rank_height = max(height // 3, 1)
        suit_height = max(height // 3, 1)
        rank_width = max(width // 3, 1)

        rank_region = processed[0:rank_height, 0:rank_width]
        suit_region = processed[rank_height : rank_height + suit_height, 0:rank_width]

        rank_template = CardTemplate(rank, "", rank_region, rank_region.shape[1], rank_region.shape[0], "rank")
        suit_template = CardTemplate("", suit, suit_region, suit_region.shape[1], suit_region.shape[0], "suit")
        full_template = CardTemplate(rank, suit, processed, width, height, "full")

        self.templates["ranks"].append(rank_template)
        self.templates["suits"].append(suit_template)
        self.templates["full_cards"].append(full_template)

        logger.info("Learned card template for %s%s", rank, suit)
        self._save_templates()

    def learn_full_deck(self, deck_image: np.ndarray, layout: str = "grid") -> None:
        """
        Placeholder for full deck learning.

        The current implementation does not attempt to automatically segment the
        deck image; callers should still extract individual card regions and call
        `learn_card_from_image`. The method exists to preserve the public API.
        """
        logger.info("learn_full_deck is not implemented (layout=%s).", layout)

    # ----------------------------------------------------------------- helpers
    def _preprocess_card_image(self, image: np.ndarray) -> np.ndarray:
        """Normalize card imagery for template matching."""
        if image is None or image.size == 0:
            raise ValueError("image must be a non-empty numpy array")

        working = image.copy()

        if working.ndim == 3:
            working = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)

        target_height = 100
        if working.shape[0] != target_height:
            scale = target_height / float(working.shape[0])
            working = cv2.resize(working, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        working = cv2.equalizeHist(working)
        working = cv2.fastNlMeansDenoising(working, h=10)

        return working

    def _match_full_card(self, card_image: np.ndarray, original_shape: Tuple[int, ...]) -> RecognitionResult:
        """Match a card against the learned full-card templates."""
        best_match: Optional[CardTemplate] = None
        best_confidence = 0.0

        for template in self.templates["full_cards"]:
            for scale in self.scales:
                scaled = cv2.resize(
                    template.template,
                    (max(int(template.width * scale), 1), max(int(template.height * scale), 1)),
                    interpolation=cv2.INTER_AREA,
                )

                if scaled.shape[0] > card_image.shape[0] or scaled.shape[1] > card_image.shape[1]:
                    continue

                result = cv2.matchTemplate(card_image, scaled, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > best_confidence:
                    best_confidence = max_val
                    best_match = template

        if best_match and best_confidence >= self.min_confidence:
            width = original_shape[1]
            height = original_shape[0]
            card = Card(best_match.rank, best_match.suit)
            return RecognitionResult(card, best_confidence, "full_card", (0, 0, width, height))

        return RecognitionResult(None, 0.0, "no_match", (0, 0, 0, 0))

    def _match_rank(self, card_image: np.ndarray) -> Tuple[str, float]:
        """Template matching for the rank portion of the card."""
        if not self.templates["ranks"]:
            return "", 0.0

        height, width = card_image.shape[:2]
        rank_region = card_image[0 : max(height // 3, 1), 0 : max(width // 3, 1)]

        best_rank = ""
        best_confidence = 0.0

        for template in self.templates["ranks"]:
            confidence = self._match_region(rank_region, template)
            if confidence > best_confidence:
                best_rank = template.rank
                best_confidence = confidence

        return best_rank, best_confidence

    def _match_suit(self, card_image: np.ndarray) -> Tuple[str, float]:
        """Template matching for the suit portion of the card."""
        if not self.templates["suits"]:
            return "", 0.0

        height, width = card_image.shape[:2]
        start_row = max(height // 3, 1)
        suit_region = card_image[start_row : start_row + max(height // 3, 1), 0 : max(width // 3, 1)]

        if suit_region.size == 0:
            return "", 0.0

        best_suit = ""
        best_confidence = 0.0

        for template in self.templates["suits"]:
            confidence = self._match_region(suit_region, template)
            if confidence > best_confidence:
                best_suit = template.suit
                best_confidence = confidence

        return best_suit, best_confidence

    def _match_region(self, region: np.ndarray, template: CardTemplate) -> float:
        """Apply multi-scale template matching for a specific region."""
        best_confidence = 0.0

        for scale in self.scales:
            scaled = cv2.resize(
                template.template,
                (max(int(template.width * scale), 1), max(int(template.height * scale), 1)),
                interpolation=cv2.INTER_AREA,
            )

            if scaled.shape[0] > region.shape[0] or scaled.shape[1] > region.shape[1]:
                continue

            result = cv2.matchTemplate(region, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            best_confidence = max(best_confidence, float(max_val))

        return best_confidence

    def _templates_path(self) -> Path:
        return self.template_dir / "card_templates.pkl"

    def _load_templates(self) -> None:
        """Load templates from disk if available."""
        path = self._templates_path()
        if not path.exists():
            return

        try:
            with path.open("rb") as fh:
                data = pickle.load(fh)
        except Exception as exc:
            logger.warning("Failed to load card templates: %s", exc)
            return

        for key in ("ranks", "suits", "full_cards"):
            items = data.get(key, [])
            filtered: List[CardTemplate] = []
            for item in items:
                if isinstance(item, CardTemplate) and isinstance(item.template, np.ndarray):
                    filtered.append(item)
            self.templates[key] = filtered

        logger.debug(
            "Loaded %d rank, %d suit, and %d full-card templates.",
            len(self.templates["ranks"]),
            len(self.templates["suits"]),
            len(self.templates["full_cards"]),
        )

    def _save_templates(self) -> None:
        """Persist learned templates to disk."""
        path = self._templates_path()

        try:
            with path.open("wb") as fh:
                pickle.dump(self.templates, fh)
        except Exception as exc:
            logger.warning("Failed to save card templates: %s", exc)
