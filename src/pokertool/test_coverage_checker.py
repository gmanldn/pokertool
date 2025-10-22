"""Test Coverage Checker - Verify test coverage requirements"""
import subprocess
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TestCoverageChecker:
    """Check test coverage and enforce requirements"""

    def __init__(self, min_coverage: float = 80.0, project_root: Optional[str] = None):
        """
        Initialize coverage checker

        Args:
            min_coverage: Minimum required coverage percentage (default 80%)
            project_root: Path to project root (defaults to current directory)
        """
        self.min_coverage = min_coverage
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def run_python_coverage(self, test_path: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Run Python test coverage using pytest-cov

        Args:
            test_path: Specific test file/directory to run (optional)

        Returns:
            Tuple of (passed, coverage_data)
        """
        try:
            # Build pytest command
            cmd = [
                "pytest",
                "--cov=src/pokertool",
                "--cov-report=json",
                "--cov-report=term-missing"
            ]

            if test_path:
                cmd.append(test_path)

            # Run pytest with coverage
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse coverage report
            coverage_file = self.project_root / ".coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
            else:
                coverage_data = self._parse_terminal_coverage(result.stdout)

            # Check if coverage meets requirement
            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            passed = total_coverage >= self.min_coverage

            logger.info(f"Python coverage: {total_coverage:.1f}% (required: {self.min_coverage}%)")

            return passed, {
                "total_coverage": total_coverage,
                "files": coverage_data.get("files", {}),
                "tests_passed": result.returncode == 0,
                "output": result.stdout
            }

        except subprocess.TimeoutExpired:
            logger.error("Coverage tests timed out")
            return False, {"error": "Tests timed out"}
        except Exception as e:
            logger.error(f"Coverage check failed: {e}")
            return False, {"error": str(e)}

    def run_frontend_coverage(self) -> Tuple[bool, Dict]:
        """
        Run frontend test coverage using Jest

        Returns:
            Tuple of (passed, coverage_data)
        """
        try:
            # Build jest command
            cmd = ["npm", "run", "test:coverage", "--", "--json"]

            # Run jest with coverage
            result = subprocess.run(
                cmd,
                cwd=self.project_root / "pokertool-frontend",
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse jest coverage output
            coverage_data = self._parse_jest_coverage(result.stdout)

            total_coverage = coverage_data.get("total_coverage", 0)
            passed = total_coverage >= self.min_coverage

            logger.info(f"Frontend coverage: {total_coverage:.1f}% (required: {self.min_coverage}%)")

            return passed, coverage_data

        except subprocess.TimeoutExpired:
            logger.error("Frontend coverage tests timed out")
            return False, {"error": "Tests timed out"}
        except Exception as e:
            logger.error(f"Frontend coverage check failed: {e}")
            return False, {"error": str(e)}

    def check_coverage_delta(
        self,
        changed_files: List[str],
        previous_coverage: Optional[Dict] = None
    ) -> Tuple[bool, Dict]:
        """
        Check that coverage didn't decrease for changed files

        Args:
            changed_files: List of file paths that were changed
            previous_coverage: Previous coverage data (optional)

        Returns:
            Tuple of (passed, delta_data)
        """
        try:
            # Get current coverage
            _, current_coverage = self.run_python_coverage()

            if not previous_coverage:
                # No baseline to compare against
                return True, {"message": "No baseline coverage data"}

            # Compare coverage for changed files
            decreased_files = []

            for file_path in changed_files:
                if not file_path.endswith('.py'):
                    continue

                current = current_coverage.get("files", {}).get(file_path, {}).get("percent_covered", 0)
                previous = previous_coverage.get("files", {}).get(file_path, {}).get("percent_covered", 0)

                if current < previous:
                    decreased_files.append({
                        "file": file_path,
                        "previous": previous,
                        "current": current,
                        "delta": current - previous
                    })

            passed = len(decreased_files) == 0

            return passed, {
                "decreased_files": decreased_files,
                "total_files_checked": len(changed_files)
            }

        except Exception as e:
            logger.error(f"Coverage delta check failed: {e}")
            return False, {"error": str(e)}

    def require_tests_for_new_code(self, changed_files: List[str]) -> Tuple[bool, Dict]:
        """
        Check that new Python files have corresponding test files

        Args:
            changed_files: List of file paths that were added

        Returns:
            Tuple of (passed, results)
        """
        missing_tests = []

        for file_path in changed_files:
            # Skip non-Python files
            if not file_path.endswith('.py'):
                continue

            # Skip test files themselves
            if 'test_' in file_path or file_path.startswith('tests/'):
                continue

            # Skip __init__.py files
            if file_path.endswith('__init__.py'):
                continue

            # Check if corresponding test file exists
            test_file = self._get_test_file_path(file_path)
            if not test_file.exists():
                missing_tests.append({
                    "file": file_path,
                    "expected_test": str(test_file)
                })

        passed = len(missing_tests) == 0

        return passed, {
            "missing_tests": missing_tests,
            "files_checked": len([f for f in changed_files if f.endswith('.py')])
        }

    def _get_test_file_path(self, source_file: str) -> Path:
        """Get expected test file path for a source file"""
        path = Path(source_file)

        # Convert src/pokertool/module.py -> tests/test_module.py
        if 'src/pokertool' in str(path):
            relative = path.relative_to('src/pokertool')
            test_path = self.project_root / 'tests' / f"test_{relative}"
            return test_path

        return self.project_root / 'tests' / f"test_{path.name}"

    def _parse_terminal_coverage(self, output: str) -> Dict:
        """Parse coverage from terminal output"""
        # Look for coverage percentage in output
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if match:
            coverage = float(match.group(1))
            return {
                "totals": {"percent_covered": coverage},
                "files": {}
            }
        return {"totals": {"percent_covered": 0}, "files": {}}

    def _parse_jest_coverage(self, output: str) -> Dict:
        """Parse Jest coverage output"""
        try:
            # Jest outputs JSON coverage summary
            coverage_match = re.search(r'"coverageMap":\s*(\{.*?\})', output, re.DOTALL)
            if coverage_match:
                coverage_data = json.loads(coverage_match.group(1))
                # Calculate total coverage
                total_lines = sum(data.get("lines", {}).get("total", 0) for data in coverage_data.values())
                covered_lines = sum(data.get("lines", {}).get("covered", 0) for data in coverage_data.values())
                total_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                return {
                    "total_coverage": total_coverage,
                    "files": coverage_data
                }
        except Exception as e:
            logger.warning(f"Failed to parse Jest coverage: {e}")

        return {"total_coverage": 0, "files": {}}

    def generate_coverage_report(self) -> str:
        """Generate human-readable coverage report"""
        python_passed, python_data = self.run_python_coverage()
        frontend_passed, frontend_data = self.run_frontend_coverage()

        report = []
        report.append("=" * 60)
        report.append("TEST COVERAGE REPORT")
        report.append("=" * 60)
        report.append("")

        # Python coverage
        report.append("Python Backend:")
        report.append(f"  Total Coverage: {python_data.get('total_coverage', 0):.1f}%")
        report.append(f"  Status: {'✅ PASSED' if python_passed else '❌ FAILED'}")
        report.append(f"  Required: {self.min_coverage}%")
        report.append("")

        # Frontend coverage
        report.append("React Frontend:")
        report.append(f"  Total Coverage: {frontend_data.get('total_coverage', 0):.1f}%")
        report.append(f"  Status: {'✅ PASSED' if frontend_passed else '❌ FAILED'}")
        report.append(f"  Required: {self.min_coverage}%")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)
