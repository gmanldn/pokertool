#!/usr/bin/env python3
r"""
classify_and_move_updates.py

Scan the repository root for .py files, decide which ones are permanent
application files vs one-time update/upgrade scripts, and (optionally)
move the update scripts into a 'forwardscripts' folder.

Heuristics used:
- Filenames with update-y prefixes/suffixes (e.g., update_, upgrade_, patch_, hotfix_, migrate_, fix_, apply_, temp_).
- Filenames matching common "versioned update" patterns (e.g., *_v\d+(_\d+)?\.py, up?date_*).
- Mentions inside the file text like "UPDATE SCRIPT", "ONE-TIME", "apply once", etc.
- Presence in `version_summary_update.md` as applied updates (we extract .py names, and look for words like "applied", "merged", "done").
- Static import analysis: anything imported (directly or indirectly) by poker_main.py is treated as PERMANENT.
- If a script is imported by any other script in the repo, it's more likely to be permanent; a script with only a __main__ entrypoint is more likely to be a one-off.
- Files inside subfolders are ignored by default (this tool focuses on root), unless --include-subfolders is provided.

Usage:
  python3 classify_and_move_updates.py [--repo .] [--move] [--include-subfolders] [--dry-run]

Defaults:
  --repo .                 Work in current directory.
  --move                   Actually move detected update scripts to forwardscripts/ (default: no move).
  --include-subfolders     Also scan Python files in immediate subfolders.
  --dry-run                Print actions only; do not move files.
  --verbose                Extra logging.
  --save-report            Write a JSON and Markdown report in repo root.

Exit codes:
  0 on success.
  1 on unexpected error.
"""
import argparse
import re
import sys
from pathlib import Path
import json
import ast
import shutil
from typing import List, Dict, Set, Tuple

UPDATE_NAME_PATTERNS = [
    r'^(?:up?date|upgrade|patch|hotfix|fix|apply|migrate|migration|repair|sanitize|saniti[sz]e|cleanup|refactor|temp|one[_-]?time)[_-].*\.py$',
    r'.*[_-](?:up?date|upgrade|patch|hotfix|fix|apply|migrate|migration|repair|sanitize|saniti[sz]e|cleanup|refactor|one[_-]?time)[_-]v?\d+(?:[_-]\d+)?\.py$',
    r'.*v?\d{2,4}(?:[_-]\d+)?\.(?:py)$',  # e.g., *_v24.py, *_2024_09.py
    r'^(?:apply|run|exec)[_-]update.*\.py$',
]

UPDATE_TEXT_HINTS = [
    "UPDATE SCRIPT",
    "ONE-TIME",
    "RUN ONCE",
    "apply once",
    "migration",
    "hotfix",
    "backfill",
    "data fix",
    "schema update",
    "autofix",
    "sanitise",
    "sanitize",
]

APPLIED_HINT_WORDS = [
    "applied",
    "merged",
    "done",
    "completed",
    "already",
    "in repo",
    "committed",
]

# Some known core app entrypoints/modules in PokerTool context
LIKELY_CORE_FILES = {
    "poker_main.py",
    "poker_modules.py",
    "poker_init.py",
    "poker_gui.py",
    "poker_gui_enhanced.py",
    "poker_go.py",
    "start.py",
    "__init__.py",
}

PY_NAME_RE = re.compile(r'([A-Za-z0-9_./-]+\.py)')

def read_text_safe(p: Path, limit_bytes: int = 2_000_000) -> str:
    try:
        data = p.read_bytes()
        if len(data) > limit_bytes:
            data = data[:limit_bytes]
        return data.decode('utf-8', errors='replace')
    except Exception:
        return ""

def extract_py_names_from_markdown(md_text: str) -> Set[str]:
    names = set(m.group(1) for m in PY_NAME_RE.finditer(md_text))
    # normalize to basename
    return {Path(n).name for n in names}

def file_matches_update_name(fname: str) -> bool:
    fname_lower = fname.lower()
    for pat in UPDATE_NAME_PATTERNS:
        if re.match(pat, fname_lower):
            return True
    # typos like 'upate_*.py'
    if fname_lower.startswith("upate_"):
        return True
    return False

def file_has_update_hints(text: str) -> bool:
    t = text.upper()
    return any(hint in t for hint in UPDATE_TEXT_HINTS)

def analyze_imports(py_path: Path) -> Set[str]:
    """Return a set of top-level imported module base names from a .py file."""
    out: Set[str] = set()
    try:
        tree = ast.parse(read_text_safe(py_path))
    except Exception:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                out.add(n.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.add(node.module.split('.')[0])
    return out

def find_import_graph(py_files: List[Path]) -> Dict[str, Set[str]]:
    """key: module (basename without .py), value: set of modules it imports"""
    graph: Dict[str, Set[str]] = {}
    name_by_file = {p: p.stem for p in py_files}
    for p in py_files:
        imports = analyze_imports(p)
        graph[name_by_file[p]] = imports
    return graph

def transitive_imports(graph: Dict[str, Set[str]], start: str) -> Set[str]:
    seen: Set[str] = set()
    stack = [start]
    while stack:
        mod = stack.pop()
        if mod in seen:
            continue
        seen.add(mod)
        for dep in graph.get(mod, set()):
            if dep not in seen:
                stack.append(dep)
    return seen

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".", help="Path to repository root (default: .)")
    ap.add_argument("--move", action="store_true", help="Move update scripts into forwardscripts/")
    ap.add_argument("--include-subfolders", action="store_true", help="Also scan immediate subfolders for .py files")
    ap.add_argument("--dry-run", action="store_true", help="Print planned actions only")
    ap.add_argument("--verbose", action="store_true", help="Verbose logging")
    ap.add_argument("--save-report", action="store_true", help="Write JSON and Markdown report")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists():
        print(f"[error] repo not found: {repo}", file=sys.stderr)
        return 1

    # collect .py files in root (and optionally immediate subfolders)
    py_files: List[Path] = [p for p in repo.glob("*.py")]
    if args.include_subfolders:
        for sub in [d for d in repo.iterdir() if d.is_dir() and not d.name.startswith(".")]:
            py_files.extend(sub.glob("*.py"))

    # Load version_summary_update.md if present
    applied_from_md: Set[str] = set()
    applied_words_present = False
    vsu = repo / "version_summary_update.md"
    if vsu.exists():
        md_text = read_text_safe(vsu)
        applied_from_md = extract_py_names_from_markdown(md_text)
        applied_words_present = any(w in md_text.lower() for w in APPLIED_HINT_WORDS)

    if args.verbose:
        print(f"[info] repo: {repo}")
        print(f"[info] py files considered: {len(py_files)}")
        if vsu.exists():
            print(f"[info] version_summary_update.md found; {len(applied_from_md)} .py names referenced")

    # Build import graph to identify files used by poker_main.py
    graph = find_import_graph([p for p in py_files if p.is_file()])
    # Resolve which module corresponds to poker_main.py if present
    poker_main = repo / "poker_main.py"
    permanent_candidates: Set[str] = set()
    if poker_main.exists():
        permanent_candidates = transitive_imports(graph, "poker_main")
        permanent_candidates.add("poker_main")
    # Also mark known core files as permanent
    for core in LIKELY_CORE_FILES:
        if (repo / core).exists():
            permanent_candidates.add(Path(core).stem)

    classifications: Dict[str, Dict[str, object]] = {}
    for p in py_files:
        name = p.name
        text = read_text_safe(p)
        reasons: List[str] = []
        decision = "unknown"

        if name in LIKELY_CORE_FILES:
            decision = "permanent"
            reasons.append("Known core filename")
        elif p.stem in permanent_candidates:
            decision = "permanent"
            reasons.append("Imported (directly or transitively) by poker_main.py / core")

        # Name-based signal
        if file_matches_update_name(name):
            if decision != "permanent":
                decision = "update"
            reasons.append("Filename matches update pattern")

        # Content-based signal
        if file_has_update_hints(text):
            if decision != "permanent":
                decision = "update"
            reasons.append("Contains update/migration text hints")

        # Mentioned in version_summary_update.md
        if name in applied_from_md and applied_words_present:
            if decision != "permanent":
                decision = "update"
            reasons.append("Mentioned as applied in version_summary_update.md")

        # If still unknown: infer by entrypoint style
        if decision == "unknown":
            if "__name__ == '__main__'" in text.replace('"', "'"):
                decision = "update"  # likely a one-off script
                reasons.append("Has __main__ entrypoint (likely standalone)")
            else:
                decision = "permanent"
                reasons.append("Defaulted to permanent (no update signals)")

        classifications[name] = {
            "path": str(p),
            "decision": decision,
            "reasons": reasons,
        }

    # Compute move plan
    to_move = [repo / name for name, info in classifications.items()
               if info["decision"] == "update" and Path(info["path"]).parent == repo]

    forwards_dir = repo / "forwardscripts"
    actions: List[str] = []

    if to_move and (args.move or args.dry_run):
        if not forwards_dir.exists():
            actions.append(f"Create directory: {forwards_dir}")
            if not args.dry_run:
                forwards_dir.mkdir(parents=True, exist_ok=True)

        init_file = forwards_dir / "__init__.py"
        if not init_file.exists():
            actions.append(f"Create file: {init_file}")
            if not args.dry_run:
                init_file.write_text("# forwardscripts package\n", encoding="utf-8")

        for src in to_move:
            dst = forwards_dir / src.name
            actions.append(f"Move {src.name} -> {forwards_dir.name}/{src.name}")
            if not args.dry_run and src.exists():
                shutil.move(str(src), str(dst))

    # Save report if requested
    if args.save_report:
        report_json = repo / "update_classification_report.json"
        report_md = repo / "update_classification_report.md"

        with report_json.open("w", encoding="utf-8") as f:
            json.dump(classifications, f, indent=2)

        with report_md.open("w", encoding="utf-8") as f:
            f.write("# Update Classification Report\n\n")
            f.write("| File | Decision | Reasons |\n")
            f.write("|------|----------|---------|\n")
            for name, info in sorted(classifications.items()):
                f.write(f"| {name} | {info['decision']} | {'; '.join(info['reasons'])} |\n")

        print(f"[report] wrote {report_json.name} and {report_md.name}")

    print("[summary] decisions:")
    for name, info in sorted(classifications.items()):
        print(f"  - {name}: {info['decision']} ({'; '.join(info['reasons'])})")

    if actions:
        print("\n[actions]")
        for a in actions:
            print(f"  - {a}")
    else:
        print("\n[actions] No move actions (use --move or --dry-run).")

    return 0

if __name__ == "__main__":
    sys.exit(main())
