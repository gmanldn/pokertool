# Detection Performance Tuning Guide

## Performance Targets

- **Target FPS:** 20-25 FPS
- **Latency:** <80ms per frame (p95)
- **Cache Hit Rate:** 60-80%
- **CPU Usage:** <40% single core
- **Memory:** <500MB for detection system

## Quick Wins

### 1. Enable Caching (60% improvement)
```bash
export DETECTION_ENABLE_CACHE=true
export DETECTION_CACHE_MAX_SIZE=150
export DETECTION_CACHE_TTL=2.0
```

### 2. Use Event Batching (40% reduction in network overhead)
```bash
export DETECTION_EVENT_BATCH_INTERVAL=0.1
export DETECTION_EVENT_MAX_BATCH_SIZE=50
```

### 3. Enable Event Deduplication (30% reduction in events)
```bash
export DETECTION_ENABLE_EVENT_DEDUP=true
```

### 4. Optimize Confidence Thresholds
```bash
# Higher thresholds = fewer events = better performance
export DETECTION_MIN_EMIT_CONFIDENCE=0.7
```

## Profiling

### Measure FPS
```python
from src.pokertool.detection_fps_counter import get_fps_counter

fps_counter = get_fps_counter()
# ... detection loop ...
print(f"Current FPS: {fps_counter.get_fps():.1f}")
print(f"Avg frame time: {fps_counter.get_avg_frame_time_ms():.1f}ms")
```

### Identify Bottlenecks
```python
from src.pokertool.detection_metrics_tracker import DetectionMetricsTracker

tracker = DetectionMetricsTracker()
# ... run detections ...

for det_type, metrics in tracker.get_all_metrics().items():
    print(f"{det_type}:")
    print(f"  Avg duration: {metrics.avg_duration_ms:.1f}ms")
    print(f"  Max duration: {metrics.max_duration_ms:.1f}ms")
    # Focus on types with highest avg_duration_ms
```

## Optimization Strategies

### Cache Strategy
- **When:** Stable table state, minimal changes
- **Benefit:** 2-3x speedup for unchanged regions
- **Trade-off:** 2-second stale data acceptable

### Parallel Detection
- **When:** Multi-core CPU available
- **Benefit:** 40-60% speedup for independent regions
- **Trade-off:** Increased CPU usage

### Adaptive ROI
- **When:** Low-confidence detections frequent
- **Benefit:** 20-30% speedup by focusing on reliable regions
- **Trade-off:** May miss edge cases

### GPU Acceleration
- **When:** CUDA/OpenCL available, high-res images
- **Benefit:** 3-5x speedup for image processing
- **Trade-off:** GPU memory requirement

## Monitoring

Track these metrics:
- FPS (target: >20)
- Frame time p95 (target: <80ms)
- Cache hit rate (target: >60%)
- Event throughput (target: <100/sec)
- Memory usage (target: <500MB)

## Troubleshooting

### Low FPS (<15 FPS)
1. Check CPU usage - if high, enable caching
2. Profile detection types - optimize slowest
3. Reduce image resolution
4. Enable parallel detection
5. Increase confidence thresholds

### High Latency (>100ms)
1. Profile hot paths
2. Enable detection cache
3. Use event batching
4. Optimize image preprocessing
5. Consider GPU acceleration

### High Memory (>1GB)
1. Reduce cache size
2. Lower event batch size
3. Clear old state snapshots
4. Check for memory leaks in detection loop

### Low Cache Hit Rate (<40%)
1. Increase TTL to 3-5 seconds
2. Increase cache size to 200-300
3. Check for frequent state changes
4. Review cache key generation
