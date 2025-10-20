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
python start.py

# Or use the module interface
python -m pokertool web

# Run the comprehensive test suite with architecture validation
python test.py

# Execute headless screen scraping (optional)
python -m pokertool scrape
```

### Restarting After Updates

After pulling updates or making configuration changes, use the restart script for a clean reboot:

```bash
# Restart web application (kills old processes and starts fresh)
python restart.py

# Restart with GUI mode
python restart.py --gui

# Just stop all processes without restarting
python restart.py --kill-only
```

The restart script:
- Gracefully stops all pokertool processes (backend API, frontend, GUI)
- Cleans up stuck processes and releases ports
- Relaunches the application with updated code/config

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

## Error Analysis & Fix Workflow

PokerTool includes an AI-optimized **Trouble Feed** system designed for systematic error analysis and staged fixing. The workflow enables you to instruct an AI assistant to "read README.md, analyze errors, then fix them in stages."

### Trouble Feed System

The **Trouble Feed** (`logs/trouble_feed.txt`) is a centralized, AI-readable error aggregation file that captures all errors and warnings from across the application with maximum detail for intelligent debugging.

**Location:** `/logs/trouble_feed.txt`

**Features:**
- **Multi-Source Aggregation**: Automatically captures errors from Backend, Frontend, WebSocket, Scraper, Database, API, Build, and System sources
- **Comprehensive Context**: Each error includes full stack traces, execution context, system state, and AI suggestion hints
- **Human & AI Readable**: Formatted with clear sections, timestamps, and structured data for both human review and AI analysis
- **Automatic Rotation**: Self-rotates at 50MB with timestamped archival to prevent unbounded growth
- **Real-Time Updates**: Errors are written immediately as they occur across all application layers
- **Deduplication**: Prevents duplicate error entries from flooding the feed

**Entry Format:**
```
====================================================================================================
[2025-10-21T14:23:45.123456+00:00] ERROR from Backend
----------------------------------------------------------------------------------------------------
Location: pokertool.scraper::detect_cards:142
Error: ValueError - Invalid card format 'Xx'

Description:
Card detection failed during OCR processing

Stack Trace:
[Full Python/JavaScript stack trace with file paths and line numbers]

Context:
- table_id: table_3
- ocr_text: Xx 10h
- confidence: 0.72
- attempt: 2/3

System State:
- memory_usage: 245.3 MB
- active_tables: 2
- websocket_connections: 1

AI Suggestion Hint:
Check OCR confidence thresholds and card validation regex patterns
====================================================================================================
```

### Staged Error Fixing Workflow

#### Stage 1: Read and Analyze Errors

**Command for AI Assistant:**
```
Read the trouble feed at /logs/trouble_feed.txt and analyze all errors.
Categorize them by severity, source, and frequency. Provide a summary.
```

**What This Does:**
- AI reads the entire trouble feed file
- Identifies patterns across errors (e.g., multiple errors from the same module)
- Groups errors by severity (WARNING, ERROR, CRITICAL)
- Highlights the most frequent or critical issues
- Suggests priority order for fixes

**Example AI Analysis Output:**
```
CRITICAL ERRORS (3):
  1. Database connection timeout in session_management.py:245 (occurred 3x)
  2. WebSocket disconnection in websocket_manager.py:89 (occurred 2x)

ERRORS (5):
  1. OCR confidence below threshold in poker_screen_scraper_betfair.py:312 (occurred 5x)
  2. Frontend TypeError in Dashboard.tsx:156 (occurred 1x)

WARNINGS (12):
  1. Slow API response time >500ms (occurred 12x)

Recommended fix order: Database connection → WebSocket → OCR threshold
```

#### Stage 2: Prioritize and Plan Fixes

**Command for AI Assistant:**
```
Based on the error analysis, create a prioritized fix plan with stages.
Start with critical issues that affect core functionality.
```

**What This Does:**
- AI creates a todo list with fix tasks in priority order
- Each task includes the error location, root cause hypothesis, and proposed fix
- Tasks are grouped into stages (e.g., "Stage 1: Database fixes", "Stage 2: WebSocket fixes")

#### Stage 3: Execute Fixes in Stages

**Command for AI Assistant:**
```
Fix the errors in Stage 1 from the plan. Read the relevant source files,
apply the fixes, and test them. Report results before moving to Stage 2.
```

**What This Does:**
- AI reads the source files mentioned in the errors
- Applies fixes based on the stack traces and context from the trouble feed
- Runs relevant tests to verify fixes
- Reports which errors are resolved
- Waits for approval before proceeding to next stage

**Example Staged Execution:**
```
Stage 1: Fix database connection timeout
  → Read src/pokertool/session_management.py:245
  → Identify connection pool exhaustion
  → Increase pool size and add connection retry logic
  → Test with pytest tests/test_session_management.py
  → Verify error no longer appears in trouble feed

Stage 2: Fix WebSocket disconnections
  → Read src/pokertool/websocket_manager.py:89
  → Add heartbeat mechanism and auto-reconnect
  → Test with WebSocket stress test
  → Monitor trouble feed for WebSocket errors
```

#### Stage 4: Verify Fixes

**Command for AI Assistant:**
```
Monitor the trouble feed for 5 minutes and confirm that the fixed errors
are no longer occurring. Report any new or remaining errors.
```

**What This Does:**
- AI monitors the trouble feed file for new entries
- Confirms that previously fixed errors are no longer appearing
- Identifies any new errors introduced by the fixes (regressions)
- Provides a final summary of the error state

### Accessing the Trouble Feed

**View recent errors:**
```bash
tail -f logs/trouble_feed.txt
```

**View all errors:**
```bash
cat logs/trouble_feed.txt
```

**Search for specific error types:**
```bash
grep "ValueError" logs/trouble_feed.txt
grep "Frontend" logs/trouble_feed.txt
grep "CRITICAL" logs/trouble_feed.txt
```

**View archived trouble feeds:**
```bash
ls -lh logs/trouble_feed_*.txt.archive
```

### Trouble Feed Integration

The trouble feed automatically captures:

1. **Backend Errors**: All Python exceptions from the FastAPI backend, scrapers, ML models, and utilities
2. **Frontend Errors**: JavaScript errors via global error handlers and unhandled promise rejections
3. **API Errors**: Failed API requests logged via POST `/api/errors/frontend` endpoint
4. **Build Errors**: Compilation and bundling failures from the frontend build process
5. **WebSocket Errors**: Connection failures, message parsing errors, and timeout issues
6. **Database Errors**: Query failures, connection issues, and data validation errors
7. **System Errors**: OS-level issues, resource exhaustion, and process crashes

### Advanced Usage

**Programmatic Error Logging (Python):**
```python
from pokertool.trouble_feed import log_backend_error, TroubleSeverity

try:
    risky_operation()
except Exception as e:
    log_backend_error(
        error=e,
        module=__name__,
        function="risky_operation",
        line_number=42,
        description="Operation failed during critical section",
        context={"user_id": 123, "attempt": 3},
        severity=TroubleSeverity.ERROR
    )
```

**Programmatic Error Logging (TypeScript):**
```typescript
import { captureError } from './services/troubleFeed';

try {
  riskyOperation();
} catch (error) {
  captureError(error as Error, {
    component: 'Dashboard',
    action: 'loadData',
    userId: 123
  });
}
```

### Best Practices

1. **Regular Monitoring**: Check the trouble feed daily or after deployments
2. **Staged Fixing**: Fix errors in priority order (CRITICAL → ERROR → WARNING)
3. **Context Preservation**: The trouble feed includes full context—use it to understand the error's environment
4. **Root Cause Analysis**: Look for patterns across multiple errors to identify systemic issues
5. **Verification**: Always verify fixes by monitoring the trouble feed after deployment
6. **Archive Review**: Periodically review archived trouble feeds to identify long-term trends

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
