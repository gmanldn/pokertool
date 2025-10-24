"""Tests for board card detection."""
import pytest
import numpy as np
from pokertool.board_card_detector import BoardCardDetector

class TestBoardCardDetector:
    def test_init(self):
        detector = BoardCardDetector()
        assert detector.min_confidence == 0.99
    
    def test_detect_empty_board(self):
        detector = BoardCardDetector()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        cards, conf = detector.detect_board_cards(image, (400, 300, 800, 400))
        assert isinstance(cards, list)
        assert 0.0 <= conf <= 1.0
    
    def test_confidence_calculation(self):
        detector = BoardCardDetector()
        conf = detector._calculate_confidence(["Ac", "Kd", "Qh"])
        assert conf >= 0.85
    
    def test_max_five_cards(self):
        detector = BoardCardDetector()
        image = np.ones((800, 1200, 3), dtype=np.uint8) * 255
        cards, conf = detector.detect_board_cards(image, (400, 300, 800, 400))
        assert len(cards) <= 5
    
    def test_extract_cards(self):
        detector = BoardCardDetector()
        board_area = np.ones((100, 500, 3), dtype=np.uint8) * 255
        cards = detector._extract_cards(board_area)
        assert isinstance(cards, list)
    
    def test_empty_roi(self):
        detector = BoardCardDetector()
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        cards, conf = detector.detect_board_cards(image, (0, 0, 0, 0))
        assert cards == []
        assert conf == 0.0
    
    def test_card_templates_loaded(self):
        detector = BoardCardDetector()
        assert detector.card_templates is not None
    
    def test_high_confidence_threshold(self):
        detector = BoardCardDetector()
        assert detector.min_confidence >= 0.99
    
    def test_detect_multiple_cards(self):
        detector = BoardCardDetector()
        image = np.random.randint(0, 255, (800, 1200, 3), dtype=np.uint8)
        cards, conf = detector.detect_board_cards(image, (200, 200, 600, 300))
        assert isinstance(cards, list)
    
    def test_confidence_range(self):
        detector = BoardCardDetector()
        conf = detector._calculate_confidence(["Ac"])
        assert 0.0 <= conf <= 1.0
