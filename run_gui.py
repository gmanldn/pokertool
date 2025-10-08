#!/usr/bin/env python3
"""
Direct GUI launcher that avoids -m module loading issues.
This ensures clean import paths for numpy and other packages.
"""
import sys
import os
from pathlib import Path

# Get paths
ROOT = Path(__file__).parent.resolve()
SRC_DIR = ROOT / 'src'
VENV_DIR = ROOT / '.venv'

# Find venv site-packages
import glob
site_packages_pattern = str(VENV_DIR / 'lib' / 'python*' / 'site-packages')
site_packages_dirs = glob.glob(site_packages_pattern)

# Fix sys.path order: site-packages MUST come before src
if site_packages_dirs:
    # Remove any existing entries
    for sp in site_packages_dirs:
        if sp in sys.path:
            sys.path.remove(sp)
    # Insert at position 1 (after script directory)
    sys.path.insert(1, site_packages_dirs[0])

# Add src after site-packages
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

# Now import and run
from pokertool.cli import main

if __name__ == '__main__':
    sys.exit(main())
