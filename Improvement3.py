# Improvement3.py
# Purpose: Sync README with actual files and embed a machine-readable API spec for poker_modules.py
# Usage: python3 Improvement3.py  (run from repository root)
# Python: 3.9+ recommended (works on macOS). Uses only stdlib.

from __future__ import annotations
import ast
import json
import os
import re
import sys
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent
README = REPO_ROOT / "README.md"
MODULE = REPO_ROOT / "poker_modules.py"
DOCS_DIR = REPO_ROOT / "docs"
SCHEMA_JSON = DOCS_DIR / "poker_modules.schema.json"

HEADER_START = "<!-- POKERTOOL-HEADER-START"
HEADER_END = "POKERTOOL-HEADER-END -->"
FILES_START = "<!-- AUTODOC:FILES-START -->"
FILES_END = "<!-- AUTODOC:FILES-END -->"
MODS_START = "<!-- AUTODOC:MODULES-START -->"
MODS_END = "<!-- AUTODOC:MODULES-END -->"

VERSION = "20"  # requested

# Fallback descriptions by filename
ROLE_HINTS = {
    "poker_modules.py": "Core poker logic: cards, enums, hand analysis",
    "poker_init.py": "Database initialization and persistence layer",
    "poker_gui.py": "Main graphical user interface",
    "poker_main.py": "Application launcher",
    "poker_go.py": "Setup/launcher with dependency checking",
    "poker_gui_autopilot.py": "Automated GUI driver for testing",
    "poker_imports.py": "Shared imports, globals, and constants",
    "poker_screen_scraper.py": "Screen/table scraping utilities",
    "poker_scraper_setup.py": "Scraper environment setup",
    "poker_tablediagram.py": "Table diagram helpers (ASCII/GUI)",
    "enhanced_poker_test_main.py": "Enhanced test entry point",
    "comprehensive_integration_tests.py": "Comprehensive integration tests",
    "final_test_validation.py": "Final validation tests",
    "gui_integration_tests.py": "GUI integration tests",
    "poker_test.py": "Unit tests",
    "security_validation_tests.py": "Security sanity checks",
    "saniitise_python_files.py": "Sanitise/fix Python files",
    "requirements.txt": "Runtime dependencies",
    "requirements_scraper.txt": "Dependencies for scraper",
    "poker_config.json": "Configuration file",
    "README.md": "Project documentation",
}

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def try_git(cmd: List[str]) -> Optional[str]:
    try:
        out = subprocess.check_output(cmd, cwd=REPO_ROOT, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None

def get_git_meta() -> Dict[str, Optional[str]]:
    return {
        "last_commit": try_git(["git", "log", "-1", "--format=%cI"]),
        "last_commit_hash": try_git(["git", "log", "-1", "--format=%H"]),
        "branch": try_git(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
    }

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def unparse(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)  # py3.9+
    except Exception:
        return ast.dump(node)

def parse_poker_modules() -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "schema": "pokermodules.v1",
        "module": "poker_modules.py",
        "generated_at": iso_now(),
        "hash": None,
        "enums": [],
        "classes": [],
        "functions": [],
        "constants": [],
        "errors": None,
    }
    if not MODULE.exists():
        spec["errors"] = "poker_modules.py not found"
        return spec

    spec["hash"] = sha256_file(MODULE)

    try:
        src = MODULE.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(MODULE))
    except Exception as e:
        spec["errors"] = f"ast.parse failed: {e.__class__.__name__}: {e}"
        return spec

    # Gather top-level assignments that look like CONSTANTS
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    spec["constants"].append({"name": t.id, "value": unparse(node.value)})

    def argspec(a: ast.arguments) -> List[Dict[str, Any]]:
        params: List[Dict[str, Any]] = []
        def add_arg(arg: ast.arg, default: Optional[ast.AST], kind: str):
            params.append({
                "name": arg.arg,
                "annotation": unparse(arg.annotation),
                "default": unparse(default) if default is not None else None,
                "kind": kind
            })

        # positional only (3.8+)
        posonly = getattr(a, "posonlyargs", [])
        for i, arg in enumerate(posonly):
            default = None
            add_arg(arg, default, "posonly")

        # regular args with defaults
        defaults = list(a.defaults)
        # align defaults to args
        n_defaults = len(defaults)
        n_args = len(a.args)
        for i, arg in enumerate(a.args):
            default = defaults[i - (n_args - n_defaults)] if i >= n_args - n_defaults else None
            add_arg(arg, default, "pos")

        if a.vararg:
            add_arg(a.vararg, None, "vararg")

        for kw, d in zip(a.kwonlyargs, a.kw_defaults):
            add_arg(kw, d, "kwonly")

        if a.kwarg:
            add_arg(a.kwarg, None, "varkw")

        return params

    def doc_firstline(doc: Optional[str]) -> Optional[str]:
        if not doc:
            return None
        # first non-empty line
        for line in doc.strip().splitlines():
            t = line.strip()
            if t:
                return t
        return None

    # Collect Enums, Classes, Functions
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [unparse(b) for b in node.bases]
            doc = ast.get_docstring(node)
            entry = {
                "name": node.name,
                "bases": bases,
                "summary": doc_firstline(doc),
                "methods": [],
                "is_enum": any(b.endswith("Enum") or b == "Enum" or b.endswith("enum.Enum") for b in bases),
            }
            # methods
            for b in node.body:
                if isinstance(b, ast.FunctionDef):
                    entry["methods"].append({
                        "name": b.name,
                        "summary": doc_firstline(ast.get_docstring(b)),
                        "returns": unparse(b.returns),
                        "params": argspec(b.args),
                        "decorators": [unparse(d) for d in b.decorator_list] if b.decorator_list else [],
                        "lineno": b.lineno,
                    })
            if entry["is_enum"]:
                # Try to capture enum members
                members = []
                for b in node.body:
                    if isinstance(b, ast.Assign):
                        for t in b.targets:
                            if isinstance(t, ast.Name):
                                members.append(t.id)
                entry["members"] = members
                spec["enums"].append(entry)
            else:
                spec["classes"].append(entry)

        elif isinstance(node, ast.FunctionDef):
            spec["functions"].append({
                "name": node.name,
                "summary": doc_firstline(ast.get_docstring(node)),
                "returns": unparse(node.returns),
                "params": argspec(node.args),
                "decorators": [unparse(d) for d in node.decorator_list] if node.decorator_list else [],
                "lineno": node.lineno,
            })

    return spec

def inventory_files() -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    # Include top-level files and selected subfolders
    globs = ["*.py", "*.txt", "*.md", "*.json", "requirements*.txt"]
    seen = set()
    for pat in globs:
        for p in sorted(REPO_ROOT.glob(pat)):
            if p.name.startswith("."):
                continue
            seen.add(p.resolve())
            files.append(p)
    # tests folder if present
    tests_dir = REPO_ROOT / "tests"
    if tests_dir.exists() and tests_dir.is_dir():
        for p in sorted(tests_dir.rglob("*")):
            if p.is_file():
                seen.add(p.resolve())
                files.append(p)

    rows = []
    for p in files:
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        except Exception:
            mtime = None
        role = ROLE_HINTS.get(p.name, "Utility/script" if p.suffix == ".py" else "Asset")
        rows.append({
            "path": str(p.relative_to(REPO_ROOT)),
            "role": role,
            "last_modified": mtime,
        })
    return rows

def render_files_table(inv: List[Dict[str, Any]]) -> str:
    # Markdown table
    header = "| File | Role | Last modified (UTC) |\n|---|---|---|"
    lines = [header]
    for r in inv:
        lines.append(f"| `{r['path']}` | {r['role']} | {r['last_modified'] or ''} |")
    return "\n".join(lines)

def ensure_header_block(text: str, files_count: int, modules_hash: Optional[str], git_meta: Dict[str, Optional[str]]) -> str:
    header_yaml = [
        HEADER_START,
        "---",
        "schema: pokerheader.v1",
        "project: pokertool",
        "file: README.md",
        f"version: '{VERSION}'",
        f"last_commit: '{git_meta.get('last_commit') or ''}'",
        f"last_commit_hash: '{git_meta.get('last_commit_hash') or ''}'",
        f"branch: '{git_meta.get('branch') or ''}'",
        f"files_count: {files_count}",
        f"modules_hash: '{modules_hash or ''}'",
        "fixes: ['readme_sync','modules_doc_generated']",
        "---",
        HEADER_END,
    ]
    block = "\n".join(header_yaml)
    if HEADER_START in text and HEADER_END in text:
        # replace existing header
        pattern = re.compile(re.escape(HEADER_START) + r".*?" + re.escape(HEADER_END), re.DOTALL)
        return pattern.sub(block, text, count=1)
    else:
        return block + "\n\n" + text

def upsert_region(text: str, start_marker: str, end_marker: str, new_content_md: str) -> str:
    block = f"{start_marker}\n{new_content_md}\n{end_marker}"
    if start_marker in text and end_marker in text:
        pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
        return pattern.sub(block, text, count=1)
    else:
        return text + ("\n\n" if text and not text.endswith("\n") else "\n") + block + "\n"

def build_modules_md(spec: Dict[str, Any]) -> str:
    # Embed JSON for machine-readability and add a short human section
    json_str = json.dumps(spec, indent=2, ensure_ascii=False)
    lines = []
    lines.append("## Machine-readable API for `poker_modules.py`")
    if spec.get("errors"):
        lines.append(f"> Generation error: `{spec['errors']}`")
    lines.append("")
    lines.append("```json")
    lines.append(json_str)
    lines.append("```")
    lines.append("")
    lines.append("_Regenerate with:_ `python3 Improvement3.py`")
    return "\n".join(lines)

def build_files_md(inv: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("## Files Included")
    lines.append("")
    lines.append(render_files_table(inv))
    return "\n".join(lines)

def seed_readme_if_missing() -> None:
    if not README.exists():
        README.write_text("# PokerTool\n\n", encoding="utf-8")

def main() -> int:
    seed_readme_if_missing()

    inv = inventory_files()
    spec = parse_poker_modules()

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with SCHEMA_JSON.open("w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)

    files_md = build_files_md(inv)
    modules_md = build_modules_md(spec)
    base = README.read_text(encoding="utf-8", errors="replace")

    # Insert/replace the canonical header
    git_meta = get_git_meta()
    updated = ensure_header_block(base, files_count=len(inv), modules_hash=spec.get("hash"), git_meta=git_meta)

    # Insert/replace the Files inventory
    updated = upsert_region(updated, FILES_START, FILES_END, files_md)

    # Insert/replace the modules spec section
    updated = upsert_region(updated, MODS_START, MODS_END, modules_md)

    # Ensure minimal high-level sections exist
    if "# Poker Assistant" not in updated and "# PokerTool" not in updated:
        intro = (
            "# Poker Assistant\n\n"
            "This repository contains the poker assistant application, GUI, core logic, scraper, and tests.\n\n"
            "Run `python3 poker_go.py` to launch. See the sections below for inventory and API details.\n"
        )
        updated = updated + ("\n\n" if not updated.endswith("\n") else "") + intro

    README.write_text(updated, encoding="utf-8")

    print("README.md updated.")
    print(f"Wrote machine-readable spec: {SCHEMA_JSON}")
    print(f"Files indexed: {len(inv)}")
    if spec.get("errors"):
        print(f"Warning: module doc error: {spec['errors']}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
