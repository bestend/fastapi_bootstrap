"""FastAPI Bootstrap

🚀 Production-ready FastAPI boilerplate with batteries included.

This package provides a complete FastAPI setup with logging, error handling,
request/response tracking, and more out of the box.

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

**Recommended import style:**
```python
from fastapi_bootstrap import create_app, LoggingAPIRoute, BaseModel
from fastapi_bootstrap.log import get_logger
from fastapi_bootstrap.exception import add_exception_handler
```

**Avoid importing from internal modules:**
```python
# ❌ Don't do this
from fastapi_bootstrap.base import create_app
from fastapi_bootstrap.exception.handler import add_exception_handler
```
"""

from .base import create_app
from .log import get_logger
from .logging_api_route import LoggingAPIRoute
from .response import ResponseFormatter
from .type import BaseModel

# Auth module (optional dependencies)
try:
    from .auth import OIDCAuth, OIDCConfig, TokenPayload

    __all__ = [
        "BaseModel",
        "LoggingAPIRoute",
        "OIDCAuth",
        "OIDCConfig",
        "ResponseFormatter",
        "TokenPayload",
        "create_app",
        "get_logger",
    ]
except ImportError:
    # Auth dependencies not installed
    __all__ = [
        "BaseModel",
        "LoggingAPIRoute",
        "ResponseFormatter",
        "create_app",
        "get_logger",
    ]

__version__ = "0.0.dev"
