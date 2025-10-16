#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone Smoke Test Runner for PokerTool
===========================================

This script provides a comprehensive smoke test runner that can:
- Start backend and frontend services if needed
- Run all smoke tests
- Generate detailed reports
- Clean up processes on completion
- Provide CI/CD-friendly exit codes

Module: scripts.run_smoke_tests
Version: 1.0.0
Last Modified: 2025-10-16

Usage:
    python scripts/run_smoke_tests.py              # Run all smoke tests
    python scripts/run_smoke_tests.py --quick      # Run quick smoke tests only
    python scripts/run_smoke_tests.py --no-start   # Don't start services (assume already running)
    python scripts/run_smoke_tests.py --verbose    # Verbose output
    python scripts/run_smoke_tests.py --report     # Generate HTML report

Exit Codes:
    0  - All smoke tests passed
    1  - Some smoke tests failed
    2  - Error starting services
    3  - Test execution error
"""

import os
import sys
import time
import signal
import socket
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / 'src'
TESTS_DIR = PROJECT_ROOT / 'tests'
LOGS_DIR = PROJECT_ROOT / 'test_logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

# Add src to path
sys.path.insert(0, str(SRC_DIR))

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log(message: str, color: str = ''):
    """Log a message with optional color."""
    if color:
        print(f"{color}{message}{Colors.ENDC}")
    else:
        print(message)


def is_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True


def wait_for_port(port: int, timeout: int = 30) -> bool:
    """Wait for a port to become available (service to start)."""
    log(f"Waiting for port {port} to be ready...", Colors.OKCYAN)
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            log(f"✓ Port {port} is ready", Colors.OKGREEN)
            return True
        time.sleep(0.5)
    log(f"✗ Port {port} did not become ready in {timeout}s", Colors.FAIL)
    return False


class ServiceManager:
    """Manage backend and frontend services."""

    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_port = 5001
        self.frontend_port = 3000

    def is_backend_running(self) -> bool:
        """Check if backend is already running."""
        return is_port_in_use(self.backend_port)

    def is_frontend_running(self) -> bool:
        """Check if frontend is already running."""
        return is_port_in_use(self.frontend_port)

    def start_backend(self) -> bool:
        """Start the backend API server."""
        if self.is_backend_running():
            log("Backend already running", Colors.WARNING)
            return True

        log("Starting backend API server...", Colors.OKBLUE)

        venv_python = str(PROJECT_ROOT / '.venv' / 'bin' / 'python')
        env = os.environ.copy()
        env['PYTHONPATH'] = str(SRC_DIR)

        try:
            self.backend_process = subprocess.Popen(
                [venv_python, '-m', 'uvicorn', 'pokertool.api:create_app',
                 '--host', '0.0.0.0', '--port', str(self.backend_port), '--factory'],
                env=env,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            # Wait for backend to be ready
            if wait_for_port(self.backend_port, timeout=30):
                log("✓ Backend started successfully", Colors.OKGREEN)
                return True
            else:
                log("✗ Backend failed to start", Colors.FAIL)
                self.stop_backend()
                return False

        except Exception as e:
            log(f"✗ Error starting backend: {e}", Colors.FAIL)
            return False

    def start_frontend(self) -> bool:
        """Start the frontend development server."""
        if self.is_frontend_running():
            log("Frontend already running", Colors.WARNING)
            return True

        log("Starting frontend server...", Colors.OKBLUE)

        frontend_dir = PROJECT_ROOT / 'pokertool-frontend'
        if not frontend_dir.exists():
            log("✗ Frontend directory not found", Colors.FAIL)
            return False

        # Check if node_modules exists
        if not (frontend_dir / 'node_modules').exists():
            log("Installing frontend dependencies...", Colors.OKCYAN)
            try:
                subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True,
                             capture_output=True, timeout=300)
            except subprocess.CalledProcessError as e:
                log(f"✗ Failed to install frontend dependencies: {e}", Colors.FAIL)
                return False

        try:
            env = os.environ.copy()
            env['REACT_APP_API_URL'] = f'http://localhost:{self.backend_port}'

            self.frontend_process = subprocess.Popen(
                ['npm', 'start'],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )

            # Wait for frontend to be ready
            if wait_for_port(self.frontend_port, timeout=60):
                log("✓ Frontend started successfully", Colors.OKGREEN)
                return True
            else:
                log("✗ Frontend failed to start", Colors.FAIL)
                self.stop_frontend()
                return False

        except Exception as e:
            log(f"✗ Error starting frontend: {e}", Colors.FAIL)
            return False

    def stop_backend(self):
        """Stop the backend server."""
        if self.backend_process:
            log("Stopping backend...", Colors.OKCYAN)
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            self.backend_process = None
            log("✓ Backend stopped", Colors.OKGREEN)

    def stop_frontend(self):
        """Stop the frontend server."""
        if self.frontend_process:
            log("Stopping frontend...", Colors.OKCYAN)
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            self.frontend_process = None
            log("✓ Frontend stopped", Colors.OKGREEN)

    def stop_all(self):
        """Stop all services."""
        self.stop_backend()
        self.stop_frontend()


class SmokeTestRunner:
    """Run smoke tests and generate reports."""

    def __init__(self, verbose: bool = False, quick: bool = False,
                 generate_report: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.generate_report = generate_report
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = LOGS_DIR / f"smoke_test_{self.timestamp}.log"
        self.results: Dict[str, Any] = {
            'timestamp': self.timestamp,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'duration': 0,
            'success': False
        }

    def print_banner(self):
        """Print test runner banner."""
        log("=" * 80, Colors.HEADER)
        log("POKERTOOL SMOKE TEST SUITE", Colors.HEADER + Colors.BOLD)
        log("=" * 80, Colors.HEADER)
        log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"Log file: {self.log_file}")
        if self.quick:
            log("Mode: QUICK", Colors.WARNING)
        else:
            log("Mode: COMPREHENSIVE", Colors.OKGREEN)
        log("-" * 80)
        log("")

    def run_tests(self) -> int:
        """Run the smoke tests."""
        self.print_banner()

        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            str(TESTS_DIR / 'test_smoke_suite.py'),
            '-v',
            '-m', 'smoke',
            '--tb=short',
            f'--log-file={self.log_file}',
        ]

        if self.verbose:
            cmd.append('-vv')

        if self.generate_report:
            report_file = LOGS_DIR / f'smoke_test_report_{self.timestamp}.html'
            cmd.extend(['--html', str(report_file), '--self-contained-html'])

        # Set environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(SRC_DIR)
        env['POKERTOOL_TEST_MODE'] = '1'

        # Run tests
        log("Running smoke tests...", Colors.OKBLUE)
        log("-" * 80)
        log("")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=False  # Show output in real-time
            )

            end_time = time.time()
            self.results['duration'] = end_time - start_time

            # Parse results from exit code
            if result.returncode == 0:
                self.results['success'] = True
                log("")
                log("=" * 80, Colors.OKGREEN)
                log("✅ ALL SMOKE TESTS PASSED!", Colors.OKGREEN + Colors.BOLD)
                log("=" * 80, Colors.OKGREEN)
            else:
                self.results['success'] = False
                log("")
                log("=" * 80, Colors.FAIL)
                log("❌ SOME SMOKE TESTS FAILED", Colors.FAIL + Colors.BOLD)
                log("=" * 80, Colors.FAIL)

            log("")
            log(f"Duration: {self.results['duration']:.2f} seconds")
            log(f"Log file: {self.log_file}")

            if self.generate_report:
                log(f"HTML report: {report_file}")

            log("")

            return result.returncode

        except Exception as e:
            log(f"✗ Error running tests: {e}", Colors.FAIL)
            return 3


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PokerTool Smoke Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_smoke_tests.py              # Run all smoke tests
  python scripts/run_smoke_tests.py --quick      # Quick tests only
  python scripts/run_smoke_tests.py --no-start   # Don't start services
  python scripts/run_smoke_tests.py --verbose    # Verbose output
  python scripts/run_smoke_tests.py --report     # Generate HTML report
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-q', '--quick', action='store_true',
                       help='Run quick tests only')
    parser.add_argument('--no-start', action='store_true',
                       help="Don't start services (assume already running)")
    parser.add_argument('--no-backend', action='store_true',
                       help="Don't start backend server")
    parser.add_argument('--no-frontend', action='store_true',
                       help="Don't start frontend server")
    parser.add_argument('--report', action='store_true',
                       help='Generate HTML report')

    args = parser.parse_args()

    # Initialize service manager
    service_manager = ServiceManager()

    # Start services if needed
    services_started = False
    if not args.no_start:
        try:
            if not args.no_backend:
                if not service_manager.start_backend():
                    log("Failed to start backend", Colors.FAIL)
                    return 2
                services_started = True

            # Frontend is optional for smoke tests
            # if not args.no_frontend:
            #     if not service_manager.start_frontend():
            #         log("Warning: Failed to start frontend", Colors.WARNING)

        except KeyboardInterrupt:
            log("\nInterrupted by user", Colors.WARNING)
            service_manager.stop_all()
            return 130

    # Run smoke tests
    try:
        runner = SmokeTestRunner(
            verbose=args.verbose,
            quick=args.quick,
            generate_report=args.report
        )

        exit_code = runner.run_tests()

        return exit_code

    except KeyboardInterrupt:
        log("\nInterrupted by user", Colors.WARNING)
        return 130

    finally:
        # Clean up services if we started them
        if services_started and not args.no_start:
            log("")
            log("Cleaning up services...", Colors.OKCYAN)
            service_manager.stop_all()
            log("✓ Cleanup complete", Colors.OKGREEN)


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
