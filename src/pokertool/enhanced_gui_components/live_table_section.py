#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LiveTable section for the enhanced GUI with real-time scraper data display."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Any, Optional, Dict, List

from pokertool.gui import EnhancedPokerAssistantFrame

from .style import COLORS, FONTS


class LiveTableSection:
    """Encapsulates the LiveTable tab with real-time scraper data display."""

    def __init__(self, host: Any, parent: tk.Misc, *, modules_loaded: bool) -> None:
        self.host = host
        self.parent = parent
        self._modules_loaded = modules_loaded
        self.manual_panel: Optional[EnhancedPokerAssistantFrame] = None
        self.status_label: Optional[tk.Label] = None
        
        # Live table data display widgets
        self.live_data_frame: Optional[tk.Frame] = None
        self.player_labels: Dict[int, Dict[str, tk.Label]] = {}
        self.board_labels: List[tk.Label] = []
        self.blinds_label: Optional[tk.Label] = None
        self.ante_label: Optional[tk.Label] = None
        self.dealer_button_label: Optional[tk.Label] = None
        self.table_status_label: Optional[tk.Label] = None
        
        # Update control
        self._update_thread: Optional[threading.Thread] = None
        self._stop_updates = False

        self._build_ui()
        self.update_autopilot_status(host.autopilot_active)
        self._start_live_updates()

    # ------------------------------------------------------------------
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

        # Left side: Live table data display
        self._build_live_data_panel(content_frame)
        
        # Right side: Manual controls and tips
        self._build_manual_panel(content_frame)

    def _build_live_data_panel(self, parent) -> None:
        """Build the live table data display panel."""
        live_container = tk.LabelFrame(
            parent,
            text="🔴 LIVE TABLE DATA",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_success"],
            relief=tk.RAISED,
            bd=2,
        )
        live_container.pack(side="left", fill="both", expand=True, padx=(0, 10))

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

        # Players section
        players_frame = tk.LabelFrame(
            self.live_data_frame,
            text="Players (Live from Scraper)",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        players_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Create scrollable frame for players
        canvas = tk.Canvas(players_frame, bg=COLORS["bg_medium"], height=200)
        scrollbar = ttk.Scrollbar(players_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_medium"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        # Initialize player display (seats 1-10)
        self.player_labels = {}
        for seat in range(1, 11):
            self._create_player_row(scrollable_frame, seat)

    def _create_player_row(self, parent, seat: int) -> None:
        """Create a row for displaying player information."""
        player_frame = tk.Frame(parent, bg=COLORS["bg_light"], relief=tk.RAISED, bd=1)
        player_frame.pack(fill="x", padx=2, pady=1)

        # Seat number
        seat_label = tk.Label(
            player_frame,
            text=f"Seat {seat}:",
            font=FONTS["body"],
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            width=8,
        )
        seat_label.pack(side="left", padx=5)

        # Player name
        name_label = tk.Label(
            player_frame,
            text="Empty",
            font=FONTS["body"],
            bg=COLORS["bg_light"],
            fg=COLORS["text_secondary"],
            width=15,
            anchor="w",
        )
        name_label.pack(side="left", padx=5)

        # Stack size
        stack_label = tk.Label(
            player_frame,
            text="$0",
            font=FONTS["body"],
            bg=COLORS["bg_light"],
            fg=COLORS["accent_warning"],
            width=10,
            anchor="w",
        )
        stack_label.pack(side="left", padx=5)

        # Hole cards
        cards_frame = tk.Frame(player_frame, bg=COLORS["bg_light"])
        cards_frame.pack(side="left", padx=5)

        card1_label = tk.Label(
            cards_frame,
            text="[ ]",
            font=("Courier", 10),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            width=3,
        )
        card1_label.pack(side="left", padx=1)

        card2_label = tk.Label(
            cards_frame,
            text="[ ]",
            font=("Courier", 10),
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            width=3,
        )
        card2_label.pack(side="left", padx=1)

        # Status (active, folded, etc.)
        status_label = tk.Label(
            player_frame,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_light"],
            fg=COLORS["text_secondary"],
            width=10,
            anchor="w",
        )
        status_label.pack(side="left", padx=5)

        self.player_labels[seat] = {
            "name": name_label,
            "stack": stack_label,
            "card1": card1_label,
            "card2": card2_label,
            "status": status_label,
        }

    def _build_manual_panel(self, parent) -> None:
        """Build the manual controls panel."""
        manual_container = tk.LabelFrame(
            parent,
            text="Manual Controls",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2,
        )
        manual_container.pack(side="right", fill="y", padx=300)

        manual_inner = tk.Frame(manual_container, bg=COLORS["bg_dark"])
        manual_inner.pack(fill="both", expand=True, padx=10, pady=10)

        if self._modules_loaded:
            try:
                self.manual_panel = EnhancedPokerAssistantFrame(manual_inner, auto_pack=False)
                self.manual_panel.pack(fill="both", expand=True)
            except Exception as manual_error:
                self.manual_panel = None
                fallback = tk.Label(
                    manual_inner,
                    text=f"Manual interface unavailable: {manual_error}",
                    font=FONTS["body"],
                    bg=COLORS["bg_dark"],
                    fg=COLORS["accent_danger"],
                    wraplength=280,
                    justify="left",
                )
                fallback.pack(fill="both", expand=True, pady=20)
        else:
            fallback = tk.Label(
                manual_inner,
                text="Manual interface modules are not available.",
                font=FONTS["body"],
                bg=COLORS["bg_dark"],
                fg=COLORS["accent_danger"],
                wraplength=280,
                justify="left",
            )
            fallback.pack(fill="both", expand=True, pady=20)

        # Status and sync info
        sync_frame = tk.LabelFrame(
            manual_container,
            text="Autopilot Sync",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=1,
        )
        sync_frame.pack(fill="x", pady=(10, 0))

        tk.Label(
            sync_frame,
            text="Autopilot status:",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).pack(anchor="w", padx=10, pady=(10, 4))

        self.status_label = tk.Label(
            sync_frame,
            text="Inactive",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
        )
        self.status_label.pack(anchor="w", padx=10, pady=(0, 10))

        self.host.manual_panel = self.manual_panel
        self.host.manual_status_label = self.status_label

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
                if self.host.autopilot_active and hasattr(self.host, 'get_live_table_data'):
                    # Get live data from the scraper
                    table_data = self.host.get_live_table_data()
                    if table_data:
                        self._update_live_display(table_data)
                        
                time.sleep(1.0)  # Update every second
            except Exception as e:
                print(f"Live update error: {e}")
                time.sleep(2.0)

    def _update_live_display(self, table_data: Dict) -> None:
        """Update the live display with scraped table data."""
        try:
            # Update table status
            if self.table_status_label:
                status = table_data.get('status', 'Active')
                confidence = table_data.get('confidence', 0)
                self.table_status_label.config(
                    text=f"{status} ({confidence:.1f}% confidence)",
                    fg=COLORS["accent_success"] if confidence > 70 else COLORS["accent_warning"]
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
                    self.player_labels[seat]["name"].config(
                        text=name,
                        fg=COLORS["text_primary"] if name != 'Empty' else COLORS["text_secondary"]
                    )
                    
                    # Update stack
                    stack = player_info.get('stack', 0)
                    self.player_labels[seat]["stack"].config(
                        text=f"${stack}" if stack > 0 else "$0"
                    )
                    
                    # Update hole cards
                    hole_cards = player_info.get('hole_cards', ['', ''])
                    self.player_labels[seat]["card1"].config(
                        text=hole_cards[0] if hole_cards[0] else "[ ]"
                    )
                    self.player_labels[seat]["card2"].config(
                        text=hole_cards[1] if len(hole_cards) > 1 and hole_cards[1] else "[ ]"
                    )
                    
                    # Update status
                    status = player_info.get('status', '')
                    self.player_labels[seat]["status"].config(
                        text=status,
                        fg=COLORS["accent_success"] if status == "Active" else COLORS["text_secondary"]
                    )

        except Exception as e:
            print(f"Display update error: {e}")

    # ------------------------------------------------------------------
    def update_autopilot_status(self, active: bool) -> None:
        """Update autopilot status display."""
        if not self.status_label:
            return
        
        if active:
            self.status_label.config(text="Active - Live data updating", fg=COLORS["accent_success"])
        else:
            self.status_label.config(text="Inactive - Manual mode only", fg=COLORS["text_secondary"])

    def focus_workspace(self) -> None:
        """Focus the manual workspace."""
        if self.manual_panel is None:
            return
        try:
            self.manual_panel.focus_set()
        except Exception:
            pass

    def stop_updates(self) -> None:
        """Stop the live update thread."""
        self._stop_updates = True


__all__ = ["LiveTableSection"]