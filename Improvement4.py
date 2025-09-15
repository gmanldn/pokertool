# Improvement4.py
# Per-file headers, README/docs sync, machine-readable API, and unit tests.
# Usage: python3 Improvement4.py  (run from repo root)

from __future__ import annotations
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------
# Config
# -----------------------------
REPO = Path(__file__).resolve().parent
DOCS = REPO / "docs"
TESTS = REPO / "tests"
README = REPO / "README.md"
MODULE_PM = REPO / "poker_modules.py"
SCHEMA_JSON = DOCS / "poker_modules.schema.json"
MANIFEST_JSON = DOCS / "manifest.json"
VERSION_FILE = REPO / "VERSION.txt"
BACKUP_DIR = REPO / ("_backup_" + datetime.now().strftime("%Y%m%d-%H%M%S"))

PROJECT = "pokertool"
HEADER_SCHEMA = "pokerheader.v1"
MODULE_SCHEMA = "pokermodules.v1"
VERSION = "20"

# Header markers
HTML_START = "<!-- POKERTOOL-HEADER-START"
HTML_END = "POKERTOOL-HEADER-END -->"
PY_START = "# POKERTOOL-HEADER-START"
PY_END = "# POKERTOOL-HEADER-END"
YAML_OPEN = "---"
YAML_CLOSE = "---"

# Managed README regions
FILES_START = "<!-- AUTODOC:FILES-START -->"
FILES_END = "<!-- AUTODOC:FILES-END -->"
MODS_START = "<!-- AUTODOC:MODULES-START -->"
MODS_END = "<!-- AUTODOC:MODULES-END -->"

ROLE_HINTS = {
    "poker_modules.py": "Core poker logic: cards, enums, hand analysis",
    "poker_init.py": "Database initialization and persistence layer",
    "poker_gui.py": "Main graphical user interface",
    "poker_main.py": "Application launcher",
    "poker_go.py": "Setup/launcher with dependency checking",
    "poker_gui_autopilot.py": "Automated GUI driver for testing",
    "poker_imports.py": "Shared imports and constants",
    "poker_screen_scraper.py": "Screen/table scraping utilities",
    "poker_scraper_setup.py": "Scraper environment setup",
    "poker_tablediagram.py": "Table diagram helpers",
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

# -----------------------------
# Utilities
# -----------------------------
def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def try_git(cmd: List[str]) -> Optional[str]:
    try:
        out = subprocess.check_output(cmd, cwd=REPO, stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return None

def git_meta() -> Dict[str, Optional[str]]:
    return {
        "last_commit": try_git(["git", "log", "-1", "--format=%cI"]),
        "last_commit_hash": try_git(["git", "log", "-1", "--format=%H"]),
        "branch": try_git(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
    }

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def ensure_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)

def backup(files: List[Path]) -> None:
    ensure_dir(BACKUP_DIR)
    for f in files:
        dst = BACKUP_DIR / f.relative_to(REPO)
        ensure_dir(dst.parent)
        shutil.copy2(f, dst)

# -----------------------------
# Module API analysis (AST)
# -----------------------------
def ast_unparse(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None

def parse_poker_modules() -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "schema": MODULE_SCHEMA,
        "module": "poker_modules.py",
        "generated_at": iso_now(),
        "hash": None,
        "enums": [],
        "classes": [],
        "functions": [],
        "constants": [],
        "errors": None,
    }
    if not MODULE_PM.exists():
        spec["errors"] = "poker_modules.py not found"
        return spec
    spec["hash"] = sha256_file(MODULE_PM)
    try:
        src = read_text(MODULE_PM)
        tree = ast.parse(src, filename=str(MODULE_PM))
    except Exception as e:
        spec["errors"] = f"ast.parse failed: {e.__class__.__name__}: {e}"
        return spec

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    spec["constants"].append({"name": t.id, "value": ast_unparse(node.value)})

    def argspec(a: ast.arguments) -> List[Dict[str, Any]]:
        params: List[Dict[str, Any]] = []
        def add(arg: ast.arg, default: Optional[ast.AST], kind: str):
            params.append({
                "name": arg.arg,
                "annotation": ast_unparse(arg.annotation),
                "default": ast_unparse(default) if default is not None else None,
                "kind": kind,
            })
        posonly = getattr(a, "posonlyargs", [])
        for arg in posonly:
            add(arg, None, "posonly")
        defaults = list(a.defaults)
        n_def, n_args = len(defaults), len(a.args)
        for i, arg in enumerate(a.args):
            default = defaults[i - (n_args - n_def)] if i >= n_args - n_def else None
            add(arg, default, "pos")
        if a.vararg:
            add(a.vararg, None, "vararg")
        for kw, d in zip(a.kwonlyargs, a.kw_defaults):
            add(kw, d, "kwonly")
        if a.kwarg:
            add(a.kwarg, None, "varkw")
        return params

    def firstline(doc: Optional[str]) -> Optional[str]:
        if not doc:
            return None
        for line in doc.strip().splitlines():
            t = line.strip()
            if t:
                return t
        return None

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast_unparse(b) for b in node.bases]
            is_enum = any((b or "").endswith("Enum") or (b == "Enum") or (b or "").endswith("enum.Enum") for b in bases)
            entry = {
                "name": node.name,
                "bases": bases,
                "summary": firstline(ast.get_docstring(node)),
                "methods": [],
            }
            for b in node.body:
                if isinstance(b, ast.FunctionDef):
                    entry["methods"].append({
                        "name": b.name,
                        "summary": firstline(ast.get_docstring(b)),
                        "returns": ast_unparse(b.returns),
                        "params": argspec(b.args),
                        "decorators": [ast_unparse(d) for d in b.decorator_list] if b.decorator_list else [],
                        "lineno": b.lineno,
                    })
            if is_enum:
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
                "summary": firstline(ast.get_docstring(node)),
                "returns": ast_unparse(node.returns),
                "params": argspec(node.args),
                "decorators": [ast_unparse(d) for d in node.decorator_list] if node.decorator_list else [],
                "lineno": node.lineno,
            })
    return spec

# -----------------------------
# Inventory and README helpers
# -----------------------------
def inventory_files() -> List[Dict[str, Any]]:
    globs = ["*.py", "*.md", "*.txt", "*.json", "requirements*.txt"]
    files: List[Path] = []
    for pat in globs:
        files += [p for p in sorted(REPO.glob(pat)) if not p.name.startswith(".")]
    tests_dir = REPO / "tests"
    if tests_dir.exists():
        for p in sorted(tests_dir.rglob("*")):
            if p.is_file():
                files.append(p)
    rows = []
    for p in files:
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        except Exception:
            mtime = ""
        role = ROLE_HINTS.get(p.name, "Script" if p.suffix == ".py" else "Asset")
        rows.append({"path": str(p.relative_to(REPO)), "role": role, "last_modified": mtime})
    return rows

def render_files_table(inv: List[Dict[str, Any]]) -> str:
    header = "| File | Role | Last modified (UTC) |\n|---|---|---|"
    lines = [header] + [f"| `{r['path']}` | {r['role']} | {r['last_modified']} |" for r in inv]
    return "\n".join(lines)

def upsert_region(text: str, start: str, end: str, body_md: str) -> str:
    block = f"{start}\n{body_md}\n{end}"
    if start in text and end in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), block, text, flags=re.DOTALL, count=1)
    return (text + ("\n" if not text.endswith("\n") else "")) + block + "\n"

def ensure_readme(inv: List[Dict[str, Any]], spec: Dict[str, Any]) -> None:
    if not README.exists():
        write_text(README, "# Poker Assistant\n\n")
    base = read_text(README)
    gm = git_meta()

    header_yaml = [
        HTML_START,
        YAML_OPEN,
        f"schema: {HEADER_SCHEMA}",
        f"project: {PROJECT}",
        "file: README.md",
        f"version: '{VERSION}'",
        f"last_commit: '{gm.get('last_commit') or ''}'",
        f"last_commit_hash: '{gm.get('last_commit_hash') or ''}'",
        f"branch: '{gm.get('branch') or ''}'",
        f"files_count: {len(inv)}",
        f"modules_hash: '{spec.get('hash') or ''}'",
        "fixes: ['readme_sync','modules_doc_generated','headers_enforced']",
        YAML_CLOSE,
        HTML_END,
    ]
    header_block = "\n".join(header_yaml)
    if HTML_START in base and HTML_END in base:
        base = re.sub(re.escape(HTML_START) + r".*?" + re.escape(HTML_END), header_block, base, flags=re.DOTALL, count=1)
    else:
        base = header_block + "\n\n" + base

    files_md = "## Files Included\n\n" + render_files_table(inv)
    base = upsert_region(base, FILES_START, FILES_END, files_md)

    json_str = json.dumps(spec, indent=2, ensure_ascii=False)
    mods_md = "## Machine-readable API for `poker_modules.py`\n\n```json\n" + json_str + "\n```\n\n_Regenerate with:_ `python3 Improvement4.py`"
    base = upsert_region(base, MODS_START, MODS_END, mods_md)

    write_text(README, base)

# -----------------------------
# Header stamping
# -----------------------------
def comment_style_for(p: Path) -> Optional[str]:
    ext = p.suffix.lower()
    if ext == ".py":
        return "py"
    if ext in (".md", ".txt"):
        return "html"
    return None

def build_header_map(file_rel: str, file_hash: str, gm: Dict[str, Optional[str]]) -> Dict[str, Any]:
    return {
        "schema": HEADER_SCHEMA,
        "project": PROJECT,
        "file": file_rel,
        "version": f"'{VERSION}'",
        "last_commit": f"'{gm.get('last_commit') or ''}'",
        "last_commit_hash": f"'{gm.get('last_commit_hash') or ''}'",
        "branch": f"'{gm.get('branch') or ''}'",
        "file_hash": f"'{file_hash}'",
        "generated_at": f"'{iso_now()}'",
        "python_min": "'3.9'",
        "fixes": "['headers_enforced']",
    }

def render_yaml_lines(kv: Dict[str, Any]) -> List[str]:
    lines = [YAML_OPEN]
    for k, v in kv.items():
        lines.append(f"{k}: {v}")
    lines.append(YAML_CLOSE)
    return lines

def stamp_header_content(style: str, kv: Dict[str, Any]) -> str:
    yaml_lines = render_yaml_lines(kv)
    if style == "py":
        lines = [PY_START] + [f"# {line}" for line in yaml_lines] + [PY_END]
        return "\n".join(lines)
    lines = [HTML_START] + yaml_lines + [HTML_END]
    return "\n".join(lines)

def split_shebang_encoding(text: str) -> Tuple[str, str]:
    lines = text.splitlines()
    prefix_lines = []
    i = 0
    while i < len(lines):
        L = lines[i]
        if i == 0 and L.startswith("#!"):
            prefix_lines.append(L); i += 1; continue
        if re.match(r"#\s*-\*-\s*coding:", L) or re.match(r"#\s*coding:", L):
            prefix_lines.append(L); i += 1; continue
        break
    prefix = "\n".join(prefix_lines)
    rest = "\n".join(lines[i:])
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    return prefix, rest

def header_regex_for(style: str) -> re.Pattern:
    if style == "py":
        return re.compile(re.escape(PY_START) + r".*?" + re.escape(PY_END), re.DOTALL)
    return re.compile(re.escape(HTML_START) + r".*?" + re.escape(HTML_END), re.DOTALL)

def stamp_file_header(p: Path, gm: Dict[str, Optional[str]]) -> bool:
    style = comment_style_for(p)
    if style is None:
        return False
    original = read_text(p)
    file_rel = str(p.relative_to(REPO)).replace("\\", "/")
    kv = build_header_map(file_rel, sha256_file(p), gm)
    header_block = stamp_header_content(style, kv)
    pattern = header_regex_for(style)
    changed = False
    if style == "py":
        prefix, rest = split_shebang_encoding(original)
        if pattern.search(rest):
            new_rest = pattern.sub(header_block, rest, count=1)
        else:
            glue = "" if not rest or rest.startswith("\n") else "\n\n"
            new_rest = header_block + glue + rest
        new_content = prefix + new_rest
        if new_content != original:
            write_text(p, new_content); changed = True
    else:
        if pattern.search(original):
            new_content = pattern.sub(header_block, original, count=1)
        else:
            new_content = header_block + "\n\n" + original
        if new_content != original:
            write_text(p, new_content); changed = True
    return changed

# -----------------------------
# README + docs + manifest
# -----------------------------
def ensure_version_file() -> None:
    write_text(VERSION_FILE, f"{VERSION}\n{iso_now()}\n")

def write_manifest(inv: List[Dict[str, Any]]) -> None:
    data = {
        "project": PROJECT,
        "version": VERSION,
        "generated_at": iso_now(),
        "files": [],
    }
    for r in inv:
        p = REPO / r["path"]
        file_hash = sha256_file(p) if p.exists() else ""
        data["files"].append({
            "path": r["path"],
            "role": r["role"],
            "hash": file_hash,
            "last_modified": r["last_modified"],
        })
    write_text(MANIFEST_JSON, json.dumps(data, indent=2))

# -----------------------------
# Unit tests (written as files)
# -----------------------------
def write_tests() -> None:
    # Build test files using joined lines to avoid nested triple quotes
    test_headers_lines = [
        "import re",
        "from pathlib import Path",
        "import unittest",
        "",
        "REPO = Path(__file__).resolve().parents[1]",
        'HTML_START = "<!-- POKERTOOL-HEADER-START"',
        'HTML_END = "POKERTOOL-HEADER-END -->"',
        'PY_START = "# POKERTOOL-HEADER-START"',
        'PY_END = "# POKERTOOL-HEADER-END"',
        'VERSION = "20"',
        "",
        "class TestPerFileHeaders(unittest.TestCase):",
        "    def _read(self, p: Path) -> str:",
        '        return p.read_text(encoding="utf-8", errors="replace")',
        "",
        "    def _has_header(self, text: str) -> bool:",
        "        return (HTML_START in text and HTML_END in text) or (PY_START in text and PY_END in text)",
        "",
        "    def _extract_yaml(self, text: str) -> str:",
        "        # Regex hits either HTML or Python header block",
        "        m = re.search(r'(<!--\\s*POKERTOOL-HEADER-START[\\s\\S]*?POKERTOOL-HEADER-END\\s*-->)|(#[\\s\\S]*?POKERTOOL-HEADER-START[\\s\\S]*?#\\s*POKERTOOL-HEADER-END)', text)",
        "        self.assertIsNotNone(m, 'Header block not found')",
        "        block = m.group(0)",
        "        yaml_lines = []",
        "        for line in block.splitlines():",
        "            s = line.strip()",
        "            if s.startswith('#'):",
        "                s = s[1:].strip()",
        "            if s.startswith('<!--') or s.endswith('-->'):",
        "                continue",
        "            yaml_lines.append(s)",
        "        inner = '\\n'.join(yaml_lines)",
        "        self.assertIn('schema: pokerheader.v1', inner)",
        "        self.assertIn(\"version: '20'\", inner)",
        "        return inner",
        "",
        "    def test_all_py_md_txt_have_headers(self):",
        "        targets = []",
        "        for ext in ('.py', '.md', '.txt'):",
        "            targets += list(REPO.glob(f'*{ext}'))",
        "        for p in targets:",
        "            if p.name.startswith('.'):",
        "                continue",
        "            if p.suffix == '.txt' and p.name == 'VERSION.txt':",
        "                continue",
        "            text = self._read(p)",
        "            self.assertTrue(self._has_header(text), f'Missing header in {p.name}')",
        "            self._extract_yaml(text)",
        "",
        "if __name__ == '__main__':",
        "    unittest.main()",
    ]
    write_text(TESTS / "test_headers.py", "\n".join(test_headers_lines))

    test_readme_lines = [
        "from pathlib import Path",
        "import unittest",
        "import re",
        "",
        "REPO = Path(__file__).resolve().parents[1]",
        "README = REPO / 'README.md'",
        'FILES_START = "<!-- AUTODOC:FILES-START -->"',
        'FILES_END = "<!-- AUTODOC:FILES-END -->"',
        'MODS_START = "<!-- AUTODOC:MODULES-START -->"',
        'MODS_END = "<!-- AUTODOC:MODULES-END -->"',
        "",
        "class TestReadmeAutodoc(unittest.TestCase):",
        "    def test_sections_present(self):",
        '        text = README.read_text(encoding="utf-8", errors="replace")',
        "        self.assertIn(FILES_START, text)",
        "        self.assertIn(FILES_END, text)",
        "        self.assertIn(MODS_START, text)",
        "        self.assertIn(MODS_END, text)",
        "        m = re.search(FILES_START + r'[\\s\\S]*?' + FILES_END, text)",
        "        self.assertIsNotNone(m)",
        "        self.assertIn('| File |', m.group(0))",
        "",
        "if __name__ == '__main__':",
        "    unittest.main()",
    ]
    write_text(TESTS / "test_readme_autodoc.py", "\n".join(test_readme_lines))

    test_schema_lines = [
        "from pathlib import Path",
        "import unittest",
        "import json",
        "",
        "REPO = Path(__file__).resolve().parents[1]",
        "SCHEMA = REPO / 'docs' / 'poker_modules.schema.json'",
        "MANIFEST = REPO / 'docs' / 'manifest.json'",
        "",
        "class TestSchemaAndManifest(unittest.TestCase):",
        "    def test_schema_exists_and_valid(self):",
        "        self.assertTrue(SCHEMA.exists(), 'poker_modules.schema.json missing')",
        "        data = json.loads(SCHEMA.read_text(encoding='utf-8'))",
        "        self.assertEqual(data.get('schema'), 'pokermodules.v1')",
        "        self.assertIn('functions', data)",
        "        self.assertIn('classes', data)",
        "        self.assertIn('enums', data)",
        "",
        "    def test_manifest_exists_and_valid(self):",
        "        self.assertTrue(MANIFEST.exists(), 'manifest.json missing')",
        "        data = json.loads(MANIFEST.read_text(encoding='utf-8'))",
        "        self.assertEqual(data.get('project'), 'pokertool')",
        "        self.assertEqual(data.get('version'), '20')",
        "        self.assertIsInstance(data.get('files'), list)",
        "",
        "if __name__ == '__main__':",
        "    unittest.main()",
    ]
    write_text(TESTS / "test_schema_and_manifest.py", "\n".join(test_schema_lines))

# -----------------------------
# Main
# -----------------------------
def main() -> int:
    ensure_dir(DOCS)
    ensure_dir(TESTS)

    targets: List[Path] = []
    for ext in (".py", ".md", ".txt"):
        targets += [p for p in REPO.glob(f"*{ext}") if not p.name.startswith(".")]
    backup(targets)

    spec = parse_poker_modules()
    write_text(SCHEMA_JSON, json.dumps(spec, indent=2, ensure_ascii=False))

    inv = inventory_files()
    ensure_readme(inv, spec)
    write_text(VERSION_FILE, f"{VERSION}\n{iso_now()}\n")
    write_manifest(inv)

    gm = git_meta()
    changed_any = False
    for p in targets:
        if p.suffix == ".txt" and p.name == "VERSION.txt":
            continue
        changed_any |= stamp_file_header(p, gm)

    if changed_any:
        inv = inventory_files()
        write_manifest(inv)

    write_tests()

    print("Headers enforced.")
    print("README synced.")
    print(f"Wrote: {SCHEMA_JSON}")
    print(f"Wrote: {MANIFEST_JSON}")
    print("Unit tests under ./tests")
    print("Run: python -m unittest")
    return 0

if __name__ == "__main__":
    sys.exit(main())
