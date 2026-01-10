"""FastAPI Bootstrap

🚀 Production-ready FastAPI boilerplate with batteries included.

**Quick Start:**
```python
from fastapi import APIRouter
from fastapi_bootstrap import create_app, LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "Hello, World!"}

app = create_app([router], title="My API", version="1.0.0")
```
"""

from .base import create_app
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
    __all__ = [
        # Core
        "BaseModel",
        "LoggingAPIRoute",
        "ResponseFormatter",
        "create_app",
        "get_logger",
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
