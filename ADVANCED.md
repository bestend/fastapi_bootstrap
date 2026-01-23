# Advanced Features

This document covers advanced FastAPI Bootstrap features for production deployments.

---

## Table of Contents

- [Security Headers](#security-headers)
- [Middleware](#middleware)
- [Authentication](#authentication)
- [Metrics](#metrics)
- [CORS Configuration](#cors-configuration)
- [Health Checks](#health-checks)
- [Complete API Reference](#complete-api-reference)

---

## Security Headers

### SecurityHeadersMiddleware

Add comprehensive security headers to all responses.

```python
from fastapi_bootstrap import create_app, SecurityHeadersMiddleware

app = create_app([router], title="My API")
app.add_middleware(SecurityHeadersMiddleware)
```

**Headers Added:**

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS connections |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Content-Security-Policy` | `default-src 'self'` | Restrict resource loading |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer information |

### Custom Security Headers

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Custom-Header"] = "value"
        return response

app.add_middleware(CustomSecurityMiddleware)
```

---

## Middleware

### Request ID Middleware

Automatically add unique request IDs to all requests for tracing.

```python
from fastapi_bootstrap import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
```

**Features:**
- Accepts existing `X-Request-ID` header if present
- Generates UUID if not provided
- Adds to response headers for client tracking
- Available in logs via `trace_id`

**Usage:**

```python
from fastapi import Request

@router.get("/test")
async def test(request: Request):
    request_id = request.headers.get("X-Request-ID")
    return {"request_id": request_id}
```

### Request Timing Middleware

Measure and expose request processing time.

```python
from fastapi_bootstrap import RequestTimingMiddleware

app.add_middleware(RequestTimingMiddleware)
```

**Features:**
- Adds `X-Process-Time` header with milliseconds
- High-precision timing using `time.perf_counter()`
- Useful for performance monitoring

**Example Response:**

```http
HTTP/1.1 200 OK
X-Process-Time: 0.0123
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Max Request Size Middleware

Prevent oversized request bodies.

```python
from fastapi_bootstrap import MaxRequestSizeMiddleware

# Limit to 10MB
app.add_middleware(MaxRequestSizeMiddleware, max_size=10 * 1024 * 1024)
```

**Configuration:**

```python
# Different limits for different endpoints
app.add_middleware(
    MaxRequestSizeMiddleware,
    max_size=5 * 1024 * 1024,  # 5MB default
    exclude_paths=["/upload"]   # Exclude specific paths
)
```

### Middleware Order

**Important:** Order matters! Apply in this sequence:

```python
# 1. Security (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request tracking
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestTimingMiddleware)

# 3. Size limits
app.add_middleware(MaxRequestSizeMiddleware, max_size=10_000_000)

# 4. Metrics (innermost - measures actual processing)
app.add_middleware(MetricsMiddleware)
```

---

## Authentication

### OIDC Authentication Setup

Requires: `pip install fastapi-bootstrap[auth]`

#### Basic Configuration

```python
from fastapi import Depends
from fastapi_bootstrap import OIDCAuth, OIDCConfig

auth = OIDCAuth(
    OIDCConfig(
        issuer="https://your-idp.com",
        audience="your-api-audience",
        jwks_uri="https://your-idp.com/.well-known/jwks.json",  # Optional
    )
)

@router.get("/protected")
async def protected(token=Depends(auth)):
    return {
        "user_id": token.sub,
        "email": token.email,
        "scopes": token.scopes,
    }
```

#### Token Claims

Access JWT claims via the token object:

```python
@router.get("/user")
async def get_current_user(token=Depends(auth)):
    return {
        "sub": token.sub,              # Subject (user ID)
        "email": token.email,          # Email claim
        "name": token.name,            # Name claim
        "scopes": token.scopes,        # Token scopes/permissions
        "exp": token.exp,              # Expiration time
        "iat": token.iat,              # Issued at
    }
```

#### Scope-Based Authorization

```python
from fastapi_bootstrap import require_scopes

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    token=Depends(auth),
    _=Depends(require_scopes(["admin", "users:delete"]))
):
    # Only users with admin OR users:delete scope can access
    return {"deleted": user_id}
```

#### Custom Token Validation

```python
from fastapi_bootstrap import OIDCAuth, OIDCConfig

class CustomAuth(OIDCAuth):
    async def validate_token(self, token: dict) -> dict:
        token = await super().validate_token(token)
        
        # Custom validation logic
        if token.get("email_verified") is not True:
            raise UnauthorizedException("Email not verified")
        
        return token

auth = CustomAuth(OIDCConfig(...))
```

#### Auth Configuration Options

```python
auth = OIDCAuth(
    OIDCConfig(
        issuer="https://your-idp.com",
        audience="your-api",
        
        # Optional JWKS URI (auto-discovered if not provided)
        jwks_uri="https://your-idp.com/.well-known/jwks.json",
        
        # Token validation options
        verify_exp=True,           # Verify expiration
        verify_aud=True,           # Verify audience
        leeway=10,                 # Clock skew tolerance (seconds)
        
        # Caching
        cache_ttl=3600,           # JWKS cache time (seconds)
    )
)
```

---

## Metrics

### Prometheus Metrics

Enable comprehensive request metrics.

```python
from fastapi_bootstrap import create_app, MetricsMiddleware, get_metrics_router

app = create_app([router], title="My API")
app.add_middleware(MetricsMiddleware)
app.include_router(get_metrics_router())  # GET /metrics
```

### Available Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `http_requests_total` | Counter | Total request count | `method`, `path`, `status` |
| `http_request_duration_seconds` | Histogram | Request latency distribution | `method`, `path` |
| `http_requests_in_progress` | Gauge | Current active requests | `method`, `path` |
| `http_request_size_bytes` | Summary | Request body size | `method`, `path` |
| `http_response_size_bytes` | Summary | Response body size | `method`, `path` |

### Example Prometheus Queries

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate (4xx + 5xx)
rate(http_requests_total{status=~"4..|5.."}[5m])

# Current load
http_requests_in_progress
```

### Custom Metrics

```python
from prometheus_client import Counter, Histogram

# Define custom metrics
user_registrations = Counter(
    'user_registrations_total',
    'Total user registrations'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Use in endpoints
@router.post("/register")
async def register(user: UserCreate):
    user_registrations.inc()
    
    with db_query_duration.labels(query_type="insert").time():
        await db.create_user(user)
    
    return {"status": "created"}
```

---

## CORS Configuration

Enable Cross-Origin Resource Sharing for your API.

### Basic CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app = create_app([router], title="My API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Development CORS

```python
import os

origins = ["http://localhost:3000"]  # Development frontend

if os.getenv("ENV") == "production":
    origins = ["https://myapp.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Preflight Requests

CORS middleware automatically handles `OPTIONS` preflight requests.

```python
# No special handling needed
@router.post("/data")
async def create_data(data: dict):
    return {"created": data}
```

Browser will automatically send `OPTIONS /data` before `POST /data`.

---

## Health Checks

### Built-in Health Check

FastAPI Bootstrap includes a basic health check at `/health`.

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Custom Health Checks

Create comprehensive health checks:

```python
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("")
async def health_check():
    return {"status": "ok"}

@health_router.get("/ready")
async def readiness_check():
    """Check if app is ready to receive traffic"""
    # Check database connection
    try:
        await db.execute("SELECT 1")
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "reason": "database unavailable"}
        )
    
    return {"status": "ready"}

@health_router.get("/live")
async def liveness_check():
    """Check if app is alive (for restart decision)"""
    return {"status": "alive"}

app.include_router(health_router)
```

### Kubernetes Health Checks

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapi
spec:
  containers:
  - name: api
    image: myapi:latest
    ports:
    - containerPort: 8000
    
    # Liveness probe (restart if failing)
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 30
    
    # Readiness probe (remove from service if failing)
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 10
```

---

## Complete API Reference

### create_app()

```python
def create_app(
    routers: list[APIRouter],
    settings: BootstrapSettings | None = None,
    *,
    dependencies: list[Any] | None = None,
    middlewares: list | None = None,
    startup_coroutines: list[Callable] | None = None,
    shutdown_coroutines: list[Callable] | None = None,
) -> FastAPI:
    """
    Create a FastAPI application with preconfigured features.
    
    Args:
        routers: List of APIRouter instances to include
        settings: BootstrapSettings for all configuration (uses defaults if None)
        dependencies: Global dependencies applied to all routes
        middlewares: Custom middleware classes to add
        startup_coroutines: Async functions to run on startup
        shutdown_coroutines: Async functions to run on shutdown
    
    Returns:
        Configured FastAPI application
    """
```

### BootstrapSettings

```python
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    GracefulShutdownSettings,
    HealthCheckSettings,
    LoggingSettings,
    MetricsSettings,
    RateLimitSettings,
    SecuritySettings,
    Stage,
)

settings = BootstrapSettings(
    # Application metadata
    title="My API",
    version="1.0.0",
    description="API description",
    
    # Environment
    stage=Stage.PROD,  # dev, staging, prod
    prefix_url="/api/v1",
    
    # Sub-configurations
    logging=LoggingSettings(level="INFO"),
    cors=CORSSettings(origins=["https://myapp.com"]),
    security=SecuritySettings(add_external_basic_auth=True),
    rate_limit=RateLimitSettings(enabled=True),
    metrics=MetricsSettings(enabled=True),
    health_check=HealthCheckSettings(endpoint="/health"),
    graceful_shutdown=GracefulShutdownSettings(timeout=30),
    docs=DocsSettings(enabled=True, swagger_oauth={...}),
)
```

### Settings Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `title` | `str` | `"FastAPI Application"` | API title |
| `version` | `str` | `"0.1.0"` | API version |
| `description` | `str` | `""` | API description |
| `stage` | `Stage` | `Stage.DEV` | Environment stage |
| `prefix_url` | `str` | `""` | URL prefix for all routes |

### CORSSettings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `origins` | `list[str]` | `[]` | Allowed origins |
| `allow_credentials` | `bool` | `True` | Allow credentials |
| `allow_methods` | `list[str]` | `["GET", "POST", ...]` | Allowed methods |
| `allow_headers` | `list[str]` | `["*"]` | Allowed headers |

### DocsSettings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `bool` | `True` | Enable docs endpoints |
| `prefix_url` | `str` | `""` | URL prefix for docs |
| `swagger_oauth` | `dict \| None` | `None` | OAuth config for Swagger UI |

### SecuritySettings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_security_headers` | `bool` | `True` | Enable security headers |
| `add_external_basic_auth` | `bool` | `False` | Add bearer auth to OpenAPI |
| `hsts_max_age` | `int` | `31536000` | HSTS max-age |
| `max_request_size` | `int` | `10MB` | Max request body size |

### LoggingAPIRoute

```python
class LoggingAPIRoute(APIRoute):
    """
    Enhanced APIRoute with automatic request/response logging.
    
    Features:
    - Logs all requests with method, path, status, duration
    - Includes trace ID from RequestIDMiddleware
    - Structured logging with Loguru
    """
```

Usage:

```python
router = APIRouter(route_class=LoggingAPIRoute)
```

### get_logger()

```python
def get_logger(name: str) -> Logger:
    """
    Get a configured Loguru logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured Loguru logger
    """
```

### BaseModel

```python
class BaseModel(PydanticBaseModel):
    """
    Enhanced Pydantic BaseModel with strict validation.
    
    Features:
    - Extra fields forbidden by default
    - Use model_validate() for validation
    - Use model_dump() for serialization
    """
    
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )
```

---

## Exception Classes

All exceptions return consistent JSON responses:

```python
from fastapi_bootstrap.exception import (
    BadRequestException,        # 400
    UnauthorizedException,      # 401
    ForbiddenException,         # 403
    NotFoundException,          # 404
    InternalServerException,    # 500
)

# Custom exceptions
class ValidationException(BadRequestException):
    def __init__(self, errors: list[str]):
        detail = f"Validation failed: {', '.join(errors)}"
        super().__init__(detail=detail)
```

---

## Examples

Complete working examples are in the [examples/](../examples/) directory:

### Simple API

```bash
cd examples/simple
uvicorn main:app --reload
```

Features: Basic routing, logging, exception handling

### CORS-Enabled API

```bash
cd examples/cors
uvicorn main:app --reload
```

Features: CORS configuration, multiple origins

### Authenticated API

```bash
cd examples/auth
uvicorn main:app --reload
```

Features: OIDC authentication, protected endpoints, scope validation

### External Auth Provider

```bash
cd examples/external_auth
uvicorn main:app --reload
```

Features: Integration with external identity providers

---

## Additional Resources

- **GitHub**: [https://github.com/bestend/fastapi_bootstrap](https://github.com/bestend/fastapi_bootstrap)
- **PyPI**: [https://pypi.org/project/fastapi-bootstrap](https://pypi.org/project/fastapi-bootstrap)
- **Issues**: [https://github.com/bestend/fastapi_bootstrap/issues](https://github.com/bestend/fastapi_bootstrap/issues)

---

**Back to [README](./README.md)**
