from __future__ import annotations
"""
Legacy launcher kept for compatibility. Prefer: `pokertool` or `pokertool gui`.
"""
from pokertool.cli import main as _cli_main  # type: ignore

def main() -> int:
    return _cli_main(["gui"])

if __name__ == "__main__":
    raise SystemExit(main())
