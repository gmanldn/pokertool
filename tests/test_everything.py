#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: test_everything.py
# version: v1.0.0
# last_commit: '2025-10-13T00:00:00Z'
# fixes:
# - date: '2025-10-13'
#   summary: Comprehensive test runner that executes all tests and logs results
# ---
# POKERTOOL-HEADER-END

Comprehensive Test Runner for PokerTool
========================================

This script runs all tests in the project and provides detailed logging and reporting.

Usage:
    python test_everything.py              # Run all tests with logging
    python test_everything.py --verbose    # Run with verbose output
    python test_everything.py --quick      # Run only quick tests (no system tests)
    python test_everything.py --system     # Run only system tests
    python test_everything.py --smoke      # Run only smoke tests (fast validation)
    python test_everything.py --failed     # Run only previously failed tests
    python test_everything.py --coverage   # Run with coverage report
"""

import sys
import os
import argparse
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Setup paths
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / 'src'
TESTS_DIR = ROOT / 'tests'
LOGS_DIR = ROOT / 'test_logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)

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


class TestRunner:
    """Comprehensive test runner with detailed logging."""

    def __init__(self, verbose: bool = False, quick: bool = False, system_only: bool = False, smoke_only: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.system_only = system_only
        self.smoke_only = smoke_only
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = LOGS_DIR / f"test_run_{self.timestamp}.log"
        self.results: Dict[str, Any] = {
            'timestamp': self.timestamp,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_skipped': 0,
            'duration': 0,
            'failures': [],
            'test_files': []
        }

    def log(self, message: str, color: str = ''):
        """Log message to both console and file."""
        # Console output with color
        if color:
            print(f"{color}{message}{Colors.ENDC}")
        else:
            print(message)

        # File output without color codes
        with open(self.log_file, 'a') as f:
            f.write(f"{message}\n")

    def print_header(self):
        """Print test runner header."""
        self.log("=" * 80, Colors.HEADER)
        self.log("POKERTOOL COMPREHENSIVE TEST SUITE", Colors.HEADER + Colors.BOLD)
        self.log("=" * 80, Colors.HEADER)
        self.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Log file: {self.log_file}")
        if self.quick:
            self.log("Mode: QUICK (unit tests only)", Colors.WARNING)
        elif self.system_only:
            self.log("Mode: SYSTEM (system tests only)", Colors.WARNING)
        elif self.smoke_only:
            self.log("Mode: SMOKE (fast validation tests)", Colors.OKCYAN)
        else:
            self.log("Mode: COMPREHENSIVE (all tests)", Colors.OKGREEN)
        self.log("-" * 80)
        self.log("")

    def discover_tests(self) -> List[Path]:
        """Discover all test files."""
        test_files = []

        if self.smoke_only:
            # Only smoke tests
            smoke_test = TESTS_DIR / 'test_smoke_suite.py'
            if smoke_test.exists():
                test_files.append(smoke_test)
        elif self.system_only:
            # Only system tests
            system_dir = TESTS_DIR / 'system'
            if system_dir.exists():
                test_files.extend(system_dir.glob('test_*.py'))
        elif self.quick:
            # Unit tests only (exclude system directory)
            for test_file in TESTS_DIR.glob('test_*.py'):
                test_files.append(test_file)
            # Add GUI tests
            gui_dir = TESTS_DIR / 'gui'
            if gui_dir.exists():
                test_files.extend(gui_dir.glob('test_*.py'))
        else:
            # All tests
            test_files.extend(TESTS_DIR.glob('test_*.py'))
            for subdir in ['system', 'gui', 'specs']:
                test_subdir = TESTS_DIR / subdir
                if test_subdir.exists():
                    test_files.extend(test_subdir.glob('test_*.py'))

        return sorted(test_files)

    def run_pytest(self, test_path: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run pytest with appropriate flags."""
        cmd = [sys.executable, '-m', 'pytest']

        # Add test path or run all
        if test_path:
            cmd.append(str(test_path))
        else:
            cmd.append(str(TESTS_DIR))

        # Add flags
        cmd.extend([
            '-v',  # Verbose
            '--tb=short',  # Short traceback format
            '--color=yes',  # Colored output
        ])

        # Try to add timeout if pytest-timeout is available
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if '--timeout' in result.stdout:
                cmd.extend([
                    '--timeout=300',  # 5 minute timeout per test
                    '--timeout-method=thread',  # Use thread-based timeout
                ])
        except:
            pass  # Skip timeout if not available

        if self.verbose:
            cmd.append('-vv')

        # Add filters based on mode
        if self.smoke_only:
            cmd.extend(['-m', 'smoke'])
        elif self.quick:
            cmd.extend(['-k', 'not system'])
        elif self.system_only:
            cmd.append(str(TESTS_DIR / 'system'))

        # Set environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(SRC_DIR)
        env['POKERTOOL_TEST_MODE'] = '1'  # Suppress GUI popups during tests

        return subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True
        )

    def run_coverage(self) -> subprocess.CompletedProcess:
        """Run tests with coverage."""
        cmd = [
            sys.executable, '-m', 'pytest',
            '--cov=src/pokertool',
            '--cov-report=html:test_logs/coverage_html',
            '--cov-report=term-missing',
            '-v'
        ]

        if self.quick:
            cmd.extend(['-k', 'not system'])

        env = os.environ.copy()
        env['PYTHONPATH'] = str(SRC_DIR)
        env['POKERTOOL_TEST_MODE'] = '1'  # Suppress GUI popups during tests

        return subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True
        )

    def parse_pytest_output(self, output: str) -> None:
        """Parse pytest output for results."""
        lines = output.split('\n')

        for line in lines:
            # Count test results
            if 'passed' in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'passed' in part.lower() and i > 0:
                            self.results['tests_passed'] = int(parts[i-1])
                except:
                    pass

            if 'failed' in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'failed' in part.lower() and i > 0:
                            self.results['tests_failed'] = int(parts[i-1])
                except:
                    pass

            if 'skipped' in line.lower():
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'skipped' in part.lower() and i > 0:
                            self.results['tests_skipped'] = int(parts[i-1])
                except:
                    pass

            # Extract failure details
            if 'FAILED' in line:
                self.results['failures'].append(line.strip())

    def print_summary(self):
        """Print test summary."""
        total = self.results['tests_passed'] + self.results['tests_failed'] + self.results['tests_skipped']
        self.results['tests_run'] = total

        self.log("")
        self.log("=" * 80, Colors.HEADER)
        self.log("TEST SUMMARY", Colors.HEADER + Colors.BOLD)
        self.log("=" * 80, Colors.HEADER)
        self.log("")

        self.log(f"Total Tests Run:  {total}")
        self.log(f"✅ Passed:        {self.results['tests_passed']}", Colors.OKGREEN)
        self.log(f"❌ Failed:        {self.results['tests_failed']}", Colors.FAIL if self.results['tests_failed'] > 0 else '')
        self.log(f"⏭️  Skipped:       {self.results['tests_skipped']}", Colors.WARNING if self.results['tests_skipped'] > 0 else '')

        if total > 0:
            pass_rate = (self.results['tests_passed'] / total) * 100
            self.log(f"Pass Rate:        {pass_rate:.1f}%")

        self.log("")

        # Print failures if any
        if self.results['failures']:
            self.log("FAILED TESTS:", Colors.FAIL + Colors.BOLD)
            self.log("-" * 80)
            for failure in self.results['failures']:
                self.log(f"  {failure}", Colors.FAIL)
            self.log("")

        # Print log locations
        self.log("LOGS AND REPORTS:", Colors.OKCYAN + Colors.BOLD)
        self.log("-" * 80)
        self.log(f"  Detailed log: {self.log_file}")
        self.log(f"  All logs:     {LOGS_DIR}/")
        self.log("")

        # Final status
        if self.results['tests_failed'] == 0:
            self.log("✅ ALL TESTS PASSED!", Colors.OKGREEN + Colors.BOLD)
        else:
            self.log("❌ SOME TESTS FAILED - SEE DETAILS ABOVE", Colors.FAIL + Colors.BOLD)

        self.log("=" * 80, Colors.HEADER)

    def save_results_json(self):
        """Save results to JSON file."""
        json_file = LOGS_DIR / f"test_results_{self.timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"  JSON results: {json_file}")

    def run(self, with_coverage: bool = False):
        """Run all tests."""
        self.print_header()

        # Discover tests
        test_files = self.discover_tests()
        self.log(f"Found {len(test_files)} test files")
        self.log("")

        # Run pytest
        self.log("Running pytest...", Colors.OKBLUE)
        self.log("-" * 80)
        self.log("")

        start_time = datetime.now()

        if with_coverage:
            result = self.run_coverage()
        else:
            result = self.run_pytest()

        end_time = datetime.now()
        self.results['duration'] = (end_time - start_time).total_seconds()

        # Log pytest output
        self.log("PYTEST OUTPUT:", Colors.OKCYAN)
        self.log("-" * 80)
        self.log(result.stdout)

        if result.stderr:
            self.log("")
            self.log("STDERR:", Colors.WARNING)
            self.log("-" * 80)
            self.log(result.stderr)

        # Parse results
        self.parse_pytest_output(result.stdout)

        # Print summary
        self.print_summary()

        # Save JSON results
        self.save_results_json()

        return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PokerTool Comprehensive Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_everything.py              # Run all tests
  python test_everything.py --verbose    # Verbose output
  python test_everything.py --quick      # Quick tests only (no system tests)
  python test_everything.py --system     # System tests only
  python test_everything.py --smoke      # Smoke tests only (fast validation)
  python test_everything.py --coverage   # Run with coverage report
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-q', '--quick', action='store_true',
                        help='Run only quick tests (exclude system tests)')
    parser.add_argument('-s', '--system', action='store_true',
                        help='Run only system tests')
    parser.add_argument('--smoke', action='store_true',
                        help='Run only smoke tests (fast validation)')
    parser.add_argument('-c', '--coverage', action='store_true',
                        help='Run with coverage report')
    parser.add_argument('-f', '--failed', action='store_true',
                        help='Run only previously failed tests (requires pytest-rerunfailures)')

    args = parser.parse_args()

    # Check for pytest
    try:
        subprocess.run([sys.executable, '-m', 'pytest', '--version'],
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}ERROR: pytest is not installed{Colors.ENDC}")
        print(f"Install with: pip install pytest pytest-timeout")
        if args.coverage:
            print(f"For coverage: pip install pytest-cov")
        return 1

    # Create and run test runner
    runner = TestRunner(
        verbose=args.verbose,
        quick=args.quick,
        system_only=args.system,
        smoke_only=args.smoke
    )

    exit_code = runner.run(with_coverage=args.coverage)

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
