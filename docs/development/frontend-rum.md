# Frontend Real User Monitoring (RUM)

PokerTool now captures Core Web Vitals and realtime navigation timings from the React frontend and streams them to the backend for aggregation. This provides visibility into user-perceived performance outside of synthetic benchmarks.

## What Gets Collected

- **Core Web Vitals:** CLS, LCP, INP, TTFB, plus FCP for additional context.
- **Navigation Timings:** High level duration, DOMContentLoaded, and load event durations.
- **Metadata:** Session identifier, page path, navigation type, release/environment tags, lightweight attribution data (e.g. largest layout shift target, interaction target).

Collection happens in `pokertool-frontend/src/services/rum.ts`. Web Vitals are sampled client-side (default 100% rate) and sent via `navigator.sendBeacon` to avoid blocking the UI.

## Backend Pipeline

1. **Ingestion endpoint** – `POST /api/rum/metrics` (see `src/pokertool/api.py`) accepts JSON payloads and enqueues persistence using FastAPI background tasks. Requests are rate-limited (`180/minute`) and correlation IDs from headers are propagated into the stored record when available.
2. **Storage** – `src/pokertool/rum_metrics.py` appends metrics as JSONL in `logs/rum/rum_metrics.jsonl`, trimming entries older than the retention window (default 7 days). The store normalises inputs and guards against oversized or malformed fields.
3. **Aggregation** – `GET /api/rum/summary` summarises the last N hours (default 24) with averages, p50/p75/p95, max values, rating distribution, and page/navigation histograms.

Supporting tests live in:

- `tests/test_rum_metrics_store.py` – unit coverage for persistence and aggregation.
- `tests/api/test_rum_metrics.py` – end-to-end ingestion/summary flow through FastAPI.

## Configuration

Environment knobs (all optional):

- `REACT_APP_RUM_ENABLED` – `"false"` disables collection in the frontend.
- `REACT_APP_RUM_SAMPLE_RATE` – float between 0 and 1 to down-sample clients.
- `REACT_APP_RUM_ENDPOINT` – override the ingestion URL (defaults to `/api/rum/metrics`).
- `REACT_APP_ENV` / `REACT_APP_VERSION` – forwarded as environment and release metadata.
- `POKERTOOL_RUM_DIR` (backend) – override storage directory for metrics JSONL.

## Operational Tips

- Use `PYTHONPATH=src python3 -m pokertool.platform_compatibility --format markdown` to regenerate the platform matrix, and `GET /api/rum/summary?hours=6` to inspect recent vitals before releases.
- Integrate the summary endpoint into dashboards or alerts to enforce Core Web Vitals budgets (e.g. LCP < 2.5s, INP < 200ms, CLS < 0.1).
- For additional analysis, the JSONL file can be imported into pandas or a time-series store; each line already contains ISO timestamps, page, and rating categories.

