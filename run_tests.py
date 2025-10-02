#!/usr/bin/env python3
"""Convenience entry point to execute the project's Python test suites."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEST_DIR = ROOT / "tests"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PokerTool test suites via pytest")
    parser.add_argument(
        "--watch", action="store_true", help="Continuously re-run tests when files change (requires pytest-watch)"
    )
    parser.add_argument(
        "--tests",
        nargs="*",
        default=[],
        help="Optional pytest node ids or file paths to run (defaults to the full test suite)",
    )
    return parser.parse_args(argv)


def build_command(args: argparse.Namespace) -> list[str]:
    command = [sys.executable, "-m", "pytest", "-m"]

    if args.tests:
        command.extend(args.tests)
    else:
        command.append(str(TEST_DIR))

    if args.watch:
        command.insert(2, "pytest_watch")
        command.insert(2, "-m")

    return command


def ensure_environment() -> None:
    pythonpath = os.environ.get("PYTHONPATH", "")
    paths = [str(ROOT), str(ROOT / "src")]
    for path in paths:
        if path not in pythonpath:
            pythonpath = f"{path}{os.pathsep}{pythonpath}" if pythonpath else path
    os.environ["PYTHONPATH"] = pythonpath


def main(argv: list[str] | None = None) -> int:
    ensure_environment()
    args = parse_args(argv)
    command = build_command(args)

    try:
        result = subprocess.run(command, cwd=ROOT)
    except FileNotFoundError as exc:
        print("Failed to execute pytest. Is it installed?", exc, file=sys.stderr)
        return 1
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
