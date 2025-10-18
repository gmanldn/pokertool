# Changelog

All notable changes to this project are tracked in this file. The structure follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and the project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [89.0.1] - 2025-10-18

### Added
- Displayed the synced release version chip alongside the PokerTool navigation title and drawer branding (`pokertool-frontend/src/components/Navigation.tsx`).
- Auto-generated TODO log alerts now include LLM-friendly prompts so AI agents can immediately investigate warnings and errors (`src/pokertool/master_logging.py`, `docs/TODO.md`).

## [89.0.0] - 2025-10-18

### Added
- Real-time pytest progress streaming with color-coded PASS/FAIL status lines and live counters for completed versus remaining tests (`tests/conftest.py`).

## [88.4.0] - 2025-10-19

### Added
- Expanded the README introduction to document the full decision stack—vision, solver, ML, coaching, and resilience systems—and highlighted current automated test coverage.

### Changed
- Refreshed the architecture knowledge base (`tests/architecture/data/architecture.json`) with the latest module metadata.
- Updated sample range presets to match the new solver baselines (`ranges/import_test.json`, `ranges/my_range.json`).

## [88.3.0] - 2025-10-19

### Added
- Published a dedicated `INSTALL.md` covering automated and manual setup paths across macOS, Linux, and Windows.

### Changed
- Extended `.gitignore` so evaluation workspaces (`evals/diff-edits/**`) never pollute future commits.

## [88.2.0] - 2025-10-18

### Changed
- Hardened optional SciPy, scikit-learn, and TensorFlow imports so optional ML features degrade gracefully instead of aborting.
- Rebuilt the card-recognition engine with defensive OpenCV handling and clearer error recovery paths.
- Toughened the bootstrap workflow in `scripts/start.py` to survive sandboxed dependency install failures.

### Added
- Introduced a floating advice facade so automated and headless workflows can surface coaching prompts without the full UI.

### Fixed
- Added a pytesseract ndarray compatibility shim used during tests to prevent type errors when OpenCV frames are passed through OCR helpers.

### Tests
- Converted the scraper logging check into a pytest-aware smoke test and tightened headless-mode filters so Betfair diagnostics no longer stall CI.

## [88.1.0] - 2025-10-17

### Added
- Delivered a feature-flag framework with dependency resolution, JSON export, and 34 comprehensive unit tests enabling staged rollouts.
- Built Phase 1 of the Betfair scraping accuracy engine, covering OCR, currency parsing, seat mapping, and dealer-button detection.
- Shipped a clickable macOS dock status window so desktop users can monitor backend state at a glance.

### Documentation
- Published a full environment variable reference, including required values, safe defaults, and security guidance.
- Documented the Betfair accuracy backlog to map implemented tasks and remaining work.
- Expanded troubleshooting documentation with setup, scraping, GUI, database, and performance playbooks.

## [88.0.0] - 2025-10-17

### Added
- Introduced process-cleanup utilities that clear stale backend/frontend instances and automatically manage macOS dock visibility.

### Changed
- Centralized all logging through `master_logging.py`, added consolidated monitoring scripts, and retired legacy log directories.
- Bundled the new error-monitoring helpers (`check-errors`, `error-summary.sh`, `monitor-errors.sh`) with the standard tooling.

### Fixed
- Resolved outstanding frontend ESLint warnings, removed unused React imports, and added an automated fixer script to keep the dashboard lint-clean.

### Documentation
- Captured permanent project instructions covering startup requirements, logging locations, and common troubleshooting steps.
