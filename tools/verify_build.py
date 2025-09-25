# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tools/verify_build.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
from __future__ import annotations
import compileall, pathlib, sys

def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    src = root / "src"
    ok = compileall.compile_dir(str(src), quiet=1, force=False)
    print("verify_build: OK" if ok else "verify_build: FAIL", file=sys.stderr if not ok else sys.stdout)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
