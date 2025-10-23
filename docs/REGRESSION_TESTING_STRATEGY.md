# PokerTool Regression Testing Strategy

**Version:** 1.0.0
**Date:** 2025-10-23
**Status:** Active
**Owner:** Development Team

---

## Executive Summary

This document outlines the comprehensive regression testing strategy for PokerTool v101+. Based on a thorough audit, **only 31% of modules (75/242) have test coverage**, leaving significant regression risk. This strategy provides a systematic approach to achieve 95%+ coverage across all critical systems.

### Key Findings
- **Total Source Modules:** 242
- **Modules WITH Tests:** 75 (31%)
- **Modules WITHOUT Tests:** 167 (69%)
- **Total Test Files:** 136 Python + 297 TypeScript = 433 tests
- **Total Test Cases:** 2,252 (as of v101.0.0)
- **Current Coverage:** 95% on tested modules, but only 31% module coverage

---

## 1. Testing Objectives

### Primary Goals
1. **Prevent Regressions:** Ensure no feature or fix is lost between versions
2. **Achieve 95%+ Coverage:** Comprehensive coverage across all critical paths
3. **Automated Detection:** Catch regressions before they reach production
4. **Version Tracking:** Link tests to version history to verify features work as implemented

### Success Metrics
- **Module Coverage:** 95%+ of all modules have dedicated tests
- **Line Coverage:** 90%+ line coverage on critical paths
- **Test Execution Time:** < 5 minutes for smoke tests, < 30 minutes for full suite
- **Regression Detection Rate:** 100% of known regressions caught before release
- **Test Reliability:** < 1% flaky test rate

---

## 2. Testing Pyramid Strategy

```
                    ┌─────────────┐
                    │   Manual    │  <5% - Exploratory testing
                    │  Exploratory │
                    └─────────────┘
                  ┌─────────────────┐
                  │    End-to-End   │  10% - Critical user journeys
                  │  Integration    │
                  └─────────────────┘
              ┌─────────────────────────┐
              │   Integration Tests     │  25% - Multi-component scenarios
              │  (API, DB, Detection)   │
              └─────────────────────────┘
          ┌─────────────────────────────────┐
          │       Unit Tests                │  60% - Individual module testing
          │  (Functions, Classes, Logic)    │
          └─────────────────────────────────┘
```

---

## 3. Test Coverage Gaps & Priorities

### CRITICAL PRIORITY (Implement Immediately)

#### Core Application Entry Points
- **api.py** - RESTful API endpoints (0% coverage)
- **database.py** - Production database layer (0% coverage)
- **scrape.py** - Screen scraping core (0% coverage)
- **gui.py** / **enhanced_gui.py** - Main UI (0% coverage)
- **smarthelper_engine.py** - Decision engine (0% coverage)
- **cli.py** - Command-line interface (0% coverage)

**Impact:** These are the application's critical path. Regressions here affect ALL users.

**Timeline:** Week 1-2

---

### HIGH PRIORITY (Implement Within Sprint)

#### Detection & Scraping Systems (38 modules, ~0% coverage)
**Detection Infrastructure:**
- detection_utils.py, detection_config.py, detection_cache.py
- detection_logger.py, detection_accuracy_tracker.py
- detection_fps_counter.py, detection_fallback.py
- detection_sanity_checks.py, detection_event_batcher.py

**Scraping Modules:**
- scraping_accuracy_system.py, scraping_master_system.py
- scraping_reliability_system.py, scraping_speed_optimizer.py
- poker_screen_scraper.py, poker_screen_scraper_betfair.py
- chrome_devtools_scraper.py, browser_tab_capture.py

**Card & Player Detection:**
- card_recognizer.py, card_confidence_scorer.py
- player_action_detector.py, player_detection_confidence.py

**OCR & Image Processing:**
- ocr_recognition.py, image_preprocessor.py
- smart_ocr_cache.py, smart_poker_detector.py

**Impact:** Detection/scraping is the foundation. Without tests, any change risks breaking the entire pipeline.

**Timeline:** Week 3-6

---

### MEDIUM PRIORITY (Implement Within Quarter)

#### Game Logic & Strategy (22 modules, mixed coverage)
**GTO & Solvers:**
- gto_solver.py, gto_ranges.py, cfr_plus.py
- qaoa_solver.py (quantum optimization)
- ✓ gto_calculator.py (HAS TESTS)
- ✓ nash_solver.py (HAS TESTS)

**Opponent Modeling:**
- opponent_profiler.py, opponent_profiling.py
- ml_opponent_modeling.py, pattern_detector.py
- exploitative_engine.py

**Decision Making:**
- live_decision_engine.py, smarthelper_cache.py
- smarthelper_websocket.py

**Calculators:**
- pot_odds_calculator.py, pot_odds_display.py
- variance_calculator.py
- ✓ equity_calculator.py (HAS TESTS)

**Impact:** Strategy modules affect decision quality. Regressions cause incorrect recommendations.

**Timeline:** Month 2-3

---

### LOWER PRIORITY (Implement As Time Permits)

#### Infrastructure & Utilities (40+ modules, mixed coverage)
**Threading:** thread_manager.py, thread_cleanup.py, thread_utils.py
**Error Handling:** error_handler.py, error_middleware.py, error_recovery.py
**Performance:** performance_telemetry.py, query_profiler.py
**Validation:** input_sanitizer.py, input_validator.py, data_validation.py
**GUI Components:** Enhanced GUI components (11 modules)

**Impact:** Infrastructure issues cause crashes/performance problems but don't affect core logic.

**Timeline:** Ongoing, continuous improvement

---

## 4. Test Types & Implementation Strategy

### 4.1 Unit Tests (60% of suite)

**Scope:** Individual functions, classes, and modules in isolation

**Pattern:**
```python
# tests/unit/test_detection_utils.py
import pytest
from pokertool.detection_utils import format_confidence, classify_detection_quality

def test_format_confidence_percentage():
    """Regression: v98.0.0 - confidence formatting"""
    assert format_confidence(0.9523) == "95.2%"
    assert format_confidence(0.123) == "12.3%"

def test_classify_detection_quality():
    """Regression: v100.0.0 - quality classification thresholds"""
    assert classify_detection_quality(0.95) == "excellent"
    assert classify_detection_quality(0.80) == "good"
    assert classify_detection_quality(0.60) == "fair"
    assert classify_detection_quality(0.40) == "poor"
```

**Coverage Goals:**
- All public functions/methods
- Edge cases (null, empty, invalid inputs)
- Error conditions
- Boundary conditions

---

### 4.2 Integration Tests (25% of suite)

**Scope:** Multi-component interactions (API + DB, Detection + OCR, etc.)

**Pattern:**
```python
# tests/integration/test_detection_pipeline.py
import pytest
from pokertool.card_recognizer import CardRecognizer
from pokertool.detection_cache import DetectionCache
from pokertool.detection_accuracy_tracker import AccuracyTracker

def test_detection_pipeline_with_caching():
    """Regression: v99.0.0 - cached detections maintain accuracy"""
    recognizer = CardRecognizer()
    cache = DetectionCache()
    tracker = AccuracyTracker()

    # First detection (cache miss)
    result1 = recognizer.detect_cards(test_image)
    cache.store(test_image_hash, result1)
    tracker.record(result1)

    # Second detection (cache hit)
    result2 = recognizer.detect_cards(test_image)
    cached = cache.get(test_image_hash)

    assert result1 == cached
    assert tracker.get_accuracy() >= 0.99
```

**Coverage Goals:**
- API endpoint + database interactions
- Detection pipeline end-to-end
- SmartHelper recommendation flow
- Error propagation across components

---

### 4.3 Smoke Tests (5-10 minutes runtime)

**Scope:** Fast validation that critical paths work

**Pattern:**
```python
# tests/smoke/test_critical_paths.py
import pytest

@pytest.mark.smoke
def test_api_server_starts():
    """Regression: v100.0.0 - API starts without errors"""
    from pokertool.api import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200

@pytest.mark.smoke
def test_database_connects():
    """Regression: v95.0.0 - database connection works"""
    from pokertool.database import get_db_connection
    conn = get_db_connection()
    assert conn.is_connected()

@pytest.mark.smoke
def test_gui_launches():
    """Regression: v82.0.0 - GUI window opens"""
    from pokertool.gui import PokerToolGUI
    gui = PokerToolGUI()
    assert gui.root is not None
```

**Run Frequency:** On every commit (pre-commit hook)

---

### 4.4 Regression Tests (Version-Specific)

**Scope:** Tests that verify specific fixes/features from version history

**Pattern:**
```python
# tests/regression/test_v100_fixes.py
import pytest

def test_chart_null_value_handling():
    """Regression: v100.3.1 - Fix null values in Chart.js tooltip callbacks

    Commit: 317e225e9 - fix: handle null values in Chart.js tooltip callbacks
    Issue: Chart.js crashes when tooltips encounter null data points
    Fix: Added null checks in tooltip callback functions
    """
    from pokertool_frontend.components import EquityChart

    data_with_nulls = [
        {"label": "Preflop", "equity": 0.45},
        {"label": "Flop", "equity": None},  # Null value
        {"label": "Turn", "equity": 0.62},
    ]

    chart = EquityChart(data=data_with_nulls)
    tooltip_text = chart.render_tooltip(index=1)

    # Should handle null gracefully
    assert tooltip_text == "Flop: N/A"  # Or similar safe default

def test_betfair_detection_accuracy():
    """Regression: v97.0.0 - Betfair scraper 99.2% accuracy

    Commit: Multiple commits - Betfair detection improvements
    Feature: 35 Betfair-specific optimizations
    Target: 99.2% accuracy, 40-80ms latency
    """
    from pokertool.modules.poker_screen_scraper_betfair import BetfairScraper

    scraper = BetfairScraper()

    # Test with known Betfair screenshot fixtures
    results = []
    for fixture in load_betfair_fixtures():
        detected = scraper.scrape(fixture.image)
        results.append(detected == fixture.expected)

    accuracy = sum(results) / len(results)
    assert accuracy >= 0.992  # 99.2% minimum
```

**Versioning Strategy:**
- Each major release gets a regression test file
- Tests reference git commit hashes
- Tests document what feature/fix they protect

---

### 4.5 Property-Based Tests (Edge Case Discovery)

**Scope:** Hypothesis-driven tests that discover edge cases

**Pattern:**
```python
# tests/property/test_equity_properties.py
from hypothesis import given, strategies as st
from pokertool.equity_calculator import calculate_equity

@given(
    hand=st.lists(st.sampled_from(['Ah','Kd','Qc']), min_size=2, max_size=2),
    board=st.lists(st.sampled_from(['Ts','9h','8c']), min_size=0, max_size=5)
)
def test_equity_always_between_0_and_1(hand, board):
    """Property: Equity is always in range [0.0, 1.0]"""
    equity = calculate_equity(hand, board)
    assert 0.0 <= equity <= 1.0

@given(
    confidence=st.floats(min_value=0.0, max_value=1.0)
)
def test_confidence_formatting_roundtrip(confidence):
    """Property: format_confidence -> parse should roundtrip"""
    formatted = format_confidence(confidence)
    parsed = parse_confidence(formatted)
    assert abs(parsed - confidence) < 0.001  # Allow for rounding
```

**Benefit:** Discovers edge cases you wouldn't think to test manually

---

## 5. Test Organization Structure

```
/tests/
├── unit/                          # Unit tests (isolated modules)
│   ├── detection/
│   │   ├── test_detection_utils.py
│   │   ├── test_detection_cache.py
│   │   └── test_card_recognizer.py
│   ├── strategy/
│   │   ├── test_gto_solver.py
│   │   └── test_opponent_profiler.py
│   └── infrastructure/
│       ├── test_thread_manager.py
│       └── test_error_handler.py
│
├── integration/                   # Multi-component tests
│   ├── test_detection_pipeline.py
│   ├── test_api_database.py
│   └── test_smarthelper_flow.py
│
├── smoke/                         # Fast critical path tests
│   ├── test_startup.py            ✓ EXISTS
│   ├── test_shutdown.py           ✓ EXISTS
│   └── test_smoke_suite.py        ✓ EXISTS
│
├── regression/                    # Version-specific regression tests
│   ├── test_v100_fixes.py
│   ├── test_v99_features.py
│   └── test_v98_enhancements.py
│
├── system/                        # System-level tests
│   └── (68 existing test files)  ✓ EXISTS
│
├── property/                      # Property-based tests
│   └── test_poker_properties.py   ✓ EXISTS
│
├── e2e/                          # End-to-end user workflows
│   └── test_user_workflows.py     ✓ EXISTS
│
├── chaos/                        # Chaos engineering
│   └── (chaos tests)              ✓ EXISTS
│
├── reliability/                  # Reliability tests
│   └── test_system_reliability.py ✓ EXISTS (NEW)
│
└── fixtures/                     # Test data and fixtures
    ├── betfair_screenshots/
    ├── detection_test_images/
    └── api_test_data/
```

---

## 6. Version History Regression Testing

### Strategy: Map Tests to Version History

Each test should reference the version/commit where the feature was added:

```python
def test_feature_name():
    """Regression: v{VERSION} - {FEATURE_DESCRIPTION}

    Commit: {COMMIT_HASH}
    Issue: {GITHUB_ISSUE} (optional)
    PR: {PULL_REQUEST} (optional)
    """
    # Test implementation
```

### Implementation Plan

#### Phase 1: Catalog Existing Features (DONE ✓)
- Analyzed git history (200+ commits from last 6 months)
- Identified 242 source modules
- Mapped existing test coverage (75 modules with tests)

#### Phase 2: Systematic Regression Test Creation

**Week 1-2: Critical Modules**
Create comprehensive tests for:
- api.py (API endpoints)
- database.py (data persistence)
- scrape.py (scraping core)
- gui.py / enhanced_gui.py (UI)
- smarthelper_engine.py (decision engine)
- cli.py (CLI)

**Week 3-6: Detection Pipeline**
Create tests for 38 detection/scraping modules:
- Detection utilities and configuration (13 modules)
- Scraping systems (10 modules)
- Card/player detection (6 modules)
- OCR and image processing (5 modules)
- Browser-based scraping (4 modules)

**Week 7-10: Strategy & Logic**
Create tests for 22 game logic modules:
- GTO solvers (5 modules)
- Opponent modeling (5 modules)
- Decision engines (4 modules)
- Calculators (4 modules)
- Range tools (4 modules)

**Week 11-12: Infrastructure**
Create tests for 40+ infrastructure modules:
- Threading and concurrency
- Error handling and recovery
- Performance monitoring
- Validation and security

---

## 7. Automated Regression Detection

### 7.1 CI/CD Pipeline Integration

```yaml
# .github/workflows/regression-tests.yml
name: Regression Tests

on:
  push:
    branches: [develop, master]
  pull_request:
    branches: [develop, master]

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v3
      - name: Run smoke tests
        run: pytest -m smoke --timeout=60

  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src/pokertool --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  regression-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v3
      - name: Run regression tests
        run: pytest tests/regression/ -v
      - name: Check version-specific tests
        run: python scripts/check_version_tests.py

  full-suite:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    needs: [smoke-tests, unit-tests]
    steps:
      - uses: actions/checkout@v3
      - name: Run full test suite
        run: python tests/test_everything.py --coverage
```

### 7.2 Pre-commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running pre-commit regression checks..."

# Run smoke tests (fast validation)
pytest -m smoke --timeout=60 -q

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed. Commit aborted."
    exit 1
fi

# Check for test coverage on modified files
python scripts/check_test_coverage.py --modified-only

if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Some modified files lack test coverage"
    echo "Continue anyway? (y/n)"
    read response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed"
exit 0
```

### 7.3 Automated Test Generation

For modules without tests, generate skeleton test files:

```bash
# scripts/generate_test_skeleton.py
#!/usr/bin/env python3
"""Generate test skeleton for modules without tests"""

import sys
from pathlib import Path

def generate_test_skeleton(module_path):
    """Generate basic test structure for a module"""
    module_name = module_path.stem
    test_name = f"test_{module_name}.py"

    # Extract functions/classes from module
    functions = extract_functions(module_path)
    classes = extract_classes(module_path)

    # Generate test file
    test_content = f'''"""Tests for {module_name}.py

Regression tests to ensure functionality doesn't break across versions.
"""

import pytest
from pokertool.{module_name} import *

# TODO: Add version regression tests
# Pattern:
# def test_feature_name():
#     """Regression: vX.Y.Z - feature description"""
#     # Test implementation

'''

    # Add test stubs for each function
    for func in functions:
        test_content += f'''
def test_{func}():
    """Test {func} functionality

    TODO: Add version number when regression was discovered
    TODO: Add commit hash that introduced this feature
    """
    # TODO: Implement test
    pytest.skip("Not implemented yet")
'''

    return test_content

# Usage: python scripts/generate_test_skeleton.py src/pokertool/detection_utils.py
```

---

## 8. Regression Test Maintenance

### 8.1 Test Review Process

**When Adding New Features:**
1. Write tests BEFORE implementing feature (TDD)
2. Document version number in test docstring
3. Include commit hash reference
4. Add to regression test suite

**When Fixing Bugs:**
1. Write failing test that reproduces bug
2. Fix bug
3. Verify test passes
4. Keep test as regression protection

**When Refactoring:**
1. Ensure all existing tests still pass
2. Add tests for any new code paths
3. Update test documentation if behavior changes

### 8.2 Test Maintenance Schedule

**Daily:**
- Smoke tests on every commit (pre-commit hook)
- Unit tests on every PR

**Weekly:**
- Full regression suite on develop branch
- Review test coverage reports

**Monthly:**
- Audit test quality and flakiness
- Update test documentation
- Prune obsolete tests

**Quarterly:**
- Major regression test review
- Update version-specific tests
- Add property-based tests for new modules

### 8.3 Test Quality Metrics

Monitor these metrics to ensure test health:

```python
# tests/test_quality_metrics.py
def test_suite_metrics():
    """Track overall test suite health"""
    metrics = {
        'total_tests': count_all_tests(),
        'module_coverage': calculate_module_coverage(),
        'line_coverage': get_line_coverage(),
        'flaky_test_rate': calculate_flaky_rate(),
        'avg_test_duration': get_avg_duration(),
        'tests_without_docstrings': count_undocumented_tests(),
    }

    # Assert quality standards
    assert metrics['module_coverage'] >= 0.95  # 95% module coverage
    assert metrics['line_coverage'] >= 0.90     # 90% line coverage
    assert metrics['flaky_test_rate'] < 0.01    # <1% flaky tests
    assert metrics['avg_test_duration'] < 0.5   # <500ms per test avg
    assert metrics['tests_without_docstrings'] == 0  # All documented
```

---

## 9. Rollout Timeline

### Phase 1: Foundation (Weeks 1-2) - CRITICAL
- [ ] Set up test infrastructure
- [ ] Create test templates and patterns
- [ ] Implement automated test skeleton generation
- [ ] Add tests for 6 critical modules (api, database, scrape, gui, smarthelper_engine, cli)
- [ ] Set up CI/CD pipeline with smoke tests

**Deliverable:** Critical paths have test coverage, smoke tests run on every commit

### Phase 2: Detection Pipeline (Weeks 3-6) - HIGH PRIORITY
- [ ] Add tests for 38 detection/scraping modules
- [ ] Create detection test fixtures (screenshots, expected outputs)
- [ ] Implement detection accuracy regression tests
- [ ] Add integration tests for detection pipeline

**Deliverable:** Detection system has comprehensive test coverage

### Phase 3: Strategy & Logic (Weeks 7-10) - MEDIUM PRIORITY
- [ ] Add tests for 22 game logic modules (GTO, opponent modeling, calculators)
- [ ] Create poker hand test fixtures
- [ ] Implement strategy regression tests
- [ ] Add property-based tests for poker logic

**Deliverable:** Game logic has comprehensive test coverage

### Phase 4: Infrastructure (Weeks 11-12) - LOWER PRIORITY
- [ ] Add tests for 40+ infrastructure modules
- [ ] Implement chaos engineering tests
- [ ] Add performance regression tests
- [ ] Complete test documentation

**Deliverable:** 95%+ module coverage, full regression protection

### Phase 5: Continuous Improvement (Ongoing)
- [ ] Monthly test quality audits
- [ ] Quarterly regression test reviews
- [ ] Add tests for new features immediately
- [ ] Maintain test documentation

**Deliverable:** Sustained 95%+ coverage, zero regressions

---

## 10. Success Criteria

### Short-term (1 month)
- ✅ 6 critical modules have comprehensive tests
- ✅ Smoke tests run on every commit
- ✅ CI/CD pipeline catches regressions automatically
- ✅ Test coverage reporting in place

### Medium-term (3 months)
- ✅ 95%+ module coverage (230+ modules with tests)
- ✅ 90%+ line coverage on critical paths
- ✅ All detection/scraping modules tested
- ✅ Regression tests for v95-v101 features

### Long-term (6 months)
- ✅ Zero known regressions in production
- ✅ <1% flaky test rate
- ✅ Full version history test coverage
- ✅ Automated regression detection for all commits

---

## 11. Tools & Technologies

### Testing Frameworks
- **pytest** - Primary test runner (already in use)
- **pytest-cov** - Coverage reporting
- **pytest-timeout** - Test timeouts (300s default)
- **hypothesis** - Property-based testing (already in use)

### CI/CD
- **GitHub Actions** - Automated test execution
- **codecov** - Coverage tracking and reporting
- **pre-commit** - Pre-commit hook management

### Test Utilities
- **pytest-mock** - Mocking and patching
- **pytest-benchmark** - Performance regression detection (already in use)
- **pytest-xdist** - Parallel test execution
- **pytest-rerunfailures** - Retry flaky tests

### Monitoring
- **pytest-json-report** - JSON test results
- **allure-pytest** - Rich test reporting
- **pytest-html** - HTML test reports

---

## 12. Documentation & Training

### Test Documentation Standards
Every test must include:
1. **Docstring** with version number and feature description
2. **Commit hash** reference (if regression test)
3. **Clear assertion messages** for failures
4. **Fixture documentation** for test data

Example:
```python
def test_betfair_scraper_accuracy():
    """Regression: v97.0.0 - Betfair scraper 99.2% accuracy

    Commit: 5523ffc5e - Betfair detection improvements
    Feature: 35 Betfair-specific optimizations
    Target: 99.2% accuracy, 40-80ms latency

    This test ensures the Betfair scraper maintains its accuracy
    improvements from v97.0.0. Any regression below 99.2% accuracy
    should be investigated immediately.
    """
    # Test implementation
```

### Developer Training
- **Testing Best Practices** guide
- **TDD Workflow** documentation
- **Regression Test Writing** tutorial
- **CI/CD Pipeline** usage guide

---

## 13. Appendix: Module Coverage Reference

### Modules WITH Tests (75 modules - 31%)
See `tests/` directory for existing test coverage:
- Core poker engine: 95% coverage (test_core_comprehensive.py)
- ML + GTO stack: 95% coverage (test_comprehensive_ml_gto.py)
- System integration: 95% coverage (test_comprehensive_system.py)
- Detection system: 99.2% accuracy validation

### Modules WITHOUT Tests (167 modules - 69%)
See Section 3 for complete list organized by priority:
- CRITICAL: 6 modules (api, database, scrape, gui, smarthelper_engine, cli)
- HIGH: 38 modules (detection/scraping pipeline)
- MEDIUM: 22 modules (game logic/strategy)
- LOWER: 40+ modules (infrastructure/utilities)

---

## Contact & Support

**Questions?** Contact the development team:
- Regression testing issues: File GitHub issue with `testing` label
- CI/CD pipeline issues: File GitHub issue with `ci/cd` label
- Test coverage questions: See DEVELOPMENT_WORKFLOW.md

**Resources:**
- Test execution: `python tests/test_everything.py --help`
- Coverage reports: `logs/coverage_html/index.html`
- Test logs: `test_logs/`

---

**Document Status:** Active
**Next Review:** 2025-11-23 (1 month)
**Owner:** Development Team
