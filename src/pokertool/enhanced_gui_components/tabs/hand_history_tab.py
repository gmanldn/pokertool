#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hand History Tab for Enhanced GUI
==================================

Displays complete hand history with detailed information about:
- All hands played
- Players and positions
- Actions and betting
- Board cards and hole cards
- Winners and pot sizes
- Hero performance statistics
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime

if TYPE_CHECKING:
    pass

from ..style import COLORS, FONTS


class HandHistoryTabMixin:
    """
    Mixin class providing Hand History tab building.

    This mixin provides the _build_hand_history_tab() method and supporting methods
    for displaying and managing hand history data.
    """

    def _build_hand_history_tab(self, parent: tk.Frame) -> None:
        """
        Build the Hand History tab.

        Args:
            parent: The parent frame (usually from ttk.Notebook)
        """
        # Configure parent
        parent.configure(bg=COLORS["bg_dark"])

        # Main container with padding
        main_frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header section
        self._build_hand_history_header(main_frame)

        # Statistics section
        self._build_hand_history_stats(main_frame)

        # Filter/Control section
        self._build_hand_history_controls(main_frame)

        # Hand list (table view)
        self._build_hand_history_table(main_frame)

        # Detail view
        self._build_hand_history_detail(main_frame)

        # Initialize data
        self._refresh_hand_history()

    def _build_hand_history_header(self, parent: tk.Frame) -> None:
        """Build the header section with title and refresh button."""
        header_frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        title = tk.Label(
            header_frame,
            text="📚 Hand History",
            font=FONTS["title"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"]
        )
        title.pack(side=tk.LEFT)

        # Refresh button
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 Refresh",
            font=FONTS["button"],
            bg=COLORS["button_bg"],
            fg=COLORS["button_fg"],
            activebackground=COLORS["button_active"],
            command=self._refresh_hand_history,
            relief=tk.RAISED,
            bd=2
        )
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # Export button
        export_btn = tk.Button(
            header_frame,
            text="💾 Export",
            font=FONTS["button"],
            bg=COLORS["button_bg"],
            fg=COLORS["button_fg"],
            activebackground=COLORS["button_active"],
            command=self._export_hand_history,
            relief=tk.RAISED,
            bd=2
        )
        export_btn.pack(side=tk.RIGHT, padx=5)

        # Clear button
        clear_btn = tk.Button(
            header_frame,
            text="🗑️ Clear All",
            font=FONTS["button"],
            bg=COLORS["danger"],
            fg="white",
            activebackground="#c0392b",
            command=self._clear_hand_history,
            relief=tk.RAISED,
            bd=2
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)

    def _build_hand_history_stats(self, parent: tk.Frame) -> None:
        """Build the statistics section."""
        stats_frame = tk.LabelFrame(
            parent,
            text="Statistics",
            font=FONTS["section"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2
        )
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # Stats grid
        stats_grid = tk.Frame(stats_frame, bg=COLORS["bg_medium"])
        stats_grid.pack(fill=tk.X, padx=10, pady=10)

        # Define stats
        self.hand_history_stats = {}
        stats = [
            ("Total Hands", "total_hands", "0"),
            ("Hands Won", "hands_won", "0"),
            ("Hands Lost", "hands_lost", "0"),
            ("Win Rate", "win_rate", "0.0%"),
            ("Total Net", "total_net", "$0.00"),
            ("Avg Pot Size", "avg_pot_size", "$0.00"),
        ]

        for idx, (label_text, key, default_value) in enumerate(stats):
            row = idx // 3
            col = idx % 3

            # Stat container
            stat_frame = tk.Frame(stats_grid, bg=COLORS["bg_dark"], relief=tk.RAISED, bd=1)
            stat_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            # Label
            label = tk.Label(
                stat_frame,
                text=label_text,
                font=FONTS["small"],
                bg=COLORS["bg_dark"],
                fg=COLORS["text_secondary"]
            )
            label.pack(pady=(5, 0))

            # Value
            value_label = tk.Label(
                stat_frame,
                text=default_value,
                font=FONTS["heading"],
                bg=COLORS["bg_dark"],
                fg=COLORS["accent"]
            )
            value_label.pack(pady=(0, 5))

            self.hand_history_stats[key] = value_label

        # Configure grid weights
        for i in range(3):
            stats_grid.columnconfigure(i, weight=1)

    def _build_hand_history_controls(self, parent: tk.Frame) -> None:
        """Build filter and control section."""
        control_frame = tk.LabelFrame(
            parent,
            text="Filters",
            font=FONTS["section"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2
        )
        control_frame.pack(fill=tk.X, pady=(0, 10))

        controls_grid = tk.Frame(control_frame, bg=COLORS["bg_medium"])
        controls_grid.pack(fill=tk.X, padx=10, pady=10)

        # Hero filter
        tk.Label(
            controls_grid,
            text="Hero:",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"]
        ).grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.hand_history_hero_var = tk.StringVar(value="All")
        hero_entry = tk.Entry(
            controls_grid,
            textvariable=self.hand_history_hero_var,
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            width=20
        )
        hero_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Table filter
        tk.Label(
            controls_grid,
            text="Table:",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"]
        ).grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.hand_history_table_var = tk.StringVar(value="All")
        table_entry = tk.Entry(
            controls_grid,
            textvariable=self.hand_history_table_var,
            font=FONTS["body"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            width=20
        )
        table_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Result filter
        tk.Label(
            controls_grid,
            text="Result:",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"]
        ).grid(row=0, column=4, padx=5, pady=5, sticky="e")

        self.hand_history_result_var = tk.StringVar(value="All")
        result_combo = ttk.Combobox(
            controls_grid,
            textvariable=self.hand_history_result_var,
            values=["All", "Won", "Lost", "Pushed"],
            font=FONTS["body"],
            state="readonly",
            width=15
        )
        result_combo.grid(row=0, column=5, padx=5, pady=5, sticky="ew")

        # Apply button
        apply_btn = tk.Button(
            controls_grid,
            text="Apply Filters",
            font=FONTS["button"],
            bg=COLORS["button_bg"],
            fg=COLORS["button_fg"],
            activebackground=COLORS["button_active"],
            command=self._apply_hand_history_filters,
            relief=tk.RAISED,
            bd=2
        )
        apply_btn.grid(row=0, column=6, padx=5, pady=5)

        controls_grid.columnconfigure(1, weight=1)
        controls_grid.columnconfigure(3, weight=1)

    def _build_hand_history_table(self, parent: tk.Frame) -> None:
        """Build the hand history table view."""
        table_frame = tk.LabelFrame(
            parent,
            text="Hand List",
            font=FONTS["section"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2
        )
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create Treeview with scrollbars
        tree_container = tk.Frame(table_frame, bg=COLORS["bg_dark"])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        hsb = ttk.Scrollbar(tree_container, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        columns = ("Time", "Table", "Hero", "Position", "Result", "Pot", "Net", "Stage", "Players")
        self.hand_history_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse"
        )
        self.hand_history_tree.pack(fill=tk.BOTH, expand=True)

        vsb.config(command=self.hand_history_tree.yview)
        hsb.config(command=self.hand_history_tree.xview)

        # Configure columns
        self.hand_history_tree.column("#0", width=0, stretch=tk.NO)
        column_widths = {
            "Time": 150,
            "Table": 150,
            "Hero": 120,
            "Position": 80,
            "Result": 80,
            "Pot": 80,
            "Net": 80,
            "Stage": 80,
            "Players": 70
        }

        for col in columns:
            self.hand_history_tree.column(col, width=column_widths[col], anchor="center")
            self.hand_history_tree.heading(col, text=col, command=lambda c=col: self._sort_hand_history_by(c))

        # Bind selection event
        self.hand_history_tree.bind("<<TreeviewSelect>>", self._on_hand_history_select)

        # Style
        style = ttk.Style()
        style.configure("Treeview", background=COLORS["bg_dark"], foreground=COLORS["text_primary"],
                       fieldbackground=COLORS["bg_dark"], borderwidth=0)
        style.configure("Treeview.Heading", background=COLORS["bg_medium"], foreground=COLORS["text_primary"])
        style.map("Treeview", background=[("selected", COLORS["accent"])])

    def _build_hand_history_detail(self, parent: tk.Frame) -> None:
        """Build the hand detail view."""
        detail_frame = tk.LabelFrame(
            parent,
            text="Hand Details",
            font=FONTS["section"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2
        )
        detail_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable text widget
        text_container = tk.Frame(detail_frame, bg=COLORS["bg_dark"])
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hand_history_detail_text = tk.Text(
            text_container,
            font=FONTS["mono"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
            height=8
        )
        self.hand_history_detail_text.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.hand_history_detail_text.yview)

        # Configure tags for colored text
        self.hand_history_detail_text.tag_config("hero", foreground=COLORS["success"])
        self.hand_history_detail_text.tag_config("winner", foreground=COLORS["accent"])
        self.hand_history_detail_text.tag_config("loser", foreground=COLORS["danger"])
        self.hand_history_detail_text.tag_config("header", font=FONTS["heading"], foreground=COLORS["text_primary"])

    def _refresh_hand_history(self) -> None:
        """Refresh the hand history display."""
        try:
            from pokertool.hand_history_db import get_hand_history_db
            from pokertool.user_config import get_poker_handle

            db = get_hand_history_db()
            hero_name = get_poker_handle()

            # Get statistics
            stats = db.get_statistics(hero_name=hero_name)

            # Update stats display
            self.hand_history_stats["total_hands"].config(text=str(stats.get("total_hands", 0)))
            self.hand_history_stats["hands_won"].config(text=str(stats.get("hands_won", 0)))
            self.hand_history_stats["hands_lost"].config(text=str(stats.get("hands_lost", 0)))
            self.hand_history_stats["win_rate"].config(text=f"{stats.get('win_rate', 0):.1f}%")
            self.hand_history_stats["total_net"].config(text=f"${stats.get('total_net', 0):.2f}")
            self.hand_history_stats["avg_pot_size"].config(text=f"${stats.get('avg_pot_size', 0):.2f}")

            # Get recent hands
            hands = db.get_recent_hands(limit=100, hero_name=hero_name if hero_name else None)

            # Clear tree
            for item in self.hand_history_tree.get_children():
                self.hand_history_tree.delete(item)

            # Populate tree
            for hand in hands:
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(hand.timestamp)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = hand.timestamp

                # Get hero info
                hero_pos = "?"
                for player in hand.players:
                    if player.is_hero:
                        hero_pos = player.position or "?"
                        break

                # Format values
                result_emoji = {"won": "✓", "lost": "✗", "pushed": "=", "unknown": "?"}
                result = f"{result_emoji.get(hand.hero_result, '?')} {hand.hero_result.capitalize()}"

                values = (
                    time_str,
                    hand.table_name,
                    hand.hero_name or "Unknown",
                    hero_pos,
                    result,
                    f"${hand.pot_size:.2f}",
                    f"${hand.hero_net:+.2f}",
                    hand.final_stage.value.capitalize(),
                    str(len(hand.players))
                )

                # Insert with color based on result
                tags = ()
                if hand.hero_net > 0:
                    tags = ("win",)
                elif hand.hero_net < 0:
                    tags = ("loss",)

                self.hand_history_tree.insert("", tk.END, iid=hand.hand_id, values=values, tags=tags)

            # Configure row colors
            self.hand_history_tree.tag_configure("win", background="#1e3a1e")
            self.hand_history_tree.tag_configure("loss", background="#3a1e1e")

        except Exception as e:
            print(f"Error refreshing hand history: {e}")
            import traceback
            traceback.print_exc()

    def _apply_hand_history_filters(self) -> None:
        """Apply filters to hand history display."""
        # TODO: Implement filtering logic
        self._refresh_hand_history()

    def _sort_hand_history_by(self, column: str) -> None:
        """Sort hand history by column."""
        # TODO: Implement sorting logic
        pass

    def _on_hand_history_select(self, event) -> None:
        """Handle hand selection in tree."""
        selection = self.hand_history_tree.selection()
        if not selection:
            return

        hand_id = selection[0]

        try:
            from pokertool.hand_history_db import get_hand_history_db

            db = get_hand_history_db()
            hand = db.get_hand(hand_id)

            if hand:
                self._display_hand_details(hand)
        except Exception as e:
            print(f"Error loading hand details: {e}")

    def _display_hand_details(self, hand) -> None:
        """Display detailed hand information."""
        self.hand_history_detail_text.config(state=tk.NORMAL)
        self.hand_history_detail_text.delete(1.0, tk.END)

        # Header
        self.hand_history_detail_text.insert(tk.END, f"Hand ID: {hand.hand_id}\n", "header")
        self.hand_history_detail_text.insert(tk.END, f"Table: {hand.table_name} ({hand.site})\n")
        self.hand_history_detail_text.insert(tk.END, f"Blinds: ${hand.small_blind}/{hand.big_blind}\n")
        self.hand_history_detail_text.insert(tk.END, f"Pot: ${hand.pot_size:.2f}\n")
        self.hand_history_detail_text.insert(tk.END, "\n")

        # Players
        self.hand_history_detail_text.insert(tk.END, "Players:\n", "header")
        for player in hand.players:
            tag = "hero" if player.is_hero else ""
            self.hand_history_detail_text.insert(
                tk.END,
                f"  Seat {player.seat_number}: {player.player_name} "
                f"[{player.position or '?'}] ${player.starting_stack:.2f}\n",
                tag
            )
        self.hand_history_detail_text.insert(tk.END, "\n")

        # Cards
        if hand.hero_cards:
            self.hand_history_detail_text.insert(tk.END, "Hero Cards: ", "header")
            self.hand_history_detail_text.insert(tk.END, f"{', '.join(hand.hero_cards)}\n", "hero")

        if hand.board_cards:
            self.hand_history_detail_text.insert(tk.END, "Board: ", "header")
            self.hand_history_detail_text.insert(tk.END, f"{', '.join(hand.board_cards)}\n")

        self.hand_history_detail_text.insert(tk.END, "\n")

        # Actions
        if hand.actions:
            self.hand_history_detail_text.insert(tk.END, "Actions:\n", "header")
            for action in hand.actions:
                self.hand_history_detail_text.insert(
                    tk.END,
                    f"  [{action.stage.value}] {action.player_name}: {action.action_type.value}"
                )
                if action.amount > 0:
                    self.hand_history_detail_text.insert(tk.END, f" ${action.amount:.2f}")
                self.hand_history_detail_text.insert(tk.END, "\n")
            self.hand_history_detail_text.insert(tk.END, "\n")

        # Results
        self.hand_history_detail_text.insert(tk.END, "Results:\n", "header")
        if hand.winners:
            self.hand_history_detail_text.insert(tk.END, f"  Winners: {', '.join(hand.winners)}\n", "winner")

        tag = "winner" if hand.hero_net > 0 else "loser" if hand.hero_net < 0 else ""
        self.hand_history_detail_text.insert(
            tk.END,
            f"  Hero Result: {hand.hero_result.capitalize()} (${hand.hero_net:+.2f})\n",
            tag
        )

        self.hand_history_detail_text.config(state=tk.DISABLED)

    def _export_hand_history(self) -> None:
        """Export hand history to file."""
        from tkinter import filedialog
        import json

        try:
            from pokertool.hand_history_db import get_hand_history_db

            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                db = get_hand_history_db()
                hands = db.get_recent_hands(limit=1000)

                data = [hand.to_dict() for hand in hands]

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                messagebox.showinfo("Export Complete", f"Exported {len(hands)} hands to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    def _clear_hand_history(self) -> None:
        """Clear all hand history (with confirmation)."""
        if messagebox.askyesno("Clear Hand History",
                              "Are you sure you want to delete ALL hand history?\n\nThis cannot be undone!"):
            try:
                from pokertool.hand_history_db import get_hand_history_db

                db = get_hand_history_db()
                db.clear_all_hands()

                self._refresh_hand_history()
                messagebox.showinfo("Success", "Hand history cleared")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")


__all__ = ["HandHistoryTabMixin"]
