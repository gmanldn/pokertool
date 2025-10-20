"""Tkinter smoke tests for the EnhancedPokerAssistant frame."""

from __future__ import annotations

import sys
from contextlib import suppress

import pytest

try:  # Tk availability differs between runner images
    import tkinter as tk
except Exception:  # pragma: no cover - system-specific
    tk = None  # type: ignore

try:
    from pyvirtualdisplay import Display  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Display = None

from pokertool.modules.poker_gui_enhanced import EnhancedPokerAssistantFrame


pytestmark = [
    pytest.mark.requires_display,
    pytest.mark.skipif(tk is None, reason="tkinter is not available on this platform"),
]


@pytest.fixture(scope="module")
def virtual_display():
    """Start a virtual display when running headless."""
    # On Windows we rely on the native desktop session instead of Xvfb
    if sys.platform.startswith("win"):
        yield
        return

    if Display is None:
        pytest.skip("pyvirtualdisplay not installed")

    with suppress(FileNotFoundError):
        display = Display(visible=0, size=(1280, 720))
        display.start()
        try:
            yield
        finally:
            display.stop()
        return

    pytest.skip("Xvfb not available on this runner")


def test_enhanced_frame_initialises(virtual_display):
    """The enhanced frame should build without raising and expose key widgets."""
    root = tk.Tk()
    root.withdraw()
    frame: EnhancedPokerAssistantFrame | None = None
    try:
        frame = EnhancedPokerAssistantFrame(root, auto_pack=False)
        root.update_idletasks()

        assert frame.winfo_exists(), "Frame failed to mount"
        assert hasattr(frame, "table_viz") and frame.table_viz.winfo_exists()
        assert hasattr(frame, "card_selector") and frame.card_selector.winfo_exists()
    finally:
        if frame is not None:
            with suppress(Exception):
                frame.destroy()
        root.destroy()
