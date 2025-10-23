# PokerTool

PokerTool is a web-based poker assistant that pairs a React dashboard with a Python strategy engine so players can make profitable decisions with real-time guidance. The backend fuses computer vision, game theory, machine learning, and compliance tooling to keep advice actionable while staying resilient in live play.

### Engine Systems That Drive Decisions
- **Vision & Table Intelligence** – The Betfair-optimised scraper (`src/pokertool/modules/poker_screen_scraper_betfair.py`) layers 35 speed, accuracy, and reliability upgrades (ROI tracking, temporal consensus, watchdog recovery) documented in `tests/architecture/data/architecture.json`, letting the engine read live tables with 95%+ extraction accuracy.
- **Probability & Solver Stack** – GTO solvers, Nash equilibrium search (`src/pokertool/nash_solver.py`), and the ICM calculator (`tests/system/test_icm_calculator.py`) collaborate to price every spot, run deviation analysis, and surface bankroll-safe lines within milliseconds.
- **Opponent Modeling & Active Learning** – `src/pokertool/ml_opponent_modeling.py` and `src/pokertool/active_learning.py` learn villain tendencies, update ranges, and feed the advice loop with personalised exploit suggestions.
- **Coaching, Reporting & Session Ops** – The analytics dashboard, advanced reporting suite, session tracker, and study-mode helpers (`src/pokertool/analytics_dashboard.py`, `src/pokertool/advanced_reporting.py`, `src/pokertool/session_management.py`) explain “why” behind every recommendation and archive hands for review.
- **Resilience & Observability** – Compliance and security layers (`src/pokertool/compliance.py`, `src/pokertool/error_handling.py`, `src/pokertool/storage.py`), health monitors, real-time startup tracking (`src/pokertool/backend_startup_logger.py`), automatic frontend error detection (`src/pokertool/frontend_error_monitor.py`), and the consolidated logging system ensure the stack survives long sessions, catches errors early, and is fully auditable after the fact.

### Test & Coverage Snapshot
- **1,199 automated tests** across 69+ files, driven by `test_everything.py` (see `docs/TESTING.md`).
- **Core poker engine:** 95%+ code coverage validated by `tests/test_core_comprehensive.py`.
- **ML + GTO stack:** 95% coverage across solvers, opponent models, and OCR pipelines (`tests/test_comprehensive_ml_gto.py`).
- **End-to-end integration:** Integrated subsystems are exercised to 95% coverage by `tests/test_comprehensive_system.py`, ensuring schedulers, compliance, OCR, and advice pipelines cooperate under load.

## Features

- Real-time hand analysis with opponent modeling and coaching prompts.
- Modern web interface with multi-table support and live WebSocket updates.
- **Backend Status monitoring tab** with live startup progress tracking and log viewer.
- **Automatic frontend error detection** with graceful shutdown and TODO creation.
- **Webpack chunk loading resilience** with exponential backoff retry mechanism.
- **Advanced Detection System** (99.2% accuracy, 40-80ms latency) with intelligent caching, event batching, board texture analysis, and comprehensive monitoring. See [Detection Docs](docs/detection/README.md).
- Automated dependency validation and environment bootstrap scripts.
- Screen-scraping utilities for Betfair-optimized capture pipelines.
- Comprehensive logging, diagnostics, and architecture graph tooling.
- Thread-safe error monitoring with real-time logging and health endpoints.

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
# Launch the web interface (backend + frontend)
python start.py

# Or use the module interface
python -m pokertool web

# Run the comprehensive test suite with architecture validation
python test.py

# Execute headless screen scraping (optional)
python -m pokertool scrape
```

**After Startup:**
1. Frontend will be available at `http://localhost:3000`
2. Backend API at `http://localhost:5001`
3. Check the **Backend** tab (`http://localhost:3000/backend`) to monitor startup progress
4. Review `logs/backend_startup.log` for detailed timing metrics

**Monitoring Startup:**
- Watch real-time progress in the Backend Status tab
- All 7 startup steps should complete in under 5 seconds
- If frontend compilation errors occur, the app will auto-shutdown with details in `logs/frontend_compile_errors.log`

### Updating the Running Application

PokerTool includes a comprehensive **Update Manager** for safely applying code changes while the app is running. This system handles graceful shutdown, code updates, frontend rebuilds, and automatic restart.

#### Quick Update (Recommended)

```bash
# Complete update cycle: stop -> pull changes -> rebuild -> restart
./scripts/full_update.sh
```

#### Check Application Status

```bash
# View process status, CPU, memory, and health metrics
./scripts/status.sh
```

#### Manual Update Process

```bash
# 1. Check if app is running
./scripts/status.sh

# 2. Gracefully stop the app (saves state, 30s timeout)
./scripts/quiesce.sh

# 3. Pull changes and rebuild frontend
./scripts/update.sh

# 4. Restart the application
./scripts/resume.sh
```

**What the Update Manager Does:**
- ✅ **Graceful Shutdown**: SIGTERM with 30-second timeout, state preservation
- ✅ **Automatic Git Pull**: Fetches latest code changes
- ✅ **Frontend Rebuild**: Runs `npm install` and `npm run build` automatically
- ✅ **Dependency Updates**: Updates Python packages from requirements.txt
- ✅ **Health Verification**: Ensures successful restart with CPU/memory monitoring
- ✅ **Comprehensive Logging**: All operations logged to `logs/update_manager.log`

**State Preservation:**
- Application state saved to `.update_state.json` during shutdown
- PID tracked in `.pokertool.pid` for process management
- Safe recovery from interrupted updates

**For detailed documentation, see:**
- [Update Procedures Guide](docs/UPDATE_PROCEDURES.md) - Complete documentation (400+ lines)
- [Scripts README](scripts/README.md) - Quick reference

#### Legacy Restart Script

For compatibility, the old restart script is still available:

```bash
# Restart web application (kills old processes and starts fresh)
python restart.py

# Restart with GUI mode
python restart.py --gui

# Just stop all processes without restarting
python restart.py --kill-only
```

**Note:** The new `full_update.sh` script is recommended as it provides better state management and logging.

Additional commands:

- `python scripts/start.py --self-test` — full system validation.
- `python src/pokertool/dependency_manager.py` — dependency health check.
- `pytest tests/ -v` — direct pytest access.

## Monitoring & Health Checks

PokerTool includes comprehensive monitoring and error detection systems to ensure reliable operation:

### Backend Status Dashboard

Access real-time startup progress and backend health via the **Backend Status** tab:

```
http://localhost:3000/backend
```

**Features:**
- Live progress tracking through 7 startup steps
- Real-time log viewer with auto-scrolling terminal output
- Step duration and timing metrics
- Visual progress indicators for each initialization phase
- Auto-refresh every 2 seconds

**Startup Steps Monitored:**
1. Clean old processes - Remove previous instances
2. Setup macOS dock icon - Configure application icon
3. Check Node.js - Verify Node.js installation
4. Install frontend dependencies - Check npm packages
5. Start backend API - Launch FastAPI on port 5001
6. Start React frontend - Launch dev server on port 3000
7. Application ready - All services operational

### Frontend Error Monitoring

PokerTool automatically detects and handles frontend compilation errors:

**Automatic Error Detection:**
- Monitors frontend build output in real-time
- Detects blocking errors: compilation failures, module not found, import errors, syntax errors
- Automatically logs all errors to `logs/frontend_compile_errors.log`
- Creates P0 tasks in `docs/TODO.md` with full error context
- Gracefully shuts down application to prevent running with broken frontend

**Error Types Detected:**
- `Failed to compile` - Build failures
- `Module not found` / `Cannot find module` - Missing dependencies
- `Attempted import error` - Import resolution failures
- `SyntaxError` / `TypeError` / `ReferenceError` - Code errors

**Chunk Loading Resilience:**
PokerTool includes automatic retry for webpack chunk loading failures:
- Exponential backoff retry strategy (1s, 2s, 3s delays)
- Maximum 3 automatic retries per chunk
- Handles both synchronous and promise-based chunk errors
- Prevents user-facing errors from transient network/caching issues

### Health Endpoints

**Backend Health Check:**
```bash
curl http://localhost:5001/health
```

**Backend Startup Status API:**
```bash
curl http://localhost:5001/api/backend/startup/status
curl http://localhost:5001/api/backend/startup/log?lines=100
```

## Logging

Centralized logs live in `logs/` and rotate automatically:

- `logs/errors-and-warnings.log` — consolidated errors + warnings; regenerate with `./scripts/monitor-errors.sh`.
- `logs/pokertool_master.log` — primary backend activity stream (INFO/DEBUG/ERROR).
- `logs/pokertool_errors.log` — structured JSON traces with execution context.
- `logs/pokertool_performance.log` — latency and resource metrics.
- `logs/pokertool_security.log` — authentication and security events.
- `logs/app-run.log` / `startup.log` — latest runtime bootstrap output.
- `logs/backend_startup.log` — detailed startup progress with timing metrics (NEW).
- `logs/frontend_compile_errors.log` — frontend compilation errors with full context (NEW).

Use `./scripts/error-summary.sh` for grouped issue reports and `tail -f logs/errors-and-warnings.log` for real-time monitoring. Additional retention policies and troubleshooting tips live in `logs/README.md`.

**Real-Time Monitoring:**
```bash
# Watch backend startup progress
tail -f logs/backend_startup.log

# Monitor frontend compilation errors
tail -f logs/frontend_compile_errors.log

# Watch all errors and warnings
tail -f logs/errors-and-warnings.log

# Monitor application runtime
tail -f logs/app-run.log
```

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

## Best Practices

### Error Handling & Monitoring

**1. Monitor Application Health Regularly**
- Check the Backend Status tab (`http://localhost:3000/backend`) after startup
- Review startup logs to ensure all 7 initialization steps completed successfully
- Monitor health endpoints (`/health`, `/api/backend/startup/status`) for production deployments

**2. Frontend Compilation Best Practices**
- If frontend compilation errors occur, the application will auto-shutdown and log details
- Check `logs/frontend_compile_errors.log` for full error context and stack traces
- Review `docs/TODO.md` for auto-created P0 tasks with fix instructions
- Never ignore compilation warnings—they often indicate future breaking changes

**3. Chunk Loading Resilience**
- The application automatically retries failed chunk loads up to 3 times
- If chunk errors persist after 3 retries, check network connectivity and clear browser cache
- Review webpack build configuration if chunk loading errors are frequent
- Monitor browser console for chunk loading patterns during testing

**4. Log Monitoring Strategy**
```bash
# Daily health check routine
tail -100 logs/backend_startup.log        # Verify clean startup
tail -100 logs/frontend_compile_errors.log # Check for build issues
tail -100 logs/pokertool_errors.log       # Review runtime errors
grep "ERROR" logs/pokertool_master.log    # Scan for error patterns
```

**5. Error Response Workflow**
1. **Detection** - Application detects error and logs to appropriate log file
2. **Logging** - Full context written to `logs/` with timestamp and stack trace
3. **TODO Creation** - Critical errors automatically create P0 tasks in `docs/TODO.md`
4. **Notification** - Terminal output shows error summary and log file location
5. **Resolution** - Fix error using context from logs and TODO tasks
6. **Verification** - Restart application and monitor logs to confirm fix

**6. Thread-Safe Error Handling**
- All error monitoring systems use thread locks for safe concurrent access
- Error detection and logging operations are non-blocking
- Multiple threads can report errors simultaneously without data corruption

**7. Production Deployment Checklist**
- [ ] Verify all startup steps complete in under 5 seconds
- [ ] Test health endpoints respond with 200 status
- [ ] Confirm frontend builds without warnings or errors
- [ ] Review recent logs for any ERROR or WARNING entries
- [ ] Test chunk loading with slow network conditions
- [ ] Verify TODO.md has no outstanding P0 tasks
- [ ] Check all log rotation policies are configured

**8. Error Prevention**
- Run `python test.py` before committing code changes
- Use `python test.py --coverage` to ensure test coverage above 95%
- Monitor `logs/trouble_feed.txt` for patterns indicating systemic issues
- Review frontend build output during development
- Test with frontend hot module replacement (HMR) to catch build issues early

### Development Best Practices

**Frontend Development:**
- Use the Backend Status tab to verify backend is fully initialized before testing
- Monitor browser console for chunk loading warnings
- Clear webpack cache (`rm -rf node_modules/.cache`) if build issues persist
- Test error boundaries and fallback UIs for graceful degradation

**Backend Development:**
- Use `logs/backend_startup.log` to optimize startup performance
- Add startup steps to BackendStartupLogger for new initialization phases
- Implement proper error handling with context logging
- Use thread-safe patterns for concurrent operations

**Integration Testing:**
- Test with frontend error monitoring active
- Verify error auto-shutdown behavior with intentional compile errors
- Test chunk loading retry mechanism with network throttling
- Validate log file creation and rotation under load

## Database

PokerTool supports multiple database backends with a flexible, backward-compatible interface.

### Database Options

#### 1. **PokerDatabase** (Legacy/Simple)

Backward compatibility wrapper for legacy code. Provides simple SQLite operations.

```python
from pokertool.database import PokerDatabase

# Simple usage
db = PokerDatabase('poker_decisions.db')
db.save_hand_analysis("AsKh", "Qh9c2d", "Fold")
hands = db.get_recent_hands(50)
print(f"Total hands: {db.get_total_hands()}")
db.close()

# Context manager usage
with PokerDatabase('poker_decisions.db') as db:
    db.save_hand_analysis("AsKh", "Qh9c2d", "Fold")
```

**Features:**
- ✅ Simple SQLite interface
- ✅ Backward compatible with legacy code
- ✅ Automatic data validation
- ✅ Context manager support

#### 2. **SecureDatabase** (Recommended)

Advanced database with encryption and security features.

```python
from pokertool.storage import SecureDatabase

db = SecureDatabase('poker_decisions.db')
db.save_hand_analysis("AsKh", "Qh9c2d", "Fold",
                     confidence_score=0.95,
                     bet_size_ratio=0.75,
                     pot_size=100.0,
                     player_position="BTN")
```

**Features:**
- ✅ Data encryption at rest
- ✅ Security validation
- ✅ Extended hand analysis fields
- ✅ Better error handling

#### 3. **ProductionDatabase** (Enterprise)

Production-ready database with PostgreSQL support and connection pooling.

```python
from pokertool.database import get_production_db

# Automatically uses PostgreSQL in production, SQLite in dev
db = get_production_db()
```

**Features:**
- ✅ PostgreSQL support
- ✅ Connection pooling
- ✅ Automatic failover
- ✅ Transaction management
- ✅ Query optimization

### Configuration

Set database type via environment variables:

```bash
# Use PostgreSQL (production)
export POKERTOOL_DB_TYPE=postgresql
export POKERTOOL_DB_HOST=localhost
export POKERTOOL_DB_PORT=5432
export POKERTOOL_DB_NAME=pokertool
export POKERTOOL_DB_USER=your_user
export POKERTOOL_DB_PASSWORD=your_password

# Use SQLite (development) - default
export POKERTOOL_DB_TYPE=sqlite
```

### Migration from v88.6.0 to v98.0.0

If you have existing code using the old database interface, it continues to work without changes:

**Your existing code (still works):**
```python
from pokertool.database import PokerDatabase
db = PokerDatabase()
# All your existing code works as-is
```

**Recommended for new code:**
```python
from pokertool.storage import SecureDatabase
db = SecureDatabase('poker_decisions.db')
# Use enhanced features
```

See [MIGRATION_GUIDE_V98.md](docs/MIGRATION_GUIDE_V98.md) for complete migration details.

### Database API Reference

See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for complete database API reference.

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
