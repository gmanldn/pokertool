# Performance Benchmark Tests

Performance benchmarks for critical code paths to detect regressions.

## Performance Targets

| Operation | Target | Fail Threshold |
|-----------|--------|----------------|
| Hand analysis | <100ms | >120ms (+20%) |
| Database queries | <50ms | >60ms (+20%) |
| API endpoints | <200ms | >240ms (+20%) |
| Module imports | <1000ms | >1200ms (+20%) |

## Running Benchmarks

### Run All Benchmarks
```bash
pytest tests/benchmark/ -v
```

### Run with Performance Details
```bash
pytest tests/benchmark/ -v -s
```

### Run Only Benchmarks (Skip Other Tests)
```bash
pytest -m benchmark
```

### Fail on Regression
```bash
pytest tests/benchmark/ --benchmark-only
```

## Benchmark Categories

### Database Performance
- Connection establishment
- Simple queries (get_total_hands)
- Memory footprint

### API Performance
- Health endpoint response time
- System health endpoint
- Memory usage

### Import Performance
- Module import times
- Dependency loading

### Computation Performance
- Hand strength calculations
- Equity calculations

## CI Integration

Benchmarks run in CI on every PR:
- Fail if performance regresses >20%
- Generate performance comparison report
- Track trends over time

## Adding New Benchmarks

```python
def test_my_operation_performance(self):
    """Benchmark my operation (<100ms)."""
    start = time.time()

    # Your operation here
    result = my_expensive_operation()

    elapsed = (time.time() - start) * 1000  # ms

    assert result is not None
    assert elapsed < 100, f"Operation took {elapsed:.2f}ms (target: <100ms)"
```

## Memory Benchmarks

Use `tracemalloc` for memory profiling:

```python
import tracemalloc

tracemalloc.start()
# Your operation
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

peak_mb = peak / 1024 / 1024
assert peak_mb < 10, f"Used {peak_mb:.2f}MB (target: <10MB)"
```

## Profiling Tools

For deeper investigation:

```bash
# Profile with cProfile
python -m cProfile -o profile.stats your_script.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

## Performance Tips

1. **Run on consistent hardware** - CI provides stable baseline
2. **Warm up caches** - Run operation once before timing
3. **Multiple iterations** - Average over 10+ runs for accuracy
4. **Isolate tests** - Don't let tests affect each other
5. **Document baselines** - Track expected performance

## Troubleshooting

### Benchmarks Failing Locally

- Your machine may be slower than CI
- Adjust thresholds in test if needed
- Focus on relative performance, not absolute

### Benchmarks Passing Locally, Failing in CI

- CI may have more strict timeouts
- Check for resource contention
- Review CI logs for specific failures

### Inconsistent Results

- Run multiple times to establish baseline
- Check for background processes
- Use dedicated test environment
