"""External Auth Example

API Gateway나 Ingress에서 인증을 처리하는 환경에서 사용하는 예제입니다.

실제 인증은 외부(Nginx, Kong, Istio 등)에서 처리되지만,
Swagger UI에서는 Bearer token을 입력할 수 있도록 OpenAPI 스키마에 포함합니다.
"""

import os

import uvicorn
from fastapi import APIRouter, Header

from fastapi_kit import LoggingAPIRoute, ResponseFormatter, create_app, get_logger

logger = get_logger()

# Create router
router = APIRouter(route_class=LoggingAPIRoute, prefix="/api", tags=["external-auth"])


@router.get("/public")
async def public_endpoint():
    """Public endpoint (external auth에서 제외)."""
    return ResponseFormatter.success(
        data={"message": "This is public"},
        message="Public access"
    )


@router.get("/protected")
async def protected_endpoint(authorization: str = Header(None)):
    """Protected endpoint (external auth 필요).

    실제 인증은 API Gateway/Ingress에서 처리됨.
    여기서는 헤더만 확인.
    """
    # External auth가 통과시킨 경우 헤더가 있음
    if not authorization:
        return ResponseFormatter.error(
            code="UNAUTHORIZED",
            message="No authorization header (external auth should add this)"
        )

    return ResponseFormatter.success(
        data={
            "message": "Protected resource",
            "auth_header": authorization[:20] + "..."  # 일부만 표시
        },
        message="Access granted by external auth"
    )


@router.get("/user-info")
async def user_info(
    x_user_email: str = Header(None),
    x_user_id: str = Header(None),
    x_user_roles: str = Header(None)
):
    """User info from external auth headers.

    API Gateway/Ingress가 검증 후 user 정보를 헤더로 전달.
    """
    return ResponseFormatter.success(
        data={
            "email": x_user_email,
            "user_id": x_user_id,
            "roles": x_user_roles.split(",") if x_user_roles else []
        },
        message="User info from external auth"
    )


# Create app with external auth enabled in OpenAPI schema
app = create_app(
    api_list=[router],
    title="External Auth Example",
    version="1.0.0",
    prefix_url="",
    docs_enable=True,
    add_external_basic_auth=True,  # ✅ Swagger UI에 Bearer auth 입력 가능
    stage=os.getenv("STAGE", "dev"),
)


if __name__ == "__main__":
    print("=" * 60)
    print("External Auth Example")
    print("=" * 60)
    print()
    print("실제 인증은 API Gateway/Ingress에서 처리됨:")
    print("  - Nginx: auth_request")
    print("  - Kong: JWT/OAuth2 plugin")
    print("  - Istio: RequestAuthentication")
    print("  - AWS ALB: Cognito integration")
    print()
    print("이 예제는 Swagger UI에서 Bearer token 입력 가능하게 함")
    print()
    print("Endpoints:")
    print("  GET  /api/public - Public")
    print("  GET  /api/protected - Protected by external auth")
    print("  GET  /api/user-info - User info from headers")
    print()
    print("Swagger UI: http://localhost:8000/docs")
    print("  1. Authorize 버튼 클릭")
    print("  2. Bearer token 입력")
    print("  3. API 테스트")
    print()
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

