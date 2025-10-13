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


class LiveTableSection:
    """Encapsulates the LiveTable tab with real-time scraper data display."""

    def __init__(self, host: Any, parent: tk.Misc, *, modules_loaded: bool) -> None:
        self.host = host
        self.parent = parent
        self._modules_loaded = modules_loaded

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
        self.my_cards_labels: List[tk.Label] = []

        # User's handle for position identification
        self.user_handle: str = ""
        self.user_seat: int = 1  # Default to seat 1

        # Update control
        self._update_thread: Optional[threading.Thread] = None
        self._stop_updates = False

        self._build_ui()
        self._prompt_for_handle()
        self._start_live_updates()

    # ------------------------------------------------------------------
    def _prompt_for_handle(self) -> None:
        """Prompt user for their poker handle on startup."""
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

    def _build_ui(self) -> None:
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

        # Live table data display (full width)
        self._build_live_data_panel(content_frame)

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

        # Table status
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

        # Board cards section
        board_frame = tk.LabelFrame(
            self.live_data_frame,
            text="Board Cards",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        board_frame.pack(fill="x", pady=(0, 10))

        board_cards_frame = tk.Frame(board_frame, bg=COLORS["bg_medium"])
        board_cards_frame.pack(pady=5)

        self.board_labels = []
        for i in range(5):  # 5 community cards max
            card_label = tk.Label(
                board_cards_frame,
                text="[ ]",
                font=("Courier", 12, "bold"),
                bg=COLORS["bg_light"],
                fg=COLORS["text_primary"],
                width=4,
                relief=tk.RAISED,
                bd=1,
            )
            card_label.pack(side="left", padx=2)
            self.board_labels.append(card_label)

        # Game info section
        game_info_frame = tk.Frame(self.live_data_frame, bg=COLORS["bg_dark"])
        game_info_frame.pack(fill="x", pady=(0, 10))

        # Blinds and ante
        blinds_frame = tk.Frame(game_info_frame, bg=COLORS["bg_dark"])
        blinds_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            blinds_frame,
            text="Blinds:",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        self.blinds_label = tk.Label(
            blinds_frame,
            text="$-/$-",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_warning"],
        )
        self.blinds_label.pack(side="left", padx=(5, 15))

        tk.Label(
            blinds_frame,
            text="Ante:",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        self.ante_label = tk.Label(
            blinds_frame,
            text="$-",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_warning"],
        )
        self.ante_label.pack(side="left", padx=(5, 15))

        # Pot display
        tk.Label(
            blinds_frame,
            text="Pot:",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        self.pot_label = tk.Label(
            blinds_frame,
            text="$0",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_success"],
        )
        self.pot_label.pack(side="left", padx=(5, 15))

        # Dealer button
        dealer_frame = tk.Frame(game_info_frame, bg=COLORS["bg_dark"])
        dealer_frame.pack(side="right")

        tk.Label(
            dealer_frame,
            text="Dealer:",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        self.dealer_button_label = tk.Label(
            dealer_frame,
            text="Seat -",
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_info"],
        )
        self.dealer_button_label.pack(side="left", padx=(5, 0))

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
        action_frame.pack(fill="both", expand=True, pady=(0, 10))

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
        self.recommended_action_label.pack(fill="both", expand=True, padx=10, pady=10)

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

        # Bet
        bet_label = tk.Label(
            player_frame,
            text="",
            font=("Arial", 8),
            bg=frame_bg,
            fg=COLORS["accent_info"]
        )
        bet_label.grid(row=3, column=0, columnspan=2)

        # Cards frame
        cards_frame = tk.Frame(player_frame, bg=frame_bg)
        cards_frame.grid(row=4, column=0, columnspan=2, pady=2)

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
        status_label.grid(row=5, column=0, columnspan=2)

        # Store references
        self.player_labels[seat] = {
            "frame": player_frame,
            "window_id": window_id,
            "seat_label": seat_label,
            "name": name_label,
            "stack": stack_label,
            "bet": bet_label,
            "card1": card1_label,
            "card2": card2_label,
            "status": status_label,
        }


    def _start_live_updates(self) -> None:
        """Start the live data update thread."""
        if self._update_thread is None or not self._update_thread.is_alive():
            self._stop_updates = False
            self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()

    def _update_loop(self) -> None:
        """Main update loop for live table data."""
        while not self._stop_updates:
            try:
                # Always try to get live data (don't wait for autopilot)
                if hasattr(self.host, 'get_live_table_data'):
                    # Get live data from the scraper
                    table_data = self.host.get_live_table_data()
                    if table_data:
                        self._update_live_display(table_data)

                time.sleep(0.5)  # Update every 500ms for live feel
            except Exception as e:
                print(f"Live update error: {e}")
                time.sleep(2.0)

    def _update_live_display(self, table_data: Dict) -> None:
        """Update the live display with scraped table data."""
        try:
            # Update table status with validation info
            if self.table_status_label:
                status = table_data.get('status', 'Active')
                confidence = table_data.get('confidence', 0)
                validation_complete = table_data.get('validation_complete', False)
                warnings = table_data.get('warnings', [])

                status_text = f"{status} ({confidence:.1f}% confidence)"
                if not validation_complete:
                    status_text += f" - ⚠️ {len(warnings)} warning(s)"

                self.table_status_label.config(
                    text=status_text,
                    fg=COLORS["accent_success"] if (confidence > 70 and validation_complete) else COLORS["accent_warning"]
                )

            # Update board cards
            board_cards = table_data.get('board_cards', [])
            for i, card_label in enumerate(self.board_labels):
                if i < len(board_cards) and board_cards[i]:
                    card_label.config(text=board_cards[i], fg=COLORS["accent_success"])
                else:
                    card_label.config(text="[ ]", fg=COLORS["text_secondary"])

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

                    # Highlight user's position in blue
                    if is_user_seat:
                        self.player_labels[seat]["frame"].config(bg="#4A90E2", bd=3)  # Blue background
                        self.player_labels[seat]["seat_label"].config(
                            text=f"🎯 YOU (S{seat})",
                            bg="#4A90E2",
                            fg="#FFFFFF",  # White text
                            width=12
                        )
                        self.player_labels[seat]["name"].config(
                            text=name,
                            bg="#4A90E2",
                            fg="#FFFFFF",  # White text
                        )
                        self.player_labels[seat]["stack"].config(
                            bg="#4A90E2",
                            fg="#FFFFFF"
                        )
                        self.player_labels[seat]["bet"].config(
                            bg="#4A90E2",
                            fg="#FFFFFF"
                        )
                        self.player_labels[seat]["status"].config(
                            bg="#4A90E2",
                            fg="#FFFFFF"
                        )
                    else:
                        # Reset to default styling for non-user seats
                        self.player_labels[seat]["frame"].config(bg=COLORS["bg_light"], bd=2)
                        self.player_labels[seat]["seat_label"].config(
                            text=f"S{seat}",
                            bg=COLORS["bg_light"],
                            fg=COLORS["text_secondary"],
                            width=3
                        )
                        self.player_labels[seat]["name"].config(
                            text=name,
                            bg=COLORS["bg_light"],
                            fg=COLORS["text_primary"] if name != 'Empty' else COLORS["text_secondary"]
                        )
                        self.player_labels[seat]["stack"].config(
                            bg=COLORS["bg_light"],
                            fg=COLORS["accent_warning"]
                        )
                        self.player_labels[seat]["bet"].config(
                            bg=COLORS["bg_light"],
                            fg=COLORS["accent_info"]
                        )
                        self.player_labels[seat]["status"].config(
                            bg=COLORS["bg_light"],
                            fg=COLORS["accent_success"] if player_info.get('status') == "Active" else COLORS["text_secondary"]
                        )

                    # Update stack
                    stack = player_info.get('stack', 0)
                    # Handle None values explicitly
                    stack = stack if stack is not None else 0
                    self.player_labels[seat]["stack"].config(
                        text=f"${stack}" if stack > 0 else "$0"
                    )

                    # Update bet
                    bet = player_info.get('bet', 0)
                    # Handle None values explicitly
                    bet = bet if bet is not None else 0
                    self.player_labels[seat]["bet"].config(
                        text=f"Bet: ${bet}" if bet > 0 else ""
                    )

                    # Update hole cards
                    hole_cards = player_info.get('hole_cards', ['', ''])
                    self.player_labels[seat]["card1"].config(
                        text=hole_cards[0] if hole_cards[0] else "[]"
                    )
                    self.player_labels[seat]["card2"].config(
                        text=hole_cards[1] if len(hole_cards) > 1 and hole_cards[1] else "[]"
                    )

                    # Update status
                    status = player_info.get('status', '')
                    self.player_labels[seat]["status"].config(
                        text=status
                    )

            # Update my hole cards
            my_cards = table_data.get('my_hole_cards', ['', ''])
            for i, card_label in enumerate(self.my_cards_labels):
                if i < len(my_cards) and my_cards[i]:
                    card_label.config(text=my_cards[i], fg=COLORS["accent_success"])
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

        except Exception as e:
            print(f"Display update error: {e}")

    # ------------------------------------------------------------------
    def stop_updates(self) -> None:
        """Stop the live update thread."""
        self._stop_updates = True


__all__ = ["LiveTableSection"]