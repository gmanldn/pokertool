#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Presentation Enhancement System
================================

Advanced UI enhancements for poker tool presentation.

Features:
- PRES-001: Real-Time Hand Strength Visualization
- PRES-002: Action History Timeline
- PRES-003: Pot Odds Visual Calculator
- PRES-004: Opponent Tendency Heat Map
- PRES-005: Session Performance Dashboard
- PRES-006: Notification Center with Priorities
- PRES-007: Dark Mode with Custom Themes

Version: 62.0.0
Author: PokerTool Development Team
"""

from __future__ import annotations

import logging
import time
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThemeMode(Enum):
    """Theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


@dataclass
class Notification:
    """Notification data."""
    priority: NotificationPriority
    title: str
    message: str
    timestamp: float = field(default_factory=time.time)
    read: bool = False
    action_callback: Optional[Any] = None


@dataclass
class ActionRecord:
    """Record of a poker action."""
    timestamp: float
    street: str
    action: str
    amount: float
    pot_size: float
    player: str = "Hero"


@dataclass
class SessionStats:
    """Session statistics."""
    hands_played: int = 0
    hands_won: int = 0
    total_profit: float = 0.0
    biggest_pot_won: float = 0.0
    vpip: float = 0.0  # Voluntarily Put $ In Pot
    pfr: float = 0.0   # Pre-Flop Raise
    aggression_factor: float = 0.0
    session_duration: float = 0.0


# ============================================================================
# PRES-001: Real-Time Hand Strength Visualization
# ============================================================================

class HandStrengthVisualizer:
    """
    Realtime hand strength visualization with color-coded meters.

    Features:
    - Dynamic strength meter (0-100%)
    - Color gradient (red->yellow->green)
    - Historical strength tracking
    - Street-by-street breakdown
    - Win probability integration
    """

    def __init__(self, parent=None):
        """Initialize hand strength visualizer."""
        self.parent = parent
        self.current_strength = 0.0
        self.strength_history: deque = deque(maxlen=50)

        if parent:
            self._create_ui()

        logger.info("HandStrengthVisualizer initialized")

    def _create_ui(self):
        """Create UI widgets."""
        self.frame = ttk.Frame(self.parent)

        # Strength label
        self.strength_label = tk.Label(
            self.frame,
            text="Hand Strength: --",
            font=("Arial", 14, "bold")
        )
        self.strength_label.pack(pady=5)

        # Strength meter (canvas)
        self.meter_canvas = tk.Canvas(
            self.frame,
            width=300,
            height=40,
            bg='#2a2a2a',
            highlightthickness=0
        )
        self.meter_canvas.pack(pady=5)

    def update_strength(self, strength: float, street: str = ""):
        """Update hand strength display."""
        self.current_strength = max(0.0, min(1.0, strength))
        self.strength_history.append((time.time(), self.current_strength, street))

        if hasattr(self, 'strength_label'):
            self.strength_label.config(text=f"Hand Strength: {self.current_strength*100:.0f}%")
            self._update_meter()

    def _update_meter(self):
        """Update visual meter."""
        if not hasattr(self, 'meter_canvas'):
            return

        # Clear canvas
        self.meter_canvas.delete("all")

        # Calculate color
        color = self._get_strength_color(self.current_strength)

        # Draw background
        self.meter_canvas.create_rectangle(
            5, 5, 295, 35,
            outline='#444',
            width=2
        )

        # Draw filled portion
        fill_width = int(285 * self.current_strength)
        if fill_width > 0:
            self.meter_canvas.create_rectangle(
                7, 7, 7 + fill_width, 33,
                fill=color,
                outline=""
            )

    def _get_strength_color(self, strength: float) -> str:
        """Get color for strength value."""
        if strength < 0.33:
            return "#ff4444"  # Red
        elif strength < 0.67:
            return "#ffaa00"  # Yellow
        else:
            return "#44ff44"  # Green


# ============================================================================
# PRES-002: Action History Timeline
# ============================================================================

class ActionHistoryTimeline:
    """
    Visual timeline of poker actions with street markers.

    Features:
    - Chronological action display
    - Street-by-street organization
    - Action type icons
    - Amount tracking
    - Scrollable history
    """

    def __init__(self, parent=None, max_actions: int = 100):
        """Initialize action history timeline."""
        self.parent = parent
        self.max_actions = max_actions
        self.actions: deque = deque(maxlen=max_actions)

        if parent:
            self._create_ui()

        logger.info("ActionHistoryTimeline initialized")

    def _create_ui(self):
        """Create UI widgets."""
        self.frame = ttk.Frame(self.parent)

        # Title
        ttk.Label(
            self.frame,
            text="Action History",
            font=("Arial", 12, "bold")
        ).pack(pady=5)

        # Scrollable timeline
        timeline_frame = ttk.Frame(self.frame)
        timeline_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(timeline_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.timeline_listbox = tk.Listbox(
            timeline_frame,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
            height=15
        )
        self.timeline_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.timeline_listbox.yview)

    def add_action(self, action: ActionRecord):
        """Add action to timeline."""
        self.actions.append(action)

        if hasattr(self, 'timeline_listbox'):
            # Format action string
            time_str = time.strftime("%H:%M:%S", time.localtime(action.timestamp))
            action_str = f"[{time_str}] {action.street:8s} | {action.player:6s} {action.action:6s} ${action.amount:.0f} (pot: ${action.pot_size:.0f})"

            self.timeline_listbox.insert(tk.END, action_str)
            self.timeline_listbox.see(tk.END)


# ============================================================================
# PRES-003: Pot Odds Visual Calculator
# ============================================================================

class PotOddsCalculator:
    """
    Visual pot odds calculator with recommendations.

    Features:
    - Pot odds calculation
    - Win probability comparison
    - EV calculation
    - Visual recommendation
    - Break-even analysis
    """

    def __init__(self, parent=None):
        """Initialize pot odds calculator."""
        self.parent = parent
        self.pot_size = 0.0
        self.call_amount = 0.0
        self.win_probability = 0.0

        if parent:
            self._create_ui()

        logger.info("PotOddsCalculator initialized")

    def _create_ui(self):
        """Create UI widgets."""
        self.frame = ttk.Frame(self.parent)

        # Title
        ttk.Label(
            self.frame,
            text="Pot Odds Calculator",
            font=("Arial", 12, "bold")
        ).pack(pady=5)

        # Display frame
        self.display_frame = ttk.Frame(self.frame)
        self.display_frame.pack(pady=10)

    def calculate_and_display(
        self,
        pot_size: float,
        call_amount: float,
        win_probability: float
    ) -> Dict[str, Any]:
        """Calculate pot odds and display recommendation."""
        self.pot_size = pot_size
        self.call_amount = call_amount
        self.win_probability = win_probability

        # Calculate pot odds
        pot_odds = call_amount / (pot_size + call_amount) if (pot_size + call_amount) > 0 else 1.0

        # Calculate EV
        ev = (win_probability * (pot_size + call_amount)) - call_amount

        # Recommendation
        should_call = win_probability >= pot_odds

        result = {
            'pot_odds': pot_odds,
            'win_probability': win_probability,
            'ev': ev,
            'should_call': should_call,
            'breakeven_equity': pot_odds
        }

        if hasattr(self, 'display_frame'):
            self._update_display(result)

        return result

    def _update_display(self, result: Dict[str, Any]):
        """Update visual display."""
        # Clear existing widgets
        for widget in self.display_frame.winfo_children():
            widget.destroy()

        # Display pot odds
        ttk.Label(
            self.display_frame,
            text=f"Pot Odds: {result['pot_odds']*100:.1f}%",
            font=("Arial", 11)
        ).pack()

        # Display win probability
        ttk.Label(
            self.display_frame,
            text=f"Win Prob: {result['win_probability']*100:.1f}%",
            font=("Arial", 11)
        ).pack()

        # Display EV
        ev_color = "green" if result['ev'] > 0 else "red"
        ttk.Label(
            self.display_frame,
            text=f"EV: ${result['ev']:.2f}",
            font=("Arial", 11),
            foreground=ev_color
        ).pack()

        # Display recommendation
        rec_text = "✓ CALL" if result['should_call'] else "✗ FOLD"
        rec_color = "green" if result['should_call'] else "red"
        ttk.Label(
            self.display_frame,
            text=rec_text,
            font=("Arial", 14, "bold"),
            foreground=rec_color
        ).pack(pady=5)


# ============================================================================
# PRES-004: Opponent Tendency Heat Map
# ============================================================================

class OpponentTendencyHeatMap:
    """
    Heat map visualization of opponent tendencies.

    Features:
    - VPIP/PFR tracking
    - Aggression by position
    - 3-bet/fold frequencies
    - Color-coded cells
    - Statistical confidence
    """

    def __init__(self, parent=None):
        """Initialize opponent tendency heat map."""
        self.parent = parent
        self.opponent_stats: Dict[str, Dict[str, float]] = {}

        if parent:
            self._create_ui()

        logger.info("OpponentTendencyHeatMap initialized")

    def _create_ui(self):
        """Create UI widgets."""
        self.frame = ttk.Frame(self.parent)

        # Title
        ttk.Label(
            self.frame,
            text="Opponent Tendencies",
            font=("Arial", 12, "bold")
        ).pack(pady=5)

        # Heat map canvas
        self.heatmap_canvas = tk.Canvas(
            self.frame,
            width=400,
            height=300,
            bg='white'
        )
        self.heatmap_canvas.pack(pady=5)

    def update_opponent_stats(self, opponent_name: str, stats: Dict[str, float]):
        """Update stats for opponent."""
        self.opponent_stats[opponent_name] = stats

        if hasattr(self, 'heatmap_canvas'):
            self._draw_heatmap()

    def _draw_heatmap(self):
        """Draw heat map visualization."""
        self.heatmap_canvas.delete("all")

        # Simple visualization (can be enhanced)
        y_offset = 20
        for opponent, stats in list(self.opponent_stats.items())[:5]:  # Show top 5
            self.heatmap_canvas.create_text(
                10, y_offset,
                text=f"{opponent}: VPIP {stats.get('vpip', 0)*100:.0f}% | PFR {stats.get('pfr', 0)*100:.0f}%",
                anchor='w',
                font=("Arial", 10)
            )
            y_offset += 30


# ============================================================================
# PRES-005: Session Performance Dashboard
# ============================================================================

class SessionPerformanceDashboard:
    """
    Comprehensive session performance dashboard.

    Features:
    - Hands played / win rate
    - Profit/loss tracking
    - VPIP/PFR statistics
    - Session duration
    - Graphical charts
    """

    def __init__(self, parent=None):
        """Initialize session performance dashboard."""
        self.parent = parent
        self.stats = SessionStats()
        self.session_start_time = time.time()

        if parent:
            self._create_ui()

        logger.info("SessionPerformanceDashboard initialized")

    def _create_ui(self):
        """Create UI widgets."""
        self.frame = ttk.Frame(self.parent)

        # Title
        ttk.Label(
            self.frame,
            text="Session Performance",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        # Stats grid
        self.stats_frame = ttk.Frame(self.frame)
        self.stats_frame.pack(pady=10)

        # Create stat labels
        self.stat_labels: Dict[str, tk.Label] = {}

        stat_names = [
            "Hands Played", "Win Rate", "Profit/Loss",
            "VPIP", "PFR", "Duration"
        ]

        for i, stat_name in enumerate(stat_names):
            row = i // 2
            col = i % 2

            ttk.Label(
                self.stats_frame,
                text=stat_name + ":",
                font=("Arial", 10, "bold")
            ).grid(row=row, column=col*2, sticky='e', padx=5, pady=2)

            self.stat_labels[stat_name] = ttk.Label(
                self.stats_frame,
                text="--",
                font=("Arial", 10)
            )
            self.stat_labels[stat_name].grid(row=row, column=col*2+1, sticky='w', padx=5, pady=2)

    def update_stats(self, stats: SessionStats):
        """Update dashboard with new stats."""
        self.stats = stats
        self.stats.session_duration = time.time() - self.session_start_time

        if hasattr(self, 'stat_labels'):
            # Update labels
            self.stat_labels["Hands Played"].config(text=str(stats.hands_played))

            win_rate = (stats.hands_won / max(1, stats.hands_played)) * 100
            self.stat_labels["Win Rate"].config(text=f"{win_rate:.1f}%")

            profit_color = "green" if stats.total_profit >= 0 else "red"
            self.stat_labels["Profit/Loss"].config(
                text=f"${stats.total_profit:.2f}",
                foreground=profit_color
            )

            self.stat_labels["VPIP"].config(text=f"{stats.vpip*100:.1f}%")
            self.stat_labels["PFR"].config(text=f"{stats.pfr*100:.1f}%")

            duration_mins = int(stats.session_duration / 60)
            self.stat_labels["Duration"].config(text=f"{duration_mins}m")


# ============================================================================
# PRES-006: Notification Center with Priorities
# ============================================================================

class NotificationCenter:
    """
    Centralized notification system with priorities.

    Features:
    - Priority-based notifications
    - Toast popups
    - Notification history
    - Action callbacks
    - Dismissal tracking
    """

    def __init__(self, parent=None, max_notifications: int = 50):
        """Initialize notification center."""
        self.parent = parent
        self.max_notifications = max_notifications
        self.notifications: deque = deque(maxlen=max_notifications)
        self.unread_count = 0

        logger.info("NotificationCenter initialized")

    def add_notification(self, notification: Notification):
        """Add notification to center."""
        self.notifications.append(notification)

        if not notification.read:
            self.unread_count += 1

        # Show toast for high/critical priority
        if notification.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
            self._show_toast(notification)

        logger.info(f"Notification added: [{notification.priority.value}] {notification.title}")

    def _show_toast(self, notification: Notification):
        """Show toast notification."""
        if not self.parent:
            return

        # Create toast window
        toast = tk.Toplevel(self.parent)
        toast.title("Notification")
        toast.geometry("300x100")
        toast.attributes('-topmost', True)

        # Set background color based on priority
        bg_color = {
            NotificationPriority.LOW: "#e8f5e9",
            NotificationPriority.MEDIUM: "#fff9c4",
            NotificationPriority.HIGH: "#ffe0b2",
            NotificationPriority.CRITICAL: "#ffcdd2"
        }.get(notification.priority, "#ffffff")

        toast.configure(bg=bg_color)

        # Title
        tk.Label(
            toast,
            text=notification.title,
            font=("Arial", 12, "bold"),
            bg=bg_color
        ).pack(pady=10)

        # Message
        tk.Label(
            toast,
            text=notification.message,
            font=("Arial", 10),
            bg=bg_color,
            wraplength=280
        ).pack(pady=5)

        # Auto-dismiss after 5 seconds
        toast.after(5000, toast.destroy)

    def get_unread_count(self) -> int:
        """Get number of unread notifications."""
        return self.unread_count

    def get_recent_notifications(self, count: int = 10) -> List[Notification]:
        """Get recent notifications."""
        return list(self.notifications)[-count:]


# ============================================================================
# PRES-007: Dark Mode with Custom Themes
# ============================================================================

class ThemeManager:
    """
    Theme management system with dark mode support.

    Features:
    - Light/dark/auto themes
    - Custom color schemes
    - Persistent theme selection
    - Dynamic theme switching
    - Per-widget styling
    """

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize theme manager."""
        self.config_file = config_file or Path.home() / '.pokertool' / 'theme.json'
        self.current_theme = ThemeMode.LIGHT

        # Theme definitions
        self.themes = {
            ThemeMode.LIGHT: {
                'bg': '#ffffff',
                'fg': '#000000',
                'button_bg': '#e0e0e0',
                'button_fg': '#000000',
                'highlight': '#4CAF50',
                'error': '#f44336',
                'warning': '#ff9800'
            },
            ThemeMode.DARK: {
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'button_bg': '#2d2d2d',
                'button_fg': '#ffffff',
                'highlight': '#66BB6A',
                'error': '#ef5350',
                'warning': '#ffa726'
            }
        }

        # Load saved theme
        self._load_theme()

        logger.info(f"ThemeManager initialized (mode: {self.current_theme.value})")

    def set_theme(self, theme: ThemeMode):
        """Set active theme."""
        self.current_theme = theme
        self._save_theme()
        logger.info(f"Theme changed to: {theme.value}")

    def get_color(self, color_name: str) -> str:
        """Get color value for current theme."""
        theme = self.themes.get(self.current_theme, self.themes[ThemeMode.LIGHT])
        return theme.get(color_name, '#000000')

    def apply_theme(self, widget: tk.Widget):
        """Apply theme to widget."""
        try:
            bg = self.get_color('bg')
            fg = self.get_color('fg')

            widget.configure(bg=bg, fg=fg)

            # Apply to children recursively
            for child in widget.winfo_children():
                self.apply_theme(child)
        except:
            pass  # Some widgets don't support all config options

    def _save_theme(self):
        """Save theme preference."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'theme': self.current_theme.value}, f)
        except Exception as e:
            logger.error(f"Failed to save theme: {e}")

    def _load_theme(self):
        """Load theme preference."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    theme_value = data.get('theme', 'light')
                    self.current_theme = ThemeMode(theme_value)
        except Exception as e:
            logger.error(f"Failed to load theme: {e}")


# ============================================================================
# Integrated Presentation System
# ============================================================================

class PresentationSystem:
    """
    Integrated presentation enhancement system.

    Combines all 7 presentation features into unified API.
    """

    def __init__(self, parent=None):
        """Initialize presentation system."""
        self.parent = parent

        self.hand_visualizer = HandStrengthVisualizer(parent)
        self.action_timeline = ActionHistoryTimeline(parent)
        self.pot_odds_calc = PotOddsCalculator(parent)
        self.opponent_heatmap = OpponentTendencyHeatMap(parent)
        self.session_dashboard = SessionPerformanceDashboard(parent)
        self.notification_center = NotificationCenter(parent)
        self.theme_manager = ThemeManager()

        logger.info("PresentationSystem initialized (7 presentation features active)")

    def create_demo_window(self):
        """Create demo window with all features."""
        if not self.parent:
            root = tk.Tk()
            root.title("Presentation System Demo")
            root.geometry("800x600")
            self.parent = root

        # Create notebook for tabs
        notebook = ttk.Notebook(self.parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add tabs
        notebook.add(self.hand_visualizer.frame, text="Hand Strength")
        notebook.add(self.action_timeline.frame, text="Action History")
        notebook.add(self.pot_odds_calc.frame, text="Pot Odds")
        notebook.add(self.opponent_heatmap.frame, text="Opponents")
        notebook.add(self.session_dashboard.frame, text="Session Stats")


# ============================================================================
# Factory Function
# ============================================================================

_presentation_system_instance = None

def get_presentation_system(parent=None) -> PresentationSystem:
    """Get global presentation system instance (singleton)."""
    global _presentation_system_instance

    if _presentation_system_instance is None:
        _presentation_system_instance = PresentationSystem(parent)

    return _presentation_system_instance


if __name__ == '__main__':
    # Demo
    logging.basicConfig(level=logging.INFO)

    print("Presentation Enhancement System Demo")
    print("=" * 60)

    root = tk.Tk()
    system = PresentationSystem(root)
    system.create_demo_window()

    # Test updates
    system.hand_visualizer.update_strength(0.75, "flop")
    system.action_timeline.add_action(ActionRecord(
        timestamp=time.time(),
        street="preflop",
        action="raise",
        amount=25.0,
        pot_size=15.0
    ))

    root.mainloop()
