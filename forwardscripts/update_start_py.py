#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: forwardscripts/update_start_py.py
# version: v30.0.0
# last_commit: '2025-10-03T00:00:00+00:00'
# fixes:
# - date: '2025-10-03'
#   summary: Update start.py launch logic to avoid -m pokertool call
# ---
# POKERTOOL-HEADER-END

"""
Apply the October 3 start.py update.

This script extracts the accompanying ``oct03_start_update.tar.gz`` archive
located in the same ``forwardscripts`` directory and overwrites the
repository’s ``start.py`` with the updated version.  The modified
``start.py`` improves launch reliability by removing the problematic
``python -m pokertool`` invocation and instead invoking
``pokertool.cli`` directly.  Run this script from the project root
after copying both the script and the archive into your
``forwardscripts`` folder.

Usage::

    python update_start_py.py

On success, the script reports that the update has been applied.  In
case of failure, an error message is printed and the process exits
with a non‑zero status.
"""

from __future__ import annotations

import tarfile
import sys
from pathlib import Path


def main() -> None:
    # Determine the base directory (parent of forwardscripts)
    script_path = Path(__file__).resolve()
    base_dir = script_path.parents[1]
    tar_path = base_dir / "forwardscripts" / "oct03_start_update.tar.gz"
    if not tar_path.exists():
        print(f"⚠️  Update archive not found: {tar_path}")
        sys.exit(1)
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(base_dir)
        print(
            "✅ start.py update applied successfully.\n"
            "   Updated files have been extracted to the repository root."
        )
    except Exception as exc:
        print(f"❌ Failed to apply updates: {exc}")
        sys.exit(1)


if __name__ == '__main__':
    main()