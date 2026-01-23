<p align="center">
  <h1 align="center">🚀 FastAPI Bootstrap</h1>
</p>

<div align="center">

**배터리 포함된 프로덕션 준비 FastAPI 보일러플레이트**

**Language:** 한국어 | [English](./README.md)

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/bestend/fastapi_bootstrap/actions/workflows/tests.yml/badge.svg)](https://github.com/bestend/fastapi_bootstrap/actions/workflows/tests.yml)

</div>

---

## ✨ 기능

- **📝 구조화된 로깅** — Loguru 기반 로깅, 요청 추적, Trace ID
- **🛡️ 예외 처리** — 중앙 집중식 에러 핸들링, 일관된 응답
- **📊 Prometheus 메트릭** — 내장 `/metrics` 엔드포인트, 요청 통계
- **🔒 보안 헤더** — HSTS, CSP, X-Frame-Options 미들웨어
- **🔐 OIDC 인증** — 선택적 JWT/JWKS 검증
- **⚡️ 타입 안전성** — Pydantic V2 통합, 향상된 BaseModel

---

## 📦 설치

```bash
pip install fastapi-bootstrap
```

---

## 🚀 빠른 시작

```python
from fastapi import APIRouter
from fastapi_bootstrap import create_app, LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "안녕하세요!"}

# 최소 설정 - 기본값 사용
app = create_app(routers=[router])

# 설정과 함께
from fastapi_bootstrap.config import BootstrapSettings

settings = BootstrapSettings(title="내 API", version="1.0.0")
app = create_app(routers=[router], settings=settings)
```

실행: `uvicorn app:app --reload`

---

## ⚙️ 설정

모든 설정은 `BootstrapSettings`를 통해 관리됩니다:

```python
from fastapi_bootstrap import create_app
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    Stage,
)

settings = BootstrapSettings(
    title="내 API",
    version="1.0.0",
    stage=Stage.PROD,
    prefix_url="/api/v1",
    cors=CORSSettings(origins=["https://myapp.com"]),
    docs=DocsSettings(enabled=True),
)

app = create_app(routers=[router], settings=settings)
```

### 환경 변수

```bash
STAGE=prod                    # dev, staging, prod
APP_TITLE="내 API"
APP_VERSION="1.0.0"
API_PREFIX_URL="/api/v1"
CORS_ORIGINS="https://myapp.com,https://api.myapp.com"
DOCS_ENABLED=true
LOG_LEVEL=INFO
```

---

## 📖 핵심 컴포넌트

### 로깅

```python
from fastapi_bootstrap import get_logger, LoggingAPIRoute

logger = get_logger(__name__)
router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    logger.info("사용자 조회", user_id=user_id)
    return {"user_id": user_id}
```

### 예외 처리

```python
from fastapi_bootstrap.exception import NotFoundException

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.get(user_id)
    if not user:
        raise NotFoundException(detail="사용자를 찾을 수 없습니다")
    return user
```

에러 응답:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "사용자를 찾을 수 없습니다"
  }
}
```

### 메트릭

```python
from fastapi_bootstrap import MetricsMiddleware, get_metrics_router

app.add_middleware(MetricsMiddleware)
app.include_router(get_metrics_router())  # GET /metrics
```

---

## 📚 API 레퍼런스

### create_app()

```python
def create_app(
    routers: list[APIRouter],
    settings: BootstrapSettings | None = None,
    *,
    dependencies: list[Any] | None = None,
    middlewares: list | None = None,
    startup_coroutines: list[Callable] | None = None,
    shutdown_coroutines: list[Callable] | None = None,
) -> FastAPI
```

| 파라미터 | 설명 |
|----------|------|
| `routers` | FastAPI APIRouter 인스턴스 목록 |
| `settings` | 모든 설정을 담은 BootstrapSettings |
| `dependencies` | 모든 라우트에 적용할 전역 의존성 |
| `middlewares` | 커스텀 미들웨어 클래스 목록 |
| `startup_coroutines` | 시작 시 실행할 비동기 함수 목록 |
| `shutdown_coroutines` | 종료 시 실행할 비동기 함수 목록 |

---

## 📚 문서

고급 기능은 [ADVANCED.md](./ADVANCED.md) 참조 (영문):
- Security Headers Configuration
- Request ID & Timing Middleware
- Max Request Size Limits
- OIDC Authentication Setup
- CORS Configuration
- Health Checks
- Complete Examples

---

## 🔄 마이그레이션

이전 버전에서 업그레이드하려면 [MIGRATION.md](./MIGRATION.md) 참조.

---

## 📁 예제

완전한 예제는 [examples/](./examples/) 디렉토리를 참조하세요.

---

## 📄 라이선스

MIT 라이선스 — [LICENSE](./LICENSE) 참조
