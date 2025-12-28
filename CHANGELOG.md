# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

