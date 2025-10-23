#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LiveTable section for the enhanced GUI with real-time scraper data display."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Any, Optional, Dict, List

from .style import COLORS, FONTS

# Performance telemetry
try:
    from ..performance_telemetry import telemetry_section, telemetry_instant
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    # No-op fallback
    from contextlib import contextmanager
    @contextmanager
    def telemetry_section(cat, op, det=None):
        yield
    def telemetry_instant(cat, op, det=None):
        pass

# Import detailed advice explainer
try:
    from ..detailed_advice_explainer import get_detailed_explainer
    EXPLAINER_AVAILABLE = True
except ImportError:
    EXPLAINER_AVAILABLE = False
    print("[LiveTableSection] Warning: detailed_advice_explainer not available")


class LiveTableSection:
    """Encapsulates the LiveTable tab with real-time scraper data display."""

    def __init__(self, host: Any, parent: tk.Misc, *, modules_loaded: bool) -> None:
        telemetry_instant('ui', 'live_table_section_init')
        print("[LiveTableSection] __init__ called")
        self.host = host
        self.parent = parent
        self._modules_loaded = modules_loaded
        print(f"[LiveTableSection] Host type: {type(host).__name__}")
        print(f"[LiveTableSection] Host has get_live_table_data: {hasattr(host, 'get_live_table_data')}")

        # Live table data display widgets
        self.live_data_frame: Optional[tk.Frame] = None
        self.table_canvas: Optional[tk.Canvas] = None
        self.player_labels: Dict[int, Dict[str, tk.Label]] = {}
        self.board_labels: List[tk.Label] = []
        self.blinds_label: Optional[tk.Label] = None
        self.ante_label: Optional[tk.Label] = None
        self.pot_label: Optional[tk.Label] = None
        self.dealer_button_label: Optional[tk.Label] = None
        self.table_status_label: Optional[tk.Label] = None
        self.recommended_action_label: Optional[tk.Label] = None
        self.detailed_explanation_label: Optional[tk.Label] = None
        self.my_cards_labels: List[tk.Label] = []

        # User's handle for position identification
        self.user_handle: str = ""
        self.user_seat: int = 1  # Default to seat 1

        # Update control
        self._update_thread: Optional[threading.Thread] = None
        self._stop_updates = False

        # Detection status indicators (LED lights)
        self.status_lights: Dict[str, tk.Label] = {}

        self._build_ui()
        # Use main thread callbacks for thread-safe updates (fixes segfault issue)
        self.parent.after(1000, self._start_main_thread_updates)
        # Handle prompt disabled - user can configure handle in settings if needed
        # self.parent.after(3000, self._prompt_for_handle)

    # ------------------------------------------------------------------
    def _prompt_for_handle(self) -> None:
        """Prompt user for their poker handle on startup."""
        try:
            from tkinter import simpledialog

            # Use simpledialog to ask for handle
            self.user_handle = simpledialog.askstring(
                "Player Handle",
                "Enter your poker handle/username:\n(This helps identify your position at the table)",
                parent=self.parent
            )

            if not self.user_handle:
                self.user_handle = ""  # Empty if cancelled
            else:
                self.user_handle = self.user_handle.strip()
                print(f"User handle set to: {self.user_handle}")
        except Exception as e:
            print(f"[LiveTableSection] Could not prompt for handle: {e}")
            self.user_handle = ""  # Use empty if prompt fails

    def _build_ui(self) -> None:
        with telemetry_section('ui', 'live_table_build_ui'):
            print("[LiveTableSection] _build_ui called")
            self._build_ui_internal()

    def _build_ui_internal(self) -> None:
        """Internal UI building implementation."""
        header_frame = tk.Frame(self.parent, bg=COLORS["bg_dark"])
        header_frame.pack(fill="x", pady=(20, 10))

        live_table_label = tk.Label(
            header_frame,
            text="🃏 LiveTable - Real-time Poker Table View",
            font=FONTS["title"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        )
        live_table_label.pack(anchor="w")

        helper_text = (
            "Live view of the detected poker table with real-time scraper data. "
            "When autopilot is active, this shows exactly what the scraper sees: "
            "player names, stacks, cards, board, blinds, ante, and dealer button."
        )
        tk.Label(
            header_frame,
            text=helper_text,
            font=FONTS["body"],
            justify="left",
            wraplength=900,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(6, 0))

        content_frame = tk.Frame(self.parent, bg=COLORS["bg_dark"])
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Detection Status Lights Panel (CRITICAL ADDITION)
        self._build_detection_status_panel(content_frame)

        # Live table data display (full width)
        self._build_live_data_panel(content_frame)

    def _build_detection_status_panel(self, parent) -> None:
        """Build compact detection status panel with LED-style indicators."""
        status_container = tk.LabelFrame(
            parent,
            text="🔍 DETECTION STATUS",
            font=("Arial", 10, "bold"),
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_info"],
            relief=tk.RAISED,
            bd=2,
        )
        status_container.pack(fill="x", pady=(0, 10))

        # Create two rows of 4 indicators each for compact layout
        indicators_config = [
            ("Players", "players"),
            ("Stacks", "stacks"),
            ("Board", "board"),
            ("Hole Cards", "hole_cards"),
            ("Dealer", "dealer"),
            ("Blinds", "blinds"),
            ("Bets", "bets"),
            ("Pot", "pot"),
        ]

        # Row 1
        row1_frame = tk.Frame(status_container, bg=COLORS["bg_medium"])
        row1_frame.pack(fill="x", padx=10, pady=(5, 2))

        # Row 2
        row2_frame = tk.Frame(status_container, bg=COLORS["bg_medium"])
        row2_frame.pack(fill="x", padx=10, pady=(2, 5))

        # Add 4 indicators to each row
        for idx, (label, key) in enumerate(indicators_config):
            target_frame = row1_frame if idx < 4 else row2_frame

            indicator_frame = tk.Frame(target_frame, bg=COLORS["bg_medium"])
            indicator_frame.pack(side="left", padx=5, expand=True)

            # LED light (circle)
            led = tk.Label(
                indicator_frame,
                text="●",
                font=("Arial", 14),
                bg=COLORS["bg_medium"],
                fg="#888888",  # Gray = unknown/inactive
                width=2
            )
            led.pack(side="left")

            # Label text
            label_widget = tk.Label(
                indicator_frame,
                text=label,
                font=("Arial", 9),
                bg=COLORS["bg_medium"],
                fg=COLORS["text_primary"]
            )
            label_widget.pack(side="left", padx=(2, 0))

            # Store LED reference for updating
            self.status_lights[key] = led

    def _build_live_data_panel(self, parent) -> None:
        """Build the live table data display panel with graphical poker table."""
        live_container = tk.LabelFrame(
            parent,
            text="🔴 LIVE POKER TABLE",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_success"],
            relief=tk.RAISED,
            bd=2,
        )
        live_container.pack(fill="both", expand=True)

        self.live_data_frame = tk.Frame(live_container, bg=COLORS["bg_dark"])
        self.live_data_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Table status with extraction method and tournament info
        status_frame = tk.Frame(self.live_data_frame, bg=COLORS["bg_dark"])
        status_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            status_frame,
            text="Table Status:",
            font=FONTS["subheading"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        self.table_status_label = tk.Label(
            status_frame,
            text="Waiting for scraper data...",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.table_status_label.pack(side="left", padx=(10, 0))

        # Tournament/Table name display
        self.tournament_label = tk.Label(
            status_frame,
            text="",
            font=("Arial", 9, "italic"),
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_info"],
        )
        self.tournament_label.pack(side="right", padx=(10, 0))

        # COMPACT TABLE INFO PANEL - Combines board, blinds, pot, and dealer
        table_info_frame = tk.LabelFrame(
            self.live_data_frame,
            text="🎴 TABLE INFO",
            font=("Arial", 14, "bold"),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=3,
        )
        table_info_frame.pack(fill="x", pady=(0, 10))

        # Main container with padding
        info_container = tk.Frame(table_info_frame, bg=COLORS["bg_medium"])
        info_container.pack(fill="x", padx=15, pady=15)

        # Top row: Blinds/Ante info on left, Dealer button on right
        top_row = tk.Frame(info_container, bg=COLORS["bg_medium"])
        top_row.pack(fill="x", pady=(0, 10))

        # Left side: Blinds and Ante
        blinds_container = tk.Frame(top_row, bg=COLORS["bg_light"], relief=tk.GROOVE, bd=2)
        blinds_container.pack(side="left", padx=(0, 10))

        tk.Label(
            blinds_container,
            text="BLINDS:",
            font=("Arial", 10, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=(10, 5))

        self.blinds_label = tk.Label(
            blinds_container,
            text="$-/$-",
            font=("Arial", 14, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["accent_warning"],
        )
        self.blinds_label.pack(side="left", padx=(0, 15))

        tk.Label(
            blinds_container,
            text="ANTE:",
            font=("Arial", 10, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=(0, 5))

        self.ante_label = tk.Label(
            blinds_container,
            text="$-",
            font=("Arial", 14, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["accent_warning"],
        )
        self.ante_label.pack(side="left", padx=(0, 10))

        # Right side: Dealer button
        dealer_container = tk.Frame(top_row, bg=COLORS["bg_light"], relief=tk.GROOVE, bd=2)
        dealer_container.pack(side="right")

        tk.Label(
            dealer_container,
            text="🔘 DEALER:",
            font=("Arial", 10, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=(10, 5))

        self.dealer_button_label = tk.Label(
            dealer_container,
            text="Seat -",
            font=("Arial", 14, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["accent_info"],
        )
        self.dealer_button_label.pack(side="left", padx=(0, 10))

        # Middle row: Board cards (centered and prominent)
        board_row = tk.Frame(info_container, bg=COLORS["bg_medium"])
        board_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            board_row,
            text="BOARD:",
            font=("Arial", 11, "bold"),
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=(0, 10))

        board_cards_frame = tk.Frame(board_row, bg="#1a1a1a", relief=tk.SUNKEN, bd=2)
        board_cards_frame.pack(side="left", padx=(0, 0))

        self.board_labels = []
        for i in range(5):  # 5 community cards max
            card_label = tk.Label(
                board_cards_frame,
                text="[ ]",
                font=("Courier", 16, "bold"),
                bg="#ffffff",
                fg="#000000",
                width=4,
                relief=tk.RAISED,
                bd=2,
            )
            card_label.pack(side="left", padx=3, pady=5)
            self.board_labels.append(card_label)

        # Bottom row: Pot display (centered and large)
        pot_row = tk.Frame(info_container, bg=COLORS["bg_medium"])
        pot_row.pack(fill="x")

        pot_container = tk.Frame(pot_row, bg=COLORS["bg_light"], relief=tk.GROOVE, bd=3)
        pot_container.pack(expand=True)

        tk.Label(
            pot_container,
            text="💰 POT:",
            font=("Arial", 12, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=(15, 5))

        self.pot_label = tk.Label(
            pot_container,
            text="$0",
            font=("Arial", 18, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["accent_success"],
        )
        self.pot_label.pack(side="left", padx=(0, 15))

        # Graphical poker table section
        table_canvas_frame = tk.Frame(self.live_data_frame, bg=COLORS["table_felt"])
        table_canvas_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Create canvas for the poker table
        self.table_canvas = tk.Canvas(
            table_canvas_frame,
            bg=COLORS["table_felt"],
            highlightthickness=2,
            highlightbackground=COLORS["table_border"],
            width=800,
            height=500
        )
        self.table_canvas.pack(fill="both", expand=True, padx=5, pady=5)

        # Draw the poker table (oval shape)
        self._draw_poker_table()

        # Initialize player display positions around the table (10 seats)
        self.player_labels = {}
        self._create_graphical_player_positions()

        # My cards section
        my_cards_frame = tk.LabelFrame(
            self.live_data_frame,
            text="🎴 My Hole Cards",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        my_cards_frame.pack(fill="x", pady=(0, 10))

        cards_display = tk.Frame(my_cards_frame, bg=COLORS["bg_medium"])
        cards_display.pack(pady=10)

        self.my_cards_labels = []
        for i in range(2):
            card_label = tk.Label(
                cards_display,
                text="[ ]",
                font=("Courier", 16, "bold"),
                bg=COLORS["bg_light"],
                fg=COLORS["accent_success"],
                width=5,
                relief=tk.RAISED,
                bd=2,
            )
            card_label.pack(side="left", padx=5)
            self.my_cards_labels.append(card_label)

        # Recommended action box
        action_frame = tk.LabelFrame(
            self.live_data_frame,
            text="💡 RECOMMENDED ACTION",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_info"],
            relief=tk.RAISED,
            bd=3,
        )
        action_frame.pack(fill="x", pady=(0, 10))

        self.recommended_action_label = tk.Label(
            action_frame,
            text="Waiting for game state...",
            font=("Helvetica", 14, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_warning"],
            wraplength=450,
            justify="center",
            relief=tk.SUNKEN,
            bd=2,
            padx=20,
            pady=20,
        )
        self.recommended_action_label.pack(fill="x", padx=10, pady=10)

        # Detailed explanation box with header and copy button
        explanation_frame = tk.LabelFrame(
            self.live_data_frame,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_info"],
            relief=tk.RAISED,
            bd=3,
        )
        explanation_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Header row with title and copy button
        header_frame = tk.Frame(explanation_frame, bg=COLORS["bg_medium"])
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        tk.Label(
            header_frame,
            text="📖 DETAILED EXPLANATION - Why This Action?",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_info"],
        ).pack(side="left")

        copy_button = tk.Button(
            header_frame,
            text="📋 Copy",
            font=("Arial", 9),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=1,
            padx=10,
            pady=2,
            command=self._copy_explanation_to_clipboard,
            cursor="hand2"
        )
        copy_button.pack(side="right", padx=5)

        # Create a text widget with scrollbar for better readability
        explanation_container = tk.Frame(explanation_frame, bg=COLORS["bg_dark"])
        explanation_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbar
        explanation_scrollbar = tk.Scrollbar(explanation_container)
        explanation_scrollbar.pack(side="right", fill="y")

        # Text widget for detailed explanation
        self.detailed_explanation_text = tk.Text(
            explanation_container,
            font=("Arial", 11),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            wrap="word",
            relief=tk.SUNKEN,
            bd=2,
            padx=15,
            pady=15,
            height=12,
            state="disabled",  # Read-only
            yscrollcommand=explanation_scrollbar.set,
        )
        self.detailed_explanation_text.pack(side="left", fill="both", expand=True)
        explanation_scrollbar.config(command=self.detailed_explanation_text.yview)

        # Visual metrics panel
        visual_metrics_frame = tk.Frame(explanation_frame, bg=COLORS["bg_dark"])
        visual_metrics_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Hand strength gauge
        strength_frame = tk.LabelFrame(
            visual_metrics_frame,
            text="Hand Strength",
            font=("Arial", 9, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"]
        )
        strength_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.strength_canvas = tk.Canvas(
            strength_frame,
            height=25,
            bg=COLORS["bg_dark"],
            highlightthickness=0
        )
        self.strength_canvas.pack(fill="x", padx=5, pady=5)

        # EV comparison chart
        ev_frame = tk.LabelFrame(
            visual_metrics_frame,
            text="EV Comparison",
            font=("Arial", 9, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"]
        )
        ev_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.ev_canvas = tk.Canvas(
            ev_frame,
            height=60,
            bg=COLORS["bg_dark"],
            highlightthickness=0
        )
        self.ev_canvas.pack(fill="x", padx=5, pady=5)

        # Configure text tags for formatting with enhanced color coding
        self.detailed_explanation_text.tag_config(
            "action_header",
            font=("Arial", 12, "bold"),
            foreground=COLORS["accent_success"],
            spacing1=5
        )
        self.detailed_explanation_text.tag_config(
            "why_header",
            font=("Arial", 11, "bold"),
            foreground=COLORS["accent_info"],
            spacing1=5
        )
        self.detailed_explanation_text.tag_config(
            "metrics_header",
            font=("Arial", 11, "bold"),
            foreground=COLORS["accent_warning"],
            spacing1=5
        )
        self.detailed_explanation_text.tag_config(
            "alternatives_header",
            font=("Arial", 11, "bold"),
            foreground="#9C27B0",  # Purple for alternatives
            spacing1=5
        )
        self.detailed_explanation_text.tag_config(
            "metric_value",
            font=("Arial", 10, "bold"),
            foreground=COLORS["accent_success"]
        )
        self.detailed_explanation_text.tag_config(
            "warning_text",
            foreground=COLORS["accent_danger"],
            font=("Arial", 10, "bold")
        )
        self.detailed_explanation_text.tag_config(
            "positive_ev",
            foreground="#00C853",
            font=("Arial", 10, "bold")
        )
        self.detailed_explanation_text.tag_config(
            "negative_ev",
            foreground="#DD2C00",
            font=("Arial", 10, "bold")
        )
        self.detailed_explanation_text.tag_config(
            "section_content",
            font=("Arial", 10),
            lmargin1=15,
            lmargin2=15
        )

    def _copy_explanation_to_clipboard(self) -> None:
        """Copy the detailed explanation text to clipboard."""
        try:
            if hasattr(self, 'detailed_explanation_text'):
                # Get all text from the widget
                explanation = self.detailed_explanation_text.get("1.0", "end-1c")

                # Copy to clipboard
                self.parent.clipboard_clear()
                self.parent.clipboard_append(explanation)

                # Show brief feedback (button text change)
                # Find the copy button and update its text temporarily
                for widget in self.parent.winfo_children():
                    if isinstance(widget, tk.LabelFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Frame):
                                for btn in child.winfo_children():
                                    if isinstance(btn, tk.Button) and "Copy" in btn['text']:
                                        original_text = btn['text']
                                        btn.config(text="✓ Copied!")
                                        self.parent.after(2000, lambda: btn.config(text=original_text))
                                        break

                print("[LiveTableSection] Explanation copied to clipboard")

        except Exception as e:
            print(f"[LiveTableSection] Error copying to clipboard: {e}")

    def _update_detailed_explanation(self, table_data: Dict) -> None:
        """Update the detailed explanation text with advice reasoning."""
        try:
            if not EXPLAINER_AVAILABLE:
                # Show a message if explainer is not available
                explanation = (
                    "⏳ Detailed explanations are loading...\n\n"
                    "The system will provide comprehensive reasoning once autopilot is active."
                )
                self._set_explanation_text(explanation)
                return

            # Get advice data from table_data if available
            advice_data = table_data.get('advice_data')

            if not advice_data:
                # Create default message when no advice is available
                explanation = (
                    "⏳ Waiting for game state...\n\n"
                    "Once autopilot detects a decision point, detailed advice will appear here explaining:\n"
                    "  • What action to take and why\n"
                    "  • Key metrics supporting the decision\n"
                    "  • Alternative actions and their expected values\n"
                    "  • Strategic context for the situation"
                )
                self._set_explanation_text(explanation)
                return

            # Generate detailed explanation using the explainer
            explainer = get_detailed_explainer()
            explanation = explainer.generate_detailed_explanation(advice_data)
            self._set_explanation_text(explanation)

        except Exception as e:
            import traceback
            print(f"[LiveTableSection] Error updating explanation: {e}")
            print(traceback.format_exc())
            self._set_explanation_text(
                f"⚠️ Error generating explanation: {str(e)}\n\n"
                "Please check logs for details."
            )

    def _set_explanation_text(self, text: str) -> None:
        """Update the text widget with new explanation text."""
        if not hasattr(self, 'detailed_explanation_text'):
            return

        try:
            # Enable editing temporarily
            self.detailed_explanation_text.config(state="normal")

            # Clear existing content
            self.detailed_explanation_text.delete("1.0", "end")

            # Insert new text
            self.detailed_explanation_text.insert("1.0", text)

            # Apply formatting to special sections
            self._apply_explanation_formatting()

            # Disable editing again (read-only)
            self.detailed_explanation_text.config(state="disabled")

            # Scroll to top
            self.detailed_explanation_text.see("1.0")

        except Exception as e:
            print(f"[LiveTableSection] Error setting explanation text: {e}")

    def _apply_explanation_formatting(self) -> None:
        """Apply text formatting tags to the explanation text with enhanced color coding."""
        try:
            # Get all text
            content = self.detailed_explanation_text.get("1.0", "end")
            lines = content.split('\n')

            # Apply formatting line by line
            for line_num, line in enumerate(lines, start=1):
                start_idx = f"{line_num}.0"
                end_idx = f"{line_num}.end"

                # Section headers with specific colors
                if line.startswith('💡'):
                    self.detailed_explanation_text.tag_add("action_header", start_idx, end_idx)
                elif line.startswith('📊 WHY:'):
                    self.detailed_explanation_text.tag_add("why_header", start_idx, end_idx)
                elif line.startswith('📈 METRICS:'):
                    self.detailed_explanation_text.tag_add("metrics_header", start_idx, end_idx)
                elif line.startswith('🔄 ALTERNATIVES:'):
                    self.detailed_explanation_text.tag_add("alternatives_header", start_idx, end_idx)

                # Highlight metric values (percentages and dollar amounts)
                import re

                # Find all percentages
                for match in re.finditer(r'\d+\.?\d*%', line):
                    match_start = f"{line_num}.{match.start()}"
                    match_end = f"{line_num}.{match.end()}"
                    self.detailed_explanation_text.tag_add("metric_value", match_start, match_end)

                # Find all dollar amounts
                for match in re.finditer(r'\$[\d,]+\.?\d*', line):
                    match_start = f"{line_num}.{match.start()}"
                    match_end = f"{line_num}.{match.end()}"
                    value_str = match.group()
                    # Color code based on positive/negative
                    if '+' in line[:match.start()]:
                        self.detailed_explanation_text.tag_add("positive_ev", match_start, match_end)
                    elif '-' in line[:match.start()] or 'loses' in line.lower() or 'negative' in line.lower():
                        self.detailed_explanation_text.tag_add("negative_ev", match_start, match_end)
                    else:
                        self.detailed_explanation_text.tag_add("metric_value", match_start, match_end)

                # Highlight warnings
                if '⚠️' in line or 'warning' in line.lower() or 'caution' in line.lower():
                    self.detailed_explanation_text.tag_add("warning_text", start_idx, end_idx)

        except Exception as e:
            print(f"[LiveTableSection] Error applying formatting: {e}")
            import traceback
            traceback.print_exc()

    def _draw_poker_table(self) -> None:
        """Draw the oval poker table on the canvas."""
        # Get canvas dimensions
        canvas_width = 800
        canvas_height = 500

        # Calculate oval dimensions (centered, with padding)
        padding = 80
        table_x1 = padding
        table_y1 = padding
        table_x2 = canvas_width - padding
        table_y2 = canvas_height - padding

        # Draw outer table border (lighter green)
        self.table_canvas.create_oval(
            table_x1 - 5, table_y1 - 5, table_x2 + 5, table_y2 + 5,
            fill=COLORS["table_border"],
            outline=COLORS["table_border"],
            width=3
        )

        # Draw main table felt
        self.table_canvas.create_oval(
            table_x1, table_y1, table_x2, table_y2,
            fill=COLORS["table_felt"],
            outline="#1a5c3f",
            width=2
        )

        # Draw inner rail (darker)
        rail_padding = 15
        self.table_canvas.create_oval(
            table_x1 + rail_padding, table_y1 + rail_padding,
            table_x2 - rail_padding, table_y2 - rail_padding,
            fill="",
            outline="#0d2a18",
            width=2
        )

    def _create_graphical_player_positions(self) -> None:
        """Create player display positions around the table."""
        # Define 10 player positions around an oval table
        # Positions are (x, y, anchor) relative to canvas
        canvas_width = 800
        canvas_height = 500
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        # Radius for player positioning
        radius_x = 340
        radius_y = 210

        # 10 seat positions around the table
        import math
        positions = []
        for i in range(10):
            angle = (i * 36 - 90) * math.pi / 180  # Start from top, go clockwise
            x = center_x + radius_x * math.cos(angle)
            y = center_y + radius_y * math.sin(angle)
            positions.append((x, y))

        # Create player frames at each position
        for seat, (x, y) in enumerate(positions, start=1):
            self._create_player_position(seat, x, y)

    def _create_player_position(self, seat: int, x: float, y: float) -> None:
        """Create a player display at a specific table position."""
        # Initially, no seat is highlighted as hero - will be determined by handle
        is_hero_seat = False
        frame_bg = COLORS["bg_light"]
        frame_bd = 2

        # Create frame for this player
        player_frame = tk.Frame(
            self.live_data_frame,
            bg=frame_bg,
            relief=tk.RAISED,
            bd=frame_bd,
            padx=5,
            pady=3
        )

        # Place it on the canvas
        window_id = self.table_canvas.create_window(x, y, window=player_frame)

        # Seat label (hero indicator will be updated dynamically)
        seat_text = f"S{seat}"
        seat_label = tk.Label(
            player_frame,
            text=seat_text,
            font=("Arial", 9, "bold"),
            bg=frame_bg,
            fg=COLORS["text_secondary"],
            width=3
        )
        seat_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Player name
        name_label = tk.Label(
            player_frame,
            text="Empty",
            font=("Arial", 10, "bold"),
            bg=frame_bg,
            fg=COLORS["text_secondary"],
            width=12
        )
        name_label.grid(row=1, column=0, columnspan=2, pady=2)

        # Stack
        stack_label = tk.Label(
            player_frame,
            text="$0",
            font=("Arial", 9),
            bg=frame_bg,
            fg=COLORS["accent_warning"]
        )
        stack_label.grid(row=2, column=0, columnspan=2)

        # Stats frame (VPIP / AF)
        stats_frame = tk.Frame(player_frame, bg=frame_bg)
        stats_frame.grid(row=3, column=0, columnspan=2)

        vpip_label = tk.Label(
            stats_frame,
            text="",
            font=("Arial", 7),
            bg=frame_bg,
            fg=COLORS["accent_info"]
        )
        vpip_label.pack(side="left", padx=1)

        af_label = tk.Label(
            stats_frame,
            text="",
            font=("Arial", 7),
            bg=frame_bg,
            fg=COLORS["accent_info"]
        )
        af_label.pack(side="left", padx=1)

        # Bet / Time Bank
        bet_label = tk.Label(
            player_frame,
            text="",
            font=("Arial", 8),
            bg=frame_bg,
            fg=COLORS["accent_info"]
        )
        bet_label.grid(row=4, column=0, columnspan=2)

        # Cards frame
        cards_frame = tk.Frame(player_frame, bg=frame_bg)
        cards_frame.grid(row=5, column=0, columnspan=2, pady=2)

        card1_label = tk.Label(
            cards_frame,
            text="[]",
            font=("Courier", 9, "bold"),
            bg="#ffffff",
            fg="#000000",
            width=3,
            relief=tk.RAISED,
            bd=1
        )
        card1_label.pack(side="left", padx=1)

        card2_label = tk.Label(
            cards_frame,
            text="[]",
            font=("Courier", 9, "bold"),
            bg="#ffffff",
            fg="#000000",
            width=3,
            relief=tk.RAISED,
            bd=1
        )
        card2_label.pack(side="left", padx=1)

        # Status indicator
        status_label = tk.Label(
            player_frame,
            text="",
            font=("Arial", 8),
            bg=frame_bg,
            fg=COLORS["text_secondary"]
        )
        status_label.grid(row=6, column=0, columnspan=2)

        # Store references
        self.player_labels[seat] = {
            "frame": player_frame,
            "window_id": window_id,
            "seat_label": seat_label,
            "name": name_label,
            "stack": stack_label,
            "vpip": vpip_label,
            "af": af_label,
            "bet": bet_label,
            "card1": card1_label,
            "card2": card2_label,
            "status": status_label,
        }


    def _start_main_thread_updates(self) -> None:
        """Start thread-safe live data updates using main thread callbacks."""
        print("[LiveTableSection] Starting main thread updates (thread-safe)")
        self._stop_updates = False
        self._update_count = 0
        self._last_status_log = 0.0
        self._main_thread_update_loop()

    def _main_thread_update_loop(self) -> None:
        """Main thread update loop using after() callbacks - THREAD SAFE."""
        if self._stop_updates:
            print("[LiveTableSection] Updates stopped")
            return

        try:
            # Get live data from the scraper (this should be thread-safe)
            if hasattr(self.host, 'get_live_table_data'):
                table_data = self.host.get_live_table_data()
                if table_data:
                    self._update_count += 1

                    # Log comprehensive status every 5 seconds
                    import time
                    current_time = time.time()
                    if current_time - self._last_status_log >= 5.0:
                        self._last_status_log = current_time
                        players_count = len(table_data.get('players', {}))
                        active_players = table_data.get('active_players', 0)
                        confidence = table_data.get('confidence', 0)
                        data_source = table_data.get('data_source', 'unknown')
                        pot = table_data.get('pot', 0)
                        stage = table_data.get('stage', 'unknown')

                        print(f"\n{'='*80}")
                        print(f"[LiveTable Status] Update #{self._update_count}")
                        print(f"  Data Source: {data_source.upper()}")
                        print(f"  Confidence: {confidence:.1f}%")
                        print(f"  Active Players: {active_players}/{players_count} seats")
                        print(f"  Pot: ${pot:.2f}")
                        print(f"  Stage: {stage.upper()}")
                        print(f"{'='*80}\n")

                    # Update display (safe - we're on main thread)
                    self._update_live_display(table_data)
                elif self._update_count % 20 == 0:
                    print(f"[LiveTable] No data available (update #{self._update_count})")
            else:
                print(f"[LiveTable] ERROR: Host does not have get_live_table_data method!")
        except Exception as e:
            print(f"[LiveTable] Update error: {e}")
            import traceback
            traceback.print_exc()

        # Schedule next update (500ms for responsive feel)
        self.parent.after(500, self._main_thread_update_loop)

    def _start_live_updates(self) -> None:
        """DEPRECATED: Old background thread method - kept for backward compatibility."""
        print("[LiveTableSection] _start_live_updates called - redirecting to thread-safe method")
        self._start_main_thread_updates()

    def _update_loop(self) -> None:
        """Main update loop for live table data."""
        print(f"[LiveTable] Update loop STARTED")
        update_count = 0
        last_status_log = 0.0
        while not self._stop_updates:
            try:
                # Always try to get live data (don't wait for autopilot)
                if hasattr(self.host, 'get_live_table_data'):
                    if update_count == 0:
                        print(f"[LiveTable] Host has get_live_table_data method ✓")
                    # Get live data from the scraper
                    table_data = self.host.get_live_table_data()
                    if table_data:
                        update_count += 1

                        # Log comprehensive status every 5 seconds
                        current_time = time.time()
                        if current_time - last_status_log >= 5.0:
                            last_status_log = current_time
                            players_count = len(table_data.get('players', {}))
                            active_players = table_data.get('active_players', 0)
                            confidence = table_data.get('confidence', 0)
                            data_source = table_data.get('data_source', 'unknown')
                            pot = table_data.get('pot', 0)
                            stage = table_data.get('stage', 'unknown')

                            print(f"\n{'='*80}")
                            print(f"[LiveTable Status] Update #{update_count}")
                            print(f"  Data Source: {data_source.upper()}")
                            print(f"  Confidence: {confidence:.1f}%")
                            print(f"  Active Players: {active_players}/{players_count} seats")
                            print(f"  Pot: ${pot:.2f}")
                            print(f"  Stage: {stage.upper()}")

                            # Log active player details
                            players = table_data.get('players', {})
                            if players:
                                print(f"  Players:")
                                for seat_num in sorted(players.keys()):
                                    player = players[seat_num]
                                    if player.get('status') == 'Active':
                                        name = player.get('name', 'Unknown')
                                        stack = player.get('stack', 0)
                                        position = player.get('position', '')
                                        dealer = " 🔘" if player.get('is_dealer') else ""
                                        print(f"    Seat {seat_num}: {name} - ${stack:.2f} {position}{dealer}")
                            print(f"{'='*80}\n")

                        self._update_live_display(table_data)
                    else:
                        if update_count % 20 == 0:
                            print(f"[LiveTable] No data available (update #{update_count})")
                else:
                    print(f"[LiveTable] ERROR: Host does not have get_live_table_data method!")
                    time.sleep(5)  # Avoid spam

                time.sleep(0.5)  # Update every 500ms for live feel (now uses cached state)
            except Exception as e:
                print(f"[LiveTable] Update error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(2.0)

    def _update_detection_lights(self, table_data: Dict) -> None:
        """Update LED status lights based on what's actually detected."""
        # Green = detected & valid, Yellow = uncertain, Red = not detected, Gray = unknown

        # Players detection
        players = table_data.get('players', {})
        active_players = sum(1 for p in players.values() if p.get('active', False))
        if active_players >= 2:
            self.status_lights['players'].config(fg="#10b981")  # Green
        elif active_players == 1:
            self.status_lights['players'].config(fg="#f59e0b")  # Yellow
        else:
            self.status_lights['players'].config(fg="#ef4444")  # Red

        # Stacks detection (check if most players have valid stacks)
        players_with_stacks = sum(1 for p in players.values() if p.get('stack', 0) > 0)
        if players_with_stacks >= active_players * 0.7:  # 70% have stacks
            self.status_lights['stacks'].config(fg="#10b981")  # Green
        elif players_with_stacks > 0:
            self.status_lights['stacks'].config(fg="#f59e0b")  # Yellow
        else:
            self.status_lights['stacks'].config(fg="#ef4444")  # Red

        # Board cards detection
        board_cards = table_data.get('board_cards', [])
        valid_board = [c for c in board_cards if c and c != '']
        if len(valid_board) >= 3:  # Flop or later
            self.status_lights['board'].config(fg="#10b981")  # Green
        elif len(valid_board) > 0:
            self.status_lights['board'].config(fg="#f59e0b")  # Yellow
        else:
            self.status_lights['board'].config(fg="#888888")  # Gray (preflop is normal)

        # Hole cards detection
        my_cards = table_data.get('my_hole_cards', [])
        valid_my_cards = [c for c in my_cards if c and c != '']
        if len(valid_my_cards) == 2:
            self.status_lights['hole_cards'].config(fg="#10b981")  # Green
        elif len(valid_my_cards) == 1:
            self.status_lights['hole_cards'].config(fg="#f59e0b")  # Yellow
        else:
            self.status_lights['hole_cards'].config(fg="#ef4444")  # Red

        # Dealer button detection
        dealer_seat = table_data.get('dealer_seat', 0)
        if dealer_seat and dealer_seat > 0:
            self.status_lights['dealer'].config(fg="#10b981")  # Green
        else:
            self.status_lights['dealer'].config(fg="#ef4444")  # Red

        # Blinds detection
        sb = table_data.get('small_blind', 0)
        bb = table_data.get('big_blind', 0)
        if sb > 0 and bb > 0:
            self.status_lights['blinds'].config(fg="#10b981")  # Green
        elif sb > 0 or bb > 0:
            self.status_lights['blinds'].config(fg="#f59e0b")  # Yellow
        else:
            self.status_lights['blinds'].config(fg="#ef4444")  # Red

        # Bets detection (check if any player has a current bet)
        players_with_bets = sum(1 for p in players.values() if p.get('bet', 0) > 0)
        if players_with_bets > 0:
            self.status_lights['bets'].config(fg="#10b981")  # Green
        else:
            self.status_lights['bets'].config(fg="#888888")  # Gray (no bets is normal)

        # Pot detection
        pot = table_data.get('pot', 0)
        if pot > 0:
            self.status_lights['pot'].config(fg="#10b981")  # Green
        else:
            self.status_lights['pot'].config(fg="#888888")  # Gray (0 pot at start is normal)

    def _update_live_display(self, table_data: Dict) -> None:
        """Update the live display with scraped table data."""
        try:
            # UPDATE DETECTION STATUS LIGHTS FIRST
            self._update_detection_lights(table_data)

            # Log the received data structure (only once per 20 updates to avoid spam)
            if not hasattr(self, '_display_update_count'):
                self._display_update_count = 0
            self._display_update_count += 1

            if self._display_update_count % 20 == 1:
                print(f"[LiveTable Display] Update #{self._display_update_count}: Received data with {len(table_data.get('players', {}))} players")
                print(f"   Confidence: {table_data.get('confidence', 0):.1f}%")
                print(f"   Pot: ${table_data.get('pot', 0)}, Stage: {table_data.get('stage', 'unknown')}")
                print(f"   Board: {table_data.get('board_cards', [])}")
                print(f"   My cards: {table_data.get('my_hole_cards', [])}")

            # Update tournament name
            if self.tournament_label:
                tournament_name = table_data.get('tournament_name')
                if tournament_name:
                    self.tournament_label.config(text=f"🏆 {tournament_name}")
                else:
                    self.tournament_label.config(text="")

            # Update table status with validation info, extraction method and data freshness
            if self.table_status_label:
                status = table_data.get('status', 'Active')
                confidence = table_data.get('confidence', 0)
                validation_complete = table_data.get('validation_complete', False)
                warnings = table_data.get('warnings', [])

                # Check extraction method
                extraction_method = table_data.get('extraction_method', 'unknown')
                extraction_time = table_data.get('extraction_time_ms', 0.0)

                # Check if data is live or cached
                data_source = table_data.get('data_source', 'unknown')
                data_age = table_data.get('data_age_seconds', 0.0)

                # Build status text with extraction method and freshness indicator
                if data_source == 'live':
                    if extraction_method == 'cdp':
                        # Chrome DevTools - fastest and most reliable
                        method_icon = "⚡"
                        method_text = "CDP"
                    else:
                        # Screenshot OCR - slower
                        method_icon = "📸"
                        method_text = "OCR"

                    status_text = f"{method_icon} {method_text} ({extraction_time:.0f}ms) - {status} ({confidence:.1f}%)"
                    status_color = COLORS["accent_success"] if (confidence and confidence > 70 and validation_complete) else COLORS["accent_warning"]
                else:
                    # Cached data
                    status_text = f"💾 CACHED ({data_age:.1f}s ago) - {status} ({confidence:.1f}% confidence)"
                    status_color = COLORS["accent_info"] if data_age < 5.0 else COLORS["accent_warning"]

                if not validation_complete:
                    status_text += f" - ⚠️ {len(warnings)} warning(s)"

                self.table_status_label.config(
                    text=status_text,
                    fg=status_color
                )

            # Update board cards with suit colors
            board_cards = table_data.get('board_cards', [])
            for i, card_label in enumerate(self.board_labels):
                if i < len(board_cards) and board_cards[i]:
                    card = board_cards[i]
                    # Determine card color based on suit
                    card_color = "#000000"  # Default black
                    # Handle both Card objects and strings
                    card_str = str(card)
                    if hasattr(card, 'suit'):
                        # Card object - check suit attribute
                        if card.suit in ['h', 'd']:
                            card_color = "#dc2626"  # Red for hearts/diamonds
                    else:
                        # String - check for suit symbols/letters
                        if '♥' in card_str or '♦' in card_str or 'h' in card_str.lower() or 'd' in card_str.lower():
                            card_color = "#dc2626"  # Red for hearts/diamonds
                    card_label.config(text=card_str, fg=card_color, bg="#ffffff")
                else:
                    card_label.config(text="[ ]", fg="#666666", bg="#cccccc")

            # Update blinds and ante
            if self.blinds_label:
                sb = table_data.get('small_blind', 0)
                bb = table_data.get('big_blind', 0)
                self.blinds_label.config(text=f"${sb}/${bb}")

            if self.ante_label:
                ante = table_data.get('ante', 0)
                self.ante_label.config(text=f"${ante}")

            # Update pot
            if self.pot_label:
                pot = table_data.get('pot', 0)
                self.pot_label.config(text=f"${pot}")

            # Update dealer button
            if self.dealer_button_label:
                dealer_seat = table_data.get('dealer_seat', 0)
                # Handle None values explicitly
                dealer_seat = dealer_seat if dealer_seat is not None else 0
                self.dealer_button_label.config(
                    text=f"Seat {dealer_seat}" if dealer_seat > 0 else "Seat -"
                )

            # Update players
            players = table_data.get('players', {})
            for seat in range(1, 11):
                if seat in self.player_labels:
                    player_info = players.get(seat, {})

                    # Update name
                    name = player_info.get('name', 'Empty')

                    # Check if this is the user's seat based on handle
                    is_user_seat = False
                    if self.user_handle and name != 'Empty':
                        is_user_seat = self.user_handle.lower() in name.lower() or name.lower() in self.user_handle.lower()
                        if is_user_seat and self.user_seat != seat:
                            self.user_seat = seat
                            print(f"Detected user at seat {seat}")

                    # Check if this is the active player's turn
                    is_active_turn = player_info.get('is_active_turn', False)

                    # Determine background color based on player state
                    if is_active_turn:
                        # Bright green for active turn
                        bg_color = "#28a745"
                        fg_color = "#FFFFFF"
                        border = 4
                    elif is_user_seat:
                        # Blue for user
                        bg_color = "#4A90E2"
                        fg_color = "#FFFFFF"
                        border = 3
                    else:
                        # Default
                        bg_color = COLORS["bg_light"]
                        fg_color = COLORS["text_primary"] if name != 'Empty' else COLORS["text_secondary"]
                        border = 2

                    # Apply styling to frame
                    self.player_labels[seat]["frame"].config(bg=bg_color, bd=border)

                    # Seat label with indicators
                    seat_label_text = f"S{seat}"
                    if is_user_seat:
                        seat_label_text = f"🎯 YOU (S{seat})"
                    if is_active_turn:
                        seat_label_text = f"▶ {seat_label_text}"

                    self.player_labels[seat]["seat_label"].config(
                        text=seat_label_text,
                        bg=bg_color,
                        fg=fg_color,
                        width=12 if is_user_seat else 5
                    )

                    # Player name
                    self.player_labels[seat]["name"].config(
                        text=name,
                        bg=bg_color,
                        fg=fg_color
                    )

                    # Stack
                    self.player_labels[seat]["stack"].config(
                        bg=bg_color,
                        fg=fg_color if is_user_seat or is_active_turn else COLORS["accent_warning"]
                    )

                    # VPIP stat
                    vpip = player_info.get('vpip')
                    if vpip is not None:
                        self.player_labels[seat]["vpip"].config(
                            text=f"VP:{vpip}%",
                            bg=bg_color,
                            fg=fg_color
                        )
                    else:
                        self.player_labels[seat]["vpip"].config(text="", bg=bg_color)

                    # AF stat
                    af = player_info.get('af')
                    if af is not None:
                        self.player_labels[seat]["af"].config(
                            text=f"AF:{af:.1f}",
                            bg=bg_color,
                            fg=fg_color
                        )
                    else:
                        self.player_labels[seat]["af"].config(text="", bg=bg_color)

                    # Bet / Time bank
                    self.player_labels[seat]["bet"].config(
                        bg=bg_color,
                        fg=fg_color if is_user_seat or is_active_turn else COLORS["accent_info"]
                    )

                    # Status
                    self.player_labels[seat]["status"].config(
                        bg=bg_color,
                        fg=fg_color if is_user_seat or is_active_turn else (
                            COLORS["accent_success"] if player_info.get('status') == "Active" else COLORS["text_secondary"]
                        )
                    )

                    # Update stack
                    stack = player_info.get('stack', 0)
                    # Handle None values explicitly
                    stack = stack if stack is not None else 0
                    self.player_labels[seat]["stack"].config(
                        text=f"${stack}" if stack > 0 else "$0"
                    )

                    # Update bet or time bank
                    bet = player_info.get('bet', 0)
                    time_bank = player_info.get('time_bank')

                    # Handle None values explicitly
                    bet = bet if bet is not None else 0

                    # Show time bank if present, otherwise show bet
                    if time_bank is not None and time_bank > 0:
                        self.player_labels[seat]["bet"].config(
                            text=f"⏱ Time: {time_bank}s",
                            fg="#FF6B6B"  # Red for time running out
                        )
                    elif bet > 0:
                        self.player_labels[seat]["bet"].config(
                            text=f"Bet: ${bet}"
                        )
                    else:
                        self.player_labels[seat]["bet"].config(text="")

                    # Update hole cards (with safe list access)
                    hole_cards = player_info.get('hole_cards', ['', ''])
                    # Ensure hole_cards is a list with at least 2 elements
                    if not isinstance(hole_cards, list):
                        hole_cards = ['', '']
                    while len(hole_cards) < 2:
                        hole_cards.append('')

                    # Convert Card objects to strings
                    card1_str = str(hole_cards[0]) if hole_cards[0] else "[]"
                    card2_str = str(hole_cards[1]) if hole_cards[1] else "[]"

                    self.player_labels[seat]["card1"].config(text=card1_str)
                    self.player_labels[seat]["card2"].config(text=card2_str)

                    # Update status
                    status = player_info.get('status', '')
                    self.player_labels[seat]["status"].config(
                        text=status
                    )

            # Update my hole cards (with safe list access)
            my_cards = table_data.get('my_hole_cards', ['', ''])
            # Ensure my_cards is a list
            if not isinstance(my_cards, list):
                my_cards = ['', '']

            for i, card_label in enumerate(self.my_cards_labels):
                if i < len(my_cards) and my_cards[i]:
                    # Convert Card objects to strings
                    card_str = str(my_cards[i])
                    card_label.config(text=card_str, fg=COLORS["accent_success"])
                else:
                    card_label.config(text="[ ]", fg=COLORS["text_secondary"])

            # Update recommended action
            if self.recommended_action_label:
                action = table_data.get('recommended_action', 'Waiting for game state...')
                action_color = COLORS["accent_success"]

                # Show validation warnings in action box if data is incomplete
                warnings = table_data.get('warnings', [])
                if warnings and not table_data.get('validation_complete', False):
                    action = "⚠️ DATA VALIDATION WARNINGS:\n\n"
                    action += "\n".join(f"• {w}" for w in warnings)
                    action_color = COLORS["accent_warning"]
                else:
                    # Color code by action type
                    if "FOLD" in action.upper():
                        action_color = COLORS["accent_danger"]
                    elif "CALL" in action.upper() or "CHECK" in action.upper():
                        action_color = COLORS["accent_warning"]
                    elif "RAISE" in action.upper() or "BET" in action.upper():
                        action_color = COLORS["accent_success"]
                    elif "ALL-IN" in action.upper():
                        action_color = COLORS["accent_info"]

                self.recommended_action_label.config(text=action, fg=action_color)

            # Update detailed explanation
            self._update_detailed_explanation(table_data)

            # Update visual metrics
            self._update_visual_metrics(table_data)

        except Exception as e:
            import traceback
            print(f"Display update error: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    def _update_visual_metrics(self, table_data: Dict) -> None:
        """Update visual metrics displays (hand strength gauge and EV chart)."""
        try:
            # Get advice data
            advice_data = table_data.get('advice_data')
            if not advice_data or not advice_data.has_data:
                return

            # Update hand strength gauge
            self._draw_hand_strength_gauge(advice_data)

            # Update EV comparison chart
            self._draw_ev_comparison_chart(advice_data)

        except Exception as e:
            print(f"[LiveTableSection] Error updating visual metrics: {e}")

    def _draw_hand_strength_gauge(self, advice_data) -> None:
        """Draw hand strength gauge as a progress bar."""
        try:
            if not hasattr(self, 'strength_canvas'):
                return

            canvas = self.strength_canvas
            canvas.delete("all")

            # Get canvas dimensions
            width = canvas.winfo_width()
            if width <= 1:
                width = 300  # Default width

            height = 25

            # Get hand strength (0-100)
            strength = advice_data.hand_percentile or (advice_data.win_probability * 100 if advice_data.win_probability else 50)

            # Draw background
            canvas.create_rectangle(0, 0, width, height, fill="#2a2a2a", outline="#444444")

            # Calculate fill width
            fill_width = (strength / 100) * width

            # Color code based on strength
            if strength >= 80:
                fill_color = "#00C853"  # Green
            elif strength >= 60:
                fill_color = "#64DD17"  # Light green
            elif strength >= 40:
                fill_color = "#FFD600"  # Yellow
            elif strength >= 20:
                fill_color = "#FF6D00"  # Orange
            else:
                fill_color = "#DD2C00"  # Red

            # Draw fill
            if fill_width > 0:
                canvas.create_rectangle(0, 0, fill_width, height, fill=fill_color, outline="")

            # Draw percentage text
            text = f"{strength:.0f}%"
            canvas.create_text(
                width / 2, height / 2,
                text=text,
                font=("Arial", 11, "bold"),
                fill="#FFFFFF"
            )

        except Exception as e:
            print(f"[LiveTableSection] Error drawing hand strength gauge: {e}")

    def _draw_ev_comparison_chart(self, advice_data) -> None:
        """Draw EV comparison as horizontal bar chart."""
        try:
            if not hasattr(self, 'ev_canvas'):
                return

            canvas = self.ev_canvas
            canvas.delete("all")

            # Get canvas dimensions
            width = canvas.winfo_width()
            if width <= 1:
                width = 300  # Default width

            height = 60

            # Collect EV values for all actions
            ev_data = []
            if advice_data.ev_fold is not None:
                ev_data.append(("Fold", advice_data.ev_fold))
            if advice_data.ev_call is not None:
                ev_data.append(("Call", advice_data.ev_call))
            if advice_data.ev_raise is not None:
                ev_data.append(("Raise", advice_data.ev_raise))

            if not ev_data:
                return

            # Find max absolute value for scaling
            max_abs_ev = max(abs(ev) for _, ev in ev_data)
            if max_abs_ev == 0:
                max_abs_ev = 1  # Avoid division by zero

            # Draw bars
            bar_height = height // len(ev_data)
            for i, (action, ev) in enumerate(ev_data):
                y = i * bar_height

                # Calculate bar width (proportional to EV)
                bar_width = abs(ev) / max_abs_ev * (width * 0.7)

                # Color code
                if ev > 0:
                    color = "#00C853"  # Green for positive EV
                elif ev < 0:
                    color = "#DD2C00"  # Red for negative EV
                else:
                    color = "#888888"  # Gray for zero

                # Draw bar from center
                center_x = width * 0.15
                if ev >= 0:
                    canvas.create_rectangle(
                        center_x, y + 2,
                        center_x + bar_width, y + bar_height - 2,
                        fill=color, outline=""
                    )
                else:
                    canvas.create_rectangle(
                        center_x - bar_width, y + 2,
                        center_x, y + bar_height - 2,
                        fill=color, outline=""
                    )

                # Draw action label
                canvas.create_text(
                    10, y + bar_height // 2,
                    text=action,
                    font=("Arial", 8),
                    fill="#FFFFFF",
                    anchor="w"
                )

                # Draw EV value
                ev_text = f"${ev:+.1f}"
                canvas.create_text(
                    width - 10, y + bar_height // 2,
                    text=ev_text,
                    font=("Arial", 8, "bold"),
                    fill=color,
                    anchor="e"
                )

        except Exception as e:
            print(f"[LiveTableSection] Error drawing EV comparison chart: {e}")

    # ------------------------------------------------------------------
    def stop_updates(self) -> None:
        """Stop the live update thread."""
        self._stop_updates = True


__all__ = ["LiveTableSection"]