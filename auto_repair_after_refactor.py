#!/usr/bin/env python3
"""
auto_repair_after_refactor.py

Second pass: fix specific syntax/structure issues reported after running
fix_and_harden_sep15.py --apply.

- Overwrite src/pokertool/error_handling.py with a clean, known-good version.
- Add 'pass' after empty 'def ...:' and 'try:' blocks in tools/tests.
- Remove REPL prompts (lines starting with '>>>' or '... ').
- Heuristically fix lines with unmatched ')' by trimming one trailing ')'
  when a line has more ')' than '(' (targets the reported line 71 issues).
- Re-run an AST compile audit and print any remaining problems.

Usage:
  python3 auto_repair_after_refactor.py          # dry-run: show intended changes
  python3 auto_repair_after_refactor.py --apply  # perform edits
"""
from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "src" / "pokertool"

# Files that were flagged in your run:
TARGETS = [
    REPO / "tools" / "verify_build.py",
    REPO / "tools" / "poker_main.py",
    REPO / "tools" / "gui_integration_tests.py",
    REPO / "tools" / "poker_gui_autopilot.py",
    REPO / "tools" / "poker_gui_original.py",
    REPO / "tests" / "test_poker.py",
    SRC / "gui.py",
    SRC / "error_handling.py",  # will be overwritten
]

CLEAN_ERROR_HANDLING = '''from __future__ import annotations
"""
error_handling.py — centralised error handling & logging (clean version).
"""
import logging
import sys
from contextlib import contextmanager

def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True,
    )

_configure_logging()
log = logging.getLogger("pokertool")

def run_safely(fn, *args, **kwargs) -> int:
    """
    Run a callable and catch all exceptions, logging a concise error.
    Return process exit code (0 on success, 1 on failure).
    """
    try:
        rv = fn(*args, **kwargs)
        return int(rv) if isinstance(rv, int) else 0
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 1
    except Exception as e:  # noqa: BLE001
        log.exception("Fatal error: %s", e)
        # Best-effort user-facing dialog if Tk is available
        try:
            import tkinter  # type: ignore
            import tkinter.messagebox  # type: ignore
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showerror("PokerTool error", f"A fatal error occurred:\\n{e}")
            root.destroy()
        except Exception:  # noqa: BLE001
            pass
        return 1

@contextmanager
def db_guard(desc: str = "DB operation"):
    """
    Wrap short DB operations. Example:
        with db_guard("saving decision"):
            storage.save_decision(...)
    """
    try:
        yield
    except Exception as e:  # noqa: BLE001
        log.exception("%s failed: %s", desc, e)
        raise
'''

RE_EMPTY_DEF = re.compile(r'^(\s*)def\s+\w+\s*\([^)]*\)\s*:\s*$')
RE_TRY = re.compile(r'^(\s*)try\s*:\s*$')
RE_PROMPT = re.compile(r'^\s*(>>>|\.\.\.)\s')

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, text: str, apply: bool) -> None:
    if apply:
        path.write_text(text, encoding="utf-8")

def ensure_pass_after_block(lines: list[str], idx: int, indent: str) -> bool:
    """
    If line idx is a 'def ...:' or 'try:' and the next non-empty line is not
    more-indented, insert '    pass'.
    """
    j = idx + 1
    # Skip blank lines and comments immediately after
    while j < len(lines) and (not lines[j].strip() or lines[j].lstrip().startswith("#")):
        j += 1
    if j >= len(lines):
        lines.insert(idx + 1, f"{indent}    pass")
        return True
    next_line = lines[j]
    next_indent = len(next_line) - len(next_line.lstrip(" "))
    if next_indent <= len(indent):
        lines.insert(idx + 1, f"{indent}    pass")
        return True
    return False

def trim_excess_closing_paren(line: str) -> tuple[str, bool]:
    # naive balance check outside of quotes; only fix a single extra ')' at EOL
    if line.strip().startswith("#"):
        return line, False
    # crude quick check
    open_count = line.count("(")
    close_count = line.count(")")
    if close_count > open_count and line.rstrip().endswith(")"):
        return line.rstrip()[:-1] + "\n", True
    return line, False

def clean_file(path: Path, apply: bool) -> list[str]:
    """
    Returns list of messages describing changes intended/made for this file.
    """
    msgs: list[str] = []
    if not path.exists():
        return [f"[skip] missing: {path}"]

    # Special case: overwrite error_handling.py with clean content
    if path == SRC / "error_handling.py":
        msgs.append(f"[overwrite] {path}")
        write_text(path, CLEAN_ERROR_HANDLING, apply)
        return msgs

    text = read_text(path)
    orig = text
    lines = text.splitlines(True)

    # 1) strip REPL prompts
    new_lines = []
    stripped = 0
    for ln in lines:
        if RE_PROMPT.match(ln):
            stripped += 1
            continue
        new_lines.append(ln)
    if stripped:
        msgs.append(f"[strip] removed {stripped} REPL prompt line(s)")
    lines = new_lines

    # 2) add 'pass' after empty def/try
    inserted = 0
    i = 0
    while i < len(lines):
        mdef = RE_EMPTY_DEF.match(lines[i])
        mtry = RE_TRY.match(lines[i])
        if mdef:
            indent = mdef.group(1)
            if ensure_pass_after_block(lines, i, indent):
                inserted += 1
                i += 1
        elif mtry:
            indent = mtry.group(1)
            if ensure_pass_after_block(lines, i, indent):
                inserted += 1
                i += 1
        i += 1
    if inserted:
        msgs.append(f"[insert] added {inserted} 'pass' stub(s)")

    # 3) trim one extra ')' at EOL when ')' > '('
    fixed_paren = 0
    for idx, ln in enumerate(lines):
        new_ln, changed = trim_excess_closing_paren(ln)
        if changed:
            lines[idx] = new_ln
            fixed_paren += 1
    if fixed_paren:
        msgs.append(f"[paren] trimmed {fixed_paren} excess closing paren(s)")

    new_text = "".join(lines)
    if new_text != orig:
        msgs.append(f"[write] {path}")
        write_text(path, new_text, apply)
    else:
        msgs.append(f"[nochange] {path}")

    return msgs

def compile_audit(paths: list[Path]) -> list[str]:
    problems: list[str] = []
    for p in paths:
        if not p.exists():
            continue
        try:
            src = read_text(p)
            ast.parse(src, filename=str(p))
        except SyntaxError as e:
            problems.append(f"{p}: SyntaxError: {e.msg} at line {e.lineno}")
        except Exception as e:
            problems.append(f"{p}: ParseError: {e}")
    return problems

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Perform changes (default: dry-run)")
    args = ap.parse_args()
    apply = args.apply

    print("== auto_repair_after_refactor ==")
    for t in TARGETS:
        msgs = clean_file(t, apply=apply)
        for m in msgs:
            print(" ", m)

    # compile audit the same targets again
    print("\n[compile audit]")
    probs = compile_audit(TARGETS)
    if probs:
        for pr in probs:
            print(" -", pr)
    else:
        print(" no syntax errors detected in target set")

    print("\nDone. (Dry-run)" if not apply else "\nDone. Changes applied.")

if __name__ == "__main__":
    main()
