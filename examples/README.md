# FastAPI Bootstrap Examples

## Examples

### [Simple](./simple/) - Basic Usage

```bash
python examples/simple/app.py
```

Logging, standardized responses, pagination

### [Auth](./auth/) - OIDC Authentication

```bash
export OIDC_ISSUER="..." OIDC_CLIENT_ID="..."
python examples/auth/app.py
```

Keycloak/Auth0 integration, role-based access control

### [CORS](./cors/) - CORS Configuration

```bash
python examples/cors/app.py  # dev
STAGE=prod ALLOWED_ORIGINS="https://myapp.com" python examples/cors/app.py  # prod
```

Environment-specific CORS settings

### [External Auth](./external_auth/) - External Authentication

```bash
python examples/external_auth/app.py
```

API Gateway/Ingress authentication, Swagger UI Bearer token support

---

## Quick Reference

### Basic App (Traditional)

```python
from fastapi_bootstrap import create_app

app = create_app([router], title="My API", prefix_url="/v1")
```

### Auto Logging

```python
from fastapi_bootstrap import LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)
```

### Standard Responses

```python
from fastapi_bootstrap import ResponseFormatter

return ResponseFormatter.success(data={...})
return ResponseFormatter.paginated(data=[...], page=1, page_size=10, total_items=100)
```

### OIDC Auth

```python
from fastapi_bootstrap import OIDCAuth, OIDCConfig

config = OIDCConfig(issuer="...", client_id="...")
auth = OIDCAuth(config)

@router.get("/me")
async def get_me(user = Depends(auth.get_current_user)):
    return {"email": user.email}
```

### Prometheus Metrics

```python
from fastapi_bootstrap import get_metrics_router, MetricsMiddleware

app.add_middleware(MetricsMiddleware)
app.include_router(get_metrics_router())
# Metrics available at GET /metrics
```

### Security Headers

```python
from fastapi_bootstrap import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    stage="prod",
    hsts_max_age=31536000,
    content_security_policy="default-src 'self'",
)
```

### Configuration

```python
from fastapi_bootstrap import BootstrapSettings, get_settings

# Load from environment variables
settings = get_settings()

# Or configure programmatically
settings = BootstrapSettings(
    stage="prod",
    logging=LoggingSettings(level="WARNING"),
    cors=CORSSettings(origins=["https://myapp.com"]),
)
```

### Sensitive Data Masking

```python
from fastapi_bootstrap import mask_sensitive_data

data = {"username": "john", "password": "secret123"}
masked = mask_sensitive_data(data)
# {"username": "john", "password": "***MASKED***"}
```

### CORS

```python
app = create_app(
    [router],
    stage="prod",
    cors_origins=["https://myapp.com"]
)
```

### External Auth (API Gateway)

```python
app = create_app(
    [router],
    add_external_basic_auth=True,  # Add Bearer auth to Swagger
)
```

