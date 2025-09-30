#!/usr/bin/env python3
"""Simple launcher that bypasses syntax scanning."""

import sys
import os

# Set NumExpr thread limit to prevent warning
os.environ['NUMEXPR_MAX_THREADS'] = '8'

# Set environment variable to skip syntax scan
os.environ['START_NO_SCAN'] = '1'

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run start.py's main
from start import main

if __name__ == '__main__':
    sys.exit(main())
