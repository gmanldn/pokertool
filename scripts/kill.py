#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Process Killer
========================

Kills all running pokertool processes, threads, and GUI instances.
Use this to clean up stuck processes before starting a new session.

Usage:
    python kill.py              # Kill all pokertool processes
    python kill.py --force      # Force kill everything immediately
    python kill.py --list       # Just list processes, don't kill
"""

from __future__ import annotations

import os
import sys
import time
import signal
import platform
import subprocess
import argparse
from pathlib import Path

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'


def log(message: str):
    """Log a message."""
    print(f"[KILL] {message}")


def get_pokertool_processes() -> list[int]:
    """
    Find all pokertool-related process PIDs.

    Returns:
        List of process IDs
    """
    current_pid = os.getpid()
    all_pids = set()

    if IS_WINDOWS:
        # Windows: Use tasklist to find python processes
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python*', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=5
            )

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1].strip('"'))
                            if pid != current_pid:
                                all_pids.add(pid)
                        except ValueError:
                            pass
        except Exception as e:
            log(f"Error finding Windows processes: {e}")

    else:
        # Unix: Use pgrep with multiple patterns
        patterns = [
            'python.*start\\.py',
            'python.*enhanced_gui',
            'python.*simple_gui',
            'python.*launch.*gui',
            'python.*run_gui',
            'python.*compact_live_advice',
            'pokertool.*gui',
            'python.*kill\\.py',  # Exclude ourselves
        ]

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

    return sorted(list(all_pids))


def get_process_info(pid: int) -> dict:
    """
    Get information about a process.

    Args:
        pid: Process ID

    Returns:
        Dict with process info (name, cmdline, status)
    """
    try:
        if IS_WINDOWS:
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                parts = result.stdout.strip().split(',')
                return {
                    'pid': pid,
                    'name': parts[0].strip('"') if parts else 'unknown',
                    'status': 'running'
                }
        else:
            # Unix: Use ps
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'command='],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                return {
                    'pid': pid,
                    'cmdline': result.stdout.strip(),
                    'status': 'running'
                }
    except Exception:
        pass

    return {'pid': pid, 'status': 'unknown'}


def list_processes():
    """List all pokertool processes without killing."""
    pids = get_pokertool_processes()

    if not pids:
        log("No pokertool processes found")
        return

    log(f"Found {len(pids)} pokertool process(es):")
    log("=" * 70)

    for pid in pids:
        info = get_process_info(pid)
        if 'cmdline' in info:
            log(f"  PID {pid}: {info['cmdline'][:80]}")
        else:
            log(f"  PID {pid}: {info.get('name', 'unknown')}")


def kill_processes(force: bool = False):
    """
    Kill all pokertool processes.

    Args:
        force: If True, use SIGKILL immediately. Otherwise try SIGTERM first.
    """
    pids = get_pokertool_processes()

    if not pids:
        log("No pokertool processes found - nothing to kill")
        return

    log(f"Found {len(pids)} pokertool process(es) to kill")

    if IS_WINDOWS:
        # Windows: Use taskkill
        for pid in pids:
            try:
                if force:
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)],
                                 capture_output=True, timeout=5)
                    log(f"Force killed PID {pid}")
                else:
                    subprocess.run(['taskkill', '/PID', str(pid)],
                                 capture_output=True, timeout=5)
                    log(f"Killed PID {pid}")
            except Exception as e:
                log(f"Error killing PID {pid}: {e}")

    else:
        # Unix: Use signals
        if force:
            # Immediate SIGKILL
            log("Force killing all processes with SIGKILL...")
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                    log(f"Force killed PID {pid}")
                except (ProcessLookupError, PermissionError) as e:
                    log(f"Could not kill PID {pid}: {e}")

        else:
            # Graceful: SIGTERM -> wait -> SIGKILL
            log("Sending SIGTERM to all processes (graceful shutdown)...")

            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    log(f"Sent SIGTERM to PID {pid}")
                except (ProcessLookupError, PermissionError) as e:
                    log(f"Could not signal PID {pid}: {e}")

            # Wait briefly for graceful shutdown
            log("Waiting 2 seconds for graceful shutdown...")
            time.sleep(2.0)

            # Force kill any remaining processes
            remaining_pids = get_pokertool_processes()
            if remaining_pids:
                log(f"Force killing {len(remaining_pids)} remaining process(es)...")
                for pid in remaining_pids:
                    try:
                        os.kill(pid, 0)  # Check if still running
                        os.kill(pid, signal.SIGKILL)
                        log(f"Force killed stuck PID {pid}")
                    except (ProcessLookupError, PermissionError):
                        pass

    # Final verification
    time.sleep(0.5)
    final_pids = get_pokertool_processes()

    if final_pids:
        log(f"⚠️  Warning: {len(final_pids)} process(es) still running:")
        for pid in final_pids:
            log(f"  - PID {pid}")
        log("You may need to kill these manually or run with --force")
    else:
        log("✓ All pokertool processes terminated successfully")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Kill all running pokertool processes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kill.py              Kill all pokertool processes (graceful)
  python kill.py --force      Force kill immediately (no graceful shutdown)
  python kill.py --list       List processes without killing
        """
    )

    parser.add_argument('--force', action='store_true',
                       help='Force kill immediately with SIGKILL')
    parser.add_argument('--list', action='store_true',
                       help='List processes without killing')

    args = parser.parse_args()

    print("=" * 70)
    print("🔫 PokerTool Process Killer")
    print("=" * 70)
    print()

    try:
        if args.list:
            list_processes()
        else:
            kill_processes(force=args.force)

        print()
        print("=" * 70)
        return 0

    except KeyboardInterrupt:
        log("Interrupted by user")
        return 130

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
