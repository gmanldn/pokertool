#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Release Management Script
====================================

Automates version updates and release branch creation.

Usage:
    python scripts/release.py --version 61.0.0 --name "Feature Name"
    python scripts/release.py --current  # Show current version
    python scripts/release.py --history  # Show release history
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from pokertool.version import get_version, print_version_info, get_release_history


def update_version(new_version: str, release_name: str = ""):
    """
    Update version across all files.

    Args:
        new_version: New version string (e.g., "61.0.0")
        release_name: Optional release name
    """
    print(f"\n📦 Updating to version {new_version}")
    print("=" * 70)

    # Update VERSION file
    version_file = ROOT / 'VERSION'
    version_file.write_text(new_version)
    print(f"✓ Updated {version_file}")

    # Update start.py
    start_file = ROOT / 'start.py'
    content = start_file.read_text()

    # Update version variable
    content = content.replace(
        f"__version__ = '{get_version()}'",
        f"__version__ = '{new_version}'"
    )

    # Update version in header
    content = content.replace(
        f"# version: v{get_version()}",
        f"# version: v{new_version}"
    )

    # Update version in docstring
    content = content.replace(
        f"PokerTool One-Click Launcher - v{get_version()}",
        f"PokerTool One-Click Launcher - v{new_version}"
    )

    # Update version in banner
    content = content.replace(
        f"POKERTOOL - Enhanced GUI v{get_version()}",
        f"POKERTOOL - Enhanced GUI v{new_version}"
    )

    start_file.write_text(content)
    print(f"✓ Updated {start_file}")

    print("\n✅ Version updated successfully!")
    print(f"   Version: {new_version}")
    if release_name:
        print(f"   Name: {release_name}")


def create_release_branch(version: str):
    """
    Create and push release branch.

    Args:
        version: Version string (e.g., "61.0.0")
    """
    branch_name = f"release/v{version}"

    print(f"\n🌿 Creating release branch: {branch_name}")
    print("=" * 70)

    try:
        # Create branch
        result = subprocess.run(
            ['git', 'checkout', '-b', branch_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ Created branch: {branch_name}")

        # Stage changes
        subprocess.run(['git', 'add', '-A'], check=True)
        print("✓ Staged all changes")

        # Commit
        commit_msg = f"Release v{version}: Version update"
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            check=True
        )
        print(f"✓ Committed: {commit_msg}")

        # Push branch
        subprocess.run(
            ['git', 'push', '-u', 'origin', branch_name],
            check=True
        )
        print(f"✓ Pushed to origin/{branch_name}")

        print("\n✅ Release branch created successfully!")
        print(f"   Branch: {branch_name}")
        print(f"   Ready for: Merge to main, Tag creation")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error creating release branch: {e}")
        print(f"   Output: {e.stderr}")
        sys.exit(1)


def create_release_tag(version: str, message: str = ""):
    """
    Create annotated release tag.

    Args:
        version: Version string (e.g., "61.0.0")
        message: Tag message
    """
    tag_name = f"v{version}"

    print(f"\n🏷️  Creating release tag: {tag_name}")
    print("=" * 70)

    try:
        if not message:
            message = f"Release {tag_name}"

        # Create annotated tag
        subprocess.run(
            ['git', 'tag', '-a', tag_name, '-m', message],
            check=True
        )
        print(f"✓ Created tag: {tag_name}")

        # Push tag
        subprocess.run(
            ['git', 'push', 'origin', tag_name],
            check=True
        )
        print(f"✓ Pushed tag to origin")

        print("\n✅ Release tag created successfully!")
        print(f"   Tag: {tag_name}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error creating tag: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PokerTool Release Management'
    )

    parser.add_argument(
        '--version',
        help='New version number (e.g., 61.0.0)'
    )

    parser.add_argument(
        '--name',
        help='Release name (e.g., "Feature Name")',
        default=""
    )

    parser.add_argument(
        '--current',
        action='store_true',
        help='Show current version'
    )

    parser.add_argument(
        '--history',
        action='store_true',
        help='Show release history'
    )

    parser.add_argument(
        '--branch',
        action='store_true',
        help='Create release branch'
    )

    parser.add_argument(
        '--tag',
        action='store_true',
        help='Create release tag'
    )

    parser.add_argument(
        '--message',
        help='Tag message',
        default=""
    )

    args = parser.parse_args()

    # Show current version
    if args.current:
        print_version_info()
        return

    # Show history
    if args.history:
        print("=" * 70)
        print("Release History")
        print("=" * 70)
        for release in get_release_history():
            print(f"\nv{release['version']} ({release['date']}) - {release['name']}")
            if 'description' in release:
                print(f"  {release['description']}")
            if 'highlights' in release:
                for highlight in release['highlights']:
                    print(f"  • {highlight}")
        return

    # Update version
    if args.version:
        update_version(args.version, args.name)

        # Create branch if requested
        if args.branch:
            create_release_branch(args.version)

        # Create tag if requested
        if args.tag:
            create_release_tag(args.version, args.message)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
