"""Player Action Detection Module

Detects player actions (fold, check, call, bet, raise, all-in) from poker table screenshots.
Uses visual indicators, button states, and text recognition.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import cv2
import numpy as np
from collections import deque
import time

logger = logging.getLogger(__name__)


class PlayerAction(Enum):
    """Enumeration of possible player actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"
    UNKNOWN = "unknown"


@dataclass
class ActionDetection:
    """Information about a detected player action."""
    player_seat: int
    action: PlayerAction
    amount: float  # 0 for fold/check
    confidence: float
    timestamp: float
    detection_method: str  # "visual", "text", "button_state"


class PlayerActionDetector:
    """Detect player actions from poker table visual indicators."""

    def __init__(self, max_history: int = 50):
        self.action_history: deque = deque(maxlen=max_history)
        self.last_actions: Dict[int, ActionDetection] = {}  # seat -> last action

        # Visual indicators for action detection
        self.fold_indicators = {
            'dimmed_player': True,  # Player area becomes dimmed/grayed out
            'crossed_cards': True,  # Cards have X overlay
            'no_chips': True,       # No chips in front of player
        }

        # Action button colors (typical poker client colors)
        self.action_colors = {
            'fold': (200, 60, 60),      # Red
            'check': (100, 200, 100),   # Green
            'call': (100, 200, 100),    # Green
            'bet': (255, 165, 0),       # Orange
            'raise': (255, 140, 0),     # Dark orange
            'all_in': (255, 0, 0),      # Bright red
        }

    def detect_player_action(
        self,
        image: np.ndarray,
        seat_number: int,
        player_roi: Tuple[int, int, int, int],
        previous_stack: float = 0.0,
        current_stack: float = 0.0,
        ocr_func=None
    ) -> Optional[ActionDetection]:
        """
        Detect action for a specific player.

        Args:
            image: Full table screenshot
            seat_number: Player's seat number
            player_roi: Region of interest for player (x0, y0, x1, y1)
            previous_stack: Player's stack before action
            current_stack: Player's stack after action
            ocr_func: Optional OCR function for text detection

        Returns:
            ActionDetection if action detected, None otherwise
        """
        x0, y0, x1, y1 = player_roi
        player_area = image[y0:y1, x0:x1]

        if player_area.size == 0:
            return None

        # Method 1: Detect action from stack change
        if abs(previous_stack - current_stack) > 0.01:
            stack_delta = previous_stack - current_stack
            action = self._infer_action_from_stack_change(
                stack_delta,
                previous_stack,
                current_stack
            )
            if action != PlayerAction.UNKNOWN:
                detection = ActionDetection(
                    player_seat=seat_number,
                    action=action,
                    amount=stack_delta if action not in [PlayerAction.FOLD, PlayerAction.CHECK] else 0.0,
                    confidence=0.85,
                    timestamp=time.time(),
                    detection_method="stack_change"
                )
                self._record_action(detection)
                return detection

        # Method 2: Detect fold from visual indicators
        if self._detect_fold_visual(player_area):
            detection = ActionDetection(
                player_seat=seat_number,
                action=PlayerAction.FOLD,
                amount=0.0,
                confidence=0.90,
                timestamp=time.time(),
                detection_method="visual"
            )
            self._record_action(detection)
            return detection

        # Method 3: Detect from action text/buttons (if OCR available)
        if ocr_func:
            action_text = self._detect_action_text(player_area, ocr_func)
            if action_text:
                action = self._parse_action_text(action_text)
                if action != PlayerAction.UNKNOWN:
                    detection = ActionDetection(
                        player_seat=seat_number,
                        action=action,
                        amount=0.0,  # Would need additional OCR for bet amounts
                        confidence=0.75,
                        timestamp=time.time(),
                        detection_method="text"
                    )
                    self._record_action(detection)
                    return detection

        return None

    def _infer_action_from_stack_change(
        self,
        stack_delta: float,
        previous_stack: float,
        current_stack: float
    ) -> PlayerAction:
        """Infer action type from stack size change."""
        if stack_delta > 0:
            # Stack decreased - player put chips in
            if current_stack == 0:
                return PlayerAction.ALL_IN
            elif stack_delta < previous_stack * 0.1:
                # Small bet relative to stack
                return PlayerAction.CALL  # or could be small bet
            else:
                # Larger bet
                return PlayerAction.RAISE  # or could be bet
        elif stack_delta == 0:
            # No stack change - check or fold
            return PlayerAction.CHECK  # or fold (need visual confirmation)

        return PlayerAction.UNKNOWN

    def _detect_fold_visual(self, player_area: np.ndarray) -> bool:
        """
        Detect fold from visual indicators in player area.

        Common fold indicators:
        - Player area becomes dimmed/grayed out
        - Cards have X or crossed-out appearance
        - Player chips disappear or become inactive
        """
        if player_area.size == 0:
            return False

        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(player_area, cv2.COLOR_BGR2GRAY)

            # Check 1: Dimmed/grayed area (low intensity)
            mean_brightness = np.mean(gray)
            if mean_brightness < 50:  # Very dark = likely dimmed
                logger.debug(f"Fold indicator: dimmed player area (brightness: {mean_brightness:.1f})")
                return True

            # Check 2: Look for red X or cross pattern
            # Red channel significantly higher than green/blue
            b, g, r = cv2.split(player_area)
            red_dominant = np.mean(r) > np.mean(g) * 1.5 and np.mean(r) > np.mean(b) * 1.5

            if red_dominant:
                # Look for X-shaped pattern using edge detection
                edges = cv2.Canny(gray, 50, 150)
                if np.sum(edges > 0) > edges.size * 0.05:  # At least 5% edges
                    logger.debug("Fold indicator: red X pattern detected")
                    return True

            # Check 3: Uniformity (folded players often show solid color)
            std_dev = np.std(gray)
            if std_dev < 10:  # Very uniform = likely inactive/folded
                logger.debug(f"Fold indicator: uniform player area (std: {std_dev:.1f})")
                return True

        except Exception as e:
            logger.debug(f"Fold visual detection failed: {e}")

        return False

    def _detect_action_text(self, player_area: np.ndarray, ocr_func) -> Optional[str]:
        """
        Detect action text in player area using OCR.

        Returns action text like "FOLD", "CHECK", "CALL", "BET", "RAISE", "ALL IN"
        """
        if player_area.size == 0:
            return None

        try:
            # Preprocess for OCR
            gray = cv2.cvtColor(player_area, cv2.COLOR_BGR2GRAY)

            # Try to find text regions (action indicators often on bright backgrounds)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

            # Run OCR
            text = ocr_func(thresh)
            if text:
                text_clean = text.strip().upper()
                logger.debug(f"Action text detected: '{text_clean}'")
                return text_clean

        except Exception as e:
            logger.debug(f"Action text detection failed: {e}")

        return None

    def _parse_action_text(self, text: str) -> PlayerAction:
        """Parse action text to PlayerAction enum."""
        text_lower = text.lower()

        if 'fold' in text_lower:
            return PlayerAction.FOLD
        elif 'check' in text_lower:
            return PlayerAction.CHECK
        elif 'call' in text_lower:
            return PlayerAction.CALL
        elif 'bet' in text_lower:
            return PlayerAction.BET
        elif 'raise' in text_lower:
            return PlayerAction.RAISE
        elif 'all' in text_lower and 'in' in text_lower:
            return PlayerAction.ALL_IN

        return PlayerAction.UNKNOWN

    def _record_action(self, detection: ActionDetection) -> None:
        """Record detected action to history."""
        self.action_history.append(detection)
        self.last_actions[detection.player_seat] = detection
        logger.info(
            f"🎯 Action detected: Seat {detection.player_seat} - {detection.action.value.upper()} "
            f"${detection.amount:.2f} (confidence: {detection.confidence:.2%})"
        )

    def get_player_last_action(self, seat_number: int) -> Optional[ActionDetection]:
        """Get the last action for a specific player."""
        return self.last_actions.get(seat_number)

    def get_recent_actions(self, count: int = 10) -> List[ActionDetection]:
        """Get N most recent actions."""
        return list(self.action_history)[-count:]

    def get_action_summary(self) -> Dict[str, int]:
        """Get summary of action counts."""
        summary = {action.value: 0 for action in PlayerAction}
        for detection in self.action_history:
            summary[detection.action.value] += 1
        return summary

    def clear_history(self) -> None:
        """Clear action history."""
        self.action_history.clear()
        self.last_actions.clear()
