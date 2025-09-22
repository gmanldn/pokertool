#!/usr/bin/env python3
"""
Git Auto-Commit Script for Pokertool Repository
Commits all changes as version24 to develop branch
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

def main():
    # Get current directory or specify your pokertool path
    repo_path = os.getcwd()
    
    # Uncomment and modify this line if you want to specify the exact path
    # repo_path = "/path/to/your/pokertool"
    
    print(f"Working in repository: {repo_path}")
    
    # Check if we're in a git repository
    stdout, stderr = run_git_command("git status", cwd=repo_path)
    if stdout is None:
        print("Error: Not in a git repository or git not available")
        sys.exit(1)
    
    # Switch to develop branch
    print("Switching to develop branch...")
    run_git_command("git checkout develop", cwd=repo_path)
    
    # Pull latest changes
    print("Pulling latest changes...")
    run_git_command("git pull origin develop", cwd=repo_path)
    
    # Check for changes
    print("Checking for changes...")
    stdout, stderr = run_git_command("git status --porcelain", cwd=repo_path)
    
    if not stdout:
        print("No changes to commit.")
        return
    
    print(f"Found changes:\n{stdout}")
    
    # Add all changes
    print("Adding all changes...")
    run_git_command("git add .", cwd=repo_path)
    
    # Commit as version24
    commit_message = "version24"
    print(f"Committing as: {commit_message}")
    run_git_command(f'git commit -m "{commit_message}"', cwd=repo_path)
    
    # Create version24 tag
    print("Creating version24 tag...")
    run_git_command("git tag -a v24 -m 'Version 24 release'", cwd=repo_path)
    
    # Push to develop branch
    print("Pushing to develop branch...")
    run_git_command("git push origin develop", cwd=repo_path)
    
    # Push tags
    print("Pushing tags...")
    run_git_command("git push origin --tags", cwd=repo_path)
    
    print("✅ Successfully committed as version24 and pushed to develop branch!")
    print("✅ Created and pushed v24 tag")

if __name__ == "__main__":
    main()