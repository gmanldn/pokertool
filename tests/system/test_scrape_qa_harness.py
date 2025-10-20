#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for Automated Scrape QA Harness
======================================

SCRAPE-014: Automated Scrape QA Harness Tests

Tests cover:
- Test case creation and loading
- Ground truth comparison
- Report generation
- Parallel execution
- Threshold checking
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import numpy as np

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from pokertool.scrape_qa_harness import (
    ScrapeQAHarness,
    TestCase,
    GroundTruth,
    FieldType,
    ThemeType,
    FieldDiff,
    TestResult,
    SuiteReport,
    create_test_case_from_screenshot,
    save_test_case,
    CV2_AVAILABLE
)


class TestGroundTruth:
    """Test GroundTruth data structure."""

    def test_create_ground_truth(self):
        """Test creating ground truth."""
        gt = GroundTruth(
            pot_size=100.0,
            player_stacks={1: 500.0, 2: 750.0},
            player_names={1: "Alice", 2: "Bob"},
            hole_cards=['As', 'Kh'],
            board_cards=['Qd', 'Jc', '9s']
        )

        assert gt.pot_size == 100.0
        assert gt.player_stacks[1] == 500.0
        assert gt.player_names[2] == "Bob"
        assert len(gt.hole_cards) == 2
        assert len(gt.board_cards) == 3

    def test_to_dict(self):
        """Test converting to dictionary."""
        gt = GroundTruth(
            pot_size=100.0,
            blinds=(5.0, 10.0)
        )

        d = gt.to_dict()

        assert d['pot_size'] == 100.0
        assert d['blinds'] == [5.0, 10.0]  # Tuple converted to list

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            'pot_size': 200.0,
            'player_stacks': {1: 300.0},
            'blinds': [10.0, 20.0]
        }

        gt = GroundTruth.from_dict(data)

        assert gt.pot_size == 200.0
        assert gt.player_stacks[1] == 300.0
        assert gt.blinds == (10.0, 20.0)  # List converted to tuple


class TestTestCase:
    """Test TestCase data structure."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_create_test_case(self, temp_dir):
        """Test creating test case."""
        gt = GroundTruth(pot_size=100.0)
        image_path = temp_dir / "test.png"
        image_path.touch()  # Create empty file

        tc = TestCase(
            id="test001",
            name="Test Case 1",
            image_path=image_path,
            ground_truth=gt,
            theme=ThemeType.STANDARD_GREEN,
            stakes="NL10",
            resolution=(1920, 1080),
            lighting="normal"
        )

        assert tc.id == "test001"
        assert tc.ground_truth.pot_size == 100.0
        assert tc.theme == ThemeType.STANDARD_GREEN

    def test_compute_hash(self, temp_dir):
        """Test hash computation."""
        gt = GroundTruth()
        image_path = temp_dir / "test.png"

        # Write some data to file
        with open(image_path, 'wb') as f:
            f.write(b'test image data')

        tc = TestCase(
            id="test001",
            name="Test",
            image_path=image_path,
            ground_truth=gt,
            theme=ThemeType.STANDARD_GREEN,
            stakes="NL10",
            resolution=(1920, 1080),
            lighting="normal"
        )

        hash1 = tc.compute_hash()
        assert len(hash1) == 32  # MD5 hash length

        # Same file should give same hash
        hash2 = tc.compute_hash()
        assert hash1 == hash2

        # Different file should give different hash
        with open(image_path, 'wb') as f:
            f.write(b'different data')

        hash3 = tc.compute_hash()
        assert hash3 != hash1


class TestFieldComparison:
    """Test field comparison methods."""

    @pytest.fixture
    def harness(self, temp_dir):
        """Create harness instance."""
        return ScrapeQAHarness(temp_dir)

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_compare_numeric_exact(self, harness):
        """Test numeric comparison with exact match."""
        diff = harness._compare_numeric(FieldType.POT_SIZE, 100.0, 100.0)

        assert diff.match is True
        assert diff.expected == 100.0
        assert diff.actual == 100.0

    def test_compare_numeric_tolerance(self, harness):
        """Test numeric comparison within tolerance."""
        # 1% tolerance
        diff = harness._compare_numeric(FieldType.POT_SIZE, 100.0, 100.5)

        assert diff.match is True  # Within 1% tolerance

    def test_compare_numeric_out_of_tolerance(self, harness):
        """Test numeric comparison outside tolerance."""
        diff = harness._compare_numeric(FieldType.POT_SIZE, 100.0, 105.0)

        assert diff.match is False  # Outside 1% tolerance

    def test_compare_numeric_missing(self, harness):
        """Test numeric comparison with missing value."""
        diff = harness._compare_numeric(FieldType.POT_SIZE, 100.0, None)

        assert diff.match is False
        assert diff.actual is None
        assert "Missing" in diff.notes

    def test_compare_string_exact(self, harness):
        """Test string comparison with exact match."""
        diff = harness._compare_string(FieldType.PLAYER_NAME, "Alice", "Alice")

        assert diff.match is True

    def test_compare_string_case_insensitive(self, harness):
        """Test case-insensitive string comparison."""
        diff = harness._compare_string(FieldType.PLAYER_NAME, "Alice", "ALICE")

        assert diff.match is True

    def test_compare_string_whitespace(self, harness):
        """Test string comparison ignores whitespace."""
        diff = harness._compare_string(FieldType.PLAYER_NAME, "Alice", "  Alice  ")

        assert diff.match is True

    def test_compare_cards_exact(self, harness):
        """Test card comparison with exact match."""
        diff = harness._compare_cards(
            FieldType.HOLE_CARDS,
            ['As', 'Kh'],
            ['As', 'Kh']
        )

        assert diff.match is True

    def test_compare_cards_order_independent(self, harness):
        """Test card comparison is order-independent."""
        diff = harness._compare_cards(
            FieldType.HOLE_CARDS,
            ['As', 'Kh'],
            ['Kh', 'As']  # Different order
        )

        assert diff.match is True

    def test_compare_cards_case_insensitive(self, harness):
        """Test card comparison is case-insensitive."""
        diff = harness._compare_cards(
            FieldType.HOLE_CARDS,
            ['As', 'Kh'],
            ['as', 'kh']
        )

        assert diff.match is True

    def test_compare_cards_mismatch(self, harness):
        """Test card comparison with mismatch."""
        diff = harness._compare_cards(
            FieldType.HOLE_CARDS,
            ['As', 'Kh'],
            ['As', 'Qh']  # Different card
        )

        assert diff.match is False

    def test_compare_exact_match(self, harness):
        """Test exact comparison with match."""
        diff = harness._compare_exact(FieldType.BUTTON_POSITION, 3, 3)

        assert diff.match is True

    def test_compare_exact_mismatch(self, harness):
        """Test exact comparison with mismatch."""
        diff = harness._compare_exact(FieldType.BUTTON_POSITION, 3, 5)

        assert diff.match is False


class TestTestCaseLoading:
    """Test loading test cases."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_load_from_manifest(self, temp_dir):
        """Test loading test cases from manifest."""
        # Create manifest
        manifest = {
            'test_cases': [
                {
                    'id': 'test001',
                    'name': 'Test Case 1',
                    'image_path': 'test001.png',
                    'ground_truth': {
                        'pot_size': 100.0,
                        'player_stacks': {1: 500.0}
                    },
                    'theme': 'standard_green',
                    'stakes': 'NL10',
                    'resolution': [1920, 1080],
                    'lighting': 'normal'
                }
            ]
        }

        manifest_path = temp_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)

        # Create dummy image
        (temp_dir / "test001.png").touch()

        # Load
        harness = ScrapeQAHarness(temp_dir)
        count = harness.load_test_suite()

        assert count == 1
        assert len(harness.test_cases) == 1
        assert harness.test_cases[0].id == 'test001'
        assert harness.test_cases[0].ground_truth.pot_size == 100.0

    def test_discover_test_cases(self, temp_dir):
        """Test auto-discovery of test cases."""
        # Create image + json pair
        image_path = temp_dir / "test001.png"
        image_path.touch()

        json_path = temp_dir / "test001.json"
        data = {
            'name': 'Auto Test',
            'ground_truth': {
                'pot_size': 200.0
            },
            'theme': 'betfair_purple',
            'stakes': 'NL25'
        }

        with open(json_path, 'w') as f:
            json.dump(data, f)

        # Discover
        harness = ScrapeQAHarness(temp_dir)
        count = harness.load_test_suite()

        assert count == 1
        assert harness.test_cases[0].id == 'test001'
        assert harness.test_cases[0].ground_truth.pot_size == 200.0
        assert harness.test_cases[0].theme == ThemeType.BETFAIR_PURPLE


class TestTestExecution:
    """Test running test cases."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def mock_scraper(self):
        """Mock scraper function."""
        def scraper(image_path):
            # Return perfect match
            return {
                'pot_size': 100.0,
                'player_stacks': {1: 500.0},
                'player_names': {1: "Alice"},
                'hole_cards': ['As', 'Kh'],
                'board_cards': ['Qd', 'Jc', '9s'],
                'button_position': 1
            }
        return scraper

    def test_run_test_case_perfect_match(self, temp_dir, mock_scraper):
        """Test running test case with perfect match."""
        gt = GroundTruth(
            pot_size=100.0,
            player_stacks={1: 500.0},
            player_names={1: "Alice"},
            hole_cards=['As', 'Kh'],
            board_cards=['Qd', 'Jc', '9s'],
            button_position=1
        )

        image_path = temp_dir / "test.png"
        image_path.touch()

        test_case = TestCase(
            id="test001",
            name="Perfect Match Test",
            image_path=image_path,
            ground_truth=gt,
            theme=ThemeType.STANDARD_GREEN,
            stakes="NL10",
            resolution=(1920, 1080),
            lighting="normal"
        )

        harness = ScrapeQAHarness(temp_dir, scraper_fn=mock_scraper)
        result = harness.run_test_case(test_case)

        assert result.success is True
        assert result.accuracy == 1.0
        assert all(diff.match for diff in result.diffs)

    def test_run_test_case_partial_match(self, temp_dir):
        """Test running test case with partial match."""
        def partial_scraper(image_path):
            return {
                'pot_size': 100.0,  # Match
                'player_stacks': {1: 999.0},  # Mismatch
                'player_names': {1: "Alice"},  # Match
                'hole_cards': ['As', 'Kh'],  # Match
                'board_cards': ['Qd', 'Jc', '9s'],  # Match
                'button_position': 2  # Mismatch
            }

        gt = GroundTruth(
            pot_size=100.0,
            player_stacks={1: 500.0},
            player_names={1: "Alice"},
            hole_cards=['As', 'Kh'],
            board_cards=['Qd', 'Jc', '9s'],
            button_position=1
        )

        image_path = temp_dir / "test.png"
        image_path.touch()

        test_case = TestCase(
            id="test001",
            name="Partial Match Test",
            image_path=image_path,
            ground_truth=gt,
            theme=ThemeType.STANDARD_GREEN,
            stakes="NL10",
            resolution=(1920, 1080),
            lighting="normal"
        )

        harness = ScrapeQAHarness(temp_dir, scraper_fn=partial_scraper)
        result = harness.run_test_case(test_case)

        # Should have some matches and some failures
        assert result.accuracy < 1.0
        assert result.accuracy > 0.0

        failed = result.get_failed_fields()
        assert FieldType.PLAYER_STACK in failed
        assert FieldType.BUTTON_POSITION in failed


class TestSuiteExecution:
    """Test running full test suite."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_suite(self, temp_dir):
        """Create sample test suite."""
        # Create 3 test cases
        for i in range(3):
            image_path = temp_dir / f"test{i:03d}.png"
            image_path.touch()

            json_path = temp_dir / f"test{i:03d}.json"
            data = {
                'name': f'Test {i}',
                'ground_truth': {
                    'pot_size': 100.0 * (i + 1)
                },
                'theme': 'standard_green',
                'stakes': 'NL10'
            }

            with open(json_path, 'w') as f:
                json.dump(data, f)

        return temp_dir

    def test_run_suite_sequential(self, sample_suite):
        """Test running suite sequentially."""
        harness = ScrapeQAHarness(sample_suite)
        harness.load_test_suite()

        report = harness.run_suite(parallel=False)

        assert report.total_tests == 3
        assert report.passed + report.failed == 3
        assert report.total_execution_time_ms > 0

    def test_run_suite_parallel(self, sample_suite):
        """Test running suite in parallel."""
        harness = ScrapeQAHarness(sample_suite)
        harness.load_test_suite()

        report = harness.run_suite(parallel=True, max_workers=2)

        assert report.total_tests == 3
        assert report.passed + report.failed == 3

    def test_suite_report_metrics(self, sample_suite):
        """Test suite report metrics."""
        harness = ScrapeQAHarness(sample_suite)
        harness.load_test_suite()

        report = harness.run_suite(parallel=False)

        # Check report structure
        assert hasattr(report, 'pass_rate')
        assert hasattr(report, 'avg_accuracy')
        assert 0.0 <= report.pass_rate <= 1.0
        assert 0.0 <= report.avg_accuracy <= 1.0


class TestReportGeneration:
    """Test report generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_report(self):
        """Create sample report."""
        results = [
            TestResult(
                test_case_id="test001",
                success=True,
                execution_time_ms=100.0,
                diffs=[
                    FieldDiff(FieldType.POT_SIZE, 100.0, 100.0, True)
                ],
                accuracy=1.0
            ),
            TestResult(
                test_case_id="test002",
                success=False,
                execution_time_ms=150.0,
                diffs=[
                    FieldDiff(FieldType.POT_SIZE, 200.0, 180.0, False)
                ],
                accuracy=0.5
            )
        ]

        return SuiteReport(
            suite_name="test_suite",
            total_tests=2,
            passed=1,
            failed=1,
            total_execution_time_ms=250.0,
            results=results,
            per_field_accuracy={FieldType.POT_SIZE: 0.5}
        )

    def test_markdown_report_generation(self, temp_dir, sample_report):
        """Test markdown report generation."""
        harness = ScrapeQAHarness(temp_dir)

        output_path = temp_dir / "report.md"
        harness.generate_markdown_report(sample_report, output_path)

        assert output_path.exists()

        # Read and check content
        content = output_path.read_text()
        assert "Scrape QA Report" in content
        assert "Summary" in content
        assert "Per-Field Accuracy" in content

    def test_report_pass_rate(self, sample_report):
        """Test pass rate calculation."""
        assert sample_report.pass_rate == 0.5  # 1/2

    def test_report_avg_accuracy(self, sample_report):
        """Test average accuracy calculation."""
        assert sample_report.avg_accuracy == 0.75  # (1.0 + 0.5) / 2


class TestThresholdChecking:
    """Test threshold checking."""

    def test_check_thresholds_pass(self):
        """Test threshold checking with passing report."""
        report = SuiteReport(
            suite_name="test",
            total_tests=10,
            passed=9,
            failed=1,
            total_execution_time_ms=1000.0,
            results=[],
            per_field_accuracy={
                FieldType.POT_SIZE: 0.9,
                FieldType.PLAYER_NAME: 0.85
            }
        )

        harness = ScrapeQAHarness(Path())
        passed, violations = harness.check_thresholds(
            report,
            min_pass_rate=0.8,
            min_field_accuracy=0.7
        )

        assert passed is True
        assert len(violations) == 0

    def test_check_thresholds_fail_pass_rate(self):
        """Test threshold checking with low pass rate."""
        report = SuiteReport(
            suite_name="test",
            total_tests=10,
            passed=6,  # 60% pass rate
            failed=4,
            total_execution_time_ms=1000.0,
            results=[],
            per_field_accuracy={}
        )

        harness = ScrapeQAHarness(Path())
        passed, violations = harness.check_thresholds(
            report,
            min_pass_rate=0.8  # Requires 80%
        )

        assert passed is False
        assert len(violations) > 0
        assert any("Pass rate" in v for v in violations)

    def test_check_thresholds_fail_field_accuracy(self):
        """Test threshold checking with low field accuracy."""
        report = SuiteReport(
            suite_name="test",
            total_tests=10,
            passed=10,
            failed=0,
            total_execution_time_ms=1000.0,
            results=[],
            per_field_accuracy={
                FieldType.POT_SIZE: 0.5  # Below threshold
            }
        )

        harness = ScrapeQAHarness(Path())
        passed, violations = harness.check_thresholds(
            report,
            min_field_accuracy=0.7  # Requires 70%
        )

        assert passed is False
        assert len(violations) > 0
        assert any("pot_size" in v for v in violations)


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_create_test_case_from_screenshot(self, temp_dir):
        """Test creating test case from screenshot."""
        image_path = temp_dir / "test.png"
        image_path.touch()

        gt = GroundTruth(pot_size=100.0)

        test_case = create_test_case_from_screenshot(
            image_path,
            gt,
            name="My Test",
            theme=ThemeType.BETFAIR_PURPLE,
            stakes="NL50"
        )

        assert test_case.id == "test"
        assert test_case.name == "My Test"
        assert test_case.theme == ThemeType.BETFAIR_PURPLE
        assert test_case.stakes == "NL50"

    def test_save_test_case(self, temp_dir):
        """Test saving test case."""
        gt = GroundTruth(
            pot_size=100.0,
            player_names={1: "Alice"}
        )

        image_path = temp_dir / "source" / "test.png"
        image_path.parent.mkdir(exist_ok=True)
        image_path.touch()

        test_case = TestCase(
            id="test001",
            name="Test Case",
            image_path=image_path,
            ground_truth=gt,
            theme=ThemeType.STANDARD_GREEN,
            stakes="NL10",
            resolution=(1920, 1080),
            lighting="normal"
        )

        output_dir = temp_dir / "output"
        save_test_case(test_case, output_dir)

        # Check JSON was created
        json_path = output_dir / "test001.json"
        assert json_path.exists()

        # Load and verify
        with open(json_path, 'r') as f:
            data = json.load(f)

        assert data['id'] == 'test001'
        assert data['ground_truth']['pot_size'] == 100.0
        assert data['ground_truth']['player_names']['1'] == "Alice"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '-s'])
