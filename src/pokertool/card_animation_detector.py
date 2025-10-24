"""Card animation detection and waiting."""
import cv2
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CardAnimationDetector:
    """Detect card animations and wait for completion."""
    
    def __init__(self):
        self.animation_threshold = 0.1
        
    def is_animating(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        """Check if cards are animating between frames."""
        if frame1.shape != frame2.shape:
            return True
        diff = cv2.absdiff(frame1, frame2)
        return np.mean(diff) > self.animation_threshold
    
    def wait_for_animation_complete(self, get_frame_func, max_wait: float = 2.0) -> bool:
        """Wait for card animation to complete."""
        import time
        start = time.time()
        prev_frame = get_frame_func()
        
        while time.time() - start < max_wait:
            time.sleep(0.1)
            curr_frame = get_frame_func()
            if not self.is_animating(prev_frame, curr_frame):
                return True
            prev_frame = curr_frame
        
        return False
