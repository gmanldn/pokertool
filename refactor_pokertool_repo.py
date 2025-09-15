#!/usr/bin/env python3
"""
refactor_pokertool_repo.py

One-shot refactor & fixer for the PokerTool repo:
- Clean repo hygiene (.gitignore, remove junk/artifacts)
- Reposition `from __future__ import annotations` to the legal top of each .py
- Restructure to a package layout: src/pokertool/{core,storage,gui,scrape,cli}.py
- Update imports to the new package
- Create __init__.py that re-exports key API (analyse_hand, Card) if present
- Create pyproject.toml and a minimal GitHub Actions workflow
- Move sidecar/driver scripts into tools/
- Report (and optionally fix) common pitfalls

Usage:
  python3 refactor_pokertool_repo.py            # dry-run
  python3 refactor_pokertool_repo.py --apply    # actually perform changes
"""
from __future__ import annotations
from __future__ import annotations


import argparse
import os
import re
import shutil
import sys
import textwrap
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent
SRC = REPO / "src" / "pokertool"
TOOLS = REPO / "tools"
GHA = REPO / ".github" / "workflows"

# Files we expect (legacy names)
LEGACY_FILES = {
    "poker_modules.py": "core.py",
    "poker_init.py": "storage.py",
    "poker_main.py": None,   # folded into CLI
    "poker_go.py": None,     # folded into CLI
    "poker_gui.py": "gui.py",
    "poker_gui_enhanced.py": "gui.py",
    "enhanced_poker_gui.py": "gui.py",
    "poker_gui_original.py": "gui.py",
    "poker_gui_autopilot.py": None,  # move to tools/
    "gui_integration_script.py": None,  # move to tools/
}

# Sidecar/driver/script patterns -> tools/
TOOL_PATTERNS = [
    r"^poker_gui_.*\.py$",
    r"^gui_.*\.py$",
    r"^hotfix_.*\.py$",
    r"^sani.*\.py$",
    r"^Improvement.*\.py$",
    r"^update_.*\.py$",
]

DELETE_GLOBS = [
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".DS_Store", ".DS_Store.pokerheader.yml",
    "backup_*", "*.pyc", "*.pyo", "*.pyd",
    "*.sqlite", "*.sqlite3", "*.db",
    ".pokertool_state.json",
]

GITIGNORE_RULES = """
# OS / editor
.DS_Store
Thumbs.db
*.swp
*.swo
.idea/
.vscode/

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.pdb
*.egg-info/
.eggs/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Local data / artifacts
*.db
*.sqlite
*.sqlite3
backup_*/
"""

PYPROJECT_TOML = """\
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pokertool"
version = "0.0.0"
description = "Poker assistant demo with GUI and hand-analysis logic"
readme = "README.md"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
scraper = ["requests>=2.32.0", "beautifulsoup4>=4.12.0"]

[project.scripts]
pokertool = "pokertool.cli:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
"""

CI_YML = """\
name: ci
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install --upgrade pip
      - run: pip install ruff mypy bandit pytest
      - run: pip install -e . || true
      - run: python -m compileall -q .
      - run: ruff check .
      - run: mypy --ignore-missing-imports src || true
      - run: pytest -q || true
"""

SCRAPE_STUB = '''\
"""
scrape.py — placeholder for screen scraping integration.

Expose functions here and call them from the GUI (e.g., via a "Screen Scraper" button).
"""

def run_screen_scraper():
    # TODO: implement real scraping logic.
    # Keep this pure (no tkinter imports) so it's testable headless.
    return {"status": "not_implemented", "message": "Screen scraper not wired yet."}
'''

CLI_FILE = '''\
"""
cli.py — CLI entrypoint for pokertool.
"""

import argparse
import sys

def main(argv=None):
    parser = argparse.ArgumentParser(prog="pokertool", description="PokerTool CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("gui", help="Launch the Tkinter GUI")
    sub.add_parser("scrape", help="Run the screen scraper (headless)")

    args = parser.parse_args(argv)

    if args.cmd in (None, "gui"):
        # Defer tkinter import to runtime
        try:
            from pokertool import gui
        except Exception as e:
            print(f"[fatal] GUI import failed: {e}", file=sys.stderr)
            return 1
        try:
            return gui.main()
        except AttributeError:
            # Fallback if gui exposes a function named run() instead
            return getattr(gui, "run")()
    elif args.cmd == "scrape":
        from pokertool import scrape
        result = scrape.run_screen_scraper()
        print(result)
        return 0

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''

INIT_TEMPLATE = '''\
"""
pokertool package — stable API surface.
"""
# Re-export commonly-used symbols if present in core.
try:
    from .core import analyse_hand, Card  # type: ignore[attr-defined]
except Exception:
    # If not present, expose nothing; users/tests can still import .core directly.
    pass
'''

FUTURE_RE = re.compile(r'^from __future__ import .+$')
SHEBANG_RE = re.compile(r'^#!')
ENCODING_RE = re.compile(r'coding[:=]\\s*([-\w.]+)')

IMPORT_MAP = {
    # from X import ...   -> from pokertool.core/storage/gui import ...
    r"from\\s+poker_modules\\s+import\\s": "from pokertool.core import ",
    r"import\\s+poker_modules\\b": "import pokertool.core as poker_modules",
    r"from\\s+poker_init\\s+import\\s": "from pokertool.storage import ",
    r"import\\s+poker_init\\b": "import pokertool.storage as poker_init",
    r"from\\s+poker_gui\\s+import\\s": "from pokertool.gui import ",
    r"import\\s+poker_gui\\b": "import pokertool.gui as poker_gui",
}

TOOL_REGEXES = [re.compile(p) for p in TOOL_PATTERNS]

def ensure_dirs(dry: bool):
    for d in (SRC, TOOLS, GHA):
        if not d.exists():
            print(f"[mkdir] {d}")
            if not dry:
                d.mkdir(parents=True, exist_ok=True)

def merge_gitignore(dry: bool):
    gi = REPO / ".gitignore"
    existing = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
    merged = existing.strip()
    if merged and not merged.endswith("\n"):
        merged += "\n"
    merged += GITIGNORE_RULES.strip() + "\n"
    if gi.exists() and existing == merged:
        print("[gitignore] no change")
        return
    print("[gitignore] write/merge")
    if not dry:
        gi.write_text(merged, encoding="utf-8")

def delete_matches(dry: bool):
    for pattern in DELETE_GLOBS:
        for p in REPO.glob(pattern):
            # don't nuke .github or src, etc., protect structure
            if p.name in (".github", "src", "tools"):
                continue
            if p.is_dir():
                print(f"[remove dir] {p}")
                if not dry:
                    shutil.rmtree(p, ignore_errors=True)
            elif p.is_file():
                print(f"[remove file] {p}")
                if not dry:
                    p.unlink(missing_ok=True)

def reposition_future_imports(py_path: Path, dry: bool) -> bool:
    """
    Move any 'from __future__ import ...' lines to the top (after shebang/encoding/docstring).
    """
    try:
        src = py_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return False

    if not any(FUTURE_RE.match(line) for line in src):
        return False

    insert_at = 0
    if src and SHEBANG_RE.match(src[0]):
        insert_at = 1
    if insert_at < len(src) and ENCODING_RE.search(src[insert_at] if insert_at < len(src) else ""):
        insert_at += 1

    # module docstring block
    def is_triple(line: str) -> bool:
        s = line.strip()
        return s.startswith('"""') or s.startswith("'''")

    if insert_at < len(src) and is_triple(src[insert_at]):
        q = src[insert_at].strip()[:3]
        j = insert_at + 1
        while j < len(src):
            if src[j].strip().endswith(q):
                insert_at = j + 1
                break
            j += 1

    futures, rest = [], []
    for line in src:
        if FUTURE_RE.match(line):
            futures.append(line)
        else:
            rest.append(line)

    new_src = rest[:insert_at] + futures + ([""] if insert_at < len(rest) and rest[insert_at].strip() else []) + rest[insert_at:]
    if new_src != src:
        print(f"[future] move to top: {py_path}")
        if not dry:
            py_path.write_text("\n".join(new_src) + "\n", encoding="utf-8")
        return True
    return False

def move_or_choose_gui(dry: bool):
    """
    Choose a canonical GUI source among possible variants.
    Priority: poker_gui.py > poker_gui_enhanced.py > enhanced_poker_gui.py > poker_gui_original.py
    Move the chosen one to src/pokertool/gui.py
    Others go to tools/
    """
    candidates = [
        "poker_gui.py",
        "poker_gui_enhanced.py",
        "enhanced_poker_gui.py",
        "poker_gui_original.py",
    ]
    chosen = None
    for c in candidates:
        if (REPO / c).exists():
            chosen = c
            break

    if chosen:
        src = REPO / chosen
        dst = SRC / "gui.py"
        if not dst.exists():
            print(f"[move] {src} -> {dst}")
            if not dry:
                shutil.move(str(src), str(dst))
        else:
            # Already moved earlier; push the legacy copy to tools
            print(f"[tools] {src} -> tools/{src.name}")
            if not dry:
                shutil.move(str(src), str(TOOLS / src.name))

    # move other GUIs to tools
    for c in candidates:
        p = REPO / c
        if p.exists() and p.name != "gui.py":
            print(f"[tools] {p} -> tools/{p.name}")
            if not dry:
                shutil.move(str(p), str(TOOLS / p.name))

def move_legacy_files(dry: bool):
    # core & storage
    for legacy, newname in LEGACY_FILES.items():
        p = REPO / legacy
        if not p.exists():
            continue
        if legacy.startswith("poker_gui") and newname == "gui.py":
            # handled by move_or_choose_gui
            continue
        if newname is None:
            # move to tools unless it's a launcher we are replacing with CLI
            tools_dst = TOOLS / p.name
            print(f"[tools] {p} -> {tools_dst}")
            if not dry:
                shutil.move(str(p), str(tools_dst))
        else:
            dst = SRC / newname
            if dst.exists():
                # already moved
                print(f"[skip] exists: {dst}")
            else:
                print(f"[move] {p} -> {dst}")
                if not dry:
                    shutil.move(str(p), str(dst))

def move_sidecar_scripts(dry: bool):
    for f in REPO.glob("*.py"):
        name = f.name
        if name == Path(__file__).name:  # don't move self
            continue
        if (SRC in f.parents) or (TOOLS in f.parents):
            continue
        for rx in TOOL_REGEXES:
            if rx.match(name):
                target = TOOLS / name
                print(f"[tools] {f} -> {target}")
                if not dry:
                    shutil.move(str(f), str(target))
                break

def write_if_missing(path: Path, content: str, label: str, dry: bool):
    if path.exists():
        return
    print(f"[write] {label}: {path}")
    if not dry:
        path.write_text(content, encoding="utf-8")

def update_imports_in_tree(dry: bool):
    for py in SRC.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        orig = text
        for pattern, repl in IMPORT_MAP.items():
            text = re.sub(pattern, repl, text)
        if text != orig:
            print(f"[imports] rewrite: {py}")
            if not dry:
                py.write_text(text, encoding="utf-8")

def audit_and_fix_future(dry: bool):
    problems = []
    for py in REPO.rglob("*.py"):
        # skip venvs and .git area
        if any(part in {".git", ".venv", "venv", "env"} for part in py.parts):
            continue
        try:
            reposition_future_imports(py, dry=dry)
            # AST parse
            src = py.read_text(encoding="utf-8", errors="ignore")
            ast.parse(src, filename=str(py))
        except SyntaxError as e:
            problems.append((str(py), f"SyntaxError: {e.msg} at line {e.lineno}"))
        except Exception as e:
            problems.append((str(py), f"ParseError: {e}"))
    if problems:
        print("\n[compile problems]")
        for f, msg in problems:
            print(f" - {f}: {msg}")
    else:
        print("\n[compile] no syntax errors detected by AST")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Perform changes (default: dry-run)")
    args = ap.parse_args()
    dry = not args.apply

    print("== refactor_pokertool_repo ==")
    ensure_dirs(dry)
    merge_gitignore(dry)
    delete_matches(dry)

    # Moves & structure
    move_or_choose_gui(dry)
    move_legacy_files(dry)
    move_sidecar_scripts(dry)

    # Seed package scaffolding
    write_if_missing(SRC / "__init__.py", INIT_TEMPLATE, "__init__.py", dry)
    write_if_missing(SRC / "scrape.py", SCRAPE_STUB, "scrape.py", dry)
    write_if_missing(SRC / "cli.py", CLI_FILE, "cli.py", dry)
    write_if_missing(REPO / "pyproject.toml", PYPROJECT_TOML, "pyproject.toml", dry)
    write_if_missing(GHA / "ci.yml", CI_YML, "GitHub Actions workflow", dry)

    # Update imports for moved files
    update_imports_in_tree(dry)

    # Fix future import placement & AST audit
    audit_and_fix_future(dry)

    print("\nTIP: install locally for dev with:")
    print("  pip install -e .")
    print("Run CLI:")
    print("  pokertool          # launches GUI by default")
    print("  pokertool gui      # explicitly launches GUI")
    print("  pokertool scrape   # headless scraper stub")

    print("\nDone. (Dry-run)" if dry else "\nDone. Changes applied.")

if __name__ == "__main__":
    main()
