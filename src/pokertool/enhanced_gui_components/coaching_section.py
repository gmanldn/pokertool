#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Coaching tab implementation for the enhanced GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from datetime import datetime
from typing import Any, Dict, List, Optional

from pokertool.core import Card, Position, analyse_hand, parse_card
from pokertool.coaching_system import RealTimeAdvice
from pokertool.i18n import format_decimal, translate
from pokertool.enhanced_gui_config import load_panel_config

from .style import COLORS, FONTS


class CoachingSection:
    """Encapsulates coaching UI and interactions."""

    def __init__(self, host: Any, parent: tk.Misc) -> None:
        self.host = host
        self.parent = parent

        self.coaching_system = host.coaching_system
        self._config = load_panel_config('coaching_panel')

        # UI elements
        self.advice_text: Optional[tk.Text] = None
        self.mistake_tree: Optional[ttk.Treeview] = None
        self.tips_text: Optional[tk.Text] = None
        self.progress_vars: Dict[str, tk.StringVar] = {}
        self.last_tip_var: Optional[tk.StringVar] = None
        self.scenario_tree: Optional[ttk.Treeview] = None
        self.action_var: Optional[tk.StringVar] = None
        self.pot_var: Optional[tk.StringVar] = None
        self.to_call_var: Optional[tk.StringVar] = None
        self.position_var: Optional[tk.StringVar] = None

        # Latest context for evaluation
        self._latest_table_state = None
        self._latest_hand_result = None
        self._latest_table_stage = None
        self._latest_position = None

        self._build_ui(parent)
        self._populate_scenarios()
        if self.coaching_system:
            self._refresh_tips(self.coaching_system.get_personalized_tips())
            self._refresh_progress_summary()

    # UI -----------------------------------------------------------------
    def _build_ui(self, parent: tk.Misc) -> None:
        parent.configure(bg=COLORS["bg_dark"])

        title = tk.Label(
            parent,
            text="",
            font=FONTS["title"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        )
        title.pack(pady=(10, 0))
        self.host._register_widget_translation(title, "coaching.title")

        main_frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        left = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        right.pack(side="left", fill="both", expand=True)

        advice_frame = tk.LabelFrame(
            left,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        advice_frame.pack(fill="x", pady=(0, 12))
        self.host._register_widget_translation(advice_frame, "coaching.sections.advice")

        self.advice_text = tk.Text(
            advice_frame,
            height=6,
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            font=FONTS["analysis"],
            wrap="word",
            state="disabled",
        )
        self.advice_text.pack(fill="both", expand=True, padx=10, pady=10)

        refresh_button = ttk.Button(
            advice_frame,
            text="",
            command=self.refresh_advice,
        )
        refresh_button.pack(padx=10, pady=(0, 10), anchor="e")
        self.host._register_widget_translation(refresh_button, "coaching.buttons.refresh_advice")

        mistake_frame = tk.LabelFrame(
            left,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        mistake_frame.pack(fill="both", expand=True, pady=(0, 12))
        self.host._register_widget_translation(mistake_frame, "coaching.sections.mistakes")

        raw_columns = self._config.get('mistakeColumns', [])
        column_defs = [
            entry for entry in raw_columns
            if isinstance(entry, dict) and entry.get('id')
        ]
        if not column_defs:
            column_defs = [
                {"id": "category", "translationKey": "coaching.mistakes.category", "width": 140},
                {"id": "severity", "translationKey": "coaching.mistakes.severity", "width": 120},
                {"id": "equity", "translationKey": "coaching.mistakes.equity", "width": 110},
                {"id": "recommendation", "translationKey": "coaching.mistakes.recommendation", "width": 220},
            ]

        columns = tuple(col['id'] for col in column_defs)
        self.mistake_tree = ttk.Treeview(
            mistake_frame,
            columns=columns,
            show="headings",
            height=6,
        )
        for col in column_defs:
            col_id = col['id']
            translation_key = col.get('translationKey', f'coaching.mistakes.{col_id}')
            width = int(col.get('width', 140))
            self.mistake_tree.heading(col_id, text=translate(translation_key))
            self.mistake_tree.column(col_id, width=width, anchor="center")

        mistake_scroll = ttk.Scrollbar(mistake_frame, orient="vertical", command=self.mistake_tree.yview)
        self.mistake_tree.configure(yscrollcommand=mistake_scroll.set)
        self.mistake_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        mistake_scroll.pack(side="left", fill="y", padx=(0, 10), pady=10)

        tips_frame = tk.LabelFrame(
            right,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        tips_frame.pack(fill="both", expand=True, pady=(0, 12))
        self.host._register_widget_translation(tips_frame, "coaching.sections.tips")

        self.tips_text = tk.Text(
            tips_frame,
            height=6,
            bg=COLORS["bg_light"],
            fg=COLORS["text_primary"],
            font=FONTS["body"],
            wrap="word",
            state="disabled",
        )
        self.tips_text.pack(fill="both", expand=True, padx=10, pady=10)

        progress_frame = tk.LabelFrame(
            right,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        progress_frame.pack(fill="x", pady=(0, 12))
        self.host._register_widget_translation(progress_frame, "coaching.sections.progress")

        raw_progress = self._config.get('progressMetrics', [])
        progress_entries = [
            entry for entry in raw_progress
            if isinstance(entry, dict) and entry.get('key')
        ]
        if not progress_entries:
            progress_entries = [
                {'key': 'hands', 'translationKey': 'coaching.progress.hands'},
                {'key': 'accuracy', 'translationKey': 'coaching.progress.accuracy'},
                {'key': 'streak', 'translationKey': 'coaching.progress.streak'},
                {'key': 'scenarios', 'translationKey': 'coaching.progress.scenarios'},
            ]

        for row, entry in enumerate(progress_entries):
            key = str(entry['key'])
            translation_key = entry.get('translationKey', f'coaching.progress.{key}')

            label_widget = tk.Label(
                progress_frame,
                text="",
                font=FONTS["body"],
                bg=COLORS["bg_medium"],
                fg=COLORS["text_primary"],
            )
            label_widget.grid(row=row, column=0, sticky="w", padx=10, pady=4)
            self.host._register_widget_translation(label_widget, translation_key)

            var = tk.StringVar(value="-")
            self.progress_vars[key] = var
            value_label = tk.Label(
                progress_frame,
                textvariable=var,
                font=FONTS["body"],
                bg=COLORS["bg_medium"],
                fg=COLORS["accent_primary"],
            )
            value_label.grid(row=row, column=1, sticky="w", padx=10, pady=4)

        tip_frame = tk.Frame(progress_frame, bg=COLORS["bg_medium"])
        tip_frame.grid(row=len(progress_entries), column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 4))

        tk.Label(
            tip_frame,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).pack(anchor="w")
        self.host._register_widget_translation(tip_frame.winfo_children()[0], "coaching.tips.last_tip")

        self.last_tip_var = tk.StringVar(value=translate("coaching.tips.empty"))
        tk.Label(
            tip_frame,
            textvariable=self.last_tip_var,
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_primary"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        scenarios_frame = tk.LabelFrame(
            right,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        scenarios_frame.pack(fill="both", expand=True)
        self.host._register_widget_translation(scenarios_frame, "coaching.sections.scenarios")

        columns = ("stage", "focus", "difficulty", "status")
        self.scenario_tree = ttk.Treeview(
            scenarios_frame,
            columns=columns,
            show="headings",
            height=6,
        )
        headings = {
            "stage": translate("coaching.scenarios.stage"),
            "focus": translate("coaching.scenarios.focus"),
            "difficulty": translate("coaching.scenarios.difficulty"),
            "status": translate("coaching.scenarios.status"),
        }
        widths = {"stage": 110, "focus": 140, "difficulty": 120, "status": 130}
        for col in columns:
            self.scenario_tree.heading(col, text=headings[col])
            self.scenario_tree.column(col, width=widths[col], anchor="center")

        scenario_scroll = ttk.Scrollbar(scenarios_frame, orient="vertical", command=self.scenario_tree.yview)
        self.scenario_tree.configure(yscrollcommand=scenario_scroll.set)
        self.scenario_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scenario_scroll.pack(side="left", fill="y", padx=(0, 10), pady=10)

        scenario_buttons = tk.Frame(scenarios_frame, bg=COLORS["bg_medium"])
        scenario_buttons.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Button(
            scenario_buttons,
            text=translate("coaching.buttons.refresh_scenarios"),
            command=self._populate_scenarios,
        ).pack(fill="x", pady=4)
        ttk.Button(
            scenario_buttons,
            text=translate("coaching.buttons.mark_complete"),
            command=self.mark_selected_scenario_completed,
        ).pack(fill="x", pady=4)
        ttk.Button(
            scenario_buttons,
            text=translate("coaching.buttons.launch_training"),
            command=self.launch_training_scenario,
        ).pack(fill="x", pady=4)

        eval_frame = tk.LabelFrame(
            scenarios_frame,
            text=translate("coaching.sections.evaluate"),
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        eval_frame.pack(fill="x", padx=10, pady=(20, 0))

        actions = translate("coaching.evaluate.actions").split(",")
        actions = [a.strip().upper() for a in actions if a.strip()]
        if not actions:
            actions = ["FOLD", "CALL", "RAISE"]

        tk.Label(
            eval_frame,
            text=translate("coaching.evaluate.action"),
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).grid(row=0, column=0, sticky="w", padx=10, pady=6)

        self.action_var = tk.StringVar(value=actions[0])
        ttk.Combobox(
            eval_frame,
            textvariable=self.action_var,
            values=actions,
            state="readonly",
            width=12,
        ).grid(row=0, column=1, sticky="w", padx=10, pady=6)

        tk.Label(
            eval_frame,
            text=translate("coaching.evaluate.pot"),
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).grid(row=0, column=2, sticky="w", padx=10, pady=6)

        self.pot_var = tk.StringVar()
        ttk.Entry(eval_frame, textvariable=self.pot_var, width=10).grid(row=0, column=3, padx=10, pady=6, sticky="w")

        tk.Label(
            eval_frame,
            text=translate("coaching.evaluate.to_call"),
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).grid(row=1, column=0, sticky="w", padx=10, pady=6)

        self.to_call_var = tk.StringVar()
        ttk.Entry(eval_frame, textvariable=self.to_call_var, width=10).grid(row=1, column=1, padx=10, pady=6, sticky="w")

        tk.Label(
            eval_frame,
            text=translate("coaching.evaluate.position"),
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).grid(row=1, column=2, sticky="w", padx=10, pady=6)

        self.position_var = tk.StringVar(value="AUTO")
        ttk.Combobox(
            eval_frame,
            textvariable=self.position_var,
            values=["AUTO", "BTN", "CO", "MP", "SB", "BB"],
            state="readonly",
            width=12,
        ).grid(row=1, column=3, padx=10, pady=6, sticky="w")

        evaluate_button = ttk.Button(
            eval_frame,
            text=translate("coaching.buttons.evaluate"),
            command=self.evaluate_recent_hand,
        )
        evaluate_button.grid(row=2, column=0, columnspan=4, padx=10, pady=(10, 12), sticky="ew")
        self.host._register_widget_translation(evaluate_button, "coaching.buttons.evaluate")

    # Behavior ------------------------------------------------------------
    def refresh_advice(self) -> None:
        if not self.coaching_system or not self.advice_text:
            return
        if self._latest_table_state is None:
            messagebox.showinfo(translate("tab.coaching"), translate("coaching.dialog.no_table_state"))
            return
        advice = self.coaching_system.get_real_time_advice(self._latest_table_state)
        if advice:
            self.update_advice(advice)

    def update_advice(self, advice: RealTimeAdvice) -> None:
        if not self.advice_text:
            return
        self.advice_text.configure(state="normal")
        self.advice_text.delete("1.0", tk.END)
        self.advice_text.insert("end", f"{advice.summary}\n\n{advice.reasoning}")
        self.advice_text.configure(state="disabled")

    def append_mistakes(self, mistakes: List[Any]) -> None:
        if not self.mistake_tree:
            return
        for mistake in mistakes:
            self.mistake_tree.insert(
                "",
                "end",
                values=(
                    mistake.category,
                    mistake.severity,
                    format_decimal(mistake.equity_delta, digits=2),
                    mistake.recommendation,
                ),
            )
        rows = self.mistake_tree.get_children()
        max_rows = 100
        if len(rows) > max_rows:
            for item in rows[:-max_rows]:
                self.mistake_tree.delete(item)

    def evaluate_recent_hand(self) -> None:
        if not self.coaching_system:
            messagebox.showerror(translate("tab.coaching"), translate("coaching.dialog.no_coaching_system"))
            return

        action = (self.action_var.get() if self.action_var else "fold").lower()

        def to_float(text: Optional[str]) -> Optional[float]:
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                return None

        pot = to_float(self.pot_var.get() if self.pot_var else None)
        to_call = to_float(self.to_call_var.get() if self.to_call_var else None)

        position = None
        if self.position_var:
            selected = self.position_var.get()
            if selected == "AUTO":
                position = self._resolve_position(self._latest_position)
            else:
                position = self._resolve_position(selected)

        feedback = self.coaching_system.evaluate_hand(
            self._latest_hand_result,
            action,
            pot=pot,
            to_call=to_call,
            position=position,
            table_stage=self._latest_table_stage,
        )

        if feedback.real_time_advice:
            self.update_advice(feedback.real_time_advice)
        if feedback.mistakes:
            self.append_mistakes(feedback.mistakes)
        if self.coaching_system:
            self._refresh_tips(self.coaching_system.get_personalized_tips())
        if feedback.personalized_tips and self.last_tip_var is not None:
            self.last_tip_var.set(feedback.personalized_tips[0])
        self._refresh_progress_summary()

    def mark_selected_scenario_completed(self) -> None:
        if not self.coaching_system or not self.scenario_tree:
            return
        selection = self.scenario_tree.selection()
        if not selection:
            messagebox.showinfo(translate("tab.coaching"), translate("coaching.dialog.no_scenario"))
            return
        scenario_id = selection[0]
        self.coaching_system.mark_scenario_completed(scenario_id)
        self._populate_scenarios()
        self._refresh_progress_summary()

    def launch_training_scenario(self) -> None:
        if not self.coaching_system or not self.scenario_tree:
            return
        selection = self.scenario_tree.selection()
        if not selection:
            messagebox.showinfo(translate("tab.coaching"), translate("coaching.dialog.no_scenario"))
            return
        scenario_id = selection[0]
        scenario = self.coaching_system.get_training_scenario(scenario_id)
        if scenario:
            scenario.launch()

    def handle_table_state(self, table_state) -> None:
        if not self.coaching_system:
            return
        self._latest_table_state = table_state
        self._latest_table_stage = getattr(table_state, "stage", None)
        self._latest_position = getattr(table_state, "hero_position", None)

        hero_cards = self._normalize_cards(getattr(table_state, "hero_cards", []))
        board_cards = self._normalize_cards(getattr(table_state, "board_cards", []))

        position = self._resolve_position(self._latest_position)

        try:
            if hero_cards:
                self._latest_hand_result = analyse_hand(
                    hero_cards,
                    board_cards,
                    position,
                    getattr(table_state, "pot_size", None),
                    getattr(table_state, "current_bet", None),
                )
            else:
                self._latest_hand_result = None
        except Exception:
            self._latest_hand_result = None

        advice = self.coaching_system.get_real_time_advice(table_state)
        if advice:
            self.host.after(0, lambda a=advice: self.update_advice(a))

    # Helpers -------------------------------------------------------------
    def populate_scenarios(self) -> None:
        self._populate_scenarios()

    def _populate_scenarios(self) -> None:
        if not self.coaching_system or not self.scenario_tree:
            return
        for item in self.scenario_tree.get_children():
            self.scenario_tree.delete(item)
        for scenario in self.coaching_system.get_training_scenarios():
            status_key = (
                "coaching.scenario.status.completed"
                if scenario.completed
                else "coaching.scenario.status.active"
            )
            status = translate(status_key)
            self.scenario_tree.insert(
                "",
                "end",
                iid=scenario.scenario_id,
                values=(scenario.stage.title(), scenario.focus, scenario.difficulty, status),
            )

    def refresh_progress_summary(self) -> None:
        self._refresh_progress_summary()

    def _refresh_progress_summary(self) -> None:
        if not self.coaching_system or not self.progress_vars:
            return
        snapshot = self.coaching_system.get_progress_snapshot()
        if "hands" in self.progress_vars:
            self.progress_vars["hands"].set(format_decimal(snapshot.hands_reviewed, digits=0))
        if "accuracy" in self.progress_vars:
            accuracy_value = format_decimal(snapshot.accuracy_score * 100, digits=0)
            self.progress_vars["accuracy"].set(
                translate("coaching.progress.accuracy_value", value=accuracy_value)
            )
        if "streak" in self.progress_vars:
            self.progress_vars["streak"].set(
                translate(
                    "coaching.progress.streak_value",
                    days=format_decimal(snapshot.streak_days, digits=0),
                )
            )
        if "scenarios" in self.progress_vars:
            self.progress_vars["scenarios"].set(format_decimal(snapshot.scenarios_completed, digits=0))
        if self.last_tip_var is not None:
            self.last_tip_var.set(snapshot.last_tip or translate("coaching.tips.empty"))

    def refresh_tips(self, tips: List[str]) -> None:
        self._refresh_tips(tips)

    def _refresh_tips(self, tips: List[str]) -> None:
        if not self.tips_text:
            return
        self.tips_text.configure(state="normal")
        self.tips_text.delete("1.0", tk.END)
        for tip in tips:
            self.tips_text.insert(tk.END, f"• {tip}\n\n")
        self.tips_text.configure(state="disabled")

    def _resolve_position(self, value: Optional[str]) -> Optional[Position]:
        if isinstance(value, Position):
            return value
        if isinstance(value, str):
            key = value.upper()
            try:
                return Position[key]
            except KeyError:
                try:
                    return Position(key)
                except ValueError:
                    return None
        return None

    def _normalize_cards(self, cards: Optional[List[Any]]) -> List[Card]:
        normalized: List[Card] = []
        if not cards:
            return normalized
        for card in cards:
            if isinstance(card, Card):
                normalized.append(card)
            elif isinstance(card, str):
                try:
                    normalized.append(parse_card(card))
                except ValueError:
                    continue
        return normalized


__all__ = ["CoachingSection"]
