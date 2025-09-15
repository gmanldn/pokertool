#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improvement2.py — PokerTool v20 follow-up (idempotent)
- Proves improvement series concept
- Generates/updates CHANGELOG.md (v20 entry)
- Refreshes docs/modules_index.json (rebuild), and README "Improvements Log"
- Updates headers on files it touches (README.md, CHANGELOG.md), appending applied_improvements
- Records applied improvements in .pokertool_state.json
"""

import os, re, json
from datetime import datetime, timezone
from pathlib import Path
import ast

VERSION_STR = "20"
PROJECT = "pokertool"
SCHEMA = "pokerheader.v1"
STATE_FILE = ".pokertool_state.json"
DOCS_DIR = Path("docs")
MODULES_INDEX_JSON = DOCS_DIR / "modules_index.json"
CHANGELOG_MD = Path("CHANGELOG.md")
README_MD = Path("README.md")
THIS_FILE = "Improvement2.py"
UTC_NOW = datetime.now(timezone.utc).isoformat()

PY_START = "# POKERTOOL-HEADER-START"
# ---
# schema: pokerheader.v1
# project: pokertool
# file: Improvement2.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Auto-labeled purpose for Improvement2.py
# ---
# POKERTOOL-HEADER-END
__version__ = "20"

MD_START = "<!-- POKERTOOL-HEADER-START"
MD_END   = "POKERTOOL-HEADER-END -->"

def load_state():
    if Path(STATE_FILE).exists():
        try:
            return json.loads(Path(STATE_FILE).read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_state(state):
    Path(STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")

def relpath(p: Path) -> str:
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)

def header_block_for_md(p: Path, applied):
    lines = [
        MD_START,
        "---",
        f"schema: {SCHEMA}",
        f"project: {PROJECT}",
        f"file: {relpath(p)}",
        f"version: '{VERSION_STR}'",
        f"last_updated_utc: '{UTC_NOW}'",
        f"applied_improvements: [{', '.join(applied)}]",
        "summary: Project changelog" if p.name == "CHANGELOG.md" else "summary: Project readme",
        "---",
        MD_END,
        "",
    ]
    return "\n".join(lines)

def parse_existing_improvements(header_text: str):
    import re
    m = re.search(r"applied_improvements:\s*\[(.*?)\]", header_text, re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw:
        return []
    parts = [x.strip() for x in raw.split(",")]
    return [p for p in parts if p]

def ensure_md_header(p: Path, improvement_name: str):
    is_md = p.suffix.lower() == ".md"
    start_marker = MD_START
    end_marker = MD_END
    text = p.read_text(encoding="utf-8", errors="replace")
    header_re = re.compile(
        r"(?s)" + re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\s*"
    )
    if header_re.search(text):
        header_text = header_re.search(text).group(0)
        applied = parse_existing_improvements(header_text)
        if improvement_name not in applied:
            applied.append(improvement_name)
        block = header_block_for_md(p, applied)
        new_text = header_re.sub(block, text, count=1)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            return True
        return False
    else:
        block = header_block_for_md(p, [improvement_name])
        p.write_text(block + text, encoding="utf-8")
        return True

def ast_index():
    index = {}
    for root, _, files in os.walk("."):
        if any(part in root for part in (".git", "venv", ".venv", "__pycache__", "build", "dist")):
            continue
        for f in files:
            if f.endswith(".py"):
                p = Path(root) / f
                try:
                    tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
                    funs, classes = [], []
                    for node in tree.body:
                        if isinstance(node, ast.FunctionDef):
                            funs.append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                    index[relpath(p)] = {"functions": funs, "classes": classes}
                except Exception as e:
                    index[relpath(p)] = {"error": f"{type(e).__name__}: {e}"}
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    MODULES_INDEX_JSON.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index

def update_readme_log(new_entry):
    if not README_MD.exists():
        README_MD.write_text("# PokerTool\n\n", encoding="utf-8")
    text = README_MD.read_text(encoding="utf-8", errors="replace")
    heading = "## Improvements Log"
    if heading not in text:
        text += f"\n\n{heading}\n\n"
        README_MD.write_text(text, encoding="utf-8")
        text = README_MD.read_text(encoding="utf-8", errors="replace")
    # Load existing JSON ledger if available
    ledger = []
    try:
        ledger = json.loads((Path("docs") / "improvements.json").read_text(encoding="utf-8"))
    except Exception:
        pass
    ledger.append(new_entry)
    # Render last 20
    rows = []
    rows.append("\n<!-- IMPROVEMENTS-START -->\n")
    rows.append("| When (UTC) | Improvement | Summary | Files touched |\n")
    rows.append("|---|---|---|---|\n")
    for e in ledger[-20:]:
        rows.append(f"| {e.get('when','')} | {e.get('name','')} | {e.get('summary','')} | {e.get('files_touched',0)} |\n")
    rows.append("<!-- IMPROVEMENTS-END -->\n")
    text = re.sub(r"\n<!-- IMPROVEMENTS-START -->.*?<!-- IMPROVEMENTS-END -->\n",
                  "\n", text, flags=re.S)
    README_MD.write_text(text + "".join(rows), encoding="utf-8")
    ensure_md_header(README_MD, THIS_FILE)

def update_changelog(index):
    if not CHANGELOG_MD.exists():
        CHANGELOG_MD.write_text("# Changelog\n\n", encoding="utf-8")
    text = CHANGELOG_MD.read_text(encoding="utf-8", errors="replace")
    entry_title = f"## v{VERSION_STR} — {UTC_NOW[:10]}"
    if entry_title not in text:
        text += (
            f"\n{entry_title}\n\n"
            "- Header unification and version markers across codebase\n"
            "- Machine-readable module inventory generated (docs/modules_index.json)\n"
            "- README Improvements Log updated\n"
        )
        CHANGELOG_MD.write_text(text, encoding="utf-8")
    ensure_md_header(CHANGELOG_MD, THIS_FILE)

def main():
    state = load_state()
    applied = state.get("applied", [])
    if THIS_FILE in applied:
        print(f"[info] {THIS_FILE} already applied; idempotent no-op.")
        return

    index = ast_index()
    update_changelog(index)

    entry = {
        "name": THIS_FILE,
        "when": UTC_NOW,
        "version": VERSION_STR,
        "summary": "CHANGELOG added, module inventory refreshed, README log updated",
        "files_touched": 2  # README.md + CHANGELOG.md
    }

    # Update README log and header on touched files
    update_readme_log(entry)

    # Mark state
    applied.append(THIS_FILE)
    state["applied"] = applied
    save_state(state)

    print(f"[ok] {THIS_FILE} applied. changelog+readme updated.")

if __name__ == "__main__":
    main()
