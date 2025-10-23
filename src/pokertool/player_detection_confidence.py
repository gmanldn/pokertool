"""Player Detection with Confidence Scores"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PlayerDetection:
    seat_number: int
    name: str
    stack: float
    confidence: float
    detection_method: str
    metadata: Dict[str, Any]

def detect_player_with_confidence(
    image, seat_number: int, method: str = "ocr"
) -> Optional[PlayerDetection]:
    """Detect player with confidence score."""
    # Placeholder for actual detection logic
    confidence = 0.85
    logger.debug(f"Player detected at seat {seat_number} with confidence {confidence:.2f}")
    return PlayerDetection(
        seat_number=seat_number,
        name=f"Player{seat_number}",
        stack=1000.0,
        confidence=confidence,
        detection_method=method,
        metadata={"timestamp": "2025-10-22"}
    )
