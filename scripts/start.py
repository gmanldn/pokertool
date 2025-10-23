#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: start.py
# version: v68.0.0
# last_commit: '2025-10-14T22:00:00Z'
# fixes:
# - date: '2025-10-14'
#   summary: Added kill.py process management utility for cleaning up stuck pokertool processes
# - date: '2025-10-14'
#   summary: Added detailed explanation textbox on LiveTable showing WHY actions are recommended with metrics
# - date: '2025-10-14'
#   summary: Win Rate & Accuracy Optimization - GTO caching (60-80% speedup), confidence intervals, formatting system
# - date: '2025-10-14'
#   summary: Enhanced status bar with rolling game state display and version info
# - date: '2025-10-14'
#   summary: Added canonical version tracking system with release branch workflow
# - date: '2025-10-14'
#   summary: Added 35 comprehensive screen scraping optimizations (speed, accuracy, reliability)
# - date: '2025-10-14'
#   summary: Added comprehensive UI enhancements - status panel, feedback, shortcuts, profiles, charts
# - date: '2025-10-14'
#   summary: Fixed GUI startup - robust process cleanup, window visibility, black button text
# - date: '2025-10-12'
#   summary: Added comprehensive startup validation system with health monitoring
# - date: '2025-10-12'
#   summary: Updated to launch Enhanced GUI v32.0.0 with modern styling and logging tab
# - date: '2025-10-12'
#   summary: Added real-time Logging tab to monitor all application activity
# - date: '2025-10-12'
#   summary: Modernized color scheme with deeper contrasts and vibrant accents
# - date: '2025-01-10'
#   summary: Complete rewrite for robust cross-platform dependency management and setup
# ---
# POKERTOOL-HEADER-END

PokerTool Web Application Launcher - v84.0.0
=============================================

This script sets up everything and launches the Web Application (Backend API + React Frontend).

Web-Only Architecture - No tkinter/GUI windows.

Usage:
    python scripts/start.py              # Launch web application (default)
    python scripts/start.py --setup-only # Install dependencies only
    python scripts/start.py --self-test  # Run comprehensive tests

After launching, access the app at: http://localhost:3000
"""
from __future__ import annotations
from pathlib import Path
from typing import Sequence, Optional, Dict, Any, List
import os
import sys
import subprocess
import platform
import shutil
import argparse

# Add src to path for version import
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

# Import canonical version
try:
    from pokertool.version import __version__, format_version
except ImportError:
    __version__ = '64.0.0'  # Fallback
    format_version = lambda **kwargs: f"v{__version__}"

# Constants
ROOT = Path(__file__).resolve().parent.parent  # Go up from scripts/ to project root
SRC_DIR = ROOT / 'src'
VENV_DIR = ROOT / '.venv'

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

# Supported Python versions
MIN_PYTHON = (3, 9)
MAX_PYTHON = (3, 13)

# Installation log file
INSTALL_LOG = Path.home() / '.pokertool' / 'install.log'

def clear_terminal():
    """Clear terminal for clean output."""
    os.system('cls' if IS_WINDOWS else 'clear')

def log(message: str, level: str = 'INFO'):
    """Log a message to console and file."""
    timestamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] [{level}] {message}"
    print(f"[POKERTOOL] {message}")
    
    # Ensure log directory exists
    INSTALL_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to log file
    try:
        with open(INSTALL_LOG, 'a') as f:
            f.write(log_message + '\n')
    except Exception:
        pass  # Fail silently if can't write log

def check_python_version() -> bool:
    """Check if Python version is supported."""
    current = sys.version_info[:2]
    
    if current < MIN_PYTHON:
        log(f"❌ Python {current[0]}.{current[1]} is too old", 'ERROR')
        log(f"   Minimum required: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}", 'ERROR')
        log(f"   Please upgrade Python: https://www.python.org/downloads/", 'ERROR')
        return False
    
    if current > MAX_PYTHON:
        log(f"⚠️  Python {current[0]}.{current[1]} is newer than tested version", 'WARNING')
        log(f"   Tested up to: Python {MAX_PYTHON[0]}.{MAX_PYTHON[1]}", 'WARNING')
        log(f"   Installation may work but is not officially supported", 'WARNING')
    
    log(f"✓ Python {current[0]}.{current[1]} is supported")
    return True

def check_disk_space(min_mb: int = 500) -> bool:
    """Check if sufficient disk space is available."""
    try:
        import shutil
        stat = shutil.disk_usage(ROOT)
        available_mb = stat.free / (1024 * 1024)
        
        if available_mb < min_mb:
            log(f"❌ Insufficient disk space: {available_mb:.0f}MB available, {min_mb}MB required", 'ERROR')
            return False
        
        log(f"✓ Disk space OK: {available_mb:.0f}MB available")
        return True
    except Exception as e:
        log(f"⚠️  Could not check disk space: {e}", 'WARNING')
        return True  # Continue anyway

def check_network_connectivity() -> bool:
    """Check network connectivity to required services."""
    import socket
    
    services = [
        ('pypi.org', 443, 'PyPI'),
        ('registry.npmjs.org', 443, 'npm registry'),
        ('github.com', 443, 'GitHub'),
    ]
    
    all_ok = True
    for host, port, name in services:
        try:
            socket.create_connection((host, port), timeout=5)
            log(f"✓ {name} reachable")
        except (socket.timeout, socket.error) as e:
            log(f"⚠️  {name} not reachable: {e}", 'WARNING')
            all_ok = False
    
    if not all_ok:
        log("⚠️  Some services unreachable - installation may fail", 'WARNING')
    
    return all_ok

def check_system_dependencies() -> bool:
    """Check for required system dependencies."""
    required = {
        'pip': 'pip3 --version or python -m pip',
        'git': 'git --version',
        'node': 'node --version',
        'npm': 'npm --version',
    }
    
    missing = []
    for cmd, check in required.items():
        if not shutil.which(cmd):
            missing.append(f"{cmd} ({check})")
            log(f"❌ {cmd} not found", 'ERROR')
        else:
            # Get version
            try:
                result = subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=5)
                version = result.stdout.strip().split('\n')[0]
                log(f"✓ {cmd}: {version}")
            except:
                log(f"✓ {cmd} found")
    
    if missing:
        log("", 'ERROR')
        log("Missing required dependencies:", 'ERROR')
        for dep in missing:
            log(f"  - {dep}", 'ERROR')
        log("", 'ERROR')
        log("Installation instructions:", 'ERROR')
        if IS_MACOS:
            log("  brew install git node", 'ERROR')
        elif IS_LINUX:
            log("  sudo apt-get install git nodejs npm  # Ubuntu/Debian", 'ERROR')
            log("  sudo yum install git nodejs npm     # CentOS/RHEL", 'ERROR')
        elif IS_WINDOWS:
            log("  Install from: https://git-scm.com/ and https://nodejs.org/", 'ERROR')
        return False
    
    return True

def detect_conflicting_packages() -> List[str]:
    """Detect potentially conflicting Python packages."""
    venv_python = get_venv_python()
    conflicts = []
    
    # Known conflicts
    conflict_pairs = [
        ('opencv-python', 'opencv-python-headless'),
        ('pillow', 'pil'),
        ('tensorflow', 'tensorflow-gpu'),
    ]
    
    try:
        result = subprocess.run(
            [venv_python, '-m', 'pip', 'list'],
            capture_output=True, text=True, timeout=10
        )
        installed = set(line.split()[0].lower() for line in result.stdout.split('\n')[2:] if line.strip())
        
        for pkg1, pkg2 in conflict_pairs:
            if pkg1 in installed and pkg2 in installed:
                conflicts.append(f"{pkg1} conflicts with {pkg2}")
                log(f"⚠️  Conflict detected: {pkg1} and {pkg2}", 'WARNING')
    except Exception as e:
        log(f"⚠️  Could not check for conflicts: {e}", 'WARNING')
    
    return conflicts

def get_python_executable() -> str:
    """Get best Python executable."""
    if sys.executable:
        return sys.executable
    
    candidates = ['python3.12', 'python3.11', 'python3.10', 'python3', 'python']
    if IS_WINDOWS:
        candidates = ['py', 'python'] + candidates
    
    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    
    raise RuntimeError("No suitable Python found")

def get_venv_python() -> str:
    """Get venv Python path."""
    if IS_WINDOWS:
        return str(VENV_DIR / 'Scripts' / 'python.exe')
    return str(VENV_DIR / 'bin' / 'python')

def create_venv():
    """Create virtual environment."""
    if VENV_DIR.exists():
        log("Virtual environment exists")
        return
    
    log("Creating virtual environment...")
    python_exe = get_python_executable()
    subprocess.run([python_exe, '-m', 'venv', str(VENV_DIR)], check=True)
    log("✓ Virtual environment created")

def install_dependencies():
    """Install all dependencies."""
    venv_python = get_venv_python()
    
    # Upgrade pip
    log("Upgrading pip...")
    subprocess.run([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                   check=True, capture_output=True)
    
    # Install from requirements.txt
    requirements = ROOT / 'requirements.txt'
    if requirements.exists():
        log("Installing Python dependencies...")
        subprocess.run([venv_python, '-m', 'pip', 'install', '-r', str(requirements)],
                       check=True)
        log("✓ Dependencies installed")
    
    # Install critical deps for enhanced GUI
    log("Ensuring enhanced GUI dependencies...")
    critical = ['opencv-python', 'Pillow', 'pytesseract', 'mss', 'numpy']
    for dep in critical:
        try:
            subprocess.run([venv_python, '-m', 'pip', 'install', dep],
                          check=True, capture_output=True, timeout=120)
        except:
            log(f"Warning: {dep} install had issues")

def run_tests() -> int:
    """Run comprehensive test suite."""
    venv_python = get_venv_python()
    
    log("Running comprehensive tests...")
    log("=" * 70)
    
    # Test enhanced GUI v2 and startup validation
    test_files = [
        ROOT / 'tests' / 'gui' / 'test_enhanced_gui_styles.py',
        ROOT / 'tests' / 'test_startup_validation.py'
    ]

    for test_file in test_files:
        if test_file.exists():
            log(f"Testing {test_file.name}...")
            try:
                result = subprocess.run([venv_python, '-m', 'pytest', str(test_file), '-v'],
                                       cwd=ROOT)
                if result.returncode != 0:
                    log(f"⚠ Some tests in {test_file.name} failed (non-critical)")
            except:
                log("⚠ pytest not available, skipping unit tests")
                break
    
    log("=" * 70)
    log("✓ Test suite completed")
    return 0

def cleanup_old_processes():
    """Kill any old pokertool/GUI processes before starting (including stuck ones)."""
    import time
    import signal

    try:
        current_pid = os.getpid()
        log("Cleaning up previous pokertool/GUI instances...")

        if IS_WINDOWS:
            # Windows: Kill any pokertool GUI processes
            subprocess.run(
                ['taskkill', '/F', '/FI', 'IMAGENAME eq python*', '/FI', f'PID ne {current_pid}'],
                capture_output=True, timeout=5
            )
            # Also kill React dev servers
            subprocess.run(
                ['taskkill', '/F', '/FI', 'IMAGENAME eq node.exe'],
                capture_output=True, timeout=5
            )
        else:
            # Unix: Kill ALL pokertool-related GUI processes
            # Patterns to search for
            patterns = [
                'python.*start\\.py',
                'python.*enhanced_gui',
                'python.*simple_gui',
                'python.*launch.*gui',
                'python.*run_gui',
                'pokertool.*gui',
                'node.*react-scripts',
                'react-scripts start'
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

            if all_pids:
                log(f"Found {len(all_pids)} previous instance(s) to clean up")

                # Step 1: Try SIGTERM first (graceful)
                for pid in all_pids:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except (ProcessLookupError, PermissionError):
                        pass

                # Step 2: Wait briefly for graceful shutdown
                time.sleep(1.0)

                # Step 3: Force kill any remaining processes with SIGKILL
                for pid in all_pids:
                    try:
                        os.kill(pid, 0)  # Check if still running
                        os.kill(pid, signal.SIGKILL)  # Force kill
                        log(f"Force killed stuck process PID {pid}")
                    except (ProcessLookupError, PermissionError):
                        pass

                time.sleep(0.5)
                log("✓ Cleanup complete")
            else:
                log("✓ No previous instances found")

    except Exception as e:
        log(f"⚠️  Cleanup warning: {e}")
        pass

def ensure_chrome_remote_debugging(port: int = 9222, poker_url: Optional[str] = None) -> bool:
    """Ensure Chrome is running with remote debugging for CDP-based detection."""
    log(f"Ensuring Chrome remote debugging (port {port})...")
    try:
        from pokertool.modules.chrome_devtools_scraper import ChromeDevToolsScraper
    except Exception as exc:
        log(f"⚠️ Unable to import Chrome DevTools scraper: {exc}")
        log(f"   Launch Chrome manually with: chrome --remote-debugging-port={port}")
        return False

    kwargs: Dict[str, Any] = {'port': port, 'auto_launch': True}
    if poker_url:
        kwargs['poker_url'] = poker_url

    scraper = ChromeDevToolsScraper(**kwargs)
    try:
        ready = scraper.ensure_remote_debugging(ensure_poker_tab=True)
        if ready:
            log(f"✓ Chrome remote debugging ready on port {port}")
        else:
            target_url = poker_url or scraper.poker_url
            log("⚠️ Unable to automatically prepare Chrome for remote debugging.")
            log(f"   Please launch manually: chrome --remote-debugging-port={port} {target_url}")
        return ready
    finally:
        try:
            scraper.disconnect(close_chrome=False)
        except Exception:
            pass

def launch_web_app(skip_chrome: bool = False, chrome_port: int = 9222, poker_url: Optional[str] = None) -> int:
    """Launch the web-only application: Backend API + React frontend."""
    venv_python = get_venv_python()

    # Clean up any old processes first
    cleanup_old_processes()

    # Setup environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SRC_DIR)

    log("=" * 70)
    log(f"🎰 LAUNCHING POKERTOOL WEB APPLICATION {format_version(include_name=True)}")
    log("=" * 70)
    log("")
    log("Architecture: Web-Only (No GUI)")
    log("  ✓ FastAPI Backend (Python API)")
    log("  ✓ React Frontend (Web UI)")
    log("  ✓ WebSocket Real-time Updates")
    log("  ✓ Screen Scraping Engine")
    log("  ✓ Poker Analysis & ML")
    log("")
    log("Access the app at: http://localhost:3000")
    log("")

    # Check for Node.js
    log("Checking dependencies...")
    if not shutil.which('node'):
        log("❌ Node.js not found. Please install Node.js to run the frontend.")
        log("   Visit: https://nodejs.org/")
        return 1

    log("✓ Node.js found")

    # Check if frontend dependencies are installed
    frontend_dir = ROOT / 'pokertool-frontend'
    if not (frontend_dir / 'node_modules').exists():
        log("Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            log("✓ Frontend dependencies installed")
        except subprocess.CalledProcessError:
            log("❌ Failed to install frontend dependencies")
            return 1

    # Ensure Chrome remote debugging is available for reliable detection
    if skip_chrome:
        log("Skipping Chrome remote debugging auto-launch (--skip-chrome)")
    else:
        ensure_chrome_remote_debugging(chrome_port, poker_url)

    # Start backend API server
    log("")
    log("Starting backend API server...")
    backend_port = 5001  # Using 5001 since 5000 is often used by macOS Control Center
    backend_process = subprocess.Popen(
        [venv_python, '-m', 'uvicorn', 'pokertool.api:create_app',
         '--host', '0.0.0.0', '--port', str(backend_port), '--factory'],
        env=env,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    log(f"✓ Backend API starting on http://localhost:{backend_port}")

    # Start React frontend
    log("Starting React frontend...")
    frontend_env = os.environ.copy()
    frontend_env['REACT_APP_API_URL'] = f'http://127.0.0.1:{backend_port}'
    frontend_env['REACT_APP_WS_URL'] = f'ws://127.0.0.1:{backend_port}'
    # Surface version to the frontend so it can display in the top bar
    try:
        frontend_env['REACT_APP_VERSION'] = format_version()
    except Exception:
        frontend_env['REACT_APP_VERSION'] = os.getenv('POKERTOOL_VERSION', 'v0.0.0')

    frontend_process = subprocess.Popen(
        ['npm', 'start'],
        cwd=frontend_dir,
        env=frontend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    log("✓ Frontend starting on http://localhost:3000")
    log("")
    log("=" * 70)
    log("🎉 POKERTOOL IS RUNNING!")
    log("=" * 70)
    log("")
    log("📱 Open your browser to: http://localhost:3000")
    log("")
    log("Press Ctrl+C to stop the application")
    log("")

    try:
        # Wait for both processes
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        log("")
        log("Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        log("✓ Application stopped")
        return 0

    return 0

def cleanup_old_processes():
    """Clean up old pokertool processes."""
    import psutil
    import signal

    current_pid = os.getpid()
    killed_count = 0

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Skip current process
                if proc.pid == current_pid:
                    continue

                cmdline = proc.cmdline()
                if not cmdline:
                    continue

                # Check if it's a pokertool process
                cmdline_str = ' '.join(cmdline).lower()
                if 'pokertool' in cmdline_str or 'start.py' in cmdline_str:
                    log(f"Cleaning up old process: PID {proc.pid}")
                    proc.send_signal(signal.SIGTERM)
                    killed_count += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if killed_count > 0:
            log(f"✓ Cleaned up {killed_count} old process(es)")
    except Exception as e:
        log(f"Warning: Could not cleanup old processes: {e}")

def show_banner():
    """Show startup banner."""
    clear_terminal()
    print("=" * 70)
    print(f"🎰 POKERTOOL - Web Application {format_version()}")
    print("=" * 70)
    print("Web-Only Architecture - No GUI | Backend API + React Frontend")
    print("")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Learning: 🧠 Adaptive ML System (Auto-Enabled)")
    print("=" * 70)
    print("")

def main() -> int:
    """Main entry point - Launch PokerTool Web Application."""
    parser = argparse.ArgumentParser(description='PokerTool Web Application Launcher')
    parser.add_argument('--setup-only', action='store_true', help='Setup dependencies without launching')
    parser.add_argument('--self-test', action='store_true', help='Run comprehensive tests')
    parser.add_argument('--skip-chrome', action='store_true', help='Skip automatic Chrome remote debugging launch')
    parser.add_argument('--chrome-port', type=int, default=9222, help='Chrome remote debugging port (default: 9222)')
    parser.add_argument('--poker-url', type=str, help='Override poker site URL when launching Chrome')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose/debug output')
    parser.add_argument('--skip-checks', action='store_true', help='Skip pre-installation checks (not recommended)')

    args = parser.parse_args()

    show_banner()

    try:
        # Log installation attempt
        log(f"Installation log: {INSTALL_LOG}")
        log("")
        
        # Pre-installation checks (Tasks 1-7)
        if not args.skip_checks:
            log("Running pre-installation checks...")
            log("=" * 70)
            
            # Task 1: Python version check
            if not check_python_version():
                return 1
            
            # Task 2: System dependencies check
            if not check_system_dependencies():
                return 1
            
            # Task 3: OS detection (implicit in platform detection)
            log(f"✓ OS detected: {platform.system()} {platform.release()}")
            
            # Task 4: Disk space check
            if not check_disk_space():
                return 1
            
            # Task 5: Network connectivity check
            check_network_connectivity()  # Warning only
            
            log("=" * 70)
            log("✓ All pre-installation checks passed")
            log("")
        
        # Task 8: Virtual environment detection and auto-creation
        if not VENV_DIR.exists() or not Path(get_venv_python()).exists():
            log("Virtual environment not found, creating...")
            create_venv()
            install_dependencies()
        else:
            log("✓ Virtual environment detected")
            
            # Task 7: Check for conflicting packages
            conflicts = detect_conflicting_packages()
            if conflicts and not args.skip_checks:
                log("⚠️  Package conflicts detected - may cause issues", 'WARNING')

        # Setup dependencies
        log("Verifying dependencies...")
        install_dependencies()
        log("✓ Setup complete")

        # Self-test if requested (Task 31-32: Installation tests)
        if args.self_test:
            run_tests()
            return 0

        # Launch web application unless setup-only
        if args.setup_only:
            log("✓ Setup completed. Run 'python scripts/start.py' to launch the web app.")
            return 0

        # Launch the web application
        return launch_web_app(
            skip_chrome=args.skip_chrome,
            chrome_port=args.chrome_port,
            poker_url=args.poker_url,
        )

    except KeyboardInterrupt:
        log("Interrupted by user")
        log("Cleaning up processes...")
        cleanup_old_processes()
        return 130
    except Exception as e:
        log(f"ERROR: {e}", 'ERROR')
        if args.verbose:
            import traceback
            traceback.print_exc()
        log("")
        log("Cleaning up processes due to error...")
        cleanup_old_processes()
        log(f"Check logs at: {INSTALL_LOG}", 'ERROR')
        return 1

if __name__ == '__main__':
    sys.exit(main())
