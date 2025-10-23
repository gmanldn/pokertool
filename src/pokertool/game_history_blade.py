#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game History Blade - Live Table Data Logger
============================================

Real-time, colorful text log showing all captured poker table data.

Features:
- Live display of table state as it's captured
- Color-coded fields for easy reading
- Clear hand boundaries and hand numbering
- All data fields displayed with timestamps
- Scroll history of all hands
- Auto-scrolling with manual override
- Compact and detailed view modes

Version: 1.0.0
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime
from pathlib import Path
import json

import logging
logger = logging.getLogger(__name__)


# ============================================================================
# Color Scheme
# ============================================================================

class GameHistoryColors:
    """Color scheme for game history display."""

    # Text colors
    HAND_HEADER = "#FF6B35"      # Orange - Hand boundaries
    TIMESTAMP = "#6C757D"         # Gray - Timestamps
    FIELD_NAME = "#4ECDC4"        # Cyan - Field names
    FIELD_VALUE = "#FFFFFF"       # White - Normal values
    HERO_CARDS = "#FFD700"        # Gold - Hero's cards
    BOARD_CARDS = "#98D8C8"       # Light green - Board cards
    POT = "#50C878"               # Emerald - Pot size
    SEAT_ACTIVE = "#7FFF00"       # Chartreuse - Active players
    SEAT_INACTIVE = "#808080"     # Gray - Inactive seats
    DEALER = "#FFD700"            # Gold - Dealer
    BLIND = "#FFA500"             # Orange - Blinds
    TURN = "#00FF00"              # Bright green - Active turn
    ERROR = "#FF4444"             # Red - Errors
    SUCCESS = "#44FF44"           # Green - Success
    WARNING = "#FFAA00"           # Amber - Warnings

    # Background colors
    BG_PRIMARY = "#1E1E1E"        # Dark - Main background
    BG_SECONDARY = "#2D2D2D"      # Darker - Alternate rows
    BG_HAND_HEADER = "#3D2817"    # Brown - Hand header background


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class HandRecord:
    """Record of a single hand."""
    hand_number: int
    start_time: float
    end_time: Optional[float] = None
    table_states: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.table_states is None:
            self.table_states = []


# ============================================================================
# Game History Blade Window
# ============================================================================

class GameHistoryBlade:
    """
    Live game history log window showing all captured table data.

    Features:
    - Real-time updates
    - Color-coded display
    - Hand boundaries
    - All data fields
    - Scrollable history
    """

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        position: tuple = None,
        width: int = 800,
        height: int = 600,
        auto_scroll: bool = True
    ):
        """
        Initialize game history blade.

        Args:
            parent: Parent window (None for standalone)
            position: (x, y) screen position
            width: Window width
            height: Window height
            auto_scroll: Auto-scroll to latest
        """
        # Create window
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()

        self.root.title("Game History - Live Table Data")
        self.root.geometry(f"{width}x{height}")

        # Always on top
        self.root.attributes('-topmost', True)

        # macOS: utility window
        try:
            self.root.attributes('-type', 'utility')
        except:
            pass

        # State
        self.auto_scroll = auto_scroll
        self.current_hand: Optional[HandRecord] = None
        self.hand_history: List[HandRecord] = []
        self.hand_counter = 0
        self.last_table_state_hash = None
        self.paused = False

        # Settings
        self.settings_file = Path.home() / ".pokertool" / "game_history_settings.json"
        self.settings = self._load_settings()

        # Create UI
        self._create_ui()

        # Position window
        if position:
            self.root.geometry(f"+{position[0]}+{position[1]}")
        else:
            self._position_default()

        # Initial message
        self._log_system_message("Game History initialized. Waiting for table data...")

        logger.info("GameHistoryBlade initialized")

    def _create_ui(self):
        """Create the UI layout."""
        # Main container
        main_frame = tk.Frame(self.root, bg=GameHistoryColors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        self._create_toolbar(main_frame)

        # Text display area (with scrollbar)
        self._create_text_area(main_frame)

        # Status bar
        self._create_status_bar(main_frame)

    def _create_toolbar(self, parent):
        """Create toolbar with controls."""
        toolbar = tk.Frame(parent, bg=GameHistoryColors.BG_SECONDARY, height=40)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        toolbar.pack_propagate(False)

        # Title
        title = tk.Label(
            toolbar,
            text="📜 Game History",
            font=("Arial", 12, "bold"),
            fg=GameHistoryColors.FIELD_NAME,
            bg=GameHistoryColors.BG_SECONDARY
        )
        title.pack(side=tk.LEFT, padx=10)

        # Pause button
        self.pause_btn = tk.Button(
            toolbar,
            text="⏸ Pause",
            command=self.toggle_pause,
            bg="#444444",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=10,
            cursor="hand2"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        # Clear button
        clear_btn = tk.Button(
            toolbar,
            text="🗑 Clear",
            command=self.clear_history,
            bg="#444444",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=10,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        # Auto-scroll toggle
        self.auto_scroll_var = tk.BooleanVar(value=self.auto_scroll)
        auto_scroll_check = tk.Checkbutton(
            toolbar,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll,
            bg=GameHistoryColors.BG_SECONDARY,
            fg=GameHistoryColors.FIELD_VALUE,
            selectcolor="#444444"
        )
        auto_scroll_check.pack(side=tk.LEFT, padx=10)

        # Export button
        export_btn = tk.Button(
            toolbar,
            text="💾 Export",
            command=self.export_history,
            bg="#444444",
            fg="#FFFFFF",
            relief=tk.FLAT,
            padx=10,
            cursor="hand2"
        )
        export_btn.pack(side=tk.RIGHT, padx=10)

    def _create_text_area(self, parent):
        """Create main text display area."""
        # Frame for text widget
        text_frame = tk.Frame(parent, bg=GameHistoryColors.BG_PRIMARY)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrolled text widget with custom colors
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            bg=GameHistoryColors.BG_PRIMARY,
            fg=GameHistoryColors.FIELD_VALUE,
            insertbackground=GameHistoryColors.FIELD_VALUE,
            font=("Courier New", 10),
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colors
        self._configure_text_tags()

        # Disable editing
        self.text_widget.config(state=tk.DISABLED)

    def _configure_text_tags(self):
        """Configure text tags for colored output."""
        self.text_widget.tag_config("hand_header",
                                    foreground=GameHistoryColors.HAND_HEADER,
                                    font=("Courier New", 11, "bold"),
                                    background=GameHistoryColors.BG_HAND_HEADER)
        self.text_widget.tag_config("timestamp",
                                    foreground=GameHistoryColors.TIMESTAMP,
                                    font=("Courier New", 9))
        self.text_widget.tag_config("field_name",
                                    foreground=GameHistoryColors.FIELD_NAME,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("field_value",
                                    foreground=GameHistoryColors.FIELD_VALUE)
        self.text_widget.tag_config("hero_cards",
                                    foreground=GameHistoryColors.HERO_CARDS,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("board_cards",
                                    foreground=GameHistoryColors.BOARD_CARDS,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("pot",
                                    foreground=GameHistoryColors.POT,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("seat_active",
                                    foreground=GameHistoryColors.SEAT_ACTIVE)
        self.text_widget.tag_config("seat_inactive",
                                    foreground=GameHistoryColors.SEAT_INACTIVE)
        self.text_widget.tag_config("dealer",
                                    foreground=GameHistoryColors.DEALER,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("blind",
                                    foreground=GameHistoryColors.BLIND,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("turn",
                                    foreground=GameHistoryColors.TURN,
                                    font=("Courier New", 10, "bold"))
        self.text_widget.tag_config("error",
                                    foreground=GameHistoryColors.ERROR)
        self.text_widget.tag_config("success",
                                    foreground=GameHistoryColors.SUCCESS)
        self.text_widget.tag_config("warning",
                                    foreground=GameHistoryColors.WARNING)

    def _create_status_bar(self, parent):
        """Create status bar."""
        status_bar = tk.Frame(parent, bg=GameHistoryColors.BG_SECONDARY, height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            font=("Arial", 9),
            fg=GameHistoryColors.FIELD_VALUE,
            bg=GameHistoryColors.BG_SECONDARY,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.hand_counter_label = tk.Label(
            status_bar,
            text="Hands: 0",
            font=("Arial", 9),
            fg=GameHistoryColors.FIELD_NAME,
            bg=GameHistoryColors.BG_SECONDARY
        )
        self.hand_counter_label.pack(side=tk.RIGHT, padx=10)

    def _position_default(self):
        """Position window at default location."""
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Right side of screen
        x = screen_width - window_width - 20
        y = 50

        self.root.geometry(f"+{x}+{y}")

    # ========================================================================
    # Public API - Update Methods
    # ========================================================================

    def update_table_state(self, table_state: Dict[str, Any]):
        """
        Update with new table state.

        Args:
            table_state: Dictionary containing table state data
        """
        if self.paused:
            return

        # Check if this is a new hand (detect hand boundaries)
        is_new_hand = self._is_new_hand(table_state)

        if is_new_hand:
            self._start_new_hand(table_state)
        else:
            self._update_current_hand(table_state)

        # Log the table state
        self._log_table_state(table_state, is_new_hand)

        # Update status
        self._update_status()

    def _is_new_hand(self, table_state: Dict[str, Any]) -> bool:
        """Detect if this is a new hand."""
        # If no current hand, it's definitely new
        if self.current_hand is None:
            return True

        # Check for indicators of new hand:
        # 1. Board cards reset (all community cards gone)
        # 2. Pot size reset to blinds
        # 3. Hero cards changed
        # 4. Stage changed to preflop

        board_cards = table_state.get('board_cards', [])
        hero_cards = table_state.get('hero_cards', [])
        pot_size = table_state.get('pot_size', 0)
        stage = table_state.get('stage', '')

        # If we have previous state
        if self.current_hand.table_states:
            prev_state = self.current_hand.table_states[-1]
            prev_board = prev_state.get('board_cards', [])
            prev_hero = prev_state.get('hero_cards', [])

            # Board cards reset
            if len(prev_board) > 0 and len(board_cards) == 0:
                return True

            # Hero cards changed
            if prev_hero != hero_cards and len(hero_cards) > 0:
                return True

            # Stage reset to preflop
            if stage.lower() == 'preflop' and prev_state.get('stage', '').lower() != 'preflop':
                return True

        return False

    def _start_new_hand(self, table_state: Dict[str, Any]):
        """Start recording a new hand."""
        # Close previous hand if exists
        if self.current_hand:
            self.current_hand.end_time = time.time()
            self.hand_history.append(self.current_hand)

        # Start new hand
        self.hand_counter += 1
        self.current_hand = HandRecord(
            hand_number=self.hand_counter,
            start_time=time.time()
        )
        self.current_hand.table_states.append(table_state)

    def _update_current_hand(self, table_state: Dict[str, Any]):
        """Update current hand with new state."""
        if self.current_hand:
            self.current_hand.table_states.append(table_state)

    def _log_table_state(self, table_state: Dict[str, Any], is_new_hand: bool):
        """Log table state to text widget."""
        self.text_widget.config(state=tk.NORMAL)

        # New hand header
        if is_new_hand:
            self._write_hand_header()

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._write_line(f"[{timestamp}] ", "timestamp", newline=False)

        # Detection info
        confidence = table_state.get('detection_confidence', 0)
        if confidence > 0:
            self._write_line(f"Confidence: {confidence:.1%} | ", "field_name", newline=False)

        method = table_state.get('extraction_method', 'unknown')
        self._write_line(f"Method: {method}\n", "field_value")

        # Hero cards
        hero_cards = table_state.get('hero_cards', [])
        if hero_cards:
            self._write_line("  Hero Cards: ", "field_name", newline=False)
            self._write_line(f"{', '.join(hero_cards)}\n", "hero_cards")

        # Board cards
        board_cards = table_state.get('board_cards', [])
        if board_cards:
            self._write_line("  Board: ", "field_name", newline=False)
            self._write_line(f"{', '.join(board_cards)}\n", "board_cards")

        # Pot
        pot_size = table_state.get('pot_size', 0)
        if pot_size > 0:
            self._write_line("  Pot: ", "field_name", newline=False)
            self._write_line(f"${pot_size:.2f}\n", "pot")

        # Stage
        stage = table_state.get('stage', 'unknown')
        self._write_line(f"  Stage: ", "field_name", newline=False)
        self._write_line(f"{stage.upper()}\n", "field_value")

        # Betting info
        to_call = table_state.get('to_call', 0)
        current_bet = table_state.get('current_bet', 0)
        if to_call > 0 or current_bet > 0:
            self._write_line("  Betting: ", "field_name", newline=False)
            self._write_line(f"To Call: ${to_call:.2f} | Current Bet: ${current_bet:.2f}\n", "field_value")

        # Blinds
        sb = table_state.get('small_blind', 0)
        bb = table_state.get('big_blind', 0)
        if sb > 0 or bb > 0:
            self._write_line("  Blinds: ", "blind", newline=False)
            self._write_line(f"${sb:.2f}/${bb:.2f}\n", "field_value")

        # Seats
        seats = table_state.get('seats', [])
        if seats:
            self._write_line("  Seats:\n", "field_name")
            for seat in seats:
                self._log_seat_info(seat, table_state)

        # Active turn
        active_turn_seat = table_state.get('active_turn_seat')
        if active_turn_seat is not None:
            self._write_line(f"  >>> ACTIVE TURN: Seat {active_turn_seat} <<<\n", "turn")

        # Separator
        self._write_line("  " + "─" * 70 + "\n", "field_name")

        self.text_widget.config(state=tk.DISABLED)

        # Auto-scroll
        if self.auto_scroll_var.get():
            self.text_widget.see(tk.END)

    def _write_hand_header(self):
        """Write hand boundary header."""
        header = f"\n{'═' * 80}\n"
        header += f"    HAND #{self.hand_counter} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"{'═' * 80}\n\n"
        self._write_line(header, "hand_header")

    def _log_seat_info(self, seat: Dict[str, Any], table_state: Dict[str, Any]):
        """Log seat information."""
        seat_num = seat.get('seat_number', '?')
        is_active = seat.get('is_active', False)
        player_name = seat.get('player_name', 'Empty')
        stack = seat.get('stack_size', 0)

        tag = "seat_active" if is_active else "seat_inactive"

        # Seat number and name
        line = f"    Seat {seat_num}: {player_name}"

        # Stack
        if stack > 0:
            line += f" (${stack:.2f})"

        # Special roles
        roles = []
        if seat.get('is_dealer'):
            roles.append("DEALER")
        if seat.get('is_small_blind'):
            roles.append("SB")
        if seat.get('is_big_blind'):
            roles.append("BB")
        if seat.get('is_hero'):
            roles.append("HERO")
        if seat.get('is_active_turn'):
            roles.append(">>> TURN <<<")

        if roles:
            line += f" [{', '.join(roles)}]"

        # Current bet
        current_bet = seat.get('current_bet', 0)
        if current_bet > 0:
            line += f" - Bet: ${current_bet:.2f}"

        # Status
        status = seat.get('status_text', '')
        if status:
            line += f" - {status}"

        line += "\n"

        # Write with appropriate tag
        if seat.get('is_active_turn'):
            self._write_line(line, "turn")
        elif seat.get('is_dealer'):
            self._write_line(line, "dealer")
        elif seat.get('is_small_blind') or seat.get('is_big_blind'):
            self._write_line(line, "blind")
        else:
            self._write_line(line, tag)

    def _write_line(self, text: str, tag: str = "field_value", newline: bool = True):
        """Write text with specified tag."""
        if newline and not text.endswith('\n'):
            text += '\n'
        self.text_widget.insert(tk.END, text, tag)

    def _log_system_message(self, message: str, level: str = "info"):
        """Log system message."""
        self.text_widget.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M:%S")
        tag = {"info": "success", "warning": "warning", "error": "error"}.get(level, "field_value")

        self._write_line(f"[{timestamp}] ", "timestamp", newline=False)
        self._write_line(f"{message}\n", tag)

        self.text_widget.config(state=tk.DISABLED)

        if self.auto_scroll_var.get():
            self.text_widget.see(tk.END)

    def _update_status(self):
        """Update status bar."""
        self.status_label.config(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        self.hand_counter_label.config(text=f"Hands: {self.hand_counter}")

    # ========================================================================
    # Control Methods
    # ========================================================================

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.config(text="▶ Resume")
            self._log_system_message("Game history paused", "warning")
        else:
            self.pause_btn.config(text="⏸ Pause")
            self._log_system_message("Game history resumed", "success")

    def clear_history(self):
        """Clear all history."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.config(state=tk.DISABLED)

        self.hand_history.clear()
        self.current_hand = None
        self.hand_counter = 0
        self.last_table_state_hash = None

        self._log_system_message("History cleared", "success")
        self._update_status()

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll."""
        self.auto_scroll = self.auto_scroll_var.get()
        self.settings['auto_scroll'] = self.auto_scroll
        self._save_settings()

    def export_history(self):
        """Export history to file."""
        try:
            export_file = Path.home() / ".pokertool" / "game_history_export.json"
            export_file.parent.mkdir(parents=True, exist_ok=True)

            export_data = {
                'export_time': datetime.now().isoformat(),
                'hand_count': self.hand_counter,
                'hands': [
                    {
                        'hand_number': h.hand_number,
                        'start_time': h.start_time,
                        'end_time': h.end_time,
                        'states_count': len(h.table_states)
                    }
                    for h in self.hand_history
                ]
            }

            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            self._log_system_message(f"History exported to {export_file}", "success")

        except Exception as e:
            self._log_system_message(f"Export failed: {e}", "error")
            logger.error(f"Export failed: {e}")

    # ========================================================================
    # Settings
    # ========================================================================

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")

        return {
            'auto_scroll': True,
            'position': None
        }

    def _save_settings(self):
        """Save settings to file."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save settings: {e}")

    # ========================================================================
    # Window Control
    # ========================================================================

    def show(self):
        """Show the window."""
        self.root.deiconify()

    def hide(self):
        """Hide the window."""
        self.root.withdraw()

    def destroy(self):
        """Destroy the window."""
        self._save_settings()
        self.root.destroy()

    def mainloop(self):
        """Start main event loop (for standalone mode)."""
        self.root.mainloop()


# ============================================================================
# Demo / Testing
# ============================================================================

def demo():
    """Demo the game history blade."""
    import random

    blade = GameHistoryBlade()

    def simulate_table_updates():
        """Simulate table state updates."""
        # Simulate a few hands
        for hand_num in range(3):
            # New hand - preflop
            state = {
                'detection_confidence': random.uniform(0.9, 1.0),
                'extraction_method': 'cdp',
                'hero_cards': ['As', 'Kh'],
                'board_cards': [],
                'pot_size': 3.0,
                'stage': 'preflop',
                'to_call': 2.0,
                'current_bet': 2.0,
                'small_blind': 1.0,
                'big_blind': 2.0,
                'active_turn_seat': 0,
                'seats': [
                    {'seat_number': 0, 'is_active': True, 'player_name': 'Hero', 'stack_size': 100.0,
                     'is_hero': True, 'is_dealer': False, 'is_small_blind': False, 'is_big_blind': False,
                     'is_active_turn': True, 'current_bet': 0},
                    {'seat_number': 1, 'is_active': True, 'player_name': 'Player1', 'stack_size': 95.0,
                     'is_dealer': False, 'is_small_blind': True, 'is_big_blind': False, 'current_bet': 1.0},
                    {'seat_number': 2, 'is_active': True, 'player_name': 'Player2', 'stack_size': 90.0,
                     'is_dealer': True, 'is_small_blind': False, 'is_big_blind': True, 'current_bet': 2.0},
                ]
            }
            blade.update_table_state(state)
            blade.root.update()
            blade.root.after(1000)

            # Flop
            state['stage'] = 'flop'
            state['board_cards'] = ['Qh', 'Jd', '9s']
            state['pot_size'] = 10.0
            state['active_turn_seat'] = 1
            blade.update_table_state(state)
            blade.root.update()
            blade.root.after(1000)

            # Turn
            state['stage'] = 'turn'
            state['board_cards'] = ['Qh', 'Jd', '9s', '2c']
            state['pot_size'] = 25.0
            blade.update_table_state(state)
            blade.root.update()
            blade.root.after(1000)

    # Start simulation after 1 second
    blade.root.after(1000, simulate_table_updates)

    blade.mainloop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Starting Game History Blade Demo...")
    demo()
