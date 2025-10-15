#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: verify_enhanced_gui.py
# version: v21.0.0
# last_commit: 2025-10-12T00:00:00Z
# fixes:
#   - date: 2025-10-12
#     summary: Verification script for enhanced GUI installation
# ---
# POKERTOOL-HEADER-END

Enhanced GUI Installation Verification
======================================

This script verifies that the enhanced GUI v21.0.0 is properly installed
and all dependencies are available.

Usage:
    python verify_enhanced_gui.py
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

def print_header():
    """Print verification header."""
    print("=" * 70)
    print("PokerTool Enhanced GUI v21.0.0 - Installation Verification")
    print("=" * 70)
    print()

def check_python_version() -> bool:
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 7:
        print(f"  ✅ Python {version_str} (OK)")
        return True
    else:
        print(f"  ❌ Python {version_str} (requires 3.7+)")
        return False

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {filepath}")
    return exists

def check_files() -> bool:
    """Check if required files exist."""
    print("\nChecking required files...")
    
    required_files = [
        "src/pokertool/gui_enhanced_v2.py",
        "src/pokertool/desktop_independent_scraper.py",
        "src/pokertool/core/__init__.py",
        "tests/test_gui_enhanced_v2.py",
        "launch_enhanced_gui_v2.py",
        "ENHANCED_GUI_V2_README.md",
        "GUI_REWORK_SUMMARY.md",
    ]
    
    all_exist = True
    for filepath in required_files:
        if not check_file_exists(filepath):
            all_exist = False
    
    return all_exist

def check_dependency(module_name: str, package_name: str = None) -> bool:
    """Check if a Python dependency is available."""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"  ✅ {package_name}")
        return True
    except ImportError:
        print(f"  ❌ {package_name} (pip install {package_name})")
        return False

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check Python dependencies."""
    print("\nChecking required dependencies...")
    
    required = [
        ('tkinter', 'tkinter'),
        ('numpy', 'numpy'),
        ('PIL', 'Pillow'),
    ]
    
    optional = [
        ('cv2', 'opencv-python'),
        ('mss', 'mss'),
        ('pytesseract', 'pytesseract'),
    ]
    
    required_ok = True
    for module, package in required:
        if not check_dependency(module, package):
            required_ok = False
    
    print("\nChecking optional dependencies...")
    missing_optional = []
    for module, package in optional:
        if not check_dependency(module, package):
            missing_optional.append(package)
    
    return required_ok, missing_optional

def check_platform_dependencies() -> List[str]:
    """Check platform-specific dependencies."""
    import platform
    
    print("\nChecking platform-specific dependencies...")
    system = platform.system()
    print(f"  Platform: {system}")
    
    missing = []
    
    if system == 'Darwin':  # macOS
        if not check_dependency('Quartz', 'pyobjc-framework-Quartz'):
            missing.append('pyobjc-framework-Quartz')
    
    elif system == 'Windows':
        try:
            import win32gui
            print(f"  ✅ pywin32")
        except ImportError:
            print(f"  ⚠️  pywin32 (optional but recommended)")
            missing.append('pywin32')
    
    elif system == 'Linux':
        print(f"  ⚠️  Note: Install 'wmctrl' system package for better functionality")
    
    return missing

def run_quick_test() -> bool:
    """Run a quick import test."""
    print("\nRunning quick import test...")
    
    try:
        print("  Importing gui_enhanced_v2...")
        sys.path.insert(0, 'src')
        from pokertool import gui_enhanced_v2
        print("  ✅ GUI module imports successfully")
        
        print("  Importing desktop_independent_scraper...")
        from pokertool import desktop_independent_scraper
        print("  ✅ Scraper module imports successfully")
        
        print("  Importing core...")
        from pokertool import core
        print("  ✅ Core module imports successfully")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def print_summary(results: dict):
    """Print verification summary."""
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_ok = all(results.values())
    
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
    
    print()
    
    if all_ok:
        print("🎉 All checks passed! Enhanced GUI is ready to use.")
        print("\nTo launch the application:")
        print("    python launch_enhanced_gui_v2.py")
    else:
        print("⚠️  Some checks failed. Please address the issues above.")
        print("\nCommon solutions:")
        print("  - Install missing dependencies: pip install -r requirements.txt")
        print("  - Verify all files are present in the repository")
        print("  - Check Python version (3.7+ required)")
    
    print("\nFor detailed documentation, see:")
    print("    ENHANCED_GUI_V2_README.md")
    print()

def main():
    """Main verification function."""
    print_header()
    
    results = {
        "Python Version": check_python_version(),
        "Required Files": check_files(),
    }
    
    deps_ok, missing_optional = check_dependencies()
    results["Required Dependencies"] = deps_ok
    
    if missing_optional:
        print(f"\n⚠️  Missing optional dependencies: {', '.join(missing_optional)}")
        print("   These are not required but recommended for full functionality.")
    
    platform_missing = check_platform_dependencies()
    if not platform_missing:
        results["Platform Dependencies"] = True
    else:
        print(f"\n⚠️  Missing platform dependencies: {', '.join(platform_missing)}")
        results["Platform Dependencies"] = False
    
    results["Import Test"] = run_quick_test()
    
    print_summary(results)
    
    return 0 if all(results.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
