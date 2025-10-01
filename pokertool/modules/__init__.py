"""Standalone Python modules for the PokerTool project."""

from __future__ import annotations

import sys
from importlib import import_module

# Re-export commonly used helpers for convenience
from .logger import logger, log_exceptions, setup_global_exception_handler  # noqa: F401

_LEGACY_ALIAS_MAP = {
    "logger": ".logger",
    "autoconfirm": ".autoconfirm",
    "browser_tab_capture": ".browser_tab_capture",
    "hand_replay_system": ".hand_replay_system",
    "note_taking_system": ".note_taking_system",
    "poker_gui_enhanced": ".poker_gui_enhanced",
    "poker_screen_scraper": ".poker_screen_scraper",
    "range_construction_tool": ".range_construction_tool",
    "run_pokertool": ".run_pokertool",
}


def _register_legacy_aliases() -> None:
    for legacy_name, relative_module in _LEGACY_ALIAS_MAP.items():
        module = import_module(relative_module, __name__)
        sys.modules.setdefault(legacy_name, module)


_register_legacy_aliases()

__all__ = [
    "logger",
    "log_exceptions",
    "setup_global_exception_handler",
]
