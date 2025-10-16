# Health Checks - Developer Guide

## Overview

The System Health Checker provides a comprehensive framework for monitoring all PokerTool components. This guide explains how to add, modify, and debug health checks.

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│   SystemHealthChecker                    │
│   - Manages check registration          │
│   - Executes periodic checks (30s)      │
│   - Caches results                       │
│   - Broadcasts via WebSocket            │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
  ┌─────────┐ ┌─────────┐ ┌─────────┐
  │ Backend │ │Scraping │ │   ML    │
  │  Checks │ │ Checks  │ │ Checks  │
  └─────────┘ └─────────┘ └─────────┘
```

### File Locations

- **Health Checker**: `src/pokertool/system_health_checker.py`
- **API Integration**: `src/pokertool/api.py` (lines 697-700, 781-834, 1256-1320)
- **Frontend**: `pokertool-frontend/src/components/SystemStatus.tsx`

## Adding a New Health Check

### Step 1: Create the Health Check Function

```python
async def check_my_feature_health() -> HealthStatus:
    """
    Check my custom feature functionality.

    Returns:
        HealthStatus: Health status object with feature information
    """
    try:
        # Import your module
        from pokertool.my_module import MyFeature

        # Test basic functionality
        feature = MyFeature()
        result = feature.test_method()

        # Validate result
        if result:
            return HealthStatus(
                feature_name='my_feature',
                category='ml',  # backend, scraping, ml, gui, advanced
                status='healthy',
                last_check=datetime.utcnow().isoformat(),
                description='My custom feature description',
                metadata={'result': result}  # Optional extra data
            )
        else:
            return HealthStatus(
                feature_name='my_feature',
                category='ml',
                status='degraded',
                last_check=datetime.utcnow().isoformat(),
                error_message='Feature returned unexpected result',
                description='My custom feature description'
            )

    except ImportError as e:
        return HealthStatus(
            feature_name='my_feature',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=f'Module not installed: {str(e)}',
            description='My custom feature description'
        )
    except Exception as e:
        return HealthStatus(
            feature_name='my_feature',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='My custom feature description'
        )
```

### Step 2: Register the Health Check

Add to `register_all_health_checks()` function in `system_health_checker.py`:

```python
def register_all_health_checks(checker: SystemHealthChecker):
    """Register all health checks with the checker."""

    # ... existing checks ...

    # Add your new check
    checker.register_check(
        'my_feature',                      # Unique identifier
        'ml',                              # Category
        check_my_feature_health,           # Check function
        'My custom feature description',   # User-facing description
        timeout=3.0                        # Max execution time in seconds
    )

    logger.info(f"Registered {len(checker.checks)} health checks")
```

### Step 3: Test Your Health Check

```bash
# Start the API server
python scripts/launch_api_simple.py

# Check the logs for your health check
# Should see: "Registered 21 health checks" (or current count + 1)

# Test via API
curl http://localhost:5001/api/system/health | jq '.categories.ml.checks[] | select(.feature_name=="my_feature")'

# Or view in the frontend
# Navigate to http://localhost:3000/system-status
```

## Health Check Best Practices

### 1. **Always Return HealthStatus**

✅ **Good**:
```python
async def check_feature() -> HealthStatus:
    try:
        # Check logic
        return HealthStatus(...)
    except Exception as e:
        return HealthStatus(status='failing', error_message=str(e), ...)
```

❌ **Bad**:
```python
async def check_feature():
    if feature_works():
        return True  # Don't return boolean!
    raise Exception("Failed")  # Don't raise, return HealthStatus
```

### 2. **Use Appropriate Timeouts**

```python
# Fast checks: database queries, file existence
timeout=2.0

# Medium checks: HTTP requests, basic ML inference
timeout=3.0

# Slow checks: Complex ML operations, external services
timeout=5.0
```

### 3. **Provide Meaningful Error Messages**

✅ **Good**:
```python
error_message='TensorFlow not installed. Run: pip install tensorflow>=2.0'
```

❌ **Bad**:
```python
error_message='Error'  # Too vague
error_message=repr(e)  # Too technical/long
```

### 4. **Use Correct Status Values**

- **healthy**: Feature working normally
- **degraded**: Feature partially working (e.g., fallback mode, reduced performance)
- **failing**: Feature completely non-functional
- **unknown**: Unable to determine status (rare, usually during initialization)

### 5. **Include Useful Metadata**

```python
metadata={
    'version': '2.1.0',
    'model_accuracy': 0.95,
    'cache_hit_rate': 0.87,
    'last_trained': '2025-10-01'
}
```

## Categories

Choose the appropriate category:

| Category | Purpose | Examples |
|----------|---------|----------|
| `backend` | Core API infrastructure | Database, WebSocket, Authentication |
| `scraping` | Screen capture and OCR | Screen capture, OCR, Table detection |
| `ml` | Machine learning features | GTO solver, Opponent modeling, Neural nets |
| `gui` | Frontend components | React server, Static assets |
| `advanced` | Optional/premium features | ROI tracking, Tournament support, Multi-table |

## Advanced Topics

### Async vs Sync Checks

All health check functions must be async:

```python
# ✅ Correct
async def check_feature() -> HealthStatus:
    result = await async_operation()
    return HealthStatus(...)

# ✅ Also correct (sync code in async function)
async def check_feature() -> HealthStatus:
    result = sync_operation()  # Sync call is fine
    return HealthStatus(...)

# ❌ Wrong
def check_feature() -> HealthStatus:  # Not async!
    return HealthStatus(...)
```

### Timeout Protection

The SystemHealthChecker automatically applies timeouts:

```python
try:
    status = await asyncio.wait_for(
        check.check_func(),
        timeout=check.timeout  # Your specified timeout
    )
except asyncio.TimeoutError:
    # Automatically returns failing status
    pass
```

You don't need to implement timeout logic in your check function.

### Caching Results

Health check results are automatically cached:

```python
# Last results stored in:
checker.last_results[feature_name]

# Access cached results:
summary = checker.get_summary()
```

### Broadcasting Updates

WebSocket updates are automatically broadcast when checks complete:

```python
# Set broadcast callback (done automatically in API initialization)
checker.set_broadcast_callback(broadcast_health_update)

# Clients receive:
{
    "type": "health_update",
    "timestamp": "2025-10-16T12:34:56Z",
    "updates": [
        {"feature": "my_feature", "status": "healthy", ...}
    ]
}
```

## Testing

### Unit Testing Health Checks

```python
# tests/test_health_checks.py
import pytest
from pokertool.system_health_checker import check_my_feature_health

@pytest.mark.asyncio
async def test_my_feature_health_success():
    """Test health check when feature is working."""
    status = await check_my_feature_health()

    assert status.feature_name == 'my_feature'
    assert status.category == 'ml'
    assert status.status == 'healthy'
    assert status.error_message is None

@pytest.mark.asyncio
async def test_my_feature_health_failure():
    """Test health check when feature is broken."""
    # Mock the feature to fail
    with patch('pokertool.my_module.MyFeature') as mock:
        mock.side_effect = Exception('Test error')

        status = await check_my_feature_health()

        assert status.status == 'failing'
        assert 'Test error' in status.error_message
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_health_checker_integration():
    """Test health checker with custom check."""
    checker = SystemHealthChecker(check_interval=60)

    # Register check
    checker.register_check(
        'test_feature',
        'backend',
        check_my_feature_health,
        'Test feature',
        timeout=2.0
    )

    # Run checks
    results = await checker.run_all_checks()

    assert 'test_feature' in results
    assert results['test_feature'].status in ['healthy', 'degraded', 'failing']
```

## Debugging

### Enable Detailed Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pokertool.system_health_checker')
logger.setLevel(logging.DEBUG)
```

### Check Logs

```bash
# Watch health check execution
tail -f pokertool.log | grep system_health_checker

# Expected output:
# INFO [pokertool.system_health_checker] Running 20 health checks...
# INFO [pokertool.system_health_checker] Health check complete: 4 healthy, 0 degraded, 16 failing
```

### Manual Testing

```python
# Test a single check
import asyncio
from pokertool.system_health_checker import check_my_feature_health

async def test():
    result = await check_my_feature_health()
    print(f"Status: {result.status}")
    print(f"Error: {result.error_message}")

asyncio.run(test())
```

### Common Issues

**Issue**: Health check never completes
- **Cause**: Blocking operation without timeout
- **Solution**: Ensure all operations are async or have internal timeouts

**Issue**: False positives (always healthy when actually failing)
- **Cause**: Exception handling too broad
- **Solution**: Be specific about what constitutes success

**Issue**: Timeout too short
- **Cause**: Complex operation needs more time
- **Solution**: Increase timeout or optimize check logic

## API Reference

### HealthStatus Class

```python
@dataclass
class HealthStatus:
    feature_name: str           # Unique feature identifier
    category: str              # backend, scraping, ml, gui, advanced
    status: str                # healthy, degraded, failing, unknown
    last_check: str            # ISO format timestamp
    latency_ms: Optional[float]        # Response time
    error_message: Optional[str]       # Error details if failing
    metadata: Optional[Dict[str, Any]] # Additional data
    description: Optional[str]         # User-facing description
```

### SystemHealthChecker Methods

```python
class SystemHealthChecker:
    def __init__(self, check_interval: int = 30)

    def register_check(
        self,
        name: str,
        category: str,
        check_func: Callable[[], Awaitable[HealthStatus]],
        description: str,
        timeout: float = 5.0
    ) -> None

    async def run_check(self, feature_name: str) -> HealthStatus
    async def run_all_checks(self) -> Dict[str, HealthStatus]

    def start_periodic_checks(self) -> None
    async def stop_periodic_checks(self) -> None

    def get_summary(self) -> Dict[str, Any]
    def set_broadcast_callback(self, callback: Callable) -> None
```

## Examples

### Example 1: External Service Check

```python
async def check_redis_health() -> HealthStatus:
    """Check Redis cache availability."""
    try:
        import redis.asyncio as redis

        client = redis.Redis(host='localhost', port=6379)
        await client.ping()

        return HealthStatus(
            feature_name='redis_cache',
            category='backend',
            status='healthy',
            last_check=datetime.utcnow().isoformat(),
            description='Redis cache for session storage'
        )
    except Exception as e:
        return HealthStatus(
            feature_name='redis_cache',
            category='backend',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=f'Redis unavailable: {str(e)}',
            description='Redis cache for session storage'
        )
```

### Example 2: ML Model Check

```python
async def check_nn_model_health() -> HealthStatus:
    """Check neural network model availability and performance."""
    try:
        from pokertool.models import load_nn_model

        start = time.time()
        model = load_nn_model()

        # Test inference
        test_input = generate_test_input()
        prediction = model.predict(test_input)
        latency = (time.time() - start) * 1000

        # Check if performance is acceptable
        if latency > 1000:  # 1 second
            return HealthStatus(
                feature_name='nn_model',
                category='ml',
                status='degraded',
                last_check=datetime.utcnow().isoformat(),
                latency_ms=latency,
                error_message=f'Slow inference: {latency:.0f}ms (expected <1000ms)',
                description='Neural network hand evaluation',
                metadata={'model_version': model.version}
            )

        return HealthStatus(
            feature_name='nn_model',
            category='ml',
            status='healthy',
            last_check=datetime.utcnow().isoformat(),
            latency_ms=latency,
            description='Neural network hand evaluation',
            metadata={'model_version': model.version}
        )

    except Exception as e:
        return HealthStatus(
            feature_name='nn_model',
            category='ml',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Neural network hand evaluation'
        )
```

### Example 3: File System Check

```python
async def check_hand_history_storage_health() -> HealthStatus:
    """Check hand history file storage."""
    try:
        from pathlib import Path

        storage_path = Path.home() / '.pokertool' / 'hands'

        # Check directory exists and is writable
        if not storage_path.exists():
            storage_path.mkdir(parents=True, exist_ok=True)

        # Test write permissions
        test_file = storage_path / '.health_check'
        test_file.write_text('test')
        test_file.unlink()

        # Check disk space
        import shutil
        total, used, free = shutil.disk_usage(storage_path)
        free_gb = free // (2**30)

        if free_gb < 1:
            return HealthStatus(
                feature_name='hand_history_storage',
                category='advanced',
                status='degraded',
                last_check=datetime.utcnow().isoformat(),
                error_message=f'Low disk space: {free_gb}GB free',
                description='Hand history file storage',
                metadata={'free_space_gb': free_gb}
            )

        return HealthStatus(
            feature_name='hand_history_storage',
            category='advanced',
            status='healthy',
            last_check=datetime.utcnow().isoformat(),
            description='Hand history file storage',
            metadata={'free_space_gb': free_gb}
        )

    except Exception as e:
        return HealthStatus(
            feature_name='hand_history_storage',
            category='advanced',
            status='failing',
            last_check=datetime.utcnow().isoformat(),
            error_message=str(e),
            description='Hand history file storage'
        )
```

---

**Last Updated**: October 2025
**Version**: v86.0.0
**Module**: system_health_checker.py
