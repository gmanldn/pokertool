#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Autopilot control panel for the enhanced GUI.

Encapsulates the dedicated Tkinter widget that exposes Autopilot controls,
statistics, and status feedback. The widget keeps translation handling and UI
state locally while notifying the host window through callbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk

from pokertool.i18n import (
    format_currency,
    format_decimal,
    register_locale_listener,
    translate,
    unregister_locale_listener,
)

from .style import COLORS, FONTS


@dataclass
class AutopilotState:
    """State snapshot for Autopilot."""

    active: bool = False
    scraping: bool = False
    site: str = "CHROME"
    tables_detected: int = 0
    actions_taken: int = 0
    last_action: str = "None"
    last_action_key: Optional[str] = "autopilot.last_action.none"
    last_decision: str = "None"
    profit_session: float = 0.0
    hands_played: int = 0
    start_time: Optional[datetime] = None


class AutopilotControlPanel(tk.Frame):
    """Tkinter frame that renders Autopilot controls and statistics."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        on_toggle_autopilot=None,
        on_settings_changed=None,
    ) -> None:
        super().__init__(parent, bg=COLORS["bg_medium"], relief=tk.RAISED, bd=3)

        self.on_toggle_autopilot = on_toggle_autopilot
        self.on_settings_changed = on_settings_changed

        self.state = AutopilotState()
        self.animation_running = False
        self._animation_id: Optional[str] = None
        self._translation_bindings: List[Tuple[Any, str, str, Dict[str, Any]]] = []
        self._locale_listener_token: Optional[int] = None

        self._build_ui()
        self._start_animation()

        self._locale_listener_token = register_locale_listener(self.apply_translations)
        self.apply_translations()

        self._on_site_changed()

        self.bind("<Destroy>", self._on_destroy)

    # Lifecycle ------------------------------------------------------------
    def _on_destroy(self, _event=None) -> None:
        """Ensure resources are cleaned up when the widget is removed."""

        self.animation_running = False
        if self._animation_id:
            try:
                self.after_cancel(self._animation_id)
            except tk.TclError:
                pass
            finally:
                self._animation_id = None

        if self._locale_listener_token is not None:
            unregister_locale_listener(self._locale_listener_token)
            self._locale_listener_token = None

    # Translation helpers --------------------------------------------------
    def _register_translation(self, widget: Any, key: str, attr: str = "text", **kwargs: Any) -> None:
        self._translation_bindings.append((widget, key, attr, kwargs))
        try:
            widget.configure(**{attr: translate(key, **kwargs)})
        except tk.TclError:
            pass

    def apply_translations(self, _locale_code: Optional[str] = None) -> None:
        for widget, key, attr, kwargs in list(self._translation_bindings):
            try:
                widget.configure(**{attr: translate(key, **kwargs)})
            except tk.TclError:
                continue

        if self.state.active:
            self.status_label.config(text=translate("autopilot.status.active"))
            self.autopilot_button.config(text=translate("autopilot.button.stop"))
        else:
            self.status_label.config(text=translate("autopilot.status.inactive"))
            self.autopilot_button.config(text=translate("autopilot.button.start"))

        if self.state.last_action_key:
            self.last_action_label.config(text=translate(self.state.last_action_key))
        elif not self.state.last_action:
            self.last_action_label.config(text=translate("autopilot.last_action.none"))

        self._refresh_statistics()

    def _refresh_statistics(self) -> None:
        self.tables_label.config(text=format_decimal(self.state.tables_detected, digits=0))
        self.hands_label.config(text=format_decimal(self.state.hands_played, digits=0))
        self.actions_label.config(text=format_decimal(self.state.actions_taken, digits=0))
        profit_color = (
            COLORS["accent_success"] if self.state.profit_session >= 0 else COLORS["accent_danger"]
        )
        self.profit_label.config(text=format_currency(self.state.profit_session), fg=profit_color)

    # UI construction ------------------------------------------------------
    def _build_ui(self) -> None:
        title_frame = tk.Frame(self, bg=COLORS["bg_medium"])
        title_frame.pack(fill="x", pady=10)

        title_label = tk.Label(
            title_frame,
            text="",
            font=FONTS["title"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        title_label.pack()
        self.title_label = title_label
        self._register_translation(title_label, "autopilot.title")

        status_frame = tk.Frame(self, bg=COLORS["bg_medium"])
        status_frame.pack(fill="x", pady=5)

        self.status_label = tk.Label(
            status_frame,
            text=translate("autopilot.status.inactive"),
            font=FONTS["status"],
            bg=COLORS["bg_medium"],
            fg=COLORS["autopilot_inactive"],
        )
        self.status_label.pack()

        self.autopilot_button = tk.Button(
            self,
            text=translate("autopilot.button.start"),
            font=FONTS["autopilot"],
            bg=COLORS["autopilot_inactive"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["autopilot_active"],
            activeforeground=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=5,
            width=20,
            height=3,
            command=self._toggle_autopilot,
        )
        self.autopilot_button.pack(pady=20)

        settings_frame = tk.LabelFrame(
            self,
            text=translate("autopilot.settings.title"),
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2,
        )
        settings_frame.pack(fill="x", padx=10, pady=10)
        self._register_translation(settings_frame, "autopilot.settings.title")

        site_frame = tk.Frame(settings_frame, bg=COLORS["bg_medium"])
        site_frame.pack(fill="x", padx=10, pady=5)

        site_label = tk.Label(
            site_frame,
            text="",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        site_label.pack(side="left")
        self._register_translation(site_label, "autopilot.settings.site")

        self.site_var = tk.StringVar(value=self.state.site)
        site_combo = ttk.Combobox(
            site_frame,
            textvariable=self.site_var,
            values=["GENERIC", "POKERSTARS", "PARTYPOKER", "IGNITION", "BOVADA", "CHROME"],
            state="readonly",
            width=15,
        )
        site_combo.pack(side="right")
        site_combo.bind("<<ComboboxSelected>>", self._on_site_changed)
        site_combo.set(self.state.site)

        strategy_frame = tk.Frame(settings_frame, bg=COLORS["bg_medium"])
        strategy_frame.pack(fill="x", padx=10, pady=5)

        strategy_label = tk.Label(
            strategy_frame,
            text="",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        strategy_label.pack(side="left")
        self._register_translation(strategy_label, "autopilot.settings.strategy")

        self.strategy_var = tk.StringVar(value="GTO")
        strategy_combo = ttk.Combobox(
            strategy_frame,
            textvariable=self.strategy_var,
            values=["GTO", "Aggressive", "Conservative", "Exploitative"],
            state="readonly",
            width=15,
        )
        strategy_combo.pack(side="right")

        self.auto_detect_var = tk.BooleanVar(value=True)
        auto_detect_cb = tk.Checkbutton(
            settings_frame,
            text=translate("autopilot.settings.auto_detect"),
            variable=self.auto_detect_var,
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_light"],
        )
        auto_detect_cb.pack(anchor="w", padx=10, pady=2)
        self._register_translation(auto_detect_cb, "autopilot.settings.auto_detect")

        self.auto_scraper_var = tk.BooleanVar(value=True)
        auto_scraper_cb = tk.Checkbutton(
            settings_frame,
            text=translate("autopilot.settings.auto_scraper"),
            variable=self.auto_scraper_var,
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_light"],
        )
        auto_scraper_cb.pack(anchor="w", padx=10, pady=2)
        self._register_translation(auto_scraper_cb, "autopilot.settings.auto_scraper")

        self.continuous_update_var = tk.BooleanVar(value=True)
        continuous_update_cb = tk.Checkbutton(
            settings_frame,
            text=translate("autopilot.settings.continuous_updates"),
            variable=self.continuous_update_var,
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_light"],
        )
        continuous_update_cb.pack(anchor="w", padx=10, pady=2)
        self._register_translation(continuous_update_cb, "autopilot.settings.continuous_updates")

        self.auto_gto_var = tk.BooleanVar(value=False)
        auto_gto_cb = tk.Checkbutton(
            settings_frame,
            text=translate("autopilot.settings.auto_gto"),
            variable=self.auto_gto_var,
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            selectcolor=COLORS["bg_light"],
        )
        auto_gto_cb.pack(anchor="w", padx=10, pady=2)
        self._register_translation(auto_gto_cb, "autopilot.settings.auto_gto")

        stats_frame = tk.LabelFrame(
            self,
            text=translate("autopilot.stats.title"),
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2,
        )
        stats_frame.pack(fill="x", padx=10, pady=10)
        self._register_translation(stats_frame, "autopilot.stats.title")

        stats_grid = tk.Frame(stats_frame, bg=COLORS["bg_medium"])
        stats_grid.pack(fill="x", padx=10, pady=10)

        tables_header = tk.Label(
            stats_grid,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        tables_header.grid(row=0, column=0, sticky="w")
        self._register_translation(tables_header, "autopilot.stats.tables")
        self.tables_label = tk.Label(
            stats_grid,
            text="0",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_success"],
        )
        self.tables_label.grid(row=0, column=1, sticky="w")

        hands_header = tk.Label(
            stats_grid,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        hands_header.grid(row=0, column=2, sticky="w", padx=(20, 0))
        self._register_translation(hands_header, "autopilot.stats.hands")
        self.hands_label = tk.Label(
            stats_grid,
            text="0",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_success"],
        )
        self.hands_label.grid(row=0, column=3, sticky="w")

        actions_header = tk.Label(
            stats_grid,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        actions_header.grid(row=1, column=0, sticky="w")
        self._register_translation(actions_header, "autopilot.stats.actions")
        self.actions_label = tk.Label(
            stats_grid,
            text="0",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_warning"],
        )
        self.actions_label.grid(row=1, column=1, sticky="w")

        profit_header = tk.Label(
            stats_grid,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        profit_header.grid(row=1, column=2, sticky="w", padx=(20, 0))
        self._register_translation(profit_header, "autopilot.stats.profit")
        self.profit_label = tk.Label(
            stats_grid,
            text="$0.00",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_success"],
        )
        self.profit_label.grid(row=1, column=3, sticky="w")

        action_frame = tk.Frame(self, bg=COLORS["bg_medium"])
        action_frame.pack(fill="x", padx=10, pady=5)

        last_action_label = tk.Label(
            action_frame,
            text="",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        last_action_label.pack(side="left")
        self._register_translation(last_action_label, "autopilot.last_action")

        self.last_action_label = tk.Label(
            action_frame,
            text=translate("autopilot.last_action.none"),
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_primary"],
        )
        self.last_action_label.pack(side="right")

    # Interaction ----------------------------------------------------------
    def _toggle_autopilot(self) -> None:
        self.state.active = not self.state.active

        if self.state.active:
            self.state.start_time = datetime.now()
            self.autopilot_button.config(bg=COLORS["autopilot_active"])
            self.status_label.config(fg=COLORS["autopilot_active"])
        else:
            self.autopilot_button.config(bg=COLORS["autopilot_inactive"])
            self.status_label.config(fg=COLORS["autopilot_inactive"])

        self.apply_translations()

        if self.on_toggle_autopilot:
            self.on_toggle_autopilot(self.state.active)

    def _on_site_changed(self, _event=None) -> None:
        selected_site = self.site_var.get()
        self.state.site = selected_site
        if self.on_settings_changed:
            self.on_settings_changed("site", selected_site)

    def _start_animation(self) -> None:
        if not self.animation_running:
            self.animation_running = True
            self._animation_id = self.after(500, self._animate_status)

    def _animate_status(self) -> None:
        if not self.animation_running:
            return

        try:
            if not self.winfo_exists():
                self.animation_running = False
                return

            if self.state.active:
                current_color = self.status_label.cget("fg")
                new_color = (
                    COLORS["autopilot_standby"]
                    if current_color == COLORS["autopilot_active"]
                    else COLORS["autopilot_active"]
                )
                self.status_label.config(fg=new_color)

            if self.animation_running and self.winfo_exists():
                self._animation_id = self.after(500, self._animate_status)
        except tk.TclError:
            self.animation_running = False
            self._animation_id = None
        except Exception as exc:
            print(f"Animation error: {exc}")
            self.animation_running = False
            self._animation_id = None

    def update_statistics(self, stats_update: Dict[str, Any]) -> None:
        if "tables_detected" in stats_update:
            self.state.tables_detected = stats_update["tables_detected"]

        if "hands_played" in stats_update:
            self.state.hands_played = stats_update["hands_played"]

        if "actions_taken" in stats_update:
            self.state.actions_taken = stats_update["actions_taken"]

        if "profit_session" in stats_update:
            self.state.profit_session = stats_update["profit_session"]

        if "last_action_key" in stats_update:
            key = stats_update["last_action_key"]
            self.state.last_action_key = key
            self.state.last_action = translate(key)
            self.last_action_label.config(text=self.state.last_action)
        elif "last_action" in stats_update:
            self.state.last_action = stats_update["last_action"]
            self.state.last_action_key = None
            self.last_action_label.config(text=self.state.last_action)

        self._refresh_statistics()
        if not self.state.last_action:
            self.last_action_label.config(text=translate("autopilot.last_action.none"))
            self.state.last_action_key = "autopilot.last_action.none"


__all__ = ["AutopilotControlPanel", "AutopilotState"]
