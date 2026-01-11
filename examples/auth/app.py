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
