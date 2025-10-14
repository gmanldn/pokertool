#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compact Live Advice Window
===========================

Ultra-compact, always-on-top floating window for real-time poker advice.

Displays:
- Recommended action (FOLD/CALL/RAISE)
- Live win probability (updated every 2 seconds)
- Confidence level with visual meter
- Concise one-line reasoning

Design:
- 300x180px compact footprint
- Always-on-top with transparency
- Smooth animations and transitions
- Minimal, elegant interface

Version: 61.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, font as tkfont
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================

class ActionType(Enum):
    """Poker action types."""
    FOLD = "FOLD"
    CALL = "CALL"
    RAISE = "RAISE"
    CHECK = "CHECK"
    ALL_IN = "ALL-IN"
    UNKNOWN = "..."


class ConfidenceLevel(Enum):
    """Confidence level classifications."""
    VERY_HIGH = (90, "#00C853")  # 90%+, Green
    HIGH = (75, "#64DD17")       # 75-90%, Light Green
    MEDIUM = (50, "#FFD600")     # 50-75%, Yellow
    LOW = (25, "#FF6D00")        # 25-50%, Orange
    VERY_LOW = (0, "#DD2C00")    # 0-25%, Red

    def __init__(self, threshold: int, color: str):
        self.threshold = threshold
        self.color = color

    @classmethod
    def from_confidence(cls, confidence: float) -> ConfidenceLevel:
        """Get confidence level from numeric confidence (0-1)."""
        conf_pct = confidence * 100
        if conf_pct >= 90:
            return cls.VERY_HIGH
        elif conf_pct >= 75:
            return cls.HIGH
        elif conf_pct >= 50:
            return cls.MEDIUM
        elif conf_pct >= 25:
            return cls.LOW
        else:
            return cls.VERY_LOW


@dataclass
class LiveAdviceData:
    """Data structure for compact live advice."""
    # Core recommendation
    action: ActionType
    action_amount: Optional[float] = None

    # Live metrics
    win_probability: float = 0.0  # 0.0-1.0
    confidence: float = 0.0  # 0.0-1.0

    # Explanation
    reasoning: str = "Waiting for data..."

    # Metadata
    timestamp: float = field(default_factory=time.time)
    is_calculating: bool = False
    has_data: bool = False

    # Alternative actions
    alternative_actions: Optional[list] = None

    # Technical details
    ev: Optional[float] = None
    pot_odds: Optional[float] = None


# ============================================================================
# Semantic Colors
# ============================================================================

class CompactColors:
    """Color scheme for compact window."""
    # Backgrounds
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F5F5F5"
    BG_DARK = "#263238"

    # Action colors
    ACTION_RAISE = "#00C853"  # Green
    ACTION_CALL = "#2979FF"   # Blue
    ACTION_FOLD = "#DD2C00"   # Red
    ACTION_CHECK = "#757575"  # Gray
    ACTION_UNKNOWN = "#9E9E9E"

    # Win probability gradient
    WIN_LOW = "#DD2C00"      # Red (0%)
    WIN_MID = "#FFD600"      # Yellow (50%)
    WIN_HIGH = "#00C853"     # Green (100%)

    # Confidence colors (from ConfidenceLevel)
    CONF_VERY_HIGH = "#00C853"
    CONF_HIGH = "#64DD17"
    CONF_MEDIUM = "#FFD600"
    CONF_LOW = "#FF6D00"
    CONF_VERY_LOW = "#DD2C00"

    # Text
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_ON_DARK = "#FFFFFF"

    # UI Elements
    BORDER = "#E0E0E0"
    SHADOW = "#00000030"
    PROGRESS_BG = "#E0E0E0"


# ============================================================================
# Animated Widgets
# ============================================================================

class AnimatedProgressBar(tk.Canvas):
    """Progress bar with smooth fill animation."""

    def __init__(self, parent, width=280, height=20, **kwargs):
        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.value = 0.0
        self.target_value = 0.0
        self.color = CompactColors.CONF_MEDIUM

        # Create background
        self.create_rectangle(
            0, 0, width, height,
            fill=CompactColors.PROGRESS_BG,
            outline=CompactColors.BORDER,
            width=1,
            tags="bg"
        )

        # Create fill bar
        self.bar = self.create_rectangle(
            0, 0, 0, height,
            fill=self.color,
            outline="",
            tags="bar"
        )

        # Animation state
        self.animating = False

    def set_value(self, value: float, color: str = None, animate: bool = True):
        """Set progress value (0.0-1.0) with optional animation."""
        self.target_value = max(0.0, min(1.0, value))
        if color:
            self.color = color
            self.itemconfig(self.bar, fill=color)

        if animate and not self.animating:
            self._animate_to_target()
        else:
            self.value = self.target_value
            self._update_bar()

    def _animate_to_target(self):
        """Smooth animation to target value."""
        self.animating = True
        step = (self.target_value - self.value) * 0.2  # Ease-out

        if abs(self.target_value - self.value) > 0.01:
            self.value += step
            self._update_bar()
            self.after(16, self._animate_to_target)  # 60fps
        else:
            self.value = self.target_value
            self._update_bar()
            self.animating = False

    def _update_bar(self):
        """Update bar position."""
        bar_width = self.width * self.value
        self.coords(self.bar, 0, 0, bar_width, self.height)


class AnimatedNumber(tk.Label):
    """Label with animated number counting."""

    def __init__(self, parent, initial_value=0, suffix="%", **kwargs):
        self.current_value = initial_value
        self.target_value = initial_value
        self.suffix = suffix
        super().__init__(parent, text=f"{initial_value}{suffix}", **kwargs)
        self.animating = False

    def set_value(self, value: float, animate: bool = True):
        """Set value with optional animation."""
        self.target_value = value

        if animate and not self.animating:
            self._animate_to_target()
        else:
            self.current_value = value
            self._update_display()

    def _animate_to_target(self):
        """Smooth count animation."""
        self.animating = True
        step = (self.target_value - self.current_value) * 0.15

        if abs(self.target_value - self.current_value) > 0.5:
            self.current_value += step
            self._update_display()
            self.after(16, self._animate_to_target)  # 60fps
        else:
            self.current_value = self.target_value
            self._update_display()
            self.animating = False

    def _update_display(self):
        """Update displayed text."""
        self.config(text=f"{int(self.current_value)}{self.suffix}")


# ============================================================================
# Main Compact Window
# ============================================================================

class CompactLiveAdviceWindow:
    """
    Ultra-compact floating window for live poker advice.

    Features:
    - Always-on-top 300x180px window
    - Live win probability updates
    - Confidence visualization
    - Smooth animations
    - Smart transparency
    """

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        position: tuple = None,
        auto_hide: bool = True
    ):
        """
        Initialize compact live advice window.

        Args:
            parent: Parent Tk window (None for standalone)
            position: (x, y) screen position (None for default bottom-right)
            auto_hide: Auto-fade when inactive
        """
        # Create window
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()

        # Window configuration
        self.root.title("Live Advice")
        self.root.geometry("300x180")
        self.root.resizable(False, False)

        # Always on top
        self.root.attributes('-topmost', True)

        # macOS: utility window
        try:
            self.root.attributes('-type', 'utility')
        except:
            pass

        # Remove window decorations (frameless)
        try:
            self.root.overrideredirect(True)
        except:
            pass

        # State
        self.current_advice: Optional[LiveAdviceData] = None
        self.auto_hide = auto_hide
        self.opacity = 0.95
        self.is_paused = False
        self.mouse_over = False

        # Animation state
        self.fade_timer = None

        # Settings
        self.settings_file = Path.home() / ".pokertool" / "compact_window_settings.json"
        self.settings = self._load_settings()

        # Create UI
        self._create_ui()

        # Position window
        if position:
            self.root.geometry(f"+{position[0]}+{position[1]}")
        else:
            self._position_default()

        # Bind events
        self._bind_events()

        # Set initial transparency
        self._set_opacity(self.opacity)

        # Show initial state
        self._show_no_data()

        logger.info("CompactLiveAdviceWindow initialized")

    def _create_ui(self):
        """Create the compact UI layout."""
        # Main container
        self.main_frame = tk.Frame(
            self.root,
            bg=CompactColors.BG_PRIMARY,
            highlightthickness=1,
            highlightbackground=CompactColors.BORDER
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header bar (drag handle + settings)
        self._create_header()

        # Action section (large, prominent)
        self._create_action_section()

        # Win probability section
        self._create_win_probability_section()

        # Confidence section
        self._create_confidence_section()

        # Reasoning section
        self._create_reasoning_section()

    def _create_header(self):
        """Create header with drag handle and settings button."""
        header = tk.Frame(self.main_frame, bg=CompactColors.BG_SECONDARY, height=24)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Drag indicator
        drag_label = tk.Label(
            header,
            text="● Live Advice",
            font=("Arial", 9),
            fg=CompactColors.TEXT_SECONDARY,
            bg=CompactColors.BG_SECONDARY
        )
        drag_label.pack(side=tk.LEFT, padx=8)

        # Make draggable
        drag_label.bind('<Button-1>', self._start_drag)
        drag_label.bind('<B1-Motion>', self._on_drag)
        header.bind('<Button-1>', self._start_drag)
        header.bind('<B1-Motion>', self._on_drag)

        # Settings button (placeholder for TASK-015)
        self.settings_btn = tk.Label(
            header,
            text="⚙",
            font=("Arial", 12),
            fg=CompactColors.TEXT_SECONDARY,
            bg=CompactColors.BG_SECONDARY,
            cursor="hand2"
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=8)

        self._drag_data = {"x": 0, "y": 0}

    def _create_action_section(self):
        """Create main action display."""
        action_frame = tk.Frame(self.main_frame, bg=CompactColors.BG_PRIMARY, height=60)
        action_frame.pack(fill=tk.X, pady=(4, 0))
        action_frame.pack_propagate(False)

        # Action label (large, bold)
        self.action_label = tk.Label(
            action_frame,
            text="...",
            font=("Arial", 48, "bold"),
            fg=CompactColors.ACTION_UNKNOWN,
            bg=CompactColors.BG_PRIMARY
        )
        self.action_label.pack(expand=True)

    def _create_win_probability_section(self):
        """Create win probability display with visual bar."""
        win_frame = tk.Frame(self.main_frame, bg=CompactColors.BG_PRIMARY, height=45)
        win_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        win_frame.pack_propagate(False)

        # Win label with animated number
        label_frame = tk.Frame(win_frame, bg=CompactColors.BG_PRIMARY)
        label_frame.pack()

        tk.Label(
            label_frame,
            text="Win: ",
            font=("Arial", 18),
            fg=CompactColors.TEXT_SECONDARY,
            bg=CompactColors.BG_PRIMARY
        ).pack(side=tk.LEFT)

        self.win_number = AnimatedNumber(
            label_frame,
            initial_value=0,
            suffix="%",
            font=("Arial", 24, "bold"),
            fg=CompactColors.TEXT_PRIMARY,
            bg=CompactColors.BG_PRIMARY
        )
        self.win_number.pack(side=tk.LEFT)

        # Visual progress bar
        self.win_bar = AnimatedProgressBar(
            win_frame,
            width=280,
            height=12,
            bg=CompactColors.BG_PRIMARY
        )
        self.win_bar.pack(pady=(2, 0))

    def _create_confidence_section(self):
        """Create confidence meter."""
        conf_frame = tk.Frame(self.main_frame, bg=CompactColors.BG_PRIMARY, height=30)
        conf_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        conf_frame.pack_propagate(False)

        # Label
        tk.Label(
            conf_frame,
            text="Confidence:",
            font=("Arial", 10),
            fg=CompactColors.TEXT_SECONDARY,
            bg=CompactColors.BG_PRIMARY
        ).pack(side=tk.LEFT)

        # Percentage
        self.conf_number = tk.Label(
            conf_frame,
            text="0%",
            font=("Arial", 10, "bold"),
            fg=CompactColors.TEXT_PRIMARY,
            bg=CompactColors.BG_PRIMARY
        )
        self.conf_number.pack(side=tk.LEFT, padx=(4, 8))

        # Progress bar
        bar_container = tk.Frame(conf_frame, bg=CompactColors.BG_PRIMARY)
        bar_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.conf_bar = AnimatedProgressBar(
            bar_container,
            width=180,
            height=16,
            bg=CompactColors.BG_PRIMARY
        )
        self.conf_bar.pack()

    def _create_reasoning_section(self):
        """Create reasoning text display."""
        reason_frame = tk.Frame(self.main_frame, bg=CompactColors.BG_SECONDARY, height=24)
        reason_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 8))
        reason_frame.pack_propagate(False)

        self.reasoning_label = tk.Label(
            reason_frame,
            text="Waiting for table data...",
            font=("Arial", 9),
            fg=CompactColors.TEXT_SECONDARY,
            bg=CompactColors.BG_SECONDARY,
            wraplength=280,
            justify=tk.CENTER
        )
        self.reasoning_label.pack(expand=True)

    def _position_default(self):
        """Position window at default location (bottom-right)."""
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Bottom-right corner with margins
        x = screen_width - window_width - 20
        y = screen_height - window_height - 80  # Leave room for dock/taskbar

        self.root.geometry(f"+{x}+{y}")

    def _bind_events(self):
        """Bind mouse and keyboard events."""
        # Mouse hover for auto-fade
        self.root.bind('<Enter>', self._on_mouse_enter)
        self.root.bind('<Leave>', self._on_mouse_leave)

        # Keyboard shortcuts (TASK-014)
        self.root.bind('<Control-l>', lambda e: self.toggle_visibility())
        self.root.bind('<Control-p>', lambda e: self.toggle_pause())
        self.root.bind('<Escape>', lambda e: self.hide())

    def _start_drag(self, event):
        """Start window drag."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event):
        """Handle window drag."""
        x = self.root.winfo_x() + event.x - self._drag_data["x"]
        y = self.root.winfo_y() + event.y - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

        # Save position
        self.settings["position"] = (x, y)
        self._save_settings()

    def _on_mouse_enter(self, event):
        """Handle mouse enter."""
        self.mouse_over = True
        self._cancel_fade()
        self._set_opacity(0.95)

    def _on_mouse_leave(self, event):
        """Handle mouse leave."""
        self.mouse_over = False
        if self.auto_hide:
            self._schedule_fade()

    def _schedule_fade(self):
        """Schedule auto-fade after 3 seconds."""
        self._cancel_fade()
        self.fade_timer = self.root.after(3000, lambda: self._set_opacity(0.70))

    def _cancel_fade(self):
        """Cancel scheduled fade."""
        if self.fade_timer:
            self.root.after_cancel(self.fade_timer)
            self.fade_timer = None

    def _set_opacity(self, opacity: float):
        """Set window opacity (0.0-1.0)."""
        self.opacity = opacity
        try:
            self.root.attributes('-alpha', opacity)
        except:
            pass

    def _load_settings(self) -> Dict[str, Any]:
        """Load window settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")

        return {
            "position": None,
            "update_frequency": 2,
            "auto_hide": True,
            "theme": "light"
        }

    def _save_settings(self):
        """Save window settings to file."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save settings: {e}")

    # ========================================================================
    # Public API
    # ========================================================================

    def update_advice(self, advice: LiveAdviceData):
        """
        Update displayed advice with smooth animations.

        Args:
            advice: LiveAdviceData with current recommendation
        """
        self.current_advice = advice

        if not advice.has_data:
            self._show_no_data()
            return

        if advice.is_calculating:
            self._show_calculating()
            return

        # Update action
        action_text = advice.action.value
        if advice.action_amount and advice.action in (ActionType.RAISE, ActionType.ALL_IN):
            action_text = f"{advice.action.value}"
            # Show amount in reasoning instead to keep action clean

        action_color = self._get_action_color(advice.action)

        # Animate action if changed
        if self.action_label.cget("text") != action_text:
            self._fade_and_update(self.action_label, action_text, action_color)

        # Update win probability with animation
        win_pct = advice.win_probability * 100
        self.win_number.set_value(win_pct, animate=True)

        # Update win bar with gradient color
        win_color = self._get_win_probability_color(advice.win_probability)
        self.win_bar.set_value(advice.win_probability, color=win_color, animate=True)

        # Update confidence
        conf_pct = advice.confidence * 100
        self.conf_number.config(text=f"{int(conf_pct)}%")

        conf_level = ConfidenceLevel.from_confidence(advice.confidence)
        self.conf_bar.set_value(advice.confidence, color=conf_level.color, animate=True)

        # Update reasoning
        reasoning_text = advice.reasoning[:50]  # Max 50 chars
        if advice.action_amount and advice.action == ActionType.RAISE:
            reasoning_text = f"${int(advice.action_amount)} - {reasoning_text}"

        self.reasoning_label.config(text=reasoning_text)

        # Schedule auto-fade
        if self.auto_hide and not self.mouse_over:
            self._schedule_fade()

        logger.debug(f"Updated advice: {action_text}, Win: {win_pct:.1f}%, Conf: {conf_pct:.1f}%")

    def _show_no_data(self):
        """Show 'no data' state."""
        self.action_label.config(text="...", fg=CompactColors.ACTION_UNKNOWN)
        self.win_number.set_value(0, animate=False)
        self.win_bar.set_value(0, color=CompactColors.PROGRESS_BG, animate=False)
        self.conf_number.config(text="0%")
        self.conf_bar.set_value(0, color=CompactColors.PROGRESS_BG, animate=False)
        self.reasoning_label.config(text="Waiting for table data...")

    def _show_calculating(self):
        """Show 'calculating' state."""
        self.action_label.config(text="...", fg=CompactColors.TEXT_SECONDARY)
        self.reasoning_label.config(text="Calculating recommendation...")

    def _fade_and_update(self, label, new_text, new_color):
        """Fade out, update, fade in animation."""
        # Simple instant update for now (TASK-004 will add smooth transitions)
        label.config(text=new_text, fg=new_color)

    def _get_action_color(self, action: ActionType) -> str:
        """Get color for action type."""
        color_map = {
            ActionType.RAISE: CompactColors.ACTION_RAISE,
            ActionType.CALL: CompactColors.ACTION_CALL,
            ActionType.FOLD: CompactColors.ACTION_FOLD,
            ActionType.CHECK: CompactColors.ACTION_CHECK,
            ActionType.ALL_IN: CompactColors.ACTION_RAISE,
            ActionType.UNKNOWN: CompactColors.ACTION_UNKNOWN
        }
        return color_map.get(action, CompactColors.ACTION_UNKNOWN)

    def _get_win_probability_color(self, win_prob: float) -> str:
        """Get gradient color for win probability (0.0-1.0)."""
        if win_prob < 0.5:
            # Red to Yellow gradient
            ratio = win_prob * 2  # 0.0-1.0 for first half
            return self._interpolate_color(CompactColors.WIN_LOW, CompactColors.WIN_MID, ratio)
        else:
            # Yellow to Green gradient
            ratio = (win_prob - 0.5) * 2  # 0.0-1.0 for second half
            return self._interpolate_color(CompactColors.WIN_MID, CompactColors.WIN_HIGH, ratio)

    def _interpolate_color(self, color1: str, color2: str, ratio: float) -> str:
        """Interpolate between two hex colors."""
        # Parse colors
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        # Interpolate
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)

        return f"#{r:02x}{g:02x}{b:02x}"

    def clear(self):
        """Clear all displayed advice."""
        self._show_no_data()

    def toggle_visibility(self):
        """Toggle window visibility."""
        if self.root.state() == 'normal':
            self.hide()
        else:
            self.show()

    def toggle_pause(self):
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.reasoning_label.config(text="⏸ PAUSED - Press Ctrl+P to resume")
        else:
            if self.current_advice:
                self.update_advice(self.current_advice)

    def show(self):
        """Show the window."""
        self.root.deiconify()
        self._set_opacity(0.95)

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
    """Demo the compact live advice window."""
    import random

    window = CompactLiveAdviceWindow()

    def update_random_advice():
        """Update with random advice for testing."""
        actions = [ActionType.FOLD, ActionType.CALL, ActionType.RAISE]
        action = random.choice(actions)

        advice = LiveAdviceData(
            action=action,
            action_amount=random.uniform(20, 200) if action == ActionType.RAISE else None,
            win_probability=random.uniform(0.2, 0.9),
            confidence=random.uniform(0.5, 0.95),
            reasoning=random.choice([
                "Strong hand, good odds",
                "Weak vs range, fold",
                "Bluff spot, +EV raise",
                "Drawing dead, fold",
                "Top pair, value bet",
                "Flush draw, semi-bluff"
            ]),
            has_data=True,
            is_calculating=False
        )

        window.update_advice(advice)

        # Schedule next update
        window.root.after(2000, update_random_advice)

    # Start with calculating state
    window.update_advice(LiveAdviceData(is_calculating=True))

    # Start updates after 1 second
    window.root.after(1000, update_random_advice)

    window.mainloop()


if __name__ == '__main__':
    print("Starting Compact Live Advice Window Demo...")
    demo()
