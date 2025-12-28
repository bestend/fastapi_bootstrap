# External Auth Example

API Gateway/Ingress authentication pattern

## Concept

Actual authentication is handled externally (Gateway/Ingress), but Swagger UI can still input Bearer tokens in OpenAPI schema

## Use Cases

### Authentication at API Gateway
- **Nginx**: `auth_request` module
- **Kong**: JWT/OAuth2 plugin
- **Istio**: RequestAuthentication
- **AWS ALB**: Cognito integration
- **Azure API Management**: JWT validation

### Flow

```
Client → API Gateway → FastAPI
         (auth)        (read headers only)
```

1. Client sends Bearer token
2. API Gateway validates token
3. On success, adds user info to headers
4. FastAPI only reads headers (no re-validation)

## Run

```bash
python examples/external_auth/app.py
# http://localhost:8000/docs
```

## Code

```python
from fastapi_kit import create_app

app = create_app(
    [router],
    add_external_basic_auth=True,  # ✅ Add Bearer auth to Swagger
)
```

**Result:**
- `bearerAuth` security scheme added to OpenAPI schema
- 🔓 Authorize button appears in Swagger UI
- Can input Bearer token

**But:**
- Actual auth handled by external Gateway/Ingress
- FastAPI only reads headers

## Nginx Example

```nginx
location /api {
    # External auth service
    auth_request /auth/validate;
    
    # Pass user info from auth service
    auth_request_set $user_email $upstream_http_x_user_email;
    auth_request_set $user_id $upstream_http_x_user_id;
    
    proxy_set_header X-User-Email $user_email;
    proxy_set_header X-User-ID $user_id;
    
    proxy_pass http://fastapi:8000;
}

location /auth/validate {
    internal;
    proxy_pass http://auth-service:8080/validate;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
}
```

## Kong Example

```yaml
services:
  - name: my-api
    url: http://fastapi:8000
    
plugins:
  - name: jwt
    config:
      claims_to_verify:
        - exp
      header_names:
        - Authorization
      
  - name: request-transformer
    config:
      add:
        headers:
          - X-User-Email:$(claims.email)
          - X-User-ID:$(claims.sub)
```

## Istio Example

```yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
spec:
  jwtRules:
    - issuer: "https://auth.example.com"
      jwksUri: "https://auth.example.com/.well-known/jwks.json"
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
spec:
  action: ALLOW
  rules:
    - from:
        - source:
            requestPrincipals: ["*"]
```

## FastAPI Endpoint

```python
@router.get("/protected")
async def protected(
    x_user_email: str = Header(None),
    x_user_id: str = Header(None)
):
    # External auth already validated
    # Just read headers
    return {
        "email": x_user_email,
        "user_id": x_user_id
    }
```

## Benefits

1. **Performance**: No re-validation in FastAPI
2. **Security**: Centralized auth logic
3. **Flexibility**: Multiple services share same auth
4. **Separation**: Auth logic separated from business logic

## Swagger UI Testing

1. Visit `http://localhost:8000/docs`
2. 🔓 Click **Authorize** button
3. Enter Bearer token
4. Test `/api/protected` endpoint

**Note:** In local dev without Gateway, may get 401 errors

## Development vs Production

### Development (no Gateway)
```python
# Add mock auth middleware
from starlette.middleware.base import BaseHTTPMiddleware

class MockAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Mock headers for dev
        request.state.user_email = "dev@example.com"
        request.state.user_id = "dev-user"
        return await call_next(request)

app.add_middleware(MockAuthMiddleware)
```

### Production (with Gateway)
```python
# Gateway adds headers, no middleware needed
app = create_app(
    [router],
    add_external_basic_auth=True,
    stage="prod"
)
```

## Comparison

| Method | Auth Location | FastAPI Role | Use Case |
|--------|--------------|--------------|----------|
| **Internal Auth** | FastAPI | Token validation | Single service |
| **External Auth** | Gateway/Ingress | Read headers only | MSA, multiple services |

