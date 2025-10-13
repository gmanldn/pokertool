# PokerTool Test Suite

## Test Folder Structure

### `tests/` - Official Test Suite
All tests that run as part of the automated test cycle are located in this folder. This is the **only** folder that should contain production test files.

**Subfolders:**
- `tests/gui/` - GUI and interface tests
- `tests/system/` - System integration and core functionality tests
- Additional test modules organized by feature

**Running Tests:**
```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/gui/test_suit_enum.py

# Run with verbose output
python3 -m pytest tests/ -v
```

### `forwardscripts/` - Roll-Forward Scripts
This folder contains **roll-forward scripts** and migration utilities, NOT production tests.

These scripts are used for:
- One-time migrations
- Database schema updates
- Development experiments
- Prototype testing

**Important:** Do NOT add test files to `forwardscripts/` that should be part of the regular test cycle. All production tests belong in `tests/`.

## Test Organization Guidelines

1. **Production tests** → `tests/` folder
2. **Roll-forward/migration scripts** → `forwardscripts/` folder
3. **Temporary test scripts** → Local only, do not commit

## Test Mode - No GUI Popups

When running tests, **GUI popup dialogs are automatically suppressed**. Instead, all errors, warnings, and info messages are logged to the console and log files.

**How it works:**
- Tests set `POKERTOOL_TEST_MODE=1` environment variable
- All messagebox dialogs check this variable and log instead of showing popups
- Prevents tests from hanging on dialog boxes

**Manual testing with suppressed popups:**
```bash
export POKERTOOL_TEST_MODE=1
python -m pytest tests/
```

## CI/CD Integration

The continuous integration pipeline runs:
```bash
pytest tests/ --tb=short -v
```

Only tests in the `tests/` folder are included in the automated test runs.
