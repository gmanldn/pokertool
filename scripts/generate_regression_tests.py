#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automated Regression Test Generator for PokerTool

This script analyzes the codebase and generates test skeletons for modules
that lack test coverage. It helps systematically achieve 95%+ test coverage
by creating structured test files following best practices.

Usage:
    python scripts/generate_regression_tests.py --module src/pokertool/api.py
    python scripts/generate_regression_tests.py --all-critical
    python scripts/generate_regression_tests.py --detection-pipeline
    python scripts/generate_regression_tests.py --report
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

# Project paths
ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / 'src' / 'pokertool'
TESTS_DIR = ROOT / 'tests'


@dataclass
class ModuleInfo:
    """Information about a source module"""
    path: Path
    name: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    docstring: Optional[str]
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW


@dataclass
class TestStatus:
    """Test coverage status for a module"""
    module_path: Path
    has_test: bool
    test_path: Optional[Path]
    test_count: int
    coverage_estimate: float


# Module priority mapping (based on regression testing strategy)
CRITICAL_MODULES = {
    'api.py', 'database.py', 'scrape.py', 'gui.py',
    'enhanced_gui.py', 'smarthelper_engine.py', 'cli.py'
}

DETECTION_PIPELINE_MODULES = {
    # Detection infrastructure
    'detection_utils.py', 'detection_config.py', 'detection_cache.py',
    'detection_logger.py', 'detection_accuracy_tracker.py', 'detection_metrics_tracker.py',
    'detection_fps_counter.py', 'detection_fallback.py', 'detection_sanity_checks.py',
    'detection_event_batcher.py', 'detection_state_persistence.py',
    # Scraping
    'scraping_accuracy_system.py', 'scraping_master_system.py',
    'scraping_reliability_system.py', 'scraping_speed_optimizer.py',
    # Card detection
    'card_recognizer.py', 'card_confidence_scorer.py', 'card_history_tracker.py',
    'player_action_detector.py', 'player_detection_confidence.py', 'suit_color_detector.py',
    # OCR
    'ocr_recognition.py', 'image_preprocessor.py', 'image_preprocessing_optimizer.py',
    'smart_ocr_cache.py', 'smart_poker_detector.py',
}

STRATEGY_MODULES = {
    'gto_solver.py', 'gto_ranges.py', 'cfr_plus.py', 'qaoa_solver.py',
    'opponent_profiler.py', 'opponent_profiling.py', 'ml_opponent_modeling.py',
    'pattern_detector.py', 'exploitative_engine.py',
    'live_decision_engine.py', 'smarthelper_cache.py', 'smarthelper_websocket.py',
    'range_generator.py', 'pot_odds_calculator.py', 'pot_odds_display.py',
    'variance_calculator.py',
}


class PythonModuleAnalyzer:
    """Analyzes Python modules to extract testable components"""

    @staticmethod
    def analyze_module(module_path: Path) -> ModuleInfo:
        """Extract functions, classes, and metadata from a Python module"""
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return ModuleInfo(
                path=module_path,
                name=module_path.stem,
                functions=[],
                classes=[],
                imports=[],
                docstring=None,
                priority='LOW'
            )

        functions = []
        classes = []
        imports = []
        docstring = ast.get_docstring(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Only include public functions (not starting with _)
                if not node.name.startswith('_'):
                    functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    imports.extend([alias.name for alias in node.names])
                elif node.module:
                    imports.append(node.module)

        # Determine priority
        module_name = module_path.name
        if module_name in CRITICAL_MODULES:
            priority = 'CRITICAL'
        elif module_name in DETECTION_PIPELINE_MODULES:
            priority = 'HIGH'
        elif module_name in STRATEGY_MODULES:
            priority = 'MEDIUM'
        else:
            priority = 'LOW'

        return ModuleInfo(
            path=module_path,
            name=module_path.stem,
            functions=functions,
            classes=classes,
            imports=imports,
            docstring=docstring,
            priority=priority
        )


class TestGenerator:
    """Generates test file skeletons for modules"""

    def __init__(self):
        self.version = self._get_current_version()

    def _get_current_version(self) -> str:
        """Get current version from VERSION file"""
        version_file = ROOT / 'VERSION'
        if version_file.exists():
            return version_file.read_text().strip()
        return 'v101.0.0'  # Default

    def generate_test_file(self, module_info: ModuleInfo) -> str:
        """Generate a test file skeleton for a module"""
        module_name = module_info.name
        test_content = self._generate_header(module_info)
        test_content += self._generate_imports(module_info)
        test_content += self._generate_fixtures(module_info)
        test_content += self._generate_function_tests(module_info)
        test_content += self._generate_class_tests(module_info)
        test_content += self._generate_integration_tests(module_info)
        test_content += self._generate_regression_tests(module_info)

        return test_content

    def _generate_header(self, module_info: ModuleInfo) -> str:
        """Generate test file header"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Regression Tests for {module_info.name}.py

Priority: {module_info.priority}
Generated: {datetime.now().strftime('%Y-%m-%d')}
Version: {self.version}

This test file ensures that functionality in {module_info.name}.py doesn't
regress across versions. Each test should reference the version where the
feature was introduced.

Test Coverage Goals:
- Unit tests for all public functions/methods
- Integration tests for component interactions
- Regression tests for known bug fixes
- Edge case handling and error conditions
"""

'''

    def _generate_imports(self, module_info: ModuleInfo) -> str:
        """Generate import statements"""
        relative_path = module_info.path.relative_to(SRC_DIR)
        import_path = str(relative_path.with_suffix('')).replace('/', '.')

        imports = f'''import pytest
from unittest.mock import Mock, patch, MagicMock
from pokertool.{import_path} import (
'''

        # Import all public functions and classes
        exports = []
        if module_info.functions:
            exports.extend(module_info.functions[:5])  # Limit to avoid overly long lines
        if module_info.classes:
            exports.extend(module_info.classes[:3])

        if exports:
            for export in exports[:-1]:
                imports += f'    {export},\n'
            imports += f'    {exports[-1]}\n'
        else:
            imports += '    # TODO: Import components to test\n'

        imports += ')\n\n'

        return imports

    def _generate_fixtures(self, module_info: ModuleInfo) -> str:
        """Generate pytest fixtures"""
        return '''
# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Sample test data for {module}"""
    # TODO: Add representative test data
    return {{
        'example_field': 'example_value',
    }}


@pytest.fixture
def mock_dependencies():
    """Mock external dependencies for isolated testing"""
    # TODO: Mock database, API calls, file I/O, etc.
    return {{
        'db': Mock(),
        'api': Mock(),
    }}

'''.format(module=module_info.name)

    def _generate_function_tests(self, module_info: ModuleInfo) -> str:
        """Generate test stubs for functions"""
        if not module_info.functions:
            return ''

        tests = '''
# ============================================================================
# Unit Tests - Functions
# ============================================================================

'''

        for func in module_info.functions[:10]:  # Limit to first 10 functions
            tests += f'''
def test_{func}_basic():
    """Test {func} with valid inputs

    Regression: {self.version} - Basic functionality
    TODO: Add commit hash when feature was introduced
    TODO: Document what this function does
    TODO: Add edge cases and error handling tests
    """
    # Arrange
    # TODO: Set up test inputs

    # Act
    # result = {func}(test_input)

    # Assert
    # TODO: Verify expected behavior
    pytest.skip("Not implemented yet - needs test data and assertions")


def test_{func}_edge_cases():
    """Test {func} with edge cases

    Regression: {self.version} - Edge case handling
    TODO: Test null, empty, invalid inputs
    TODO: Test boundary conditions
    """
    pytest.skip("Not implemented yet - needs edge case scenarios")


def test_{func}_error_handling():
    """Test {func} error handling

    Regression: {self.version} - Error conditions
    TODO: Test expected exceptions
    TODO: Test error messages
    """
    pytest.skip("Not implemented yet - needs error scenarios")

'''

        return tests

    def _generate_class_tests(self, module_info: ModuleInfo) -> str:
        """Generate test stubs for classes"""
        if not module_info.classes:
            return ''

        tests = '''
# ============================================================================
# Unit Tests - Classes
# ============================================================================

'''

        for cls in module_info.classes[:5]:  # Limit to first 5 classes
            tests += f'''
class Test{cls}:
    """Test suite for {cls} class

    Regression: {self.version} - {cls} functionality
    TODO: Add commit hash for class introduction
    TODO: Document class purpose and responsibilities
    """

    @pytest.fixture
    def instance(self):
        """Create {cls} instance for testing"""
        # TODO: Initialize with test configuration
        return {cls}()

    def test_initialization(self, instance):
        """Test {cls} initialization

        Regression: {self.version} - Object creation
        TODO: Verify initial state
        """
        pytest.skip("Not implemented yet - verify initialization")

    def test_public_methods(self, instance):
        """Test {cls} public methods

        Regression: {self.version} - Method behavior
        TODO: Test each public method
        """
        pytest.skip("Not implemented yet - add method tests")

    def test_state_transitions(self, instance):
        """Test {cls} state transitions

        Regression: {self.version} - State management
        TODO: Test state changes
        """
        pytest.skip("Not implemented yet - add state tests")

    def test_error_handling(self, instance):
        """Test {cls} error handling

        Regression: {self.version} - Error conditions
        TODO: Test exception scenarios
        """
        pytest.skip("Not implemented yet - add error tests")

'''

        return tests

    def _generate_integration_tests(self, module_info: ModuleInfo) -> str:
        """Generate integration test stubs"""
        return f'''
# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
def test_integration_with_dependencies():
    """Test {module_info.name} integration with dependencies

    Regression: {self.version} - Component integration
    TODO: Test with real dependencies (database, API, etc.)
    TODO: Test data flow between components
    """
    pytest.skip("Not implemented yet - needs integration scenario")


@pytest.mark.integration
def test_end_to_end_workflow():
    """Test complete workflow through {module_info.name}

    Regression: {self.version} - End-to-end functionality
    TODO: Test realistic user workflow
    TODO: Verify final output/state
    """
    pytest.skip("Not implemented yet - needs e2e scenario")

'''

    def _generate_regression_tests(self, module_info: ModuleInfo) -> str:
        """Generate regression test section"""
        return f'''
# ============================================================================
# Regression Tests (Version-Specific)
# ============================================================================

# TODO: Add regression tests for specific bugs/features
#
# Pattern:
# def test_bug_fix_description():
#     """Regression: vX.Y.Z - Fix for [bug description]
#
#     Commit: [commit_hash]
#     Issue: [GitHub issue number]
#
#     [Detailed description of what was broken and how it was fixed]
#     """
#     # Test that reproduces the original bug
#     # Should pass now that bug is fixed
#

# Example template:
# def test_example_regression():
#     """Regression: {self.version} - Example bug fix
#
#     Commit: abc123def - Fix example bug
#     Issue: #123
#
#     Original issue: [description]
#     Fix: [description]
#     """
#     # Test implementation
#     pass

'''


class TestCoverageAnalyzer:
    """Analyzes test coverage across the codebase"""

    def __init__(self):
        self.src_dir = SRC_DIR
        self.tests_dir = TESTS_DIR

    def find_all_modules(self) -> List[Path]:
        """Find all Python modules in src/pokertool/"""
        modules = []
        for path in self.src_dir.rglob('*.py'):
            # Skip __init__.py and test files
            if path.name != '__init__.py' and not path.name.startswith('test_'):
                modules.append(path)
        return sorted(modules)

    def find_test_for_module(self, module_path: Path) -> Optional[Path]:
        """Find corresponding test file for a module"""
        module_name = module_path.stem
        test_name = f'test_{module_name}.py'

        # Search in tests/ and all subdirectories
        for test_file in self.tests_dir.rglob(test_name):
            return test_file

        return None

    def analyze_coverage(self) -> Dict[str, TestStatus]:
        """Analyze test coverage for all modules"""
        modules = self.find_all_modules()
        coverage = {}

        for module_path in modules:
            test_path = self.find_test_for_module(module_path)
            has_test = test_path is not None

            # Estimate test count if test file exists
            test_count = 0
            if test_path and test_path.exists():
                with open(test_path, 'r') as f:
                    content = f.read()
                    test_count = len(re.findall(r'^\s*def test_', content, re.MULTILINE))

            status = TestStatus(
                module_path=module_path,
                has_test=has_test,
                test_path=test_path,
                test_count=test_count,
                coverage_estimate=1.0 if has_test else 0.0
            )

            coverage[module_path.name] = status

        return coverage

    def generate_coverage_report(self) -> str:
        """Generate comprehensive coverage report"""
        coverage = self.analyze_coverage()

        total_modules = len(coverage)
        tested_modules = sum(1 for s in coverage.values() if s.has_test)
        untested_modules = total_modules - tested_modules
        coverage_pct = (tested_modules / total_modules * 100) if total_modules > 0 else 0

        report = f'''
# Test Coverage Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total modules: {total_modules}
- Modules WITH tests: {tested_modules} ({coverage_pct:.1f}%)
- Modules WITHOUT tests: {untested_modules} ({100-coverage_pct:.1f}%)

## Modules Without Tests (Priority Order)

### CRITICAL PRIORITY
'''

        # Group by priority
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            analyzer = PythonModuleAnalyzer()
            priority_modules = []

            for module_name, status in sorted(coverage.items()):
                if not status.has_test:
                    info = analyzer.analyze_module(status.module_path)
                    if info.priority == priority:
                        priority_modules.append((module_name, status))

            if priority_modules:
                report += f'\n### {priority} PRIORITY\n'
                for module_name, status in priority_modules:
                    relative_path = status.module_path.relative_to(SRC_DIR)
                    report += f'- [ ] {relative_path}\n'

        report += '\n\n## Modules With Tests\n'
        for module_name, status in sorted(coverage.items()):
            if status.has_test:
                relative_path = status.module_path.relative_to(SRC_DIR)
                report += f'- [x] {relative_path} ({status.test_count} tests)\n'

        return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate regression test skeletons for untested modules',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--module',
        type=Path,
        help='Generate test for specific module (e.g., src/pokertool/api.py)'
    )
    parser.add_argument(
        '--all-critical',
        action='store_true',
        help='Generate tests for all CRITICAL priority modules'
    )
    parser.add_argument(
        '--detection-pipeline',
        action='store_true',
        help='Generate tests for all detection pipeline modules'
    )
    parser.add_argument(
        '--strategy',
        action='store_true',
        help='Generate tests for all strategy/logic modules'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate coverage report without creating test files'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=TESTS_DIR / 'unit',
        help='Output directory for generated tests (default: tests/unit/)'
    )

    args = parser.parse_args()

    analyzer_obj = TestCoverageAnalyzer()
    generator = TestGenerator()
    module_analyzer = PythonModuleAnalyzer()

    # Generate coverage report
    if args.report:
        report = analyzer_obj.generate_coverage_report()
        print(report)

        # Save to file
        report_file = ROOT / 'test_coverage_report.md'
        with open(report_file, 'w') as f:
            f.write(report)
        print(f'\n✅ Report saved to: {report_file}')
        return 0

    # Determine which modules to process
    modules_to_test = []

    if args.module:
        if args.module.exists():
            modules_to_test.append(args.module)
        else:
            print(f'❌ Module not found: {args.module}')
            return 1

    elif args.all_critical:
        coverage = analyzer_obj.analyze_coverage()
        for module_name in CRITICAL_MODULES:
            if module_name in coverage and not coverage[module_name].has_test:
                modules_to_test.append(coverage[module_name].module_path)

    elif args.detection_pipeline:
        coverage = analyzer_obj.analyze_coverage()
        for module_name in DETECTION_PIPELINE_MODULES:
            if module_name in coverage and not coverage[module_name].has_test:
                modules_to_test.append(coverage[module_name].module_path)

    elif args.strategy:
        coverage = analyzer_obj.analyze_coverage()
        for module_name in STRATEGY_MODULES:
            if module_name in coverage and not coverage[module_name].has_test:
                modules_to_test.append(coverage[module_name].module_path)

    else:
        print('❌ Please specify --module, --all-critical, --detection-pipeline, --strategy, or --report')
        parser.print_help()
        return 1

    # Generate test files
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for module_path in modules_to_test:
        print(f'\n📝 Generating test for: {module_path.name}')

        # Analyze module
        module_info = module_analyzer.analyze_module(module_path)

        # Generate test content
        test_content = generator.generate_test_file(module_info)

        # Determine output path
        test_filename = f'test_{module_info.name}.py'

        # Create subdirectory based on priority
        if module_info.priority == 'CRITICAL':
            output_dir = args.output_dir / 'critical'
        elif module_info.priority == 'HIGH':
            output_dir = args.output_dir / 'detection'
        elif module_info.priority == 'MEDIUM':
            output_dir = args.output_dir / 'strategy'
        else:
            output_dir = args.output_dir / 'infrastructure'

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / test_filename

        # Write test file
        with open(output_path, 'w') as f:
            f.write(test_content)

        print(f'✅ Created: {output_path}')
        print(f'   Priority: {module_info.priority}')
        print(f'   Functions: {len(module_info.functions)}')
        print(f'   Classes: {len(module_info.classes)}')

    print(f'\n✅ Generated {len(modules_to_test)} test files in {args.output_dir}')
    print('\n📋 Next steps:')
    print('1. Review generated test files')
    print('2. Fill in test implementations (replace pytest.skip)')
    print('3. Add version numbers and commit hashes')
    print('4. Run tests: pytest tests/unit/ -v')

    return 0


if __name__ == '__main__':
    sys.exit(main())
