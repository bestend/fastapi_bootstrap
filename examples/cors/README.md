# CORS Example

Environment-specific CORS configuration

## Run

```bash
# Development (all origins allowed)
python examples/cors/app.py

# Production (specific origins only)
STAGE=prod ALLOWED_ORIGINS="https://myapp.com,https://www.myapp.com" \
  python examples/cors/app.py
```

## Auto Configuration by Environment

```python
from fastapi_bootstrap.config import BootstrapSettings, CORSSettings, Stage

# dev (default: all origins allowed)
settings = BootstrapSettings(stage=Stage.DEV)
app = create_app(routers=[router], settings=settings)
# → cors origins = ["*"]

# prod (must set explicitly)
settings = BootstrapSettings(
    stage=Stage.PROD,
    cors=CORSSettings(origins=["https://myapp.com"]),
)
app = create_app(routers=[router], settings=settings)
```

## Code

```python
import os

import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, create_app
from fastapi_bootstrap.config import BootstrapSettings, CORSSettings, Stage

router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/data")
async def get_data():
    return {"message": "CORS-enabled endpoint"}


# Parse environment
stage = Stage(os.getenv("STAGE", "dev"))
origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else None

settings = BootstrapSettings(
    title="CORS Example",
    stage=stage,
    cors=CORSSettings(origins=origins) if origins else None,
)
app = create_app(routers=[router], settings=settings)

if __name__ == "__main__":
    print(f"Stage: {stage}")
    print(f"Allowed origins: {origins or '*'}")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

```bash
# Test endpoint
curl "http://localhost:8000/data"
```

Or test CORS from browser console:

```javascript
// Browser console (from http://example.com)
fetch('http://localhost:8000/data')
  .then(r => r.json())
  .then(console.log)
  .catch(err => console.error('CORS Error:', err));
```

## Environment Comparison

| Environment | origins | credentials | Use Case |
|-------------|---------|-------------|----------|
| dev | `["*"]` | True | Local development |
| staging | patterns | True | Testing |
| prod | explicit | True | Production |

## Security

### ✅ Safe Config

```python
# Production
from fastapi_bootstrap.config import BootstrapSettings, CORSSettings, Stage

settings = BootstrapSettings(
    stage=Stage.PROD,
    cors=CORSSettings(
        origins=["https://myapp.com"],  # Explicit
        allow_credentials=True,
    ),
)
```

### ❌ Dangerous Config

```python
# ❌ Never in production!
cors=CORSSettings(
    origins=["*"],
    allow_credentials=True,  # wildcard + credentials
)
```

## Troubleshooting

### CORS Error

**Fix:**
```python
# Add origin
cors=CORSSettings(origins=["https://your-domain.com"])

# Or use dev mode
settings = BootstrapSettings(stage=Stage.DEV)
```

### Preflight Failed

```python
# Include OPTIONS method
cors=CORSSettings(allow_methods=["GET", "POST", "OPTIONS"])
```

## Environment Variables

```bash
# .env.prod
STAGE=prod
ALLOWED_ORIGINS=https://myapp.com,https://www.myapp.com
```

