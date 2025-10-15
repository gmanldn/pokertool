#!/usr/bin/env python3
"""
Automated debugging loop for start.py
Runs start.py repeatedly, logs errors, and helps identify issues.
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
LOG_FILE = ROOT / "debug_loop.log"
ERROR_LOG = ROOT / "error_summary.log"

def log_message(msg: str, to_error: bool = False):
    """Log a message to both console and log files."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")
    
    if to_error:
        with open(ERROR_LOG, "a") as f:
            f.write(formatted + "\n")

def run_start_py(iteration: int):
    """Run start.py and capture output."""
    log_message(f"\n{'='*60}")
    log_message(f"🔄 ITERATION {iteration}")
    log_message(f"{'='*60}\n")
    
    cmd = [sys.executable, str(ROOT / "start.py"), "--all"]
    
    log_message(f"Running: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=ROOT
        )
        
        # Monitor output in real-time
        errors_found = []
        output_lines = []
        
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            line = line.rstrip()
            output_lines.append(line)
            print(line)  # Real-time output
            
            # Check for common error patterns
            if any(err in line.lower() for err in ['error', 'exception', 'failed', 'traceback', 'importerror', 'modulenotfounderror']):
                errors_found.append(line)
        
        process.wait(timeout=120)  # 2 minute timeout
        returncode = process.returncode
        
        # Analyze results
        if returncode != 0:
            log_message(f"❌ Process exited with code {returncode}", to_error=True)
            if errors_found:
                log_message("\n📋 Errors detected:", to_error=True)
                for error in errors_found[:10]:  # Show first 10 errors
                    log_message(f"  - {error}", to_error=True)
            return False, errors_found, output_lines
        else:
            log_message("✅ Process completed successfully")
            return True, [], output_lines
            
    except subprocess.TimeoutExpired:
        log_message("⏱️  Process timeout - might be running GUI", to_error=True)
        process.kill()
        return False, ["Timeout - possibly GUI launched successfully"], []
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}", to_error=True)
        return False, [str(e)], []

def suggest_fixes(errors: list) -> list:
    """Analyze errors and suggest fixes."""
    suggestions = []
    
    for error in errors:
        error_lower = error.lower()
        
        if 'torch' in error_lower or 'pytorch' in error_lower:
            suggestions.append("🔧 Install torch: .venv/bin/pip install torch --extra-index-url https://download.pytorch.org/whl/cpu")
        
        if 'easyocr' in error_lower:
            suggestions.append("🔧 Install easyocr: .venv/bin/pip install easyocr")
        
        if 'tkinter' in error_lower or '_tkinter' in error_lower:
            suggestions.append("🔧 Install tkinter: brew install python-tk@3.12")
        
        if 'module' in error_lower and 'not found' in error_lower:
            suggestions.append("🔧 Run: python3 start.py --python to install dependencies")
        
        if 'importerror' in error_lower or 'modulenotfounderror' in error_lower:
            suggestions.append("🔧 Check virtual environment and reinstall dependencies")
    
    return list(set(suggestions))  # Remove duplicates

def git_commit(message: str):
    """Commit changes to git."""
    try:
        subprocess.run(["git", "add", "."], cwd=ROOT, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=ROOT, check=True, capture_output=True)
        log_message(f"✅ Committed: {message}")
        return True
    except subprocess.CalledProcessError:
        log_message("⚠️  Git commit failed (might be no changes)")
        return False

def main():
    """Main debugging loop."""
    log_message("\n" + "="*60)
    log_message("🚀 POKERTOOL DEBUG LOOP STARTED")
    log_message("="*60)
    
    # Clear old logs
    if LOG_FILE.exists():
        LOG_FILE.unlink()
    if ERROR_LOG.exists():
        ERROR_LOG.unlink()
    
    max_iterations = 10
    iteration = 0
    consecutive_failures = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        success, errors, output = run_start_py(iteration)
        
        if success:
            log_message("\n🎉 START.PY COMPLETED SUCCESSFULLY!")
            log_message("The application should now be running.")
            break
        
        consecutive_failures += 1
        
        # Analyze errors and provide suggestions
        if errors:
            suggestions = suggest_fixes(errors)
            if suggestions:
                log_message("\n💡 SUGGESTED FIXES:", to_error=True)
                for suggestion in suggestions:
                    log_message(f"  {suggestion}", to_error=True)
        
        # Check if we should continue
        if consecutive_failures >= 3:
            log_message(f"\n⚠️  {consecutive_failures} consecutive failures")
            log_message("Manual intervention may be required.")
            log_message(f"Check {ERROR_LOG} for error summary.")
            
            # One more try with full setup
            log_message("\n🔄 Attempting full environment reset...")
            try:
                subprocess.run([sys.executable, str(ROOT / "start.py"), "--venv", "--python"], 
                             cwd=ROOT, check=True, timeout=300)
                consecutive_failures = 0  # Reset counter after successful setup
            except:
                break
        
        # Small delay between iterations
        time.sleep(2)
    
    log_message("\n" + "="*60)
    log_message("🏁 DEBUG LOOP COMPLETED")
    log_message(f"Total iterations: {iteration}")
    log_message(f"Check logs at: {LOG_FILE}")
    if ERROR_LOG.exists():
        log_message(f"Error summary at: {ERROR_LOG}")
    log_message("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("\n\n⚠️  Debug loop interrupted by user")
        sys.exit(130)
