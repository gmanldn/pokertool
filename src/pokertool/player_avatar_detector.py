"""Player avatar detection."""
import cv2
import numpy as np

class PlayerAvatarDetector:
    def detect_avatar(self, player_roi: np.ndarray) -> np.ndarray:
        """Extract player avatar from ROI."""
        if player_roi.size == 0:
            return np.array([])
        # Assume avatar is in top-left corner
        h, w = player_roi.shape[:2]
        avatar = player_roi[0:min(50, h), 0:min(50, w)]
        return avatar
    
    def compare_avatars(self, avatar1: np.ndarray, avatar2: np.ndarray) -> float:
        """Compare two avatars for similarity."""
        if avatar1.size == 0 or avatar2.size == 0:
            return 0.0
        if avatar1.shape != avatar2.shape:
            avatar2 = cv2.resize(avatar2, (avatar1.shape[1], avatar1.shape[0]))
        diff = cv2.absdiff(avatar1, avatar2)
        similarity = 1.0 - (np.mean(diff) / 255.0)
        return similarity
