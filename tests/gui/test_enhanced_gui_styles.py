#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest.mock import MagicMock, patch

from pokertool.enhanced_gui import COLORS, IntegratedPokerAssistant


def test_notebook_tab_style_configuration():
    """Ensure notebook tab styling is configured with contrasting colors."""
    app = IntegratedPokerAssistant.__new__(IntegratedPokerAssistant)

    with patch("pokertool.enhanced_gui.ttk.Style") as mock_style_cls, patch(
        "pokertool.enhanced_gui.sys.platform",
        "linux",
    ):
        style_instance = mock_style_cls.return_value
        # Protect theme_use for linux to avoid KeyError when theme missing
        style_instance.theme_use = MagicMock()

        app._setup_styles()

    style_instance.configure.assert_any_call("TNotebook", background=COLORS["bg_dark"])
    style_instance.configure.assert_any_call(
        "TNotebook.Tab",
        background=COLORS["bg_medium"],
        foreground=COLORS["text_primary"],
        padding=[12, 6],
    )
    style_instance.map.assert_called_with(
        "TNotebook.Tab",
        background=[("selected", COLORS["bg_dark"]), ("!selected", COLORS["bg_medium"])],
        foreground=[("selected", COLORS["accent_primary"]), ("!selected", COLORS["text_primary"])],
    )
