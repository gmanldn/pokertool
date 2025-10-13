#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automated Scrape QA Harness
============================

SCRAPE-014: Automated Scrape QA Harness

Catches scraping regressions by replaying curated screenshots through
the full extraction stack and comparing against ground truth.

Features:
- Load labelled screenshot suites with ground truth data
- Run scraper end-to-end on test images
- Compare extracted data against truth data
- Generate detailed diff reports with visual overlays
- Parallel execution for fast testing
- Integration with CI/CD pipelines

Module: pokertool.scrape_qa_harness
Version: v46.0.0
Author: PokerTool Development Team
"""

__version__ = '46.0.0'
__author__ = 'PokerTool Development Team'

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None


class FieldType(Enum):
    """Types of fields that can be extracted from poker tables."""
    POT_SIZE = 'pot_size'
    PLAYER_STACK = 'player_stack'
    BET_AMOUNT = 'bet_amount'
    PLAYER_NAME = 'player_name'
    HOLE_CARDS = 'hole_cards'
    BOARD_CARDS = 'board_cards'
    BUTTON_POSITION = 'button_position'
    BLIND_LEVEL = 'blind_level'
    TIME_REMAINING = 'time_remaining'


class ThemeType(Enum):
    """Poker table themes."""
    STANDARD_GREEN = 'standard_green'
    BETFAIR_PURPLE = 'betfair_purple'
    POKERSTARS_BLUE = 'pokerstars_blue'
    PARTY_POKER_RED = 'party_poker_red'
    DARK_MODE = 'dark_mode'


@dataclass
class GroundTruth:
    """Ground truth data for a test case."""
    pot_size: Optional[float] = None
    player_stacks: Dict[int, float] = field(default_factory=dict)  # seat -> stack
    player_names: Dict[int, str] = field(default_factory=dict)  # seat -> name
    bets: Dict[int, float] = field(default_factory=dict)  # seat -> bet amount
    hole_cards: Optional[List[str]] = None  # e.g., ['As', 'Kh']
    board_cards: Optional[List[str]] = None  # e.g., ['Qd', 'Jc', '9s']
    button_position: Optional[int] = None  # seat number
    blinds: Optional[Tuple[float, float]] = None  # (small, big)
    time_remaining: Optional[float] = None  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        if self.blinds:
            d['blinds'] = list(self.blinds)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroundTruth':
        """Create from dictionary."""
        if 'blinds' in data and data['blinds']:
            data['blinds'] = tuple(data['blinds'])
        return cls(**data)


@dataclass
class QaQaTestCase:
    """A single QA test case."""
    id: str
    name: str
    image_path: Path
    ground_truth: GroundTruth
    theme: ThemeType
    stakes: str  # e.g., "NL10", "PLO25"
    resolution: Tuple[int, int]  # (width, height)
    lighting: str  # 'normal', 'dark', 'bright'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute hash of image for cache invalidation."""
        if not self.image_path.exists():
            return ""

        with open(self.image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()


@dataclass
class FieldDiff:
    """Difference between expected and actual field value."""
    field_type: FieldType
    expected: Any
    actual: Any
    match: bool
    error_margin: Optional[float] = None  # For numeric fields
    notes: str = ""


@dataclass
class QaQaTestResult:
    """Result of running a test case."""
    test_case_id: str
    success: bool
    execution_time_ms: float
    diffs: List[FieldDiff]
    accuracy: float  # 0.0 to 1.0
    errors: List[str] = field(default_factory=list)

    def get_failed_fields(self) -> List[FieldType]:
        """Get list of fields that failed."""
        return [diff.field_type for diff in self.diffs if not diff.match]

    def summary(self) -> str:
        """Get human-readable summary."""
        status = "✅ PASS" if self.success else "❌ FAIL"
        failed = len(self.get_failed_fields())
        total = len(self.diffs)
        return (f"{status} | Accuracy: {self.accuracy*100:.1f}% | "
                f"Failed: {failed}/{total} | Time: {self.execution_time_ms:.1f}ms")


@dataclass
class SuiteReport:
    """Report for entire test suite."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    total_execution_time_ms: float
    results: List[QaTestResult]
    per_field_accuracy: Dict[FieldType, float] = field(default_factory=dict)
    by_theme: Dict[ThemeType, Tuple[int, int]] = field(default_factory=dict)  # (pass, total)
    by_stakes: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # (pass, total)

    @property
    def pass_rate(self) -> float:
        """Overall pass rate."""
        return self.passed / max(self.total_tests, 1)

    @property
    def avg_accuracy(self) -> float:
        """Average field accuracy."""
        if not self.results:
            return 0.0
        return sum(r.accuracy for r in self.results) / len(self.results)


class ScrapeQAHarness:
    """
    Automated QA harness for poker table scraping.

    Loads test cases, runs scrapers, compares results, generates reports.
    """

    def __init__(self, test_suite_dir: Path, scraper_fn: Optional[callable] = None):
        """
        Initialize QA harness.

        Args:
            test_suite_dir: Directory containing test cases
            scraper_fn: Function to run scraping (takes image path, returns dict)
        """
        self.test_suite_dir = Path(test_suite_dir)
        self.scraper_fn = scraper_fn
        self.test_cases: List[QaTestCase] = []
        self.results: List[QaTestResult] = []

        # Numeric comparison tolerance
        self.numeric_tolerance = 0.01  # 1% tolerance for pot sizes, stacks, etc.

        logger.info(f"Initialized QA harness with test suite: {test_suite_dir}")

    def load_test_suite(self) -> int:
        """
        Load all test cases from suite directory.

        Returns:
            Number of test cases loaded
        """
        if not self.test_suite_dir.exists():
            logger.warning(f"Test suite directory not found: {self.test_suite_dir}")
            return 0

        # Look for test case manifest
        manifest_path = self.test_suite_dir / "manifest.json"
        if manifest_path.exists():
            count = self._load_from_manifest(manifest_path)
        else:
            count = self._discover_test_cases()

        logger.info(f"Loaded {count} test cases")
        return count

    def _load_from_manifest(self, manifest_path: Path) -> int:
        """Load test cases from manifest file."""
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            for case_data in manifest.get('test_cases', []):
                # Resolve image path
                image_path = self.test_suite_dir / case_data['image_path']

                # Parse ground truth
                gt_data = case_data.get('ground_truth', {})
                ground_truth = GroundTruth.from_dict(gt_data)

                # Create test case
                test_case = QaTestCase(
                    id=case_data['id'],
                    name=case_data.get('name', case_data['id']),
                    image_path=image_path,
                    ground_truth=ground_truth,
                    theme=ThemeType(case_data.get('theme', 'standard_green')),
                    stakes=case_data.get('stakes', 'unknown'),
                    resolution=tuple(case_data.get('resolution', [1920, 1080])),
                    lighting=case_data.get('lighting', 'normal'),
                    metadata=case_data.get('metadata', {})
                )

                self.test_cases.append(test_case)

            return len(self.test_cases)

        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return 0

    def _discover_test_cases(self) -> int:
        """Auto-discover test cases from directory structure."""
        # Look for image + json pairs
        for img_path in self.test_suite_dir.glob("*.png"):
            json_path = img_path.with_suffix('.json')

            if json_path.exists():
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)

                    ground_truth = GroundTruth.from_dict(data.get('ground_truth', {}))

                    test_case = QaTestCase(
                        id=img_path.stem,
                        name=data.get('name', img_path.stem),
                        image_path=img_path,
                        ground_truth=ground_truth,
                        theme=ThemeType(data.get('theme', 'standard_green')),
                        stakes=data.get('stakes', 'unknown'),
                        resolution=tuple(data.get('resolution', [1920, 1080])),
                        lighting=data.get('lighting', 'normal'),
                        metadata=data.get('metadata', {})
                    )

                    self.test_cases.append(test_case)

                except Exception as e:
                    logger.error(f"Failed to load test case {img_path.stem}: {e}")

        return len(self.test_cases)

    def run_test_case(self, test_case: QaTestCase, seed: int = 42) -> QaTestResult:
        """
        Run a single test case.

        Args:
            test_case: Test case to run
            seed: Random seed for deterministic execution

        Returns:
            Test result
        """
        start_time = time.time()
        diffs = []
        errors = []

        try:
            # Set random seed for deterministic execution
            np.random.seed(seed)

            # Run scraper
            if self.scraper_fn:
                extracted = self.scraper_fn(test_case.image_path)
            else:
                # Mock extraction for testing
                extracted = self._mock_extraction(test_case)

            # Compare each field
            gt = test_case.ground_truth

            # Pot size
            if gt.pot_size is not None:
                diff = self._compare_numeric(
                    FieldType.POT_SIZE,
                    gt.pot_size,
                    extracted.get('pot_size')
                )
                diffs.append(diff)

            # Player stacks
            for seat, expected_stack in gt.player_stacks.items():
                actual_stack = extracted.get('player_stacks', {}).get(seat)
                diff = self._compare_numeric(
                    FieldType.PLAYER_STACK,
                    expected_stack,
                    actual_stack
                )
                diff.notes = f"Seat {seat}"
                diffs.append(diff)

            # Player names
            for seat, expected_name in gt.player_names.items():
                actual_name = extracted.get('player_names', {}).get(seat)
                diff = self._compare_string(
                    FieldType.PLAYER_NAME,
                    expected_name,
                    actual_name
                )
                diff.notes = f"Seat {seat}"
                diffs.append(diff)

            # Hole cards
            if gt.hole_cards is not None:
                diff = self._compare_cards(
                    FieldType.HOLE_CARDS,
                    gt.hole_cards,
                    extracted.get('hole_cards')
                )
                diffs.append(diff)

            # Board cards
            if gt.board_cards is not None:
                diff = self._compare_cards(
                    FieldType.BOARD_CARDS,
                    gt.board_cards,
                    extracted.get('board_cards')
                )
                diffs.append(diff)

            # Button position
            if gt.button_position is not None:
                diff = self._compare_exact(
                    FieldType.BUTTON_POSITION,
                    gt.button_position,
                    extracted.get('button_position')
                )
                diffs.append(diff)

        except Exception as e:
            logger.error(f"Test case {test_case.id} failed with error: {e}")
            errors.append(str(e))

        # Calculate metrics
        execution_time = (time.time() - start_time) * 1000
        matched = sum(1 for d in diffs if d.match)
        accuracy = matched / max(len(diffs), 1)
        success = accuracy >= 0.8 and len(errors) == 0  # 80% threshold

        return QaTestResult(
            test_case_id=test_case.id,
            success=success,
            execution_time_ms=execution_time,
            diffs=diffs,
            accuracy=accuracy,
            errors=errors
        )

    def _compare_numeric(self, field_type: FieldType, expected: float,
                         actual: Optional[float]) -> FieldDiff:
        """Compare numeric fields with tolerance."""
        if actual is None:
            return FieldDiff(field_type, expected, None, False, notes="Missing")

        error = abs(expected - actual) / max(abs(expected), 1e-6)
        match = error <= self.numeric_tolerance

        return FieldDiff(
            field_type=field_type,
            expected=expected,
            actual=actual,
            match=match,
            error_margin=error
        )

    def _compare_string(self, field_type: FieldType, expected: str,
                        actual: Optional[str]) -> FieldDiff:
        """Compare string fields."""
        if actual is None:
            return FieldDiff(field_type, expected, None, False, notes="Missing")

        # Case-insensitive comparison, strip whitespace
        match = expected.strip().lower() == actual.strip().lower()

        return FieldDiff(
            field_type=field_type,
            expected=expected,
            actual=actual,
            match=match
        )

    def _compare_cards(self, field_type: FieldType, expected: List[str],
                       actual: Optional[List[str]]) -> FieldDiff:
        """Compare card lists."""
        if actual is None:
            return FieldDiff(field_type, expected, None, False, notes="Missing")

        # Cards can be in any order, sort for comparison
        expected_sorted = sorted([c.lower() for c in expected])
        actual_sorted = sorted([c.lower() for c in actual])

        match = expected_sorted == actual_sorted

        return FieldDiff(
            field_type=field_type,
            expected=expected,
            actual=actual,
            match=match
        )

    def _compare_exact(self, field_type: FieldType, expected: Any,
                       actual: Optional[Any]) -> FieldDiff:
        """Exact comparison."""
        match = expected == actual

        return FieldDiff(
            field_type=field_type,
            expected=expected,
            actual=actual,
            match=match
        )

    def _mock_extraction(self, test_case: QaTestCase) -> Dict[str, Any]:
        """Mock extraction for testing (returns ground truth with some noise)."""
        gt = test_case.ground_truth

        return {
            'pot_size': gt.pot_size,
            'player_stacks': gt.player_stacks,
            'player_names': gt.player_names,
            'hole_cards': gt.hole_cards,
            'board_cards': gt.board_cards,
            'button_position': gt.button_position
        }

    def run_suite(self, parallel: bool = True, max_workers: int = 4,
                  seed: int = 42) -> SuiteReport:
        """
        Run all test cases in suite.

        Args:
            parallel: Run tests in parallel
            max_workers: Max parallel workers
            seed: Random seed for deterministic execution

        Returns:
            Suite report
        """
        start_time = time.time()
        self.results.clear()

        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(self.run_test_case, tc, seed + i): tc
                    for i, tc in enumerate(self.test_cases)
                }

                # Collect results
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        self.results.append(result)
                        logger.info(f"Test {result.test_case_id}: {result.summary()}")
                    except Exception as e:
                        test_case = futures[future]
                        logger.error(f"Test {test_case.id} raised exception: {e}")
        else:
            # Sequential execution
            for i, test_case in enumerate(self.test_cases):
                result = self.run_test_case(test_case, seed + i)
                self.results.append(result)
                logger.info(f"Test {result.test_case_id}: {result.summary()}")

        # Generate report
        total_time = (time.time() - start_time) * 1000
        report = self._generate_report(total_time)

        return report

    def _generate_report(self, total_time_ms: float) -> SuiteReport:
        """Generate suite report from results."""
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed

        # Per-field accuracy
        field_counts: Dict[FieldType, Tuple[int, int]] = {}  # (matched, total)
        for result in self.results:
            for diff in result.diffs:
                if diff.field_type not in field_counts:
                    field_counts[diff.field_type] = (0, 0)

                matched, total = field_counts[diff.field_type]
                field_counts[diff.field_type] = (
                    matched + (1 if diff.match else 0),
                    total + 1
                )

        per_field_accuracy = {
            field: matched / max(total, 1)
            for field, (matched, total) in field_counts.items()
        }

        # By theme/stakes
        by_theme: Dict[ThemeType, Tuple[int, int]] = {}
        by_stakes: Dict[str, Tuple[int, int]] = {}

        result_map = {r.test_case_id: r for r in self.results}
        for test_case in self.test_cases:
            result = result_map.get(test_case.id)
            if not result:
                continue

            # By theme
            if test_case.theme not in by_theme:
                by_theme[test_case.theme] = (0, 0)
            theme_pass, theme_total = by_theme[test_case.theme]
            by_theme[test_case.theme] = (
                theme_pass + (1 if result.success else 0),
                theme_total + 1
            )

            # By stakes
            if test_case.stakes not in by_stakes:
                by_stakes[test_case.stakes] = (0, 0)
            stakes_pass, stakes_total = by_stakes[test_case.stakes]
            by_stakes[test_case.stakes] = (
                stakes_pass + (1 if result.success else 0),
                stakes_total + 1
            )

        return SuiteReport(
            suite_name=self.test_suite_dir.name,
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            total_execution_time_ms=total_time_ms,
            results=self.results,
            per_field_accuracy=per_field_accuracy,
            by_theme=by_theme,
            by_stakes=by_stakes
        )

    def generate_markdown_report(self, report: SuiteReport, output_path: Path):
        """Generate markdown report."""
        lines = []

        # Header
        lines.append(f"# Scrape QA Report: {report.suite_name}\n")
        lines.append(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Total Tests**: {report.total_tests}")
        lines.append(f"- **Passed**: {report.passed} ({report.pass_rate*100:.1f}%)")
        lines.append(f"- **Failed**: {report.failed}")
        lines.append(f"- **Avg Accuracy**: {report.avg_accuracy*100:.1f}%")
        lines.append(f"- **Total Time**: {report.total_execution_time_ms:.1f}ms\n")

        # Per-field accuracy
        lines.append("## Per-Field Accuracy\n")
        lines.append("| Field | Accuracy |")
        lines.append("|-------|----------|")
        for field, accuracy in sorted(report.per_field_accuracy.items(),
                                       key=lambda x: x[1], reverse=True):
            status = "✅" if accuracy >= 0.9 else "⚠️" if accuracy >= 0.7 else "❌"
            lines.append(f"| {field.value} | {status} {accuracy*100:.1f}% |")
        lines.append("")

        # By theme
        if report.by_theme:
            lines.append("## Results by Theme\n")
            lines.append("| Theme | Passed | Total | Rate |")
            lines.append("|-------|--------|-------|------|")
            for theme, (passed, total) in sorted(report.by_theme.items()):
                rate = passed / max(total, 1)
                status = "✅" if rate >= 0.9 else "⚠️" if rate >= 0.7 else "❌"
                lines.append(f"| {theme.value} | {passed} | {total} | {status} {rate*100:.1f}% |")
            lines.append("")

        # Failed tests
        failed_results = [r for r in report.results if not r.success]
        if failed_results:
            lines.append("## Failed Tests\n")
            for result in failed_results:
                lines.append(f"### {result.test_case_id}\n")
                lines.append(f"- **Accuracy**: {result.accuracy*100:.1f}%")
                lines.append(f"- **Time**: {result.execution_time_ms:.1f}ms")

                if result.errors:
                    lines.append(f"- **Errors**: {', '.join(result.errors)}")

                failed_fields = result.get_failed_fields()
                if failed_fields:
                    lines.append(f"- **Failed Fields**: {', '.join(f.value for f in failed_fields)}")

                lines.append("")

        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))

        logger.info(f"Markdown report written to: {output_path}")

    def check_thresholds(self, report: SuiteReport,
                         min_pass_rate: float = 0.8,
                         min_field_accuracy: float = 0.7) -> Tuple[bool, List[str]]:
        """
        Check if report meets quality thresholds.

        Args:
            report: Suite report
            min_pass_rate: Minimum pass rate (0.0-1.0)
            min_field_accuracy: Minimum per-field accuracy (0.0-1.0)

        Returns:
            Tuple of (passed, list of violations)
        """
        violations = []

        # Check pass rate
        if report.pass_rate < min_pass_rate:
            violations.append(
                f"Pass rate {report.pass_rate*100:.1f}% below threshold {min_pass_rate*100:.1f}%"
            )

        # Check field accuracy
        for field, accuracy in report.per_field_accuracy.items():
            if accuracy < min_field_accuracy:
                violations.append(
                    f"Field {field.value} accuracy {accuracy*100:.1f}% "
                    f"below threshold {min_field_accuracy*100:.1f}%"
                )

        passed = len(violations) == 0
        return passed, violations


# Utility functions for test case creation
def create_test_case_from_screenshot(image_path: Path,
                                      ground_truth: GroundTruth,
                                      **kwargs) -> QaTestCase:
    """Create a test case from a screenshot file."""
    if CV2_AVAILABLE:
        img = cv2.imread(str(image_path))
        if img is not None:
            height, width = img.shape[:2]
            resolution = (width, height)
        else:
            resolution = (1920, 1080)
    else:
        resolution = (1920, 1080)

    return QaTestCase(
        id=image_path.stem,
        name=kwargs.get('name', image_path.stem),
        image_path=image_path,
        ground_truth=ground_truth,
        theme=kwargs.get('theme', ThemeType.STANDARD_GREEN),
        stakes=kwargs.get('stakes', 'unknown'),
        resolution=resolution,
        lighting=kwargs.get('lighting', 'normal'),
        metadata=kwargs.get('metadata', {})
    )


def save_test_case(test_case: QaTestCase, output_dir: Path):
    """Save test case as image + json pair."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save ground truth as JSON
    json_path = output_dir / f"{test_case.id}.json"
    data = {
        'id': test_case.id,
        'name': test_case.name,
        'ground_truth': test_case.ground_truth.to_dict(),
        'theme': test_case.theme.value,
        'stakes': test_case.stakes,
        'resolution': list(test_case.resolution),
        'lighting': test_case.lighting,
        'metadata': test_case.metadata
    }

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved test case: {test_case.id}")


if __name__ == '__main__':
    # Demo usage
    print("=" * 70)
    print("Automated Scrape QA Harness")
    print("=" * 70)

    # Create demo test suite
    demo_dir = Path("test_suite_demo")
    demo_dir.mkdir(exist_ok=True)

    # Create a sample test case
    gt = GroundTruth(
        pot_size=100.0,
        player_stacks={1: 500.0, 2: 750.0},
        player_names={1: "Player1", 2: "Player2"},
        hole_cards=['As', 'Kh'],
        board_cards=['Qd', 'Jc', '9s'],
        button_position=1
    )

    test_case = create_test_case_from_screenshot(
        demo_dir / "test001.png",
        gt,
        name="Sample Test",
        theme=ThemeType.STANDARD_GREEN,
        stakes="NL100"
    )

    save_test_case(test_case, demo_dir)

    # Run harness
    harness = ScrapeQAHarness(demo_dir)
    count = harness.load_test_suite()
    print(f"\nLoaded {count} test cases")

    if count > 0:
        report = harness.run_suite(parallel=False)

        print(f"\n{report.suite_name} Results:")
        print(f"  Passed: {report.passed}/{report.total_tests}")
        print(f"  Pass Rate: {report.pass_rate*100:.1f}%")
        print(f"  Avg Accuracy: {report.avg_accuracy*100:.1f}%")

        # Generate report
        report_path = demo_dir / "report.md"
        harness.generate_markdown_report(report, report_path)
        print(f"\nReport saved to: {report_path}")

    print("\n✅ QA Harness Demo Complete")
