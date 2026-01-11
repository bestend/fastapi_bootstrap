# Auth Example

OIDC/Keycloak authentication integration

## Run

```bash
export OIDC_ISSUER="https://keycloak.example.com/realms/myrealm"
export OIDC_CLIENT_ID="my-api"
export OIDC_CLIENT_SECRET="your-secret"

python examples/auth/app.py
# http://localhost:8000/docs
```

## Authentication Methods (2 options)

Test both ways in Swagger UI:

### 1️⃣ OAuth2 (Authorization Code Flow)

**Automatic login for Swagger UI testing**

1. 🔓 Click Authorize button
2. Select **OAuth2AuthorizationCodeBearer**
3. Click Authorize
4. Keycloak login page opens
5. Login → Return to Swagger
6. ✅ Token automatically included in all requests

### 2️⃣ Bearer Token (Manual JWT)

**Real frontend scenario - manual token input**

1. 🔓 Click Authorize button
2. Select **BearerAuth**
3. Paste JWT token
4. Click Authorize
5. ✅ Token included in all requests

**Get token:**
```bash
curl -X POST https://keycloak.../token \
  -d "grant_type=password" \
  -d "client_id=my-api" \
  -d "username=user" \
  -d "password=pass" \
  | jq -r '.access_token'
```

## Comparison

| Method | Use Case | Benefit |
|--------|----------|---------|
| **OAuth2** | Swagger UI testing | Automatic login, convenient |
| **Bearer** | Frontend scenario | Real-world flow testing |

**In production:**
- Frontend gets token via OAuth2
- Sends to backend via Bearer header
- Backend only validates token

## Keycloak Setup

**Admin Console → Clients → [your-client] → Settings:**

```
✅ Standard Flow Enabled: ON
✅ Direct Access Grants Enabled: ON
✅ Valid Redirect URIs: http://localhost:8000/*
✅ Web Origins: +
```

## Code

```python
import os

import uvicorn
from fastapi import APIRouter, Depends

from fastapi_bootstrap import (
    LoggingAPIRoute,
    OIDCAuth,
    OIDCConfig,
    TokenPayload,
    create_app,
)

config = OIDCConfig(
    issuer=os.getenv("OIDC_ISSUER", "https://keycloak.example.com/realms/myrealm"),
    client_id=os.getenv("OIDC_CLIENT_ID", "my-client"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET", ""),
    audience=None,
)

auth = OIDCAuth(config, enable_swagger_ui=True)
router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/public")
async def public():
    return {"message": "Public endpoint"}


@router.get("/me")
async def get_me(user: TokenPayload = Depends(auth.get_current_user)):
    return {
        "sub": user.sub,
        "email": user.email,
        "username": user.preferred_username,
        "roles": user.roles,
    }


@router.get("/admin")
async def admin_only(user: TokenPayload = Depends(auth.require_roles(["admin"]))):
    return {"message": "Admin access", "user": user.email}


app = create_app(
    api_list=[router],
    title="Auth Example",
    swagger_ui_init_oauth={
        "clientId": config.client_id,
        "clientSecret": config.client_secret,
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

if __name__ == "__main__":
    print(f"OIDC Issuer: {config.issuer}")
    print(f"Client ID: {config.client_id}")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Endpoints

```bash
# Public
GET /public

# Authenticated
GET /me

# Admin role required
GET /admin
```

## Role/Group Checks

```python
# Single role
auth.require_roles(["admin"])

# OR condition
auth.require_roles(["admin", "moderator"])

# AND condition (both required)
auth.require_roles(["admin", "superuser"], require_all=True)

# Group check
auth.require_groups(["/engineering"])
```

## Troubleshooting

### Invalid redirect_uri
```
Keycloak Valid Redirect URIs:
http://localhost:8000/*
http://localhost:8000/v1/docs/oauth2-redirect
```

### Invalid audience
```python
config = OIDCConfig(..., audience=None)  # Keycloak uses None
```

### Failed to fetch
```
Keycloak:
✅ Direct Access Grants Enabled: ON
✅ Web Origins: +
```

## Provider-specific Config

```python
# Keycloak
OIDCConfig(issuer="https://keycloak.../realms/myrealm", ..., audience=None)

# Auth0
OIDCConfig(issuer="https://myapp.auth0.com", ..., audience="https://api.myapp.com")

# Google
OIDCConfig(issuer="https://accounts.google.com", ..., audience=client_id)
```

