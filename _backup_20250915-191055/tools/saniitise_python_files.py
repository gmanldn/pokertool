#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: saniitise_python_files.py
# version: '20'
# last_updated_utc: '2025-09-15T02:05:50.037678+00:00'
# applied_improvements: [Improvement1.py]
# summary: Sanitize Python files
# ---
# POKERTOOL-HEADER-END
__version__ = "20"


import sys, pathlib

ZERO_WIDTH = {
    ord("\ufeff"): None,  # BOM
    ord("\u200b"): None,  # ZWSP
    ord("\u200c"): None,  # ZWNJ
    ord("\u200d"): None,  # ZWJ
    ord("\u2060"): None,  # WJ
    ord("\u00a0"): " ",   # NBSP -> space
}
SMART_QUOTES = str.maketrans({""": '"', """: '"', "'": "'", "'": "'"})

def clean_text(s: str) -> str:
    s = s.translate(ZERO_WIDTH).translate(SMART_QUOTES)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s

def has_merge_markers(s: str) -> bool:
    return any(m in s for m in ("<<<<<<<", "=======", ">>>>>>>"))

root = pathlib.Path(".")
targets = [p for p in root.rglob("*.py") if not any(v in p.parts for v in (".venv", "venv", "__pycache__"))]

errors = []
for p in targets:
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin1")
    cleaned = clean_text(text)

    if cleaned != text:
        bak = p.with_suffix(p.suffix + ".bak")
        bak.write_text(text, encoding="utf-8")
        p.write_text(cleaned, encoding="utf-8", newline="\n")

    try:
        compile(cleaned, str(p), "exec")
    except SyntaxError as e:
        errors.append((p, e))
        line = cleaned.splitlines()[e.lineno - 1] if e.lineno else ""
        print(f"SyntaxError: {p}:{e.lineno}:{e.offset} {e.msg}")
        print(f">>> {line}")
        if e.lineno == 1 and has_merge_markers(cleaned[:2000]):
            print("Note: merge-conflict markers detected near file start.")

print("\nBackups written as *.py.bak")
sys.exit(1 if errors else 0)
