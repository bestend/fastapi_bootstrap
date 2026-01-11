# FastAPI Bootstrap

Production-ready FastAPI boilerplate with batteries included.

[한국어](./README.ko.md) | English

## Features

- **📝 Structured Logging** — Loguru-based logging with request tracking and trace IDs
- **🛡️ Exception Handling** — Centralized error handling with consistent responses
- **📊 Prometheus Metrics** — Built-in `/metrics` endpoint with request statistics
- **🔒 Security Headers** — HSTS, CSP, X-Frame-Options middleware
- **🔐 OIDC Authentication** — Optional JWT/JWKS validation
- **⚡️ Type Safety** — Pydantic V2 integration with enhanced BaseModel

## Installation

```bash
pip install fastapi-bootstrap
```

## Quick Start

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

## Core Components

### Application Factory

```python
from fastapi_bootstrap import create_app

app = create_app(
    routers=[router],
    title="My API",
    version="1.0.0"
)
```

### Logging

```python
from fastapi_bootstrap import get_logger, LoggingAPIRoute

logger = get_logger(__name__)
router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    logger.info("Fetching user", user_id=user_id)
    return {"user_id": user_id}
```

### Exception Handling

```python
from fastapi_bootstrap.exception import NotFoundException

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.get(user_id)
    if not user:
        raise NotFoundException(detail="User not found")
    return user
```

Error response:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found"
  }
}
```

### Metrics

```python
from fastapi_bootstrap import MetricsMiddleware, get_metrics_router

app.add_middleware(MetricsMiddleware)
app.include_router(get_metrics_router())  # GET /metrics
```

## Documentation

For advanced features, see [ADVANCED.md](./ADVANCED.md):
- Security Headers Configuration
- Request ID & Timing Middleware
- Max Request Size Limits
- OIDC Authentication Setup
- CORS Configuration
- Health Checks
- Complete Examples

## Examples

See [examples/](./examples/) directory for complete working examples.

## License

MIT License - see [LICENSE](./LICENSE)
