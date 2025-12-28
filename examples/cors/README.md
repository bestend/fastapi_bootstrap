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

### Production (explicit origins)

```python
app = create_app(
    [router],
    stage="prod",
    cors_origins=[
        "https://myapp.com",
        "https://www.myapp.com",
    ],
    cors_allow_credentials=True,
)
```

### Custom Config

```python
app = create_app(
    [router],
    stage="prod",
    cors_origins=["https://partner.com"],
    cors_allow_credentials=False,
    cors_allow_methods=["GET", "POST"],
    cors_allow_headers=["Content-Type", "Authorization"],
)
```

### Environment Variable Based

```python
import os

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app = create_app(
    [router],
    stage=os.getenv("STAGE", "dev"),
    cors_origins=origins or None,
)
```

## Testing

```javascript
// Browser console (from http://example.com)
fetch('http://localhost:8000/v1/api/public')
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

