#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Application Restart Script
=====================================

Cleanly restarts the PokerTool application after updates or configuration changes.

This script:
1. Gracefully stops all running pokertool processes (backend API, frontend, GUI)
2. Cleans up any stuck processes
3. Waits for ports to be released
4. Relaunches the application

Usage:
    python restart.py              # Restart web application (default)
    python restart.py --gui        # Restart with GUI
    python restart.py --kill-only  # Just kill processes without restarting
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent

def log(message):
    """Print log message with timestamp."""
    print(f"[RESTART] {message}")

def kill_processes():
    """Kill all pokertool-related processes."""
    log("Stopping all pokertool processes...")
    
    current_pid = os.getpid()
    
    # For Unix-like systems (macOS, Linux)
    if sys.platform != 'win32':
        patterns = [
            'python.*start\\.py',
            '\\.venv/bin/python.*start\\.py',
            'python.*enhanced_gui',
            'python.*launch.*gui',
            'uvicorn.*pokertool',
            'python.*uvicorn.*pokertool',
            '\\.venv.*uvicorn.*pokertool',
            'python.*-m.*uvicorn.*pokertool',
            'node.*react-scripts',
            'react-scripts start',
            'npm start',
        ]
        
        all_pids = set()
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ['pgrep', '-f', pattern],
                    capture_output=True, text=True, timeout=3
                )
                pids = [int(pid) for pid in result.stdout.strip().split('\n')
                       if pid and pid.strip() and int(pid) != current_pid]
                all_pids.update(pids)
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
        
        # Check processes on ports 5001 and 3000
        for port in [5001, 3000]:
            try:
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True, text=True, timeout=3
                )
                port_pids = [int(pid) for pid in result.stdout.strip().split('\n')
                           if pid and pid.strip() and int(pid) != current_pid]
                if port_pids:
                    log(f"Found process(es) using port {port}")
                    all_pids.update(port_pids)
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                pass
        
        if all_pids:
            log(f"Found {len(all_pids)} process(es) to stop")
            
            # Try graceful shutdown first (SIGTERM)
            for pid in all_pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    log(f"Sent SIGTERM to PID {pid}")
                except (ProcessLookupError, PermissionError):
                    pass
            
            # Wait for graceful shutdown
            time.sleep(2.0)
            
            # Force kill any remaining processes (SIGKILL)
            still_running = []
            for pid in all_pids:
                try:
                    os.kill(pid, 0)  # Check if still running
                    os.kill(pid, signal.SIGKILL)
                    still_running.append(pid)
                    log(f"Force killed PID {pid}")
                except (ProcessLookupError, PermissionError):
                    pass
            
            if still_running:
                log(f"Force killed {len(still_running)} stuck process(es)")
            
            time.sleep(1.0)
            log("✓ All processes stopped")
        else:
            log("✓ No running processes found")
    
    # For Windows
    else:
        subprocess.run(
            ['taskkill', '/F', '/FI', f'IMAGENAME eq python*', '/FI', f'PID ne {current_pid}'],
            capture_output=True, timeout=5
        )
        subprocess.run(
            ['taskkill', '/F', '/FI', 'IMAGENAME eq node.exe'],
            capture_output=True, timeout=5
        )
        log("✓ Processes stopped (Windows)")

def wait_for_ports():
    """Wait for ports 5001 and 3000 to be released."""
    log("Waiting for ports to be released...")
    
    max_wait = 10  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            if sys.platform != 'win32':
                result = subprocess.run(
                    ['lsof', '-ti', ':5001', ':3000'],
                    capture_output=True, text=True, timeout=2
                )
                if not result.stdout.strip():
                    log("✓ Ports are free")
                    return True
            else:
                # Windows doesn't have lsof, just wait
                time.sleep(2)
                log("✓ Waited for ports")
                return True
        except:
            pass
        
        time.sleep(0.5)
    
    log("✓ Port wait timeout (proceeding anyway)")
    return True

def start_app(gui_mode=False):
    """Start the application."""
    if gui_mode:
        log("Starting PokerTool with GUI...")
        subprocess.Popen([sys.executable, str(ROOT / 'start.py'), '--gui'])
    else:
        log("Starting PokerTool web application...")
        subprocess.Popen([sys.executable, str(ROOT / 'start.py')])
    
    time.sleep(2)
    log("✓ Application started")
    log("")
    log("=" * 70)
    log("🎉 POKERTOOL RESTARTED SUCCESSFULLY!")
    log("=" * 70)
    log("")
    if not gui_mode:
        log("📱 Access the app at: http://localhost:3000")
        log("🔧 API documentation: http://localhost:5001/docs")
    log("")

def main():
    """Main restart routine."""
    import argparse
    
    parser = argparse.ArgumentParser(description='PokerTool Application Restart Script')
    parser.add_argument('--gui', action='store_true', help='Restart with GUI mode')
    parser.add_argument('--kill-only', action='store_true', help='Only kill processes without restarting')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔄 POKERTOOL RESTART SCRIPT")
    print("=" * 70)
    print("")
    
    try:
        # Step 1: Kill existing processes
        kill_processes()
        
        # Step 2: Wait for ports to be released
        wait_for_ports()
        
        # Step 3: Restart (unless kill-only mode)
        if not args.kill_only:
            start_app(gui_mode=args.gui)
            return 0
        else:
            log("✓ Processes stopped (kill-only mode)")
            return 0
    
    except KeyboardInterrupt:
        log("Restart interrupted by user")
        return 130
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())