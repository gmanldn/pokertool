"""Unit tests for the legacy poker_gui_enhanced compatibility helpers."""

from __future__ import annotations

import builtins
import importlib
import sys
import types

import pytest


MODULE_PATH = "pokertool.modules.poker_gui_enhanced"


def test_informs_when_tkinter_missing(monkeypatch):
    """Importing without Tk should raise a helpful error message."""

    original_import = builtins.__import__
    module_backup = sys.modules.get(MODULE_PATH)

    def fake_import(name, *args, **kwargs):
        if name == "tkinter" or name.startswith("tkinter."):
            raise ModuleNotFoundError("tkinter is absent")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop(MODULE_PATH, None)

    with pytest.raises(ImportError) as excinfo:
        importlib.import_module(MODULE_PATH)

    assert "Tkinter is required" in str(excinfo.value)

    if module_backup is not None:
        sys.modules[MODULE_PATH] = module_backup


def test_informs_when_gui_components_missing():
    """Missing pokertool.gui exports should surface a clear ImportError."""

    module_backup = sys.modules.get(MODULE_PATH)
    original_gui = sys.modules.get("pokertool.gui")
    sys.modules.pop(MODULE_PATH, None)
    sys.modules["pokertool.gui"] = types.ModuleType("pokertool.gui")

    with pytest.raises(ImportError) as excinfo:
        importlib.import_module(MODULE_PATH)

    assert "Unable to import pokertool.gui components" in str(excinfo.value)

    # Restore original module state
    sys.modules.pop("pokertool.gui", None)
    if original_gui is not None:
        sys.modules["pokertool.gui"] = original_gui
    if module_backup is not None:
        sys.modules[MODULE_PATH] = module_backup
