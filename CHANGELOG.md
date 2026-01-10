# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-10

### Added


#### Configuration Management
- `BootstrapSettings` - Centralized Pydantic-based configuration class
- `LoggingSettings`, `CORSSettings`, `SecuritySettings` - Typed configuration models
- `get_settings()` - Cached settings loader from environment variables
- `mask_sensitive_data()` - Utility for masking sensitive fields in logs

#### Security Middleware
- `SecurityHeadersMiddleware` - HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- `RequestIDMiddleware` - Automatic request ID generation and propagation
- `RequestTimingMiddleware` - Response time tracking (X-Response-Time header)
- `MaxRequestSizeMiddleware` - Request body size limiting

#### Prometheus Metrics
- `MetricsMiddleware` - Automatic request metrics collection
- `get_metrics_router()` - Prometheus-compatible `/metrics` endpoint
- `MetricsRegistry` - Counter, Gauge, Histogram implementations
- Request count, latency histogram, in-progress requests, error tracking


### Changed
- Updated minimum dependency versions for better compatibility
- Status upgraded from Alpha to Beta
- Enhanced `__init__.py` exports for easier imports

### Fixed
- Various type hints improvements

## [0.1.2] - 2026-01-05

### Fixed
- Minor bug fixes and improvements

## [0.1.1] - 2026-01-02

### Changed
- Improved logging module structure and organization
- Enhanced OpenTelemetry integration with optional dependency support

### Removed
- Internal cleanup: removed unused utility files

## [0.1.0] - 2024-12-29

### Added

#### Core Features
- `create_app()` - FastAPI application factory with batteries included
- `LoggingAPIRoute` - Automatic request/response logging
- `ResponseFormatter` - Standardized response format (success, error, paginated)
- Structured logging with Loguru integration
- OpenTelemetry trace ID support
- Centralized exception handling
- Health check endpoint (`/healthz`)
- Graceful shutdown support
- Environment-based configuration (dev/staging/prod)

#### Authentication
- `OIDCAuth` - OIDC/OAuth2 integration (Keycloak, Auth0, Google, Azure AD)
- `OIDCConfig` - OIDC configuration with auto-discovery
- `TokenPayload` - JWT token payload with user info
- Role-based access control (RBAC)
- Group-based access control
- Optional authentication support
- Dual authentication in Swagger UI:
  - OAuth2 Authorization Code Flow (automatic login)
  - Bearer Token (manual JWT input)

#### CORS & Security
- Environment-based CORS configuration
- `add_external_basic_auth` - API Gateway/Ingress authentication support
- Secure production defaults

#### Type Safety
- Pydantic V2 based models
- Full type hints support

#### Examples
- Simple - Basic usage with logging and response formatting
- Auth - OIDC authentication with Keycloak
- CORS - Environment-specific CORS configuration
- External Auth - API Gateway authentication pattern

