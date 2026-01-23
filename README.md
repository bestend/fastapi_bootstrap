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

# Minimal - uses defaults
app = create_app(routers=[router])

# With settings
from fastapi_bootstrap.config import BootstrapSettings

settings = BootstrapSettings(title="My API", version="1.0.0")
app = create_app(routers=[router], settings=settings)
```

Run with: `uvicorn app:app --reload`

## Configuration

All configuration is done via `BootstrapSettings`:

```python
from fastapi_bootstrap import create_app
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    Stage,
)

settings = BootstrapSettings(
    title="My API",
    version="1.0.0",
    stage=Stage.PROD,
    prefix_url="/api/v1",
    cors=CORSSettings(origins=["https://myapp.com"]),
    docs=DocsSettings(enabled=True),
)

app = create_app(routers=[router], settings=settings)
```

### Environment Variables

```bash
STAGE=prod                    # dev, staging, prod
APP_TITLE="My API"
APP_VERSION="1.0.0"
API_PREFIX_URL="/api/v1"
CORS_ORIGINS="https://myapp.com,https://api.myapp.com"
DOCS_ENABLED=true
LOG_LEVEL=INFO
```

## Core Components

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

## API Reference

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
) -> FastAPI
```

| Parameter | Description |
|-----------|-------------|
| `routers` | List of FastAPI APIRouter instances |
| `settings` | BootstrapSettings for all configuration |
| `dependencies` | Global dependencies for all routes |
| `middlewares` | Custom middleware classes |
| `startup_coroutines` | Async functions to run on startup |
| `shutdown_coroutines` | Async functions to run on shutdown |

## Documentation

For advanced features, see [ADVANCED.md](./ADVANCED.md):
- Security Headers Configuration
- Request ID & Timing Middleware
- Max Request Size Limits
- OIDC Authentication Setup
- CORS Configuration
- Health Checks
- Complete Examples

## Migration from v1.x

See [MIGRATION.md](./MIGRATION.md) for upgrading from previous versions.

## Examples

See [examples/](./examples/) directory for complete working examples.

## License

MIT License - see [LICENSE](./LICENSE)
