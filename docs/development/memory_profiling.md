## GUI Memory Profiling

PokerTool can capture long-session memory diagnostics for the HUD/GUI. The profiler samples heap allocations with `tracemalloc`, records active thread counts, and writes structured JSONL entries for later analysis.

### Enabling the profiler

Set the environment variable before launching the GUI (desktop or `start.py`):

```bash
export POKERTOOL_ENABLE_MEMORY_PROFILING=1
# optional tuning
export POKERTOOL_MEMORY_INTERVAL=30        # seconds between samples (default 60)
export POKERTOOL_MEMORY_REPORT_LIMIT=20    # top allocation sites per snapshot (default 15)
```

When enabled, the profiler writes to `logs/memory/gui_memory.jsonl`. Each line contains:

- `timestamp` (UTC)
- current & peak traced memory in kilobytes
- active thread count
- `top_allocations`: the heaviest allocation sites with formatted tracebacks

### Analysing results

The JSONL format makes it easy to ingest into notebooks or dashboards:

```python
import json
from pathlib import Path

path = Path("logs/memory/gui_memory.jsonl")
samples = [json.loads(line) for line in path.open()]
```

Plot `current_kb` to visualise drift, or diff the `top_allocations` to spot widgets that are never released.

### Best practices

- Run the profiler during multi-hour HUD sessions to surface leaks.
- Combine with long-running automated GUI flows so memory is exercised.
- Commit suspicious snapshots to an issue and share the `gui_memory.jsonl` file for triage.
