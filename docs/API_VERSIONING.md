# PokerTool API Versioning Strategy
> Issue Register: Use `python new_task.py` to append GUID-tagged entries to `docs/TODO.md`; manual edits are rejected and historical backlog lives in `docs/TODO_ARCHIVE.md`.

## Overview

This document defines the versioning strategy for the PokerTool REST API to ensure backward compatibility, smooth migrations, and clear communication of breaking changes.

**Current API Version:** v1
**Last Updated:** October 2025
**Status:** Active Development

---

## Table of Contents

- [Versioning Scheme](#versioning-scheme)
- [Implementation Approach](#implementation-approach)
- [Version Lifecycle](#version-lifecycle)
- [Breaking Changes Policy](#breaking-changes-policy)
- [Migration Guide](#migration-guide)
- [Best Practices](#best-practices)

---

## Versioning Scheme

### Semantic Versioning

PokerTool API follows **Semantic Versioning 2.0.0** (semver.org):

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

**Examples:**
- `v1.0.0` → Initial stable release
- `v1.1.0` → Added new endpoints, backward compatible
- `v1.1.1` → Bug fixes only
- `v2.0.0` → Breaking changes, new major version

### URL-based Versioning

API version is specified in the URL path:

```
https://api.pokertool.app/v1/analyze
https://api.pokertool.app/v2/analyze
```

**Rationale:**
- **Clear and explicit**: Version is immediately visible in the URL
- **Easy routing**: Simple to route requests to different handlers
- **Caching friendly**: CDNs and proxies can cache by version
- **Client clarity**: Developers know exactly which version they're using

---

## Implementation Approach

### Directory Structure

```
src/pokertool/
├── api.py                      # Main API factory and core logic
├── api_v1/
│   ├── __init__.py
│   ├── router.py               # V1 route definitions
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── analysis.py         # /v1/analyze
│   │   ├── auth.py             # /v1/auth/*
│   │   ├── database.py         # /v1/database/*
│   │   ├── scraper.py          # /v1/scraper/*
│   │   └── system.py           # /v1/system/*
│   ├── models.py               # V1 Pydantic models
│   └── dependencies.py         # V1 dependencies
├── api_v2/                     # Future: V2 API (when needed)
│   ├── __init__.py
│   ├── router.py
│   └── ...
└── api_common/                 # Shared utilities across versions
    ├── __init__.py
    ├── middleware.py
    ├── security.py
    └── utils.py
```

### FastAPI Router Implementation

**File: `src/pokertool/api_v1/router.py`**

```python
from fastapi import APIRouter
from .endpoints import analysis, auth, database, scraper, system

# Create V1 router with prefix
router_v1 = APIRouter(
    prefix="/v1",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

# Include sub-routers
router_v1.include_router(
    analysis.router,
    prefix="/analysis",
    tags=["analysis"]
)
router_v1.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)
router_v1.include_router(
    database.router,
    prefix="/database",
    tags=["database"]
)
router_v1.include_router(
    scraper.router,
    prefix="/scraper",
    tags=["scraper"]
)
router_v1.include_router(
    system.router,
    prefix="/system",
    tags=["system"]
)
```

**File: `src/pokertool/api.py` (Updated)**

```python
from fastapi import FastAPI
from api_v1.router import router_v1
# from api_v2.router import router_v2  # Future

def create_app():
    app = FastAPI(
        title="PokerTool API",
        description="Professional poker analysis and automation API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Include versioned routers
    app.include_router(router_v1)
    # app.include_router(router_v2)  # Future

    # Root endpoint - API information
    @app.get("/")
    async def root():
        return {
            "name": "PokerTool API",
            "version": "1.0.0",
            "available_versions": ["v1"],
            "docs": "/docs",
            "health": "/v1/health"
        }

    # Version negotiation (future)
    @app.get("/version")
    async def get_version_info():
        return {
            "current": "v1",
            "supported": ["v1"],
            "deprecated": [],
            "sunset_dates": {}
        }

    return app
```

### Header-based Version Negotiation (Optional)

For clients that prefer headers over URL paths:

```python
from fastapi import Header, HTTPException

async def get_api_version(
    accept_version: str = Header(default="v1", alias="Accept-Version")
) -> str:
    """
    Extract API version from Accept-Version header.
    Defaults to v1 if not specified.
    """
    supported_versions = ["v1"]

    if accept_version not in supported_versions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported API version: {accept_version}. Supported: {supported_versions}"
        )

    return accept_version
```

---

## Version Lifecycle

### Stages

1. **Development** → Active development, frequent changes
2. **Beta** → Feature complete, testing phase
3. **Stable** → Production-ready, recommended for all users
4. **Deprecated** → Replaced by newer version, will be removed
5. **Sunset** → No longer supported, removed

### Lifecycle Timeline

```
Development (0-3 months)
    ↓
Beta (1-2 months)
    ↓
Stable (12+ months)
    ↓
Deprecated (6 months notice)
    ↓
Sunset (3 months after deprecation)
```

### Version Support Policy

- **Current version (v1)**: Full support, all features
- **Previous version (v0)**: Security fixes only (if exists)
- **Deprecated versions**: No updates, 6-month sunset period

**Communication:**
- Deprecation announcements via:
  - API response headers (`X-API-Deprecated: true`)
  - Changelog (`CHANGELOG.md`)
  - Documentation updates
  - Email notifications to registered API users

---

## Breaking Changes Policy

### What Constitutes a Breaking Change?

**Breaking changes require a new MAJOR version:**

1. **Removing endpoints** or routes
2. **Renaming fields** in request/response models
3. **Changing field types** (e.g., string → int)
4. **Making optional fields required**
5. **Removing fields** from responses
6. **Changing authentication mechanisms**
7. **Modifying error response formats**
8. **Changing URL structures**

**Non-breaking changes (MINOR/PATCH versions):**

1. **Adding new endpoints**
2. **Adding optional fields** to requests
3. **Adding fields** to responses
4. **Fixing bugs** that don't change contracts
5. **Performance improvements**
6. **Documentation updates**

### Breaking Change Checklist

Before introducing breaking changes:

- [ ] Document the change in `CHANGELOG.md`
- [ ] Update API documentation
- [ ] Create migration guide for clients
- [ ] Announce deprecation at least 6 months in advance
- [ ] Provide side-by-side comparison (old vs new)
- [ ] Test backward compatibility extensively
- [ ] Update client SDKs (if any)
- [ ] Notify all registered API users

---

## Migration Guide

### Upgrading from v1 to v2 (Future)

When v2 is released, this section will contain:

1. **Key Differences**: What changed between v1 and v2
2. **Step-by-Step Migration**: How to update your code
3. **Code Examples**: Before and after comparisons
4. **Common Pitfalls**: What to watch out for
5. **Testing**: How to validate your migration

**Example Migration (Hypothetical):**

```python
# V1 (Old)
POST /v1/analyze
{
    "hand": "AsKh",
    "board": "AdKcQh"
}

# V2 (New)
POST /v2/analysis/hand
{
    "hole_cards": ["As", "Kh"],
    "community_cards": ["Ad", "Kc", "Qh"],
    "context": {
        "position": "BTN",
        "pot_size": 100
    }
}
```

### Parallel Running (Transition Period)

During transition periods, both v1 and v2 will be available:

```python
# Both versions accessible simultaneously
https://api.pokertool.app/v1/analyze  # Deprecated but functional
https://api.pokertool.app/v2/analysis/hand  # New, recommended
```

**Transition Timeline:**
- **Month 0**: v2 released (beta)
- **Month 1-2**: v2 stabilizes
- **Month 3**: v1 marked deprecated
- **Month 9**: v1 sunset (removal)

---

## Best Practices

### For API Maintainers

1. **Never break existing contracts** within the same major version
2. **Add new features** via new endpoints or optional fields
3. **Deprecate gracefully** with long notice periods
4. **Version all responses** with `X-API-Version` header
5. **Monitor usage** of deprecated endpoints
6. **Maintain comprehensive docs** for all versions
7. **Test backward compatibility** in CI/CD
8. **Version data models separately** from API routes

### For API Consumers

1. **Always specify version** in URL path
2. **Pin to a specific version** in production
3. **Subscribe to changelog** for updates
4. **Test against beta versions** before they go stable
5. **Prepare for deprecations** during transition periods
6. **Handle version errors** gracefully
7. **Use version negotiation headers** if available
8. **Monitor deprecation warnings** in responses

### Response Headers

All API responses should include version information:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: v1
X-API-Deprecated: false
X-API-Sunset-Date: null
```

For deprecated versions:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: v1
X-API-Deprecated: true
X-API-Deprecation-Date: 2026-01-01
X-API-Sunset-Date: 2026-07-01
Link: </v2/docs>; rel="successor-version"
```

---

## Version Documentation

### OpenAPI/Swagger Support

Each version maintains its own OpenAPI specification:

```
/v1/docs          # Swagger UI for v1
/v2/docs          # Swagger UI for v2
/docs             # Latest version (redirect)
```

**Implementation:**

```python
app_v1 = FastAPI(
    title="PokerTool API v1",
    version="1.0.0",
    openapi_url="/v1/openapi.json",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc"
)

app_v2 = FastAPI(
    title="PokerTool API v2",
    version="2.0.0",
    openapi_url="/v2/openapi.json",
    docs_url="/v2/docs",
    redoc_url="/v2/redoc"
)
```

---

## Changelog

### v1.0.0 (Current)

**Released:** October 2025

**Endpoints:**
- `GET /v1/health` - Health check
- `POST /v1/analyze` - Hand analysis
- `POST /v1/auth/login` - Authentication
- `POST /v1/auth/refresh` - Token refresh
- `GET /v1/database/stats` - Database statistics
- `GET /v1/scraper/status` - Scraper status
- `POST /v1/scraper/start` - Start scraper
- `POST /v1/scraper/stop` - Stop scraper

**Features:**
- JWT authentication
- Rate limiting
- Input validation
- WebSocket support
- CORS configuration

---

## Future Considerations

### Content Negotiation

Future versions may support content negotiation via `Accept` header:

```http
Accept: application/vnd.pokertool.v1+json
Accept: application/vnd.pokertool.v2+json
```

### GraphQL Alternative

Consider GraphQL for flexible versioning:
- Schema evolution without versioning
- Deprecate fields instead of endpoints
- Client-specified response shape

### API Gateway

For production deployments:
- Use API gateway (Kong, Tyk, AWS API Gateway)
- Centralized version routing
- Traffic management
- Analytics and monitoring

---

## Resources

- [Semantic Versioning 2.0.0](https://semver.org/)
- [API Versioning Best Practices](https://swagger.io/blog/api-strategy/api-versioning-best-practices/)
- [FastAPI Versioning](https://fastapi.tiangolo.com/advanced/sub-applications/)
- [RFC 7231 - HTTP Semantics](https://tools.ietf.org/html/rfc7231)

---

## Contact

For questions about API versioning:
- **GitHub Issues**: [github.com/pokertool/pokertool/issues](https://github.com/pokertool/pokertool/issues)
- **Documentation**: [docs.pokertool.app](https://docs.pokertool.app)
- **Changelog**: `CHANGELOG.md`

---

*Last Updated: October 2025 (v86.5.0)*
