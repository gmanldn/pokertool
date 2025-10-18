# -*- coding: utf-8 -*-
"""PyInstaller-friendly entrypoint for the enhanced PokerTool GUI."""

from __future__ import annotations

from pokertool.cli import main as cli_main


def run() -> int:
    """Launch the enhanced GUI via the CLI."""
    return cli_main(['gui'])


if __name__ == '__main__':
    raise SystemExit(run())
