# Backend Health Monitoring Issues - Investigation Report

## Executive Summary

The backend is running and fully operational, but **the frontend health monitor tab shows offline** due to multiple cascading issues. The core root causes are:

1. **Rate Limiting Too Aggressive** - Health endpoint hit by 429 (Too Many Requests)
2. **PYTHONPATH Not Set** - Backend startup script doesn't properly set Python module path
3. **Frontend Port Configuration** - Hardcoded port assumptions
4. **WebSocket Connection Failures** - Real-time health updates not being delivered
5. **Health Check Error Handling** - Poor error messages to frontend

---

## Investigation Findings

### Test Results

```bash
# Backend Health Endpoint Response
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
{"error":"Rate limit exceeded: 60 per 1 minute"}

# Backend Status
✅ uvicorn process running on port 5001
✅ FastAPI application initialized
✅ System health checker initialized
✅ Periodic health checks running (20 checks registered)
✅ Database connection working
✅ All backend services operational
```

### Root Causes Identified

#### 1. Rate Limiting Configuration (CRITICAL)
- **Issue**: Health endpoint rate-limited to 60 requests/minute
- **Impact**: Frontend polling every 30 seconds hits limit after ~2 hours
- **Location**: `src/pokertool/api.py:77-79` (SlowAPI rate limiter)
- **Severity**: CRITICAL - Blocks health monitoring completely

#### 2. Backend Startup Process (CRITICAL)
- **Issue**: `start.py` doesn't set PYTHONPATH when uvicorn starts
- **Impact**: Direct uvicorn calls fail with `ModuleNotFoundError: No module named 'pokertool'`
- **Location**: `start.py:547-550` - Missing env setup
- **Evidence**: Manual run with `PYTHONPATH=src` works; standard `start.py` fails
- **Severity**: CRITICAL - Backend won't start from standard process

#### 3. Frontend Configuration (HIGH)
- **Issue**: Frontend hardcoded to expect backend on port 5001, but uses `buildApiUrl()` which may have wrong config
- **Location**: `pokertool-frontend/src/hooks/useSystemHealth.ts:149, 193`
- **Impact**: Frontend can't connect if port changes
- **Severity**: HIGH - Inflexible configuration

#### 4. WebSocket Health Updates (HIGH)
- **Issue**: WebSocket connection at `/ws/system-health` established, but may be throttled by rate limiter too
- **Location**: `src/pokertool/api.py:2347-2417`
- **Impact**: Real-time updates not received by frontend
- **Severity**: HIGH - No live health updates

#### 5. Cache Configuration (MEDIUM)
- **Issue**: Frontend caches health data for 5 minutes - stale data shown when backend offline
- **Location**: `pokertool-frontend/src/hooks/useSystemHealth.ts:63-64`
- **Impact**: Misleading status when backend is down
- **Severity**: MEDIUM - Wrong information displayed

#### 6. Error Messages (MEDIUM)
- **Issue**: Generic rate limit error - no helpful diagnostic info
- **Location**: `src/pokertool/api.py` rate limiter responses
- **Impact**: Users can't debug what's wrong
- **Severity**: MEDIUM - Poor user experience

#### 7. Health Endpoint Dependencies (MEDIUM)
- **Issue**: Health checks may fail if dependencies missing (TensorFlow, etc.)
- **Location**: `src/pokertool/system_health_checker.py`
- **Impact**: Partial health checks failing silently
- **Severity**: MEDIUM - Incomplete health information

#### 8. Connection Status Component (LOW)
- **Issue**: ConnectionStatus component shows "Waiting for backend" but doesn't retry
- **Location**: `pokertool-frontend/src/components/ConnectionStatus.tsx`
- **Impact**: UI doesn't actively reconnect
- **Severity**: LOW - User must manually refresh

#### 9. Backend Logs Not Visible (LOW)
- **Issue**: Uvicorn logs go to stdout/stderr but not easily accessible to frontend
- **Location**: Backend logging infrastructure
- **Impact**: Can't see errors in browser
- **Severity**: LOW - Developer experience

#### 10. Port Documentation (LOW)
- **Issue**: Multiple port assumptions throughout codebase (5001, 3000, 8000)
- **Location**: Multiple files
- **Impact**: Confusion about correct ports
- **Severity**: LOW - Documentation

---

## 20 TODO Tasks to Fix

### Phase 1: Rate Limiting Fix (Tasks 1-3) - CRITICAL

**TODO 1: Reduce Health Endpoint Rate Limit**
- **File**: `src/pokertool/api.py`
- **Change**: Increase health endpoint limit from 60/min to 600/min (10/second)
- **Reason**: Health checks run every 30 seconds, and frontend may poll faster
- **Test**: `tests/test_health_endpoint_rate_limit.py::test_health_endpoint_not_rate_limited`
- **Expected**: Health endpoint can handle 10 consecutive requests

**TODO 2: Exclude Health Endpoint from Global Rate Limit**
- **File**: `src/pokertool/api.py`
- **Change**: Create separate rate limiter for `/api/system/health` (unlimited or very high)
- **Reason**: Health checks are monitoring; should never be rate-limited
- **Test**: `tests/test_health_endpoint_rate_limit.py::test_health_endpoint_excluded_from_limit`
- **Expected**: Unlimited requests to health endpoint

**TODO 3: Rate Limit WebSocket Health Stream Separately**
- **File**: `src/pokertool/api.py`
- **Change**: WebSocket `/ws/system-health` should have its own rate limit (per-connection)
- **Reason**: Live updates should be always available
- **Test**: `tests/test_websocket_health_stream.py::test_websocket_not_rate_limited`
- **Expected**: WebSocket maintains connection under load

### Phase 2: Backend Startup Fix (Tasks 4-6) - CRITICAL

**TODO 4: Fix start.py PYTHONPATH Export**
- **File**: `start.py`
- **Change**: Line 493 - `env['PYTHONPATH'] = str(SRC_DIR)` is set, verify it's used in all subprocess calls
- **Reason**: Uvicorn process needs access to pokertool module
- **Test**: `tests/test_startup.py::test_backend_starts_with_pythonpath`
- **Expected**: Backend starts without ModuleNotFoundError

**TODO 5: Add Backend Startup Validation**
- **File**: `start.py`
- **Change**: After starting backend, validate health endpoint responds with 200 (after rate limit reset)
- **Reason**: Catch startup failures immediately
- **Test**: `tests/test_startup.py::test_backend_health_validates`
- **Expected**: Startup fails with clear error if backend unhealthy

**TODO 6: Create Alternative Backend Startup Script**
- **File**: Create `scripts/start_backend_dev.sh`
- **Change**: Standalone script to start just the backend with proper env
- **Reason**: Easier debugging without full frontend stack
- **Test**: `tests/test_startup.py::test_backend_dev_script`
- **Expected**: Script starts backend successfully on port 5001

### Phase 3: Frontend Configuration Fix (Tasks 7-9) - HIGH

**TODO 7: Make Backend Port Configurable**
- **File**: `pokertool-frontend/src/config/api.ts`
- **Change**: Read backend port from `REACT_APP_BACKEND_PORT` env var (default 5001)
- **Reason**: Support different deployment environments
- **Test**: `tests/frontend/test_api_config.test.ts::test_api_port_configurable`
- **Expected**: Frontend can connect to non-standard port

**TODO 8: Add Backend Port Auto-Detection**
- **File**: `pokertool-frontend/src/hooks/useSystemHealth.ts`
- **Change**: Try ports 5001, 5000, 8000, 3001 in sequence if primary fails
- **Reason**: Fallback if port changes
- **Test**: `tests/frontend/test_port_discovery.test.ts::test_port_auto_detection`
- **Expected**: Frontend finds backend on alternate ports

**TODO 9: Improve Frontend Error Messages**
- **File**: `pokertool-frontend/src/hooks/useSystemHealth.ts`
- **Change**: Line 173 - differentiate between rate limit vs connection error vs other
- **Reason**: Users can't debug connectivity issues
- **Test**: `tests/frontend/test_error_messages.test.ts::test_error_message_clarity`
- **Expected**: Clear error messages for different failure modes

### Phase 4: WebSocket & Real-time Updates (Tasks 10-12) - HIGH

**TODO 10: Fix WebSocket Reconnection Logic**
- **File**: `pokertool-frontend/src/hooks/useSystemHealth.ts`
- **Change**: Line 222 - exponential backoff (10s → 30s → 1min) instead of fixed 10s
- **Reason**: Reduce server load during outages
- **Test**: `tests/frontend/test_websocket_reconnect.test.ts::test_exponential_backoff`
- **Expected**: Reconnection attempts reduce load over time

**TODO 11: Add WebSocket Heartbeat/Ping**
- **File**: `src/pokertool/api.py`
- **Change**: Add periodic ping messages from server to keep connection alive
- **Reason**: Detect dead connections faster
- **Test**: `tests/test_websocket_heartbeat.py::test_ping_pong_mechanism`
- **Expected**: Server sends ping, client responds pong every 30 seconds

**TODO 12: Implement Health Check Retry with Jitter**
- **File**: `pokertool-frontend/src/hooks/useSystemHealth.ts`
- **Change**: Add random jitter to retry timing to prevent thundering herd
- **Reason**: Multiple clients hitting same endpoint simultaneously
- **Test**: `tests/frontend/test_health_retry_jitter.test.ts::test_jitter_distribution`
- **Expected**: Retries distributed randomly over interval

### Phase 5: Cache & Stale Data (Tasks 13-14) - MEDIUM

**TODO 13: Reduce Frontend Cache TTL**
- **File**: `pokertool-frontend/src/hooks/useSystemHealth.ts`
- **Change**: Line 63 - reduce from 5 minutes to 1 minute cache TTL
- **Reason**: Stale data more obvious and helpful
- **Test**: `tests/frontend/test_cache_ttl.test.ts::test_cache_expires_in_one_minute`
- **Expected**: Cache expires after 1 minute

**TODO 14: Add Cache Staleness Indicator**
- **File**: `pokertool-frontend/src/components/SystemHealthMonitor.tsx`
- **Change**: Show "Cached from X minutes ago" warning when using stale data
- **Reason**: Users know data may be outdated
- **Test**: `tests/frontend/test_cache_indicator.test.ts::test_stale_data_warning`
- **Expected**: Warning displayed when cache is used

### Phase 6: Error Handling & Messages (Tasks 15-17) - MEDIUM

**TODO 15: Improve Rate Limit Error Response**
- **File**: `src/pokertool/api.py`
- **Change**: Return helpful message: "Health endpoint rate-limited. Backend is working but too many requests. Check logs."
- **Reason**: Current message doesn't help users
- **Test**: `tests/test_rate_limit_messages.py::test_rate_limit_helpful_message`
- **Expected**: Error message includes helpful diagnostic info

**TODO 16: Add Backend Health Check Logging**
- **File**: `src/pokertool/system_health_checker.py`
- **Change**: Log health check failures with detailed reasons
- **Reason**: Can't debug health issues without logs
- **Test**: `tests/test_health_logging.py::test_health_failures_logged`
- **Expected**: Health check failures logged with details

**TODO 17: Create Health Status Dashboard**
- **File**: Create `pokertool-frontend/src/components/HealthStatusDashboard.tsx`
- **Change**: Show detailed health info: last check time, check duration, failure reasons
- **Reason**: Debug frontend needs detailed health info
- **Test**: `tests/frontend/test_health_dashboard.test.ts::test_dashboard_renders`
- **Expected**: Dashboard shows all health details

### Phase 7: Dependency & Configuration (Tasks 18-20) - MEDIUM/LOW

**TODO 18: Add Optional Dependency Checks**
- **File**: `src/pokertool/system_health_checker.py`
- **Change**: Gracefully handle missing dependencies (TensorFlow, PaddleOCR) without failing
- **Reason**: Health checks shouldn't fail due to optional dependencies
- **Test**: `tests/test_optional_dependencies.py::test_health_works_without_tensorflow`
- **Expected**: Health checks pass even with missing optional deps

**TODO 19: Document Backend Port Configuration**
- **File**: Create `docs/BACKEND_PORT_CONFIG.md`
- **Change**: Explain all port assumptions and how to change them
- **Reason**: Users confused by multiple ports
- **Test**: Manual verification - docs exist and are clear
- **Expected**: Clear documentation on port configuration

**TODO 20: Create Backend Health Monitoring Tests**
- **File**: Create `tests/test_backend_health_complete.py`
- **Change**: Comprehensive test suite verifying health endpoint, WebSocket, rate limiting, error handling
- **Reason**: Prevent regression of these issues
- **Test**: Run complete test suite
- **Expected**: All tests pass, issues fixed

---

## Implementation Order

### Immediately (Critical Path - Day 1)
1. **TODO 1-2**: Fix rate limiting (unblock health endpoint)
2. **TODO 4**: Fix PYTHONPATH in start.py (backend startup)
3. **TODO 5**: Add startup validation

### Short-term (Day 2-3)
4. **TODO 7-9**: Frontend configuration fixes
5. **TODO 10-12**: WebSocket & real-time fixes
6. **TODO 15-16**: Better error messages

### Medium-term (Day 4-5)
7. **TODO 3, 6, 13-14**: Additional improvements
8. **TODO 18-20**: Documentation & comprehensive testing

---

## Success Criteria

- ✅ Health endpoint responds with 200 (not 429)
- ✅ WebSocket connection established and maintained
- ✅ Frontend health monitor shows "healthy" when backend running
- ✅ Frontend shows "offline" within 1-2 seconds of backend shutdown
- ✅ Error messages are clear and actionable
- ✅ All 20 TODO tasks have unit tests
- ✅ All tests passing

---

## Testing Strategy

Each task includes unit tests in format:
```
tests/test_<todo_number>_<description>.py
```

Run all health-related tests:
```bash
pytest tests/test_health* tests/test_startup* tests/test_websocket* tests/test_rate_limit* -v
```

---

## Notes

- Backend is **actually operational** - all services running
- Issue is purely in health **monitoring & communication**
- Rate limiting is the primary blocker
- Frontend needs better error handling & fallback logic
- Documentation needed on port configuration

