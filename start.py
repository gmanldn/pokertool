#!/usr/bin/env python3
from __future__ import annotations
"""
start.py — root-level wrapper that delegates to tools/poker_go.py

Usage:
  python3 start.py            # runs poker_go (with pre-scan)
  python3 start.py --no-scan  # skip the auto-fix scan if supported by poker_go
"""
import sys
from pathlib import Path
import importlib.util

def _load_tools_poker_go():
    repo_root = Path(__file__).resolve().parent
    pg = repo_root / "tools" / "poker_go.py"
    if not pg.exists():
        raise FileNotFoundError(f"Could not find tools/poker_go.py at: {pg}")
    spec = importlib.util.spec_from_file_location("tools_poker_go", pg)
    if not spec or not spec.loader:
        raise ImportError("Failed to prepare loader for tools/poker_go.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod

def main() -> int:
    mod = _load_tools_poker_go()
    entry = getattr(mod, "main", None) or getattr(mod, "run", None)
    if not callable(entry):
        raise SystemExit("tools/poker_go.py must expose a callable main() or run().")
    # Prefer passing argv to main(argv: Optional[list[str]]), fall back to no-arg call.
    try:
        rv = entry(sys.argv[1:])  # type: ignore[misc]
    except TypeError:
        rv = entry()              # type: ignore[misc]
    return int(rv) if isinstance(rv, int) else 0

if __name__ == "__main__":
    raise SystemExit(main())
