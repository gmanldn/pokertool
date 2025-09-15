#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: pokertool/poker_go.py
# version: '20'
# last_commit: '2025-09-15T01:25:21.989996+00:00'
# fixes: []
# ---
# POKERTOOL-HEADER-END
"""
poker_go.py — zero-prompt launcher for gmanldn/pokertool.

Goals
- Run from the repo folder without modifying files.
- Auto-answer any input() prompts during setup ("y" / proceed).
- Prefer GUI; fall back to CLI if tkinter or GUI import fails.
- Keep sys.path sane so local modules beat any site-packages shadows.
- Provide clear exit codes.

Usage
  python3 poker_go.py                 # normal, prefer GUI
  python3 poker_go.py --cli           # force CLI
  python3 poker_go.py --no-init       # skip database/init step
  python3 poker_go.py --selftest      # quick import/run checks

Only stdlib used.
"""

from __future__ import annotations

import argparse
import builtins
import contextlib
import importlib
import os
import runpy
import sys
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Callable, Optional
import os as _os
if _os.environ.get('POKER_AUTOCONFIRM','1') in {'1','true','True'}:
    import builtins as _bi
    _bi.input = lambda *a, **k: 'y'


REPO_ROOT = Path(__file__).resolve().parent


def _put_repo_first_on_syspath() -> None:
    # Ensure the repo root is first so local modules win.
    repo = str(REPO_ROOT)
    if sys.path[0] != repo:
        if repo in sys.path:
            sys.path.remove(repo)
        sys.path.insert(0, repo)


@contextlib.contextmanager
def _auto_confirm_inputs(answer: str = "y"):
    """
    Temporarily monkey-patch builtins.input to auto-confirm.

    Any call like input("Continue? y/n: ") will receive `answer`.
    """
    original_input = builtins.input

    def _fake_input(prompt: str = "") -> str:
        # Print prompt to stay transparent, then auto-answer.
        try:
            sys.stdout.write(str(prompt))
            sys.stdout.flush()
        except Exception:
            pass
        return answer

    builtins.input = _fake_input
    try:
        yield
    finally:
        builtins.input = original_input


def _module_exists(name: str) -> bool:
    try:
        importlib.util.find_spec(name)
        return True
    except Exception:
        return False


def _try_import(name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _tk_available() -> bool:
    try:
        import tkinter  # noqa: F401
        return True
    except Exception:
        return False


def _run_module_as_main(mod_name: str) -> int:
    """
    Execute a module as if run via `python -m <mod>`.
    Returns 0 on success, nonzero on error.
    """
    try:
        runpy.run_module(mod_name, run_name="__main__")
        return 0
    except SystemExit as e:
        # Allow modules that call sys.exit(code).
        try:
            code = int(e.code) if e.code is not None else 0
        except Exception:
            code = 1
        return code
    except Exception as e:
        print(f"[poker_go] Error running module '{mod_name}': {e}", file=sys.stderr)
        return 1


def _run_with_timeout(fn: Callable[[], int], timeout_sec: float) -> int:
    """
    Run a callable that returns an int status, with a timeout.
    If timeout elapses, returns 124 (like GNU timeout).
    """
    result_holder = {"code": 124}

    def _target():
        try:
            result_holder["code"] = fn()
        except Exception:
            result_holder["code"] = 1

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    return result_holder["code"]


def initialize(no_init: bool) -> int:
    """
    Run initialization steps in a non-interactive way.
    Returns 0 on success or if skipped, nonzero on hard failure.
    """
    if no_init:
        return 0

    # Export an env flag some scripts may honor for non-interactive runs.
    os.environ.setdefault("POKERTOOL_AUTOCONFIRM", "1")
    os.environ.setdefault("PT_AUTOCONFIRM", "1")

    # If an autoconfirm helper exists, import it first (safe no-op if unused).
    if _module_exists("autoconfirm"):
        _try_import("autoconfirm")

    # If an explicit init module exists, run it with auto-confirm.
    if _module_exists("poker_init"):
        def _run_init() -> int:
            with _auto_confirm_inputs("y"):
                return _run_module_as_main("poker_init")

        # Guard against hanging prompts with a hard timeout.
        # If your init is slow but legit, bump this.
        return _run_with_timeout(_run_init, timeout_sec=30.0)

    # If there is no dedicated init, treat as success.
    return 0


def launch(prefer_cli: bool) -> int:
    """
    Launch the application. Prefer GUI unless --cli or no tkinter.
    Fallback order:
      GUI path: poker_gui -> poker_main
      CLI path: poker_main
    """
    # Force local imports
    _put_repo_first_on_syspath()

    if not prefer_cli and _tk_available() and _module_exists("poker_gui"):
        # Try GUI first
        code = _run_module_as_main("poker_gui")
        if code == 0:
            return 0
        print("[poker_go] GUI failed, falling back to CLI...", file=sys.stderr)

    # CLI fallback
    if _module_exists("poker_main"):
        return _run_module_as_main("poker_main")

    # As a last resort, try the GUI even if tkinter check failed previously
    # in case the GUI has a CLI shim.
    if _module_exists("poker_gui"):
        return _run_module_as_main("poker_gui")

    print("[poker_go] Neither poker_main.py nor poker_gui.py is available.", file=sys.stderr)
    return 127


def selftest() -> int:
    """
    Quick sanity checks: imports and dry-run init.
    Returns 0 if things look workable.
    """
    _put_repo_first_on_syspath()
    ok = True

    for mod in ("poker_modules", "poker_main", "poker_gui", "poker_init"):
        exists = _module_exists(mod)
        print(f"[selftest] {mod:13s} : {'found' if exists else 'missing'}")
        ok &= exists or (mod in ("poker_gui", "poker_init"))  # GUI/init may be optional

    # Try a fast non-interactive init if present
    init_code = initialize(no_init=False)
    print(f"[selftest] init exit code: {init_code}")
    ok &= (init_code in (0, 2))  # allow benign nonzero if script uses special codes

    # Do not actually launch GUI here.
    return 0 if ok else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--cli", action="store_true", help="force CLI mode (skip GUI)")
    p.add_argument("--no-init", action="store_true", help="skip initialization step")
    p.add_argument("--selftest", action="store_true", help="run quick checks and exit")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    _put_repo_first_on_syspath()

    if args.selftest:
        return selftest()

    init_code = initialize(no_init=args.no_init)
    if init_code not in (0, 2):
        # Non-fatal: proceed anyway but report.
        print(f"[poker_go] init returned {init_code}, continuing...", file=sys.stderr)

    return launch(prefer_cli=args.cli)


if __name__ == "__main__":
    sys.exit(main())
