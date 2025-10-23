#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PokerTool Feature Management & Release Automation Script
========================================================

This script automates the process of committing features and creating releases
for the PokerTool project. It handles:
- Feature commits to the develop branch
- Automated release version management
- Release branch creation
- Git push operations

Usage:
    # Add a feature to develop branch
    python add_feature.py --message "Add new poker hand analyzer"
    
    # Create and push a release
    python add_feature.py --release --message "Release v1.2.0 with new features"
    
    # Dry run (preview without executing)
    python add_feature.py --message "Test commit" --dry-run
    
    # Stage specific files
    python add_feature.py --message "Fix bug" --files src/pokertool/api.py tests/

Requirements:
    - Git must be installed and accessible
    - GITREPO_LOCATION.md file must exist in project root
    - Working directory must be clean or have staged changes

Author: PokerTool Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class GitRepoManager:
    """Manages Git repository operations for feature additions and releases."""
    
    def __init__(self, repo_location_file: str = "GITREPO_LOCATION.md", dry_run: bool = False):
        """
        Initialize the Git repository manager.
        
        Args:
            repo_location_file: Path to file containing Git repository location
            dry_run: If True, preview operations without executing them
        """
        self.dry_run = dry_run
        self.repo_location_file = Path(repo_location_file)
        self.repo_url = self._read_repo_location()
        self.project_root = Path.cwd()
        
    def _read_repo_location(self) -> str:
        """
        Read the Git repository URL from GITREPO_LOCATION.md file.
        
        Returns:
            Git repository URL
            
        Raises:
            FileNotFoundError: If GITREPO_LOCATION.md doesn't exist
            ValueError: If file is empty or invalid
        """
        if not self.repo_location_file.exists():
            raise FileNotFoundError(
                f"{Colors.FAIL}Error: {self.repo_location_file} not found. "
                f"Please create this file with your Git repository URL.{Colors.ENDC}"
            )
        
        content = self.repo_location_file.read_text().strip()
        
        # Extract URL from markdown if needed
        if content.startswith('http') or content.startswith('git@'):
            return content
        
        # Try to extract from markdown code block or link
        url_match = re.search(r'(https?://[^\s)]+|git@[^\s)]+)', content)
        if url_match:
            return url_match.group(1)
        
        raise ValueError(
            f"{Colors.FAIL}Error: Could not find valid Git repository URL in "
            f"{self.repo_location_file}{Colors.ENDC}"
        )
    
    def _run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Execute a shell command.
        
        Args:
            command: Command and arguments as list
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        if self.dry_run:
            print(f"{Colors.OKCYAN}[DRY RUN] Would execute: {' '.join(command)}{Colors.ENDC}")
            return (0, "", "")
        
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                cwd=self.project_root
            )
            return (result.returncode, result.stdout, result.stderr)
        except Exception as e:
            return (1, "", str(e))
    
    def check_git_installed(self) -> bool:
        """
        Check if Git is installed and accessible.
        
        Returns:
            True if Git is available, False otherwise
        """
        returncode, _, _ = self._run_command(['git', '--version'])
        return returncode == 0
    
    def get_current_branch(self) -> str:
        """
        Get the currently checked out Git branch.
        
        Returns:
            Current branch name
        """
        returncode, stdout, _ = self._run_command(['git', 'branch', '--show-current'])
        if returncode == 0:
            return stdout.strip()
        return ""
    
    def get_repo_status(self) -> Tuple[bool, str]:
        """
        Check repository status for uncommitted changes.
        
        Returns:
            Tuple of (has_changes, status_output)
        """
        returncode, stdout, _ = self._run_command(['git', 'status', '--porcelain'])
        has_changes = bool(stdout.strip())
        return (has_changes, stdout)
    
    def stage_files(self, files: Optional[List[str]] = None) -> bool:
        """
        Stage files for commit.
        
        Args:
            files: List of file paths to stage, or None to stage all changes
            
        Returns:
            True if successful, False otherwise
        """
        if files:
            for file in files:
                returncode, _, stderr = self._run_command(['git', 'add', file])
                if returncode != 0:
                    print(f"{Colors.FAIL}Error staging {file}: {stderr}{Colors.ENDC}")
                    return False
        else:
            returncode, _, stderr = self._run_command(['git', 'add', '-A'])
            if returncode != 0:
                print(f"{Colors.FAIL}Error staging all files: {stderr}{Colors.ENDC}")
                return False
        
        print(f"{Colors.OKGREEN}✓ Files staged successfully{Colors.ENDC}")
        return True
    
    def commit_changes(self, message: str) -> bool:
        """
        Commit staged changes with the given message.
        
        Args:
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        returncode, _, stderr = self._run_command(['git', 'commit', '-m', message])
        if returncode != 0:
            print(f"{Colors.FAIL}Error committing changes: {stderr}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✓ Changes committed: {message}{Colors.ENDC}")
        return True
    
    def checkout_branch(self, branch: str, create: bool = False) -> bool:
        """
        Checkout a Git branch.
        
        Args:
            branch: Branch name to checkout
            create: Whether to create the branch if it doesn't exist
            
        Returns:
            True if successful, False otherwise
        """
        command = ['git', 'checkout']
        if create:
            command.append('-b')
        command.append(branch)
        
        returncode, _, stderr = self._run_command(command)
        if returncode != 0:
            print(f"{Colors.FAIL}Error checking out branch {branch}: {stderr}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✓ Checked out branch: {branch}{Colors.ENDC}")
        return True
    
    def push_branch(self, branch: str, set_upstream: bool = False) -> bool:
        """
        Push branch to remote repository.
        
        Args:
            branch: Branch name to push
            set_upstream: Whether to set upstream tracking
            
        Returns:
            True if successful, False otherwise
        """
        command = ['git', 'push']
        if set_upstream:
            command.extend(['-u', 'origin', branch])
        else:
            command.extend(['origin', branch])
        
        returncode, _, stderr = self._run_command(command, capture_output=True)
        if returncode != 0:
            print(f"{Colors.FAIL}Error pushing branch {branch}: {stderr}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✓ Pushed branch: {branch}{Colors.ENDC}")
        return True
    
    def get_latest_version(self) -> str:
        """
        Get the latest version tag from Git.
        
        Returns:
            Latest version string (e.g., "1.2.3") or "0.0.0" if none found
        """
        returncode, stdout, _ = self._run_command([
            'git', 'tag', '--list', 'v*', '--sort=-v:refname'
        ])
        
        if returncode == 0 and stdout.strip():
            latest_tag = stdout.strip().split('\n')[0]
            # Remove 'v' prefix if present
            return latest_tag.lstrip('v')
        
        return "0.0.0"
    
    def increment_version(self, version: str, bump_type: str = "minor") -> str:
        """
        Increment version number.
        
        Args:
            version: Current version string (e.g., "1.2.3")
            bump_type: Type of version bump (major, minor, patch)
            
        Returns:
            New version string
        """
        parts = [int(x) for x in version.split('.')]
        major, minor, patch = parts[0], parts[1], parts[2]
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def create_tag(self, version: str, message: str) -> bool:
        """
        Create an annotated Git tag.
        
        Args:
            version: Version string for the tag
            message: Tag annotation message
            
        Returns:
            True if successful, False otherwise
        """
        tag_name = f"v{version}"
        returncode, _, stderr = self._run_command([
            'git', 'tag', '-a', tag_name, '-m', message
        ])
        
        if returncode != 0:
            print(f"{Colors.FAIL}Error creating tag {tag_name}: {stderr}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✓ Created tag: {tag_name}{Colors.ENDC}")
        return True
    
    def push_tags(self) -> bool:
        """
        Push all tags to remote repository.
        
        Returns:
            True if successful, False otherwise
        """
        returncode, _, stderr = self._run_command(['git', 'push', '--tags'])
        if returncode != 0:
            print(f"{Colors.FAIL}Error pushing tags: {stderr}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKGREEN}✓ Tags pushed successfully{Colors.ENDC}")
        return True


def add_feature(
    message: str,
    files: Optional[List[str]] = None,
    dry_run: bool = False
) -> bool:
    """
    Add a feature by committing changes to the develop branch.
    
    Args:
        message: Commit message describing the feature
        files: Optional list of specific files to commit
        dry_run: If True, preview without executing
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Adding Feature ==={Colors.ENDC}\n")
    
    manager = GitRepoManager(dry_run=dry_run)
    
    # Verify Git is installed
    if not manager.check_git_installed():
        print(f"{Colors.FAIL}Error: Git is not installed or not in PATH{Colors.ENDC}")
        return False
    
    print(f"{Colors.OKBLUE}Repository: {manager.repo_url}{Colors.ENDC}")
    
    # Check current branch
    current_branch = manager.get_current_branch()
    print(f"{Colors.OKBLUE}Current branch: {current_branch}{Colors.ENDC}")
    
    # Switch to develop if needed
    if current_branch != "develop":
        print(f"{Colors.WARNING}Switching to develop branch...{Colors.ENDC}")
        if not manager.checkout_branch("develop"):
            return False
    
    # Check for changes
    has_changes, status = manager.get_repo_status()
    if not has_changes and not files:
        print(f"{Colors.WARNING}No changes to commit{Colors.ENDC}")
        return True
    
    # Stage files
    print(f"\n{Colors.OKBLUE}Staging changes...{Colors.ENDC}")
    if not manager.stage_files(files):
        return False
    
    # Commit changes
    print(f"\n{Colors.OKBLUE}Committing changes...{Colors.ENDC}")
    if not manager.commit_changes(message):
        return False
    
    # Push to develop
    print(f"\n{Colors.OKBLUE}Pushing to develop branch...{Colors.ENDC}")
    if not manager.push_branch("develop"):
        return False
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Feature added successfully!{Colors.ENDC}")
    return True


def create_release(
    message: str,
    bump_type: str = "minor",
    dry_run: bool = False
) -> bool:
    """
    Create a new release with version bump and release branch.
    
    Args:
        message: Release message
        bump_type: Type of version bump (major, minor, patch)
        dry_run: If True, preview without executing
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Creating Release ==={Colors.ENDC}\n")
    
    manager = GitRepoManager(dry_run=dry_run)
    
    # Verify Git is installed
    if not manager.check_git_installed():
        print(f"{Colors.FAIL}Error: Git is not installed or not in PATH{Colors.ENDC}")
        return False
    
    print(f"{Colors.OKBLUE}Repository: {manager.repo_url}{Colors.ENDC}")
    
    # Get current version
    current_version = manager.get_latest_version()
    print(f"{Colors.OKBLUE}Current version: v{current_version}{Colors.ENDC}")
    
    # Calculate new version
    new_version = manager.increment_version(current_version, bump_type)
    print(f"{Colors.OKGREEN}New version: v{new_version}{Colors.ENDC}")
    
    release_branch = f"release/v{new_version}"
    
    # Switch to develop
    current_branch = manager.get_current_branch()
    if current_branch != "develop":
        print(f"\n{Colors.OKBLUE}Switching to develop branch...{Colors.ENDC}")
        if not manager.checkout_branch("develop"):
            return False
    
    # Create release branch
    print(f"\n{Colors.OKBLUE}Creating release branch: {release_branch}{Colors.ENDC}")
    if not manager.checkout_branch(release_branch, create=True):
        return False
    
    # Create version tag
    print(f"\n{Colors.OKBLUE}Creating version tag...{Colors.ENDC}")
    tag_message = f"{message}\n\nRelease v{new_version} - {datetime.now().strftime('%Y-%m-%d')}"
    if not manager.create_tag(new_version, tag_message):
        return False
    
    # Push release branch
    print(f"\n{Colors.OKBLUE}Pushing release branch...{Colors.ENDC}")
    if not manager.push_branch(release_branch, set_upstream=True):
        return False
    
    # Push tags
    print(f"\n{Colors.OKBLUE}Pushing tags...{Colors.ENDC}")
    if not manager.push_tags():
        return False
    
    # Switch back to develop
    print(f"\n{Colors.OKBLUE}Switching back to develop...{Colors.ENDC}")
    if not manager.checkout_branch("develop"):
        return False
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Release v{new_version} created successfully!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  Release branch: {release_branch}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  Tag: v{new_version}{Colors.ENDC}")
    
    return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="PokerTool Feature Management & Release Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a feature to develop
  python add_feature.py --message "Add new poker hand analyzer"
  
  # Add specific files
  python add_feature.py --message "Fix bug" --files src/api.py tests/test_api.py
  
  # Create a minor release (1.2.3 -> 1.3.0)
  python add_feature.py --release --message "Release with new features"
  
  # Create a major release (1.2.3 -> 2.0.0)
  python add_feature.py --release --bump major --message "Major update"
  
  # Create a patch release (1.2.3 -> 1.2.4)
  python add_feature.py --release --bump patch --message "Bug fixes"
  
  # Dry run (preview without executing)
  python add_feature.py --message "Test" --dry-run
        """
    )
    
    parser.add_argument(
        '-m', '--message',
        required=True,
        help='Commit or release message'
    )
    
    parser.add_argument(
        '-r', '--release',
        action='store_true',
        help='Create a release instead of just committing to develop'
    )
    
    parser.add_argument(
        '-b', '--bump',
        choices=['major', 'minor', 'patch'],
        default='minor',
        help='Version bump type for releases (default: minor)'
    )
    
    parser.add_argument(
        '-f', '--files',
        nargs='+',
        help='Specific files to commit (default: all changes)'
    )
    
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Preview operations without executing them'
    )
    
    args = parser.parse_args()
    
    try:
        if args.release:
            success = create_release(
                message=args.message,
                bump_type=args.bump,
                dry_run=args.dry_run
            )
        else:
            success = add_feature(
                message=args.message,
                files=args.files,
                dry_run=args.dry_run
            )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Operation cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
