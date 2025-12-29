"""OIDC/Keycloak authentication example.

This example shows how to integrate OIDC authentication (Keycloak, Auth0, etc.)
with FastAPI Bootstrap.

Requirements:
    pip install fastapi_bootstrap[auth]
"""

import os

import uvicorn
from fastapi import APIRouter, Depends

from fastapi_bootstrap import (
    LoggingAPIRoute,
    OIDCAuth,
    OIDCConfig,
    ResponseFormatter,
    TokenPayload,
    create_app,
    get_logger,
)

logger = get_logger()

# Configure OIDC/Keycloak
config = OIDCConfig(
    issuer=os.getenv(
        "OIDC_ISSUER", "https://keycloak.example.com/realms/myrealm"
    ),
    client_id=os.getenv("OIDC_CLIENT_ID", "my-client"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET", ""),
    audience=None,  # Keycloak에서 audience를 설정하지 않은 경우 None으로 설정
)

# Initialize auth handler
# enable_swagger_ui=True: OAuth2 flow + Bearer token 둘 다 지원
auth = OIDCAuth(config, enable_swagger_ui=True)

# Create router
router = APIRouter(route_class=LoggingAPIRoute, prefix="/api", tags=["auth-demo"])


# Public endpoint (no authentication)
@router.get("/public")
async def public_endpoint():
    """Public endpoint - no authentication required."""
    return ResponseFormatter.success(
        data={"message": "This is a public endpoint"}, message="Public access"
    )


# Protected endpoint (authentication required)
@router.get("/me")
async def get_current_user(user: TokenPayload = Depends(auth.get_current_user)):
    """Get current user info - authentication required.

    Headers:
        Authorization: Bearer <token>
    """
    return ResponseFormatter.success(
        data={
            "sub": user.sub,
            "email": user.email,
            "username": user.preferred_username,
            "name": user.name,
            "roles": user.roles,
            "groups": user.groups,
        },
        message="User info retrieved",
    )


# Role-based endpoint (requires admin role)
@router.get("/admin")
async def admin_only(user: TokenPayload = Depends(auth.require_roles(["admin"]))):
    """Admin only endpoint - requires 'admin' role.

    Headers:
        Authorization: Bearer <token>
    """
    return ResponseFormatter.success(
        data={"message": "Welcome, admin!", "user": user.email},
        message="Admin access granted",
    )


# Multiple roles (any one required)
@router.get("/moderator")
async def moderator_endpoint(
        user: TokenPayload = Depends(auth.require_roles(["admin", "moderator"]))
):
    """Moderator endpoint - requires 'admin' OR 'moderator' role.

    Headers:
        Authorization: Bearer <token>
    """
    return ResponseFormatter.success(
        data={"message": "Moderator access", "roles": user.roles}
    )


# Multiple roles (all required)
@router.delete("/system/purge")
async def dangerous_operation(
        user: TokenPayload = Depends(
            auth.require_roles(["admin", "superuser"], require_all=True)
        )
):
    """Dangerous operation - requires BOTH 'admin' AND 'superuser' roles.

    Headers:
        Authorization: Bearer <token>
    """
    return ResponseFormatter.success(
        data={"message": "Purge initiated", "by": user.email},
        message="Dangerous operation executed",
    )


# Group-based access
@router.get("/departments/engineering")
async def engineering_data(
        user: TokenPayload = Depends(auth.require_groups(["/engineering", "/developers"]))
):
    """Engineering department data - requires engineering or developers group.

    Headers:
        Authorization: Bearer <token>
    """
    return ResponseFormatter.success(
        data={"department": "engineering", "members": 42}, message="Department data"
    )


# Optional authentication
@router.get("/posts")
async def list_posts(user: TokenPayload | None = Depends(auth.optional_auth())):
    """List posts - returns personalized results if authenticated.

    Headers:
        Authorization: Bearer <token> (optional)
    """
    if user:
        # Authenticated user - return personalized posts
        return ResponseFormatter.success(
            data={
                "posts": ["Your post 1", "Your post 2"],
                "personalized": True,
                "user": user.email,
            },
            message="Personalized posts",
        )
    else:
        # Anonymous user - return public posts
        return ResponseFormatter.success(
            data={"posts": ["Public post 1", "Public post 2"], "personalized": False},
            message="Public posts",
        )


# Create app
PREFIX_URL = "/v1"
app = create_app(
    api_list=[router],
    title="OIDC Auth Demo",
    version="1.0.0",
    prefix_url=PREFIX_URL,
    docs_enable=True,
    health_check_api="/healthz",
    graceful_timeout=0,
    stage=os.getenv("STAGE", "dev"),
    cors_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://0.0.0.0:8000"],
    cors_allow_credentials=True,
    swagger_ui_init_oauth={
        "clientId": config.client_id,
        "clientSecret": config.client_secret,
        "appName": "OIDC Auth Demo",
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": ["openid", "profile", "email"],
        "useBasicAuthenticationWithAccessCodeGrant": False,
    },
)

if __name__ == "__main__":
    print("=" * 60)
    print("OIDC Auth Example")
    print("=" * 60)
    print(f"Issuer: {config.issuer}")
    print(f"Client: {config.client_id}")
    print()
    print("Endpoints:")
    print(f"  GET  {PREFIX_URL}/api/public - Public")
    print(f"  GET  {PREFIX_URL}/api/me - Current user")
    print(f"  GET  {PREFIX_URL}/api/admin - Admin only")
    print(f"  GET  {PREFIX_URL}/api/moderator - Admin or Moderator")
    print()
    docs_path = f"{PREFIX_URL}/docs" if PREFIX_URL else "/docs"
    print(f"Swagger UI: http://localhost:8000{docs_path}")
    print()
    print("인증 방법 (2가지):")
    print("  1️⃣  OAuth2 (Authorize 버튼)")
    print("     - Keycloak 로그인 페이지로 이동")
    print("     - 자동으로 토큰 획득")
    print("     - Swagger UI 테스트용")
    print()
    print("  2️⃣  Bearer Token (Authorize 버튼)")
    print("     - 직접 JWT 토큰 입력")
    print("     - 프론트엔드 → 백엔드 시나리오 테스트")
    print("     - curl로 토큰 획득 후 붙여넣기")
    print()
    print("Keycloak 설정:")
    print("  Valid Redirect URIs: http://localhost:8000/*")
    print("  Web Origins: +")
    print("  Direct Access Grants: ON")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
