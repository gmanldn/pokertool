#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Floating Advice Window
================================

Upgraded floating window with all high-impact UI improvements:
- Detection status panel
- One-click feedback
- Keyboard shortcuts
- Window management
- Semantic colors
- Loading states
- Multi-level information hierarchy

Version: 2.0.0
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time

from .ui_enhancements import (
    SemanticColors,
    DetectionStatusPanel,
    DetectionStatus,
    FeedbackPanel,
    KeyboardShortcutManager,
    WindowManager,
    LoadingState
)


class InformationLevel(Enum):
    """Information display levels."""
    SUMMARY = "summary"        # Just action + confidence
    EXPANDED = "expanded"       # + reasoning + metrics
    EXPERT = "expert"           # + all technical details


@dataclass
class AdviceData:
    """Complete advice data structure."""
    # Core recommendation
    action: str
    confidence: float
    amount: Optional[float] = None

    # Metrics
    ev: Optional[float] = None
    pot_odds: Optional[float] = None
    hand_strength: Optional[float] = None

    # Explanation
    reasoning: str = ""

    # Technical details
    detection_quality: Optional[Dict] = None
    alternative_actions: Optional[List] = None
    gto_comparison: Optional[Dict] = None

    timestamp: float = 0.0


class EnhancedFloatingAdviceWindow:
    """
    Enhanced floating advice window with all high-impact improvements.

    Features:
    - Multi-level information display
    - Live detection status
    - One-click feedback
    - Keyboard shortcuts
    - Smart window management
    - Semantic color system
    - Loading states
    """

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        width: int = 400,
        height: int = 650,
        on_feedback: Optional[Callable] = None
    ):
        """Initialize enhanced floating window."""

        # Create window
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()

        self.window.title("PokerTool Enhanced Advice")
        self.window.geometry(f"{width}x{height}")

        # Set always on top
        self.window.attributes('-topmost', True)

        # macOS specific
        try:
            self.window.attributes('-type', 'utility')
        except:
            pass

        # State
        self.current_advice: Optional[AdviceData] = None
        self.information_level = InformationLevel.EXPANDED
        self.is_paused = False
        self.show_status_panel = True
        self.on_feedback = on_feedback

        # Window management
        self.window_manager = WindowManager(self.window)

        # Keyboard shortcuts
        self.shortcuts = KeyboardShortcutManager(self.window)
        self._setup_shortcuts()

        # Create UI
        self._create_ui()

        # Apply default styling
        self.window.configure(bg=SemanticColors.BG_PRIMARY)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.shortcuts.register('<space>', self.toggle_pause)
        self.shortcuts.register('h', self.toggle_window)
        self.shortcuts.register('d', self.toggle_status_panel)
        self.shortcuts.register('i', self.cycle_information_level)
        self.shortcuts.register('f', self._quick_feedback_good)
        self.shortcuts.register('1', lambda: self._quick_rating(1))
        self.shortcuts.register('2', lambda: self._quick_rating(2))
        self.shortcuts.register('3', lambda: self._quick_rating(3))
        self.shortcuts.register('4', lambda: self._quick_rating(4))
        self.shortcuts.register('5', lambda: self._quick_rating(5))

    def _create_ui(self):
        """Create the enhanced UI."""
        # Main container with scrolling
        self.main_container = ttk.Frame(self.window)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Create canvas for scrolling
        self.canvas = tk.Canvas(
            self.main_container,
            bg=SemanticColors.BG_PRIMARY,
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.main_container,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Detection Status Panel
        self.status_panel = DetectionStatusPanel(self.scrollable_frame)
        self.status_panel.pack(fill=tk.X, padx=10, pady=10)

        # Separator
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=10)

        # Action recommendation section
        self._create_action_section()

        # Metrics section
        self._create_metrics_section()

        # Reasoning section
        self._create_reasoning_section()

        # Expert details section (initially hidden)
        self._create_expert_section()

        # Feedback section
        self.feedback_panel = FeedbackPanel(
            self.scrollable_frame,
            on_feedback=self._handle_feedback
        )
        self.feedback_panel.pack(fill=tk.X, padx=10, pady=10)

        # Controls section
        self._create_controls_section()

    def _create_action_section(self):
        """Create the main action recommendation section."""
        action_frame = ttk.Frame(self.scrollable_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        # Action label (large, prominent)
        self.action_label = tk.Label(
            action_frame,
            text="WAITING...",
            font=("Arial", 36, "bold"),
            fg=SemanticColors.TEXT_SECONDARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.action_label.pack(pady=(0, 10))

        # Amount label (for RAISE)
        self.amount_label = tk.Label(
            action_frame,
            text="",
            font=("Arial", 20, "bold"),
            fg=SemanticColors.TEXT_PRIMARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.amount_label.pack()

        # Confidence bar with label
        conf_container = ttk.Frame(action_frame)
        conf_container.pack(fill=tk.X, pady=10)

        self.confidence_label = tk.Label(
            conf_container,
            text="Confidence: --",
            font=("Arial", 12),
            fg=SemanticColors.TEXT_SECONDARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.confidence_label.pack()

        self.confidence_bar = ttk.Progressbar(
            conf_container,
            length=350,
            mode='determinate'
        )
        self.confidence_bar.pack(pady=5)

    def _create_metrics_section(self):
        """Create the metrics display section."""
        self.metrics_frame = ttk.Frame(self.scrollable_frame)
        self.metrics_frame.pack(fill=tk.X, padx=10, pady=10)

        # Grid layout
        metrics_grid = ttk.Frame(self.metrics_frame)
        metrics_grid.pack(fill=tk.X)

        # EV
        self.ev_label = tk.Label(
            metrics_grid,
            text="EV: --",
            font=("Arial", 11),
            fg=SemanticColors.TEXT_PRIMARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.ev_label.grid(row=0, column=0, sticky="w", padx=5, pady=3)

        # Pot Odds
        self.pot_odds_label = tk.Label(
            metrics_grid,
            text="Pot Odds: --",
            font=("Arial", 11),
            fg=SemanticColors.TEXT_PRIMARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.pot_odds_label.grid(row=0, column=1, sticky="e", padx=5, pady=3)

        # Hand Strength
        self.hand_strength_label = tk.Label(
            metrics_grid,
            text="Hand Strength: --",
            font=("Arial", 11),
            fg=SemanticColors.TEXT_PRIMARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.hand_strength_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=3)

        metrics_grid.columnconfigure(0, weight=1)
        metrics_grid.columnconfigure(1, weight=1)

    def _create_reasoning_section(self):
        """Create the reasoning text section."""
        self.reasoning_frame = ttk.Frame(self.scrollable_frame)
        self.reasoning_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        reasoning_title = tk.Label(
            self.reasoning_frame,
            text="Reasoning",
            font=("Arial", 10, "bold"),
            fg=SemanticColors.TEXT_SECONDARY,
            bg=SemanticColors.BG_PRIMARY,
            anchor="w"
        )
        reasoning_title.pack(anchor="w")

        # Text widget
        self.reasoning_text = tk.Text(
            self.reasoning_frame,
            height=4,
            wrap=tk.WORD,
            font=("Arial", 10),
            fg=SemanticColors.TEXT_PRIMARY,
            bg=SemanticColors.BG_SECONDARY,
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.reasoning_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.reasoning_text.config(state=tk.DISABLED)

    def _create_expert_section(self):
        """Create the expert details section."""
        self.expert_frame = ttk.Frame(self.scrollable_frame)
        # Initially not packed - only shown in expert mode

        # Title
        expert_title = tk.Label(
            self.expert_frame,
            text="Expert Details",
            font=("Arial", 10, "bold"),
            fg=SemanticColors.TEXT_SECONDARY,
            bg=SemanticColors.BG_PRIMARY,
            anchor="w"
        )
        expert_title.pack(anchor="w", padx=10, pady=(10, 5))

        # Details text
        self.expert_text = tk.Text(
            self.expert_frame,
            height=6,
            wrap=tk.WORD,
            font=("Courier", 9),
            fg=SemanticColors.TEXT_SECONDARY,
            bg=SemanticColors.BG_SECONDARY,
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.expert_text.pack(fill=tk.BOTH, expand=True, padx=10)
        self.expert_text.config(state=tk.DISABLED)

    def _create_controls_section(self):
        """Create controls and status section."""
        controls_frame = ttk.Frame(self.scrollable_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=10)

        # Info level indicator
        self.level_label = tk.Label(
            controls_frame,
            text="Press 'i' to change detail level",
            font=("Arial", 9),
            fg=SemanticColors.TEXT_SECONDARY,
            bg=SemanticColors.BG_PRIMARY
        )
        self.level_label.pack()

        # Pause indicator
        self.pause_label = tk.Label(
            controls_frame,
            text="",
            font=("Arial", 9, "bold"),
            fg=SemanticColors.CAUTION,
            bg=SemanticColors.BG_PRIMARY
        )
        self.pause_label.pack()

    def update_advice(self, advice: AdviceData):
        """Update the window with new advice."""
        if self.is_paused:
            return

        self.current_advice = advice

        # Update action
        self.action_label.config(
            text=advice.action,
            fg=self._get_action_color(advice.action)
        )

        # Update amount
        if advice.amount:
            self.amount_label.config(text=f"${advice.amount:.2f}")
        else:
            self.amount_label.config(text="")

        # Update confidence
        conf_color = SemanticColors.get_confidence_color(advice.confidence)
        self.confidence_label.config(
            text=f"Confidence: {advice.confidence:.0%}",
            fg=conf_color
        )
        self.confidence_bar['value'] = advice.confidence * 100

        # Update metrics
        if advice.ev is not None:
            ev_color = SemanticColors.POSITIVE if advice.ev > 0 else SemanticColors.NEGATIVE
            self.ev_label.config(
                text=f"EV: ${advice.ev:+.2f}",
                fg=ev_color
            )

        if advice.pot_odds is not None:
            self.pot_odds_label.config(text=f"Pot Odds: {advice.pot_odds:.1%}")

        if advice.hand_strength is not None:
            self.hand_strength_label.config(text=f"Hand Strength: {advice.hand_strength:.0%}")

        # Update reasoning
        self.reasoning_text.config(state=tk.NORMAL)
        self.reasoning_text.delete('1.0', tk.END)
        self.reasoning_text.insert('1.0', advice.reasoning or "Analyzing...")
        self.reasoning_text.config(state=tk.DISABLED)

        # Update expert details if available
        if advice.detection_quality:
            self._update_expert_details(advice)

        # Show/hide sections based on information level
        self._update_information_level()

    def _get_action_color(self, action: str) -> str:
        """Get color for action."""
        action = action.upper()
        if action in ['FOLD']:
            return SemanticColors.NEGATIVE
        elif action in ['CALL', 'CHECK']:
            return SemanticColors.CAUTION
        elif action in ['RAISE', 'BET', 'ALL-IN']:
            return SemanticColors.POSITIVE
        return SemanticColors.NEUTRAL

    def _update_expert_details(self, advice: AdviceData):
        """Update expert details section."""
        self.expert_text.config(state=tk.NORMAL)
        self.expert_text.delete('1.0', tk.END)

        details = []

        if advice.detection_quality:
            details.append("Detection Quality:")
            for key, value in advice.detection_quality.items():
                details.append(f"  {key}: {value}")

        if advice.alternative_actions:
            details.append("\nAlternative Actions:")
            for alt in advice.alternative_actions:
                details.append(f"  {alt}")

        if advice.gto_comparison:
            details.append("\nGTO Comparison:")
            for key, value in advice.gto_comparison.items():
                details.append(f"  {key}: {value}")

        self.expert_text.insert('1.0', '\n'.join(details))
        self.expert_text.config(state=tk.DISABLED)

    def _update_information_level(self):
        """Update UI based on information level."""
        if self.information_level == InformationLevel.SUMMARY:
            # Hide everything except action and confidence
            self.metrics_frame.pack_forget()
            self.reasoning_frame.pack_forget()
            self.expert_frame.pack_forget()

        elif self.information_level == InformationLevel.EXPANDED:
            # Show metrics and reasoning
            self.metrics_frame.pack(fill=tk.X, padx=10, pady=10)
            self.reasoning_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.expert_frame.pack_forget()

        elif self.information_level == InformationLevel.EXPERT:
            # Show everything
            self.metrics_frame.pack(fill=tk.X, padx=10, pady=10)
            self.reasoning_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.expert_frame.pack(fill=tk.BOTH, expand=True)

        self.level_label.config(
            text=f"Detail Level: {self.information_level.value.upper()} (press 'i' to change)"
        )

    def update_detection_status(self, status: DetectionStatus):
        """Update detection status panel."""
        self.status_panel.update_status(status)

    def toggle_pause(self):
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_label.config(text="⏸ PAUSED (press SPACE to resume)")
        else:
            self.pause_label.config(text="")

    def toggle_window(self):
        """Toggle window visibility."""
        if self.window.state() == 'withdrawn':
            self.window.deiconify()
        else:
            self.window.withdraw()

    def toggle_status_panel(self):
        """Toggle status panel visibility."""
        self.show_status_panel = not self.show_status_panel
        if self.show_status_panel:
            self.status_panel.pack(fill=tk.X, padx=10, pady=10, before=self.metrics_frame)
        else:
            self.status_panel.pack_forget()

    def cycle_information_level(self):
        """Cycle through information levels."""
        levels = list(InformationLevel)
        current_idx = levels.index(self.information_level)
        next_idx = (current_idx + 1) % len(levels)
        self.information_level = levels[next_idx]
        self._update_information_level()

    def _handle_feedback(self, feedback_type: str):
        """Handle feedback submission."""
        if self.on_feedback:
            feedback_data = {
                'type': feedback_type,
                'advice': self.current_advice,
                'timestamp': time.time()
            }
            self.on_feedback(feedback_data)

    def _quick_feedback_good(self):
        """Quick positive feedback via keyboard."""
        self._handle_feedback('helpful')

    def _quick_rating(self, rating: int):
        """Quick rating via keyboard (1-5)."""
        self._handle_feedback(f'rating_{rating}')

    def show_loading(self, message: str = "Analyzing..."):
        """Show loading state."""
        # Clear existing content temporarily
        for widget in self.scrollable_frame.winfo_children():
            widget.pack_forget()

        loading = LoadingState(self.scrollable_frame, message=message)
        loading.pack(expand=True)

    def run(self):
        """Run the window."""
        self.window.mainloop()


# ============================================================================
# DEMO
# ============================================================================

if __name__ == '__main__':
    """Demo the enhanced floating window."""

    def on_feedback(data):
        print(f"Feedback received: {data}")

    # Create window
    window = EnhancedFloatingAdviceWindow(on_feedback=on_feedback)

    # Update with demo detection status
    demo_status = DetectionStatus(
        table_detected=True,
        fps=28.3,
        pot_confidence=0.87,
        cards_confidence=0.94,
        blinds_confidence=0.81,
        learning_active=True,
        cdp_connected=True
    )
    window.update_detection_status(demo_status)

    # Update with demo advice
    demo_advice = AdviceData(
        action="RAISE",
        confidence=0.88,
        amount=15.50,
        ev=2.35,
        pot_odds=0.28,
        hand_strength=0.72,
        reasoning="You have a strong top pair with good kicker. The pot odds are favorable and you're likely ahead of villain's range. A value raise here maximizes your EV.",
        detection_quality={
            'pot_ocr': 0.87,
            'cards_ocr': 0.94,
            'table_detection': 0.96
        },
        alternative_actions=['CALL (EV: +$1.20)', 'FOLD (EV: -$5.00)'],
        gto_comparison={'gto_action': 'RAISE', 'your_action': 'RAISE', 'alignment': '100%'}
    )
    window.update_advice(demo_advice)

    # Run
    window.run()
