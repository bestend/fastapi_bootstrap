"""CORS Configuration Example

이 예제는 FastAPI Bootstrap에서 CORS를 환경별로 설정하는 방법을 보여줍니다.

Features:
- 환경별 CORS 설정 (dev/staging/prod)
- 안전한 프로덕션 설정
- 커스텀 CORS 설정
"""

import os

import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, ResponseFormatter, create_app, get_logger

logger = get_logger()

# Create router
router = APIRouter(route_class=LoggingAPIRoute, prefix="/api", tags=["cors-demo"])


@router.get("/public")
async def public_endpoint():
    """Public endpoint accessible from any origin (in dev mode)."""
    return ResponseFormatter.success(
        data={"message": "This endpoint respects CORS settings"},
        message="CORS test successful"
    )


@router.post("/data")
async def post_data(data: dict):
    """POST endpoint to test CORS with credentials."""
    return ResponseFormatter.success(
        data={"received": data, "message": "Data processed successfully"},
        message="POST with CORS"
    )


# === Example 1: Development (Permissive CORS) ===
def create_dev_app():
    """개발 환경 - 모든 origin 허용"""
    return create_app(
        api_list=[router],
        title="CORS Dev Example",
        version="1.0.0",
        prefix_url="/v1",
        stage="dev",  # 자동으로 CORS origins=["*"] 설정
    )


# === Example 2: Production (Restrictive CORS) ===
def create_prod_app():
    """프로덕션 환경 - 특정 origin만 허용"""
    return create_app(
        api_list=[router],
        title="CORS Prod Example",
        version="1.0.0",
        prefix_url="/v1",
        stage="prod",
        cors_origins=[
            "https://myapp.com",
            "https://www.myapp.com",
            "https://app.myapp.com",
        ],
        cors_allow_credentials=True,  # 쿠키/인증 허용
    )


# === Example 3: Custom CORS ===
def create_custom_cors_app():
    """커스텀 CORS 설정"""
    return create_app(
        api_list=[router],
        title="CORS Custom Example",
        version="1.0.0",
        prefix_url="/v1",
        stage="prod",
        cors_origins=[
            "https://partner1.com",
            "https://partner2.com",
        ],
        cors_allow_credentials=False,  # 쿠키 차단
        cors_allow_methods=["GET", "POST"],  # GET, POST만 허용
        cors_allow_headers=["Content-Type", "Authorization"],  # 특정 헤더만
    )


# === Example 4: Environment-based CORS ===
def create_app_from_env():
    """환경변수 기반 CORS 설정"""
    stage = os.getenv("STAGE", "dev")

    # 환경변수에서 origins 읽기
    origins_str = os.getenv("ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in origins_str.split(",") if o.strip()] if origins_str else None

    return create_app(
        api_list=[router],
        title="CORS Env Example",
        version="1.0.0",
        prefix_url="/v1",
        stage=stage,
        cors_origins=origins,  # None이면 stage에 따라 자동 설정
        cors_allow_credentials=stage != "dev",  # dev가 아니면 credentials 허용
    )


# Default app (environment-based)
app = create_app_from_env()


if __name__ == "__main__":
    print("=" * 60)
    print("CORS Configuration Example")
    print("=" * 60)

    stage = os.getenv("STAGE", "dev")
    print(f"Stage: {stage}")
    print()

    if stage == "dev":
        print("Development Mode:")
        print("  ✅ CORS Origins: * (all origins allowed)")
        print("  ✅ Methods: * (all methods allowed)")
        print("  ✅ Headers: * (all headers allowed)")
        print()
        print("⚠️  WARNING: Not suitable for production!")
    elif stage == "prod":
        origins = os.getenv("ALLOWED_ORIGINS", "")
        if origins:
            print("Production Mode:")
            print(f"  ✅ CORS Origins: {origins}")
            print("  ✅ Methods: GET, POST, PUT, DELETE, PATCH")
            print("  ✅ Headers: Accept, Content-Type, Authorization")
        else:
            print("Production Mode:")
            print("  ⚠️  No CORS origins specified!")
            print("  ❌ All origins will be blocked")
            print()
            print("Set ALLOWED_ORIGINS environment variable:")
            print("  export ALLOWED_ORIGINS='https://myapp.com,https://www.myapp.com'")

    print()
    print("Endpoints:")
    print("  GET  /v1/api/public - Test CORS GET request")
    print("  POST /v1/api/data - Test CORS POST request")
    print()
    print("Test CORS:")
    print("  1. Open browser console on http://example.com")
    print("  2. Run:")
    print("     fetch('http://localhost:8000/v1/api/public')")
    print("       .then(r => r.json())")
    print("       .then(console.log)")
    print()
    print("API Docs: http://localhost:8000/v1/docs")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

