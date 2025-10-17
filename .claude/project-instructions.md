# PokerTool Project Instructions

This file contains permanent project memory and critical conventions for working with the PokerTool codebase.

## CRITICAL: Application Startup

**THE APP MUST ALWAYS BE STARTED FROM THE PROJECT ROOT USING `start.py`**

```bash
# CORRECT - From project root
python3 start.py

# WRONG - Do not use these methods
cd scripts && python start.py
python scripts/start.py
```

### Why This Matters:
- `start.py` sets up the correct PYTHONPATH
- Ensures all imports resolve correctly
- Initializes logging and configuration properly
- Prevents import errors and path resolution issues

## Error Checking and Monitoring

### Centralized Error Log
The project uses a unified error monitoring system. All errors and warnings are consolidated in:

```
logs/errors-and-warnings.log
```

### Quick Error Check Command
```bash
./scripts/check-errors
```

This script:
1. Scans all log files (backend, frontend, runtime)
2. Consolidates errors and warnings
3. Groups them by frequency
4. Shows critical issues first

### Primary Log Files to Monitor

**Backend (Python/API):**
- `logs/pokertool_master.log` - Main backend log
- `logs/pokertool_errors.log` - Error-only log
- `logs/pokertool_performance.log` - Performance metrics
- `logs/pokertool_security.log` - Security events

**Frontend (React/TypeScript):**
- `pokertool-frontend/build/` - Production build output
- TypeScript compilation: `cd pokertool-frontend && npx tsc --noEmit`
- Build: `cd pokertool-frontend && npm run build`

**Runtime:**
- `logs/app-run.log` - Application runtime log
- `logs/errors-and-warnings.log` - **Consolidated error log (check this first!)**

### Error Monitoring Scripts

```bash
# Quick error summary
./scripts/error-summary.sh

# Live error monitoring
./scripts/monitor-errors.sh

# Complete error check (scan + analyze + summarize)
./scripts/check-errors
```

## Project Structure

```
pokertool/
├── start.py                    # MAIN ENTRY POINT - Always use this!
├── src/pokertool/              # Python source code
├── pokertool-frontend/         # React TypeScript frontend
├── tests/                      # Pytest test suite
├── scripts/                    # Utility scripts
└── logs/                       # ALL logs go here (centralized)
```

## Testing

### Run Tests
```bash
# Backend tests (from root)
PYTHONPATH=src python3 -m pytest tests/ -v

# Frontend build check
cd pokertool-frontend && npm run build

# Frontend TypeScript check
cd pokertool-frontend && npx tsc --noEmit
```

### Test File Conventions
- All test files MUST be proper pytest files (no standalone scripts)
- Use `test_*.py` naming convention
- Never use `sys.exit()` in test files
- Mark tests that require external dependencies with `@pytest.mark.xfail` or `@pytest.skip`

## Logging System

**ALL logging uses the centralized master_logging.py system**

- No legacy log files allowed
- All logs write to `logs/` directory
- Use `master_logging.py` for all logging configuration
- Never create standalone log files

### Accessing Logs
```python
from pokertool.master_logging import get_logger

logger = get_logger(__name__)
logger.info("Your message here")
```

## Version Management

Version bumps follow semantic versioning:
- Format: `MAJOR.MINOR.PATCH`
- Current version is tracked in git commit messages
- Version bump commits use format: `chore: Bump version from X.Y.Z to A.B.C`

## Git Workflow

1. Work on `develop` branch
2. Run full test cycle before committing
3. Version bump commits are separate from feature commits
4. Always push to `develop` branch

```bash
# Standard workflow
git status
git add -A
git commit -m "fix: Description of changes"
git push origin develop
```

## Common Errors and Solutions

### Import Errors
- **Solution**: Always run from project root using `start.py`
- Verify PYTHONPATH is set to `src/`

### Frontend Build Failures
- Check `pokertool-frontend/src/` for TypeScript errors
- Run `npx tsc --noEmit` to see compilation errors
- Check `logs/errors-and-warnings.log` for details

### Test Collection Errors
- Remove any test files with `sys.exit()` calls
- Ensure all test files are proper pytest format
- Check for duplicate test files (e.g., `*2.py` files)

### Dependency Errors
- Common: tesseract, pandas C extensions, OpenCV
- These are environment issues, not code issues
- Mark affected tests with `@pytest.mark.xfail`

## Important Files

### Configuration
- `.gitignore` - Git exclusions
- `pytest.ini` - Pytest configuration
- `pyproject.toml` - Python project metadata
- `pokertool-frontend/tsconfig.json` - TypeScript config
- `pokertool-frontend/package.json` - NPM dependencies

### Documentation
- `logs/README.md` - Logging system documentation
- This file (`.claude/project-instructions.md`) - Project memory

## Quick Reference Commands

```bash
# Start application
python3 start.py

# Check for errors
./scripts/check-errors

# Run tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Build frontend
cd pokertool-frontend && npm run build

# Monitor logs live
tail -f logs/errors-and-warnings.log
```

## Remember
- **ALWAYS** start from root with `start.py`
- **ALWAYS** check `logs/errors-and-warnings.log` first for errors
- **NEVER** create legacy log files outside `logs/` directory
- **NEVER** use standalone test scripts (must be pytest format)
