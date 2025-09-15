#!/usr/bin/env python3
"""
code_scan.py — strict syntax scanner & auto-fixer for Python repos (enhanced).

Features
--------
- Recursively scans *.py (skips common junk dirs, configurable)
- Strict checks: ast.parse and py_compile
- Multi-pass, in-place auto-fixes with timestamped backups
- Fixers:
  * Move `from __future__` imports to legal top
  * Insert `pass` for empty blocks (def/class/if/elif/else/for/while/try/except/finally/with)
  * Ensure 'try:' has at least one 'except' or 'finally' (auto-insert `except Exception: pass`)
  * Strip REPL prompts (>>> / ... )
  * Normalize invisibles/BOM; normalize CRLF; expand tabs->spaces; trim trailing whitespace
  * Trim excess closing brackets at EOL: ')', ']', '}'
  * Remove dangling '\' at EOF; ensure newline at EOF
  * Aggressive:
      - Close unterminated triple-quoted strings at EOF
      - Repair a single-line unterminated ' or " string at the SyntaxError line
  * AST Enum transformer:
      - Detect Enum classes where __init__ assigns self.value and other attributes
      - Replace with __new__ setting obj._value_ and same attributes
      - Remove fragile __init__; optionally add @property def val(self): return self.value

Usage
-----
  python3 code_scan.py                   # fix in place, backups enabled
  python3 code_scan.py --dry-run         # no writes, show intent
  python3 code_scan.py --aggressive      # enable extra risky-but-helpful fixes
  python3 code_scan.py --max-passes 5    # more passes per file
  python3 code_scan.py --include-hidden  # include dotfiles/dirs
  python3 code_scan.py --root path/to/repo

Exit codes
----------
  0 = all files compile after fixes
  1 = at least one file still fails after all passes
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys
import time
import py_compile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set

DEFAULT_EXCLUDES = {
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "build", "dist", "node_modules",
}

TRIPLE_DQ = '"""'
TRIPLE_SQ = "'''"

# -------------------- I/O helpers --------------------

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text_with_backup(p: Path, txt: str, *, dry_run: bool) -> None:
    if dry_run:
        return
    ts = time.strftime("%Y%m%d%H%M%S")
    bak = p.with_suffix(p.suffix + f".bak_{ts}")
    try:
        bak.write_text(read_text(p), encoding="utf-8")
    except FileNotFoundError:
        pass
    p.write_text(txt, encoding="utf-8")

def ast_ok(src: str, filename: str) -> Tuple[bool, str, Optional[int]]:
    try:
        ast.parse(src, filename=filename)
        return True, "", None
    except SyntaxError as e:
        return False, f"{e.msg}", e.lineno
    except Exception as e:
        return False, f"ParseError: {e}", None

def py_compile_ok(path: Path) -> Tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, f"{e.msg.strip()}"
    except Exception as e:
        return False, f"CompileError: {e}"

# -------------------- normalizations --------------------

def normalize_line_endings(txt: str) -> Tuple[str, bool]:
    new = txt.replace("\r\n", "\n").replace("\r", "\n")
    return new, new != txt

def expand_tabs(txt: str, spaces: int = 4) -> Tuple[str, bool]:
    new = txt.expandtabs(spaces)
    return new, new != txt

def strip_trailing_whitespace(txt: str) -> Tuple[str, bool]:
    lines = txt.splitlines(keepends=True)
    new_lines = [re.sub(r"[ \t]+(\r?\n)$", r"\1", ln) for ln in lines]
    new = "".join(new_lines)
    return new, new != txt

def ensure_newline_eof(txt: str) -> Tuple[str, bool]:
    return (txt if txt.endswith("\n") else txt + "\n", not txt.endswith("\n"))

def normalize_invisibles(txt: str) -> Tuple[str, int]:
    before = txt
    txt = txt.replace("\u00A0", " ")   # NBSP -> space
    txt = txt.replace("\u200B", "")    # ZWSP
    txt = txt.replace("\u200C", "")    # ZWNJ
    txt = txt.replace("\u200D", "")    # ZWJ
    txt = txt.replace("\ufeff", "")    # BOM
    return txt, int(txt != before)

# -------------------- textual fixers --------------------

FUTURE_RE = re.compile(r"^from\s+__future__\s+import\s+.+$", re.M)
SHEBANG_RE = re.compile(r'^#!')
ENCODING_RE = re.compile(r'coding[:=]\s*([-\w.]+)')

def reposition_future_imports(txt: str) -> Tuple[str, bool]:
    if not FUTURE_RE.search(txt):
        return txt, False

    lines = txt.splitlines(keepends=True)
    insert_at = 0
    if lines and SHEBANG_RE.match(lines[0]):
        insert_at = 1
    if insert_at < len(lines) and ENCODING_RE.search(lines[insert_at]):
        insert_at += 1

    def is_triple(s: str) -> bool:
        s = s.strip()
        return s.startswith(TRIPLE_DQ) or s.startswith(TRIPLE_SQ)

    if insert_at < len(lines) and is_triple(lines[insert_at]):
        q = lines[insert_at].strip()[:3]
        j = insert_at + 1
        while j < len(lines):
            if lines[j].strip().endswith(q):
                insert_at = j + 1
                break
            j += 1

    futures, rest = [], []
    for ln in lines:
        if FUTURE_RE.match(ln):
            futures.append(ln)
        else:
            rest.append(ln)

    out = rest[:insert_at] + futures
    if insert_at < len(rest) and rest[insert_at].strip():
        out += ["\n"]
    out += rest[insert_at:]
    new = "".join(out)
    return new, new != txt

COLON_BLOCK_RE = re.compile(
    r'^(\s*)(def|class|if|elif|else|for|while|try|except|finally|with)\b[^#\n]*:\s*(#.*)?$'
)

def insert_pass_for_empty_blocks(txt: str) -> Tuple[str, int]:
    lines = txt.splitlines(keepends=True)
    added = 0
    i = 0
    while i < len(lines):
        m = COLON_BLOCK_RE.match(lines[i])
        if m:
            indent = m.group(1)
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].lstrip().startswith("#")):
                j += 1
            if j >= len(lines):
                lines.insert(i + 1, indent + "    pass\n"); added += 1; i += 1
            else:
                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_indent <= len(indent):
                    lines.insert(i + 1, indent + "    pass\n"); added += 1; i += 1
        i += 1
    return "".join(lines), added

REPL_PROMPT_RE = re.compile(r'^\s*(>>>|\.\.\.)\s')

def strip_repl_prompts(txt: str) -> Tuple[str, int]:
    out, removed = [], 0
    for ln in txt.splitlines(keepends=True):
        if REPL_PROMPT_RE.match(ln):
            removed += 1
            continue
        out.append(ln)
    return "".join(out), removed

def trim_excess_closing_brackets(txt: str) -> Tuple[str, int]:
    """
    If a line ends with an unmatched closing bracket, trim one at a time.
    Handles ')', ']', '}' at EOL.
    """
    lines = txt.splitlines(keepends=True)
    fixed = 0
    for idx, ln in enumerate(lines):
        if ln.strip().startswith("#"):
            continue
        s = ln.rstrip("\n")
        changed = False
        for ch_open, ch_close in (("(", ")"), ("[", "]"), ("{", "}")):
            if s.endswith(ch_close):
                if s.count(ch_close) > s.count(ch_open):
                    s = s[:-1]
                    fixed += 1
                    changed = True
        if changed:
            lines[idx] = s + "\n"
    return "".join(lines), fixed

def fix_eof_backslash(txt: str) -> Tuple[str, bool]:
    lines = txt.splitlines(keepends=True)
    for i in range(len(lines)-1, -1, -1):
        if lines[i].strip():
            if lines[i].rstrip().endswith("\\"):
                lines[i] = lines[i].rstrip().rstrip("\\") + "\n"
                return "".join(lines), True
            break
    return txt, False

def ensure_try_has_handler(txt: str) -> Tuple[str, int]:
    """
    Ensure that each 'try:' suite is followed by at least one handler ('except'/'finally').
    If not, insert 'except Exception: pass' immediately after the suite.
    Heuristic using indentation scanning.
    """
    lines = txt.splitlines(keepends=True)
    inserted = 0
    i = 0
    while i < len(lines):
        m = re.match(r'^(\s*)try\s*:\s*(#.*)?$', lines[i])
        if not m:
            i += 1
            continue
        base_indent = len(m.group(1))
        # find end of try suite
        j = i + 1
        # at least one indented line belongs to suite (after earlier 'insert_pass', there is)
        while j < len(lines):
            l = lines[j]
            if not l.strip() or l.lstrip().startswith("#"):
                j += 1; continue
            cur_indent = len(l) - len(l.lstrip(" "))
            if cur_indent <= base_indent:
                # suite ended; check if handler starts here
                if not re.match(r'^\s*(except\b|finally\b|else\b)', l):
                    # insert handler before this line
                    ins = " " * base_indent + "except Exception:\n" + " " * (base_indent + 4) + "pass\n"
                    lines.insert(j, ins)
                    inserted += 1
                    i = j + 1
                else:
                    i = j
                break
            j += 1
        else:
            # EOF reached; add handler at EOF
            ins = " " * base_indent + "except Exception:\n" + " " * (base_indent + 4) + "pass\n"
            lines.append(ins)
            inserted += 1
            i = len(lines)
    return "".join(lines), inserted

def close_unterminated_triple_quotes(txt: str) -> Tuple[str, int]:
    added = 0
    if txt.count(TRIPLE_DQ) % 2 == 1:
        txt += TRIPLE_DQ + "  # auto-closed\n"; added += 1
    if txt.count(TRIPLE_SQ) % 2 == 1:
        txt += TRIPLE_SQ + "  # auto-closed\n"; added += 1
    return txt, added

def try_fix_unterminated_simple_string(txt: str, err_line: Optional[int]) -> Tuple[str, bool]:
    """
    Aggressive healer: if ast reports "unterminated string literal" or "EOL while scanning string literal",
    attempt to close the string at the error line by appending the same quote char.
    """
    if not err_line:
        return txt, False
    lines = txt.splitlines(keepends=True)
    if err_line - 1 < 0 or err_line - 1 >= len(lines):
        return txt, False
    ln = lines[err_line - 1]
    # Heuristic: find last quote char in line; if odd count from there, append it at EOL
    for q in ("'", '"'):
        # ignore triple quotes; they're handled elsewhere
        if ln.count(q) % 2 == 1 and ln.count(q*3) == 0:
            lines[err_line - 1] = ln.rstrip("\n") + q + "\n"
            return "".join(lines), True
    return txt, False

# -------------------- AST Enum transformer --------------------

class EnumRewriter(ast.NodeTransformer):
    """
    Transform Enum classes that assign `self.value = value` in __init__
    into a __new__ that sets `_value_` and preserves other attributes.
    Also injects a `val` property if not present.
    Only triggers on simple `self.<attr> = <param>` assignments.
    """
    def __init__(self) -> None:
        super().__init__()
        self.transformed_classes: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        is_enum = False
        for b in node.bases:
            if isinstance(b, ast.Name) and b.id in {"Enum", "IntEnum", "StrEnum"}:
                is_enum = True
            elif isinstance(b, ast.Attribute) and getattr(b, "attr", "") in {"Enum", "IntEnum", "StrEnum"}:
                is_enum = True
        if not is_enum:
            return self.generic_visit(node)

        # find __init__
        init_idx = None
        init_fn: Optional[ast.FunctionDef] = None
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                init_idx = i
                init_fn = stmt
                break
        if init_fn is None:
            return self.generic_visit(node)

        # parse assignments self.<attr> = <param>
        param_names = [arg.arg for arg in init_fn.args.args][1:]  # skip self
        allowed_rhs = set(param_names)
        mapping: Dict[str, str] = {}  # attr_name -> param_name
        ok = True
        for st in init_fn.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Attribute):
                target = st.targets[0]
                if not (isinstance(target.value, ast.Name) and target.value.id == "self"):
                    ok = False; break
                attr = target.attr
                # RHS must be a Name and one of params
                if isinstance(st.value, ast.Name) and st.value.id in allowed_rhs:
                    mapping[attr] = st.value.id
                else:
                    ok = False; break
            elif isinstance(st, ast.Pass):
                continue
            else:
                # Non-trivial code in __init__; bail out
                ok = False; break
        if not ok:
            return self.generic_visit(node)
        if "value" not in mapping:
            return self.generic_visit(node)

        # Build __new__(cls, <params>) with _value_ and other attrs
        cls_args = [ast.arg(arg="cls")]
        for p in param_names:
            cls_args.append(ast.arg(arg=p))
        new_fn = ast.FunctionDef(
            name="__new__",
            args=ast.arguments(
                posonlyargs=[],
                args=cls_args,
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=[],
            decorator_list=[],
            returns=None,
            type_comment=None,
        )
        # obj = object.__new__(cls)
        new_body: List[ast.stmt] = [
            ast.Assign(
                targets=[ast.Name(id="obj", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id="object", ctx=ast.Load()), attr="__new__", ctx=ast.Load()),
                    args=[ast.Name(id="cls", ctx=ast.Load())],
                    keywords=[],
                ),
            ),
            # obj._value_ = <value_param>
            ast.Assign(
                targets=[ast.Attribute(value=ast.Name(id="obj", ctx=ast.Load()), attr="_value_", ctx=ast.Store())],
                value=ast.Name(id=mapping["value"], ctx=ast.Load()),
            ),
        ]
        # for other attrs: obj.<attr> = <param>
        for attr, param in mapping.items():
            if attr == "value":
                continue
            new_body.append(
                ast.Assign(
                    targets=[ast.Attribute(value=ast.Name(id="obj", ctx=ast.Load()), attr=attr, ctx=ast.Store())],
                    value=ast.Name(id=param, ctx=ast.Load()),
                )
            )
        # return obj
        new_body.append(ast.Return(value=ast.Name(id="obj", ctx=ast.Load())))
        new_fn.body = new_body

        # Remove __init__, insert __new__ at top of methods
        new_body_list: List[ast.stmt] = []
        for i, stmt in enumerate(node.body):
            if i == init_idx:
                continue
            new_body_list.append(stmt)
        # try place __new__ early (after possible docstring/assigns)
        insertion_index = 0
        if new_body_list and isinstance(new_body_list[0], ast.Expr) and isinstance(getattr(new_body_list[0], "value", None), ast.Constant) and isinstance(new_body_list[0].value.value, str):
            insertion_index = 1
        new_body_list.insert(insertion_index, new_fn)

        # Add @property val if not present
        has_val_property = any(
            isinstance(st, ast.FunctionDef) and st.name == "val" and any(
                isinstance(dec, ast.Name) and dec.id == "property" for dec in st.decorator_list
            )
            for st in new_body_list
        )
        if not has_val_property:
            val_fn = ast.FunctionDef(
                name="val",
                args=ast.arguments(posonlyargs=[], args=[ast.arg(arg="self")], vararg=None,
                                   kwonlyargs=[], kw_defaults=[], defaults=[]),
                body=[ast.Return(value=ast.Attribute(value=ast.Name(id="self", ctx=ast.Load()), attr="value", ctx=ast.Load()))],
                decorator_list=[ast.Name(id="property", ctx=ast.Load())],
                returns=None,
                type_comment=None,
            )
            new_body_list.append(val_fn)

        node.body = new_body_list
        self.transformed_classes.add(node.name)
        return node

def transform_enums_via_ast(txt: str) -> Tuple[str, int]:
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        return txt, 0
    rewriter = EnumRewriter()
    new_tree = rewriter.visit(tree)
    ast.fix_missing_locations(new_tree)
    if not rewriter.transformed_classes:
        return txt, 0
    new_src = ast.unparse(new_tree)
    return new_src + ("\n" if not new_src.endswith("\n") else ""), len(rewriter.transformed_classes)

# -------------------- scanning & fixing loop --------------------

def find_python_files(root: Path, include_hidden: bool, extra_excludes: set[str]) -> List[Path]:
    found: List[Path] = []
    excludes = set(DEFAULT_EXCLUDES) | extra_excludes
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        # prune dirs
        for d in list(dirnames):
            if d in excludes or (not include_hidden and d.startswith(".")):
                dirnames.remove(d)
        for fn in filenames:
            if fn.endswith(".py") and (include_hidden or not fn.startswith(".")):
                found.append(dp / fn)
    return found

def attempt_textual_fixes(src: str, *, aggressive: bool) -> Tuple[str, List[str]]:
    changes: List[str] = []
    src0 = src

    # Normalizations
    src, c = normalize_line_endings(src);             changes += ["normalize_line_endings"] if c else []
    src, c = expand_tabs(src);                        changes += ["expand_tabs"] if c else []
    src, c = strip_trailing_whitespace(src);          changes += ["strip_trailing_whitespace"] if c else []
    src, c = normalize_invisibles(src);               changes += ["normalize_invisibles"] if c else []
    src, c = ensure_newline_eof(src);                 changes += ["ensure_newline_eof"] if c else []

    # Structural textual fixes
    src, moved = reposition_future_imports(src);      changes += ["reposition_future_imports"] if moved else []
    src, rem = strip_repl_prompts(src);               changes += [f"strip_repl_prompts(-{rem})"] if rem else []
    src, added = insert_pass_for_empty_blocks(src);   changes += [f"insert_pass_for_empty_blocks(+{added})"] if added else []
    src, ins = ensure_try_has_handler(src);           changes += [f"ensure_try_has_handler(+{ins})"] if ins else []
    src, fixed = trim_excess_closing_brackets(src);   changes += [f"trim_excess_closing_brackets(-{fixed})"] if fixed else []
    src, removed = fix_eof_backslash(src);            changes += ["fix_eof_backslash"] if removed else []

    # Aggressive triple-quote closer
    if aggressive:
        src, q = close_unterminated_triple_quotes(src); changes += [f"close_unterminated_triple_quotes(+{q})"] if q else []

    return src, changes if src != src0 else []

def process_file(path: Path, *, dry_run: bool, aggressive: bool, max_passes: int) -> Tuple[bool, List[str]]:
    """
    Returns (final_success, log_lines).
    """
    log: List[str] = []
    original = read_text(path)

    # First pass checks
    ok_ast, msg_ast, err_line = ast_ok(original, str(path))
    ok_comp, msg_comp = (py_compile_ok(path) if ok_ast else (False, "Skipped compile due to AST error"))

    if ok_ast and ok_comp:
        log.append("OK (no change)")
        return True, log

    current = original
    for passno in range(1, max_passes + 1):
        pass_changes: List[str] = []

        # Textual healers first
        current, changes = attempt_textual_fixes(current, aggressive=aggressive)
        pass_changes += changes

        # Try parsing now
        ok_ast, msg_ast, err_line = ast_ok(current, str(path))
        if not ok_ast:
            # if unterminated simple string and aggressive: try closing on the error line
            if aggressive and ("unterminated string literal" in msg_ast.lower() or "eol while scanning string literal" in msg_ast.lower()):
                current, closed = try_fix_unterminated_simple_string(current, err_line)
                if closed:
                    pass_changes.append(f"close_unterminated_simple_quote@{err_line}")
                    ok_ast, msg_ast, err_line = ast_ok(current, str(path))

        # If AST OK, try Enum transform
        if ok_ast:
            transformed = 0
            new_src, tcount = transform_enums_via_ast(current)
            if tcount:
                transformed += tcount
                current = new_src
                pass_changes.append(f"enum_transform(+{tcount})")
                ok_ast, msg_ast, err_line = ast_ok(current, str(path))

        if ok_ast:
            pass_changes.append("ast: OK")
            # write to disk now to allow py_compile to run on the real file
            write_text_with_backup(path, current, dry_run=dry_run)
            ok_comp, msg_comp = py_compile_ok(path)
            if ok_comp:
                pass_changes.append("compile: OK")
                log.append(f"pass {passno}: " + ", ".join(pass_changes))
                break
            else:
                pass_changes.append(f"compile: {msg_comp}")

        else:
            pass_changes.append(f"ast: {msg_ast}")

        log.append(f"pass {passno}: " + (", ".join(pass_changes) if pass_changes else "no changes"))

    # If not compiled yet but content changed, ensure we wrote last attempt
    if read_text(path) != current and not dry_run:
        write_text_with_backup(path, current, dry_run=False)

    # Final status
    final_src = read_text(path)
    ok_ast, msg_ast, _ = ast_ok(final_src, str(path))
    if not ok_ast:
        log.append(f"FINAL ast: {msg_ast}")
        return False, log
    ok_comp, msg_comp = py_compile_ok(path)
    if not ok_comp:
        log.append(f"FINAL compile: {msg_comp}")
        return False, log

    log.append("FINAL: OK")
    return True, log

# -------------------- main --------------------

def find_python_files(root: Path, include_hidden: bool, extra_excludes: set[str]) -> List[Path]:
    found: List[Path] = []
    excludes = set(DEFAULT_EXCLUDES) | extra_excludes
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        # prune dirs
        for d in list(dirnames):
            if d in excludes or (not include_hidden and d.startswith(".")):
                dirnames.remove(d)
        for fn in filenames:
            if fn.endswith(".py") and (include_hidden or not fn.startswith(".")):
                found.append(dp / fn)
    return found

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Root directory to scan (default: current dir)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; show intended changes only")
    ap.add_argument("--include-hidden", action="store_true", help="Include hidden files/dirs")
    ap.add_argument("--exclude", action="append", default=[], help="Extra dir names to exclude (repeatable)")
    ap.add_argument("--max-passes", type=int, default=4, help="Max fix passes per file (default: 4)")
    ap.add_argument("--aggressive", action="store_true", help="Enable risky-but-helpful fixes (triple/simple quote closers)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    files = find_python_files(root, include_hidden=args.include_hidden, extra_excludes=set(args.exclude))
    if not files:
        print("No Python files found.")
        return 0

    print(f"Scanning {len(files)} Python files under {root} ...")
    any_fail = False
    for p in sorted(files):
        rel = p.relative_to(root)
        success, logs = process_file(p, dry_run=args.dry_run, aggressive=args.aggressive, max_passes=args.max_passes)
        status = "OK" if success else "FAIL"
        print(f"\n[{status}] {rel}")
        for line in logs:
            print("  -", line)
        if not success:
            any_fail = True

    print("\nSummary:", "ALL OK ✅" if not any_fail else "Some files still failing ❌")
    return 0 if not any_fail else 1

if __name__ == "__main__":
    sys.exit(main())
