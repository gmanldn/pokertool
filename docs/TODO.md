# PokerTool TODO

Last updated: 2025-10-20

This file tracks the active backlog at a glance. Keep items small, outcome‑focused, and linked to code where possible. Older, verbose plans have been removed; refer to git history if needed.

Conventions
- Priority: P0 (critical ROI), P1 (high), P2 (medium), P3 (low)
- Effort: S (<1 day), M (1–3 days), L (>3 days)
- Status: TODO | IN PROGRESS | BLOCKED | DONE
- Format: [ ] [P#][E#] Title — details and code path(s)

## Now (P0: highest ROI)

- [x] [P0][S] Rationalize top-right UI indicators (backend/loaded) — ✅ Complete: consolidated 3 separate indicators into single unified "System Status" indicator with 5 states (ready/backend_down/ws_down/degraded/starting), added 600ms debouncing for health data, smooth 0.3s CSS transitions, comprehensive tooltip. File: `pokertool-frontend/src/components/Navigation.tsx:86-140`. Commit: f7566b9c2
- [x] [P0][M] Concurrency regression tests for shared thread pool — race/leak harness for `src/pokertool/threading.py`; fail on resource leaks in CI. (17 tests in `tests/test_threading_concurrency.py`)
- [x] [P0][M] HUD overlay integration tests with prerecorded screenshots — drive on-table updates, profile switching, stat rendering via fixtures. (16 tests in `tests/test_hud_overlay_integration.py`)
- [x] [P0][S] Error tracking integration — add Sentry (or Rollbar) SDK in backend (`src/pokertool/master_logging.py`, `src/pokertool/api.py`) and frontend; tag correlation IDs. (Frontend init added; backend already integrated; correlation IDs tagged)
- [x] [P0][M] System health history and trends — persist health results, add `GET /api/system/health/history`, and show 24h trend in UI. Cache results (5s TTL) and rate-limit. ✅ Complete: endpoints exist, persistence to `logs/health_history/health_history.jsonl`, UI uses `useSystemHealthTrends` hook, cache + rate-limit implemented)
- [x] [P0][S] HUD Designer developer guide — document recording/saving/applying profiles; place in `docs/advanced/hud.md` and link from install docs.

## Next (P1)

- [x] [P1][M] TypeScript strict mode — enable in frontend; remove `any` and add missing types. ✅ Complete: strict mode already enabled in tsconfig, all 4 remaining `any` types replaced with proper types (AxiosInstance, AxiosResponse, AxiosError, unknown)
- [ ] [P1][M] OpenTelemetry tracing for key API paths — minimal spans around request handling and external calls; propagate correlation IDs.
- [x] [P1][S] WebSocket reliability tests — `ws/system-health` connect, broadcast to multiple clients, backoff/reconnect.
- [x] [P1][M] RBAC audit — verify all sensitive endpoints enforce roles; extend tests covering `src/pokertool/rbac.py` policies. ✅ Complete: all admin endpoints (`/admin/users`, `/admin/system/stats`, `/gamification/badges`) properly enforce admin role via `get_admin_user` dependency. Tests exist in `tests/api/test_admin_endpoints_authorization.py`. Fixed test imports and installed httpx. Full audit report in `RBAC_AUDIT_REPORT.md`. No security vulnerabilities found.
- [x] [P1][S] Fix `/auth/token` handler signature — annotate `request: Request` so SlowAPI limiter works without errors in tests/runtime.
- [ ] [P1][M] Lazy-load and cache ML models — reduce startup latency and memory; add warmup path and metrics.
- [ ] [P1][M] Long-session memory profiling — tracemalloc sampling for GUI to detect widget/thread leaks.
- [ ] [P1][M] End-to-end dashboard test — frontend subscribes to health updates; simulate failures and verify status changes.

## Later (P2/P3)

- [ ] [P2][M] Visual regression snapshots for key UI components (HUD, SystemStatus) in light/dark themes.
- [ ] [P2][M] Load testing of critical APIs (Locust/k6) with alert thresholds.
- [ ] [P2][S] Structured JSON logging everywhere; consistent fields and log rotation. (Added correlation_id and request_id fields to JSON formatter)
- [ ] [P3][M] Internationalization of core UI strings; verify number/date formats.
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
