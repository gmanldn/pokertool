#!/usr/bin/env python3
from __future__ import annotations

"""
poker_go.py — bootstraps the app by:
  1) finding the repo root,
  2) running code_scan.py to auto-fix syntax/structure issues,
  3) verifying compilation,
  4) launching the GUI with graceful error handling.

Usage:
  python3 poker_go.py
Options:
  --no-scan     Skip the auto-fix scan phase (not recommended)
"""

import argparse
import compileall
import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def find_repo_root(start: Path) -> Path:
    """
    Walk up until we find a marker ('.git' or 'pyproject.toml') or hit filesystem root.
    """
    cur = start.resolve()
    while True:
        if (cur / ".git").exists() or (cur / "pyproject.toml").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            return start.resolve()
        cur = parent


def run_code_scan(repo_root: Path) -> int:
    """
    Run code_scan.py with aggressive fixes and multi-pass healing.
    Prefer importing its main() directly; fall back to a subprocess.
    Returns exit code (0=OK, nonzero=errors remain).
    """
    scan = repo_root / "code_scan.py"
    if scan.exists():
        # Try to import and call main() directly
        try:
            spec = importlib.util.spec_from_file_location("code_scan", scan)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                # Emulate CLI: aggressive, 4 passes
                # Some versions expose main(); if not, fall back to subprocess below.
                if hasattr(mod, "main") and callable(mod.main):
                    # Temporarily patch argv for argparse inside code_scan
                    prev_argv = sys.argv[:]
                    try:
                        sys.argv = [str(scan), "--aggressive", "--max-passes", "4"]
                        rc = int(mod.main())  # type: ignore[call-arg]
                        return rc
                    finally:
                        sys.argv = prev_argv
        except Exception as e:
            print(f"[code_scan] import/exec failed: {e} — falling back to subprocess", file=sys.stderr)

    # Subprocess fallback (works even if code_scan not importable)
    if scan.exists():
        cmd = [sys.executable, str(scan), "--aggressive", "--max-passes", "4"]
        print(f"[code_scan] subprocess: {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=str(repo_root))
        return proc.returncode

    # If code_scan.py is missing, do a strict compile-only health check
    print("[code_scan] code_scan.py not found — doing strict compile check only", file=sys.stderr)
    ok = compileall.compile_dir(str(repo_root), quiet=1, force=False, legacy=True)
    return 0 if ok else 1


def verify_compiles(repo_root: Path) -> None:
    """
    Compile the whole repo to bytecode. Raises SystemExit on failure.
    """
    print("[verify] compiling repository to bytecode…")
    ok = compileall.compile_dir(str(repo_root), quiet=1, force=False, legacy=True)
    if not ok:
        print("[verify] ❌ compile step failed — fix the reported files above and re-run.", file=sys.stderr)
        raise SystemExit(2)
    print("[verify] ✅ compile OK")


def try_launch_gui() -> int:
    """
    Try to launch the GUI via several strategies, with friendly errors.
    """
    # 1) Preferred: packaged entry pokertool.gui
    try:
        gui = importlib.import_module("pokertool.gui")
        launch = getattr(gui, "main", getattr(gui, "run", None))
        if callable(launch):
            return int(launch()) if isinstance(launch(), int) else 0  # type: ignore[call-arg]
    except Exception as e:
        print(f"[launch] pokertool.gui import failed: {e}", file=sys.stderr)

    # 2) Local source fallback: src/pokertool/gui.py
    here = Path(__file__).resolve().parent
    repo_root = find_repo_root(here)
    src_gui = repo_root / "src" / "pokertool" / "gui.py"
    if src_gui.exists():
        try:
            spec = importlib.util.spec_from_file_location("pokertool_gui_fallback", src_gui)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                launch = getattr(mod, "main", getattr(mod, "run", None))
                if callable(launch):
                    rv = launch()
                    return int(rv) if isinstance(rv, int) else 0
        except Exception as e:
            print(f"[launch] src/pokertool/gui.py failed: {e}", file=sys.stderr)

    # 3) Legacy flat layout: poker_gui.py in repo root
    legacy_gui = repo_root / "poker_gui.py"
    if legacy_gui.exists():
        try:
            spec = importlib.util.spec_from_file_location("legacy_poker_gui", legacy_gui)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                launch = getattr(mod, "main", getattr(mod, "run", None))
                if callable(launch):
                    rv = launch()
                    return int(rv) if isinstance(rv, int) else 0
        except Exception as e:
            print(f"[launch] legacy poker_gui.py failed: {e}", file=sys.stderr)

    # If all else fails, try a friendly Tk error dialog (best-effort)
    try:
        import tkinter as tk  # type: ignore
        from tkinter import messagebox  # type: ignore
        root = tk.Tk(); root.withdraw()
        messagebox.showerror(
            "PokerTool",
            "Could not find/launch the GUI.\n"
            "Make sure either the package 'pokertool' is importable or 'src/pokertool/gui.py' exists."
        )
        root.destroy()
    except Exception:
        pass
    return 1


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PokerTool launcher with pre-flight self-heal scan.")
    parser.add_argument("--no-scan", action="store_true", help="Skip the code_scan.py auto-fix stage")
    args = parser.parse_args(argv)

    repo_root = find_repo_root(Path(__file__).parent)
    print(f"[poker_go] repo root: {repo_root}")

    if not args.no_scan:
        rc = run_code_scan(repo_root)
        if rc != 0:
            print(f"[poker_go] code_scan reported problems (rc={rc}). Aborting launch.", file=sys.stderr)
            return rc

    verify_compiles(repo_root)
    print("[poker_go] launching GUI…")
    return try_launch_gui()


if __name__ == "__main__":
    raise SystemExit(main())
