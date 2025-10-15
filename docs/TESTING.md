# Testing Guide

## Comprehensive Test Suite

PokerTool includes a comprehensive test runner (`test_everything.py`) that executes all 1199 tests and provides detailed logging and reporting.

### Quick Start

```bash
# Run all tests with detailed logging
python test_everything.py

# Quick tests only (excludes system tests)
python test_everything.py --quick

# System/integration tests only
python test_everything.py --system

# Verbose output
python test_everything.py --verbose

# With coverage report
python test_everything.py --coverage
```

### Test Organization

Tests are organized in the `tests/` directory:

- **tests/gui/** - GUI and interface tests
- **tests/system/** - System integration tests
- **tests/** - Root level unit tests

**Important:** Production tests go in `tests/` folder only. Roll-forward scripts go in `forwardscripts/`.

### Test Configuration

Pytest is configured in `pyproject.toml` with:

- **Timeout:** 300 seconds (5 minutes) per test
- **Markers:** `slow`, `system`, `unit`, `gui`, `ml`, `scraper`, `asyncio`
- **Output:** Verbose, short tracebacks, colored output

### Test Logs

All test runs generate timestamped logs in `test_logs/`:

- **test_run_YYYYMMDD_HHMMSS.log** - Detailed execution logs
- **test_results_YYYYMMDD_HHMMSS.json** - Machine-readable results
- **coverage_html/** - HTML coverage reports (with --coverage)

View latest results:
```bash
ls -t test_logs/test_run_*.log | head -1 | xargs cat
```

### Recent Fixes

#### Pytest Collection Warnings (Fixed)

The following classes were renamed to avoid pytest mistaking them for test classes:

- `TestCase` → `QaTestCase` (in `scrape_qa_harness.py`)
- `TestResult` → `QaTestResult` (in `scrape_qa_harness.py`)
- `TestType` → `StatTestType` (in `stats_validator.py`)

**Reason:** Pytest collects any class starting with "Test" as a test class. These were dataclasses and enums, not test classes.

#### Process Cleanup (Fixed)

Added automatic cleanup of old pokertool processes on startup in `start.py`:

- Kills old processes before launching GUI
- Works on Windows, macOS, and Linux
- Non-blocking - continues even if cleanup fails

### Running Specific Tests

```bash
# Run specific test file
python -m pytest tests/gui/test_suit_enum.py -v

# Run specific test class
python -m pytest tests/gui/test_suit_enum.py::TestSuitEnum -v

# Run specific test method
python -m pytest tests/gui/test_suit_enum.py::TestSuitEnum::test_suit_values -v

# Run tests matching pattern
python -m pytest -k "test_suit" -v

# Run tests with marker
python -m pytest -m "not slow" -v
```

### Continuous Integration

The test suite is designed for CI/CD integration:

```bash
# CI-friendly run with JSON output
python test_everything.py --quick
# Check exit code: 0 = pass, non-zero = fail

# View JSON results for CI dashboard
cat test_logs/test_results_*.json | jq .
```

### Troubleshooting

**Timeout Issues:**

- Tests timeout at 300 seconds per test
- Install `pytest-timeout` for better timeout handling: `pip install pytest-timeout`

**Collection Warnings:**

- Ensure non-test classes don't start with "Test"
- Add markers to `pyproject.toml` if using custom markers

**Import Errors:**

- Ensure `PYTHONPATH` includes `src/` directory
- The test runner sets this automatically

## Test Coverage

To generate coverage reports:

```bash
# HTML coverage report
python test_everything.py --coverage

# View coverage report
open test_logs/coverage_html/index.html
```

Current test statistics:

- **1199 total tests**
- **69+ test files**
- **Multiple test categories:** unit, system, GUI, ML, scraper
