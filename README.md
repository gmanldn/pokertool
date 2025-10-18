# PokerTool

PokerTool is a web-based poker assistant that pairs a React dashboard with a Python strategy engine so players can make profitable decisions with real-time guidance. The backend fuses computer vision, game theory, machine learning, and compliance tooling to keep advice actionable while staying resilient in live play.

### Engine Systems That Drive Decisions
- **Vision & Table Intelligence** – The Betfair-optimised scraper (`src/pokertool/modules/poker_screen_scraper_betfair.py`) layers 35 speed, accuracy, and reliability upgrades (ROI tracking, temporal consensus, watchdog recovery) documented in `tests/architecture/data/architecture.json`, letting the engine read live tables with 95%+ extraction accuracy.
- **Probability & Solver Stack** – GTO solvers, Nash equilibrium search (`src/pokertool/nash_solver.py`), and the ICM calculator (`tests/system/test_icm_calculator.py`) collaborate to price every spot, run deviation analysis, and surface bankroll-safe lines within milliseconds.
- **Opponent Modeling & Active Learning** – `src/pokertool/ml_opponent_modeling.py` and `src/pokertool/active_learning.py` learn villain tendencies, update ranges, and feed the advice loop with personalised exploit suggestions.
- **Coaching, Reporting & Session Ops** – The analytics dashboard, advanced reporting suite, session tracker, and study-mode helpers (`src/pokertool/analytics_dashboard.py`, `src/pokertool/advanced_reporting.py`, `src/pokertool/session_management.py`) explain “why” behind every recommendation and archive hands for review.
- **Resilience & Observability** – Compliance and security layers (`src/pokertool/compliance.py`, `src/pokertool/error_handling.py`, `src/pokertool/storage.py`), health monitors, and the consolidated logging system ensure the stack survives long sessions and is auditable after the fact.

### Test & Coverage Snapshot
- **1,199 automated tests** across 69+ files, driven by `test_everything.py` (see `docs/TESTING.md`).
- **Core poker engine:** 95%+ code coverage validated by `tests/test_core_comprehensive.py`.
- **ML + GTO stack:** 95% coverage across solvers, opponent models, and OCR pipelines (`tests/test_comprehensive_ml_gto.py`).
- **End-to-end integration:** Integrated subsystems are exercised to 95% coverage by `tests/test_comprehensive_system.py`, ensuring schedulers, compliance, OCR, and advice pipelines cooperate under load.

## Features

- Real-time hand analysis with opponent modeling and coaching prompts.
- Modern web interface with multi-table support and live WebSocket updates.
- Automated dependency validation and environment bootstrap scripts.
- Screen-scraping utilities for Betfair-optimized capture pipelines.
- Comprehensive logging, diagnostics, and architecture graph tooling.

## Prerequisites

- Python 3.8 – 3.13 (3.13 supported with limited features).
- macOS 10.15+, Ubuntu 18.04+, or Windows 10/11.
- Recommended system packages: Tesseract OCR and tkinter (`brew install python-tk tesseract`, `apt install python3-tk tesseract-ocr`).

## Installation

```bash
git clone https://github.com/gmanldn/pokertool.git
cd pokertool
python scripts/start.py --all
```

The installer validates dependencies, provisions the virtual environment, and prepares the web UI assets. Use `python scripts/start.py --help` for advanced options.

## Quick Start

```bash
# Launch the web interface
python -m pokertool web

# Run the comprehensive test suite with architecture validation
python test.py

# Execute headless screen scraping (optional)
python -m pokertool scrape
```

Additional commands:

- `python scripts/start.py --self-test` — full system validation.
- `python src/pokertool/dependency_manager.py` — dependency health check.
- `pytest tests/ -v` — direct pytest access.

## Logging

Centralized logs live in `logs/` and rotate automatically:

- `logs/errors-and-warnings.log` — consolidated errors + warnings; regenerate with `./scripts/monitor-errors.sh`.
- `logs/pokertool_master.log` — primary backend activity stream (INFO/DEBUG/ERROR).
- `logs/pokertool_errors.log` — structured JSON traces with execution context.
- `logs/pokertool_performance.log` — latency and resource metrics.
- `logs/pokertool_security.log` — authentication and security events.
- `logs/app-run.log` / `startup.log` — latest runtime bootstrap output.

Use `./scripts/error-summary.sh` for grouped issue reports and `tail -f logs/errors-and-warnings.log` for real-time monitoring. Additional retention policies and troubleshooting tips live in `logs/README.md`.

## Testing Process

- `python test.py` — full pipeline: architecture graph refresh, architecture validation suite, then unit/integration tests.
- `python test.py --quick` — skips slow markers for rapid feedback.
- `python test.py --no-graph` — reuses existing architecture graph data.
- `python test.py --coverage` — generates HTML + terminal coverage reports.
- `pytest tests/ -k <pattern>` — targeted debugging; architecture graph lives in `tests/architecture/data/`.

Failures in scraper-related tests often mean no live Betfair table is available; rerun with `pytest -m "not scraper"` if you need to bypass them locally.

## Documentation

- `FEATURES.md` — detailed feature grid.
- `docs/` — architecture, deployment, and integration guides.
- `GRAPHDATA.md` — architecture graph schema and tooling.
- `logs/README.md` — centralized logging playbook.

Release notes live in `CHANGELOG.md`, and `VERSION` tracks the current build tag.

## Contributing

Contributions are welcome. Review `CONTRIBUTING.md`, follow the coding standards, and run `python test.py` before opening a pull request. Issues and feature requests can be filed through the GitHub issue tracker.

## License

PokerTool is released under the Apache License 2.0. See `LICENSE` for details.
