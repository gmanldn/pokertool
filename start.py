#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
import importlib
import importlib.util

def _load_poker_go():
    # 1) Try normal import (works if repo root is on sys.path)
    try:
        return importlib.import_module("poker_go")
    except Exception:
        # 2) Fallback: import from a sibling file next to start.py
        here = Path(__file__).resolve().parent
        pg = here / "poker_go.py"
        if not pg.exists():
            raise FileNotFoundError(f"poker_go.py not found at: {pg}")
        spec = importlib.util.spec_from_file_location("poker_go", pg)
        if not spec or not spec.loader:
            raise ImportError("Failed to prepare loader for poker_go.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod

def main() -> int:
    mod = _load_poker_go()
    entry = getattr(mod, "main", None) or getattr(mod, "run", None)
    if not callable(entry):
        raise SystemExit("poker_go must expose a callable main() or run().")
    # pass through CLI args (e.g., --no-scan)
    rv = entry(sys.argv[1:]) if entry.__code__.co_argcount else entry()
    return int(rv) if isinstance(rv, int) else 0

if __name__ == "__main__":
    raise SystemExit(main())
