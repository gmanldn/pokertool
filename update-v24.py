#!/usr/bin/env python3
"""
Safe Git Auto-Commit Script for Pokertool Repository
Commits all changes with safety checks to develop branch
"""

import subprocess
import sys
import os
from datetime import datetime

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

def count_file_changes(status_output):
    """Count additions, modifications, and deletions from git status"""
    lines = status_output.strip().split('\n')
    additions = sum(1 for line in lines if line.startswith('A ') or line.startswith('??'))
    modifications = sum(1 for line in lines if line.startswith('M '))
    deletions = sum(1 for line in lines if line.startswith('D '))
    return additions, modifications, deletions

def main():
    # Get current directory
    repo_path = os.getcwd()
    print(f"Working in repository: {repo_path}")
    
    # Check if we're in a git repository
    stdout, stderr = run_git_command("git status", cwd=repo_path)
    if stdout is None:
        print("Error: Not in a git repository or git not available")
        sys.exit(1)
    
    # Ensure we're on develop branch
    print("Ensuring we're on develop branch...")
    current_branch, _ = run_git_command("git branch --show-current", cwd=repo_path)
    if current_branch != "develop":
        print(f"Switching from {current_branch} to develop branch...")
        stdout, stderr = run_git_command("git checkout develop", cwd=repo_path)
        if stdout is None:
            print("Failed to switch to develop branch")
            sys.exit(1)
    
    # Pull latest changes
    print("Pulling latest changes...")
    run_git_command("git pull origin develop", cwd=repo_path)
    
    # Check for changes with safety analysis
    print("Checking for changes...")
    stdout, stderr = run_git_command("git status --porcelain", cwd=repo_path)
    
    if not stdout:
        print("No changes to commit.")
        return
    
    # Safety check: count file changes
    additions, modifications, deletions = count_file_changes(stdout)
    print(f"Change summary: +{additions} new files, ~{modifications} modified, -{deletions} deleted")
    
    # Safety abort if too many deletions detected
    if deletions > 100:
        print(f"🚨 SAFETY ABORT: {deletions} file deletions detected!")
        print("This seems excessive and potentially dangerous.")
        print("Please review changes manually before proceeding.")
        print("Run 'git status' to see what would be deleted.")
        sys.exit(1)
    
    # Show first 20 changes for review
    changes_preview = stdout.split('\n')[:20]
    print("Preview of changes:")
    for change in changes_preview:
        print(f"  {change}")
    if len(stdout.split('\n')) > 20:
        print(f"  ... and {len(stdout.split('\n')) - 20} more changes")
    
    # Ask for confirmation if many changes
    total_changes = additions + modifications + deletions
    if total_changes > 50:
        response = input(f"\n⚠️  {total_changes} total changes detected. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Aborted by user.")
            sys.exit(0)
    
    # Add all changes
    print("Adding all changes...")
    stdout, stderr = run_git_command("git add .", cwd=repo_path)
    if stdout is None:
        print("Failed to add changes")
        sys.exit(1)
    
    # Generate timestamp-based commit message
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    commit_message = f"Auto-commit v24 update - {timestamp}"
    print(f"Committing as: {commit_message}")
    
    stdout, stderr = run_git_command(f'git commit -m "{commit_message}"', cwd=repo_path)
    if stdout is None:
        print("Failed to commit changes")
        sys.exit(1)
    
    # Check if v24 tag already exists and handle appropriately
    print("Checking for existing v24 tag...")
    stdout, stderr = run_git_command("git tag -l v24", cwd=repo_path)
    
    if stdout == "v24":
        print("⚠️  v24 tag already exists. Creating v24-update tag instead...")
        tag_name = f"v24-update-{timestamp}"
        run_git_command(f'git tag -a {tag_name} -m "Version 24 update - {timestamp}"', cwd=repo_path)
    else:
        print("Creating v24 tag...")
        tag_name = "v24"
        run_git_command(f'git tag -a {tag_name} -m "Version 24 release"', cwd=repo_path)
    
    # Push to develop branch
    print("Pushing to develop branch...")
    stdout, stderr = run_git_command("git push origin develop", cwd=repo_path)
    if stdout is None:
        print("Failed to push to develop branch")
        sys.exit(1)
    
    # Push tags
    print("Pushing tags...")
    stdout, stderr = run_git_command("git push origin --tags", cwd=repo_path)
    if stdout is None:
        print("Warning: Failed to push tags, but main commit succeeded")
    
    print("✅ Successfully committed and pushed to develop branch!")
    print(f"✅ Created and pushed {tag_name} tag")

if __name__ == "__main__":
    main()
