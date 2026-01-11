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
# dev
app = create_app([router], stage="dev")
# → cors_origins = ["*"]

# prod
app = create_app([router], stage="prod")
# → cors_origins = []  ⚠️ Must set explicitly!
```

## Code

```python
import os

import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, create_app

router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/data")
async def get_data():
    return {"message": "CORS-enabled endpoint"}


app = create_app(
    api_list=[router],
    title="CORS Example",
    stage=os.getenv("STAGE", "dev"),
    cors_origins=os.getenv("ALLOWED_ORIGINS", "").split(",") or None,
)

if __name__ == "__main__":
    print(f"Stage: {os.getenv('STAGE', 'dev')}")
    print(f"Allowed origins: {os.getenv('ALLOWED_ORIGINS', '*')}")
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
cors_origins=["https://myapp.com"]  # Explicit
cors_allow_credentials=True
```

### ❌ Dangerous Config

```python
# ❌ Never in production!
cors_origins=["*"]
cors_allow_credentials=True  # wildcard + credentials
```

## Troubleshooting

### CORS Error

**Fix:**
```python
# Add origin
cors_origins=["https://your-domain.com"]

# Or use dev mode
stage="dev"
```

### Preflight Failed

```python
# Include OPTIONS method
cors_allow_methods=["GET", "POST", "OPTIONS"]
```

## Environment Variables

```bash
# .env.prod
STAGE=prod
ALLOWED_ORIGINS=https://myapp.com,https://www.myapp.com
```

