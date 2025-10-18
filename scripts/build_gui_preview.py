#!/usr/bin/env python3
"""Build the enhanced GUI preview binary using PyInstaller."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = REPO_ROOT / "packaging" / "pyinstaller" / "pokertool_gui.spec"
DIST_DIR = REPO_ROOT / "dist" / "PokerToolGUI"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


def run_pyinstaller() -> None:
    """Invoke PyInstaller with the project spec file."""
    if not SPEC_FILE.exists():
        raise FileNotFoundError(f"PyInstaller spec not found: {SPEC_FILE}")

    subprocess.run(
        ["pyinstaller", "--noconfirm", str(SPEC_FILE)],
        check=True,
        cwd=REPO_ROOT,
    )


def archive_output() -> Path:
    """Compress the PyInstaller dist output for distribution."""
    if not DIST_DIR.exists():
        raise FileNotFoundError(f"Expected PyInstaller output missing: {DIST_DIR}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARTIFACTS_DIR / "pokertool-gui-preview"
    archive_file = shutil.make_archive(str(archive_path), "zip", DIST_DIR)
    return Path(archive_file)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Build PokerTool GUI preview package.")
    parser.add_argument(
        "--archive/--no-archive",
        dest="archive",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Whether to create a zipped artifact (default: true).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip the PyInstaller build step and only (optionally) archive existing output.",
    )
    return parser.parse_args()


def main() -> int:
    """Build and archive the GUI preview binary."""
    args = parse_args()
    if not args.skip_build:
        run_pyinstaller()
    if args.archive:
        archive_path = archive_output()
        print(f"GUI preview archive created at: {archive_path}")
    else:
        print("Archive step skipped; dist/ output left in place.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI helper
    raise SystemExit(main())
