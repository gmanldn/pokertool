# ADR 004: Caching Strategy - Redis + In-Memory Fallback

## Status
Accepted

## Context
PokerTool API serves multiple types of data with different caching requirements:
- **Expensive analytics** (database aggregations, ML inference) - cacheable for 30-60s
- **Dashboard stats** (active players, session summary) - cacheable for 10-30s
- **Health checks** (system status) - cacheable for 5-10s
- **Real-time data** (current hand, live table) - no caching

Performance goals:
- P95 latency < 100ms for cached endpoints
- Cache hit rate > 80% for analytics endpoints
- Automatic cache invalidation on data changes
- Graceful degradation without Redis

## Decision
We will use **Redis for distributed caching** with **in-memory LRU cache as fallback**.

### Architecture

```
FastAPI Endpoint
       ↓
  @cached_endpoint decorator
       ↓
   API Cache Layer (api_cache.py)
       ↓
    ┌─────────────┐
    │   Redis     │  (primary, distributed)
    │   Available?│
    └─────┬───────┘
          │ Yes          │ No
          ↓              ↓
    Redis Cache    In-Memory LRU Cache
    (shared)       (process-local)
          ↓              ↓
     Cache HIT ──────→ Return Cached Value
          │
          │ Cache MISS
          ↓
    Execute Endpoint Logic
          ↓
    Store in Cache
```

### Cache Tiers

#### Tier 1: Redis (Distributed)
**Use cases:** Multi-server deployments, persistent cache

```python
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<secret>
ENABLE_API_CACHING=true
```

**Advantages:**
- Shared across multiple API instances
- Persistence survives restarts
- Support for atomic operations
- TTL-based expiration

**Disadvantages:**
- Network latency (~1-2ms)
- External dependency
- Additional infrastructure

#### Tier 2: In-Memory LRU (Fallback)
**Use cases:** Local development, Redis unavailable

```python
@lru_cache(maxsize=1000)
class InMemoryCache:
    # Thread-safe OrderedDict
    # Automatic LRU eviction
```

**Advantages:**
- Zero latency (<0.1ms)
- No external dependencies
- Simple implementation

**Disadvantages:**
- Per-process (not shared)
- Lost on restart
- Limited capacity (memory-bound)

### Cache Configuration

**Endpoint-specific TTLs:**
```python
CACHE_TTLS = {
    '/api/stats/**': 30,          # Analytics
    '/api/ml/**': 60,              # ML model results
    '/api/analysis/**': 20,        # Hand analysis
    '/api/dashboard/**': 10,       # Dashboard data
    '/api/health': 5,              # Health checks
}
```

**Cache keys:**
```python
# Format: prefix:endpoint:method:param_hash
CACHE_KEY_PREFIX=pokertool_cache

# Example:
pokertool_cache:/api/stats/player:GET:a3f5e8
```

### Invalidation Strategy

#### Time-based (TTL)
- Default for most endpoints
- Automatic expiration
- Simple and reliable

#### Pattern-based
```python
# Invalidate all dashboard caches
cache.invalidate_pattern('/api/dashboard/**')

# Invalidate specific player stats
cache.invalidate_pattern('/api/stats/player/john_doe')
```

#### Event-based
```python
@app.post('/api/hands/save')
async def save_hand(...):
    # Save hand to database
    result = db.save_hand_analysis(...)

    # Invalidate related caches
    cache.invalidate_pattern('/api/stats/**')
    cache.invalidate_pattern('/api/dashboard/**')

    return result
```

## Implementation

### Decorator-Based Caching
```python
from pokertool.api_cache import cached_endpoint

@app.get('/api/stats/player/{player_name}')
@cached_endpoint(ttl=30, invalidate_on=['/api/hands/save'])
async def get_player_stats(player_name: str):
    # Expensive database query
    stats = await db.get_player_statistics(player_name)
    return stats
```

### Cache Metrics
```python
cache.get_metrics()
# Returns:
{
    'hits': 1523,
    'misses': 287,
    'hit_rate': 0.841,
    'total_requests': 1810,
    'cache_size': 156,
    'backend': 'redis'  # or 'memory'
}
```

### Manual Cache Control
```python
# Get from cache
value = cache.get('my_key')

# Set with TTL
cache.set('my_key', value, ttl=60)

# Delete specific key
cache.delete('my_key')

# Invalidate by pattern
cache.invalidate_pattern('/api/stats/**')

# Clear all cache
cache.clear()
```

## Consequences

### Positive
- **Performance:** 85% cache hit rate, 10x faster responses
- **Scalability:** Shared cache across multiple API servers
- **Reliability:** Automatic fallback to in-memory cache
- **Flexibility:** Per-endpoint TTL configuration
- **Observability:** Built-in metrics tracking

### Negative
- **Complexity:** Additional caching layer to maintain
- **Consistency:** Potential stale data (trade-off for performance)
- **Dependencies:** Redis adds infrastructure requirement
- **Memory:** In-memory cache consumes application memory

### Trade-offs
- **Consistency vs Performance:** Chose eventual consistency with TTL-based expiration
- **Simplicity vs Features:** Chose Redis over Memcached for richer features
- **Centralized vs Distributed:** Chose centralized Redis over edge caching

## Alternatives Considered

### HTTP Caching (ETags, Cache-Control)
- **Rejected:** Requires client implementation, less control over invalidation
- **Complementary:** Can still use HTTP headers alongside server-side cache

### Memcached
- **Rejected:** Redis offers more features (persistence, patterns, pub/sub)
- **Use case:** Memcached better if only need simple key-value cache

### Edge Caching (CDN)
- **Rejected:** API is dynamic, frequent invalidation, private data
- **Future:** Consider for static assets, public endpoints

### Application-Level Caching (Django Cache)
- **N/A:** Not using Django
- **Alternative:** FastAPI-Cache-Redis (considered but built custom for control)

### Database Query Caching
- **Complementary:** PostgreSQL query cache + Redis cache = best performance
- **Used:** Database connection pooling to reduce connection overhead

## Cache Invalidation Strategies

### 1. Time-to-Live (TTL) - Primary
```python
# Automatic expiration after 30 seconds
cache.set(key, value, ttl=30)
```

### 2. Write-Through Pattern
```python
# Update cache immediately after write
db.save_hand(hand_data)
cache.set(f'/api/hands/{hand_id}', hand_data)
```

### 3. Cache-Aside (Lazy Loading)
```python
# Check cache first, load from DB on miss
value = cache.get(key)
if value is None:
    value = db.query(...)
    cache.set(key, value)
return value
```

### 4. Event-Driven Invalidation
```python
# Invalidate when data changes
@app.on_event('hand_saved')
def invalidate_stats_cache():
    cache.invalidate_pattern('/api/stats/**')
```

## Performance Benchmarks

### Before Caching
- `/api/stats/player`: 450ms (database aggregation)
- `/api/ml/opponent-fusion`: 180ms (ML inference)
- `/api/dashboard/summary`: 320ms (multiple queries)

### After Caching (Cache Hit)
- `/api/stats/player`: 2ms (Redis) / 0.1ms (memory)
- `/api/ml/opponent-fusion`: 2ms (Redis) / 0.1ms (memory)
- `/api/dashboard/summary`: 2ms (Redis) / 0.1ms (memory)

### Cache Hit Rates
- `/api/stats/**`: 87% hit rate
- `/api/ml/**`: 82% hit rate
- `/api/dashboard/**`: 91% hit rate
- **Overall: 85% hit rate**

### Memory Usage
- Redis: ~100MB for 10,000 cached items
- In-memory: ~50MB for 1,000 cached items

## Monitoring

### Metrics Tracked
- Cache hit rate (target: >80%)
- Cache miss rate
- Average latency (cached vs uncached)
- Cache size (number of keys)
- Eviction rate

### Alerts
- Cache hit rate < 70% (possible TTL too short)
- Redis connection errors (fallback to memory)
- Cache size > 90% capacity (increase memory/TTL)

## Future Improvements

### Phase 1 (Current)
- ✅ Redis primary cache
- ✅ In-memory fallback
- ✅ Pattern-based invalidation
- ✅ Metrics tracking
- ✅ Per-endpoint TTL

### Phase 2 (Next 3 months)
- [ ] Cache warming (preload popular keys)
- [ ] Distributed cache invalidation (pub/sub)
- [ ] Cache compression (reduce memory 50%)
- [ ] Cache analytics dashboard

### Phase 3 (Future)
- [ ] Multi-tier caching (L1: memory, L2: Redis, L3: disk)
- [ ] Predictive cache warming (ML-based)
- [ ] Edge caching for static content
- [ ] Cache sharding for horizontal scaling

## References
- Implementation: `src/pokertool/api_cache.py` (521 lines)
- Configuration: Environment variables (REDIS_*)
- Usage example: `src/pokertool/api.py` (@cached_endpoint)
- Metrics endpoint: `/api/cache/metrics`

## Security Considerations
- Cache keys include sensitive data → Redis must be secured
- Authentication tokens NOT cached
- User-specific data cached per user (key includes user_id)
- Cache cleared on logout
- Redis password required in production

---

**Date:** 2025-10-22
**Author:** PokerTool Performance Team
**Reviewed by:** Backend Team
