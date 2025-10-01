"""Module entry point so `python -m pokertool` dispatches to the CLI."""

from __future__ import annotations

from .cli import main


if __name__ == '__main__':  # pragma: no cover - thin wrapper
    raise SystemExit(main())
