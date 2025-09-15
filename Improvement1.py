#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improvement1.py — PokerTool v20 schema rollout (idempotent)
- Adds/updates canonical headers (pokerheader.v1) on all relevant files
- Sets module __version__ to "20" where applicable
- Generates/updates README "Improvements Log" (idempotent)
- Produces machine-readable audit: docs/improvements.json, docs/modules_index.json
- Compiles all .py files (py_compile) and AST-parses them to detect syntax issues (no import side-effects)
- Writes build report to build_reports/report_<timestamp>.json (+ .txt summary)
- Records applied improvements in .pokertool_state.json
"""

import os, re, json, ast, py_compile, traceback, hashlib
from datetime import datetime, timezone
from pathlib import Path

VERSION_STR = "20"
PROJECT = "pokertool"
SCHEMA = "pokerheader.v1"
STATE_FILE = ".pokertool_state.json"
DOCS_DIR = Path("docs")
TOOLS_DIR = Path("tools")
REPORTS_DIR = Path("build_reports")
IMPROVEMENTS_JSON = DOCS_DIR / "improvements.json"
MODULES_INDEX_JSON = DOCS_DIR / "modules_index.json"
CHANGELOG_MD = Path("CHANGELOG.md")  # created by Improvement2, but we'll not touch here
README_MD = Path("README.md")
THIS_FILE = "Improvement1.py"
UTC_NOW = datetime.now(timezone.utc).isoformat()

# File type header markers
PY_START = "# POKERTOOL-HEADER-START"
PY_END   = "# POKERTOOL-HEADER-END"
MD_START = "<!-- POKERTOOL-HEADER-START"
MD_END   = "POKERTOOL-HEADER-END -->"

# Purpose hints by filename (fallbacks are auto-generated)
PURPOSE_HINTS = {
    "poker_modules.py": "Core poker logic, hand analysis, and card handling",
    "poker_init.py": "Database initialization and persistence layer",
    "poker_gui.py": "Main graphical user interface",
    "poker_main.py": "Application launcher",
    "poker_go.py": "Setup script with dependency checks",
    "poker_gui_autopilot.py": "GUI automation for tests",
    "poker_imports.py": "Import glue / public API surface",
    "poker_screen_scraper.py": "Screen scraping utilities",
    "poker_scraper_setup.py": "Scraper setup helpers",
    "poker_tablediagram.py": "Table diagram utilities",
    "poker_test.py": "Unit tests",
    "comprehensive_integration_tests.py": "Comprehensive integration tests",
    "gui_integration_tests.py": "GUI integration tests",
    "final_test_validation.py": "Final validation tests",
    "security_validation_tests.py": "Security validation tests",
    "saniitise_python_files.py": "Sanitize Python files",
    "README.md": "Project overview and usage",
}

# ---------------------------------------------------------------------

def load_state():
    if Path(STATE_FILE).exists():
        try:
            return json.loads(Path(STATE_FILE).read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_state(state):
    Path(STATE_FILE).write_text(json.dumps(state, indent=2), encoding="utf-8")

def ensure_dirs():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def relpath(p: Path) -> str:
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)

def file_purpose(p: Path) -> str:
    return PURPOSE_HINTS.get(p.name, f"Auto-labeled purpose for {p.name}")

def hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

def header_block_for_py(p: Path, applied_improvements):
    rel = relpath(p)
    purpose = file_purpose(p)
    applied_str = ", ".join(applied_improvements)
    lines = [
        PY_START,
        "# ---",
        f"# schema: {SCHEMA}",
        f"# project: {PROJECT}",
        f"# file: {rel}",
        f"# version: '{VERSION_STR}'",
        f"# last_updated_utc: '{UTC_NOW}'",
        f"# applied_improvements: [{applied_str}]",
        f"# summary: {purpose}",
        "# ---",
        PY_END,
        "",
    ]
    return "\n".join(lines)

def header_block_for_md(p: Path, applied_improvements):
    rel = relpath(p)
    purpose = file_purpose(p)
    applied_str = ", ".join(applied_improvements)
    lines = [
        MD_START,
        "---",
        f"schema: {SCHEMA}",
        f"project: {PROJECT}",
        f"file: {rel}",
        f"version: '{VERSION_STR}'",
        f"last_updated_utc: '{UTC_NOW}'",
        f"applied_improvements: [{applied_str}]",
        f"summary: {purpose}",
        "---",
        MD_END,
        "",
    ]
    return "\n".join(lines)

def parse_existing_improvements(header_text: str):
    # Extract applied_improvements list if present
    m = re.search(r"applied_improvements:\s*\[(.*?)\]", header_text, re.IGNORECASE)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw:
        return []
    # Split on commas (simple parser; entries are names like Improvement1.py)
    parts = [x.strip() for x in raw.split(",")]
    return [p for p in parts if p]

def ensure_header(p: Path, improvement_name: str):
    text = p.read_text(encoding="utf-8", errors="replace")
    is_py = p.suffix == ".py"
    start_marker = PY_START if is_py else MD_START
    end_marker = PY_END if is_py else MD_END
    header_re = re.compile(
        r"(?s)" + re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\s*"
    )
    if header_re.search(text):
        # Update existing header: merge applied_improvements and bump version/time
        header_text = header_re.search(text).group(0)
        applied = parse_existing_improvements(header_text)
        if improvement_name not in applied:
            applied.append(improvement_name)
        # Rebuild header with merged list
        block = header_block_for_py(p, applied) if is_py else header_block_for_md(p, applied)
        new_text = header_re.sub(block, text, count=1)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            return True, "updated-header"
        return False, "header-unchanged"
    else:
        # Insert new header at top (respect shebang for .py)
        applied = [improvement_name]
        block = header_block_for_py(p, applied) if is_py else header_block_for_md(p, applied)
        if is_py and text.startswith("#!"):
            # keep shebang first line
            first_line, rest = text.split("\n", 1)
            new_text = first_line + "\n" + block + rest
        else:
            new_text = block + text
        p.write_text(new_text, encoding="utf-8")
        return True, "inserted-header"

def ensure_version_var(p: Path):
    if p.suffix != ".py":
        return False, "not-python"
    text = p.read_text(encoding="utf-8", errors="replace")
    # If __version__ exists, update; else insert right after header or at top
    version_re = re.compile(r"^(__version__\s*=\s*['\"])([^'\"]+)(['\"])", re.MULTILINE)
    m = version_re.search(text)
    if m:
        new_text = version_re.sub(rf"\g<1>{VERSION_STR}\3", text, count=1)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            return True, "version-updated"
        return False, "version-unchanged"
    # Insert after header if present
    header_end_idx = text.find(PY_END)
    insertion = f"__version__ = \"{VERSION_STR}\"\n\n"
    if header_end_idx != -1:
        insert_at = header_end_idx + len(PY_END)
        new_text = text[:insert_at] + "\n" + insertion + text[insert_at:]
    else:
        new_text = insertion + text
    p.write_text(new_text, encoding="utf-8")
    return True, "version-inserted"

def find_target_files():
    root = Path.cwd()
    ignore_dirs = {".git", ".venv", "venv", "__pycache__", ".idea", ".eggs", "build", "dist"}
    exts = {".py", ".md"}
    files = []
    for dp, dn, fn in os.walk(root):
        dname = Path(dp).name
        if dname in ignore_dirs:
            continue
        for f in fn:
            p = Path(dp) / f
            if p.suffix in exts:
                files.append(p)
    return files

def py_compile_file(p: Path):
    try:
        py_compile.compile(str(p), doraise=True)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def ast_index_file(p: Path):
    results = {"functions": [], "classes": []}
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                results["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                results["classes"].append(node.name)
        return True, results, None
    except Exception as e:
        return False, results, f"{type(e).__name__}: {e}"

def update_readme_log(entries):
    # Ensure README exists
    if not README_MD.exists():
        README_MD.write_text("# PokerTool\n\n", encoding="utf-8")

    text = README_MD.read_text(encoding="utf-8", errors="replace")
    heading = "## Improvements Log"
    if heading not in text:
        text += f"\n\n{heading}\n\n"
        README_MD.write_text(text, encoding="utf-8")

    text = README_MD.read_text(encoding="utf-8", errors="replace")
    # Build a normalized table section (idempotent insert/update for this improvement)
    # We'll append a compact markdown list keyed by improvement name + hash of content.
    out_lines = []
    out_lines.append("\n<!-- IMPROVEMENTS-START -->\n")
    # If there is an existing block, remove and replace (keep idempotent single block)
    text = re.sub(r"\n<!-- IMPROVEMENTS-START -->.*?<!-- IMPROVEMENTS-END -->\n",
                  "\n", text, flags=re.S)
    out_lines.append("| When (UTC) | Improvement | Summary | Files touched |\n")
    out_lines.append("|---|---|---|---|\n")
    for e in entries:
        out_lines.append(f"| {e['when']} | {e['name']} | {e['summary']} | {e['files_touched']} |\n")
    out_lines.append("<!-- IMPROVEMENTS-END -->\n")
    README_MD.write_text(text + "".join(out_lines), encoding="utf-8")

def main():
    ensure_dirs()
    state = load_state()
    applied = state.get("applied", [])
    if THIS_FILE in applied:
        print(f"[info] {THIS_FILE} already applied; idempotent no-op.")
        return

    all_files = find_target_files()
    updated = []
    header_changes = 0
    version_changes = 0

    # Apply headers + version bumps
    for p in all_files:
        if p.name == THIS_FILE:
            continue
        # headers
        changed, how = ensure_header(p, THIS_FILE)
        if changed:
            updated.append({"file": relpath(p), "change": how})
            header_changes += 1
        # version var for .py
        v_changed, v_how = ensure_version_var(p)
        if v_changed and p.suffix == ".py":
            updated.append({"file": relpath(p), "change": v_how})
            version_changes += 1

    # Compile and AST index
    compile_results = {}
    modules_index = {}
    compile_failures = 0
    for p in sorted([x for x in all_files if x.suffix == ".py"]):
        ok, err = py_compile_file(p)
        compile_results[relpath(p)] = {"compiled": ok, "error": err}
        if not ok:
            compile_failures += 1
        ok2, idx, err2 = ast_index_file(p)
        modules_index[relpath(p)] = {"ok": ok2, "index": idx, "error": err2}

    # Write machine-readable outputs
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    MODULES_INDEX_JSON.write_text(json.dumps(modules_index, indent=2), encoding="utf-8")

    # Improvements ledger (append or create)
    improvements = []
    if IMPROVEMENTS_JSON.exists():
        try:
            improvements = json.loads(IMPROVEMENTS_JSON.read_text(encoding="utf-8"))
        except Exception:
            improvements = []
    summary = f"v{VERSION_STR} header rollout, version vars, compile+AST audit"
    improvements.append({
        "name": THIS_FILE,
        "when": UTC_NOW,
        "version": VERSION_STR,
        "summary": summary,
        "files_touched": len(updated),
        "compile_failures": compile_failures,
    })
    IMPROVEMENTS_JSON.write_text(json.dumps(improvements, indent=2), encoding="utf-8")

    # Update README Improvements Log (render last N=20)
    update_readme_log(improvements[-20:])

    # Build report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "improvement": THIS_FILE,
        "timestamp_utc": UTC_NOW,
        "version": VERSION_STR,
        "updated": updated,
        "compile_results": compile_results,
        "compile_failures": compile_failures,
        "modules_index_json": str(MODULES_INDEX_JSON),
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (REPORTS_DIR / f"report_{THIS_FILE}_{stamp}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPORTS_DIR / f"report_{THIS_FILE}_{stamp}.txt").write_text(
        f"Improvement: {THIS_FILE}\nTime (UTC): {UTC_NOW}\nVersion: {VERSION_STR}\n"
        f"Files touched: {len(updated)}\nCompile failures: {compile_failures}\n",
        encoding="utf-8"
    )

    # Write a simple tools/verify_build.py (idempotent create if missing)
    verify_path = TOOLS_DIR / "verify_build.py"
    if not verify_path.exists():
        verify_path.write_text(
            "# Auto-generated by Improvement1.py\n"
            "import py_compile, os, sys\n"
            "fail=0\n"
            "for root,_,files in os.walk('.'):\n"
            "    if any(part in root for part in ('.git','venv','.venv','__pycache__','build','dist')):\n"
            "        continue\n"
            "    for f in files:\n"
            "        if f.endswith('.py') and f!='verify_build.py':\n"
            "            p=os.path.join(root,f)\n"
            "            try:\n"
            "                py_compile.compile(p, doraise=True)\n"
            "            except Exception as e:\n"
            "                print('[compile-fail]', p, e)\n"
            "                fail+=1\n"
            "print('compile_failures=',fail)\n"
            "sys.exit(1 if fail else 0)\n",
            encoding="utf-8"
        )

    # Mark state
    applied.append(THIS_FILE)
    state["applied"] = applied
    save_state(state)

    print(f"[ok] {THIS_FILE} applied. headers:{header_changes} version_updates:{version_changes} compile_failures:{compile_failures}")

if __name__ == "__main__":
    main()
