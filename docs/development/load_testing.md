## PokerTool API Load Testing

The `tools/load_testing/locustfile.py` script exercises the highest-value REST endpoints (`/api/system/health`, `/api/system/health/history`, `/api/system/health/trends`, and `/api/scraping/accuracy/metrics`) and enforces alert thresholds for average latency and failure ratio.

### Prerequisites

Install Locust into your development environment:

```bash
pip install "locust>=2.20"
```

Optionally, add the `load-test` extra when installing PokerTool from source:

```bash
pip install -e ".[api,load-test]"
```

### Running the test

1. Start the backend API on `http://localhost:5001`.
2. Export credentials if your auth settings differ from defaults:

```bash
export POKERTOOL_LOADTEST_USERNAME=admin
export POKERTOOL_LOADTEST_PASSWORD=pokertool
```

3. Launch Locust (web UI):

```bash
locust -f tools/load_testing/locustfile.py
```

or run headless for CI:

```bash
locust -f tools/load_testing/locustfile.py \
  --headless --users 50 --spawn-rate 5 --run-time 10m
```

### Alert thresholds

The script fails the run (sets exit code 1) when either threshold is breached:

- `POKERTOOL_LOADTEST_MAX_AVG_MS` (default `500` ms)
- `POKERTOOL_LOADTEST_MAX_FAILURE_RATIO` (default `0.01`)

Tune these values via environment variables to match staging/production SLOs.

### Extending scenarios

Add additional tasks inside `PokerToolTasks` for endpoints you want to protect (e.g. `/api/analysis` or RBAC-protected routes). Each task automatically reuses the JWT acquired during `on_start`.
