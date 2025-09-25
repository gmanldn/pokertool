#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: backups/develop_20250922_053042/git_commit_main.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Automated Git Commit Script for Main Branch
Commits all changes with enhanced safety checks for production deployments
"""

import subprocess
import sys
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def run_git_command(command, cwd=None):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        print(f"Error output: {e.stderr}")
        return None, e.stderr

def backup_changed_files(repo_path):
    """Create backup of changed files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(repo_path) / f"backups/main_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of changed files
    stdout, _ = run_git_command("git diff --name-only HEAD", cwd=repo_path)
    if stdout:
        changed_files = stdout.split('\n')
        for file_path in changed_files:
            if file_path and os.path.exists(os.path.join(repo_path, file_path)):
                src_file = Path(repo_path) / file_path
                dst_file = backup_dir / file_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception as e:
                    print(f"Warning: Could not backup {file_path}: {e}")
    
    # Also get untracked files
    stdout, _ = run_git_command("git ls-files --others --exclude-standard", cwd=repo_path)
    if stdout:
        untracked_files = stdout.split('\n')
        for file_path in untracked_files:
            if file_path and os.path.exists(os.path.join(repo_path, file_path)):
                src_file = Path(repo_path) / file_path
                dst_file = backup_dir / file_path
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception as e:
                    print(f"Warning: Could not backup {file_path}: {e}")
    
    print(f"✅ Files backed up to: {backup_dir}")
    return backup_dir

def count_file_changes(status_output):
    """Count additions, modifications, and deletions from git status"""
    lines = status_output.strip().split('\n')
    additions = sum(1 for line in lines if line.startswith('A ') or line.startswith('??'))
    modifications = sum(1 for line in lines if line.startswith('M '))
    deletions = sum(1 for line in lines if line.startswith('D '))
    return additions, modifications, deletions

def log_commit_info(repo_path, commit_hash, changes_summary):
    """Log commit information for tracking"""
    log_file = Path(repo_path) / "commit_log.json"
    
    commit_info = {
        "timestamp": datetime.now().isoformat(),
        "branch": "main",
        "commit_hash": commit_hash,
        "changes_summary": changes_summary,
        "script_version": "1.0"
    }
    
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(commit_info)
    
    # Keep only last 100 commits
    logs = logs[-100:]
    
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)

def run_tests(repo_path):
    """Run unit tests before committing to main branch"""
    print("🧪 Running unit tests before main branch commit...")
    
    # Try different test commands
    test_commands = [
        "python -m pytest tests/ -v",
        "python -m unittest discover tests/",
        "python -m pytest -v",
        "python test_*.py"
    ]
    
    for cmd in test_commands:
        stdout, stderr = run_git_command(cmd, cwd=repo_path)
        if stdout is not None:
            print(f"✅ Tests passed with command: {cmd}")
            return True
    
    print("⚠️  Could not run tests or tests failed. Proceeding with caution...")
    return False

def check_branch_sync(repo_path):
    """Check if main branch is in sync with develop"""
    print("🔄 Checking branch synchronization...")
    
    # Get latest commits from both branches
    main_commit, _ = run_git_command("git rev-parse main", cwd=repo_path)
    develop_commit, _ = run_git_command("git rev-parse develop", cwd=repo_path)
    
    if main_commit and develop_commit:
        if main_commit == develop_commit:
            print("✅ Main and develop branches are in sync")
            return True
        else:
            print("⚠️  Main and develop branches are out of sync")
            # Check if develop is ahead
            ahead_behind, _ = run_git_command("git rev-list --left-right --count main...develop", cwd=repo_path)
            if ahead_behind:
                behind, ahead = ahead_behind.split('\t')
                print(f"📊 Main is {behind} commits behind and {ahead} commits ahead of develop")
            return False
    return False

def create_release_tag(repo_path, version):
    """Create a release tag for the main branch commit"""
    tag_name = f"v{version}"
    print(f"🏷️  Creating release tag: {tag_name}")
    
    # Check if tag already exists
    stdout, _ = run_git_command(f"git tag -l {tag_name}", cwd=repo_path)
    if stdout == tag_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_name = f"v{version}-{timestamp}"
        print(f"⚠️  Tag v{version} exists, creating: {tag_name}")
    
    release_message = f"Release version {version} - {datetime.now().strftime('%Y-%m-%d')}"
    run_git_command(f'git tag -a {tag_name} -m "{release_message}"', cwd=repo_path)
    return tag_name

def main():
    # Get current directory
    repo_path = os.getcwd()
    print(f"🔧 Working in repository: {repo_path}")
    
    # Check if we're in a git repository
    stdout, stderr = run_git_command("git status", cwd=repo_path)
    if stdout is None:
        print("❌ Error: Not in a git repository or git not available")
        sys.exit(1)
    
    # Ensure we're on main branch
    print("🔄 Ensuring we're on main branch...")
    current_branch, _ = run_git_command("git branch --show-current", cwd=repo_path)
    if current_branch != "main":
        print(f"🔄 Switching from {current_branch} to main branch...")
        stdout, stderr = run_git_command("git checkout main", cwd=repo_path)
        if stdout is None:
            print("❌ Failed to switch to main branch")
            sys.exit(1)
    
    # Pull latest changes
    print("📥 Pulling latest changes...")
    run_git_command("git pull origin main", cwd=repo_path)
    
    # Check branch synchronization
    check_branch_sync(repo_path)
    
    # Check for changes with safety analysis
    print("🔍 Checking for changes...")
    stdout, stderr = run_git_command("git status --porcelain", cwd=repo_path)
    
    if not stdout:
        print("✅ No changes to commit.")
        return
    
    # Backup changed files
    backup_dir = backup_changed_files(repo_path)
    
    # Safety check: count file changes
    additions, modifications, deletions = count_file_changes(stdout)
    changes_summary = {
        "additions": additions,
        "modifications": modifications,
        "deletions": deletions,
        "total": additions + modifications + deletions
    }
    
    print(f"📊 Change summary: +{additions} new files, ~{modifications} modified, -{deletions} deleted")
    
    # Enhanced safety checks for main branch
    if deletions > 10:
        print(f"🚨 PRODUCTION SAFETY ABORT: {deletions} file deletions detected!")
        print("This seems risky for main branch. Please review carefully.")
        print("Consider merging from develop instead of direct commits to main.")
        sys.exit(1)
    
    if changes_summary['total'] > 100:
        print(f"🚨 LARGE CHANGESET WARNING: {changes_summary['total']} total changes!")
        print("This is a large changeset for main branch.")
        response = input("Continue with production deployment? (y/N): ")
        if response.lower() != 'y':
            print("Aborted by user.")
            sys.exit(0)
    
    # Run tests before committing to main
    run_tests(repo_path)
    
    # Show first 20 changes for review
    changes_preview = stdout.split('\n')[:20]
    print("👀 Preview of changes:")
    for change in changes_preview:
        print(f"  {change}")
    if len(stdout.split('\n')) > 20:
        print(f"  ... and {len(stdout.split('\n')) - 20} more changes")
    
    # Add all changes
    print("➕ Adding all changes...")
    stdout, stderr = run_git_command("git add .", cwd=repo_path)
    if stdout is None:
        print("❌ Failed to add changes")
        sys.exit(1)
    
    # Generate timestamp-based commit message for production
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    commit_message = f"Production release - {timestamp} - {changes_summary['total']} changes"
    print(f"💾 Committing as: {commit_message}")
    
    stdout, stderr = run_git_command(f'git commit -m "{commit_message}"', cwd=repo_path)
    if stdout is None:
        print("❌ Failed to commit changes")
        sys.exit(1)
    
    # Get commit hash
    commit_hash, _ = run_git_command("git rev-parse HEAD", cwd=repo_path)
    
    # Create release tag (assume version 25 for now)
    tag_name = create_release_tag(repo_path, "25")
    
    # Log commit information
    log_commit_info(repo_path, commit_hash, changes_summary)
    
    # Push to main branch
    print("🚀 Pushing to main branch...")
    stdout, stderr = run_git_command("git push origin main", cwd=repo_path)
    if stdout is None:
        print("❌ Failed to push to main branch")
        sys.exit(1)
    
    # Push tags
    print("🏷️  Pushing release tags...")
    stdout, stderr = run_git_command("git push origin --tags", cwd=repo_path)
    if stdout is None:
        print("⚠️  Failed to push tags, but main commit succeeded")
    
    print("✅ Successfully committed and pushed to main branch!")
    print(f"📝 Commit hash: {commit_hash}")
    print(f"🏷️  Release tag: {tag_name}")
    print(f"💾 Backup created at: {backup_dir}")
    print("🎉 Production deployment complete!")

if __name__ == "__main__":
    main()
