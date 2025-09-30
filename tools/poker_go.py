# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: tools/poker_go.py
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
from __future__ import annotations
from typing import Sequence
import atexit

from start import main as start_main, cleanup as start_cleanup


def main(argv: Sequence[str] | None = None) -> int:
    """Legacy wrapper that now delegates to start.py."""
    atexit.register(start_cleanup)
    return start_main(argv)


if __name__ == '__main__':
    raise SystemExit(main())
