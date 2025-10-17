#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Settings tab implementation for the enhanced GUI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from typing import Any, Dict, List, Optional

from pokertool.i18n import (
    available_locales,
    format_currency,
    get_current_locale,
    set_locale,
    translate,
)

from .style import COLORS, FONTS


class SettingsSection:
    """Encapsulates settings UI: categories and localization controls."""

    def __init__(self, host: Any, parent: tk.Misc) -> None:
        self.host = host
        self.parent = parent

        self._locale_code_by_name: Dict[str, str] = {}
        self._locale_name_by_code: Dict[str, str] = {}
        self._locale_currency_map: Dict[str, str] = {}

        self.language_var: Optional[tk.StringVar] = None
        self.currency_display_var: Optional[tk.StringVar] = None

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        container = tk.Frame(self.parent, bg=COLORS["bg_dark"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        title = tk.Label(
            container,
            text="",
            font=FONTS["title"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        )
        title.pack(pady=(0, 20))
        self.host._register_widget_translation(title, "settings.title")

        for key in [
            "settings.category.autopilot",
            "settings.category.screen_recognition",
            "settings.category.gto",
            "settings.category.opponent_modeling",
            "settings.category.multi_table",
            "settings.category.security",
        ]:
            frame = tk.LabelFrame(
                container,
                text="",
                font=FONTS["heading"],
                bg=COLORS["bg_medium"],
                fg=COLORS["text_primary"],
            )
            frame.pack(fill="x", pady=10)
            self.host._register_widget_translation(frame, key)

            placeholder = tk.Label(
                frame,
                text="",
                font=FONTS["body"],
                bg=COLORS["bg_medium"],
                fg=COLORS["text_secondary"],
            )
            placeholder.pack(padx=10, pady=10)
            self.host._register_widget_translation(placeholder, "settings.placeholder")

        localization_frame = tk.LabelFrame(
            container,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        localization_frame.pack(fill="x", pady=10)
        self.host._register_widget_translation(localization_frame, "settings.localization.section")

        locales_available = available_locales()
        self._locale_code_by_name = {entry["name"]: entry["code"] for entry in locales_available}
        self._locale_name_by_code = {entry["code"]: entry["name"] for entry in locales_available}
        self._locale_currency_map = {entry["code"]: entry["currency"] for entry in locales_available}

        current_locale = get_current_locale()
        current_locale_name = self._locale_name_by_code.get(current_locale, current_locale)

        language_label = tk.Label(
            localization_frame,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        language_label.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.host._register_widget_translation(language_label, "settings.language.label")

        self.language_var = tk.StringVar(value=current_locale_name)
        language_combo = ttk.Combobox(
            localization_frame,
            textvariable=self.language_var,
            values=[entry["name"] for entry in locales_available],
            state="readonly",
            width=28,
        )
        language_combo.grid(row=0, column=1, sticky="w", padx=10, pady=8)
        language_combo.bind("<<ComboboxSelected>>", self._on_language_changed)

        currency_label = tk.Label(
            localization_frame,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        currency_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))
        self.host._register_widget_translation(currency_label, "settings.currency.label")

        self.currency_display_var = tk.StringVar()
        currency_value_label = tk.Label(
            localization_frame,
            textvariable=self.currency_display_var,
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_primary"],
        )
        currency_value_label.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 10))

        localization_frame.columnconfigure(1, weight=1)
        self.update_localization_display()

    # ------------------------------------------------------------------
    def update_localization_display(self) -> None:
        if not self.currency_display_var:
            return

        current_locale = get_current_locale()
        if self.language_var and current_locale in self._locale_name_by_code:
            self.language_var.set(self._locale_name_by_code[current_locale])

        currency_code = self._locale_currency_map.get(current_locale)
        if currency_code:
            sample = format_currency(1234.56, currency=currency_code)
            display_text = f"{currency_code} ({sample})"
        else:
            display_text = current_locale.upper()
        self.currency_display_var.set(display_text)

    def _on_language_changed(self, _event=None) -> None:
        if not self.language_var:
            return
        selected_name = self.language_var.get().strip()
        locale_code = self._locale_code_by_name.get(selected_name)
        if not locale_code or locale_code == get_current_locale():
            return
        try:
            set_locale(locale_code)
            messagebox.showinfo(
                translate("tab.settings"),
                translate("settings.language.applied", language=selected_name),
            )
        except Exception as exc:  # pragma: no cover - display errors to user
            messagebox.showerror(translate("tab.settings"), str(exc))


__all__ = ["SettingsSection"]
