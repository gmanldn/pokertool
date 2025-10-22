"""
Detection Configuration Module
==============================

Centralized configuration for detection confidence thresholds and quality settings.
"""

import os
from typing import Dict
from dataclasses import dataclass


@dataclass
class ConfidenceThresholds:
    """Confidence threshold settings for detection quality control."""

    # Card detection thresholds
    card_min_confidence: float = 0.7
    card_high_confidence: float = 0.9

    # Pot detection thresholds
    pot_min_confidence: float = 0.6
    pot_high_confidence: float = 0.85

    # Player detection thresholds
    player_min_confidence: float = 0.65
    player_high_confidence: float = 0.88

    # Button/position detection thresholds
    button_min_confidence: float = 0.75
    button_high_confidence: float = 0.92

    # Action detection thresholds
    action_min_confidence: float = 0.70
    action_high_confidence: float = 0.90

    # Board detection thresholds
    board_min_confidence: float = 0.72
    board_high_confidence: float = 0.91

    # General threshold for event emission
    min_confidence_to_emit: float = 0.6

    @classmethod
    def from_env(cls) -> 'ConfidenceThresholds':
        """
        Create thresholds from environment variables.

        Environment variables:
            DETECTION_CARD_MIN_CONFIDENCE: Minimum confidence for card detection (default: 0.7)
            DETECTION_CARD_HIGH_CONFIDENCE: High confidence for card detection (default: 0.9)
            DETECTION_POT_MIN_CONFIDENCE: Minimum confidence for pot detection (default: 0.6)
            DETECTION_PLAYER_MIN_CONFIDENCE: Minimum confidence for player detection (default: 0.65)
            DETECTION_MIN_EMIT_CONFIDENCE: Minimum confidence to emit any event (default: 0.6)
        """
        return cls(
            card_min_confidence=float(os.getenv('DETECTION_CARD_MIN_CONFIDENCE', '0.7')),
            card_high_confidence=float(os.getenv('DETECTION_CARD_HIGH_CONFIDENCE', '0.9')),
            pot_min_confidence=float(os.getenv('DETECTION_POT_MIN_CONFIDENCE', '0.6')),
            pot_high_confidence=float(os.getenv('DETECTION_POT_HIGH_CONFIDENCE', '0.85')),
            player_min_confidence=float(os.getenv('DETECTION_PLAYER_MIN_CONFIDENCE', '0.65')),
            player_high_confidence=float(os.getenv('DETECTION_PLAYER_HIGH_CONFIDENCE', '0.88')),
            button_min_confidence=float(os.getenv('DETECTION_BUTTON_MIN_CONFIDENCE', '0.75')),
            button_high_confidence=float(os.getenv('DETECTION_BUTTON_HIGH_CONFIDENCE', '0.92')),
            action_min_confidence=float(os.getenv('DETECTION_ACTION_MIN_CONFIDENCE', '0.70')),
            action_high_confidence=float(os.getenv('DETECTION_ACTION_HIGH_CONFIDENCE', '0.90')),
            board_min_confidence=float(os.getenv('DETECTION_BOARD_MIN_CONFIDENCE', '0.72')),
            board_high_confidence=float(os.getenv('DETECTION_BOARD_HIGH_CONFIDENCE', '0.91')),
            min_confidence_to_emit=float(os.getenv('DETECTION_MIN_EMIT_CONFIDENCE', '0.6')),
        )

    def should_emit_event(self, confidence: float, detection_type: str = 'general') -> bool:
        """
        Determine if an event should be emitted based on confidence.

        Args:
            confidence: Confidence score (0-1)
            detection_type: Type of detection (card, pot, player, etc.)

        Returns:
            True if confidence meets minimum threshold for this detection type
        """
        type_thresholds = {
            'card': self.card_min_confidence,
            'pot': self.pot_min_confidence,
            'player': self.player_min_confidence,
            'button': self.button_min_confidence,
            'action': self.action_min_confidence,
            'board': self.board_min_confidence,
        }

        min_threshold = type_thresholds.get(detection_type.lower(), self.min_confidence_to_emit)
        return confidence >= min_threshold

    def is_high_confidence(self, confidence: float, detection_type: str = 'general') -> bool:
        """
        Determine if a detection has high confidence.

        Args:
            confidence: Confidence score (0-1)
            detection_type: Type of detection

        Returns:
            True if confidence exceeds high threshold for this detection type
        """
        type_high_thresholds = {
            'card': self.card_high_confidence,
            'pot': self.pot_high_confidence,
            'player': self.player_high_confidence,
            'button': self.button_high_confidence,
            'action': self.action_high_confidence,
            'board': self.board_high_confidence,
        }

        high_threshold = type_high_thresholds.get(detection_type.lower(), 0.85)
        return confidence >= high_threshold

    def get_confidence_level(self, confidence: float, detection_type: str = 'general') -> str:
        """
        Get confidence level label (LOW/MEDIUM/HIGH).

        Args:
            confidence: Confidence score (0-1)
            detection_type: Type of detection

        Returns:
            'HIGH', 'MEDIUM', or 'LOW'
        """
        if self.is_high_confidence(confidence, detection_type):
            return 'HIGH'
        elif self.should_emit_event(confidence, detection_type):
            return 'MEDIUM'
        else:
            return 'LOW'


# Global singleton
_detection_config: ConfidenceThresholds | None = None


def get_detection_config() -> ConfidenceThresholds:
    """Get or create the global detection configuration."""
    global _detection_config
    if _detection_config is None:
        _detection_config = ConfidenceThresholds.from_env()
    return _detection_config


def reload_detection_config() -> ConfidenceThresholds:
    """Reload detection configuration from environment variables."""
    global _detection_config
    _detection_config = ConfidenceThresholds.from_env()
    return _detection_config
