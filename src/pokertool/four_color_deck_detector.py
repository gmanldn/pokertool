"""4-color deck detection support."""
import cv2
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class FourColorDeckDetector:
    """Detect and handle 4-color deck card recognition."""
    
    def __init__(self):
        self.color_map = {
            'spades': (0, 0, 0),      # Black
            'hearts': (255, 0, 0),    # Red
            'diamonds': (0, 0, 255),  # Blue
            'clubs': (0, 255, 0)      # Green
        }
    
    def detect_suit_by_color(self, card_roi: np.ndarray) -> str:
        """Detect card suit by color in 4-color deck."""
        if card_roi.size == 0:
            return "unknown"
        
        avg_color = np.mean(card_roi, axis=(0, 1))
        
        # Find closest color match
        min_dist = float('inf')
        best_suit = "unknown"
        
        for suit, color in self.color_map.items():
            dist = np.linalg.norm(avg_color - np.array(color))
            if dist < min_dist:
                min_dist = dist
                best_suit = suit
        
        return best_suit
    
    def is_four_color_deck(self, table_image: np.ndarray) -> bool:
        """Detect if table is using 4-color deck."""
        # Check if we see blue or green suits
        hsv = cv2.cvtColor(table_image, cv2.COLOR_BGR2HSV)
        
        # Green hue range for clubs
        green_mask = cv2.inRange(hsv, (40, 50, 50), (80, 255, 255))
        
        # Blue hue range for diamonds
        blue_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
        
        # If significant green or blue, likely 4-color deck
        return np.sum(green_mask) > 100 or np.sum(blue_mask) > 100
