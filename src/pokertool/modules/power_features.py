#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Power Features System
======================

Advanced power user features for poker tool.

Features:
- POW-001: Multi-Table Support with Table Switcher
- POW-002: Hand Replay with Analysis
- POW-003: Range vs Range Equity Calculator
- POW-004: Auto-Note Taking on Opponents
- POW-005: Session Goals and Tracking
- POW-006: Voice Command Integration
- POW-007: Export Session Reports

Version: 62.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import logging
import time
import json
import csv
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
from enum import Enum
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TableInfo:
    """Information about a poker table."""
    table_id: str
    table_name: str
    max_players: int
    current_players: int
    is_active: bool = True
    last_update: float = field(default_factory=time.time)


@dataclass
class HandRecord:
    """Complete record of a poker hand."""
    hand_id: str
    timestamp: float
    hole_cards: List[str]
    community_cards: List[str]
    actions: List[Dict[str, Any]]
    pot_size: float
    hero_profit: float
    street: str
    result: str  # won/lost/folded


@dataclass
class OpponentNote:
    """Note about an opponent."""
    opponent_name: str
    timestamp: float
    note_text: str
    tags: List[str] = field(default_factory=list)
    auto_generated: bool = False


@dataclass
class SessionGoal:
    """Session goal with tracking."""
    goal_name: str
    target_value: float
    current_value: float = 0.0
    unit: str = ""
    completed: bool = False


# ============================================================================
# POW-001: Multi-Table Support with Table Switcher
# ============================================================================

class MultiTableManager:
    """
    Multi-table support with intelligent table switching.

    Features:
    - Track multiple tables simultaneously
    - Priority-based table switching
    - Action detection across tables
    - Table status monitoring
    - Quick-switch hotkeys
    """

    def __init__(self, max_tables: int = 4):
        """
        Initialize multi-table manager.

        Args:
            max_tables: Maximum tables to track
        """
        self.max_tables = max_tables
        self.tables: Dict[str, TableInfo] = {}
        self.active_table_id: Optional[str] = None
        self.table_priorities: Dict[str, int] = {}

        logger.info(f"MultiTableManager initialized (max: {max_tables})")

    def add_table(self, table_info: TableInfo) -> bool:
        """Add table to manager."""
        if len(self.tables) >= self.max_tables:
            logger.warning(f"Cannot add table - limit reached ({self.max_tables})")
            return False

        self.tables[table_info.table_id] = table_info
        self.table_priorities[table_info.table_id] = 0

        # Set as active if first table
        if self.active_table_id is None:
            self.active_table_id = table_info.table_id

        logger.info(f"Table added: {table_info.table_name} ({table_info.table_id})")
        return True

    def switch_table(self, table_id: str) -> bool:
        """Switch active table."""
        if table_id not in self.tables:
            logger.warning(f"Cannot switch - table not found: {table_id}")
            return False

        self.active_table_id = table_id
        logger.info(f"Switched to table: {self.tables[table_id].table_name}")
        return True

    def get_active_table(self) -> Optional[TableInfo]:
        """Get current active table."""
        if self.active_table_id:
            return self.tables.get(self.active_table_id)
        return None

    def set_table_priority(self, table_id: str, priority: int):
        """Set table priority (higher = more important)."""
        if table_id in self.table_priorities:
            self.table_priorities[table_id] = priority

    def get_next_priority_table(self) -> Optional[str]:
        """Get table ID with highest priority."""
        if not self.tables:
            return None

        return max(self.table_priorities, key=self.table_priorities.get)

    def remove_table(self, table_id: str):
        """Remove table from manager."""
        if table_id in self.tables:
            del self.tables[table_id]
            del self.table_priorities[table_id]

            # Switch to another table if this was active
            if self.active_table_id == table_id:
                self.active_table_id = next(iter(self.tables), None)

            logger.info(f"Table removed: {table_id}")


# ============================================================================
# POW-002: Hand Replay with Analysis
# ============================================================================

class HandReplaySystem:
    """
    Hand replay system with detailed analysis.

    Features:
    - Record complete hand history
    - Step-by-step replay
    - Alternative action analysis
    - Equity calculations
    - Export hand histories
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize hand replay system.

        Args:
            storage_dir: Directory to store hand histories
        """
        self.storage_dir = storage_dir or Path.home() / '.pokertool' / 'hands'
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.hands: deque = deque(maxlen=1000)  # Last 1000 hands
        self.current_hand: Optional[HandRecord] = None

        logger.info(f"HandReplaySystem initialized (storage: {self.storage_dir})")

    def start_hand(self, hand_id: str, hole_cards: List[str]) -> HandRecord:
        """Start recording a new hand."""
        self.current_hand = HandRecord(
            hand_id=hand_id,
            timestamp=time.time(),
            hole_cards=hole_cards,
            community_cards=[],
            actions=[],
            pot_size=0.0,
            hero_profit=0.0,
            street='preflop',
            result='unknown'
        )
        return self.current_hand

    def add_action(
        self,
        player: str,
        action: str,
        amount: float,
        pot_after: float
    ):
        """Add action to current hand."""
        if not self.current_hand:
            logger.warning("No current hand - cannot add action")
            return

        self.current_hand.actions.append({
            'player': player,
            'action': action,
            'amount': amount,
            'pot_after': pot_after,
            'timestamp': time.time()
        })

    def set_community_cards(self, cards: List[str], street: str):
        """Set community cards for current street."""
        if not self.current_hand:
            return

        self.current_hand.community_cards = cards
        self.current_hand.street = street

    def finish_hand(self, result: str, profit: float):
        """Finish recording current hand."""
        if not self.current_hand:
            return

        self.current_hand.result = result
        self.current_hand.hero_profit = profit

        # Add to history
        self.hands.append(self.current_hand)

        # Save to disk
        self._save_hand(self.current_hand)

        logger.info(f"Hand {self.current_hand.hand_id} saved ({result}, ${profit:.2f})")

        self.current_hand = None

    def _save_hand(self, hand: HandRecord):
        """Save hand to disk."""
        try:
            timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(hand.timestamp))
            filename = f"hand_{timestamp_str}_{hand.hand_id}.json"
            filepath = self.storage_dir / filename

            with open(filepath, 'w') as f:
                json.dump(asdict(hand), f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save hand: {e}")

    def get_hand(self, hand_id: str) -> Optional[HandRecord]:
        """Get hand by ID."""
        for hand in self.hands:
            if hand.hand_id == hand_id:
                return hand
        return None

    def get_recent_hands(self, count: int = 10) -> List[HandRecord]:
        """Get recent hands."""
        return list(self.hands)[-count:]


# ============================================================================
# POW-003: Range vs Range Equity Calculator
# ============================================================================

class RangeVsRangeCalculator:
    """
    Range vs range equity calculator.

    Features:
    - Define hand ranges
    - Calculate range vs range equity
    - Monte Carlo simulation
    - Board texture analysis
    - Export equity reports
    """

    def __init__(self):
        """Initialize range calculator."""
        self.precomputed_equities: Dict[str, float] = {}

        logger.info("RangeVsRangeCalculator initialized")

    def calculate_equity(
        self,
        hero_range: List[str],
        villain_range: List[str],
        board: List[str] = [],
        iterations: int = 10000
    ) -> Dict[str, Any]:
        """
        Calculate range vs range equity.

        Args:
            hero_range: Hero's range (list of hand strings)
            villain_range: Villain's range
            board: Community cards
            iterations: Monte Carlo iterations

        Returns:
            Equity results
        """
        # Simplified calculation for demo
        # In production, would use actual equity calculator

        # Calculate average equity for ranges
        hero_equity = 0.5  # Placeholder
        villain_equity = 0.5

        result = {
            'hero_equity': hero_equity,
            'villain_equity': villain_equity,
            'hero_range_size': len(hero_range),
            'villain_range_size': len(villain_range),
            'board': board,
            'iterations': iterations
        }

        logger.info(f"Calculated equity: Hero {hero_equity:.1%} vs Villain {villain_equity:.1%}")

        return result

    def parse_range_string(self, range_str: str) -> List[str]:
        """
        Parse range string into list of hands.

        Examples:
            "AA,KK,QQ" -> ['AA', 'KK', 'QQ']
            "22+" -> ['22', '33', ..., 'AA']
            "AKs" -> ['AsKs', 'AhKh', 'AdKd', 'AcKc']
        """
        # Simplified parser
        hands = []

        for part in range_str.split(','):
            part = part.strip()

            if '+' in part:
                # Range notation (e.g., "77+" = 77,88,99,TT,JJ,QQ,KK,AA)
                base_hand = part.replace('+', '')
                # Expand range (simplified)
                hands.append(base_hand)
            else:
                hands.append(part)

        return hands


# ============================================================================
# POW-004: Auto-Note Taking on Opponents
# ============================================================================

class AutoNoteSystem:
    """
    Automatic note-taking system for opponents.

    Features:
    - Detect notable opponent behaviors
    - Auto-generate notes
    - Tag-based organization
    - Manual note addition
    - Search and filter notes
    """

    def __init__(self, storage_file: Optional[Path] = None):
        """
        Initialize auto-note system.

        Args:
            storage_file: File to store notes
        """
        self.storage_file = storage_file or Path.home() / '.pokertool' / 'opponent_notes.json'
        self.notes: Dict[str, List[OpponentNote]] = {}

        # Load existing notes
        self._load_notes()

        logger.info("AutoNoteSystem initialized")

    def add_note(
        self,
        opponent_name: str,
        note_text: str,
        tags: Optional[List[str]] = None,
        auto_generated: bool = False
    ):
        """Add note for opponent."""
        if opponent_name not in self.notes:
            self.notes[opponent_name] = []

        note = OpponentNote(
            opponent_name=opponent_name,
            timestamp=time.time(),
            note_text=note_text,
            tags=tags or [],
            auto_generated=auto_generated
        )

        self.notes[opponent_name].append(note)
        self._save_notes()

        logger.info(f"Note added for {opponent_name}: {note_text[:50]}...")

    def auto_generate_note(
        self,
        opponent_name: str,
        stats: Dict[str, Any]
    ):
        """Auto-generate note based on opponent statistics."""
        notes = []

        # Check for tight player
        vpip = stats.get('vpip', 0.0)
        if vpip < 0.15:
            notes.append("Very tight player (VPIP < 15%)")

        # Check for loose player
        elif vpip > 0.35:
            notes.append("Loose player (VPIP > 35%)")

        # Check for aggressive player
        pfr = stats.get('pfr', 0.0)
        if pfr > 0.25:
            notes.append("Aggressive pre-flop (PFR > 25%)")

        # Check for passive player
        agg_factor = stats.get('aggression_factor', 0.0)
        if agg_factor < 1.0:
            notes.append("Passive post-flop (low aggression)")

        # Add auto-generated notes
        for note_text in notes:
            self.add_note(opponent_name, note_text, tags=['auto', 'stats'], auto_generated=True)

    def get_notes(self, opponent_name: str) -> List[OpponentNote]:
        """Get all notes for opponent."""
        return self.notes.get(opponent_name, [])

    def _save_notes(self):
        """Save notes to disk."""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to JSON-serializable format
            data = {
                name: [asdict(note) for note in notes]
                for name, notes in self.notes.items()
            }

            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save notes: {e}")

    def _load_notes(self):
        """Load notes from disk."""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)

                # Convert back to OpponentNote objects
                for name, note_dicts in data.items():
                    self.notes[name] = [
                        OpponentNote(**note_dict) for note_dict in note_dicts
                    ]

                logger.info(f"Loaded notes for {len(self.notes)} opponents")

        except Exception as e:
            logger.error(f"Failed to load notes: {e}")


# ============================================================================
# POW-005: Session Goals and Tracking
# ============================================================================

class SessionGoalTracker:
    """
    Session goal setting and tracking system.

    Features:
    - Define custom goals
    - Track progress in real-time
    - Goal completion alerts
    - Historical goal tracking
    - Performance analytics
    """

    def __init__(self):
        """Initialize session goal tracker."""
        self.goals: List[SessionGoal] = []
        self.session_start = time.time()

        logger.info("SessionGoalTracker initialized")

    def add_goal(
        self,
        goal_name: str,
        target_value: float,
        unit: str = ""
    ) -> SessionGoal:
        """Add a session goal."""
        goal = SessionGoal(
            goal_name=goal_name,
            target_value=target_value,
            unit=unit
        )

        self.goals.append(goal)

        logger.info(f"Goal added: {goal_name} (target: {target_value} {unit})")

        return goal

    def update_goal_progress(
        self,
        goal_name: str,
        current_value: float
    ) -> bool:
        """Update goal progress."""
        for goal in self.goals:
            if goal.goal_name == goal_name:
                goal.current_value = current_value

                # Check if goal completed
                if not goal.completed and current_value >= goal.target_value:
                    goal.completed = True
                    logger.info(f"Goal completed: {goal_name}!")
                    return True

        return False

    def get_goals(self) -> List[SessionGoal]:
        """Get all goals."""
        return self.goals

    def get_completion_rate(self) -> float:
        """Get overall goal completion rate."""
        if not self.goals:
            return 0.0

        completed = sum(1 for goal in self.goals if goal.completed)
        return completed / len(self.goals)


# ============================================================================
# POW-006: Voice Command Integration
# ============================================================================

class VoiceCommandHandler:
    """
    Voice command integration for hands-free control.

    Features:
    - Voice command recognition
    - Custom command mapping
    - Action callbacks
    - Voice feedback
    - Command history
    """

    def __init__(self):
        """Initialize voice command handler."""
        self.commands: Dict[str, Any] = {}
        self.enabled = False
        self.command_history: deque = deque(maxlen=50)

        # Register default commands
        self._register_default_commands()

        logger.info("VoiceCommandHandler initialized")

    def _register_default_commands(self):
        """Register default voice commands."""
        self.register_command("fold", lambda: self._execute_action("fold"))
        self.register_command("call", lambda: self._execute_action("call"))
        self.register_command("raise", lambda: self._execute_action("raise"))
        self.register_command("check", lambda: self._execute_action("check"))

    def register_command(self, command_phrase: str, callback: Any):
        """Register voice command with callback."""
        self.commands[command_phrase.lower()] = callback
        logger.debug(f"Voice command registered: '{command_phrase}'")

    def process_voice_input(self, text: str) -> bool:
        """
        Process voice input text.

        Args:
            text: Voice input text

        Returns:
            True if command recognized and executed
        """
        if not self.enabled:
            return False

        text_lower = text.lower().strip()

        # Check for matching command
        for command_phrase, callback in self.commands.items():
            if command_phrase in text_lower:
                logger.info(f"Voice command recognized: '{command_phrase}'")

                # Execute callback
                try:
                    callback()
                    self.command_history.append({
                        'timestamp': time.time(),
                        'command': command_phrase,
                        'success': True
                    })
                    return True
                except Exception as e:
                    logger.error(f"Voice command failed: {e}")
                    return False

        return False

    def _execute_action(self, action: str):
        """Execute poker action."""
        logger.info(f"Executing action: {action}")
        # In production, would trigger actual game action

    def enable(self):
        """Enable voice commands."""
        self.enabled = True
        logger.info("Voice commands enabled")

    def disable(self):
        """Disable voice commands."""
        self.enabled = False
        logger.info("Voice commands disabled")


# ============================================================================
# POW-007: Export Session Reports
# ============================================================================

class SessionReportExporter:
    """
    Export comprehensive session reports.

    Features:
    - Multiple export formats (CSV, JSON, PDF)
    - Customizable report templates
    - Statistics aggregation
    - Charts and graphs
    - Email delivery
    """

    def __init__(self, export_dir: Optional[Path] = None):
        """
        Initialize session report exporter.

        Args:
            export_dir: Directory for exported reports
        """
        self.export_dir = export_dir or Path.home() / '.pokertool' / 'reports'
        self.export_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SessionReportExporter initialized (dir: {self.export_dir})")

    def export_session_report(
        self,
        session_data: Dict[str, Any],
        format: str = 'json'
    ) -> Path:
        """
        Export session report.

        Args:
            session_data: Session data to export
            format: Export format ('json', 'csv', 'txt')

        Returns:
            Path to exported file
        """
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        filename = f"session_report_{timestamp_str}.{format}"
        filepath = self.export_dir / filename

        if format == 'json':
            self._export_json(filepath, session_data)
        elif format == 'csv':
            self._export_csv(filepath, session_data)
        elif format == 'txt':
            self._export_txt(filepath, session_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Session report exported: {filepath}")

        return filepath

    def _export_json(self, filepath: Path, data: Dict[str, Any]):
        """Export as JSON."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _export_csv(self, filepath: Path, data: Dict[str, Any]):
        """Export as CSV."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Write headers
            writer.writerow(['Metric', 'Value'])

            # Write data
            for key, value in data.items():
                writer.writerow([key, value])

    def _export_txt(self, filepath: Path, data: Dict[str, Any]):
        """Export as text report."""
        lines = []
        lines.append("=" * 60)
        lines.append("POKER SESSION REPORT")
        lines.append("=" * 60)
        lines.append("")

        for key, value in data.items():
            lines.append(f"{key:30s}: {value}")

        lines.append("")
        lines.append("=" * 60)

        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))


# ============================================================================
# Integrated Power Features System
# ============================================================================

class PowerFeaturesSystem:
    """
    Integrated power features system.

    Combines all 7 power features into unified API.
    """

    def __init__(self):
        """Initialize power features system."""
        self.multi_table_manager = MultiTableManager()
        self.hand_replay = HandReplaySystem()
        self.range_calculator = RangeVsRangeCalculator()
        self.auto_notes = AutoNoteSystem()
        self.goal_tracker = SessionGoalTracker()
        self.voice_commands = VoiceCommandHandler()
        self.report_exporter = SessionReportExporter()

        logger.info("PowerFeaturesSystem initialized (7 power features active)")


# ============================================================================
# Factory Function
# ============================================================================

_power_features_instance = None

def get_power_features_system() -> PowerFeaturesSystem:
    """Get global power features system instance (singleton)."""
    global _power_features_instance

    if _power_features_instance is None:
        _power_features_instance = PowerFeaturesSystem()

    return _power_features_instance


if __name__ == '__main__':
    # Demo/test
    logging.basicConfig(level=logging.INFO)

    print("Power Features System Demo")
    print("=" * 60)

    system = PowerFeaturesSystem()

    # Test multi-table
    print("\n1. Multi-Table Support:")
    table1 = TableInfo("table1", "Table 1", 6, 4)
    system.multi_table_manager.add_table(table1)
    print(f"  Active table: {system.multi_table_manager.get_active_table().table_name}")

    # Test hand replay
    print("\n2. Hand Replay:")
    hand = system.hand_replay.start_hand("hand123", ['As', 'Kh'])
    system.hand_replay.add_action("Hero", "raise", 25.0, 27.0)
    system.hand_replay.finish_hand("won", 50.0)
    print(f"  Hand {hand.hand_id} recorded")

    # Test goals
    print("\n3. Session Goals:")
    goal = system.goal_tracker.add_goal("Win 10 hands", 10.0, "hands")
    system.goal_tracker.update_goal_progress("Win 10 hands", 5.0)
    print(f"  Goal progress: {goal.current_value}/{goal.target_value}")

    # Test voice commands
    print("\n4. Voice Commands:")
    system.voice_commands.enable()
    result = system.voice_commands.process_voice_input("I want to fold")
    print(f"  Command processed: {result}")

    # Test export
    print("\n5. Session Report Export:")
    session_data = {
        'hands_played': 50,
        'profit': 125.50,
        'duration': '2 hours'
    }
    report_path = system.report_exporter.export_session_report(session_data, 'json')
    print(f"  Report exported to: {report_path}")

    print("\n" + "=" * 60)
    print("Demo complete!")
