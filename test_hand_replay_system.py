# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_hand_replay_system.py
# version: v28.0.0
# last_commit: '2025-09-30T12:00:00+01:00'
# fixes:
# - date: '2025-09-30'
#   summary: Unit tests for Hand Replay System (REPLAY-001)
# ---
# POKERTOOL-HEADER-END

"""
Unit tests for Hand Replay System.

Tests all components of the hand replay system including:
- Frame management
- Animation calculations
- Analysis overlay
- Annotation management
- Sharing/export functionality
"""

from __future__ import annotations

import pytest
import json
import datetime
from pathlib import Path
from typing import Dict, List
import tempfile
import shutil

from hand_replay_system import (
    HandReplaySystem,
    ReplayFrame,
    ReplayAnimation,
    AnalysisOverlay,
    AnnotationManager,
    ShareManager,
    PlayerAction,
    ActionType,
    Street,
    Annotation,
    AnalysisData
)


class TestPlayerAction:
    """Test suite for PlayerAction class."""
    
    def test_create_player_action(self):
        """Test creating a player action."""
        action = PlayerAction(
            player_name="TestPlayer",
            action_type=ActionType.RAISE,
            amount=50.0,
            position="BTN"
        )
        
        assert action.player_name == "TestPlayer"
        assert action.action_type == ActionType.RAISE
        assert action.amount == 50.0
        assert action.position == "BTN"
        assert action.timestamp is not None
    
    def test_player_action_serialization(self):
        """Test serialization and deserialization of PlayerAction."""
        action = PlayerAction(
            player_name="TestPlayer",
            action_type=ActionType.BET,
            amount=25.0
        )
        
        # Serialize
        action_dict = action.to_dict()
        assert action_dict['player_name'] == "TestPlayer"
        assert action_dict['action_type'] == "bet"
        assert action_dict['amount'] == 25.0
        
        # Deserialize
        restored_action = PlayerAction.from_dict(action_dict)
        assert restored_action.player_name == action.player_name
        assert restored_action.action_type == action.action_type
        assert restored_action.amount == action.amount


class TestReplayFrame:
    """Test suite for ReplayFrame class."""
    
    def test_create_frame(self):
        """Test creating a replay frame."""
        frame = ReplayFrame(
            frame_id=0,
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Player1": 900.0, "Player2": 950.0}
        )
        
        assert frame.frame_id == 0
        assert frame.street == Street.FLOP
        assert frame.pot_size == 100.0
        assert len(frame.board_cards) == 3
        assert "Player1" in frame.player_stacks
    
    def test_frame_with_action(self):
        """Test frame with player action."""
        action = PlayerAction(
            player_name="Player1",
            action_type=ActionType.BET,
            amount=50.0
        )
        
        frame = ReplayFrame(
            frame_id=1,
            street=Street.FLOP,
            pot_size=150.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Player1": 850.0, "Player2": 950.0},
            action=action,
            description="Player1 bets $50"
        )
        
        assert frame.action is not None
        assert frame.action.action_type == ActionType.BET
        assert frame.description == "Player1 bets $50"
    
    def test_frame_serialization(self):
        """Test frame serialization and deserialization."""
        frame = ReplayFrame(
            frame_id=2,
            street=Street.TURN,
            pot_size=200.0,
            board_cards=["As", "Kh", "Qd", "7c"],
            player_stacks={"Player1": 800.0, "Player2": 900.0}
        )
        
        # Serialize
        frame_dict = frame.to_dict()
        assert frame_dict['frame_id'] == 2
        assert frame_dict['street'] == "turn"
        
        # Deserialize
        restored_frame = ReplayFrame.from_dict(frame_dict)
        assert restored_frame.frame_id == frame.frame_id
        assert restored_frame.street == frame.street
        assert restored_frame.pot_size == frame.pot_size


class TestAnnotation:
    """Test suite for Annotation class."""
    
    def test_create_annotation(self):
        """Test creating an annotation."""
        annotation = Annotation(
            annotation_id="test_1",
            frame_id=5,
            text="Good spot to bluff",
            author="Analyst1",
            position=(100.0, 200.0),
            color="#FF0000"
        )
        
        assert annotation.annotation_id == "test_1"
        assert annotation.frame_id == 5
        assert annotation.text == "Good spot to bluff"
        assert annotation.author == "Analyst1"
        assert annotation.position == (100.0, 200.0)
        assert annotation.color == "#FF0000"
    
    def test_annotation_serialization(self):
        """Test annotation serialization."""
        annotation = Annotation(
            annotation_id="test_2",
            frame_id=10,
            text="Consider check-raising here",
            author="Pro1"
        )
        
        # Serialize
        ann_dict = annotation.to_dict()
        assert ann_dict['annotation_id'] == "test_2"
        assert ann_dict['text'] == "Consider check-raising here"
        
        # Deserialize
        restored = Annotation.from_dict(ann_dict)
        assert restored.annotation_id == annotation.annotation_id
        assert restored.text == annotation.text


class TestAnnotationManager:
    """Test suite for AnnotationManager class."""
    
    def test_add_annotation(self):
        """Test adding annotations."""
        manager = AnnotationManager()
        
        annotation = manager.add_annotation(
            frame_id=1,
            text="Test annotation",
            author="Tester"
        )
        
        assert annotation.frame_id == 1
        assert annotation.text == "Test annotation"
        assert 1 in manager.annotations
    
    def test_get_annotations(self):
        """Test retrieving annotations for a frame."""
        manager = AnnotationManager()
        
        manager.add_annotation(frame_id=1, text="First", author="User1")
        manager.add_annotation(frame_id=1, text="Second", author="User2")
        manager.add_annotation(frame_id=2, text="Third", author="User3")
        
        frame_1_annotations = manager.get_annotations(1)
        assert len(frame_1_annotations) == 2
        
        frame_2_annotations = manager.get_annotations(2)
        assert len(frame_2_annotations) == 1
    
    def test_delete_annotation(self):
        """Test deleting annotations."""
        manager = AnnotationManager()
        
        annotation = manager.add_annotation(
            frame_id=1,
            text="To be deleted",
            author="User"
        )
        
        # Delete annotation
        result = manager.delete_annotation(annotation.annotation_id)
        assert result is True
        
        # Verify it's gone
        annotations = manager.get_annotations(1)
        assert len(annotations) == 0
        
        # Try to delete non-existent annotation
        result = manager.delete_annotation("fake_id")
        assert result is False
    
    def test_annotation_serialization(self):
        """Test annotation manager serialization."""
        manager = AnnotationManager()
        
        manager.add_annotation(frame_id=1, text="Ann1", author="User1")
        manager.add_annotation(frame_id=2, text="Ann2", author="User2")
        
        # Export
        data = manager.to_dict()
        assert '1' in data
        assert '2' in data
        
        # Import
        new_manager = AnnotationManager()
        new_manager.from_dict(data)
        assert len(new_manager.get_annotations(1)) == 1
        assert len(new_manager.get_annotations(2)) == 1


class TestAnalysisData:
    """Test suite for AnalysisData class."""
    
    def test_create_analysis_data(self):
        """Test creating analysis data."""
        analysis = AnalysisData(
            equity=65.5,
            pot_odds=0.25,
            recommended_action="RAISE",
            explanation="Strong equity advantage"
        )
        
        assert analysis.equity == 65.5
        assert analysis.pot_odds == 0.25
        assert analysis.recommended_action == "RAISE"
    
    def test_analysis_serialization(self):
        """Test analysis data serialization."""
        analysis = AnalysisData(
            equity=55.0,
            pot_odds=0.33,
            recommended_action="CALL"
        )
        
        # Serialize
        data = analysis.to_dict()
        assert data['equity'] == 55.0
        
        # Deserialize
        restored = AnalysisData.from_dict(data)
        assert restored.equity == analysis.equity
        assert restored.recommended_action == analysis.recommended_action


class TestAnalysisOverlay:
    """Test suite for AnalysisOverlay class."""
    
    def test_analyze_frame(self):
        """Test analyzing a frame."""
        overlay = AnalysisOverlay()
        
        action = PlayerAction(
            player_name="Villain",
            action_type=ActionType.BET,
            amount=50.0
        )
        
        frame = ReplayFrame(
            frame_id=0,
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Hero": 900.0, "Villain": 850.0},
            action=action
        )
        
        analysis = overlay.analyze_frame(frame, ["Ac", "Kd"])
        
        assert analysis.equity is not None
        assert analysis.pot_odds is not None
        assert analysis.recommended_action is not None
        assert len(analysis.explanation) > 0
    
    def test_analysis_caching(self):
        """Test that analysis results are cached."""
        overlay = AnalysisOverlay()
        
        frame = ReplayFrame(
            frame_id=1,
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["2h", "3d", "4c"],
            player_stacks={"Hero": 900.0}
        )
        
        # First analysis
        analysis1 = overlay.analyze_frame(frame, ["Ah", "Kh"])
        
        # Second analysis (should be cached)
        analysis2 = overlay.analyze_frame(frame, ["Ah", "Kh"])
        
        assert analysis1 is analysis2  # Same object due to caching
        assert frame.frame_id in overlay.analysis_cache
    
    def test_pot_odds_calculation(self):
        """Test pot odds calculation."""
        overlay = AnalysisOverlay()
        
        action = PlayerAction(
            player_name="Villain",
            action_type=ActionType.BET,
            amount=100.0
        )
        
        frame = ReplayFrame(
            frame_id=2,
            street=Street.TURN,
            pot_size=200.0,
            board_cards=["Ah", "Kh", "Qd", "7c"],
            player_stacks={"Hero": 900.0, "Villain": 800.0},
            action=action
        )
        
        analysis = overlay.analyze_frame(frame, ["As", "Ks"])
        
        # Pot odds = call_amount / (pot + call_amount)
        # = 100 / (200 + 100) = 100 / 300 = 0.333...
        expected_pot_odds = 100.0 / 300.0
        assert abs(analysis.pot_odds - expected_pot_odds) < 0.001


class TestReplayAnimation:
    """Test suite for ReplayAnimation class."""
    
    def test_create_animation(self):
        """Test creating animation controller."""
        animation = ReplayAnimation(fps=60, duration_ms=500)
        
        assert animation.fps == 60
        assert animation.duration_ms == 500
        assert animation.current_speed == 1.0
    
    def test_calculate_transition(self):
        """Test transition calculation between frames."""
        animation = ReplayAnimation()
        
        start_frame = ReplayFrame(
            frame_id=0,
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Player1": 1000.0, "Player2": 1000.0}
        )
        
        end_frame = ReplayFrame(
            frame_id=1,
            street=Street.FLOP,
            pot_size=200.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Player1": 900.0, "Player2": 1100.0}
        )
        
        # Test at 50% progress
        transition = animation.calculate_transition(start_frame, end_frame, 0.5)
        
        assert transition['pot_size'] == 150.0  # Midpoint
        assert transition['player_stacks']['Player1'] == 950.0
        assert transition['player_stacks']['Player2'] == 1050.0
        assert transition['progress'] == 0.5
    
    def test_transition_edge_cases(self):
        """Test transition at edge cases (0% and 100%)."""
        animation = ReplayAnimation()
        
        start_frame = ReplayFrame(
            frame_id=0,
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=[],
            player_stacks={"Player1": 1000.0}
        )
        
        end_frame = ReplayFrame(
            frame_id=1,
            street=Street.FLOP,
            pot_size=200.0,
            board_cards=[],
            player_stacks={"Player1": 900.0}
        )
        
        # At 0% progress
        transition_start = animation.calculate_transition(start_frame, end_frame, 0.0)
        assert transition_start['pot_size'] == 100.0
        
        # At 100% progress
        transition_end = animation.calculate_transition(start_frame, end_frame, 1.0)
        assert transition_end['pot_size'] == 200.0
    
    def test_invalid_progress(self):
        """Test that invalid progress values raise error."""
        animation = ReplayAnimation()
        
        frame = ReplayFrame(
            frame_id=0,
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=[],
            player_stacks={}
        )
        
        with pytest.raises(ValueError):
            animation.calculate_transition(frame, frame, -0.1)
        
        with pytest.raises(ValueError):
            animation.calculate_transition(frame, frame, 1.1)
    
    def test_set_speed(self):
        """Test setting animation speed."""
        animation = ReplayAnimation()
        
        animation.set_speed(2.0)
        assert animation.current_speed == 2.0
        
        animation.set_speed(0.5)
        assert animation.current_speed == 0.5
        
        with pytest.raises(ValueError):
            animation.set_speed(0.0)
        
        with pytest.raises(ValueError):
            animation.set_speed(-1.0)


class TestShareManager:
    """Test suite for ShareManager class."""
    
    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for exports."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_create_share_manager(self, temp_export_dir):
        """Test creating share manager."""
        manager = ShareManager(export_dir=temp_export_dir)
        
        assert manager.export_dir == temp_export_dir
        assert manager.export_dir.exists()
    
    def test_export_to_json(self, temp_export_dir):
        """Test exporting replay to JSON."""
        manager = ShareManager(export_dir=temp_export_dir)
        
        frames = [
            ReplayFrame(
                frame_id=0,
                street=Street.PREFLOP,
                pot_size=0.0,
                board_cards=[],
                player_stacks={"Player1": 1000.0}
            ),
            ReplayFrame(
                frame_id=1,
                street=Street.FLOP,
                pot_size=20.0,
                board_cards=["As", "Kh", "Qd"],
                player_stacks={"Player1": 990.0}
            )
        ]
        
        output_path = manager.export_to_json(frames, "test_hand")
        
        assert output_path.exists()
        assert output_path.name == "test_hand.json"
        
        # Verify contents
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['frame_count'] == 2
        assert len(data['frames']) == 2
    
    def test_export_with_annotations(self, temp_export_dir):
        """Test exporting replay with annotations."""
        manager = ShareManager(export_dir=temp_export_dir)
        
        frames = [
            ReplayFrame(
                frame_id=0,
                street=Street.FLOP,
                pot_size=100.0,
                board_cards=["As", "Kh", "Qd"],
                player_stacks={"Player1": 900.0}
            )
        ]
        
        annotations = {
            0: [
                Annotation(
                    annotation_id="ann_1",
                    frame_id=0,
                    text="Test annotation",
                    author="Tester"
                )
            ]
        }
        
        output_path = manager.export_to_json(
            frames,
            "test_with_annotations",
            annotations=annotations
        )
        
        # Verify annotations in export
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'annotations' in data
        assert '0' in data['annotations']
    
    def test_import_from_json(self, temp_export_dir):
        """Test importing replay from JSON."""
        manager = ShareManager(export_dir=temp_export_dir)
        
        # First export
        original_frames = [
            ReplayFrame(
                frame_id=0,
                street=Street.FLOP,
                pot_size=100.0,
                board_cards=["As", "Kh"],
                player_stacks={"Player1": 900.0}
            )
        ]
        
        export_path = manager.export_to_json(original_frames, "import_test")
        
        # Then import
        imported_frames, imported_annotations = manager.import_from_json(export_path)
        
        assert len(imported_frames) == 1
        assert imported_frames[0].pot_size == 100.0
        assert imported_frames[0].street == Street.FLOP
    
    def test_generate_share_link(self, temp_export_dir):
        """Test generating share link."""
        manager = ShareManager(export_dir=temp_export_dir)
        
        link = manager.generate_share_link("abc123")
        
        assert "abc123" in link
        assert link.startswith("http")


class TestHandReplaySystem:
    """Test suite for HandReplaySystem class."""
    
    def test_create_system(self):
        """Test creating hand replay system."""
        system = HandReplaySystem()
        
        assert len(system.frames) == 0
        assert system.current_frame_index == 0
        assert system.animation is not None
        assert system.analysis_overlay is not None
        assert system.annotation_manager is not None
        assert system.share_manager is not None
    
    def test_add_frame(self):
        """Test adding frames to replay."""
        system = HandReplaySystem()
        
        frame1 = system.add_frame(
            street=Street.PREFLOP,
            pot_size=0.0,
            board_cards=[],
            player_stacks={"Player1": 1000.0, "Player2": 1000.0}
        )
        
        assert frame1.frame_id == 0
        assert len(system.frames) == 1
        
        frame2 = system.add_frame(
            street=Street.FLOP,
            pot_size=20.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Player1": 990.0, "Player2": 990.0}
        )
        
        assert frame2.frame_id == 1
        assert len(system.frames) == 2
    
    def test_navigation(self):
        """Test frame navigation."""
        system = HandReplaySystem()
        
        # Add multiple frames
        for i in range(5):
            system.add_frame(
                street=Street.FLOP,
                pot_size=float(i * 10),
                board_cards=[],
                player_stacks={}
            )
        
        # Test next
        frame = system.next_frame()
        assert frame.frame_id == 1
        assert system.current_frame_index == 1
        
        # Test previous
        frame = system.previous_frame()
        assert frame.frame_id == 0
        assert system.current_frame_index == 0
        
        # Test jump
        frame = system.jump_to_frame(3)
        assert frame.frame_id == 3
        assert system.current_frame_index == 3
    
    def test_navigation_boundaries(self):
        """Test navigation at boundaries."""
        system = HandReplaySystem()
        
        system.add_frame(
            street=Street.FLOP,
            pot_size=0.0,
            board_cards=[],
            player_stacks={}
        )
        
        # Try to go previous from start
        result = system.previous_frame()
        assert result is None
        assert system.current_frame_index == 0
        
        # Try to go next from end
        result = system.next_frame()
        assert result is None
        assert system.current_frame_index == 0
    
    def test_get_frame(self):
        """Test getting specific frame."""
        system = HandReplaySystem()
        
        system.add_frame(
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["As"],
            player_stacks={}
        )
        
        frame = system.get_frame(0)
        assert frame is not None
        assert frame.pot_size == 100.0
        
        # Non-existent frame
        frame = system.get_frame(999)
        assert frame is None
    
    def test_analyze_current_frame(self):
        """Test analyzing current frame."""
        system = HandReplaySystem()
        
        action = PlayerAction(
            player_name="Villain",
            action_type=ActionType.BET,
            amount=50.0
        )
        
        system.add_frame(
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Hero": 900.0, "Villain": 850.0},
            action=action
        )
        
        analysis = system.analyze_current_frame(["Ac", "Kc"])
        
        assert analysis is not None
        assert analysis.equity is not None
        assert analysis.pot_odds is not None
    
    def test_export_and_import(self):
        """Test complete export and import cycle."""
        system1 = HandReplaySystem()
        
        # Build a replay
        system1.add_frame(
            street=Street.PREFLOP,
            pot_size=0.0,
            board_cards=[],
            player_stacks={"Player1": 1000.0}
        )
        
        system1.add_frame(
            street=Street.FLOP,
            pot_size=20.0,
            board_cards=["As", "Kh", "Qd"],
            player_stacks={"Player1": 990.0}
        )
        
        # Add annotation
        system1.annotation_manager.add_annotation(
            frame_id=1,
            text="Test annotation",
            author="Tester"
        )
        
        # Export
        export_path = system1.export_replay("cycle_test")
        assert export_path.exists()
        
        # Import into new system
        system2 = HandReplaySystem()
        system2.import_replay(export_path)
        
        assert len(system2.frames) == 2
        assert system2.frames[0].street == Street.PREFLOP
        assert system2.frames[1].pot_size == 20.0
        assert len(system2.annotation_manager.get_annotations(1)) == 1
    
    def test_get_frame_count(self):
        """Test getting frame count."""
        system = HandReplaySystem()
        
        assert system.get_frame_count() == 0
        
        system.add_frame(
            street=Street.FLOP,
            pot_size=0.0,
            board_cards=[],
            player_stacks={}
        )
        
        assert system.get_frame_count() == 1
        
        for _ in range(5):
            system.add_frame(
                street=Street.FLOP,
                pot_size=0.0,
                board_cards=[],
                player_stacks={}
            )
        
        assert system.get_frame_count() == 6
    
    def test_reset(self):
        """Test resetting the replay system."""
        system = HandReplaySystem()
        
        # Add data
        system.add_frame(
            street=Street.FLOP,
            pot_size=100.0,
            board_cards=["As"],
            player_stacks={"Player1": 900.0}
        )
        
        system.annotation_manager.add_annotation(
            frame_id=0,
            text="Test",
            author="User"
        )
        
        # Reset
        system.reset()
        
        assert len(system.frames) == 0
        assert system.current_frame_index == 0
        assert len(system.annotation_manager.annotations) == 0
        assert len(system.analysis_overlay.analysis_cache) == 0


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_hand_replay_workflow(self):
        """Test a complete hand replay workflow from start to finish."""
        system = HandReplaySystem()
        
        # Preflop
        action1 = PlayerAction(
            player_name="BTN",
            action_type=ActionType.RAISE,
            amount=10.0,
            position="BTN"
        )
        
        system.add_frame(
            street=Street.PREFLOP,
            pot_size=10.0,
            board_cards=[],
            player_stacks={"BTN": 990.0, "BB": 1000.0},
            action=action1,
            description="BTN raises to $10"
        )
        
        # Flop
        action2 = PlayerAction(
            player_name="BB",
            action_type=ActionType.CALL,
            amount=10.0,
            position="BB"
        )
        
        system.add_frame(
            street=Street.FLOP,
            pot_size=20.0,
            board_cards=["As", "Kh", "7d"],
            player_stacks={"BTN": 990.0, "BB": 990.0},
            action=action2,
            description="BB calls"
        )
        
        # Add annotations
        system.annotation_manager.add_annotation(
            frame_id=1,
            text="Strong flop for AK",
            author="Coach"
        )
        
        # Navigate and analyze
        system.jump_to_frame(1)
        analysis = system.analyze_current_frame(["As", "Kc"])
        
        assert analysis is not None
        assert system.get_frame_count() == 2
        
        # Export
        export_path = system.export_replay("complete_hand")
        assert export_path.exists()
        
        # Verify export structure
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        assert data['frame_count'] == 2
        assert 'annotations' in data
        
        # Import and verify
        new_system = HandReplaySystem()
        new_system.import_replay(export_path)
        
        assert new_system.get_frame_count() == 2
        assert len(new_system.annotation_manager.get_annotations(1)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
