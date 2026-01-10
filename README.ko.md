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
- **🛡️ 예외 처리** — 중앙 집중식 에러 핸들링, 커스텀 응답
- **📊 Prometheus 메트릭** — 내장 `/metrics` 엔드포인트, 요청 통계
- **🔒 보안 헤더** — HSTS, CSP, X-Frame-Options 미들웨어
- **🔐 OIDC 인증** — JWKS 지원 JWT 검증 (선택)
- **⚡️ 타입 안전성** — Pydantic V2 통합, 향상된 BaseModel

---

## 📦 설치

```bash
pip install fastapi-bootstrap

# 인증 지원 포함
pip install fastapi-bootstrap[auth]
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

app = create_app([router], title="내 API", version="1.0.0")
```

실행: `uvicorn app:app --reload`

---

## 📖 핵심 API

### `create_app()`

모든 기능이 구성된 FastAPI 애플리케이션을 생성합니다.

```python
from fastapi_bootstrap import create_app

app = create_app(
    routers=[router],           # APIRouter 리스트
    title="내 API",             # API 제목
    version="1.0.0",            # API 버전
    description="",             # API 설명
    docs_url="/docs",           # Swagger UI 경로 (None으로 비활성화)
    openapi_url="/openapi.json",
    lifespan=None,              # 커스텀 lifespan 컨텍스트 매니저
)
```

### `LoggingAPIRoute`

타이밍과 Trace ID를 포함한 요청/응답 로깅 기능이 있는 향상된 APIRoute.

```python
from fastapi import APIRouter
from fastapi_bootstrap import LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

출력:
```
INFO | trace_id=abc123 | GET /users/42 | 200 OK | 12.5ms
```

### `get_logger()`

구성된 Loguru 로거 인스턴스를 가져옵니다.

```python
from fastapi_bootstrap import get_logger

logger = get_logger(__name__)
logger.info("처리 시작", user_id=123, action="fetch")
```

### `BaseModel`

엄격한 검증이 포함된 향상된 Pydantic BaseModel.

```python
from fastapi_bootstrap import BaseModel

class User(BaseModel):
    name: str
    email: str
    age: int | None = None
```

---

## 📊 메트릭

`MetricsMiddleware`로 Prometheus 메트릭을 활성화합니다.

```python
from fastapi_bootstrap import create_app, MetricsMiddleware, get_metrics_router

app = create_app([router], title="내 API")
app.add_middleware(MetricsMiddleware)
app.include_router(get_metrics_router())  # /metrics 엔드포인트 추가
```

제공되는 메트릭:
- `http_requests_total` — 메서드, 경로, 상태별 총 요청 수
- `http_request_duration_seconds` — 요청 지연 히스토그램
- `http_requests_in_progress` — 현재 활성 요청 수
- `http_request_size_bytes` — 요청 본문 크기
- `http_response_size_bytes` — 응답 본문 크기

---

## 🔒 보안 헤더

모든 응답에 보안 헤더를 추가합니다.

```python
from fastapi_bootstrap import create_app, SecurityHeadersMiddleware

app = create_app([router], title="내 API")
app.add_middleware(SecurityHeadersMiddleware)
```

추가되는 헤더:
- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Referrer-Policy`

---

## 🛡️ 미들웨어

### Request ID 미들웨어

모든 요청에 고유 요청 ID를 추가합니다 (`X-Request-ID` 헤더).

```python
from fastapi_bootstrap import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)
```

### Request Timing 미들웨어

요청 처리 시간을 `X-Process-Time` 헤더로 추가합니다.

```python
from fastapi_bootstrap import RequestTimingMiddleware

app.add_middleware(RequestTimingMiddleware)
```

### Max Request Size 미들웨어

요청 본문 크기를 제한합니다.

```python
from fastapi_bootstrap import MaxRequestSizeMiddleware

app.add_middleware(MaxRequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB
```

---

## 🔐 인증 (선택)

JWKS 검증을 지원하는 OIDC/JWT 인증. `pip install fastapi-bootstrap[auth]` 필요.

```python
from fastapi import Depends
from fastapi_bootstrap import OIDCAuth, OIDCConfig

auth = OIDCAuth(
    OIDCConfig(
        issuer="https://your-idp.com",
        audience="your-api-audience",
    )
)

@router.get("/protected")
async def protected(token=Depends(auth)):
    return {"user": token.sub}
```

---

## ⚠️ 예외 처리

일관된 에러 응답을 위한 내장 예외 클래스.

```python
from fastapi_bootstrap.exception import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    InternalServerException,
)

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.get(user_id)
    if not user:
        raise NotFoundException(detail="사용자를 찾을 수 없습니다")
    return user
```

에러 응답 형식:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "사용자를 찾을 수 없습니다"
  }
}
```

---

## 🌐 CORS

API에 CORS를 활성화합니다.

```python
from fastapi.middleware.cors import CORSMiddleware

app = create_app([router], title="내 API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📁 예제

완전한 예제는 [examples/](./examples/) 디렉토리를 참조하세요:

| 예제 | 설명 |
|------|------|
| [simple](./examples/simple/) | 기본 사용법, 로깅 |
| [cors](./examples/cors/) | CORS 설정 |
| [auth](./examples/auth/) | OIDC 인증 |
| [external_auth](./examples/external_auth/) | 외부 인증 제공자 |

---

## 🏥 헬스 체크

내장 헬스 체크 엔드포인트 `/health`:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 📄 라이선스

MIT 라이선스 — [LICENSE](./LICENSE) 참조



