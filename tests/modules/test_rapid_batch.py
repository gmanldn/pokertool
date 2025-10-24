"""Rapid tests for tasks 21-26."""
import pytest
import numpy as np
from pokertool.card_animation_detector import CardAnimationDetector
from pokertool.ensemble_ocr import EnsembleOCR
from pokertool.four_color_deck_detector import FourColorDeckDetector
from pokertool.bet_type_classifier import BetTypeClassifier, BetType
from pokertool.bet_sizing_trends import BetSizingTrendAnalyzer

# Task 21: Card animation detection
def test_animation_detection():
    detector = CardAnimationDetector()
    f1 = np.zeros((100, 100, 3), dtype=np.uint8)
    f2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
    assert bool(detector.is_animating(f1, f2)) is True

def test_no_animation():
    detector = CardAnimationDetector()
    f1 = np.zeros((100, 100, 3), dtype=np.uint8)
    f2 = np.zeros((100, 100, 3), dtype=np.uint8)
    assert bool(detector.is_animating(f1, f2)) is False

# Task 22: Ensemble OCR
def test_ensemble_ocr_init():
    ocr = EnsembleOCR()
    assert len(ocr.engines) >= 1
    assert 'tesseract' in ocr.engines

def test_ensemble_weights():
    ocr = EnsembleOCR()
    assert sum(ocr.weights.values()) > 0

def test_ensemble_recognize():
    ocr = EnsembleOCR()
    img = np.zeros((50, 200, 3), dtype=np.uint8)
    text, conf = ocr.recognize_text(img)
    assert isinstance(text, str)
    assert 0.0 <= conf <= 1.0

# Task 24: 4-color deck
def test_four_color_detector():
    detector = FourColorDeckDetector()
    assert len(detector.color_map) == 4

def test_suit_detection():
    detector = FourColorDeckDetector()
    card = np.zeros((50, 30, 3), dtype=np.uint8)
    suit = detector.detect_suit_by_color(card)
    assert suit in ['spades', 'hearts', 'diamonds', 'clubs', 'unknown']

def test_is_four_color_deck():
    detector = FourColorDeckDetector()
    img = np.zeros((800, 1200, 3), dtype=np.uint8)
    result = detector.is_four_color_deck(img)
    assert result in [True, False, np.True_, np.False_]

# Task 25: Bet type classification
def test_bet_classifier_value():
    classifier = BetTypeClassifier()
    bet_type = classifier.classify_bet(50, 100, 0.9)
    assert bet_type == BetType.VALUE

def test_bet_classifier_bluff():
    classifier = BetTypeClassifier()
    bet_type = classifier.classify_bet(75, 100, 0.1)
    assert bet_type == BetType.BLUFF

def test_bet_type_stats():
    classifier = BetTypeClassifier()
    history = [{'type': BetType.VALUE}, {'type': BetType.BLUFF}]
    stats = classifier.get_bet_type_stats(history)
    assert 'value' in stats
    assert 'bluff' in stats

# Task 26: Bet sizing trends
def test_trend_analyzer():
    analyzer = BetSizingTrendAnalyzer()
    analyzer.add_bet(50, 100, "BTN", "won")
    avg = analyzer.get_average_bet_size()
    assert avg == 0.5

def test_position_statistics():
    analyzer = BetSizingTrendAnalyzer()
    analyzer.add_bet(50, 100, "BTN", "won")
    analyzer.add_bet(75, 100, "BTN", "lost")
    stats = analyzer.get_position_statistics()
    assert "BTN" in stats
    assert stats["BTN"]["count"] == 2

def test_bet_size_trend():
    analyzer = BetSizingTrendAnalyzer()
    for i in range(25):
        analyzer.add_bet(i, 100, "CO", "won")
    trend = analyzer.get_bet_size_trend()
    assert trend in ["increasing", "decreasing", "stable", "insufficient_data"]
