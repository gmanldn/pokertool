#!/usr/bin/env python3
"""
PokerTool Test Runner

Orchestrates the complete test cycle for PokerTool:
1. Updates architecture graph database
2. Runs architecture validation tests
3. Runs all unit and integration tests

Usage:
    python test.py              # Run all tests with graph update
    python test.py --no-graph   # Skip graph update
    python test.py --quick      # Quick tests only (skip slow tests)
    python test.py --coverage   # Run with coverage report
"""

import sys
import subprocess
import argparse
from pathlib import Path


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_command(cmd, description, fail_fast=True):
    """
    Run a command and handle errors.

    Args:
        cmd: Command to run (list)
        description: Human-readable description
        fail_fast: If True, exit on failure. If False, continue.

    Returns:
        True if successful, False otherwise
    """
    print(f">>> {description}")
    print(f"    Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=Path.cwd())

    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        if fail_fast:
            sys.exit(result.returncode)
        return False
    else:
        print(f"\n✓ {description} completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Run PokerTool test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py                    # Full test cycle with graph update
  python test.py --no-graph         # Skip graph database update
  python test.py --quick            # Quick tests only
  python test.py --coverage         # Run with coverage report
  python test.py --architecture     # Only architecture tests
        """
    )

    parser.add_argument(
        '--no-graph',
        action='store_true',
        help='Skip architecture graph database update'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (skip slow tests)'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage report'
    )

    parser.add_argument(
        '--architecture',
        action='store_true',
        help='Run only architecture graph tests'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Determine pytest executable
    pytest_cmd = ['.venv/bin/pytest']

    # Build pytest arguments
    pytest_args = []

    if args.verbose:
        pytest_args.append('-v')

    if args.quick:
        pytest_args.extend(['-m', 'not slow'])

    if args.coverage:
        pytest_args.extend(['--cov=src/pokertool', '--cov-report=html', '--cov-report=term'])

    # ========================================================================
    # Step 1: Update Architecture Graph Database
    # ========================================================================

    if not args.no_graph:
        print_section("Step 1: Updating Architecture Graph Database")

        success = run_command(
            ['.venv/bin/python', '-m', 'tests.architecture.graph_builder'],
            "Architecture graph database update",
            fail_fast=False
        )

        if not success:
            print("\n⚠️  Warning: Graph update failed, but continuing with tests...")
            print("    Tests will use existing graph data.\n")
    else:
        print_section("Step 1: Skipping Architecture Graph Update (--no-graph)")

    # ========================================================================
    # Step 2: Run Architecture Validation Tests
    # ========================================================================

    print_section("Step 2: Architecture Validation Tests")

    arch_test_cmd = pytest_cmd + ['tests/test_architecture_graph.py'] + pytest_args

    run_command(
        arch_test_cmd,
        "Architecture validation tests",
        fail_fast=True
    )

    # If only architecture tests requested, exit here
    if args.architecture:
        print_section("Test Cycle Complete")
        print("✓ Architecture tests passed")
        return

    # ========================================================================
    # Step 3: Run All Other Tests
    # ========================================================================

    print_section("Step 3: Unit and Integration Tests")

    # Run all tests except architecture (to avoid duplication)
    all_tests_cmd = pytest_cmd + [
        'tests/',
        '--ignore=tests/test_architecture_graph.py'
    ] + pytest_args

    run_command(
        all_tests_cmd,
        "Unit and integration tests",
        fail_fast=True
    )

    # ========================================================================
    # Test Cycle Complete
    # ========================================================================

    print_section("Test Cycle Complete")
    print("✓ Architecture graph database updated")
    print("✓ Architecture validation tests passed")
    print("✓ All unit and integration tests passed")

    if args.coverage:
        print("\n📊 Coverage report generated:")
        print("   Open: htmlcov/index.html")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
