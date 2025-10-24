"""Tests for avatar detection."""
import pytest
import numpy as np
from pokertool.player_avatar_detector import PlayerAvatarDetector

def test_avatar_detection():
    detector = PlayerAvatarDetector()
    roi = np.zeros((100, 100, 3), dtype=np.uint8)
    avatar = detector.detect_avatar(roi)
    assert avatar.shape == (50, 50, 3)

def test_avatar_comparison():
    detector = PlayerAvatarDetector()
    a1 = np.zeros((50, 50, 3), dtype=np.uint8)
    a2 = np.zeros((50, 50, 3), dtype=np.uint8)
    similarity = detector.compare_avatars(a1, a2)
    assert similarity == 1.0
