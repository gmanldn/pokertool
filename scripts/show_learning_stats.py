#!/usr/bin/env python3
"""
Quick Learning Stats Viewer
============================

Shows current learning system statistics.

Usage:
    python show_learning_stats.py
"""

import sys
from pathlib import Path

# Setup path
ROOT = Path(__file__).parent
SRC_DIR = ROOT / 'src'
sys.path.insert(0, str(SRC_DIR))

# Import and run
from pokertool.view_learning_stats import view_learning_stats

if __name__ == '__main__':
    sys.exit(view_learning_stats())
