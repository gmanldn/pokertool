# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: hand_replay_system.py
# version: v28.0.0
# last_commit: '2025-09-30T12:00:00+01:00'
# fixes:
# - date: '2025-09-30'
#   summary: Initial implementation of Hand Replay System (REPLAY-001)
# ---
# POKERTOOL-HEADER-END

"""
Hand Replay System Module

This module provides visual hand replay capabilities with animation support,
analysis overlays, sharing mechanisms, and annotation features.

Public API:
    - HandReplaySystem: Main replay system class
    - ReplayFrame: Represents a single frame in the replay
    - ReplayAnimation: Handles animation between frames
    - AnalysisOverlay: Provides strategic analysis during replay
    - ShareManager: Handles sharing and export functionality
    - AnnotationManager: Manages annotations on replays

Dependencies:
    - poker_config (for configuration)
    - logger (for logging)
    - json, datetime (standard library)

Last Reviewed: 2025-09-30
"""

from __future__ import annotations

import json
import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
from pathlib import Path

try:
    from pokertool.modules.logger import logger, log_exceptions
except ImportError:
    # Fallback for standalone usage
    class _FakeLogger:
        """Fallback logger when main logger unavailable."""
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
        def debug(self, *args, **kwargs): pass
    
    logger = _FakeLogger()
    
    def log_exceptions(func):
        """Fallback decorator."""
        return func


class ActionType(Enum):
    """Enumeration of possible poker actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"
    DEAL = "deal"
    SHOW = "show"


class Street(Enum):
    """Enumeration of poker streets."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


@dataclass
class PlayerAction:
    """Represents a single player action in a hand."""
    player_name: str
    action_type: ActionType
    amount: float = 0.0
    timestamp: Optional[datetime.datetime] = None
    position: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'player_name': self.player_name,
            'action_type': self.action_type.value,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'position': self.position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerAction':
        """Create from dictionary."""
        data['action_type'] = ActionType(data['action_type'])
        if data.get('timestamp'):
            data['timestamp'] = datetime.datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ReplayFrame:
    """
    Represents a single frame in a hand replay.
    
    A frame captures the complete state at a specific moment during hand play.
    """
    frame_id: int
    street: Street
    pot_size: float
    board_cards: List[str] = field(default_factory=list)
    player_stacks: Dict[str, float] = field(default_factory=dict)
    action: Optional[PlayerAction] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'frame_id': self.frame_id,
            'street': self.street.value,
            'pot_size': self.pot_size,
            'board_cards': self.board_cards,
            'player_stacks': self.player_stacks,
            'action': self.action.to_dict() if self.action else None,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReplayFrame':
        """Create from dictionary."""
        data['street'] = Street(data['street'])
        if data.get('action'):
            data['action'] = PlayerAction.from_dict(data['action'])
        return cls(**data)


@dataclass
class Annotation:
    """Represents an annotation on a replay frame."""
    annotation_id: str
    frame_id: int
    text: str
    author: str
    position: Tuple[float, float] = (0.0, 0.0)  # x, y coordinates
    color: str = "#FFFF00"  # Default yellow
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'annotation_id': self.annotation_id,
            'frame_id': self.frame_id,
            'text': self.text,
            'author': self.author,
            'position': list(self.position),
            'color': self.color,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Annotation':
        """Create from dictionary."""
        data['position'] = tuple(data['position'])
        data['created_at'] = datetime.datetime.fromisoformat(data['created_at'])
        return cls(**data)


class AnnotationManager:
    """
    Manages annotations for replay frames.
    
    Provides functionality to add, edit, delete, and retrieve annotations.
    """
    
    def __init__(self):
        """Initialize annotation manager."""
        self.annotations: Dict[int, List[Annotation]] = {}
        logger.info("AnnotationManager initialized")
    
    @log_exceptions
    def add_annotation(
        self,
        frame_id: int,
        text: str,
        author: str,
        position: Tuple[float, float] = (0.0, 0.0),
        color: str = "#FFFF00"
    ) -> Annotation:
        """
        Add an annotation to a frame.
        
        Args:
            frame_id: ID of the frame to annotate
            text: Annotation text
            author: Name of annotation author
            position: (x, y) coordinates for annotation placement
            color: Hex color code for annotation
            
        Returns:
            Created Annotation object
        """
        annotation_id = f"{frame_id}_{len(self.annotations.get(frame_id, []))}"
        annotation = Annotation(
            annotation_id=annotation_id,
            frame_id=frame_id,
            text=text,
            author=author,
            position=position,
            color=color
        )
        
        if frame_id not in self.annotations:
            self.annotations[frame_id] = []
        
        self.annotations[frame_id].append(annotation)
        logger.info(f"Added annotation to frame {frame_id}", annotation_id=annotation_id)
        return annotation
    
    @log_exceptions
    def get_annotations(self, frame_id: int) -> List[Annotation]:
        """
        Get all annotations for a specific frame.
        
        Args:
            frame_id: ID of the frame
            
        Returns:
            List of annotations for the frame
        """
        return self.annotations.get(frame_id, [])
    
    @log_exceptions
    def delete_annotation(self, annotation_id: str) -> bool:
        """
        Delete an annotation by ID.
        
        Args:
            annotation_id: ID of annotation to delete
            
        Returns:
            True if deleted, False if not found
        """
        for frame_id, annotations in self.annotations.items():
            for i, annotation in enumerate(annotations):
                if annotation.annotation_id == annotation_id:
                    del self.annotations[frame_id][i]
                    logger.info(f"Deleted annotation {annotation_id} from frame {frame_id}")
                    return True
        
        logger.warning(f"Annotation {annotation_id} not found")
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all annotations to dictionary."""
        return {
            str(frame_id): [ann.to_dict() for ann in annotations]
            for frame_id, annotations in self.annotations.items()
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Import annotations from dictionary."""
        self.annotations = {
            int(frame_id): [Annotation.from_dict(ann) for ann in annotations]
            for frame_id, annotations in data.items()
        }


@dataclass
class AnalysisData:
    """Strategic analysis data for a replay frame."""
    equity: Optional[float] = None
    pot_odds: Optional[float] = None
    recommended_action: Optional[str] = None
    explanation: str = ""
    ev_calculation: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisData':
        """Create from dictionary."""
        return cls(**data)


class AnalysisOverlay:
    """
    Provides strategic analysis overlay for replay frames.
    
    Calculates and displays equity, pot odds, recommended actions, and EV.
    """
    
    def __init__(self):
        """Initialize analysis overlay."""
        self.analysis_cache: Dict[int, AnalysisData] = {}
        logger.info("AnalysisOverlay initialized")
    
    @log_exceptions
    def analyze_frame(self, frame: ReplayFrame, hole_cards: List[str]) -> AnalysisData:
        """
        Analyze a replay frame for strategic insights.
        
        Args:
            frame: ReplayFrame to analyze
            hole_cards: Player's hole cards
            
        Returns:
            AnalysisData with strategic insights
        """
        # Cache check
        if frame.frame_id in self.analysis_cache:
            return self.analysis_cache[frame.frame_id]
        
        analysis = AnalysisData()
        
        # Calculate equity (simplified - would use actual equity calculator in production)
        if len(frame.board_cards) > 0:
            # Placeholder equity calculation
            analysis.equity = self._calculate_equity(hole_cards, frame.board_cards)
        
        # Calculate pot odds
        if frame.action and frame.action.action_type in [ActionType.BET, ActionType.RAISE]:
            call_amount = frame.action.amount
            pot_after_call = frame.pot_size + call_amount
            analysis.pot_odds = call_amount / pot_after_call if pot_after_call > 0 else 0
        
        # Recommend action
        analysis.recommended_action = self._recommend_action(frame, analysis)
        analysis.explanation = self._generate_explanation(frame, analysis)
        
        # Cache the analysis
        self.analysis_cache[frame.frame_id] = analysis
        logger.debug(f"Analyzed frame {frame.frame_id}", analysis=analysis.to_dict())
        
        return analysis
    
    def _calculate_equity(self, hole_cards: List[str], board_cards: List[str]) -> float:
        """
        Calculate hand equity.
        
        Note: This is a simplified placeholder. Production version would use
        actual poker hand evaluation and Monte Carlo simulation.
        
        Args:
            hole_cards: Player's hole cards
            board_cards: Community cards
            
        Returns:
            Estimated equity as percentage (0-100)
        """
        # Placeholder: Would integrate with actual hand evaluator
        # For now, return a reasonable estimate based on street
        if len(board_cards) == 0:
            return 50.0  # Preflop, assume average equity
        elif len(board_cards) == 3:
            return 45.0  # Flop
        elif len(board_cards) == 4:
            return 40.0  # Turn
        else:
            return 35.0  # River
    
    def _recommend_action(self, frame: ReplayFrame, analysis: AnalysisData) -> str:
        """
        Recommend action based on analysis.
        
        Args:
            frame: Current frame
            analysis: Analysis data
            
        Returns:
            Recommended action string
        """
        if analysis.pot_odds and analysis.equity:
            equity_decimal = analysis.equity / 100
            if equity_decimal > analysis.pot_odds * 1.2:
                return "RAISE"
            elif equity_decimal > analysis.pot_odds:
                return "CALL"
            else:
                return "FOLD"
        
        return "CHECK"
    
    def _generate_explanation(self, frame: ReplayFrame, analysis: AnalysisData) -> str:
        """
        Generate explanation for recommended action.
        
        Args:
            frame: Current frame
            analysis: Analysis data
            
        Returns:
            Explanation string
        """
        parts = []
        
        if analysis.equity:
            parts.append(f"Hand equity: {analysis.equity:.1f}%")
        
        if analysis.pot_odds:
            parts.append(f"Pot odds: {analysis.pot_odds * 100:.1f}%")
        
        if analysis.recommended_action:
            parts.append(f"Recommendation: {analysis.recommended_action}")
        
        return " | ".join(parts) if parts else "Analysis unavailable"


class ReplayAnimation:
    """
    Handles animation between replay frames.
    
    Provides smooth transitions and timing control.
    """
    
    def __init__(self, fps: int = 30, duration_ms: int = 1000):
        """
        Initialize animation controller.
        
        Args:
            fps: Frames per second for animation
            duration_ms: Duration of transitions in milliseconds
        """
        self.fps = fps
        self.duration_ms = duration_ms
        self.is_playing = False
        self.current_speed = 1.0
        logger.info("ReplayAnimation initialized", fps=fps, duration_ms=duration_ms)
    
    @log_exceptions
    def calculate_transition(
        self,
        start_frame: ReplayFrame,
        end_frame: ReplayFrame,
        progress: float
    ) -> Dict[str, Any]:
        """
        Calculate interpolated state between two frames.
        
        Args:
            start_frame: Starting frame
            end_frame: Ending frame
            progress: Progress between frames (0.0 to 1.0)
            
        Returns:
            Dictionary with interpolated values
        """
        if not 0 <= progress <= 1:
            raise ValueError("Progress must be between 0 and 1")
        
        # Interpolate pot size
        pot_size = start_frame.pot_size + (end_frame.pot_size - start_frame.pot_size) * progress
        
        # Interpolate player stacks
        player_stacks = {}
        all_players = set(start_frame.player_stacks.keys()) | set(end_frame.player_stacks.keys())
        
        for player in all_players:
            start_stack = start_frame.player_stacks.get(player, 0)
            end_stack = end_frame.player_stacks.get(player, 0)
            player_stacks[player] = start_stack + (end_stack - start_stack) * progress
        
        return {
            'pot_size': pot_size,
            'player_stacks': player_stacks,
            'progress': progress
        }
    
    def set_speed(self, speed: float) -> None:
        """
        Set playback speed.
        
        Args:
            speed: Playback speed multiplier (0.5 = half speed, 2.0 = double speed)
        """
        if speed <= 0:
            raise ValueError("Speed must be positive")
        
        self.current_speed = speed
        logger.info(f"Animation speed set to {speed}x")


class ShareManager:
    """
    Manages sharing and export of hand replays.
    
    Supports multiple export formats and sharing platforms.
    """
    
    def __init__(self, export_dir: Optional[Path] = None):
        """
        Initialize share manager.
        
        Args:
            export_dir: Directory for exported files (default: ./exports)
        """
        self.export_dir = export_dir or Path("./exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ShareManager initialized", export_dir=str(self.export_dir))
    
    @log_exceptions
    def export_to_json(
        self,
        frames: List[ReplayFrame],
        filename: str,
        include_analysis: bool = False,
        annotations: Optional[Dict[int, List[Annotation]]] = None
    ) -> Path:
        """
        Export replay to JSON format.
        
        Args:
            frames: List of replay frames
            filename: Output filename
            include_analysis: Whether to include analysis data
            annotations: Optional annotations to include
            
        Returns:
            Path to exported file
        """
        export_data = {
            'version': '1.0',
            'exported_at': datetime.datetime.now().isoformat(),
            'frame_count': len(frames),
            'frames': [frame.to_dict() for frame in frames]
        }
        
        if annotations:
            export_data['annotations'] = {
                str(k): [ann.to_dict() for ann in v]
                for k, v in annotations.items()
            }
        
        output_path = self.export_dir / f"{filename}.json"
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported replay to {output_path}", frame_count=len(frames))
        return output_path
    
    @log_exceptions
    def import_from_json(self, filepath: Path) -> Tuple[List[ReplayFrame], Optional[Dict[int, List[Annotation]]]]:
        """
        Import replay from JSON format.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Tuple of (frames, annotations)
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        frames = [ReplayFrame.from_dict(frame_data) for frame_data in data['frames']]
        
        annotations = None
        if 'annotations' in data:
            annotations = {
                int(frame_id): [Annotation.from_dict(ann) for ann in anns]
                for frame_id, anns in data['annotations'].items()
            }
        
        logger.info(f"Imported replay from {filepath}", frame_count=len(frames))
        return frames, annotations
    
    @log_exceptions
    def generate_share_link(self, replay_id: str) -> str:
        """
        Generate a shareable link for a replay.
        
        Args:
            replay_id: Unique identifier for the replay
            
        Returns:
            Shareable URL
        """
        # Placeholder for actual sharing service integration
        base_url = "https://pokertool.example.com/replay"
        share_link = f"{base_url}/{replay_id}"
        logger.info(f"Generated share link", replay_id=replay_id, link=share_link)
        return share_link


class HandReplaySystem:
    """
    Main Hand Replay System.
    
    Coordinates all replay functionality including playback, analysis,
    annotations, and sharing.
    """
    
    def __init__(self):
        """Initialize the hand replay system."""
        self.frames: List[ReplayFrame] = []
        self.current_frame_index: int = 0
        self.animation = ReplayAnimation()
        self.analysis_overlay = AnalysisOverlay()
        self.annotation_manager = AnnotationManager()
        self.share_manager = ShareManager()
        logger.info("HandReplaySystem initialized")
    
    @log_exceptions
    def add_frame(
        self,
        street: Street,
        pot_size: float,
        board_cards: List[str],
        player_stacks: Dict[str, float],
        action: Optional[PlayerAction] = None,
        description: str = ""
    ) -> ReplayFrame:
        """
        Add a new frame to the replay.
        
        Args:
            street: Current street
            pot_size: Size of the pot
            board_cards: Community cards
            player_stacks: Dictionary of player stacks
            action: Optional player action
            description: Optional description
            
        Returns:
            Created ReplayFrame
        """
        frame_id = len(self.frames)
        frame = ReplayFrame(
            frame_id=frame_id,
            street=street,
            pot_size=pot_size,
            board_cards=board_cards.copy(),
            player_stacks=player_stacks.copy(),
            action=action,
            description=description
        )
        self.frames.append(frame)
        logger.debug(f"Added frame {frame_id} to replay", street=street.value)
        return frame
    
    @log_exceptions
    def get_frame(self, frame_id: int) -> Optional[ReplayFrame]:
        """
        Get a specific frame by ID.
        
        Args:
            frame_id: ID of frame to retrieve
            
        Returns:
            ReplayFrame if found, None otherwise
        """
        if 0 <= frame_id < len(self.frames):
            return self.frames[frame_id]
        logger.warning(f"Frame {frame_id} not found")
        return None
    
    @log_exceptions
    def next_frame(self) -> Optional[ReplayFrame]:
        """
        Move to next frame.
        
        Returns:
            Next ReplayFrame if available, None if at end
        """
        if self.current_frame_index < len(self.frames) - 1:
            self.current_frame_index += 1
            frame = self.frames[self.current_frame_index]
            logger.debug(f"Moved to frame {self.current_frame_index}")
            return frame
        return None
    
    @log_exceptions
    def previous_frame(self) -> Optional[ReplayFrame]:
        """
        Move to previous frame.
        
        Returns:
            Previous ReplayFrame if available, None if at beginning
        """
        if self.current_frame_index > 0:
            self.current_frame_index -= 1
            frame = self.frames[self.current_frame_index]
            logger.debug(f"Moved to frame {self.current_frame_index}")
            return frame
        return None
    
    @log_exceptions
    def jump_to_frame(self, frame_id: int) -> Optional[ReplayFrame]:
        """
        Jump to a specific frame.
        
        Args:
            frame_id: ID of frame to jump to
            
        Returns:
            ReplayFrame if found, None otherwise
        """
        if 0 <= frame_id < len(self.frames):
            self.current_frame_index = frame_id
            logger.info(f"Jumped to frame {frame_id}")
            return self.frames[frame_id]
        logger.warning(f"Cannot jump to frame {frame_id}")
        return None
    
    @log_exceptions
    def get_current_frame(self) -> Optional[ReplayFrame]:
        """
        Get the current frame.
        
        Returns:
            Current ReplayFrame if available, None otherwise
        """
        if 0 <= self.current_frame_index < len(self.frames):
            return self.frames[self.current_frame_index]
        return None
    
    @log_exceptions
    def analyze_current_frame(self, hole_cards: List[str]) -> AnalysisData:
        """
        Analyze the current frame.
        
        Args:
            hole_cards: Player's hole cards
            
        Returns:
            AnalysisData for current frame
        """
        current_frame = self.get_current_frame()
        if current_frame is None:
            raise ValueError("No current frame available")
        
        return self.analysis_overlay.analyze_frame(current_frame, hole_cards)
    
    @log_exceptions
    def export_replay(self, filename: str, include_annotations: bool = True) -> Path:
        """
        Export the entire replay.
        
        Args:
            filename: Output filename
            include_annotations: Whether to include annotations
            
        Returns:
            Path to exported file
        """
        annotations = self.annotation_manager.annotations if include_annotations else None
        return self.share_manager.export_to_json(
            self.frames,
            filename,
            annotations=annotations
        )
    
    @log_exceptions
    def import_replay(self, filepath: Path) -> None:
        """
        Import a replay from file.
        
        Args:
            filepath: Path to replay file
        """
        frames, annotations = self.share_manager.import_from_json(filepath)
        self.frames = frames
        self.current_frame_index = 0
        
        if annotations:
            self.annotation_manager.annotations = annotations
        
        logger.info(f"Imported replay with {len(frames)} frames")
    
    def get_frame_count(self) -> int:
        """
        Get total number of frames.
        
        Returns:
            Number of frames in replay
        """
        return len(self.frames)
    
    def reset(self) -> None:
        """Reset the replay system to initial state."""
        self.frames = []
        self.current_frame_index = 0
        self.annotation_manager.annotations = {}
        self.analysis_overlay.analysis_cache = {}
        logger.info("HandReplaySystem reset")


# Example usage
if __name__ == "__main__":
    # Create a replay system
    replay_system = HandReplaySystem()
    
    # Add preflop frame
    action1 = PlayerAction(
        player_name="Player1",
        action_type=ActionType.RAISE,
        amount=10.0,
        position="BTN"
    )
    
    frame1 = replay_system.add_frame(
        street=Street.PREFLOP,
        pot_size=10.0,
        board_cards=[],
        player_stacks={"Player1": 990.0, "Player2": 1000.0},
        action=action1,
        description="Button raises to $10"
    )
    
    # Add flop frame
    frame2 = replay_system.add_frame(
        street=Street.FLOP,
        pot_size=20.0,
        board_cards=["As", "Kh", "7d"],
        player_stacks={"Player1": 990.0, "Player2": 990.0},
        description="Flop dealt"
    )
    
    # Add annotation
    replay_system.annotation_manager.add_annotation(
        frame_id=1,
        text="Strong flop for top pair",
        author="Analyst1",
        position=(100.0, 200.0)
    )
    
    # Analyze frame
    analysis = replay_system.analyze_current_frame(["As", "Qc"])
    print(f"Analysis: {analysis.explanation}")
    
    # Export replay
    export_path = replay_system.export_replay("example_hand")
    print(f"Exported to: {export_path}")
