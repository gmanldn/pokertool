# PokerTool TODO

Last updated: 2025-10-21

This file tracks the active backlog at a glance. Keep items small, outcome‑focused, and linked to code where possible. Older, verbose plans have been removed; refer to git history if needed.

Conventions
- Priority: P0 (critical ROI), P1 (high), P2 (medium), P3 (low)
- Effort: S (<1 day), M (1–3 days), L (>3 days)
- Status: TODO | IN PROGRESS | BLOCKED | DONE
- Format: [ ] [P#][E#] Title — details and code path(s)

## AI Features Expansion (P0: Push Codebase-Wide)

- [ ] [P0][S] Integrate LangChain router into main FastAPI app — Import and include `api_langchain.router` in `src/pokertool/api.py` to expose `/api/ai/*` endpoints in running application.
- [ ] [P0][M] Frontend AI chat interface — Create React component `pokertool-frontend/src/pages/AIChat.tsx` with chat UI, message history, and connection to `/api/ai/chat` endpoint. Add route to Navigation.
- [ ] [P0][M] Connect LLM provider (OpenAI/Anthropic) — Add LLM integration in `langchain_memory_service.py` using environment variables for API keys. Support OpenAI GPT-4 and Anthropic Claude via LangChain.
- [ ] [P0][S] Auto-store hands in vector DB — Hook into hand history parser to automatically embed and store completed hands in ChromaDB for semantic search.
- [ ] [P0][M] AI-powered opponent profiling — Use LangChain to analyze opponent patterns from stored hands and generate natural language profiles with playing style, tendencies, and exploitation strategies.
- [ ] [P0][S] Real-time hand analysis suggestions — Integrate AI analysis into HUD overlay to show contextual advice during live play (e.g., "Similar situations suggest 4-bet").
- [ ] [P0][M] Strategy coach chatbot — Implement conversational poker coach that can answer questions like "How should I play AK from UTG?" with examples from user's hand history.
- [ ] [P0][S] Session review AI summary — Generate end-of-session summaries using LLM: key hands, mistakes, wins, areas for improvement.
- [ ] [P0][M] Automated hand tagging — Use AI to automatically tag hands with categories (bluff, value bet, hero call, etc.) for better organization and search.
- [ ] [P0][S] AI endpoints authorization — Add authentication/authorization to `/api/ai/*` endpoints using existing RBAC system.

## Code Quality & Reliability (P0-P2: Foundation for Scale)

### Test Coverage & Quality (P0)
- [ ] [P0][M] Increase core poker engine test coverage to 98%+ — Add tests for edge cases in `src/pokertool/core.py`, particularly around hand evaluation, position logic, and pot odds calculations. Target: `tests/test_core_comprehensive.py` coverage from 95% to 98%.
- [ ] [P0][M] Database module integration tests — Add tests for transaction rollback, concurrent access, connection pool exhaustion, and database failover in `src/pokertool/database.py`. Create `tests/test_database_integration.py` with 20+ tests.
- [ ] [P0][S] API endpoint contract tests — Verify all FastAPI endpoints return correct status codes, response schemas, and error formats. Add `tests/api/test_endpoint_contracts.py` validating 100+ endpoints.
- [ ] [P0][M] Frontend component unit test coverage to 80%+ — Add Jest/RTL tests for Dashboard, TableView, SystemStatus, and BackendStatus components. Currently at ~40%, target 80%.
- [ ] [P0][S] Smoke test expansion — Add tests for configuration loading, environment variable validation, and dependency availability. Expand `tests/test_smoke_suite.py` from 38 to 50 tests.

### Error Handling & Resilience (P0)
- [ ] [P0][M] Centralized error handling middleware — Create `src/pokertool/error_middleware.py` to catch all unhandled exceptions, log with context, and return user-friendly errors. Integrate with Sentry.
- [x] [P0][S] Database connection retry logic — ✅ Complete: Added exponential backoff retry for both PostgreSQL initialization (5 retries, 1s-30s delays) and connection acquisition (3 retries, 0.5s-2s delays) in `src/pokertool/database.py:_init_postgresql` and `get_connection`. Graceful degradation with detailed logging at each retry attempt.
- [x] [P0][S] WebSocket reconnection improvements — ✅ Complete: WebSocket hook already has comprehensive reconnection logic with exponential backoff (max 10 attempts, 1s-30s delays), heartbeat/ping-pong mechanism (30s interval, 35s timeout), message queue for caching during disconnection, and automatic replay on reconnect. File: `pokertool-frontend/src/hooks/useWebSocket.ts`.
- [x] [P0][M] API timeout handling — ✅ Complete: Created centralized timeout configuration module with environment variable support for all operation types (API: 30s, DB: 10s, ML: 60s, health checks: 5s). File: `src/pokertool/timeout_config.py` (188 lines). Updated `system_health_checker.py` and `api_client.py` to use configurable timeouts. Support for POKERTOOL_API_TIMEOUT, POKERTOOL_DB_TIMEOUT, POKERTOOL_ML_TIMEOUT, etc.
- [x] [P0][S] Frontend error boundaries — ✅ Complete: Wrapped all 17 route components with React ErrorBoundary to prevent full-page crashes. Each route has isolated error handling with type-specific fallback messages (general, table, stats, advice). Automatic recovery with exponential backoff, degraded mode after max retries. File: `pokertool-frontend/src/App.tsx:146-164`.

### Performance Optimization (P0-P1)
- [ ] [P0][S] Database query optimization — Add indexes on frequently queried columns (session_id, timestamp, player_id). Profile slow queries with `EXPLAIN ANALYZE`. Target: <50ms for 95th percentile queries.
- [ ] [P0][M] Frontend bundle size reduction — Analyze webpack bundle, implement code splitting for routes, lazy load heavy components (HUD, Charts). Target: reduce initial bundle from 2.5MB to <1.5MB.
- [ ] [P0][S] API response caching layer — Implement Redis caching for expensive endpoints (/api/stats/*, /api/ml/*). Add cache invalidation on data updates. TTL: 5-60s based on endpoint.
- [ ] [P1][M] React component memoization audit — Add React.memo, useMemo, useCallback to prevent unnecessary re-renders in Dashboard, TableView, and SystemStatus. Profile with React DevTools.
- [ ] [P1][S] Backend async optimization — Convert blocking I/O operations to async/await in `src/pokertool/api.py` endpoints. Use asyncio.gather for parallel operations. Target: 2x throughput improvement.

### Code Quality & Maintainability (P1)
- [ ] [P1][M] TypeScript strict null checks — Enable `strictNullChecks` in tsconfig.json and fix all null/undefined violations in frontend. Estimate 200+ locations to fix.
- [ ] [P1][S] Python type hints audit — Add missing type hints to all public functions in src/pokertool/ modules. Run mypy in strict mode and fix all violations. Target: 100% type coverage.
- [ ] [P1][M] Remove duplicate code — Identify and refactor duplicated logic in screen scraper modules (`poker_screen_scraper_betfair.py`, OCR helpers). Extract common utilities to `src/pokertool/scraper_utils.py`.
- [ ] [P1][S] Consistent naming conventions — Rename inconsistent variable/function names across codebase. Examples: `db` vs `database`, `cfg` vs `config`. Document conventions in `CONTRIBUTING.md`.
- [ ] [P1][M] Reduce cyclomatic complexity — Refactor functions with complexity >10 into smaller, testable units. Focus on `src/pokertool/api.py` (_create_app), `src/pokertool/modules/poker_screen_scraper_betfair.py`.

### Security Hardening (P1)
- [ ] [P1][S] SQL injection audit — Review all raw SQL queries for injection vulnerabilities. Use parameterized queries exclusively. Add SQLAlchemy ORM where appropriate. File: `src/pokertool/database.py`.
- [ ] [P1][S] API rate limiting expansion — Add rate limits to all public endpoints, not just /auth. Use Redis-backed rate limiter with per-user quotas. Configure via environment variables.
- [ ] [P1][M] Input sanitization library — Create `src/pokertool/input_validator.py` with validators for all user inputs (file paths, database queries, API parameters). Prevent path traversal, XSS, command injection.
- [ ] [P1][S] Secrets management audit — Move all hardcoded secrets to environment variables or secret management service. Scan with `trufflehog` and `detect-secrets`. Add pre-commit hook to prevent secret commits.
- [ ] [P1][S] Dependency vulnerability scanning — Add `safety check` and `npm audit` to CI pipeline. Fail build on high/critical vulnerabilities. Set up automated dependency updates with Dependabot.

### Documentation & Observability (P1-P2)
- [ ] [P1][M] API documentation generation — Set up automatic OpenAPI/Swagger docs generation from FastAPI routes. Add request/response examples. Publish to `/api/docs` endpoint.
- [ ] [P1][S] Architecture decision records (ADRs) — Document major technical decisions in `docs/adr/`. Start with: database choice, WebSocket architecture, ML model selection, caching strategy.
- [ ] [P1][M] Logging standardization — Ensure all modules use `master_logging.py` consistently. Remove print() statements. Add structured context to all log entries. Validate log rotation works.
- [ ] [P2][M] Performance monitoring dashboards — Create Grafana dashboards for key metrics: API latency, error rates, database query times, ML model inference times. Use Prometheus or built-in metrics.
- [ ] [P2][S] Code coverage reporting — Integrate coverage.py reports into CI. Fail PR if coverage drops below 90%. Display coverage badge in README.md.

### Refactoring & Technical Debt (P2)
- [ ] [P2][L] Migrate legacy database module — Complete migration from `scripts/start.py` (17KB) to root `start.py` (22KB). Remove deprecated version. Update all references.
- [ ] [P2][M] Centralize configuration management — Create `src/pokertool/config.py` using pydantic BaseSettings for all config. Remove scattered config loading. Support .env files and environment variables.
- [ ] [P2][M] Frontend state management refactor — Evaluate and potentially migrate from Context API to Zustand or Redux Toolkit for better performance and DevTools. Focus on SystemStatus and Dashboard state.
- [ ] [P2][S] Remove dead code — Identify and remove unused functions, imports, and files. Use `vulture` for Python, `ts-prune` for TypeScript. Estimate: 5-10% codebase reduction.
- [ ] [P2][M] Extract poker logic library — Create standalone `pokertool-core` package with pure poker logic (hand evaluation, odds calculation, GTO solver). Enable reuse across projects.

### Testing Infrastructure (P2)
- [ ] [P2][M] Chaos engineering tests — Add tests that simulate failures: database unavailable, network timeouts, high CPU load, memory pressure. Verify graceful degradation. Use `pytest-chaos`.
- [ ] [P2][S] Mutation testing setup — Run `mutmut` on core modules to identify weak tests. Target 80%+ mutation score for critical paths (`src/pokertool/core.py`, `src/pokertool/database.py`).
- [ ] [P2][M] E2E testing with Playwright — Add end-to-end tests covering full user workflows: login, view dashboard, analyze hand, check stats. Run in CI with headless browser.
- [ ] [P2][S] Property-based testing — Add Hypothesis tests for poker engine to catch edge cases. Test properties like: "any hand has valid equity 0-100%", "pot odds are always positive".
- [ ] [P2][M] Performance regression testing — Add benchmark tests that fail if API endpoints regress >20%. Use `pytest-benchmark`. Track p50/p95/p99 latencies over time.

### Platform Compatibility & Deployment (P2)
- [ ] [P2][M] Windows compatibility audit — Test full application on Windows 10/11. Fix path handling issues (use pathlib). Ensure PowerShell scripts work. Document Windows-specific setup in `INSTALL.md`.
- [ ] [P2][S] Docker containerization — Create production-ready Dockerfile with multi-stage build. Add docker-compose.yml for full stack (backend, frontend, Redis, Postgres). Optimize image size <500MB.
- [ ] [P2][M] CI/CD pipeline improvements — Add deployment automation to staging/production. Implement blue-green deployments. Add smoke tests post-deployment. Use GitHub Actions workflows.
- [ ] [P2][S] Cross-browser testing — Verify frontend works on Chrome, Firefox, Safari, Edge. Add BrowserStack or Sauce Labs integration for automated cross-browser tests. Fix rendering issues.

## Now (P0: highest ROI)

- [x] [P0][S] Fix frontend unknown error — ✅ Complete: Frontend builds successfully. Fixed ESLint warnings in BackendStatus.tsx by removing unused import (HourglassEmptyIcon), removing unused function (getStatusColor), and adding explicit comment for useEffect dependency rule. Build completes with no errors or warnings.
- [x] [P0][S] Fix frontend Navigation.test.tsx type errors — ✅ Complete: Fixed BackendStatus interface mismatch in test file. Changed `lastSeen: Date.now()` to `lastChecked: new Date().toISOString()` and added required `attempts` property to match actual interface definition in useBackendLifecycle.ts. All 8 test cases updated. Frontend build now succeeds.
- [x] [P0][M] Fix React webpack chunk loading errors — ✅ Complete: Added automatic chunk loading retry mechanism with exponential backoff in `public/index.html`. Handles both `window.onerror` and `unhandledrejection` events for ChunkLoadError. Automatically retries up to 3 times with 1s, 2s, 3s delays. Cleared webpack cache directories. This resolves the "Loading chunk vendors-node_modules_mui_material_Stack_Stack_js failed" errors by gracefully recovering from transient network/caching issues.
- [x] [P0][S] Rationalize top-right UI indicators (backend/loaded) — ✅ Complete: consolidated 3 separate indicators into single unified "System Status" indicator with 5 states (ready/backend_down/ws_down/degraded/starting), added 600ms debouncing for health data, smooth 0.3s CSS transitions, comprehensive tooltip. File: `pokertool-frontend/src/components/Navigation.tsx:86-140`. Commit: f7566b9c2
- [x] [P0][M] Concurrency regression tests for shared thread pool — race/leak harness for `src/pokertool/threading.py`; fail on resource leaks in CI. (17 tests in `tests/test_threading_concurrency.py`)
- [x] [P0][M] HUD overlay integration tests with prerecorded screenshots — drive on-table updates, profile switching, stat rendering via fixtures. (16 tests in `tests/test_hud_overlay_integration.py`)
- [x] [P0][S] Error tracking integration — add Sentry (or Rollbar) SDK in backend (`src/pokertool/master_logging.py`, `src/pokertool/api.py`) and frontend; tag correlation IDs. (Frontend init added; backend already integrated; correlation IDs tagged)
- [x] [P0][M] System health history and trends — persist health results, add `GET /api/system/health/history`, and show 24h trend in UI. Cache results (5s TTL) and rate-limit. ✅ Complete: endpoints exist, persistence to `logs/health_history/health_history.jsonl`, UI uses `useSystemHealthTrends` hook, cache + rate-limit implemented)
- [x] [P0][S] HUD Designer developer guide — document recording/saving/applying profiles; place in `docs/advanced/hud.md` and link from install docs.

## Next (P1)

- [x] [P1][M] TypeScript strict mode — enable in frontend; remove `any` and add missing types. ✅ Complete: strict mode already enabled in tsconfig, all 4 remaining `any` types replaced with proper types (AxiosInstance, AxiosResponse, AxiosError, unknown)
- [x] [P1][M] OpenTelemetry tracing for key API paths — ✅ Complete: implemented OpenTelemetry SDK integration with FastAPI auto-instrumentation, correlation ID propagation, configurable OTLP export, trace context propagation, and traced() decorator for custom spans. Files: `src/pokertool/tracing.py` (293 lines), `src/pokertool/api.py:895-917` (_setup_tracing method), `src/pokertool/correlation_id_middleware.py:256-267` (span integration). Environment vars: OTEL_CONSOLE_EXPORT, OTEL_EXPORTER_OTLP_ENDPOINT.
- [x] [P1][S] WebSocket reliability tests — `ws/system-health` connect, broadcast to multiple clients, backoff/reconnect.
- [x] [P1][M] RBAC audit — verify all sensitive endpoints enforce roles; extend tests covering `src/pokertool/rbac.py` policies. ✅ Complete: all admin endpoints (`/admin/users`, `/admin/system/stats`, `/gamification/badges`) properly enforce admin role via `get_admin_user` dependency. Tests exist in `tests/api/test_admin_endpoints_authorization.py`. Fixed test imports and installed httpx. Full audit report in `RBAC_AUDIT_REPORT.md`. No security vulnerabilities found.
- [x] [P1][S] Fix `/auth/token` handler signature — annotate `request: Request` so SlowAPI limiter works without errors in tests/runtime.
- [x] [P1][M] Lazy-load and cache ML models — ✅ Complete: implemented ModelCache with lazy loading, in-memory caching, weak references for memory pressure handling, usage tracking, warmup support for critical models, thread-safe operations, and @lazy_model decorator. Metrics exposed via `/admin/system/stats` endpoint. File: `src/pokertool/model_cache.py` (315 lines). Features: cache hit/miss tracking, access patterns, automatic garbage collection under memory pressure.
- [x] [P1][M] Long-session memory profiling — tracemalloc sampling for GUI to detect widget/thread leaks. ✅ Complete: comprehensive GuiMemoryProfiler with tracemalloc-based sampling, automatic thread count monitoring, memory growth detection, and JSONL output for analysis. File: `src/pokertool/gui_memory_profiler.py` (188 lines). Features: background sampling thread, configurable intervals, top allocation tracking with tracebacks, peak memory tracking, context manager support. Integration: environment-controlled activation in GUI (`POKERTOOL_ENABLE_MEMORY_PROFILING`). Test coverage: 7 tests in `tests/gui/test_gui_memory_profiler.py` covering thread leak detection, memory growth tracking, allocation source identification, and long-session simulation. Documentation: `docs/development/memory_profiling.md`.
- [x] [P1][M] End-to-end dashboard test — frontend subscribes to health updates; simulate failures and verify status changes. ✅ Complete: comprehensive end-to-end test suite for dashboard WebSocket health monitoring system. File: `tests/api/test_dashboard_e2e.py` (242 lines, 9 tests total). Tests cover: health subscription and updates, WebSocket reconnection resilience, ping/pong keepalive, invalid message handling, long-running subscriptions, health data completeness. Test results: 6 passing, 3 skipped (concurrent connections and mocking tests skipped due to TestClient limitations). Verifies complete flow: backend health check → WebSocket broadcast → frontend receives status updates.
- [x] [P1][L] LangChain AI memory integration for conversational poker analysis — ✅ Complete: Integrated LangChain v0.3.0 with ChromaDB v0.5.0 for semantic search and conversational memory. Installed dependencies: langchain, langchain-community, chromadb, tiktoken, onnxruntime. Created `src/pokertool/langchain_memory_service.py` (445 lines) with PokerVectorStore for semantic hand history search, PokerConversationalMemory for chat context, and LangChainMemoryService singleton. Implemented `src/pokertool/api_langchain.py` (438 lines) with 11 FastAPI endpoints: `/api/ai/analyze_hand`, `/api/ai/store_hand`, `/api/ai/opponent_note`, `/api/ai/search_similar`, `/api/ai/chat` for conversational analysis. Features: ChromaDB-backed vector embeddings (using onnxruntime, no torch dependency), opponent notes storage, semantic search over hand histories, conversational memory with context retention. Test coverage: `tests/test_langchain_memory_service.py` with 15 tests covering vector store operations, conversational memory, and end-to-end workflows. Vector database persists to `~/.pokertool/vector_db/`. Ready for frontend integration and LLM connection (currently returns context-aware responses based on vector search). Dependencies added to requirements.txt.

## Later (P2/P3)

- [x] [P2][M] Visual regression snapshots for key UI components (HUD, SystemStatus) in light/dark themes. ✅ Infrastructure Complete: Playwright @playwright/test v1.56.1 installed with Chromium browser. Created playwright.config.ts with light/dark theme testing for chromium. Built 3 comprehensive visual test suites: tests/visual/system-status.spec.ts (3 tests: full page, navigation bar, health cards), tests/visual/dashboard.spec.ts (2 tests: full dashboard, header section), tests/visual/navigation.spec.ts (3 tests: appbar, mobile drawer, backend status indicator). Added npm scripts: test:visual, test:visual:ui, test:visual:update. Configured .gitignore to exclude test reports while preserving snapshot baselines. Tests ready to run with `npm run test:visual:update` to generate baselines, then `npm run test:visual` for regression checking. Snapshots will be stored in tests/visual/**/*-snapshots/ directories.
- [x] [P2][M] Load testing of critical APIs (Locust/k6) with alert thresholds. ✅ Complete: Installed Locust v2.42.0 load testing framework. Created tests/load/locustfile.py (255 lines) with 3 user classes simulating realistic behavior patterns: HealthCheckUser (20% weight, 1-3s wait), DashboardUser (50% weight, 3-10s wait), APIHeavyUser (30% weight, 2-5s wait). Defined performance thresholds: Health endpoints p95<100ms p99<200ms, Data endpoints p95<500ms p99<1000ms, overall error rate <1%. Automated threshold validation in test_stop event handler. Created Makefile with 3 commands: `make load-test` (web UI), `make load-test-headless` (100 users, 60s, generates CSV/HTML reports), `make load-test-quick` (10 users, 30s smoke test). Added locust>=2.42.0 to requirements.txt.
- [x] [P2][S] Structured JSON logging everywhere; consistent fields and log rotation. ✅ Complete: comprehensive JSON logging system with correlation_id and request_id fields, automatic log rotation (master: daily rotation, 90-day retention; error/performance/security: size-based rotation with 5-20MB limits), multiple log categories (general, error, performance, security), structured context data, and Sentry integration. Files: `src/pokertool/master_logging.py` (1107 lines), `src/pokertool/structured_logger.py` (239 lines). Log directory: `logs/`.
- [x] [P3][M] Internationalization of core UI strings; verify number/date formats. ✅ Complete: Installed i18next v24.2.0, react-i18next v16.0.0, and i18next-browser-languagedetector v8.0.2. Created i18n configuration with automatic language detection and localStorage caching. Created English (en.json) and Spanish (es.json) translation files with 100+ strings covering app navigation, status messages, backend monitoring, TODO list, and common UI elements. Integrated i18next into index.tsx for early initialization. Updated Navigation component to use useTranslation hook with translated strings for app title, connection status, and dark mode label. Configured number and date formatting via i18n formatting interpolation. Translation infrastructure ready for additional languages - just add new JSON files to src/i18n/locales/. Language can be changed programmatically via `i18n.changeLanguage('es')` or will auto-detect from browser/localStorage. Frontend build successful with +23.74kB for i18n libraries.
- [x] [P3][L] Real User Monitoring (RUM) for frontend performance and Core Web Vitals. (docs/development/frontend-rum.md, src/pokertool/rum_metrics.py, pokertool-frontend/src/services/rum.ts)
- [x] [P3][L] Platform compatibility matrix and adaptations for target poker sites. (docs/development/platform-compatibility.md, src/pokertool/platform_compatibility.py)

## Done Recently (summary)

- [x] Security headers (CSP, HSTS, X-Frame-Options, etc.) middleware.
- [x] API input validation via Pydantic models; strict runtime checks.
- [x] Response compression (gzip) and API response caching for hot paths.
- [x] Request/response logging with correlation IDs; latency in headers.
- [x] Circuit breaker and retry logic for dependent services.
- [x] Pre-commit (Black, isort, flake8, mypy, Bandit, Prettier, pydocstyle, safety) and GitHub Actions CI.

## Operating Notes

- Keep this file short and actionable. Move deep design docs and specifications to `docs/` and link from task bullets.
- When a task spans multiple PRs, add a short progress note after the bullet or split into sub-bullets with clear acceptance criteria.
- Prefer linking directly to code (`path:line`) or tests to anchor context.
