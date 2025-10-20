# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tools/saniitise_python_files.py
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
__version__ = '20'

import sys
import pathlib

ZERO_WIDTH = {
    ord("\ufeff"): None,  # BOM
    ord("\u200b"): None,  # ZWSP
    ord("\u200c"): None,  # ZWNJ
    ord("\u200d"): None,  # ZWJ
    ord("\u2060"): None,  # WJ
    ord("\u00a0"): ' ',   # NBSP -> space
}
SMART_QUOTES = str.maketrans({""": '"', """: '"', "'": "'", "'": "'"})

def clean_text(s: str) -> str:
    """Clean text by removing zero-width characters and normalizing quotes."""
    s = s.translate(ZERO_WIDTH).translate(SMART_QUOTES)
    s = s.replace("\r\n", '\n').replace('\r', '\n')
    return s

def has_merge_markers(s: str) -> bool:
    """Check if text contains Git merge conflict markers."""
    return any(m in s for m in ('<<<<<<<', '=======', '>>>>>>>'))

def main():
    """Main function to sanitize Python files."""
    root = pathlib.Path('.')
    targets = [p for p in root.rglob('*.py') if not any(v in p.parts for v in ('.venv', 'venv', '__pycache__'))]

    errors = []
    for p in targets:
        raw = p.read_bytes()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            text = raw.decode('latin1')
        
        cleaned = clean_text(text)

        if cleaned != text:
            bak = p.with_suffix(p.suffix + '.bak')
            bak.write_text(text, encoding='utf-8')
            p.write_text(cleaned, encoding='utf-8', newline="\n")

        try:
            compile(cleaned, str(p), 'exec')
        except SyntaxError as e:
            errors.append((p, e))
            line = cleaned.splitlines()[e.lineno - 1] if e.lineno else ''
            print(f'SyntaxError: {p}: {e.lineno}: {e.offset} {e.msg}')
            print(f'>>> {line}')
            if e.lineno == 1 and has_merge_markers(cleaned[:2000]):
                print("Note: merge-conflict markers detected near file start.")

    if errors:
        print("\nBackups written as *.py.bak")
        sys.exit(1)
    else:
        print("All Python files are clean.")
        sys.exit(0)

if __name__ == '__main__':
    main()
