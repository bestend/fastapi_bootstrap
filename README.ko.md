<p align="center">
  <h1 align="center">🚀 FastAPI Kit</h1>
</p>

<div align="center">

**배터리 포함된 프로덕션 준비 FastAPI 보일러플레이트**

**Language:** 한국어 | [English](./README.md)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-yellow)](https://github.com/bestend/fastapi-kit)
[![Tests](https://github.com/bestend/fastapi-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/bestend/fastapi-kit/actions/workflows/tests.yml)

</div>

---

## ✨ 개요

**FastAPI Kit**은 강력한 API를 빠르게 구축하는 데 필요한 모든 것을 포함하는 프로덕션 준비 FastAPI 보일러플레이트입니다. 사전 구성된 로깅, 에러 핸들링, 요청/응답 추적 등을 즉시 사용할 수 있습니다.

매 FastAPI 프로젝트마다 같은 보일러플레이트 코드를 작성하는 것을 멈추세요. FastAPI Kit으로 바로 기능 개발을 시작하세요.

---

## 🎯 주요 기능

- **📝 스마트 로깅** — Loguru를 사용한 구조화된 로깅, 요청/응답 추적, Trace ID
- **🛡️ 예외 처리** — 커스터마이징 가능한 에러 응답과 중앙 집중식 에러 핸들링
- **🔍 요청 추적** — OpenTelemetry 통합으로 자동 Trace ID 전파
- **🎨 커스텀 API Route** — 자동 요청/응답 로깅이 포함된 향상된 APIRoute
- **⚡️ 타입 안전성** — Pydantic V2 통합으로 강력한 데이터 검증
- **🏥 헬스 체크** — 내장 헬스 체크 엔드포인트
- **📚 자동 문서화** — 자동 OpenAPI/Swagger UI 생성
- **🔧 높은 설정성** — 로깅, CORS, 미들웨어 등을 커스터마이징 가능
- **🚀 프로덕션 준비** — Graceful shutdown, 환경 기반 설정

---

## 📦 설치

```bash
pip install fastapi-kit
```

---

## 🚀 빠른 시작

완전한 예제는 [examples/](./examples/) 디렉토리를 참조하세요.

### 간단한 예제

```bash
# 예제 실행
python examples/simple/app.py

# 접속
http://localhost:8000/v1/docs
```

### 기본 사용법

```python
from fastapi import APIRouter
from fastapi_kit import create_app, LoggingAPIRoute

# API 라우터 생성
router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/hello")
async def hello():
    return {"message": "안녕하세요!"}

# 최소 설정으로 앱 생성
app = create_app(
    [router],
    title="내 API",
    version="1.0.0",
)
```

### 앱 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 전체 설정 예제

```python
from fastapi import APIRouter
from fastapi_kit import create_app, LoggingAPIRoute, get_logger

logger = get_logger()

router = APIRouter(route_class=LoggingAPIRoute)

@router.get("/api/hello")
async def hello():
    logger.info("Hello 엔드포인트 호출됨")
    return {"message": "안녕하세요!"}

async def startup_handler(app):
    logger.info("애플리케이션 시작 중...")
    # 데이터베이스, 커넥션 등 초기화

async def shutdown_handler(app):
    logger.info("애플리케이션 종료 중...")
    # 리소스 정리

app = create_app(
    api_list=[router],
    title="내 프로덕션 API",
    version="1.0.0",
    prefix_url="/api/v1",
    graceful_timeout=10,
    docs_enable=True,
    docs_prefix_url="/api/v1",
    health_check_api="/healthz",
    startup_coroutines=[startup_handler],
    shutdown_coroutines=[shutdown_handler],
    stage="prod",  # dev, staging, prod
)
```

---

## 📖 핵심 컴포넌트

### 1. `create_app()`

모든 기능이 활성화된 FastAPI 애플리케이션을 생성하는 메인 함수입니다.

**파라미터:**
- `api_list`: APIRouter 인스턴스 목록
- `title`: API 제목
- `version`: API 버전
- `prefix_url`: 모든 라우트의 URL 접두사
- `graceful_timeout`: 종료 전 대기 시간(초) (기본값: 10)
- `docs_enable`: API 문서 활성화/비활성화 (기본값: True)
- `health_check_api`: 헬스 체크 엔드포인트 경로 (기본값: "/healthz")
- `startup_coroutines`: 시작 시 실행할 비동기 함수 목록
- `shutdown_coroutines`: 종료 시 실행할 비동기 함수 목록
- `stage`: 환경 스테이지 (dev/staging/prod)

### 2. `LoggingAPIRoute`

Trace ID와 함께 모든 요청과 응답을 자동으로 로깅하는 향상된 APIRoute 클래스입니다.

```python
from fastapi import APIRouter
from fastapi_kit import LoggingAPIRoute

router = APIRouter(route_class=LoggingAPIRoute)
```

### 3. `get_logger()`

사전 구성된 Loguru 로거 인스턴스를 가져옵니다.

```python
from fastapi_kit import get_logger

logger = get_logger()
logger.info("애플리케이션 시작됨")
logger.error("문제가 발생했습니다")
```

### 4. `BaseModel`

합리적인 기본값을 가진 향상된 Pydantic BaseModel입니다.

```python
from fastapi_kit import BaseModel

class UserRequest(BaseModel):
    name: str
    email: str
    age: int = 0
```

### 5. 예외 처리

커스터마이징 가능한 에러 응답과 함께 자동 예외 처리를 제공합니다.

```python
from fastapi_kit.exception import BadRequestHeaderError, InvalidAccessTokenError

# 커스텀 예외 발생
raise BadRequestHeaderError("잘못된 헤더 형식")
raise InvalidAccessTokenError("토큰 만료됨")
```

---

## 🔧 환경 변수

환경 변수를 사용하여 애플리케이션을 구성합니다:

```bash
# 로깅
export LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
export LOG_JSON=false              # JSON 로그는 true, 예쁜 로그는 false
export LOG_STRING_LENGTH=5000      # 로그 문자열 최대 길이

# 애플리케이션
export CONFIG_FILE=config.yaml     # 설정 파일 경로
```

---

## 📝 로깅 기능

FastAPI Kit은 고급 로깅 기능을 포함합니다:

- **구조화된 로깅**: JSON 또는 예쁘게 포맷된 로그
- **요청/응답 로깅**: 모든 API 호출 자동 로깅
- **Trace ID 전파**: OpenTelemetry로 서비스 간 요청 추적
- **컨텍스트 바인딩**: 로그 항목에 컨텍스트 정보 첨부
- **로그 절단**: 긴 로그 메시지 자동 절단
- **표준 라이브러리 통합**: uvicorn, fastapi 등의 로그 캡처

로그 출력 예제:
```
2024-12-28 22:30:15.123 | INFO  | app.py:main:42 | request | abc123def | GET | /api/v1/users | {"query": "active"}
2024-12-28 22:30:15.234 | INFO  | app.py:main:42 | response | abc123def | GET | /api/v1/users | 200 | {"users": [...]}
```

---

## 🎨 예제 애플리케이션

다음을 포함한 완전한 예제는 `example.py`를 참조하세요:
- 설정 관리
- 서비스 초기화
- 의존성 주입
- 커스텀 미들웨어
- 시작/종료 핸들러

---

## 🧪 테스트

```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 테스트 실행
pytest tests/

# 커버리지와 함께 실행
pytest tests/ --cov=fastapi_kit --cov-report=html
```

---

## 🛠️ 개발

```bash
# 저장소 클론
git clone https://github.com/bestend/fastapi-kit.git
cd fastapi-kit

# 개발 모드로 설치
pip install -e ".[dev]"

# 린팅 실행
ruff check src/ tests/

# 코드 포맷
ruff format src/ tests/

# 타입 체킹
mypy src/
```

---

## 📚 고급 사용법

### 커스텀 예외 핸들러

```python
from fastapi_kit.exception import ErrorInfo, get_exception_definitions

# 커스텀 예외 추가
class CustomError(Exception):
    pass

# 커스텀 에러 정보 등록
get_exception_definitions()[CustomError] = ErrorInfo(
    status_code=400,
    msg="커스텀 에러 발생",
    log_level="warning"
)
```

### 커스텀 미들웨어

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 전처리
        response = await call_next(request)
        # 후처리
        return response

app = create_app(
    [router],
    middlewares=[CustomMiddleware]
)
```

---

## 📚 예제

[examples/](./examples/) 디렉토리에서 완전하고 실행 가능한 예제를 확인할 수 있습니다:

### 1. [Simple Example](./examples/simple/)
로깅, 응답 형식화, 페이지네이션을 포함한 기본 사용법.

```bash
python examples/simple/app.py
# http://localhost:8000/v1/docs 접속
```

### 2. [Auth Example](./examples/auth/)
역할 기반 접근 제어를 포함한 OIDC/Keycloak 인증.

```bash
# 환경 변수 설정
export OIDC_ISSUER="https://keycloak.example.com/realms/myrealm"
export OIDC_CLIENT_ID="my-api"

python examples/auth/app.py
# http://localhost:8000/v1/docs 접속
```

### 3. [CORS Example](./examples/cors/)
환경별 CORS 설정 및 보안 모범 사례.

```bash
# 개발 환경
python examples/cors/app.py

# 프로덕션 환경
STAGE=prod ALLOWED_ORIGINS="https://myapp.com" python examples/cors/app.py
```

### 4. [External Auth Example](./examples/external_auth/)
API Gateway/Ingress 인증 및 Swagger UI Bearer token 지원.

```bash
python examples/external_auth/app.py
# http://localhost:8000/docs 접속
```

자세한 내용은 [examples/README.md](./examples/README.md)를 참조하세요.

---

## 🤝 기여하기

기여는 환영합니다! Pull Request를 자유롭게 제출해 주세요.

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스로 제공됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🙏 감사의 말

- [confee](https://github.com/bestend/confee)에서 영감을 받았습니다 - 올바른 설정 관리
- [FastAPI](https://fastapi.tiangolo.com/)로 구축 - 현대적이고 빠른 웹 프레임워크
- [Loguru](https://github.com/Delgan/loguru)로 로깅 - 간단한 Python 로깅



