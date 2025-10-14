#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool UI Enhancements
==========================

High-impact UI improvements for better information delivery and user feedback.

Features:
- Detection Status Panel
- Semantic Color System
- One-Click Feedback
- Keyboard Shortcuts
- Window Management
- Loading States
- Multi-Level Information Hierarchy

Version: 1.0.0
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import json
from pathlib import Path


# ============================================================================
# SEMANTIC COLOR SYSTEM
# ============================================================================

class SemanticColors:
    """Semantic color system for consistent UI theming."""

    # Action colors
    POSITIVE = "#00C853"      # Green - Good actions, profitable
    NEGATIVE = "#DD2C00"      # Red - Bad actions, danger
    CAUTION = "#FF6D00"       # Orange - Warning, medium confidence
    NEUTRAL = "#2196F3"       # Blue - Information
    INSIGHT = "#9C27B0"       # Purple - Learning, special insights

    # Confidence levels
    CONF_VERY_HIGH = "#00C853"  # 90%+
    CONF_HIGH = "#64DD17"       # 75-90%
    CONF_MEDIUM = "#FFD600"     # 60-75%
    CONF_LOW = "#FF6D00"        # 40-60%
    CONF_VERY_LOW = "#DD2C00"   # <40%

    # Status colors
    STATUS_ACTIVE = "#00C853"
    STATUS_WARNING = "#FFD600"
    STATUS_ERROR = "#DD2C00"
    STATUS_INACTIVE = "#9E9E9E"

    # Background colors
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F5F5F5"
    BG_CARD = "#FAFAFA"
    BG_DARK = "#263238"
    BG_DARK_CARD = "#37474F"

    # Text colors
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"
    TEXT_ON_DARK = "#FFFFFF"

    @classmethod
    def get_confidence_color(cls, confidence: float) -> str:
        """Get color based on confidence level."""
        if confidence >= 0.9:
            return cls.CONF_VERY_HIGH
        elif confidence >= 0.75:
            return cls.CONF_HIGH
        elif confidence >= 0.6:
            return cls.CONF_MEDIUM
        elif confidence >= 0.4:
            return cls.CONF_LOW
        else:
            return cls.CONF_VERY_LOW


# ============================================================================
# DETECTION STATUS PANEL
# ============================================================================

@dataclass
class DetectionStatus:
    """Status information for detection systems."""
    table_detected: bool = False
    fps: float = 0.0
    pot_confidence: float = 0.0
    cards_confidence: float = 0.0
    blinds_confidence: float = 0.0
    learning_active: bool = False
    cdp_connected: bool = False
    last_update: float = 0.0


class DetectionStatusPanel(ttk.Frame):
    """
    Live status panel showing detection health and performance.

    HIGH IMPACT: Provides immediate visibility into system state.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize the detection status panel."""
        super().__init__(parent, **kwargs)

        self.status = DetectionStatus()
        self._create_ui()

    def _create_ui(self):
        """Create the UI elements."""
        # Title
        title = tk.Label(
            self,
            text="Detection Status",
            font=("Arial", 12, "bold"),
            fg=SemanticColors.TEXT_PRIMARY,
            bg=SemanticColors.BG_CARD
        )
        title.pack(pady=(5, 10))

        # Status indicators grid
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Table Detection
        self._create_status_row(
            status_frame, 0, "Table:", "table",
            "Whether poker table is detected"
        )

        # FPS Counter
        self._create_metric_row(
            status_frame, 1, "FPS:", "fps",
            "Screen capture frame rate"
        )

        # OCR Confidence - Pot
        self._create_confidence_row(
            status_frame, 2, "Pot OCR:", "pot_conf"
        )

        # OCR Confidence - Cards
        self._create_confidence_row(
            status_frame, 3, "Cards OCR:", "cards_conf"
        )

        # OCR Confidence - Blinds
        self._create_confidence_row(
            status_frame, 4, "Blinds OCR:", "blinds_conf"
        )

        # Learning System
        self._create_status_row(
            status_frame, 5, "Learning:", "learning",
            "Adaptive learning system status"
        )

        # CDP Connection
        self._create_status_row(
            status_frame, 6, "CDP:", "cdp",
            "Chrome DevTools Protocol connection"
        )

    def _create_status_row(self, parent: ttk.Frame, row: int,
                          label: str, key: str, tooltip: str):
        """Create a status indicator row."""
        # Label
        lbl = tk.Label(
            parent,
            text=label,
            font=("Arial", 10),
            fg=SemanticColors.TEXT_SECONDARY,
            anchor="w"
        )
        lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)

        # Status dot
        dot = tk.Label(
            parent,
            text="●",
            font=("Arial", 16),
            fg=SemanticColors.STATUS_INACTIVE
        )
        dot.grid(row=row, column=1, sticky="e", padx=5)

        # Store reference
        setattr(self, f"{key}_dot", dot)

        # Tooltip
        self._create_tooltip(lbl, tooltip)

    def _create_metric_row(self, parent: ttk.Frame, row: int,
                          label: str, key: str, tooltip: str):
        """Create a metric display row."""
        # Label
        lbl = tk.Label(
            parent,
            text=label,
            font=("Arial", 10),
            fg=SemanticColors.TEXT_SECONDARY,
            anchor="w"
        )
        lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)

        # Value
        value = tk.Label(
            parent,
            text="--",
            font=("Arial", 10, "bold"),
            fg=SemanticColors.TEXT_PRIMARY,
            anchor="e"
        )
        value.grid(row=row, column=1, sticky="e", padx=5)

        # Store reference
        setattr(self, f"{key}_label", value)

        # Tooltip
        self._create_tooltip(lbl, tooltip)

    def _create_confidence_row(self, parent: ttk.Frame, row: int,
                              label: str, key: str):
        """Create a confidence bar row."""
        # Label
        lbl = tk.Label(
            parent,
            text=label,
            font=("Arial", 10),
            fg=SemanticColors.TEXT_SECONDARY,
            anchor="w"
        )
        lbl.grid(row=row, column=0, sticky="w", padx=5, pady=2)

        # Progress bar
        progress = ttk.Progressbar(
            parent,
            length=100,
            mode='determinate'
        )
        progress.grid(row=row, column=1, sticky="e", padx=5)

        # Store reference
        setattr(self, f"{key}_bar", progress)

    def _create_tooltip(self, widget: tk.Widget, text: str):
        """Add tooltip to widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(
                tooltip,
                text=text,
                background=SemanticColors.BG_DARK,
                foreground=SemanticColors.TEXT_ON_DARK,
                relief=tk.SOLID,
                borderwidth=1,
                font=("Arial", 9),
                padx=5,
                pady=3
            )
            label.pack()

            widget._tooltip = tooltip

        def hide_tooltip(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                delattr(widget, '_tooltip')

        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def update_status(self, status: DetectionStatus):
        """Update the status panel with new data."""
        self.status = status

        # Update table detection
        self.table_dot.config(
            fg=SemanticColors.STATUS_ACTIVE if status.table_detected
            else SemanticColors.STATUS_ERROR
        )

        # Update FPS
        self.fps_label.config(text=f"{status.fps:.1f}")

        # Update confidence bars
        self.pot_conf_bar['value'] = status.pot_confidence * 100
        self.cards_conf_bar['value'] = status.cards_confidence * 100
        self.blinds_conf_bar['value'] = status.blinds_confidence * 100

        # Update learning status
        self.learning_dot.config(
            fg=SemanticColors.STATUS_ACTIVE if status.learning_active
            else SemanticColors.STATUS_INACTIVE
        )

        # Update CDP status
        self.cdp_dot.config(
            fg=SemanticColors.STATUS_ACTIVE if status.cdp_connected
            else SemanticColors.STATUS_WARNING
        )


# ============================================================================
# ONE-CLICK FEEDBACK SYSTEM
# ============================================================================

class FeedbackButton(tk.Button):
    """Stylized feedback button with hover effects."""

    def __init__(self, parent: tk.Widget, icon: str, color: str,
                 callback: Callable, **kwargs):
        """Initialize feedback button."""
        super().__init__(
            parent,
            text=icon,
            font=("Arial", 20),
            fg=color,
            bg=SemanticColors.BG_CARD,
            activeforeground=color,
            activebackground=SemanticColors.BG_SECONDARY,
            relief=tk.FLAT,
            cursor="hand2",
            command=callback,
            **kwargs
        )

        # Hover effects
        self.bind('<Enter>', lambda e: self.config(bg=SemanticColors.BG_SECONDARY))
        self.bind('<Leave>', lambda e: self.config(bg=SemanticColors.BG_CARD))


class FeedbackPanel(ttk.Frame):
    """
    One-click feedback system for user input.

    HIGH IMPACT: Enables rapid user feedback for learning system.
    """

    def __init__(self, parent: tk.Widget,
                 on_feedback: Optional[Callable[[str], None]] = None,
                 **kwargs):
        """Initialize feedback panel."""
        super().__init__(parent, **kwargs)

        self.on_feedback = on_feedback
        self.last_feedback_time = 0.0
        self._create_ui()

    def _create_ui(self):
        """Create the UI elements."""
        # Title
        title = tk.Label(
            self,
            text="Was this helpful?",
            font=("Arial", 10),
            fg=SemanticColors.TEXT_SECONDARY
        )
        title.pack(pady=(5, 5))

        # Button container
        button_frame = ttk.Frame(self)
        button_frame.pack()

        # Thumbs up
        FeedbackButton(
            button_frame,
            icon="👍",
            color=SemanticColors.POSITIVE,
            callback=lambda: self._submit_feedback("helpful")
        ).pack(side=tk.LEFT, padx=10)

        # Thumbs down
        FeedbackButton(
            button_frame,
            icon="👎",
            color=SemanticColors.NEGATIVE,
            callback=lambda: self._submit_feedback("not_helpful")
        ).pack(side=tk.LEFT, padx=10)

        # Feedback status
        self.status_label = tk.Label(
            self,
            text="",
            font=("Arial", 9),
            fg=SemanticColors.TEXT_SECONDARY
        )
        self.status_label.pack(pady=(5, 0))

    def _submit_feedback(self, feedback_type: str):
        """Submit feedback and show confirmation."""
        # Throttle feedback
        now = time.time()
        if now - self.last_feedback_time < 1.0:
            return

        self.last_feedback_time = now

        # Call callback
        if self.on_feedback:
            self.on_feedback(feedback_type)

        # Show confirmation
        message = "Thanks!" if feedback_type == "helpful" else "Noted!"
        self.status_label.config(
            text=message,
            fg=SemanticColors.POSITIVE if feedback_type == "helpful"
            else SemanticColors.CAUTION
        )

        # Clear message after 2 seconds
        self.after(2000, lambda: self.status_label.config(text=""))


# ============================================================================
# KEYBOARD SHORTCUTS
# ============================================================================

class KeyboardShortcutManager:
    """
    Manages keyboard shortcuts for the application.

    HIGH IMPACT: Enables power users to work efficiently.
    """

    DEFAULT_SHORTCUTS = {
        '<space>': 'toggle_pause',
        'f': 'submit_feedback',
        'h': 'toggle_window',
        'd': 'toggle_debug',
        'r': 'refresh_detection',
        '1': 'rating_1',
        '2': 'rating_2',
        '3': 'rating_3',
        '4': 'rating_4',
        '5': 'rating_5',
    }

    def __init__(self, window: tk.Tk):
        """Initialize shortcut manager."""
        self.window = window
        self.shortcuts: Dict[str, Callable] = {}
        self.enabled = True

    def register(self, key: str, callback: Callable):
        """Register a keyboard shortcut."""
        self.shortcuts[key] = callback
        self.window.bind(key, lambda e: self._handle_shortcut(key))

    def _handle_shortcut(self, key: str):
        """Handle shortcut activation."""
        if not self.enabled:
            return

        callback = self.shortcuts.get(key)
        if callback:
            callback()

    def enable(self):
        """Enable shortcuts."""
        self.enabled = True

    def disable(self):
        """Disable shortcuts."""
        self.enabled = False

    def get_help_text(self) -> str:
        """Get help text for all shortcuts."""
        help_lines = ["Keyboard Shortcuts:", ""]

        descriptions = {
            '<space>': "Pause/Resume monitoring",
            'f': "Submit feedback",
            'h': "Hide/Show window",
            'd': "Toggle debug mode",
            'r': "Refresh detection",
            '1-5': "Quick rating (1=worst, 5=best)"
        }

        for key, action in descriptions.items():
            help_lines.append(f"  {key:<10} {action}")

        return "\n".join(help_lines)


# ============================================================================
# WINDOW MANAGEMENT
# ============================================================================

class WindowManager:
    """
    Advanced window management with snap, persistence, and transparency.

    HIGH IMPACT: Provides flexible window control.
    """

    def __init__(self, window: tk.Tk, config_file: Optional[Path] = None):
        """Initialize window manager."""
        self.window = window
        self.config_file = config_file or Path.home() / '.pokertool_window.json'
        self.snap_threshold = 20  # pixels

        # Bind events
        self.window.bind('<ButtonPress-1>', self._start_move)
        self.window.bind('<B1-Motion>', self._on_move)
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)

        # Load saved position
        self.load_position()

    def _start_move(self, event):
        """Start window move."""
        self.window._drag_start_x = event.x
        self.window._drag_start_y = event.y

    def _on_move(self, event):
        """Handle window move with edge snapping."""
        # Calculate new position
        x = self.window.winfo_x() + event.x - self.window._drag_start_x
        y = self.window.winfo_y() + event.y - self.window._drag_start_y

        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Snap to edges
        if x < self.snap_threshold:
            x = 0
        elif x + window_width > screen_width - self.snap_threshold:
            x = screen_width - window_width

        if y < self.snap_threshold:
            y = 0
        elif y + window_height > screen_height - self.snap_threshold:
            y = screen_height - window_height

        # Move window
        self.window.geometry(f"+{x}+{y}")

    def _on_close(self):
        """Handle window close - save position."""
        self.save_position()
        self.window.destroy()

    def save_position(self):
        """Save window position and size."""
        config = {
            'x': self.window.winfo_x(),
            'y': self.window.winfo_y(),
            'width': self.window.winfo_width(),
            'height': self.window.winfo_height()
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save window position: {e}")

    def load_position(self):
        """Load saved window position and size."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            # Validate position is on screen
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            x = max(0, min(config['x'], screen_width - config['width']))
            y = max(0, min(config['y'], screen_height - config['height']))

            self.window.geometry(f"{config['width']}x{config['height']}+{x}+{y}")
        except Exception as e:
            print(f"Failed to load window position: {e}")

    def set_transparency(self, alpha: float):
        """Set window transparency (0.0 = invisible, 1.0 = opaque)."""
        alpha = max(0.0, min(1.0, alpha))
        self.window.attributes('-alpha', alpha)

    def set_always_on_top(self, on_top: bool):
        """Set always-on-top state."""
        self.window.attributes('-topmost', on_top)


# ============================================================================
# LOADING STATES
# ============================================================================

class LoadingState(ttk.Frame):
    """
    Loading state indicator with skeleton screens.

    HIGH IMPACT: Provides immediate feedback during operations.
    """

    def __init__(self, parent: tk.Widget, message: str = "Loading...", **kwargs):
        """Initialize loading state."""
        super().__init__(parent, **kwargs)

        # Spinner
        self.spinner_label = tk.Label(
            self,
            text="⏳",
            font=("Arial", 24),
            fg=SemanticColors.NEUTRAL
        )
        self.spinner_label.pack(pady=10)

        # Message
        self.message_label = tk.Label(
            self,
            text=message,
            font=("Arial", 12),
            fg=SemanticColors.TEXT_SECONDARY
        )
        self.message_label.pack()

        # Start spinner animation
        self._animate_spinner()

    def _animate_spinner(self):
        """Animate the spinner."""
        spinners = ["⏳", "⌛"]
        current = self.spinner_label['text']
        next_spinner = spinners[(spinners.index(current) + 1) % len(spinners)]
        self.spinner_label.config(text=next_spinner)

        # Continue animation
        self.after(500, self._animate_spinner)

    def update_message(self, message: str):
        """Update the loading message."""
        self.message_label.config(text=message)


class SkeletonLoader(tk.Canvas):
    """Skeleton screen loader for content placeholders."""

    def __init__(self, parent: tk.Widget, width: int, height: int, **kwargs):
        """Initialize skeleton loader."""
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=SemanticColors.BG_SECONDARY,
            highlightthickness=0,
            **kwargs
        )

        # Draw skeleton rectangles
        self._draw_skeleton()

        # Animate pulsing
        self._animate_pulse()

    def _draw_skeleton(self):
        """Draw skeleton placeholder shapes."""
        # Title bar
        self.create_rectangle(
            10, 10, 200, 30,
            fill=SemanticColors.BG_DARK,
            outline=""
        )

        # Content lines
        for i in range(3):
            y = 50 + i * 30
            width = 250 - i * 30
            self.create_rectangle(
                10, y, width, y + 15,
                fill=SemanticColors.BG_DARK,
                outline=""
            )

    def _animate_pulse(self):
        """Animate pulsing effect."""
        # Simple opacity animation would go here
        # For now just a placeholder
        self.after(1000, self._animate_pulse)


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

if __name__ == '__main__':
    """Demonstrate UI enhancements."""

    root = tk.Tk()
    root.title("PokerTool UI Enhancements Demo")
    root.geometry("400x600")
    root.configure(bg=SemanticColors.BG_PRIMARY)

    # Demo container
    container = ttk.Frame(root)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Detection Status Panel
    status_panel = DetectionStatusPanel(container)
    status_panel.pack(fill=tk.X, pady=10)

    # Update with demo data
    demo_status = DetectionStatus(
        table_detected=True,
        fps=30.5,
        pot_confidence=0.85,
        cards_confidence=0.92,
        blinds_confidence=0.78,
        learning_active=True,
        cdp_connected=True
    )
    status_panel.update_status(demo_status)

    # Feedback Panel
    feedback_panel = FeedbackPanel(
        container,
        on_feedback=lambda f: print(f"Feedback: {f}")
    )
    feedback_panel.pack(fill=tk.X, pady=10)

    # Loading State Demo
    loading_frame = ttk.Frame(container)
    loading_frame.pack(fill=tk.BOTH, expand=True, pady=10)

    loading = LoadingState(loading_frame, message="Analyzing hand...")
    loading.pack()

    # Keyboard shortcuts
    shortcuts = KeyboardShortcutManager(root)
    shortcuts.register('h', lambda: print("Toggle window"))
    shortcuts.register('d', lambda: print("Debug mode"))

    # Window management
    window_mgr = WindowManager(root)

    # Shortcuts help
    help_text = shortcuts.get_help_text()
    help_label = tk.Label(
        container,
        text=help_text,
        font=("Courier", 9),
        fg=SemanticColors.TEXT_SECONDARY,
        justify=tk.LEFT,
        bg=SemanticColors.BG_SECONDARY,
        padx=10,
        pady=10
    )
    help_label.pack(fill=tk.X, pady=10)

    root.mainloop()
