# Security Modules Integration Guide

## Overview

This guide provides comprehensive instructions for integrating the PokerTool security infrastructure modules into your FastAPI application. The security modules include CSRF Protection, RBAC (Role-Based Access Control), Correlation ID Middleware, and API Client Library.

**Created**: October 2025
**Version**: 1.0.0
**Modules Covered**:
- CSRF Protection (`src/pokertool/csrf_protection.py`)
- RBAC System (`src/pokertool/rbac.py`)
- Correlation ID Middleware (`src/pokertool/correlation_id_middleware.py`)
- API Client Library (`src/pokertool/api_client.py`)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [CSRF Protection Integration](#csrf-protection-integration)
3. [RBAC System Integration](#rbac-system-integration)
4. [Correlation ID Middleware Integration](#correlation-id-middleware-integration)
5. [API Client Library Usage](#api-client-library-usage)
6. [Complete Integration Example](#complete-integration-example)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Dependencies

```bash
pip install fastapi>=0.104.0
pip install uvicorn>=0.24.0
pip install requests>=2.32.0
pip install pydantic>=2.5.0
```

### Environment Variables

Create a `.env` file with the following variables:

```bash
# CSRF Protection
CSRF_SECRET_KEY=your-secure-random-key-min-32-chars

# API Configuration
API_BASE_URL=http://localhost:5001
API_SECRET_KEY=your-api-secret-key

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## CSRF Protection Integration

### Basic Setup

```python
from fastapi import FastAPI
from pokertool.csrf_protection import (
    CSRFProtection,
    CSRFMiddleware,
    create_csrf_protection
)
import os

app = FastAPI()

# Initialize CSRF protection
csrf_secret = os.getenv("CSRF_SECRET_KEY", "default-secret-key-change-in-production")
csrf_protection = create_csrf_protection(secret_key=csrf_secret)

# Add CSRF middleware
app.add_middleware(
    CSRFMiddleware,
    csrf_protection=csrf_protection,
    exempt_paths=[
        "/docs",           # Swagger UI
        "/redoc",          # ReDoc
        "/openapi.json",   # OpenAPI schema
        "/health",         # Health check
        "/auth/login"      # Public auth endpoint
    ]
)
```

### Frontend Integration

#### Getting CSRF Token

```typescript
// React Hook for CSRF Token
import { useState, useEffect } from 'react';

export function useCSRFToken() {
  const [csrfToken, setCSRFToken] = useState<string | null>(null);

  useEffect(() => {
    // Get token from cookie
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];

    if (token) {
      setCSRFToken(token);
    }
  }, []);

  return csrfToken;
}
```

#### Making Protected Requests

```typescript
// Example: POST request with CSRF token
async function submitForm(data: any) {
  const csrfToken = getCookie('csrf_token');

  const response = await fetch('/api/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken
    },
    credentials: 'include',  // Include cookies
    body: JSON.stringify(data)
  });

  return response.json();
}

function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
}
```

### Custom Configuration

```python
from pokertool.csrf_protection import CSRFProtection, CSRFMiddleware

# Advanced configuration
csrf_protection = CSRFProtection(
    secret_key=os.getenv("CSRF_SECRET_KEY"),
    token_name="csrf_token",           # Form field name
    header_name="X-CSRF-Token",        # HTTP header name
    cookie_name="csrf_token",          # Cookie name
    cookie_secure=True,                # HTTPS only (set False for dev)
    cookie_httponly=False,             # Allow JS access
    cookie_samesite="Strict",          # CSRF protection
    token_expiry=3600                  # 1 hour expiration
)

app.add_middleware(
    CSRFMiddleware,
    csrf_protection=csrf_protection,
    exempt_paths=["/api/public/*"]
)
```

---

## RBAC System Integration

### Basic Setup

```python
from fastapi import FastAPI, Depends, HTTPException
from pokertool.rbac import (
    Permission,
    Role,
    RBACSystem,
    get_rbac_system,
    require_permission,
    require_role
)

app = FastAPI()

# Initialize RBAC system (singleton)
rbac = get_rbac_system()

# Assign roles to users (typically done during user creation/management)
rbac.assign_role("user_123", Role.USER)
rbac.assign_role("admin_456", Role.ADMIN)
rbac.assign_role("analyst_789", Role.ANALYST)
```

### Protecting Routes with Permissions

```python
from fastapi import Request

@app.get("/api/analyze")
async def analyze_hand(
    request: Request,
    _: None = Depends(require_permission(Permission.ANALYZE_HAND))
):
    """
    This endpoint requires ANALYZE_HAND permission.

    The permission check happens in the dependency:
    - Extracts user_id from request.state.user_id
    - Checks if user has required permission
    - Raises 403 if permission denied
    """
    return {"message": "Hand analysis result"}

@app.post("/api/admin/users")
async def create_user(
    request: Request,
    _: None = Depends(require_role(Role.ADMIN))
):
    """
    This endpoint requires ADMIN role.
    """
    return {"message": "User created"}
```

### Setting User Context in Middleware

```python
from fastapi import Request
import jwt

@app.middleware("http")
async def authenticate_user(request: Request, call_next):
    """Extract user ID from JWT token and set in request state."""

    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                os.getenv("API_SECRET_KEY"),
                algorithms=["HS256"]
            )

            # Set user_id in request state for RBAC checks
            request.state.user_id = payload.get("user_id")

        except jwt.InvalidTokenError:
            request.state.user_id = None

    response = await call_next(request)
    return response
```

### Custom Roles and Permissions

```python
from pokertool.rbac import Permission, RBACSystem

rbac = get_rbac_system()

# Define custom permission
Permission.EXPORT_DATA = "export:data"

# Define custom role with specific permissions
rbac.define_role(
    role="premium_user",
    description="Premium subscription user",
    permissions={
        Permission.ANALYZE_HAND,
        Permission.VIEW_ANALYSIS,
        Permission.USE_GTO_SOLVER,
        Permission.EXPORT_DATA
    },
    inherits_from=[Role.USER]
)

# Assign custom role to user
rbac.assign_role("user_999", "premium_user")
```

### Function Decorators

```python
from pokertool.rbac import requires_permission, Permission

@requires_permission(Permission.ANALYZE_HAND)
def analyze_poker_hand(user_id: str, hand_data: dict):
    """
    This function requires ANALYZE_HAND permission.

    Note: user_id must be first positional arg or keyword arg.
    """
    # Perform hand analysis
    return {"result": "analysis data"}

# Usage
try:
    result = analyze_poker_hand(
        user_id="user_123",
        hand_data={"cards": ["As", "Kh"]}
    )
except PermissionError as e:
    print(f"Access denied: {e}")
```

---

## Correlation ID Middleware Integration

### Basic Setup

```python
from fastapi import FastAPI
from pokertool.correlation_id_middleware import (
    CorrelationIdMiddleware,
    get_correlation_id,
    CorrelationIdFilter
)
import logging

app = FastAPI()

# Add correlation ID middleware
app.add_middleware(
    CorrelationIdMiddleware,
    header_name="X-Correlation-ID"
)

# Configure logging with correlation ID filter
logger = logging.getLogger()
logger.addFilter(CorrelationIdFilter())

# Configure log format to include correlation ID
logging.basicConfig(
    format='%(asctime)s - %(correlation_id)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

### Using Correlation IDs in Routes

```python
from pokertool.correlation_id_middleware import get_correlation_id

@app.get("/api/process")
async def process_request():
    # Get current correlation ID
    corr_id = get_correlation_id()

    logger.info(f"Processing request with correlation ID: {corr_id}")

    # Correlation ID is automatically included in logs via filter
    logger.info("Processing data...")

    return {
        "correlation_id": corr_id,
        "result": "success"
    }
```

### Propagating to External Services

```python
from pokertool.correlation_id_middleware import CorrelationIdPropagator
import httpx

@app.get("/api/external")
async def call_external_service():
    # Automatically includes correlation ID in headers
    headers = CorrelationIdPropagator.get_headers({
        "Authorization": "Bearer token"
    })

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://external-api.com/data",
            headers=headers
        )

    return response.json()

# Alternative: Using helper method
@app.get("/api/external2")
async def call_external_service_helper():
    async with httpx.AsyncClient() as client:
        response = await CorrelationIdPropagator.call_service(
            client.get,
            "https://external-api.com/data"
        )

    return response.json()
```

### Database Query Tracing

```python
from pokertool.correlation_id_middleware import DatabaseQueryTracer

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    # Trace database query with correlation ID
    query_metadata = DatabaseQueryTracer.trace_query(
        query="SELECT * FROM users WHERE id = :id",
        params={"id": user_id}
    )

    logger.info(f"Executing query: {query_metadata}")

    # Execute actual query...
    return {"user_id": user_id}
```

---

## API Client Library Usage

### Basic Client Usage

```python
from pokertool.api_client import PokerToolClient

# Initialize client with API key
client = PokerToolClient(
    base_url="http://localhost:5001",
    api_key="your-api-key-here",
    timeout=30,
    max_retries=3
)

# Check API health
health = client.get_health()
print(f"API Status: {health}")

# Analyze a hand
result = client.analyze_hand(
    hole_cards=["As", "Kh"],
    community_cards=["Qh", "Jd", "Tc"],
    pot_size=100.0,
    stack_size=1000.0,
    position="button",
    num_players=6,
    street="flop"
)

print(f"Recommendation: {result.recommendation}")
print(f"Confidence: {result.confidence}")
print(f"Equity: {result.equity}")
```

### Context Manager Usage

```python
from pokertool.api_client import PokerToolClient

# Automatic session cleanup
with PokerToolClient(base_url="http://localhost:5001", api_key="key") as client:
    # Get statistics
    stats = client.get_statistics(user_id="user_123")

    # Get hand history
    history = client.get_hand_history(limit=50, offset=0)

    print(f"Total hands: {len(history.get('hands', []))}")
# Session automatically closed here
```

### Authentication with JWT

```python
from pokertool.api_client import PokerToolClient

# Initialize with username/password
client = PokerToolClient(
    base_url="http://localhost:5001",
    username="testuser",
    password="securepassword"
)

# Authenticate and get JWT tokens
client.authenticate()

# Now make authenticated requests
result = client.analyze_hand(...)
```

### Error Handling

```python
from pokertool.api_client import (
    PokerToolClient,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

client = PokerToolClient(base_url="http://localhost:5001", api_key="key")

try:
    result = client.analyze_hand(...)

except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    print(f"Status code: {e.status_code}")

except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement backoff strategy

except ValidationError as e:
    print(f"Invalid input: {e}")
    print(f"Details: {e.response_data}")

except APIError as e:
    print(f"API error: {e}")
    print(f"Status: {e.status_code}")
```

---

## Complete Integration Example

Here's a complete example showing all modules working together:

```python
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import jwt
import logging

from pokertool.csrf_protection import CSRFProtection, CSRFMiddleware
from pokertool.rbac import (
    Role, Permission, RBACSystem, get_rbac_system,
    require_permission, require_role
)
from pokertool.correlation_id_middleware import (
    CorrelationIdMiddleware,
    get_correlation_id,
    CorrelationIdFilter
)

# Initialize FastAPI app
app = FastAPI(title="PokerTool Secure API")

# Configure logging
logger = logging.getLogger(__name__)
logger.addFilter(CorrelationIdFilter())
logging.basicConfig(
    format='%(asctime)s - %(correlation_id)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize security systems
rbac = get_rbac_system()
csrf_protection = CSRFProtection(
    secret_key=os.getenv("CSRF_SECRET_KEY", "change-me-in-production")
)

# Add middleware (order matters!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    CorrelationIdMiddleware,
    header_name="X-Correlation-ID"
)

app.add_middleware(
    CSRFMiddleware,
    csrf_protection=csrf_protection,
    exempt_paths=["/docs", "/redoc", "/openapi.json", "/health", "/auth/login"]
)

# Authentication middleware
@app.middleware("http")
async def authenticate_user(request: Request, call_next):
    """Extract user ID from JWT and set in request state."""
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                os.getenv("API_SECRET_KEY"),
                algorithms=["HS256"]
            )
            request.state.user_id = payload.get("user_id")
            logger.info(f"Authenticated user: {request.state.user_id}")
        except jwt.InvalidTokenError:
            request.state.user_id = None
            logger.warning("Invalid JWT token")

    response = await call_next(request)
    return response

# Public endpoints
@app.get("/health")
async def health_check():
    """Public health check endpoint."""
    corr_id = get_correlation_id()
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "correlation_id": corr_id
    }

@app.post("/auth/login")
async def login(username: str, password: str):
    """Public login endpoint (CSRF exempt)."""
    # Verify credentials (simplified)
    if username == "admin" and password == "admin123":
        user_id = "admin_001"

        # Assign role
        rbac.assign_role(user_id, Role.ADMIN)

        # Generate JWT
        token = jwt.encode(
            {"user_id": user_id},
            os.getenv("API_SECRET_KEY"),
            algorithm="HS256"
        )

        logger.info(f"User {username} logged in successfully")
        return {"access_token": token, "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="Invalid credentials")

# Protected endpoints with RBAC
@app.post("/api/analyze")
async def analyze_hand(
    request: Request,
    hand_data: dict,
    _: None = Depends(require_permission(Permission.ANALYZE_HAND))
):
    """
    Analyze poker hand.

    Requires: ANALYZE_HAND permission
    Protected by: CSRF middleware
    """
    user_id = request.state.user_id
    corr_id = get_correlation_id()

    logger.info(f"User {user_id} analyzing hand")

    # Perform analysis...
    return {
        "recommendation": "raise",
        "confidence": 0.85,
        "correlation_id": corr_id
    }

@app.get("/api/admin/users")
async def list_users(
    request: Request,
    _: None = Depends(require_role(Role.ADMIN))
):
    """
    List all users.

    Requires: ADMIN role
    """
    logger.info("Admin listing all users")

    # Fetch users...
    return {"users": ["user1", "user2", "user3"]}

@app.post("/api/export")
async def export_data(
    request: Request,
    _: None = Depends(require_permission(Permission.EXPORT_ANALYTICS))
):
    """
    Export analytics data.

    Requires: EXPORT_ANALYTICS permission
    Protected by: CSRF middleware
    """
    user_id = request.state.user_id
    logger.info(f"User {user_id} exporting data")

    # Generate export...
    return {"export_url": "/downloads/export_123.csv"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
```

---

## Best Practices

### 1. CSRF Protection

- **Always use HTTPS in production** to prevent token interception
- **Set appropriate exempt paths** for public endpoints (health checks, docs)
- **Configure cookie security** appropriately for your environment
- **Handle token expiration** gracefully in frontend
- **Test with actual browsers** to ensure cookie behavior works correctly

### 2. RBAC System

- **Use principle of least privilege** - assign minimum required permissions
- **Create role hierarchy** to reduce permission duplication
- **Audit permission changes** in production
- **Don't hardcode user IDs** - always get from authenticated context
- **Test permission boundaries** thoroughly

### 3. Correlation IDs

- **Always add correlation ID filter** to your logging configuration
- **Propagate IDs to external services** for distributed tracing
- **Include correlation IDs in error responses** for debugging
- **Use consistent header names** across all services
- **Log correlation IDs at service boundaries**

### 4. API Client

- **Use context managers** for automatic cleanup
- **Implement proper error handling** for all API calls
- **Configure appropriate timeouts** based on endpoint characteristics
- **Use retry logic wisely** - some operations shouldn't be retried
- **Cache client instances** when making multiple calls

---

## Troubleshooting

### CSRF Protection Issues

**Problem**: CSRF token missing error
**Solution**: Ensure cookies are enabled and `credentials: 'include'` is set in fetch requests

**Problem**: Token mismatch error
**Solution**: Verify the same token is sent in both cookie and header

**Problem**: Token expired
**Solution**: Implement token refresh logic in frontend

### RBAC Issues

**Problem**: 403 Forbidden despite having correct role
**Solution**: Verify `request.state.user_id` is set correctly in authentication middleware

**Problem**: Permissions not inherited
**Solution**: Check role definition includes correct `inherits_from` parameter

### Correlation ID Issues

**Problem**: Correlation ID is "N/A" in logs
**Solution**: Ensure `CorrelationIdFilter` is added to logger before making requests

**Problem**: IDs not propagating to external services
**Solution**: Use `CorrelationIdPropagator.get_headers()` or `call_service()` methods

### API Client Issues

**Problem**: Connection timeout
**Solution**: Increase `timeout` parameter or check network connectivity

**Problem**: Too many retries
**Solution**: Reduce `max_retries` or implement circuit breaker pattern

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangzhou.com/)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [RBAC Best Practices](https://en.wikipedia.org/wiki/Role-based_access_control)
- [Distributed Tracing with Correlation IDs](https://www.w3.org/TR/trace-context/)

---

## Support

For issues or questions:
1. Check the test files for usage examples
2. Review module docstrings for detailed API documentation
3. Open an issue on GitHub with correlation ID and error details

---

**Document Version**: 1.0.0
**Last Updated**: October 2025
**Maintained By**: PokerTool Development Team
