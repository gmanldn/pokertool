# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tools/poker_main.py
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
from __future__ import annotations

"""
Legacy launcher kept for compatibility. Prefer: `pokertool` or `pokertool gui`.
"""
from pokertool.cli import main as _cli_main  # type: ignore

def main() -> int:
    """Launch the GUI via the legacy CLI shim to preserve backwards compatibility."""
    return _cli_main(["gui"])

if __name__ == '__main__':
    raise SystemExit(main())
