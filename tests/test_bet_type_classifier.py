#!/usr/bin/env python3
"""Tests for Bet Type Classifier"""

import pytest
from src.pokertool.bet_type_classifier import (
    BetTypeClassifier,
    BetType,
    BetClassification
)


class TestBetTypeClassifier:
    """Test suite for BetTypeClassifier"""

    def test_initialization(self):
        """Test classifier initialization"""
        classifier = BetTypeClassifier()
        assert len(classifier.classification_history) == 0
        assert classifier.frame_count == 0
        assert classifier.value_bet_min_strength == 0.7
        assert classifier.bluff_max_strength == 0.3

    def test_continuation_bet_detection(self):
        """Test C-bet classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=10.0,
            pot_size=15.0,
            street="flop",
            was_preflop_aggressor=True,
            facing_bet=False
        )

        assert classification.bet_type == BetType.CONTINUATION_BET
        assert classification.bet_amount == 10.0
        assert classification.bet_to_pot_ratio == pytest.approx(0.667, 0.01)

    def test_value_bet_detection(self):
        """Test value bet classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=30.0,
            pot_size=40.0,
            street="river",
            hand_strength=0.9
        )

        assert classification.bet_type == BetType.VALUE_BET
        assert classification.bet_amount == 30.0

    def test_bluff_detection(self):
        """Test bluff classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=20.0,
            pot_size=25.0,
            street="turn",
            hand_strength=0.2
        )

        assert classification.bet_type == BetType.BLUFF
        assert classification.bet_amount == 20.0

    def test_semi_bluff_detection(self):
        """Test semi-bluff classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=15.0,
            pot_size=20.0,
            street="flop",
            hand_strength=0.5,
            has_draw=True
        )

        assert classification.bet_type == BetType.SEMI_BLUFF

    def test_blocking_bet_detection(self):
        """Test blocking bet classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=5.0,
            pot_size=20.0,  # 0.25 pot ratio < 0.33 threshold
            street="river"
        )

        assert classification.bet_type == BetType.BLOCKING_BET
        assert classification.bet_to_pot_ratio < 0.33

    def test_check_raise_detection(self):
        """Test check-raise classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=25.0,
            pot_size=30.0,
            street="flop",
            was_checked_to=True,
            facing_bet=True
        )

        assert classification.bet_type == BetType.CHECK_RAISE

    def test_squeeze_detection(self):
        """Test squeeze classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=40.0,
            pot_size=50.0,
            street="preflop",
            facing_bet=True,
            num_opponents=2
        )

        assert classification.bet_type == BetType.SQUEEZE

    def test_donk_bet_detection(self):
        """Test donk bet classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=12.0,
            pot_size=18.0,
            street="flop",
            position="BB",
            was_preflop_aggressor=False
        )

        assert classification.bet_type == BetType.DONK_BET

    def test_probe_bet_detection(self):
        """Test probe bet classification"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=15.0,
            pot_size=20.0,
            street="turn",
            was_checked_to=True,
            facing_bet=False
        )

        assert classification.bet_type == BetType.PROBE_BET

    def test_unknown_classification(self):
        """Test unknown classification for ambiguous situations"""
        classifier = BetTypeClassifier()
        classification = classifier.classify_bet(
            bet_amount=10.0,
            pot_size=15.0,
            street="river"
            # No hand strength or context provided
        )

        assert classification.bet_type == BetType.UNKNOWN

    def test_get_classifications_by_type(self):
        """Test filtering by bet type"""
        classifier = BetTypeClassifier()

        classifier.classify_bet(10.0, 15.0, street="flop", was_preflop_aggressor=True)  # C-BET
        classifier.classify_bet(30.0, 40.0, hand_strength=0.9)  # VALUE
        classifier.classify_bet(20.0, 25.0, hand_strength=0.2)  # BLUFF

        c_bets = classifier.get_classifications_by_type(BetType.CONTINUATION_BET)
        value_bets = classifier.get_classifications_by_type(BetType.VALUE_BET)
        bluffs = classifier.get_classifications_by_type(BetType.BLUFF)

        assert len(c_bets) == 1
        assert len(value_bets) == 1
        assert len(bluffs) == 1

    def test_get_recent_classifications(self):
        """Test retrieval of recent classifications"""
        classifier = BetTypeClassifier()

        for i in range(5):
            classifier.classify_bet(10.0 + i, 15.0 + i, hand_strength=0.5)

        recent = classifier.get_recent_classifications(count=3)
        assert len(recent) == 3
        assert recent[-1].bet_amount == 14.0  # Most recent

    def test_statistics_generation(self):
        """Test statistics calculation"""
        classifier = BetTypeClassifier()

        classifier.classify_bet(10.0, 15.0, street="flop", was_preflop_aggressor=True, confidence=0.90)
        classifier.classify_bet(30.0, 40.0, hand_strength=0.9, confidence=0.95)
        classifier.classify_bet(20.0, 25.0, hand_strength=0.2, confidence=0.85)

        stats = classifier.get_statistics()

        assert stats["total_classifications"] == 3
        assert "classifications_by_type" in stats
        assert "avg_bet_to_pot_ratio" in stats
        assert "avg_confidence" in stats
        assert stats["avg_confidence"] == 0.9  # (0.90 + 0.95 + 0.85) / 3

    def test_empty_classifier_statistics(self):
        """Test statistics on empty classifier"""
        classifier = BetTypeClassifier()
        stats = classifier.get_statistics()

        assert stats["total_classifications"] == 0
        assert stats["avg_bet_to_pot_ratio"] == 0.0
        assert stats["avg_confidence"] == 0.0

    def test_bet_to_pot_ratio_calculation(self):
        """Test bet-to-pot ratio calculation"""
        classifier = BetTypeClassifier()

        # 50% pot bet
        c1 = classifier.classify_bet(10.0, 20.0)
        assert c1.bet_to_pot_ratio == 0.5

        # Pot-sized bet
        c2 = classifier.classify_bet(30.0, 30.0)
        assert c2.bet_to_pot_ratio == 1.0

        # Overbet (2x pot)
        c3 = classifier.classify_bet(40.0, 20.0)
        assert c3.bet_to_pot_ratio == 2.0

    def test_frame_number_increment(self):
        """Test frame number increments"""
        classifier = BetTypeClassifier()

        c1 = classifier.classify_bet(10.0, 15.0)
        c2 = classifier.classify_bet(20.0, 25.0)
        c3 = classifier.classify_bet(30.0, 35.0)

        assert c1.frame_number == 1
        assert c2.frame_number == 2
        assert c3.frame_number == 3

    def test_reset_functionality(self):
        """Test classifier reset"""
        classifier = BetTypeClassifier()

        classifier.classify_bet(10.0, 15.0)
        classifier.classify_bet(20.0, 25.0)

        assert len(classifier.classification_history) == 2
        assert classifier.frame_count == 2

        classifier.reset()

        assert len(classifier.classification_history) == 0
        assert classifier.frame_count == 0

    def test_realistic_hand_progression(self):
        """Test realistic hand bet sequence"""
        classifier = BetTypeClassifier()

        # Preflop raise, then c-bet flop
        c1 = classifier.classify_bet(
            bet_amount=6.0,
            pot_size=3.0,
            street="flop",
            position="BTN",
            was_preflop_aggressor=True
        )
        assert c1.bet_type == BetType.CONTINUATION_BET

        # Turn value bet with strong hand
        c2 = classifier.classify_bet(
            bet_amount=15.0,
            pot_size=20.0,
            street="turn",
            hand_strength=0.85
        )
        assert c2.bet_type == BetType.VALUE_BET

        # River bluff
        c3 = classifier.classify_bet(
            bet_amount=25.0,
            pot_size=35.0,
            street="river",
            hand_strength=0.15
        )
        assert c3.bet_type == BetType.BLUFF

        stats = classifier.get_statistics()
        assert stats["total_classifications"] == 3

    def test_position_tracking(self):
        """Test that position is tracked"""
        classifier = BetTypeClassifier()

        c1 = classifier.classify_bet(10.0, 15.0, position="BTN")
        c2 = classifier.classify_bet(20.0, 25.0, position="BB")

        assert c1.position == "BTN"
        assert c2.position == "BB"

    def test_street_tracking(self):
        """Test that street is tracked"""
        classifier = BetTypeClassifier()

        c1 = classifier.classify_bet(10.0, 15.0, street="flop")
        c2 = classifier.classify_bet(20.0, 25.0, street="turn")
        c3 = classifier.classify_bet(30.0, 35.0, street="river")

        assert c1.street == "flop"
        assert c2.street == "turn"
        assert c3.street == "river"

    def test_confidence_tracking(self):
        """Test confidence score tracking"""
        classifier = BetTypeClassifier()

        c1 = classifier.classify_bet(10.0, 15.0, confidence=0.95)
        c2 = classifier.classify_bet(20.0, 25.0, confidence=0.85)

        assert c1.confidence == 0.95
        assert c2.confidence == 0.85


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
