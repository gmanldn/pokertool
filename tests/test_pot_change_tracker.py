#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for Pot Change Tracker
============================

Comprehensive test suite for pot size change detection and tracking.
"""

import pytest
from datetime import datetime
from src.pokertool.pot_change_tracker import (
    PotChangeTracker,
    ChangeType,
    PotChange
)


class TestPotChangeTracker:
    """Test suite for PotChangeTracker"""

    def test_initialization(self):
        """Test tracker initialization"""
        tracker = PotChangeTracker(rake_percentage=0.05, min_change_threshold=0.01)
        assert tracker.current_pot_size == 0.0
        assert tracker.previous_pot_size == 0.0
        assert len(tracker.change_history) == 0
        assert tracker.rake_percentage == 0.05
        assert tracker.min_change_threshold == 0.01

    def test_basic_bet_detection(self):
        """Test detection of initial bet"""
        tracker = PotChangeTracker()
        change = tracker.update_pot_size(10.0, confidence=0.95)

        assert change is not None
        assert change.change_type == ChangeType.BET
        assert change.change_amount == 10.0
        assert change.previous_size == 0.0
        assert change.new_size == 10.0
        assert change.confidence == 0.95

    def test_call_detection(self):
        """Test detection of call"""
        tracker = PotChangeTracker()
        tracker.update_pot_size(10.0)  # Initial bet
        change = tracker.update_pot_size(20.0)  # Call

        assert change.change_type == ChangeType.CALL
        assert change.change_amount == 10.0

    def test_raise_detection(self):
        """Test detection of raise"""
        tracker = PotChangeTracker()
        tracker.update_pot_size(10.0)  # Initial bet
        change = tracker.update_pot_size(30.0)  # Raise (3x pot)

        assert change.change_type == ChangeType.RAISE
        assert change.change_amount == 20.0

    def test_rake_detection(self):
        """Test detection of rake"""
        tracker = PotChangeTracker(rake_percentage=0.05)
        tracker.update_pot_size(100.0)  # Build pot
        change = tracker.update_pot_size(95.0)  # 5% rake

        assert change.change_type == ChangeType.RAKE
        assert change.change_amount == -5.0

    def test_pot_award_detection(self):
        """Test detection of pot being awarded"""
        tracker = PotChangeTracker()
        tracker.update_pot_size(100.0)
        change = tracker.update_pot_size(0.0)  # Pot awarded

        assert change.change_type == ChangeType.AWARD
        assert change.new_size == 0.0

    def test_insignificant_change_ignored(self):
        """Test that insignificant changes are ignored"""
        tracker = PotChangeTracker(min_change_threshold=1.0)
        tracker.update_pot_size(10.0)
        change = tracker.update_pot_size(10.5)  # Only $0.50 change

        assert change is None  # Too small to track

    def test_position_tracking(self):
        """Test tracking of player positions"""
        tracker = PotChangeTracker()
        change = tracker.update_pot_size(10.0, player_position="BTN")

        assert change.player_position == "BTN"

    def test_session_tracking(self):
        """Test tracking of session IDs"""
        tracker = PotChangeTracker()
        change = tracker.update_pot_size(10.0, session_id="session_123")

        assert change.session_id == "session_123"

    def test_get_recent_changes(self):
        """Test retrieval of recent changes"""
        tracker = PotChangeTracker()

        # Create 5 changes
        for i in range(5):
            tracker.update_pot_size((i + 1) * 10.0)

        recent = tracker.get_recent_changes(count=3)
        assert len(recent) == 3
        assert recent[-1].new_size == 50.0  # Most recent

    def test_get_changes_by_type(self):
        """Test filtering changes by type"""
        tracker = PotChangeTracker()

        tracker.update_pot_size(10.0)  # BET
        tracker.update_pot_size(20.0)  # CALL
        tracker.update_pot_size(50.0)  # RAISE

        bets = tracker.get_changes_by_type(ChangeType.BET)
        calls = tracker.get_changes_by_type(ChangeType.CALL)
        raises = tracker.get_changes_by_type(ChangeType.RAISE)

        assert len(bets) == 1
        assert len(calls) == 1
        assert len(raises) == 1

    def test_total_action_calculation(self):
        """Test calculation of total action"""
        tracker = PotChangeTracker()

        tracker.update_pot_size(10.0)  # +10
        tracker.update_pot_size(20.0)  # +10
        tracker.update_pot_size(50.0)  # +30

        total_action = tracker.get_total_action()
        assert total_action == 50.0

    def test_total_rake_calculation(self):
        """Test calculation of total rake"""
        tracker = PotChangeTracker(rake_percentage=0.05)

        tracker.update_pot_size(100.0)
        tracker.update_pot_size(95.0)  # -5 rake
        tracker.update_pot_size(200.0)
        tracker.update_pot_size(190.0)  # -10 rake

        total_rake = tracker.get_total_rake()
        assert total_rake == 15.0

    def test_action_by_position(self):
        """Test tracking action by position"""
        tracker = PotChangeTracker()

        tracker.update_pot_size(10.0, player_position="BTN")
        tracker.update_pot_size(20.0, player_position="SB")
        tracker.update_pot_size(40.0, player_position="BTN")

        action_by_pos = tracker.get_action_by_position()

        assert action_by_pos["BTN"] == 30.0  # 10 + 20
        assert action_by_pos["SB"] == 10.0

    def test_anomaly_detection(self):
        """Test detection of anomalous changes"""
        tracker = PotChangeTracker()

        # Create normal changes
        for _ in range(10):
            tracker.update_pot_size(tracker.current_pot_size + 10.0)

        # Create anomalous change
        tracker.update_pot_size(tracker.current_pot_size + 1000.0)

        anomalies = tracker.detect_anomalies(std_dev_threshold=2.0)

        assert len(anomalies) > 0
        assert anomalies[-1].change_amount == 1000.0

    def test_reset_functionality(self):
        """Test tracker reset"""
        tracker = PotChangeTracker()

        tracker.update_pot_size(10.0)
        tracker.update_pot_size(20.0)
        tracker.update_pot_size(30.0)

        assert len(tracker.change_history) == 3
        assert tracker.current_pot_size == 30.0

        tracker.reset()

        assert len(tracker.change_history) == 0
        assert tracker.current_pot_size == 0.0
        assert tracker.previous_pot_size == 0.0
        assert tracker.frame_count == 0

    def test_statistics_generation(self):
        """Test generation of tracker statistics"""
        tracker = PotChangeTracker(rake_percentage=0.05)

        tracker.update_pot_size(10.0, player_position="BTN")  # BET
        tracker.update_pot_size(20.0, player_position="SB")   # CALL
        tracker.update_pot_size(50.0, player_position="BB")   # RAISE
        tracker.update_pot_size(47.5)  # RAKE (5% of 50)

        stats = tracker.get_statistics()

        assert stats["total_changes"] == 4
        assert stats["total_action"] == 50.0
        assert stats["total_rake"] == 2.5
        assert stats["avg_change"] > 0
        assert stats["largest_change"] == 30.0
        assert "changes_by_type" in stats
        assert "action_by_position" in stats

    def test_empty_tracker_statistics(self):
        """Test statistics on empty tracker"""
        tracker = PotChangeTracker()
        stats = tracker.get_statistics()

        assert stats["total_changes"] == 0
        assert stats["total_action"] == 0.0
        assert stats["total_rake"] == 0.0
        assert stats["avg_change"] == 0.0
        assert stats["largest_change"] == 0.0

    def test_realistic_hand_progression(self):
        """Test realistic poker hand pot progression"""
        tracker = PotChangeTracker(rake_percentage=0.05)

        # Preflop
        tracker.update_pot_size(1.5, player_position="SB")   # SB posts
        tracker.update_pot_size(3.0, player_position="BB")   # BB posts
        tracker.update_pot_size(9.0, player_position="UTG")  # UTG raises to 9
        tracker.update_pot_size(18.0, player_position="BTN") # BTN calls
        tracker.update_pot_size(27.0, player_position="BB")  # BB calls

        # Flop
        tracker.update_pot_size(54.0, player_position="BB")  # BB bets pot
        tracker.update_pot_size(81.0, player_position="BTN") # BTN calls

        # Turn
        tracker.update_pot_size(162.0, player_position="BB") # BB bets pot

        # River (BTN folds, pot awarded with rake)
        tracker.update_pot_size(154.0)  # 5% rake
        tracker.update_pot_size(0.0)    # Pot awarded

        stats = tracker.get_statistics()

        assert stats["total_changes"] == 10
        assert stats["total_rake"] == 8.0
        assert stats["total_action"] > 0

        # Verify hand ended properly
        assert tracker.change_history[-1].change_type == ChangeType.AWARD

    def test_confidence_tracking(self):
        """Test that confidence scores are tracked"""
        tracker = PotChangeTracker()

        change1 = tracker.update_pot_size(10.0, confidence=0.95)
        change2 = tracker.update_pot_size(20.0, confidence=0.85)
        change3 = tracker.update_pot_size(30.0, confidence=0.75)

        assert change1.confidence == 0.95
        assert change2.confidence == 0.85
        assert change3.confidence == 0.75

    def test_frame_number_increment(self):
        """Test that frame numbers increment correctly"""
        tracker = PotChangeTracker()

        change1 = tracker.update_pot_size(10.0)
        change2 = tracker.update_pot_size(20.0)
        change3 = tracker.update_pot_size(30.0)

        assert change1.frame_number == 1
        assert change2.frame_number == 2
        assert change3.frame_number == 3

    def test_timestamp_ordering(self):
        """Test that timestamps are in chronological order"""
        tracker = PotChangeTracker()

        change1 = tracker.update_pot_size(10.0)
        change2 = tracker.update_pot_size(20.0)
        change3 = tracker.update_pot_size(30.0)

        assert change1.timestamp <= change2.timestamp <= change3.timestamp

    def test_negative_change_classification(self):
        """Test classification of negative pot changes"""
        tracker = PotChangeTracker(rake_percentage=0.05)

        tracker.update_pot_size(100.0)

        # Small decrease - likely rake
        rake_change = tracker.update_pot_size(95.0)
        assert rake_change.change_type == ChangeType.RAKE

        # Large decrease - likely return
        return_change = tracker.update_pot_size(50.0)
        assert return_change.change_type == ChangeType.RETURN

    def test_zero_pot_handling(self):
        """Test handling of zero pot size"""
        tracker = PotChangeTracker()

        # Start with zero
        assert tracker.current_pot_size == 0.0

        # Update to non-zero
        change1 = tracker.update_pot_size(10.0)
        assert change1.change_type == ChangeType.BET

        # Return to zero
        change2 = tracker.update_pot_size(0.0)
        assert change2.change_type == ChangeType.AWARD


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
