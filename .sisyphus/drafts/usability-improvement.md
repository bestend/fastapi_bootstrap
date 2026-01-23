# Draft: FastAPI Bootstrap 사용성 개선

## 현재 상황 요약

**프로젝트 타입**: FastAPI Bootstrap 라이브러리 (다른 프로젝트에서 import해서 사용)
**핵심 기능**: `create_app()` 팩토리로 프로덕션 레디 앱 빠르게 생성

---

## 사용자가 언급한 문제점

- [x] **하드코딩된 기능들**: 유연성 부족 → 탐색 결과 참고
- [x] 문서 개선 필요

---

## 탐색 결과 종합

### 1. 개발자 경험 (DX) 문제점

| 영역 | 현재 상태 | 문제점 |
|------|----------|--------|
| **개발 도구** | Makefile 없음 | 공통 명령어(테스트, 린트, 서버) 수동 실행 필요 |
| **컨테이너** | Dockerfile 없음 | 배포 가이드 부재 |
| **패키지 관리** | pip 사용 | uv 지원 없음 (글로벌 설정과 불일치) |
| **개발 서버** | uvicorn 직접 실행 | 래퍼 스크립트 없음 |

### 2. 설정 복잡성 (핵심 문제)

**`create_app()`에 25개 이상 파라미터** - 이게 "하드코딩된 기능"으로 느껴질 수 있음:
- 두 가지 설정 방식 혼재: `BootstrapSettings` vs 개별 파라미터
- 예제 간 불일치: `api_list` vs `routers`
- deprecated 필드 존재 (`json_output`)

### 3. 온보딩 마찰점

**명확하지 않은 부분:**
- `LoggingAPIRoute`를 써야 로깅이 되는데, 이게 명확하지 않음
- OIDC 설정이 복잡함 (JWKS, issuer, audience 이해 필요)
- External auth 설정 방법 불명확
- 메트릭스 미들웨어 수동 추가 필요

### 4. 문서 갭

| 부족한 문서 | 영향 |
|------------|------|
| 개발 워크플로우 가이드 | 로컬 개발 시작 어려움 |
| Docker/배포 예제 | 프로덕션 배포 막막 |
| 트러블슈팅 가이드 | 문제 해결 어려움 |
| 설정 마이그레이션 가이드 | 파라미터 → Settings 전환 혼란 |
| CONTRIBUTING.md | 기여 방법 불명확 |

### 5. 하드코딩 (경미)

- 예제 port/host 고정 (예제라서 OK)
- JWKS 캐시 TTL 1시간 고정
- Staging CORS 패턴 고정

---

## 개선 방향 (우선순위별)

### 🔴 높은 우선순위

1. **Makefile 추가** - 공통 명령어 (dev, test, lint, format)
2. **Dockerfile + docker-compose** - 컨테이너 개발/배포
3. **uv 지원** - lockfile, `uv sync` 지원
4. **create_app API 단순화** - 파라미터 줄이기 또는 프리셋 제공
5. **개발 환경 설정 가이드** - README에 로컬 개발 워크플로우 추가

### 🟡 중간 우선순위

6. **예제 패턴 통일** - 파라미터 이름, 구조 일관성
7. **설정 마이그레이션 가이드** - 파라미터 → Settings 전환 문서
8. **트러블슈팅 섹션** - 일반적인 문제와 해결법
9. **CONTRIBUTING.md** - 기여 가이드

### 🟢 낮은 우선순위

10. **deprecated 필드 정리**
11. **아키텍처 다이어그램**
12. **대화형 설정 마법사** (CLI)

---

## 확정된 결정사항

### API 단순화
- **방향**: Settings 완전 통합
- **하위 호환성**: 브레이킹 체인지 OK (마이그레이션 가이드 제공)
- **목표**: `create_app(routers, settings=...)` 형태로 단순화

### 문서 개선
- **우선순위 1**: README 전면 개편
- **우선순위 2**: 예제 통일 및 확장
- **우선순위 3**: API 레퍼런스 정리
- **우선순위 4**: CONTRIBUTING.md

## 테스트 전략 (확정)

- **방식**: TDD (테스트 먼저 작성)
- **인프라**: pytest (이미 구성됨)
- **실행**: `pytest -v --cov=fastapi_bootstrap`
- **패턴**: `tests/test_*.py`

---

## 최종 결정사항 (Metis 자문 후 확정)

### 설정 구조
- **방향**: Sub-config 생성
- **추가할 것**: `DocsSettings`, `SwaggerSettings` (또는 통합)
- `prefix_url`도 적절한 위치에 추가

### 파라미터 변경
- `api_list` → `routers` 이름 변경 (Breaking change)

### Deprecation 전략
- **즉시 제거** (clean break)
- 마이그레이션 가이드 제공

### 문서 언어
- **영어/한국어 동시 업데이트**

---

## 실행 플랜

### Phase 1: BootstrapSettings 확장 (config.py)
1. `DocsSettings` sub-config 생성
   - `enabled: bool = True`
   - `prefix_url: str = ""`
   - `swagger_oauth: dict | None = None`
2. `prefix_url: str = ""` 루트에 추가
3. `SecuritySettings`에 `add_external_basic_auth: bool = False` 추가
4. 테스트 작성

### Phase 2: create_app 시그니처 변경 (base.py)
1. 새 시그니처 테스트 먼저 작성 (TDD)
2. `api_list` → `routers` 이름 변경
3. 개별 파라미터 제거, settings에서 읽도록 변경
4. 남길 파라미터: `routers`, `settings`, `dependencies`, `middlewares`, `startup_coroutines`, `shutdown_coroutines`

### Phase 3: Examples 업데이트 (examples/**/app.py)
1. 모든 example을 새 시그니처로 변경
2. 각 example의 README.md 업데이트

### Phase 4: Documentation 개편
1. README.md / README.ko.md - Quick start 중심으로 개편
2. ADVANCED.md - API Reference 정리
3. Migration Guide 추가 (MIGRATION.md 또는 CHANGELOG)
4. CONTRIBUTING.md 신규 작성

---

## CLEARANCE CHECK ✅

- [x] Core objective: Settings 완전 통합 + 문서 대폭 개편
- [x] Scope boundaries: 브레이킹 체인지 OK, 문서 4종, 양쪽 언어
- [x] No critical ambiguities: 모든 세부사항 확정
- [x] Technical approach: Sub-config + 즉시 제거
- [x] Test strategy: TDD
- [x] No blocking questions: 없음

**→ 실행 준비 완료**

---

## Scope Boundaries

### ✅ INCLUDE (사용자 선택)
- [x] **create_app API 단순화** - 핵심 개선
- [x] **문서 대폭 개선** - 핵심 개선

### ❌ EXCLUDE (이번 범위 아님)
- [ ] Makefile 추가 - 나중에
- [ ] Dockerfile 추가 - 나중에
- [ ] uv 지원 - 나중에
- [ ] Loguru 외 로깅 라이브러리 지원 - 제외
- [ ] 새로운 기능 추가 - 제외

---

## 상세 논의: create_app API 단순화

### 현재 상태 분석 (완료)

**create_app() 파라미터 21개:**

| 카테고리 | 파라미터 | 용도 |
|---------|---------|------|
| **필수** | `api_list` | 라우터 목록 |
| **메타데이터** | `title`, `version` | 앱 정보 |
| **URL** | `prefix_url`, `docs_prefix_url` | 경로 프리픽스 |
| **CORS (5개)** | `cors_origins`, `cors_allow_credentials`, `cors_allow_methods`, `cors_allow_headers`, `stage` | CORS 설정 |
| **기능 경로** | `health_check_api`, `metrics_api` | 엔드포인트 경로 |
| **미들웨어** | `middlewares`, `dependencies` | 커스텀 미들웨어/의존성 |
| **라이프사이클** | `startup_coroutines`, `shutdown_coroutines`, `graceful_timeout` | 시작/종료 |
| **문서** | `docs_enable`, `add_external_basic_auth`, `swagger_ui_init_oauth` | API 문서 |
| **설정 객체** | `settings` | BootstrapSettings (부분 오버라이드) |

**핵심 문제: Settings가 있어도 부분 오버라이드만 됨**
```python
# settings가 제공되면 오버라이드되는 것:
title, version, stage, health_check_api, graceful_timeout, cors_*

# 여전히 파라미터로 전달해야 하는 것:
prefix_url, middlewares, dependencies, startup/shutdown_coroutines,
metrics_api, docs_*, swagger_ui_init_oauth
```

### 단순화 방향 후보

**1. Settings 완전 통합 (권장)**
```python
# 모든 설정을 Settings에 통합
app = create_app(routers, settings=BootstrapSettings(...))

# 또는 환경변수에서 자동 로드
app = create_app(routers)  # settings = BootstrapSettings.from_env() 자동
```

**2. 프리셋 패턴**
```python
app = create_app(routers, preset="minimal")    # 로깅만
app = create_app(routers, preset="standard")   # 로깅 + CORS + 헬스체크
app = create_app(routers, preset="production") # 전체 + 보안 헤더
```

**3. 빌더 패턴**
```python
app = (AppBuilder(routers)
    .title("My API")
    .with_cors(origins=["*"])
    .with_metrics()
    .build())
```

**4. 하이브리드 (Settings + 프리셋)**
```python
app = create_app(routers, preset="production", settings=custom_settings)
```

---

## 상세 논의: 문서 대폭 개선

### 문서 개선 후보
1. **개발 워크플로우 가이드** - 로컬 개발 시작부터 끝까지
2. **트러블슈팅 섹션** - 일반적인 문제와 해결법
3. **예제 패턴 통일** - 일관된 구조와 설명
4. **설정 마이그레이션 가이드** - 파라미터 → Settings
5. **아키텍처 다이어그램** - 컴포넌트 관계 시각화
6. **CONTRIBUTING.md** - 기여 가이드
