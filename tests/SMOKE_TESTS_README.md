# PokerTool Smoke Test Suite

## Overview

The PokerTool smoke test suite provides fast, comprehensive validation of the entire application. These tests are designed to quickly verify that all critical components are functioning correctly before deployment or after significant changes.

## What are Smoke Tests?

Smoke tests are a subset of tests that:
- **Run quickly** (target: <2 minutes for full suite)
- **Are non-destructive** (don't modify production data)
- **Test critical paths** (ensure core functionality works)
- **Validate integration** (verify components work together)
- **Provide confidence** (give quick feedback on system health)

## Test Coverage

The smoke test suite validates:

### 1. System Health
- ✅ Python version compatibility (3.10-3.13)
- ✅ Project structure and critical files
- ✅ Virtual environment setup
- ✅ Dependencies installation

### 2. Backend API
- ✅ API module imports and initialization
- ✅ FastAPI app creation
- ✅ Health endpoint
- ✅ Authentication endpoints
- ✅ System health monitoring
- ✅ ML feature endpoints

### 3. Frontend
- ✅ Directory structure
- ✅ Package.json validity
- ✅ Critical component files
- ✅ React app structure

### 4. Database
- ✅ Database module imports
- ✅ Database creation
- ✅ Basic operations (queries, inserts)

### 5. Screen Scraper
- ✅ Scraper module imports
- ✅ Scraper initialization
- ✅ OCR dependencies

### 6. ML Features
- ✅ ML module imports
- ✅ GTO solver availability
- ✅ NumPy operations
- ✅ ML data structures

### 7. WebSocket
- ✅ WebSocket manager imports
- ✅ Connection manager creation
- ✅ Detection WebSocket manager

### 8. Authentication
- ✅ Auth service imports and creation
- ✅ Token generation
- ✅ Token verification
- ✅ User management

### 9. End-to-End Workflow
- ✅ Full import chain
- ✅ Services initialization
- ✅ API with services integration

### 10. Error Handling
- ✅ API error responses
- ✅ Database error handling
- ✅ Graceful degradation

## Running Smoke Tests

### Option 1: Using pytest directly
```bash
# Run all smoke tests
pytest tests/test_smoke_suite.py -v -m smoke

# Run with coverage
pytest tests/test_smoke_suite.py --cov=src/pokertool -m smoke

# Run specific test class
pytest tests/test_smoke_suite.py::TestBackendAPI -v
```

### Option 2: Using the standalone runner
```bash
# Run all smoke tests (will start services if needed)
python scripts/run_smoke_tests.py

# Run with verbose output
python scripts/run_smoke_tests.py --verbose

# Don't start services (assume already running)
python scripts/run_smoke_tests.py --no-start

# Generate HTML report
python scripts/run_smoke_tests.py --report
```

### Option 3: Using the comprehensive test runner
```bash
# Run only smoke tests
python tests/test_everything.py --smoke

# Run smoke tests with verbose output
python tests/test_everything.py --smoke --verbose
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Smoke Tests

on: [push, pull_request]

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run smoke tests
        run: python scripts/run_smoke_tests.py
```

### Exit Codes
- `0` - All smoke tests passed
- `1` - Some smoke tests failed
- `2` - Error starting services
- `3` - Test execution error
- `130` - Interrupted by user

## Best Practices

### When to Run Smoke Tests

1. **Before every commit** - Ensure your changes don't break core functionality
2. **After pulling changes** - Verify the codebase still works
3. **Before deployment** - Final validation before releasing
4. **After dependency updates** - Check for breaking changes
5. **During development** - Quick feedback loop

### Adding New Smoke Tests

When adding new critical features, update the smoke test suite:

1. Add a new test class in `tests/test_smoke_suite.py`
2. Follow the existing pattern (fast, focused, non-destructive)
3. Mark tests with `@pytest.mark.smoke`
4. Update this README with new coverage
5. Keep tests under 2 minutes total

Example:
```python
class TestNewFeature:
    """Smoke tests for new feature."""

    @pytest.mark.smoke
    def test_feature_imports(self):
        """Test that new feature can be imported."""
        try:
            from pokertool.modules import new_feature
        except ImportError as e:
            pytest.fail(f"Cannot import new feature: {e}")

    @pytest.mark.smoke
    def test_feature_initialization(self):
        """Test that new feature can be initialized."""
        from pokertool.modules.new_feature import NewFeature

        feature = NewFeature()
        assert feature is not None
```

### Troubleshooting

#### Tests fail with "Port already in use"
- Stop any running PokerTool instances
- Check for stuck processes: `ps aux | grep pokertool`
- Kill stuck processes: `pkill -f pokertool`

#### Tests fail with "Module not found"
- Ensure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`
- Check PYTHONPATH: Should include `src/` directory

#### Tests fail with "Backend not responding"
- Increase timeout in `SmokeTestConfig`
- Check backend logs in `test_logs/`
- Verify port 5001 is not blocked by firewall

#### Tests are too slow
- Reduce timeout values in test fixtures
- Skip optional tests with `pytest -k "not slow"`
- Use `--quick` mode for faster subset

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Total runtime | <2 minutes | ~90 seconds |
| Setup time | <10 seconds | ~5 seconds |
| Test count | 40-60 tests | 55 tests |
| Coverage | >80% critical paths | ~85% |

## Maintenance

### Monthly Tasks
- [ ] Review and update test coverage
- [ ] Check for deprecated tests
- [ ] Update dependencies
- [ ] Verify CI/CD integration

### After Major Changes
- [ ] Add new smoke tests for new features
- [ ] Update existing tests if APIs changed
- [ ] Verify all tests still pass
- [ ] Update documentation

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Smoke Testing Best Practices](https://martinfowler.com/bliki/SmokeTest.html)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

## Support

For issues or questions about the smoke test suite:
1. Check this README
2. Review test logs in `test_logs/`
3. Open an issue on GitHub
4. Contact the development team

---

**Last Updated:** 2025-10-16
**Maintainer:** PokerTool Development Team
**Version:** 1.0.0
