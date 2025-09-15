#!/usr/bin/env python3
"""
Consolidate GUI onto poker_gui_enhanced.py and fix misplaced __future__ imports.

Usage:
  python3 consolidate_gui_and_future_fixes.py
  python3 consolidate_gui_and_future_fixes.py --dry-run
  python3 consolidate_gui_and_future_fixes.py --delete   # permanently delete old GUI files
  python3 consolidate_gui_and_future_fixes.py --root /path/to/repo

What it does:
  1) Rewrites imports/usages of old GUI modules to poker_gui_enhanced.
  2) Moves old GUI modules into deprecated/_removed_<ts>/ (or deletes with --delete).
  3) Relocates any 'from __future__ import ...' to the top (after shebang/encoding and module docstring).
  4) Updates .md/.txt to mention poker_gui_enhanced.py instead of poker_gui.py, etc.
  5) Saves changed files and prints a summary.

Safe, idempotent, and logs everything. Intended for macOS/Linux with Python 3.8+.
"""

import argparse
import datetime as _dt
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

# --- Configuration -----------------------------------------------------------

# GUI module names to consolidate away from:
OLD_GUI_NAMES = [
    "poker_gui",
    "poker_gui_original",
    "enhanced_poker_gui",
    "poker_gui_autopilot",
]

# Target GUI module:
TARGET_GUI = "poker_gui_enhanced"

# File names that are clearly GUI modules to remove/relocate if present:
GUI_FILES_TO_REMOVE = {
    "poker_gui.py",
    "poker_gui_original.py",
    "enhanced_poker_gui.py",
    "poker_gui_autopilot.py",
}

# Text files to update command examples in:
TEXT_EXTS = {".md", ".txt"}

# Python files:
PY_EXT = ".py"

# Patterns to fix "from __future__ import ..." placement
FUTURE_IMPORT_RE = re.compile(r"^\s*from\s+__future__\s+import\s+([A-Za-z0-9_,\s]+)\s*$")

# Patterns to rewrite imports referencing old GUI modules
#  - from X import Y  -> from poker_gui_enhanced import Y
#  - import X         -> import poker_gui_enhanced
#  - import X as y    -> import poker_gui_enhanced as y
FROM_IMPORT_RE = re.compile(
    r"(^|\n)\s*from\s+(?P<mod>{mods})\s+import\s+(?P<rest>.+)".format(
        mods="|".join(map(re.escape, OLD_GUI_NAMES))
    )
)
IMPORT_RE = re.compile(
    r"(^|\n)\s*import\s+(?P<mod>{mods})(?P<alias>\s+as\s+\w+)?".format(
        mods="|".join(map(re.escape, OLD_GUI_NAMES))
    )
)

# Replace common CLI mentions of old GUI entrypoints in docs
CLI_REPLACEMENTS = [
    (re.compile(r"\bpython3?\s+poker_gui\.py\b"), "python3 poker_gui_enhanced.py"),
    (re.compile(r"\bpython3?\s+enhanced_poker_gui\.py\b"), "python3 poker_gui_enhanced.py"),
    (re.compile(r"\bpython3?\s+poker_gui_original\.py\b"), "python3 poker_gui_enhanced.py"),
    (re.compile(r"\bpython3?\s+poker_gui_autopilot\.py\b"), "python3 poker_gui_enhanced.py"),
]


# --- Helpers ----------------------------------------------------------------

def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback with errors='ignore' if odd encoding found
        return p.read_text(encoding="utf-8", errors="ignore")

def _write_text(p: Path, s: str):
    p.write_text(s, encoding="utf-8")

def _is_python_file(p: Path) -> bool:
    return p.is_file() and p.suffix == PY_EXT

def _is_text_doc(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in TEXT_EXTS

def _find_module_docstring_bounds(lines: List[str]) -> Tuple[int, int]:
    """
    Return (start_index, end_index_exclusive) of a top-of-file triple-quoted docstring,
    or (-1, -1) if none. Respects shebang/encoding lines above.
    """
    idx = 0
    n = len(lines)

    # Skip shebang
    if idx < n and lines[idx].startswith("#!"):
        idx += 1

    # Skip encoding comment (PEP 263)
    if idx < n and re.match(r"^\s*#.*coding[:=]\s*[-\w.]+", lines[idx]):
        idx += 1

    # Skip blanks/comments until first code or triple-quoted string
    while idx < n and (not lines[idx].strip() or lines[idx].lstrip().startswith("#")):
        idx += 1

    if idx >= n:
        return (-1, -1)

    line = lines[idx].lstrip()
    triple = None
    if line.startswith('"""') or line.startswith("'''"):
        triple = line[:3]
    else:
        return (-1, -1)

    # Find the end of the triple-quoted string
    start = idx
    # If the opening and closing are on the same line
    if line.count(triple) >= 2:
        return (start, start + 1)

    idx += 1
    while idx < n:
        if triple in lines[idx]:
            return (start, idx + 1)
        idx += 1

    # Unterminated docstring – treat as none to avoid breaking the file
    return (-1, -1)

def _relocate_future_imports(text: str) -> Tuple[str, bool]:
    """
    Move all "from __future__ import ..." statements to the allowed top-of-file location:
    after shebang/encoding and after a top-level docstring (if present).
    """
    lines = text.splitlines(keepends=False)
    n = len(lines)
    if n == 0:
        return text, False

    # Collect and remove all future imports
    future_lines = []
    keep_lines = []
    for ln in lines:
        m = FUTURE_IMPORT_RE.match(ln)
        if m:
            # collect the entire line; we'll deduplicate later
            future_lines.append(ln.strip())
        else:
            keep_lines.append(ln)

    if not future_lines:
        return text, False

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for fl in future_lines:
        if fl not in seen:
            deduped.append(fl)
            seen.add(fl)

    # Find insertion point after shebang/encoding and module docstring
    lines2 = keep_lines
    start, end = _find_module_docstring_bounds(lines2)
    insert_at = 0
    # Skip shebang
    if insert_at < len(lines2) and lines2[insert_at].startswith("#!"):
        insert_at += 1
    # Skip encoding
    if insert_at < len(lines2) and re.match(r"^\s*#.*coding[:=]\s*[-\w.]+", lines2[insert_at]):
        insert_at += 1
    # If there is a module docstring at the top, insert after it
    if start == insert_at:
        insert_at = end

    # Also ensure there's a blank line after the future block if needed
    block = deduped[:]
    if insert_at < len(lines2) and lines2[insert_at].strip():
        block.append("")  # blank line to separate

    new_lines = lines2[:insert_at] + block + lines2[insert_at:]
    return "\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), True

def _rewrite_gui_imports(text: str) -> Tuple[str, bool]:
    changed = False

    def repl_from(m):
        nonlocal changed
        changed = True
        return f"{m.group(1)}from {TARGET_GUI} import {m.group('rest')}"

    def repl_import(m):
        nonlocal changed
        alias = m.group("alias") or ""
        changed = True
        return f"{m.group(1)}import {TARGET_GUI}{alias}"

    new_text = FROM_IMPORT_RE.sub(repl_from, text)
    new_text = IMPORT_RE.sub(repl_import, new_text)
    return new_text, changed

def _rewrite_cli_mentions(text: str) -> Tuple[str, bool]:
    changed = False
    for pat, repl in CLI_REPLACEMENTS:
        new_text, n = pat.subn(repl, text)
        if n > 0:
            changed = True
            text = new_text
    return text, changed


# --- Core -------------------------------------------------------------------

def process_python_file(p: Path) -> Tuple[bool, List[str]]:
    original = _read_text(p)
    updated = original
    messages = []

    # 1) Move future imports to the top
    updated, moved_future = _relocate_future_imports(updated)
    if moved_future:
        messages.append("fixed_future_imports")

    # 2) Rewrite GUI imports
    updated2, gui_changed = _rewrite_gui_imports(updated)
    if gui_changed:
        messages.append("rewrote_gui_imports")
        updated = updated2

    if updated != original:
        _write_text(p, updated)
        return True, messages
    return False, messages

def process_text_file(p: Path) -> Tuple[bool, List[str]]:
    original = _read_text(p)
    updated, changed = _rewrite_cli_mentions(original)
    if changed:
        _write_text(p, updated)
        return True, ["updated_cli_examples"]
    return False, []

def move_or_delete_old_gui_files(root: Path, delete: bool, dry_run: bool) -> List[str]:
    moved = []
    ts = _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    deprec_dir = root / "deprecated" / f"_removed_{ts}"
    if not delete and not dry_run:
        deprec_dir.mkdir(parents=True, exist_ok=True)

    for name in GUI_FILES_TO_REMOVE:
        p = root / name
        if not p.exists():
            continue
        if delete:
            action = f"deleted {p}"
            if not dry_run:
                p.unlink()
            moved.append(action)
        else:
            dest = deprec_dir / name
            action = f"moved {p} -> {dest}"
            if not dry_run:
                shutil.move(str(p), str(dest))
            moved.append(action)

    return moved

def main():
    ap = argparse.ArgumentParser(description="Consolidate GUI + fix future imports across repo")
    ap.add_argument("--root", default=".", help="Repo root (default: current directory)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change but do not modify files")
    ap.add_argument("--delete", action="store_true", help="Permanently delete old GUI files instead of moving to deprecated/")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[error] root not found: {root}", file=sys.stderr)
        sys.exit(2)

    print(f"[info] repo: {root}")
    backup_dir = root / f"_backup_{_dt.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    if not args.dry_run:
        backup_dir.mkdir(exist_ok=False)
    print(f"[info] backup: {backup_dir} (created)")

    changed_files = []
    touched = {}
    # Prepare a list of candidate files
    candidates = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if p.name.startswith(".") and p.name not in {".gitignore"}:
            continue
        if _is_python_file(p) or _is_text_doc(p):
            candidates.append(p)

    # Backup everything we might change
    for p in candidates:
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        bdst = backup_dir / rel
        if not args.dry_run:
            bdst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(bdst))

    # Process files
    for p in candidates:
        if _is_python_file(p):
            changed, msgs = process_python_file(p)
        elif _is_text_doc(p):
            changed, msgs = process_text_file(p)
        else:
            changed, msgs = (False, [])
        if changed:
            changed_files.append(str(p))
            touched[str(p)] = msgs

    # Move or delete old GUI files (but never touch TARGET_GUI)
    gui_moves = move_or_delete_old_gui_files(root, delete=args.delete, dry_run=args.dry_run)

    # Summary
    print("\n=== Summary ===")
    print(f"Files examined: {len(candidates)}")
    print(f"Files changed:  {len(changed_files)}")
    if changed_files:
        for f in changed_files:
            print(" -", f, ":", ",".join(touched[f]))
    if gui_moves:
        print("\nGUI file actions:")
        for act in gui_moves:
            print(" -", act)

    if args.dry_run:
        print("\n[info] DRY RUN mode: no files were modified.")
    else:
        print("\n[info] Done. A full backup of originals is in:", backup_dir)

if __name__ == "__main__":
    main()
