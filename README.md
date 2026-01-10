<p align="center">
  <h1 align="center">🚀 FastAPI Bootstrap</h1>
</p>

<div align="center">

**Production-ready FastAPI boilerplate with batteries included**

**Language:** [한국어](./README.ko.md) | English

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bestend/fastapi_bootstrap/actions/workflows/tests.yml/badge.svg)](https://github.com/bestend/fastapi_bootstrap/actions/workflows/tests.yml)

</div>

---

## ✨ Features

- **📝 Structured Logging** — Loguru-based logging with request tracking & trace IDs
- **🛡️ Exception Handling** — Centralized error handling with customizable responses  
- **📊 Prometheus Metrics** — Built-in `/metrics` endpoint with request stats
- **🔒 Security Headers** — HSTS, CSP, X-Frame-Options middleware
- **🔐 OIDC Authentication** — JWT validation with JWKS support (optional)
- **⚡️ Type Safety** — Pydantic V2 integration with enhanced BaseModel

---

## 📦 Installation

```bash
pip install fastapi-bootstrap

# With authentication support
pip install fastapi-bootstrap[auth]
```

---

## 🚀 Quick Start

```python
from fastapi import APIRouter
from fastapi_bootstrap import create_app, LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "Hello, World!"}

app = create_app([router], title="My API", version="1.0.0")
```

Run with: `uvicorn app:app --reload`

---

## 📖 Core API

### `create_app()`

Creates a configured FastAPI application with all features enabled.

```python
from fastapi_bootstrap import create_app

app = create_app(
    routers=[router],           # List of APIRouters
    title="My API",             # API title
    version="1.0.0",            # API version
    description="",             # API description
    docs_url="/docs",           # Swagger UI path (None to disable)
    openapi_url="/openapi.json",
    lifespan=None,              # Custom lifespan context manager
)
```

### `LoggingAPIRoute`

Enhanced APIRoute that logs requests/responses with timing and trace IDs.

```python
from fastapi import APIRouter
from fastapi_bootstrap import LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

Output:
```
INFO | trace_id=abc123 | GET /users/42 | 200 OK | 12.5ms
```

### `get_logger()`

Get a configured Loguru logger instance.

```python
from fastapi_bootstrap import get_logger

logger = get_logger(__name__)
logger.info("Processing started", user_id=123, action="fetch")
```

### `BaseModel`

Enhanced Pydantic BaseModel with strict validation.

```python
from fastapi_bootstrap import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int | None = None
```

---

## 📊 Metrics

Enable Prometheus metrics with `MetricsMiddleware`.

```python
from fastapi_bootstrap import create_app, MetricsMiddleware, get_metrics_router

app = create_app([router], title="My API")
app.add_middleware(MetricsMiddleware)
app.include_router(get_metrics_router())  # Adds /metrics endpoint
```

Available metrics:
- `http_requests_total` — Total request count by method, path, status
- `http_request_duration_seconds` — Request latency histogram
- `http_requests_in_progress` — Current active requests
- `http_request_size_bytes` — Request body size
- `http_response_size_bytes` — Response body size

---

## 🔒 Security Headers

Add security headers to all responses.

```python
from fastapi_bootstrap import create_app, SecurityHeadersMiddleware

app = create_app([router], title="My API")
app.add_middleware(SecurityHeadersMiddleware)
```

Headers added:
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Referrer-Policy`

---

## 🛡️ Middleware

### Request ID Middleware

Adds unique request ID to all requests (via `X-Request-ID` header).

```python
from fastapi_bootstrap import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
```

### Request Timing Middleware

Adds `X-Process-Time` header with request duration.

```python
from fastapi_bootstrap import RequestTimingMiddleware

app.add_middleware(RequestTimingMiddleware)
```

### Max Request Size Middleware

Limits request body size.

```python
from fastapi_bootstrap import MaxRequestSizeMiddleware

app.add_middleware(MaxRequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB
```

---

## 🔐 Authentication (Optional)

OIDC/JWT authentication with JWKS validation. Requires `pip install fastapi-bootstrap[auth]`.

```python
from fastapi import Depends
from fastapi_bootstrap import OIDCAuth, OIDCConfig

auth = OIDCAuth(
    OIDCConfig(
        issuer="https://your-idp.com",
        audience="your-api-audience",
    )
)

@router.get("/protected")
async def protected(token=Depends(auth)):
    return {"user": token.sub}
```

---

## ⚠️ Exception Handling

Built-in exception classes for consistent error responses.

```python
from fastapi_bootstrap.exception import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    InternalServerException,
)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.get(user_id)
    if not user:
        raise NotFoundException(detail="User not found")
    return user
```

Error response format:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found"
  }
}
```

---

## 🌐 CORS

Enable CORS for your API.

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

---

## 📁 Examples

See the [examples/](./examples/) directory for complete examples:

| Example | Description |
|---------|-------------|
| [simple](./examples/simple/) | Basic usage with logging |
| [cors](./examples/cors/) | CORS configuration |
| [auth](./examples/auth/) | OIDC authentication |
| [external_auth](./examples/external_auth/) | External auth provider |

---

## 🏥 Health Check

Built-in health check at `/health`:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 📄 License

MIT License — see [LICENSE](./LICENSE)
