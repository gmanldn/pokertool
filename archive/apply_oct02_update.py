#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: apply_oct02_update.py
# version: v30.0.0
# last_commit: '2025-10-02T00:00:00+00:00'
# fixes:
# - date: '2025-10-02'
#   summary: Apply October 2 updates including Betfair detection improvements and Table View enhancements
# ---
# POKERTOOL-HEADER-END
"""
Apply the October 2 updates for PokerTool.

This script extracts an accompanying tar archive containing updated
modules (screen scraper enhancements, GUI changes, translations) and
overwrites the corresponding files in your local repository.  The
archive `oct02_update_files.tar.gz` must be located in the same
`forwardscripts` directory as this script.  After running this
script, review the changes and commit them to your repository.

Usage:
    python apply_oct02_update.py

This script performs in‑place extraction and will overwrite existing
files.  It does not modify any other files or run any external
processes.
"""

import tarfile
import os
import sys
from pathlib import Path


def main() -> None:
    # Determine base directory (parent of forwardscripts)
    script_path = Path(__file__).resolve()
    base_dir = script_path.parents[1]
    tar_path = base_dir / "forwardscripts" / "oct02_update_files.tar.gz"
    if not tar_path.exists():
        print(f"⚠️  Update archive not found: {tar_path}")
        sys.exit(1)
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(base_dir)
        print("✅ October 2 updates applied successfully.\n"
              "   Updated files have been extracted to the repository root.")
    except Exception as exc:
        print(f"❌ Failed to apply updates: {exc}")
        sys.exit(1)


if __name__ == '__main__':
    main()