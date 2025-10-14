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


class WindowMode(Enum):
    """Window display modes with different sizes and information density."""
    ULTRA_COMPACT = ("ultra", 180, 110)  # Minimal: Action + Win% only - optimized
    COMPACT = ("compact", 280, 160)      # Current: Basic info - optimized smaller
    STANDARD = ("standard", 380, 260)    # More metrics - optimized
    DETAILED = ("detailed", 480, 380)    # All features - optimized

    def __init__(self, mode_id: str, width: int, height: int):
        self.mode_id = mode_id
        self.width = width
        self.height = height


class ThemeMode(Enum):
    """Theme modes for the window."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Auto-switch based on time


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
    win_prob_lower: float = 0.0  # Lower bound of 95% CI
    win_prob_upper: float = 1.0  # Upper bound of 95% CI
    confidence: float = 0.0  # 0.0-1.0

    # Explanation
    reasoning: str = "Waiting for data..."

    # Metadata
    timestamp: float = field(default_factory=time.time)
    is_calculating: bool = False
    has_data: bool = False

    # Alternative actions (now enhanced)
    alternative_actions: Optional[list] = None

    # Technical details
    ev: Optional[float] = None
    pot_odds: Optional[float] = None

    # NEW: Multi-action EV comparison
    ev_fold: float = 0.0
    ev_call: Optional[float] = None
    ev_raise: Optional[float] = None
    ev_check: Optional[float] = None

    # NEW: Poker metrics
    stack_pot_ratio: Optional[float] = None  # SPR
    outs_count: Optional[int] = None  # Number of outs
    outs_percentage: Optional[float] = None  # % to improve
    hand_percentile: Optional[float] = None  # 0-100, higher is better

    # NEW: Bet sizing options
    bet_sizes: Optional[Dict[str, float]] = None  # {"1/3 pot": 33, "1/2 pot": 50, ...}

    # NEW: Position and street
    position: Optional[str] = None  # BTN, SB, BB, EP, MP, LP
    street: Optional[str] = None  # preflop, flop, turn, river

    # NEW: Opponent data
    opponent_stats: Optional[Dict[str, Any]] = None  # VPIP, PFR, etc.

    # NEW: Time pressure
    time_remaining: Optional[float] = None  # seconds remaining to act


# ============================================================================
# Semantic Colors
# ============================================================================

class CompactColors:
    """Color scheme for compact window (supports light and dark modes)."""

    @staticmethod
    def get_colors(theme: ThemeMode = ThemeMode.LIGHT):
        """Get color scheme for specified theme."""
        if theme == ThemeMode.DARK:
            return CompactColors._dark_colors()
        elif theme == ThemeMode.AUTO:
            # Auto-switch based on time (6 PM - 6 AM = dark mode)
            import datetime
            hour = datetime.datetime.now().hour
            if 18 <= hour or hour < 6:
                return CompactColors._dark_colors()
        return CompactColors._light_colors()

    @staticmethod
    def _light_colors():
        """Light mode color scheme."""
        return {
            # Backgrounds
            'BG_PRIMARY': "#FFFFFF",
            'BG_SECONDARY': "#F5F5F5",
            'BG_ACCENT': "#E8F5E9",

            # Action colors
            'ACTION_RAISE': "#00C853",
            'ACTION_CALL': "#2979FF",
            'ACTION_FOLD': "#DD2C00",
            'ACTION_CHECK': "#757575",
            'ACTION_UNKNOWN': "#9E9E9E",

            # Win probability gradient
            'WIN_LOW': "#DD2C00",
            'WIN_MID': "#FFD600",
            'WIN_HIGH': "#00C853",

            # Confidence colors
            'CONF_VERY_HIGH': "#00C853",
            'CONF_HIGH': "#64DD17",
            'CONF_MEDIUM': "#FFD600",
            'CONF_LOW': "#FF6D00",
            'CONF_VERY_LOW': "#DD2C00",

            # Text
            'TEXT_PRIMARY': "#212121",
            'TEXT_SECONDARY': "#757575",
            'TEXT_ACCENT': "#00C853",

            # UI Elements
            'BORDER': "#E0E0E0",
            'SHADOW': "#00000030",
            'PROGRESS_BG': "#E0E0E0",

            # Position colors
            'POSITION_IP': "#00C853",  # In position (green)
            'POSITION_OOP': "#DD2C00",  # Out of position (red)

            # EV indicators
            'EV_POSITIVE': "#00C853",
            'EV_NEGATIVE': "#DD2C00",
            'EV_NEUTRAL': "#757575"
        }

    @staticmethod
    def _dark_colors():
        """Dark mode color scheme."""
        return {
            # Backgrounds
            'BG_PRIMARY': "#1E1E1E",
            'BG_SECONDARY': "#2D2D2D",
            'BG_ACCENT': "#1B5E20",

            # Action colors (slightly muted for dark mode)
            'ACTION_RAISE': "#00E676",
            'ACTION_CALL': "#448AFF",
            'ACTION_FOLD': "#FF5252",
            'ACTION_CHECK': "#9E9E9E",
            'ACTION_UNKNOWN': "#757575",

            # Win probability gradient
            'WIN_LOW': "#FF5252",
            'WIN_MID': "#FFEB3B",
            'WIN_HIGH': "#00E676",

            # Confidence colors
            'CONF_VERY_HIGH': "#00E676",
            'CONF_HIGH': "#76FF03",
            'CONF_MEDIUM': "#FFEB3B",
            'CONF_LOW': "#FF9100",
            'CONF_VERY_LOW': "#FF5252",

            # Text
            'TEXT_PRIMARY': "#E0E0E0",
            'TEXT_SECONDARY': "#B0B0B0",
            'TEXT_ACCENT': "#00E676",

            # UI Elements
            'BORDER': "#424242",
            'SHADOW': "#00000060",
            'PROGRESS_BG': "#424242",

            # Position colors
            'POSITION_IP': "#00E676",
            'POSITION_OOP': "#FF5252",

            # EV indicators
            'EV_POSITIVE': "#00E676",
            'EV_NEGATIVE': "#FF5252",
            'EV_NEUTRAL': "#9E9E9E"
        }

    # Maintain backward compatibility - default to light theme
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F5F5F5"
    BG_DARK = "#263238"
    ACTION_RAISE = "#00C853"
    ACTION_CALL = "#2979FF"
    ACTION_FOLD = "#DD2C00"
    ACTION_CHECK = "#757575"
    ACTION_UNKNOWN = "#9E9E9E"
    WIN_LOW = "#DD2C00"
    WIN_MID = "#FFD600"
    WIN_HIGH = "#00C853"
    CONF_VERY_HIGH = "#00C853"
    CONF_HIGH = "#64DD17"
    CONF_MEDIUM = "#FFD600"
    CONF_LOW = "#FF6D00"
    CONF_VERY_LOW = "#DD2C00"
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_ON_DARK = "#FFFFFF"
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
        auto_hide: bool = True,
        window_mode: WindowMode = WindowMode.COMPACT,
        theme_mode: ThemeMode = ThemeMode.LIGHT,
        separate_dock_icon: bool = False
    ):
        """
        Initialize compact live advice window.

        Args:
            parent: Parent Tk window (None for standalone)
            position: (x, y) screen position (None for default bottom-right)
            auto_hide: Auto-fade when inactive
            window_mode: Display mode (ultra-compact, compact, standard, detailed)
            theme_mode: Theme (light, dark, auto)
            separate_dock_icon: If True, configure for separate dock icon (macOS)
        """
        # Create window
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()

        # Configure for separate dock icon on macOS
        if separate_dock_icon:
            try:
                # Set different window class to separate from parent
                self.root.wm_class("PokerToolAdvice", "PokerToolAdvice")

                # Ungroup from parent window
                self.root.wm_group("")

                print("  ✓ Compact window configured for separate dock icon")
            except Exception as e:
                print(f"  ⚠️  Could not configure separate dock icon: {e}")

        # Display mode and theme
        self.window_mode = window_mode
        self.theme_mode = theme_mode
        self.colors = CompactColors.get_colors(theme_mode)

        # Window configuration
        self.root.title("Live Advice")
        self.root.geometry(f"{window_mode.width}x{window_mode.height}")
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

        # UI component references (will be set in _create_ui)
        self.main_frame = None
        self.action_label = None
        self.win_number = None
        self.win_bar = None
        self.conf_number = None
        self.conf_bar = None
        self.reasoning_label = None
        self.pot_odds_label = None
        self.ev_panel = None
        self.spr_label = None
        self.outs_label = None
        self.percentile_label = None
        self.position_badge = None
        self.street_badge = None
        self.bet_sizing_frame = None
        self.alternative_actions_frame = None
        self.opponent_stats_frame = None
        self.time_indicator = None

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

        logger.info(f"CompactLiveAdviceWindow initialized (mode: {window_mode.mode_id}, theme: {theme_mode.value})")

    def _create_ui(self):
        """Create the compact UI layout based on window mode."""
        # Main container
        self.main_frame = tk.Frame(
            self.root,
            bg=self.colors['BG_PRIMARY'],
            highlightthickness=1,
            highlightbackground=self.colors['BORDER']
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header bar (drag handle + settings)
        self._create_header()

        # Position & Street badges (all modes)
        if self.window_mode in (WindowMode.COMPACT, WindowMode.STANDARD, WindowMode.DETAILED):
            self._create_position_street_badges()

        # Action section (large, prominent) - all modes
        self._create_action_section()

        # Win probability section - all modes
        self._create_win_probability_section()

        # Pot odds display (compact and above)
        if self.window_mode in (WindowMode.COMPACT, WindowMode.STANDARD, WindowMode.DETAILED):
            self._create_pot_odds_section()

        # Confidence section - all modes
        self._create_confidence_section()

        # SPR, Outs, Percentile (standard and above)
        if self.window_mode in (WindowMode.STANDARD, WindowMode.DETAILED):
            self._create_poker_metrics_section()

        # EV comparison panel (standard and above)
        if self.window_mode in (WindowMode.STANDARD, WindowMode.DETAILED):
            self._create_ev_comparison_panel()

        # Bet sizing suggestions (detailed only)
        if self.window_mode == WindowMode.DETAILED:
            self._create_bet_sizing_section()

        # Alternative actions (detailed only)
        if self.window_mode == WindowMode.DETAILED:
            self._create_alternative_actions_section()

        # Reasoning section - all modes
        self._create_reasoning_section()

        # Opponent stats (detailed only)
        if self.window_mode == WindowMode.DETAILED:
            self._create_opponent_stats_section()

        # Time indicator (all modes, shown when relevant)
        self._create_time_indicator()

    def _create_header(self):
        """Create header with drag handle and settings button."""
        header = tk.Frame(self.main_frame, bg=self.colors['BG_SECONDARY'], height=24)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Drag indicator
        drag_label = tk.Label(
            header,
            text="● Live Advice",
            font=("Arial", 9),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_SECONDARY']
        )
        drag_label.pack(side=tk.LEFT, padx=8)

        # Make draggable
        drag_label.bind('<Button-1>', self._start_drag)
        drag_label.bind('<B1-Motion>', self._on_drag)
        header.bind('<Button-1>', self._start_drag)
        header.bind('<B1-Motion>', self._on_drag)

        # Settings button - now functional
        self.settings_btn = tk.Label(
            header,
            text="⚙",
            font=("Arial", 12),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_SECONDARY'],
            cursor="hand2"
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=8)
        self.settings_btn.bind('<Button-1>', self._show_settings_menu)

        self._drag_data = {"x": 0, "y": 0}

    def _create_position_street_badges(self):
        """Create position and street indicator badges."""
        badge_frame = tk.Frame(self.main_frame, bg=self.colors['BG_PRIMARY'], height=20)
        badge_frame.pack(fill=tk.X, pady=(2, 0))
        badge_frame.pack_propagate(False)

        # Position badge
        self.position_badge = tk.Label(
            badge_frame,
            text="POS",
            font=("Arial", 8, "bold"),
            fg=self.colors['TEXT_PRIMARY'],
            bg=self.colors['BG_ACCENT'],
            relief=tk.FLAT,
            padx=4,
            pady=1
        )
        self.position_badge.pack(side=tk.LEFT, padx=(10, 4))

        # Street badge
        self.street_badge = tk.Label(
            badge_frame,
            text="STREET",
            font=("Arial", 8, "bold"),
            fg=self.colors['TEXT_PRIMARY'],
            bg=self.colors['BG_ACCENT'],
            relief=tk.FLAT,
            padx=4,
            pady=1
        )
        self.street_badge.pack(side=tk.LEFT, padx=4)

    def _create_action_section(self):
        """Create main action display."""
        # Adjust height based on window mode
        height = 60 if self.window_mode == WindowMode.ULTRA_COMPACT else 50
        font_size = 40 if self.window_mode == WindowMode.ULTRA_COMPACT else 36  # Reduced for compact UI

        action_frame = tk.Frame(self.main_frame, bg=self.colors['BG_PRIMARY'], height=height)
        action_frame.pack(fill=tk.X, pady=(4, 0))
        action_frame.pack_propagate(False)

        # Action label (large, bold)
        self.action_label = tk.Label(
            action_frame,
            text="...",
            font=("Arial", font_size, "bold"),
            fg=self.colors['ACTION_UNKNOWN'],
            bg=self.colors['BG_PRIMARY']
        )
        self.action_label.pack(expand=True)

    def _create_win_probability_section(self):
        """Create win probability display with visual bar."""
        win_frame = tk.Frame(self.main_frame, bg=self.colors['BG_PRIMARY'], height=45)
        win_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        win_frame.pack_propagate(False)

        # Win label with animated number
        label_frame = tk.Frame(win_frame, bg=self.colors['BG_PRIMARY'])
        label_frame.pack()

        tk.Label(
            label_frame,
            text="Win: ",
            font=("Arial", 14),  # Reduced for compact UI
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_PRIMARY']
        ).pack(side=tk.LEFT)

        self.win_number = AnimatedNumber(
            label_frame,
            initial_value=0,
            suffix="%",
            font=("Arial", 20, "bold"),  # Reduced for compact UI
            fg=self.colors['TEXT_PRIMARY'],
            bg=self.colors['BG_PRIMARY']
        )
        self.win_number.pack(side=tk.LEFT)

        # Visual progress bar
        bar_width = self.window_mode.width - 20
        self.win_bar = AnimatedProgressBar(
            win_frame,
            width=bar_width,
            height=12,
            bg=self.colors['BG_PRIMARY']
        )
        self.win_bar.pack(pady=(2, 0))

    def _create_pot_odds_section(self):
        """Create pot odds display with visual indicator."""
        odds_frame = tk.Frame(self.main_frame, bg=self.colors['BG_PRIMARY'], height=22)
        odds_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        odds_frame.pack_propagate(False)

        # Pot odds label
        self.pot_odds_label = tk.Label(
            odds_frame,
            text="Pot Odds: - | Need: - | Have: -",
            font=("Arial", 9),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_PRIMARY']
        )
        self.pot_odds_label.pack(side=tk.LEFT)

    def _create_confidence_section(self):
        """Create confidence meter."""
        conf_frame = tk.Frame(self.main_frame, bg=self.colors['BG_PRIMARY'], height=30)
        conf_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        conf_frame.pack_propagate(False)

        # Label
        tk.Label(
            conf_frame,
            text="Confidence:",
            font=("Arial", 10),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_PRIMARY']
        ).pack(side=tk.LEFT)

        # Percentage
        self.conf_number = tk.Label(
            conf_frame,
            text="0%",
            font=("Arial", 10, "bold"),
            fg=self.colors['TEXT_PRIMARY'],
            bg=self.colors['BG_PRIMARY']
        )
        self.conf_number.pack(side=tk.LEFT, padx=(4, 8))

        # Progress bar
        bar_container = tk.Frame(conf_frame, bg=self.colors['BG_PRIMARY'])
        bar_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        bar_width = min(180, self.window_mode.width - 150)
        self.conf_bar = AnimatedProgressBar(
            bar_container,
            width=bar_width,
            height=16,
            bg=self.colors['BG_PRIMARY']
        )
        self.conf_bar.pack()

    def _create_poker_metrics_section(self):
        """Create SPR, outs, and percentile display."""
        metrics_frame = tk.Frame(self.main_frame, bg=self.colors['BG_SECONDARY'], height=25)
        metrics_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        metrics_frame.pack_propagate(False)

        # SPR
        self.spr_label = tk.Label(
            metrics_frame,
            text="SPR: -",
            font=("Arial", 9, "bold"),
            fg=self.colors['TEXT_PRIMARY'],
            bg=self.colors['BG_SECONDARY']
        )
        self.spr_label.pack(side=tk.LEFT, padx=(0, 10))

        # Outs
        self.outs_label = tk.Label(
            metrics_frame,
            text="Outs: -",
            font=("Arial", 9),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_SECONDARY']
        )
        self.outs_label.pack(side=tk.LEFT, padx=(0, 10))

        # Hand percentile
        self.percentile_label = tk.Label(
            metrics_frame,
            text="Hand: -",
            font=("Arial", 9),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_SECONDARY']
        )
        self.percentile_label.pack(side=tk.LEFT)

    def _create_ev_comparison_panel(self):
        """Create multi-action EV comparison panel."""
        ev_frame = tk.Frame(self.main_frame, bg=self.colors['BG_ACCENT'], height=25)
        ev_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        ev_frame.pack_propagate(False)

        # EV panel container
        self.ev_panel = tk.Label(
            ev_frame,
            text="Fold: 0 | Call: - | Raise: -",
            font=("Arial", 9),
            fg=self.colors['TEXT_PRIMARY'],
            bg=self.colors['BG_ACCENT']
        )
        self.ev_panel.pack(expand=True)

    def _create_bet_sizing_section(self):
        """Create bet sizing suggestions."""
        self.bet_sizing_frame = tk.Frame(self.main_frame, bg=self.colors['BG_SECONDARY'], height=28)
        self.bet_sizing_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        self.bet_sizing_frame.pack_propagate(False)

        # Will be populated dynamically when showing raise suggestions
        tk.Label(
            self.bet_sizing_frame,
            text="Bet sizes: ",
            font=("Arial", 8),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_SECONDARY']
        ).pack(side=tk.LEFT, padx=(0, 5))

    def _create_alternative_actions_section(self):
        """Create alternative actions panel."""
        self.alternative_actions_frame = tk.Frame(self.main_frame, bg=self.colors['BG_PRIMARY'], height=22)
        self.alternative_actions_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        self.alternative_actions_frame.pack_propagate(False)

        tk.Label(
            self.alternative_actions_frame,
            text="Alt: ",
            font=("Arial", 8),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_PRIMARY']
        ).pack(side=tk.LEFT)

    def _create_reasoning_section(self):
        """Create reasoning text display."""
        wrap_length = self.window_mode.width - 20
        reason_frame = tk.Frame(self.main_frame, bg=self.colors['BG_SECONDARY'], height=24)
        reason_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 8))
        reason_frame.pack_propagate(False)

        self.reasoning_label = tk.Label(
            reason_frame,
            text="Waiting for table data...",
            font=("Arial", 9),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_SECONDARY'],
            wraplength=wrap_length,
            justify=tk.CENTER
        )
        self.reasoning_label.pack(expand=True)

    def _create_opponent_stats_section(self):
        """Create opponent stats mini-HUD."""
        self.opponent_stats_frame = tk.Frame(self.main_frame, bg=self.colors['BG_ACCENT'], height=22)
        self.opponent_stats_frame.pack(fill=tk.X, padx=10, pady=(0, 2))
        self.opponent_stats_frame.pack_propagate(False)

        tk.Label(
            self.opponent_stats_frame,
            text="Opp: ",
            font=("Arial", 8),
            fg=self.colors['TEXT_SECONDARY'],
            bg=self.colors['BG_ACCENT']
        ).pack(side=tk.LEFT)

    def _create_time_indicator(self):
        """Create time bank countdown indicator (shown when relevant)."""
        self.time_indicator = tk.Label(
            self.main_frame,
            text="",
            font=("Arial", 10, "bold"),
            fg="#FF5252",
            bg=self.colors['BG_PRIMARY']
        )
        # Not packed by default, will pack when time pressure detected

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

        # Keyboard shortcuts
        self.root.bind('<Control-l>', lambda e: self.toggle_visibility())
        self.root.bind('<Control-p>', lambda e: self.toggle_pause())
        self.root.bind('<Escape>', lambda e: self.hide())
        self.root.bind('<Control-r>', lambda e: self.cycle_window_mode())
        self.root.bind('<Control-t>', lambda e: self.toggle_theme())
        self.root.bind('<Control-plus>', lambda e: self.adjust_opacity(0.05))
        self.root.bind('<Control-minus>', lambda e: self.adjust_opacity(-0.05))

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

    def _show_settings_menu(self, event):
        """Show settings dropdown menu."""
        menu = tk.Menu(self.root, tearoff=0)

        # Window mode submenu
        mode_menu = tk.Menu(menu, tearoff=0)
        for mode in WindowMode:
            mode_menu.add_command(
                label=f"{mode.mode_id.capitalize()} ({mode.width}x{mode.height})",
                command=lambda m=mode: self.set_window_mode(m)
            )
        menu.add_cascade(label="Window Size", menu=mode_menu)

        # Theme submenu
        theme_menu = tk.Menu(menu, tearoff=0)
        for theme in ThemeMode:
            theme_menu.add_command(
                label=theme.value.capitalize(),
                command=lambda t=theme: self.set_theme(t)
            )
        menu.add_cascade(label="Theme", menu=theme_menu)

        # Opacity
        menu.add_separator()
        menu.add_command(label="Increase Opacity (Ctrl++)", command=lambda: self.adjust_opacity(0.05))
        menu.add_command(label="Decrease Opacity (Ctrl+-)", command=lambda: self.adjust_opacity(-0.05))

        # Auto-hide
        menu.add_separator()
        menu.add_checkbutton(label="Auto-hide", variable=tk.BooleanVar(value=self.auto_hide),
                            command=self.toggle_auto_hide)

        # Show menu
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def cycle_window_mode(self):
        """Cycle through window modes."""
        modes = list(WindowMode)
        current_idx = modes.index(self.window_mode)
        next_idx = (current_idx + 1) % len(modes)
        self.set_window_mode(modes[next_idx])

    def set_window_mode(self, mode: WindowMode):
        """Set window mode and rebuild UI."""
        if mode == self.window_mode:
            return

        self.window_mode = mode

        # Save to settings
        self.settings['window_mode'] = mode.mode_id
        self._save_settings()

        # Resize window
        self.root.geometry(f"{mode.width}x{mode.height}")

        # Rebuild UI
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self._create_ui()

        # Restore current advice
        if self.current_advice:
            self.update_advice(self.current_advice)

        logger.info(f"Switched to {mode.mode_id} mode")

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_mode == ThemeMode.LIGHT:
            self.set_theme(ThemeMode.DARK)
        else:
            self.set_theme(ThemeMode.LIGHT)

    def set_theme(self, theme: ThemeMode):
        """Set theme and update colors."""
        if theme == self.theme_mode:
            return

        self.theme_mode = theme
        self.colors = CompactColors.get_colors(theme)

        # Save to settings
        self.settings['theme'] = theme.value
        self._save_settings()

        # Rebuild UI with new colors
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self._create_ui()

        # Restore current advice
        if self.current_advice:
            self.update_advice(self.current_advice)

        logger.info(f"Switched to {theme.value} theme")

    def adjust_opacity(self, delta: float):
        """Adjust window opacity."""
        new_opacity = max(0.3, min(1.0, self.opacity + delta))
        self._set_opacity(new_opacity)
        logger.info(f"Opacity set to {new_opacity:.0%}")

    def toggle_auto_hide(self):
        """Toggle auto-hide feature."""
        self.auto_hide = not self.auto_hide
        self.settings['auto_hide'] = self.auto_hide
        self._save_settings()
        logger.info(f"Auto-hide: {self.auto_hide}")

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

        # ====== Core elements (all modes) ======

        # Update position and street badges
        if self.position_badge and advice.position:
            pos_text = advice.position.upper()
            self.position_badge.config(text=pos_text)
            # Color code position (green=IP, red=OOP)
            if advice.position in ('BTN', 'CO', 'HJ'):
                self.position_badge.config(bg=self.colors.get('POSITION_IP', '#00C853'))
            else:
                self.position_badge.config(bg=self.colors.get('POSITION_OOP', '#DD2C00'))

        if self.street_badge and advice.street:
            street_text = advice.street.upper()[:4]  # PREF, FLOP, TURN, RIVE
            self.street_badge.config(text=street_text)

        # Update action
        action_text = advice.action.value
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

        # Update pot odds (compact and above)
        if self.pot_odds_label and advice.pot_odds is not None:
            # Calculate what we need
            pot_odds_pct = advice.pot_odds * 100
            win_needed = pot_odds_pct
            have_equity = advice.win_probability * 100

            # Format pot odds as ratio
            if advice.pot_odds > 0:
                ratio = int(1 / advice.pot_odds)
                odds_text = f"Pot Odds: {ratio}:1 | Need: {win_needed:.0f}% | Have: {have_equity:.0f}%"

                # Add visual indicator
                if have_equity >= win_needed:
                    odds_text += " ✓"
                    self.pot_odds_label.config(fg=self.colors.get('EV_POSITIVE', '#00C853'))
                else:
                    odds_text += " ✗"
                    self.pot_odds_label.config(fg=self.colors.get('EV_NEGATIVE', '#DD2C00'))
            else:
                odds_text = "Pot Odds: - | Need: - | Have: -"

            self.pot_odds_label.config(text=odds_text)

        # Update confidence
        conf_pct = advice.confidence * 100
        self.conf_number.config(text=f"{int(conf_pct)}%")

        conf_level = ConfidenceLevel.from_confidence(advice.confidence)
        self.conf_bar.set_value(advice.confidence, color=conf_level.color, animate=True)

        # ====== Poker metrics (standard and above) ======

        if self.spr_label and advice.stack_pot_ratio is not None:
            spr = advice.stack_pot_ratio
            spr_text = f"SPR: {spr:.1f}"
            self.spr_label.config(text=spr_text)
            # Color code SPR (red=<3, yellow=3-10, green=>10)
            if spr < 3:
                self.spr_label.config(fg="#DD2C00")
            elif spr < 10:
                self.spr_label.config(fg="#FFD600")
            else:
                self.spr_label.config(fg="#00C853")

        if self.outs_label and advice.outs_count is not None:
            outs_text = f"Outs: {advice.outs_count}"
            if advice.outs_percentage:
                outs_text += f" ({advice.outs_percentage:.0f}%)"
            self.outs_label.config(text=outs_text)

        if self.percentile_label and advice.hand_percentile is not None:
            percentile_text = f"Hand: Top {100 - advice.hand_percentile:.0f}%"
            self.percentile_label.config(text=percentile_text)

        # ====== EV comparison (standard and above) ======

        if self.ev_panel:
            ev_parts = []
            ev_parts.append(f"Fold: 0")

            if advice.ev_call is not None:
                color_call = "+" if advice.ev_call > 0 else ""
                ev_parts.append(f"Call: {color_call}{advice.ev_call:.1f}")

            if advice.ev_raise is not None:
                color_raise = "+" if advice.ev_raise > 0 else ""
                ev_parts.append(f"Raise: {color_raise}{advice.ev_raise:.1f}")

            ev_text = " | ".join(ev_parts)
            self.ev_panel.config(text=ev_text)

        # ====== Bet sizing (detailed only) ======

        if self.bet_sizing_frame and advice.bet_sizes:
            # Clear existing bet buttons
            for widget in self.bet_sizing_frame.winfo_children()[1:]:
                widget.destroy()

            # Add bet size buttons
            for size_label, amount in advice.bet_sizes.items():
                btn = tk.Label(
                    self.bet_sizing_frame,
                    text=f"{size_label}: ${int(amount)}",
                    font=("Arial", 8),
                    fg=self.colors['TEXT_PRIMARY'],
                    bg=self.colors['BG_ACCENT'],
                    relief=tk.RAISED,
                    padx=3,
                    pady=1,
                    cursor="hand2"
                )
                btn.pack(side=tk.LEFT, padx=2)

        # ====== Alternative actions (detailed only) ======

        if self.alternative_actions_frame and advice.alternative_actions:
            # Clear existing
            for widget in self.alternative_actions_frame.winfo_children()[1:]:
                widget.destroy()

            # Show up to 2 alternatives
            for i, alt in enumerate(advice.alternative_actions[:2], 1):
                if isinstance(alt, dict):
                    alt_text = f"{i}. {alt.get('action', '?')}"
                    if 'ev' in alt:
                        alt_text += f" ({alt['ev']:+.1f})"
                else:
                    alt_text = f"{i}. {alt}"

                label = tk.Label(
                    self.alternative_actions_frame,
                    text=alt_text,
                    font=("Arial", 8),
                    fg=self.colors['TEXT_SECONDARY'],
                    bg=self.colors['BG_PRIMARY']
                )
                label.pack(side=tk.LEFT, padx=5)

        # ====== Reasoning ======

        reasoning_text = advice.reasoning[:50]  # Max 50 chars
        if advice.action_amount and advice.action == ActionType.RAISE:
            reasoning_text = f"${int(advice.action_amount)} - {reasoning_text}"

        self.reasoning_label.config(text=reasoning_text)

        # ====== Opponent stats (detailed only) ======

        if self.opponent_stats_frame and advice.opponent_stats:
            # Clear existing
            for widget in self.opponent_stats_frame.winfo_children()[1:]:
                widget.destroy()

            stats = advice.opponent_stats
            stats_text = []
            if 'vpip' in stats:
                stats_text.append(f"VPIP: {stats['vpip']:.0f}%")
            if 'pfr' in stats:
                stats_text.append(f"PFR: {stats['pfr']:.0f}%")
            if '3bet' in stats:
                stats_text.append(f"3-bet: {stats['3bet']:.0f}%")

            label = tk.Label(
                self.opponent_stats_frame,
                text=" | ".join(stats_text),
                font=("Arial", 8),
                fg=self.colors['TEXT_SECONDARY'],
                bg=self.colors['BG_ACCENT']
            )
            label.pack(side=tk.LEFT)

        # ====== Time pressure indicator ======

        if self.time_indicator and advice.time_remaining is not None:
            if advice.time_remaining > 0 and advice.time_remaining < 30:
                # Show time indicator
                time_text = f"⏱ {int(advice.time_remaining)}s"
                self.time_indicator.config(text=time_text)
                if not self.time_indicator.winfo_ismapped():
                    self.time_indicator.pack(side=tk.TOP, pady=2)

                # Flash if < 5 seconds
                if advice.time_remaining < 5:
                    self.time_indicator.config(fg="#FF0000")
                else:
                    self.time_indicator.config(fg="#FF5252")
            else:
                # Hide time indicator
                if self.time_indicator.winfo_ismapped():
                    self.time_indicator.pack_forget()

        # Schedule auto-fade
        if self.auto_hide and not self.mouse_over:
            self._schedule_fade()

        logger.debug(f"Updated advice: {action_text}, Win: {win_pct:.1f}%, Conf: {conf_pct:.1f}%")

    def _show_no_data(self):
        """Show 'no data' state."""
        self.action_label.config(text="...", fg=self.colors['ACTION_UNKNOWN'])
        self.win_number.set_value(0, animate=False)
        self.win_bar.set_value(0, color=self.colors['PROGRESS_BG'], animate=False)
        self.conf_number.config(text="0%")
        self.conf_bar.set_value(0, color=self.colors['PROGRESS_BG'], animate=False)
        self.reasoning_label.config(text="Waiting for table data...")

    def _show_calculating(self):
        """Show 'calculating' state."""
        self.action_label.config(text="...", fg=self.colors['TEXT_SECONDARY'])
        self.reasoning_label.config(text="Calculating recommendation...")

    def _fade_and_update(self, label, new_text, new_color):
        """Fade out, update, fade in animation."""
        # Simple instant update for now
        label.config(text=new_text, fg=new_color)

    def _get_action_color(self, action: ActionType) -> str:
        """Get color for action type."""
        color_map = {
            ActionType.RAISE: self.colors['ACTION_RAISE'],
            ActionType.CALL: self.colors['ACTION_CALL'],
            ActionType.FOLD: self.colors['ACTION_FOLD'],
            ActionType.CHECK: self.colors['ACTION_CHECK'],
            ActionType.ALL_IN: self.colors['ACTION_RAISE'],
            ActionType.UNKNOWN: self.colors['ACTION_UNKNOWN']
        }
        return color_map.get(action, self.colors['ACTION_UNKNOWN'])

    def _get_win_probability_color(self, win_prob: float) -> str:
        """Get gradient color for win probability (0.0-1.0)."""
        if win_prob < 0.5:
            # Red to Yellow gradient
            ratio = win_prob * 2  # 0.0-1.0 for first half
            return self._interpolate_color(self.colors['WIN_LOW'], self.colors['WIN_MID'], ratio)
        else:
            # Yellow to Green gradient
            ratio = (win_prob - 0.5) * 2  # 0.0-1.0 for second half
            return self._interpolate_color(self.colors['WIN_MID'], self.colors['WIN_HIGH'], ratio)

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
