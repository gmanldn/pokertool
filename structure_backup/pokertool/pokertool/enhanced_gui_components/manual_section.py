#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Manual play workspace section for the enhanced GUI."""

from __future__ import annotations

import tkinter as tk

from typing import Any, Optional

from pokertool.gui import EnhancedPokerAssistantFrame

from .style import COLORS, FONTS


class ManualPlaySection:
    """Encapsulates the Manual Play tab within the enhanced GUI."""

    def __init__(self, host: Any, parent: tk.Misc, *, modules_loaded: bool) -> None:
        self.host = host
        self.parent = parent
        self._modules_loaded = modules_loaded
        self.manual_panel: Optional[EnhancedPokerAssistantFrame] = None
        self.status_label: Optional[tk.Label] = None

        self._build_ui()
        self.update_autopilot_status(host.autopilot_active)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        header_frame = tk.Frame(self.parent, bg=COLORS["bg_dark"])
        header_frame.pack(fill="x", pady=(20, 10))

        manual_label = tk.Label(
            header_frame,
            text="",
            font=FONTS["title"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
        )
        manual_label.pack(anchor="w")
        self.host._register_widget_translation(manual_label, "manual.title")

        helper_text = (
            "Use the manual workspace below to select cards, adjust players, "
            "and review live analysis without leaving the main window."
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

        manual_container = tk.LabelFrame(
            content_frame,
            text="",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2,
        )
        manual_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.host._register_widget_translation(manual_container, "manual.title")

        manual_inner = tk.Frame(manual_container, bg=COLORS["bg_dark"])
        manual_inner.pack(fill="both", expand=True, padx=10, pady=10)

        if self._modules_loaded:
            try:
                self.manual_panel = EnhancedPokerAssistantFrame(manual_inner, auto_pack=False)
                self.manual_panel.pack(fill="both", expand=True)
            except Exception as manual_error:  # pragma: no cover - fallback UI
                self.manual_panel = None
                fallback = tk.Label(
                    manual_inner,
                    text=f"Manual interface unavailable: {manual_error}",
                    font=FONTS["body"],
                    bg=COLORS["bg_dark"],
                    fg=COLORS["accent_danger"],
                    wraplength=600,
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
                wraplength=600,
                justify="left",
            )
            fallback.pack(fill="both", expand=True, pady=20)

        sidebar = tk.Frame(content_frame, bg=COLORS["bg_dark"])
        sidebar.pack(side="right", fill="y")

        tips_frame = tk.LabelFrame(
            sidebar,
            text="Manual Workflow Tips",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2,
        )
        tips_frame.pack(fill="both", padx=0, pady=(0, 10))

        tips_text = (
            "1. Click cards in the grid to assign hole cards and board streets.\n"
            "2. Adjust stacks, blinds, and active seats from the control panel.\n"
            "3. Use ANALYZE HAND to refresh insights inside the workspace."
        )
        tk.Label(
            tips_frame,
            text=tips_text,
            font=FONTS["body"],
            justify="left",
            wraplength=320,
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
        ).pack(fill="x", padx=12, pady=12)

        sync_frame = tk.LabelFrame(
            sidebar,
            text="Session Sync",
            font=FONTS["heading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
            relief=tk.RAISED,
            bd=2,
        )
        sync_frame.pack(fill="both")

        tk.Label(
            sync_frame,
            text="Autopilot status:",
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        self.status_label = tk.Label(
            sync_frame,
            text="",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
        )
        self.status_label.pack(anchor="w", padx=12, pady=(0, 12))
        self.host._register_widget_translation(self.status_label, "autopilot.status.inactive")

        tk.Label(
            sync_frame,
            text="Switch tabs at any time — the manual workspace stays in sync with live updates.",
            font=FONTS["body"],
            justify="left",
            wraplength=320,
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
        ).pack(fill="x", padx=12, pady=(0, 12))

        self.host.manual_panel = self.manual_panel
        self.host.manual_status_label = self.status_label

    # ------------------------------------------------------------------
    def update_autopilot_status(self, active: bool) -> None:
        if not self.status_label:
            return
        key = "autopilot.status.active" if active else "autopilot.status.inactive"
        self.host._update_widget_translation_key(self.status_label, key)
        color = COLORS["accent_success"] if active else COLORS["text_secondary"]
        self.status_label.config(fg=color)

    def focus_workspace(self) -> None:
        if self.manual_panel is None:
            return
        try:
            self.manual_panel.focus_set()
        except Exception:
            pass


__all__ = ["ManualPlaySection"]
