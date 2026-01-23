# Migration Guide

## v1.x → v2.0

### Breaking Changes

#### 1. `create_app()` Signature Changed

**Before (v1.x):**
```python
app = create_app(
    api_list=[router],
    title="My API",
    version="1.0.0",
    stage="prod",
    cors_origins=["https://myapp.com"],
    health_check_api="/healthz",
    docs_enable=True,
    add_external_basic_auth=False,
    swagger_ui_init_oauth={...},
)
```

**After (v2.0):**
```python
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    HealthCheckSettings,
    SecuritySettings,
    Stage,
)

settings = BootstrapSettings(
    title="My API",
    version="1.0.0",
    stage=Stage.PROD,
    cors=CORSSettings(origins=["https://myapp.com"]),
    health_check=HealthCheckSettings(endpoint="/healthz"),
    docs=DocsSettings(
        enabled=True,
        swagger_oauth={...},
    ),
    security=SecuritySettings(add_external_basic_auth=False),
)

app = create_app(routers=[router], settings=settings)
```

#### 2. Parameter Renamed: `api_list` → `routers`

**Before:**
```python
app = create_app(api_list=[router1, router2])
```

**After:**
```python
app = create_app(routers=[router1, router2])
```

#### 3. Individual Parameters Removed

The following parameters are no longer accepted directly by `create_app()`:

| Removed Parameter | New Location |
|-------------------|--------------|
| `title` | `settings.title` |
| `version` | `settings.version` |
| `stage` | `settings.stage` |
| `prefix_url` | `settings.prefix_url` |
| `graceful_timeout` | `settings.graceful_shutdown.timeout` |
| `health_check_api` | `settings.health_check.endpoint` |
| `metrics_api` | `settings.metrics.endpoint` |
| `docs_enable` | `settings.docs.enabled` |
| `docs_prefix_url` | `settings.docs.prefix_url` |
| `add_external_basic_auth` | `settings.security.add_external_basic_auth` |
| `cors_origins` | `settings.cors.origins` |
| `cors_allow_credentials` | `settings.cors.allow_credentials` |
| `cors_allow_methods` | `settings.cors.allow_methods` |
| `cors_allow_headers` | `settings.cors.allow_headers` |
| `swagger_ui_init_oauth` | `settings.docs.swagger_oauth` |

#### 4. Kept Parameters (Code-Level)

These parameters remain in `create_app()` because they are code objects, not configuration:

```python
app = create_app(
    routers=[router],
    settings=settings,
    dependencies=[Depends(verify_api_key)],
    middlewares=[CustomMiddleware],
    startup_coroutines=[init_db],
    shutdown_coroutines=[close_db],
)
```

---

## Quick Migration Steps

### Step 1: Update Imports

```python
# Add config imports
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    Stage,
)
```

### Step 2: Create Settings Object

```python
settings = BootstrapSettings(
    title="My API",
    version="1.0.0",
    # ... move all your configuration here
)
```

### Step 3: Update create_app() Call

```python
# Before
app = create_app(api_list=[router], title="My API", ...)

# After
app = create_app(routers=[router], settings=settings)
```

---

## Environment Variables

New environment variables for v2.0:

| Variable | Description |
|----------|-------------|
| `STAGE` | Application stage (dev, staging, prod) |
| `APP_TITLE` | API title |
| `APP_VERSION` | API version |
| `API_PREFIX_URL` | URL prefix for all routes |
| `DOCS_ENABLED` | Enable/disable docs |
| `DOCS_PREFIX_URL` | URL prefix for docs |
| `ADD_EXTERNAL_BASIC_AUTH` | Add bearer auth to OpenAPI |
| `CORS_ORIGINS` | Comma-separated list of origins |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials |
| `GRACEFUL_SHUTDOWN_TIMEOUT` | Shutdown timeout in seconds |
| `METRICS_ENABLED` | Enable metrics endpoint |
| `METRICS_ENDPOINT` | Metrics endpoint path |

### Using Environment Variables

```python
settings = BootstrapSettings.from_env()
app = create_app(routers=[router], settings=settings)
```

---

## Full Migration Example

### Before (v1.x)

```python
from fastapi import APIRouter
from fastapi_bootstrap import create_app, LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "Hello"}

app = create_app(
    api_list=[router],
    title="My API",
    version="1.0.0",
    stage="prod",
    prefix_url="/api/v1",
    cors_origins=["https://myapp.com"],
    cors_allow_credentials=True,
    health_check_api="/health",
    docs_enable=True,
    add_external_basic_auth=True,
    swagger_ui_init_oauth={
        "clientId": "my-client",
        "usePkceWithAuthorizationCodeGrant": True,
    },
    graceful_timeout=30,
)
```

### After (v2.0)

```python
from fastapi import APIRouter
from fastapi_bootstrap import create_app, LoggingAPIRoute
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    GracefulShutdownSettings,
    HealthCheckSettings,
    SecuritySettings,
    Stage,
)

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "Hello"}

settings = BootstrapSettings(
    title="My API",
    version="1.0.0",
    stage=Stage.PROD,
    prefix_url="/api/v1",
    cors=CORSSettings(
        origins=["https://myapp.com"],
        allow_credentials=True,
    ),
    health_check=HealthCheckSettings(endpoint="/health"),
    docs=DocsSettings(
        enabled=True,
        swagger_oauth={
            "clientId": "my-client",
            "usePkceWithAuthorizationCodeGrant": True,
        },
    ),
    security=SecuritySettings(add_external_basic_auth=True),
    graceful_shutdown=GracefulShutdownSettings(timeout=30),
)

app = create_app(routers=[router], settings=settings)
```

---

## Benefits of v2.0

1. **Single Source of Truth**: All configuration in one `BootstrapSettings` object
2. **Type Safety**: Pydantic validation for all settings
3. **Environment Variables**: Easy loading via `BootstrapSettings.from_env()`
4. **Cleaner API**: `create_app()` has only 6 parameters instead of 21
5. **Better IDE Support**: Full autocomplete for all settings
