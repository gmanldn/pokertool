#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Floating Advice Window for PokerTool
=====================================

A simple, reliable floating window that tells the player exactly what to do
using all available knowledge (GTO solver, EV calculator, confidence API).

Features:
- Always-on-top window with clean, minimal UI
- Primary action recommendation (FOLD/CALL/RAISE)
- Confidence level with visual bar
- Supporting information (pot odds, EV, hand strength)
- Brief reasoning text
- Update throttling (max 2 updates/second)
- Window positioning/sizing preferences

ENHANCED VERSION 2.0:
- Live detection status panel
- One-click feedback system
- Keyboard shortcuts
- Multi-level information hierarchy
- Profile system integration
- Performance tracking

Version: 2.0.0
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class ActionType(Enum):
    """Primary poker actions."""
    FOLD = "FOLD"
    CALL = "CALL"
    RAISE = "RAISE"
    CHECK = "CHECK"
    ALL_IN = "ALL-IN"


class ConfidenceLevel(Enum):
    """Confidence levels for recommendations."""
    VERY_HIGH = ("VERY HIGH", "#00C853", 0.9)    # Green
    HIGH = ("HIGH", "#64DD17", 0.75)             # Light green
    MEDIUM = ("MEDIUM", "#FFD600", 0.6)          # Yellow
    LOW = ("LOW", "#FF6D00", 0.4)                # Orange
    VERY_LOW = ("VERY LOW", "#DD2C00", 0.0)      # Red

    def __init__(self, label: str, color: str, threshold: float):
        self.label = label
        self.color = color
        self.threshold = threshold

    @classmethod
    def from_confidence(cls, confidence: float) -> ConfidenceLevel:
        """Get confidence level from numeric confidence."""
        if confidence >= 0.9:
            return cls.VERY_HIGH
        elif confidence >= 0.75:
            return cls.HIGH
        elif confidence >= 0.6:
            return cls.MEDIUM
        elif confidence >= 0.4:
            return cls.LOW
        else:
            return cls.VERY_LOW


@dataclass
class Advice:
    """Poker advice recommendation."""
    action: ActionType
    confidence: float  # 0-1
    amount: Optional[float] = None  # For RAISE/BET
    ev: Optional[float] = None  # Expected value
    pot_odds: Optional[float] = None  # Pot odds (0-1)
    hand_strength: Optional[float] = None  # Hand strength (0-1)
    reasoning: str = ""
    timestamp: float = 0.0


class FloatingAdviceWindow:
    """
    Floating advice window that shows real-time poker recommendations.

    Always-on-top window with clean UI showing:
    - Primary action (FOLD/CALL/RAISE)
    - Confidence level with visual bar
    - Supporting information
    - Brief reasoning
    """

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        width: int = 350,
        height: int = 250
    ):
        """
        Initialize the floating advice window.

        Args:
            parent: Parent window (None for standalone)
            width: Window width in pixels
            height: Window height in pixels
        """
        # Create window
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("PokerTool Advice")
        self.window.geometry(f"{width}x{height}")

        # Set always on top
        self.window.attributes('-topmost', True)

        # Make window stay on top but allow interaction with other windows
        try:
            # macOS specific
            self.window.attributes('-type', 'utility')
        except:
            pass

        # Current advice
        self.current_advice: Optional[Advice] = None
        self.last_update_time: float = 0.0
        self.update_throttle: float = 0.5  # Max 2 updates per second

        # Create UI
        self._create_ui()

        # Position window
        self._position_window()

    def _create_ui(self):
        """Create the UI elements."""
        # Main container with card-like appearance
        self.main_frame = ttk.Frame(self.window, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header: Action label
        self.action_label = tk.Label(
            self.main_frame,
            text="WAITING...",
            font=("Arial", 36, "bold"),
            fg="#666666",
            bg="#f5f5f5"
        )
        self.action_label.pack(pady=(0, 10))

        # Amount label (for RAISE)
        self.amount_label = tk.Label(
            self.main_frame,
            text="",
            font=("Arial", 20, "bold"),
            fg="#333333"
        )
        self.amount_label.pack()

        # Confidence frame
        confidence_frame = ttk.Frame(self.main_frame)
        confidence_frame.pack(fill=tk.X, pady=10)

        # Confidence label
        self.confidence_label = tk.Label(
            confidence_frame,
            text="Confidence: --",
            font=("Arial", 12),
            fg="#666666"
        )
        self.confidence_label.pack()

        # Confidence progress bar
        self.confidence_bar = ttk.Progressbar(
            confidence_frame,
            length=300,
            mode='determinate'
        )
        self.confidence_bar.pack(pady=5)

        # Supporting info frame
        info_frame = ttk.Frame(self.main_frame)
        info_frame.pack(fill=tk.X, pady=5)

        # Grid layout for info
        self.ev_label = tk.Label(
            info_frame,
            text="EV: --",
            font=("Arial", 10),
            fg="#444444"
        )
        self.ev_label.grid(row=0, column=0, sticky="w")

        self.pot_odds_label = tk.Label(
            info_frame,
            text="Pot Odds: --",
            font=("Arial", 10),
            fg="#444444"
        )
        self.pot_odds_label.grid(row=0, column=1, sticky="e")

        self.hand_strength_label = tk.Label(
            info_frame,
            text="Hand: --",
            font=("Arial", 10),
            fg="#444444"
        )
        self.hand_strength_label.grid(row=1, column=0, sticky="w", columnspan=2)

        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)

        # Reasoning text
        self.reasoning_text = tk.Text(
            self.main_frame,
            height=3,
            wrap=tk.WORD,
            font=("Arial", 9),
            fg="#555555",
            bg="#f9f9f9",
            relief=tk.FLAT,
            padx=5,
            pady=5
        )
        self.reasoning_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.reasoning_text.config(state=tk.DISABLED)

        # Set window background
        self.window.configure(bg="#f5f5f5")
        self.main_frame.configure(style="Card.TFrame")

        # Configure styles
        style = ttk.Style()
        style.configure("Card.TFrame", background="#f5f5f5")

    def _position_window(self):
        """Position window at top-right of screen."""
        # Update window to get actual size
        self.window.update_idletasks()

        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Get window dimensions
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()

        # Position at top-right with 20px margin
        x = screen_width - window_width - 20
        y = 20

        self.window.geometry(f"+{x}+{y}")

    def update_advice(self, advice: Advice):
        """
        Update the displayed advice.

        Args:
            advice: New advice to display
        """
        # Throttle updates
        current_time = time.time()
        if current_time - self.last_update_time < self.update_throttle:
            return

        self.current_advice = advice
        self.last_update_time = current_time

        # Update action
        action_text = advice.action.value
        if advice.amount and advice.action == ActionType.RAISE:
            action_text = f"{advice.action.value} ${advice.amount:.0f}"

        # Get confidence level
        conf_level = ConfidenceLevel.from_confidence(advice.confidence)

        # Update action label
        self.action_label.config(
            text=action_text,
            fg=conf_level.color
        )

        # Update amount label
        if advice.amount and advice.action == ActionType.RAISE:
            self.amount_label.config(text=f"${advice.amount:.0f}")
        else:
            self.amount_label.config(text="")

        # Update confidence
        self.confidence_label.config(
            text=f"Confidence: {conf_level.label} ({advice.confidence*100:.0f}%)"
        )
        self.confidence_bar['value'] = advice.confidence * 100

        # Update EV
        if advice.ev is not None:
            ev_text = f"EV: ${advice.ev:.2f}" if advice.ev >= 0 else f"EV: -${abs(advice.ev):.2f}"
            ev_color = "#00C853" if advice.ev >= 0 else "#DD2C00"
            self.ev_label.config(text=ev_text, fg=ev_color)
        else:
            self.ev_label.config(text="EV: --")

        # Update pot odds
        if advice.pot_odds is not None:
            self.pot_odds_label.config(text=f"Pot Odds: {advice.pot_odds*100:.0f}%")
        else:
            self.pot_odds_label.config(text="Pot Odds: --")

        # Update hand strength
        if advice.hand_strength is not None:
            self.hand_strength_label.config(text=f"Hand Strength: {advice.hand_strength*100:.0f}%")
        else:
            self.hand_strength_label.config(text="Hand: --")

        # Update reasoning
        self.reasoning_text.config(state=tk.NORMAL)
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(1.0, advice.reasoning or "Waiting for analysis...")
        self.reasoning_text.config(state=tk.DISABLED)

    def clear_advice(self):
        """Clear the displayed advice."""
        self.action_label.config(text="WAITING...", fg="#666666")
        self.amount_label.config(text="")
        self.confidence_label.config(text="Confidence: --")
        self.confidence_bar['value'] = 0
        self.ev_label.config(text="EV: --")
        self.pot_odds_label.config(text="Pot Odds: --")
        self.hand_strength_label.config(text="Hand: --")
        self.reasoning_text.config(state=tk.NORMAL)
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(1.0, "Waiting for table detection...")
        self.reasoning_text.config(state=tk.DISABLED)

    def show(self):
        """Show the window."""
        self.window.deiconify()

    def hide(self):
        """Hide the window."""
        self.window.withdraw()

    def destroy(self):
        """Destroy the window."""
        self.window.destroy()

    def mainloop(self):
        """Start the window main loop (for standalone mode)."""
        self.window.mainloop()


def demo():
    """Demo the floating advice window."""
    import random

    window = FloatingAdviceWindow()

    def update_random_advice():
        """Update with random advice for demo."""
        actions = [ActionType.FOLD, ActionType.CALL, ActionType.RAISE]
        action = random.choice(actions)

        advice = Advice(
            action=action,
            confidence=random.uniform(0.4, 0.95),
            amount=random.uniform(20, 200) if action == ActionType.RAISE else None,
            ev=random.uniform(-50, 50),
            pot_odds=random.uniform(0.2, 0.4),
            hand_strength=random.uniform(0.3, 0.9),
            reasoning=f"{'Strong' if action != ActionType.FOLD else 'Weak'} hand against opponent range. "
                     f"{'Good' if action != ActionType.FOLD else 'Poor'} pot odds."
        )

        window.update_advice(advice)

        # Schedule next update
        window.window.after(2000, update_random_advice)

    # Start with initial advice
    window.window.after(1000, update_random_advice)

    window.mainloop()


# ============================================================================
# ENHANCED VERSION INTEGRATION
# ============================================================================

# Try to import enhanced version with all improvements
try:
    from .enhanced_floating_window import (
        EnhancedFloatingAdviceWindow,
        AdviceData,
        InformationLevel
    )
    from .ui_enhancements import DetectionStatus
    from .ui_profiles_dashboard import ProfileManager, PlayStyle

    ENHANCED_AVAILABLE = True

    # Create convenience alias
    FloatingAdviceWindowV2 = EnhancedFloatingAdviceWindow

except ImportError as e:
    ENHANCED_AVAILABLE = False
    # Keep using basic version
    FloatingAdviceWindowV2 = FloatingAdviceWindow


if __name__ == '__main__':
    print("Starting Floating Advice Window demo...")
    print(f"Enhanced version available: {ENHANCED_AVAILABLE}")
    demo()
