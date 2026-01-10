"""FastAPI Bootstrap

🚀 Production-ready FastAPI boilerplate with batteries included.

This package provides a complete FastAPI setup with logging, error handling,
request/response tracking, metrics, security headers, and more out of the box.

**Quick Start (Traditional):**
```python
from fastapi import APIRouter
from fastapi_bootstrap import create_app, LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "Hello, World!"}

app = create_app([router], title="My API", version="1.0.0")
```

**Quick Start (Builder Pattern):**
```python
from fastapi import APIRouter
from fastapi_bootstrap import bootstrap, LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "Hello, World!"}

app = (
    bootstrap()
    .title("My API")
    .version("1.0.0")
    .stage("prod")
    .with_cors(origins=["https://myapp.com"])
    .with_security_headers()
    .with_metrics()
    .add_router(router)
    .build()
)
```

**Recommended import style:**
```python
from fastapi_bootstrap import create_app, bootstrap, LoggingAPIRoute, BaseModel
from fastapi_bootstrap.log import get_logger
from fastapi_bootstrap.config import BootstrapSettings
from fastapi_bootstrap.metrics import get_metrics_router
```
"""

from .base import create_app
from .builder import FastAPIBootstrap, bootstrap
from .config import (
    BootstrapSettings,
    CORSSettings,
    LoggingSettings,
    SecuritySettings,
    Stage,
    get_settings,
    mask_sensitive_data,
)
from .log import get_logger
from .logging_api_route import LoggingAPIRoute
from .metrics import MetricsMiddleware, get_metrics_registry, get_metrics_router
from .middleware import (
    MaxRequestSizeMiddleware,
    RequestIDMiddleware,
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
)
from .response import ResponseFormatter
from .type import BaseModel

# Auth module (optional dependencies)
try:
    from .auth import OIDCAuth, OIDCConfig, TokenPayload

    __all__ = [
        # Core
        "BaseModel",
        "LoggingAPIRoute",
        "ResponseFormatter",
        "create_app",
        "get_logger",
        # Builder
        "FastAPIBootstrap",
        "bootstrap",
        # Config
        "BootstrapSettings",
        "CORSSettings",
        "LoggingSettings",
        "SecuritySettings",
        "Stage",
        "get_settings",
        "mask_sensitive_data",
        # Metrics
        "MetricsMiddleware",
        "get_metrics_registry",
        "get_metrics_router",
        # Middleware
        "MaxRequestSizeMiddleware",
        "RequestIDMiddleware",
        "RequestTimingMiddleware",
        "SecurityHeadersMiddleware",
        # Auth (optional)
        "OIDCAuth",
        "OIDCConfig",
        "TokenPayload",
    ]
except ImportError:
    # Auth dependencies not installed
    __all__ = [
        # Core
        "BaseModel",
        "LoggingAPIRoute",
        "ResponseFormatter",
        "create_app",
        "get_logger",
        # Builder
        "FastAPIBootstrap",
        "bootstrap",
        # Config
        "BootstrapSettings",
        "CORSSettings",
        "LoggingSettings",
        "SecuritySettings",
        "Stage",
        "get_settings",
        "mask_sensitive_data",
        # Metrics
        "MetricsMiddleware",
        "get_metrics_registry",
        "get_metrics_router",
        # Middleware
        "MaxRequestSizeMiddleware",
        "RequestIDMiddleware",
        "RequestTimingMiddleware",
        "SecurityHeadersMiddleware",
    ]

__version__ = "0.2.0"
