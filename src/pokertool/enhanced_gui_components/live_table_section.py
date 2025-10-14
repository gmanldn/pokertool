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
        # TEMPORARILY DISABLED: LiveTable updates cause segfault due to OCR thread-safety issues
        # TODO: Implement thread-safe OCR or use main thread callbacks
        # self._start_live_updates()  # Start updates FIRST
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
        print("[LiveTableSection] _build_ui called")
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


    def _start_live_updates(self) -> None:
        """Start the live data update thread."""
        print("[LiveTableSection] _start_live_updates called")
        try:
            if self._update_thread is None or not self._update_thread.is_alive():
                print("[LiveTableSection] Starting update thread...")
                self._stop_updates = False
                self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
                self._update_thread.start()
                print(f"[LiveTableSection] Update thread started: {self._update_thread.is_alive()}")
            else:
                print("[LiveTableSection] Update thread already running")
        except Exception as e:
            print(f"[LiveTableSection] ERROR starting update thread: {e}")
            import traceback
            traceback.print_exc()

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

                    self.player_labels[seat]["card1"].config(
                        text=hole_cards[0] if hole_cards[0] else "[]"
                    )
                    self.player_labels[seat]["card2"].config(
                        text=hole_cards[1] if hole_cards[1] else "[]"
                    )

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
            import traceback
            print(f"Display update error: {e}")
            print(f"Traceback: {traceback.format_exc()}")

    # ------------------------------------------------------------------
    def stop_updates(self) -> None:
        """Stop the live update thread."""
        self._stop_updates = True


__all__ = ["LiveTableSection"]