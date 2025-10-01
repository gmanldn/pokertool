#!/usr/bin/env python3
"""Simple launcher that bypasses syntax scanning."""

import sys
import os
import subprocess
from pathlib import Path

# Set NumExpr thread limit to prevent warning
os.environ['NUMEXPR_MAX_THREADS'] = '8'

# Set environment variable to skip syntax scan
os.environ['START_NO_SCAN'] = '1'

MODULE_DIR = Path(__file__).resolve().parent
ROOT = MODULE_DIR.parent.parent

for path in (MODULE_DIR, ROOT, ROOT / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# CRITICAL: Install dependencies before importing anything else
def ensure_critical_dependencies():
    """Ensure critical dependencies are installed before startup."""
    critical_deps = [
        ('cv2', 'opencv-python'),
        ('PIL', 'Pillow'),
        ('pytesseract', 'pytesseract'),
    ]
    
    missing = []
    for module_name, package_name in critical_deps:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print(f"\n{'='*60}")
        print("📦 Installing missing critical dependencies...")
        print(f"{'='*60}")
        for package in missing:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Failed to install {package}: {e}")
                print(f"   Please run manually: pip install {package}")
        print(f"{'='*60}\n")

# Install dependencies BEFORE importing start module
ensure_critical_dependencies()

# Import and run start.py's main
from start import main

if __name__ == '__main__':
    sys.exit(main())
