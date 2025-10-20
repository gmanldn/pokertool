#!/usr/bin/env python3
"""
Refactor the nested pokertool/pokertool structure to a single pokertool package.
"""

import shutil
import os
from pathlib import Path

# Paths
ROOT = Path(__file__).parent
OUTER = ROOT / 'src' / 'pokertool'
INNER = OUTER / 'pokertool'

print("=== PokerTool Structure Refactoring ===\n")

# Safety checks
if not INNER.exists():
    print("ERROR: Inner pokertool directory doesn't exist!")
    exit(1)

if not OUTER.exists():
    print("ERROR: Outer pokertool directory doesn't exist!")
    exit(1)

print(f"Outer dir: {OUTER}")
print(f"Inner dir: {INNER}\n")

# Create backup
backup_dir = ROOT / 'structure_backup'
if backup_dir.exists():
    print("Removing old backup...")
    shutil.rmtree(backup_dir)

print("Creating backup...")
shutil.copytree(OUTER, backup_dir / 'pokertool')
print(f"✓ Backup created at: {backup_dir}\n")

# Read the inner __init__.py (the good one with version info)
inner_init = INNER / '__init__.py'
inner_init_content = inner_init.read_text()

# Read the inner __main__.py (the good one that works)
inner_main = INNER / '__main__.py'
inner_main_content = inner_main.read_text()

# Get list of items to move
items_to_move = []
for item in INNER.iterdir():
    if item.name not in ['__pycache__', '.DS_Store']:
        items_to_move.append(item)

print(f"Found {len(items_to_move)} items to move\n")

# Move all items from inner to outer
print("Moving files and directories...")
moved_count = 0
for item in items_to_move:
    dest = OUTER / item.name
    
    # Skip __init__.py and __main__.py for now (handle specially)
    if item.name in ['__init__.py', '__main__.py']:
        continue
    
    # Check if destination exists
    if dest.exists():
        print(f"  WARNING: {dest.name} already exists in outer, skipping...")
        continue
    
    print(f"  Moving: {item.name}")
    shutil.move(str(item), str(dest))
    moved_count += 1

print(f"✓ Moved {moved_count} items\n")

# Now handle __init__.py - use the inner one (it has proper version info)
print("Updating __init__.py...")
outer_init = OUTER / '__init__.py'
outer_init.write_text(inner_init_content)
print("✓ Updated __init__.py with proper content\n")

# Update __main__.py - simplify it now that structure is flat
print("Updating __main__.py...")
new_main_content = '''"""Module entry point so `python -m pokertool` dispatches to the CLI."""

from __future__ import annotations

from .cli import main


if __name__ == '__main__':  # pragma: no cover - thin wrapper
    raise SystemExit(main())
'''
outer_main = OUTER / '__main__.py'
outer_main.write_text(new_main_content)
print("✓ Updated __main__.py\n")

# Remove the now-empty inner pokertool directory
print("Removing empty inner directory...")
if INNER.exists():
    # Check if it's truly empty (except __pycache__)
    remaining = [item for item in INNER.iterdir() if item.name != '__pycache__']
    if remaining:
        print(f"  WARNING: Inner directory not empty! Contains: {[item.name for item in remaining]}")
        print("  Not deleting. Please review manually.")
    else:
        shutil.rmtree(INNER)
        print("✓ Removed inner pokertool directory\n")

# Update cli.py to use relative imports (should already be correct)
print("Checking cli.py imports...")
cli_file = OUTER / 'cli.py'
if cli_file.exists():
    cli_content = cli_file.read_text()
    if 'from . import' in cli_content:
        print("✓ cli.py already uses relative imports\n")
    else:
        print("  WARNING: cli.py might need import updates\n")

print("=== Refactoring Complete! ===")
print(f"\nBackup location: {backup_dir}")
print("\nNext steps:")
print("1. Run: python3 start.py --launch")
print("2. If it works, delete the backup: rm -rf structure_backup")
print("3. If it doesn't work, restore: rm -rf src/pokertool && mv structure_backup/pokertool src/")
