#!/usr/bin/env python3
"""Image preprocessing for card detection including glare removal."""

import cv2
import numpy as np
from typing import Optional

class ImagePreprocessor:
    """Preprocess card images to remove reflections and glare."""

    def remove_glare(self, image: np.ndarray) -> np.ndarray:
        """
        Remove glare/reflections from card image.

        Args:
            image: Input image (BGR)

        Returns:
            Processed image with glare removed
        """
        if image is None or image.size == 0:
            return image

        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel to reduce glare
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # Merge and convert back
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return result

    def enhance_card(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance card image for better OCR.

        Args:
            image: Input card image

        Returns:
            Enhanced image
        """
        if image is None or image.size == 0:
            return image

        # Remove glare
        no_glare = self.remove_glare(image)

        # Sharpen
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(no_glare, -1, kernel)

        return sharpened


class AnimationHandler:
    """Handles card animation detection and waiting."""

    def __init__(self, stability_threshold: int = 3):
        """
        Initialize handler.

        Args:
            stability_threshold: Number of stable frames required
        """
        self.stability_threshold = stability_threshold
        self.stable_frames = 0
        self.last_hash: Optional[int] = None

    def is_stable(self, image: np.ndarray) -> bool:
        """
        Check if image is stable (animation complete).

        Args:
            image: Current frame

        Returns:
            True if animation complete
        """
        if image is None or image.size == 0:
            return False

        # Simple hash-based stability check
        current_hash = hash(image.tobytes())

        if current_hash == self.last_hash:
            self.stable_frames += 1
        else:
            self.stable_frames = 0
            self.last_hash = current_hash

        return self.stable_frames >= self.stability_threshold

    def reset(self):
        """Reset stability tracking."""
        self.stable_frames = 0
        self.last_hash = None


_preprocessor_instance: Optional[ImagePreprocessor] = None
_animation_handler_instance: Optional[AnimationHandler] = None

def get_image_preprocessor() -> ImagePreprocessor:
    """Get global image preprocessor."""
    global _preprocessor_instance
    if _preprocessor_instance is None:
        _preprocessor_instance = ImagePreprocessor()
    return _preprocessor_instance

def get_animation_handler() -> AnimationHandler:
    """Get global animation handler."""
    global _animation_handler_instance
    if _animation_handler_instance is None:
        _animation_handler_instance = AnimationHandler()
    return _animation_handler_instance
