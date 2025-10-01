"""Tests for the theme system utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.theme_system import (
    MarketplaceEntry,
    Palette,
    Theme,
    ThemeEditor,
    ThemeEngine,
    ThemeMarketplace,
    Typography,
)


def create_engine(tmp_path: Path) -> ThemeEngine:
    storage = tmp_path / "themes"
    return ThemeEngine(storage_dir=storage)


def build_theme(theme_id: str, name: str, base_color: str) -> Theme:
    palette = Palette(
        primary=base_color,
        secondary="#222",
        accent="#ff9900",
        background="#111111",
        text="#ffffff",
    )
    typography = Typography(font_family="Inter", base_size=14)
    return Theme(theme_id=theme_id, name=name, palette=palette, typography=typography, sounds_enabled=True)


def test_theme_registration_and_application(tmp_path):
    engine = create_engine(tmp_path)
    midnight = build_theme("midnight", "Midnight", "#0a0f2f")
    engine.register_theme(midnight, activate=True)

    applied = engine.apply_theme("midnight", components=["window", "toolbar"])
    assert applied["window"]["background"] == "#111111"
    assert engine.active_theme() and engine.active_theme().theme_id == "midnight"

    preview = engine.preview_theme(midnight)
    assert preview["preview_window"]["accent"] == "#ff9900"


def test_theme_editor_and_marketplace(tmp_path):
    engine = create_engine(tmp_path)
    editor = ThemeEditor(engine)
    base_theme = build_theme("daylight", "Daylight", "#fafafa")
    draft = editor.create_draft("draft1", base_theme_id=None, theme=base_theme)
    draft.theme.palette.accent = "#33aaff"
    editor.update_draft("draft1", draft.theme)
    published = editor.publish_draft("draft1", activate=True)
    assert engine.get_theme(published.theme_id)

    marketplace = ThemeMarketplace()
    entry = MarketplaceEntry(theme_id="daylight", author="Coach", price=4.99, description="Bright theme")
    marketplace.register_entry(entry)
    download = marketplace.download_theme("daylight")
    assert download.downloads == 1
    listings = marketplace.list_entries()
    assert listings[0].theme_id == "daylight"
