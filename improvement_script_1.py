#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: improvement_script_1.py
# version: v20.0.0
# last_commit: '2025-09-23T14:49:14.025430+00:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Poker Tool Enhancement Script 1: GUI Improvements
This script implements the enhanced GUI with improved error handling and modern UI.
It follows the repo's guidelines for incremental improvements and git commits.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Configuration
REPO_ROOT = Path("/Users/georgeridout/Desktop/pokertool")
VERSION = "21"
IMPROVEMENT_NAME = "GUI_Enhancement_1"
COMMIT_MESSAGE = "feat: Enhanced GUI with modern UI, robust error handling, and improved UX"

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    if cwd is None:
        cwd = REPO_ROOT
    
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error output: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command {cmd}: {e}")
        return False

def backup_existing_file(filepath):
    """Create backup of existing file."""
    if filepath.exists():
        backup_path = filepath.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup")
        shutil.copy2(filepath, backup_path)
        print(f"Backed up {filepath} to {backup_path}")
        return backup_path
    return None

def update_header(filepath, improvement_name):
    """Update the pokertool header in a file."""
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return False
    
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Update version and improvement info
        header_start = "# POKERTOOL-HEADER-START"
        header_end = "# POKERTOOL-HEADER-END"
        
        if header_start in content and header_end in content:
            # Update existing header
            start_idx = content.find(header_start)
            end_idx = content.find(header_end) + len(header_end)
            
            new_header = f"""{header_start}
# ---
# schema: pokerheader.v1
# project: pokertool
# file: {filepath.name}
# version: '{VERSION}'
# last_updated_utc: '{datetime.now(timezone.utc).isoformat()}'
# applied_improvements: [{improvement_name}]
# summary: Enhanced version with {improvement_name}
# ---
{header_end}"""
            
            updated_content = content[:start_idx] + new_header + content[end_idx:]
            
            # Update version variable if present
            if '__version__ = ' in updated_content:
                import re
                updated_content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{VERSION}"', updated_content)
            
            filepath.write_text(updated_content, encoding='utf-8')
            print(f"Updated header in {filepath}")
            return True
        else:
            print(f"No pokertool header found in {filepath}")
            return False
            
    except Exception as e:
        print(f"Error updating header in {filepath}: {e}")
        return False

def main():
    """Main improvement implementation."""
    print(f"=== Poker Tool Enhancement Script 1: GUI Improvements ===")
    print(f"Working directory: {REPO_ROOT}")
    print(f"Target version: {VERSION}")
    print(f"Improvement: {IMPROVEMENT_NAME}")
    print()
    
    # Verify we're in the right directory
    if not (REPO_ROOT / "poker_modules.py").exists():
        print(f"Error: Not in pokertool repository root. Expected to find poker_modules.py")
        sys.exit(1)
    
    # Change to repo directory
    os.chdir(REPO_ROOT)
    
    # Check git status
    print("Checking git status...")
    if not run_command("git status --porcelain"):
        print("Error checking git status")
        sys.exit(1)
    
    # Create the enhanced GUI file
    enhanced_gui_path = REPO_ROOT / "poker_gui_enhanced.py"
    
    print(f"Creating enhanced GUI file: {enhanced_gui_path}")
    
    # The enhanced GUI code (this would be the content from the artifact)
    enhanced_gui_content = '''#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: poker_gui_enhanced.py
# version: '21'
# last_updated_utc: '2025-09-23T12:00:00.000000+00:00'
# applied_improvements: [GUI_Enhancement_1]
# summary: Enhanced main graphical user interface with improved error handling and modern UI
# ---
# POKERTOOL-HEADER-END
__version__ = "21"

"""
Enhanced Poker GUI - Robust and Modern Interface
Improved version of the main GUI with better error handling, validation, and UX.