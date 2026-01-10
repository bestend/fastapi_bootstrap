"""Builder pattern API for FastAPI Bootstrap.

This module provides a fluent builder interface for creating FastAPI applications
with a more intuitive and chainable API.

Example:
    ```python
    from fastapi_bootstrap.builder import FastAPIBootstrap

    app = (
        FastAPIBootstrap()
        .title("My API")
        .version("1.0.0")
        .stage("prod")
        .with_logging(level="INFO", json_output=True)
        .with_cors(origins=["https://myapp.com"])
        .with_security_headers()
        .with_metrics()
        .with_auth(oidc_config)
        .add_router(router)
        .build()
    )
    ```
"""

from collections.abc import Callable
from typing import Any, Self

from fastapi import APIRouter, FastAPI

from fastapi_bootstrap.base import create_app
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    GracefulShutdownSettings,
    HealthCheckSettings,
    LogFormat,
    LoggingSettings,
    MetricsSettings,
    RateLimitSettings,
    SecuritySettings,
    Stage,
)


class FastAPIBootstrap:
    """Fluent builder for creating FastAPI applications.

    This class provides a chainable API for configuring and creating
    production-ready FastAPI applications with all the features of
    fastapi_bootstrap.

    Example:
        ```python
        # Simple usage
        app = (
            FastAPIBootstrap()
            .title("My API")
            .version("1.0.0")
            .add_router(router)
            .build()
        )

        # Full configuration
        app = (
            FastAPIBootstrap()
            .title("Production API")
            .version("2.0.0")
            .description("A production-ready API")
            .stage("prod")
            .prefix("/api/v2")
            .with_logging(level="WARNING", json_output=True)
            .with_cors(
                origins=["https://myapp.com"],
                allow_credentials=True,
            )
            .with_security_headers(
                hsts_max_age=31536000,
                content_security_policy="default-src 'self'",
            )
            .with_metrics(endpoint="/metrics")
            .with_health_check(endpoint="/health")
            .with_graceful_shutdown(timeout=30)
            .add_router(users_router, prefix="/users")
            .add_router(posts_router, prefix="/posts")
            .on_startup(init_database)
            .on_shutdown(cleanup_database)
            .build()
        )
        ```
    """

    def __init__(self):
        """Initialize the builder with default settings."""
        self._settings = BootstrapSettings()
        self._routers: list[tuple[APIRouter, str | None, list[Any] | None]] = []
        self._middlewares: list[Any] = []
        self._startup_coroutines: list[Callable] = []
        self._shutdown_coroutines: list[Callable] = []
        self._dependencies: list[Any] = []
        self._prefix_url: str = ""
        self._docs_enable: bool = True
        self._docs_prefix_url: str = ""
        self._add_bearer_auth: bool = False
        self._swagger_ui_init_oauth: dict[str, Any] | None = None
        self._oidc_config: Any = None
        self._enable_security_headers: bool = False
        self._security_headers_config: dict[str, Any] = {}
        self._enable_metrics: bool = False
        self._enable_request_id: bool = False
        self._enable_request_timing: bool = False

    def title(self, title: str) -> Self:
        """Set the API title.

        Args:
            title: API title for documentation

        Returns:
            Self for chaining
        """
        self._settings.title = title
        return self

    def version(self, version: str) -> Self:
        """Set the API version.

        Args:
            version: API version string

        Returns:
            Self for chaining
        """
        self._settings.version = version
        return self

    def description(self, description: str) -> Self:
        """Set the API description.

        Args:
            description: API description for documentation

        Returns:
            Self for chaining
        """
        self._settings.description = description
        return self

    def stage(self, stage: str | Stage) -> Self:
        """Set the application stage.

        Args:
            stage: Environment stage ("dev", "staging", or "prod")

        Returns:
            Self for chaining
        """
        if isinstance(stage, str):
            stage = Stage(stage.lower())
        self._settings.stage = stage
        return self

    def prefix(self, prefix: str) -> Self:
        """Set the URL prefix for all routes.

        Args:
            prefix: URL prefix (e.g., "/api/v1")

        Returns:
            Self for chaining
        """
        self._prefix_url = prefix
        return self

    def with_logging(
        self,
        level: str = "INFO",
        json_output: bool = False,
        max_string_length: int = 5000,
        truncation_threshold: int = 2000,
    ) -> Self:
        """Configure logging settings.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            json_output: Enable JSON log output
            max_string_length: Maximum length for logged strings
            truncation_threshold: Threshold for truncating strings in structures

        Returns:
            Self for chaining
        """
        self._settings.logging = LoggingSettings(
            level=level,
            format=LogFormat.JSON if json_output else LogFormat.TEXT,
            json_output=json_output,
            string_max_length=max_string_length,
            truncation_threshold=truncation_threshold,
        )
        return self

    def with_cors(
        self,
        origins: list[str] | None = None,
        allow_credentials: bool = True,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        max_age: int = 600,
    ) -> Self:
        """Configure CORS settings.

        Args:
            origins: Allowed origins (None for stage-based defaults)
            allow_credentials: Allow credentials in CORS requests
            allow_methods: Allowed HTTP methods
            allow_headers: Allowed HTTP headers
            expose_headers: Headers to expose to browser
            max_age: Max age for preflight cache

        Returns:
            Self for chaining
        """
        self._settings.cors = CORSSettings(
            origins=origins or [],
            allow_credentials=allow_credentials,
            allow_methods=allow_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=allow_headers or ["*"],
            expose_headers=expose_headers or ["X-Request-ID", "X-Trace-ID"],
            max_age=max_age,
        )
        return self

    def with_security_headers(
        self,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        content_security_policy: str | None = "default-src 'self'",
        x_frame_options: str = "DENY",
        enable_in_dev: bool = False,
    ) -> Self:
        """Enable security headers middleware.

        Args:
            hsts_max_age: HSTS max-age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            content_security_policy: CSP header value
            x_frame_options: X-Frame-Options value
            enable_in_dev: Enable in development mode

        Returns:
            Self for chaining
        """
        self._enable_security_headers = True
        self._security_headers_config = {
            "hsts_max_age": hsts_max_age,
            "hsts_include_subdomains": hsts_include_subdomains,
            "content_security_policy": content_security_policy,
            "x_frame_options": x_frame_options,
            "enable_in_dev": enable_in_dev,
        }
        return self

    def with_metrics(
        self,
        endpoint: str = "/metrics",
        include_in_schema: bool = False,
    ) -> Self:
        """Enable Prometheus metrics.

        Args:
            endpoint: Metrics endpoint path
            include_in_schema: Include in OpenAPI schema

        Returns:
            Self for chaining
        """
        self._enable_metrics = True
        self._settings.metrics = MetricsSettings(
            enabled=True,
            endpoint=endpoint,
            include_in_schema=include_in_schema,
        )
        return self

    def with_health_check(
        self,
        endpoint: str = "/healthz",
        include_in_schema: bool = False,
    ) -> Self:
        """Configure health check endpoint.

        Args:
            endpoint: Health check endpoint path
            include_in_schema: Include in OpenAPI schema

        Returns:
            Self for chaining
        """
        self._settings.health_check = HealthCheckSettings(
            endpoint=endpoint,
            include_in_schema=include_in_schema,
        )
        return self

    def with_graceful_shutdown(self, timeout: int = 10) -> Self:
        """Configure graceful shutdown.

        Args:
            timeout: Seconds to wait for in-flight requests

        Returns:
            Self for chaining
        """
        self._settings.graceful_shutdown = GracefulShutdownSettings(timeout=timeout)
        return self

    def with_rate_limit(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ) -> Self:
        """Enable rate limiting.

        Args:
            requests_per_minute: Max requests per minute per client
            burst_size: Allowed burst above limit

        Returns:
            Self for chaining
        """
        self._settings.rate_limit = RateLimitSettings(
            enabled=True,
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
        )
        return self

    def with_request_id(self, header_name: str = "X-Request-ID") -> Self:
        """Enable request ID middleware.

        Args:
            header_name: Header name for request ID

        Returns:
            Self for chaining
        """
        self._enable_request_id = True
        return self

    def with_request_timing(self, header_name: str = "X-Response-Time") -> Self:
        """Enable request timing middleware.

        Args:
            header_name: Header name for response time

        Returns:
            Self for chaining
        """
        self._enable_request_timing = True
        return self

    def with_auth(self, oidc_config: Any, enable_swagger_ui: bool = True) -> Self:
        """Configure OIDC authentication.

        Args:
            oidc_config: OIDCConfig instance
            enable_swagger_ui: Enable OAuth2 flow in Swagger UI

        Returns:
            Self for chaining
        """
        self._oidc_config = oidc_config
        self._add_bearer_auth = True
        if enable_swagger_ui and oidc_config:
            self._swagger_ui_init_oauth = {
                "clientId": oidc_config.client_id,
                "usePkceWithAuthorizationCodeGrant": True,
            }
        return self

    def with_docs(
        self,
        enable: bool = True,
        prefix_url: str = "",
    ) -> Self:
        """Configure API documentation.

        Args:
            enable: Enable docs endpoints
            prefix_url: URL prefix for docs

        Returns:
            Self for chaining
        """
        self._docs_enable = enable
        self._docs_prefix_url = prefix_url
        return self

    def add_router(
        self,
        router: APIRouter,
        prefix: str = "",
        dependencies: list[Any] | None = None,
    ) -> Self:
        """Add an API router.

        Args:
            router: FastAPI APIRouter instance
            prefix: Optional prefix for this router
            dependencies: Optional dependencies for this router

        Returns:
            Self for chaining
        """
        self._routers.append((router, prefix, dependencies))
        return self

    def add_middleware(self, middleware: Any, **kwargs: Any) -> Self:
        """Add a custom middleware.

        Args:
            middleware: Middleware class
            **kwargs: Middleware configuration

        Returns:
            Self for chaining
        """
        self._middlewares.append((middleware, kwargs))
        return self

    def add_dependency(self, dependency: Any) -> Self:
        """Add a global dependency.

        Args:
            dependency: FastAPI dependency

        Returns:
            Self for chaining
        """
        self._dependencies.append(dependency)
        return self

    def on_startup(self, coroutine: Callable) -> Self:
        """Add a startup coroutine.

        Args:
            coroutine: Async function to run on startup

        Returns:
            Self for chaining
        """
        self._startup_coroutines.append(coroutine)
        return self

    def on_shutdown(self, coroutine: Callable) -> Self:
        """Add a shutdown coroutine.

        Args:
            coroutine: Async function to run on shutdown

        Returns:
            Self for chaining
        """
        self._shutdown_coroutines.append(coroutine)
        return self

    def build(self) -> FastAPI:
        """Build the FastAPI application.

        Returns:
            Configured FastAPI application instance
        """
        # Prepare routers - combine with individual prefixes
        api_list = []
        for router, prefix, deps in self._routers:
            if prefix:
                # Create a new router with the combined prefix
                combined_router = APIRouter()
                combined_router.include_router(router, prefix=prefix)
                api_list.append(combined_router)
            else:
                api_list.append(router)

        # Get CORS config based on stage
        cors_config = self._settings.get_cors_config_for_stage()

        # Create base app using create_app
        app = create_app(
            api_list=api_list,
            title=self._settings.title,
            version=self._settings.version,
            prefix_url=self._prefix_url,
            graceful_timeout=self._settings.graceful_shutdown.timeout,
            dependencies=self._dependencies if self._dependencies else None,
            startup_coroutines=self._startup_coroutines if self._startup_coroutines else None,
            shutdown_coroutines=self._shutdown_coroutines if self._shutdown_coroutines else None,
            health_check_api=self._settings.health_check.endpoint,
            metrics_api=self._settings.metrics.endpoint,
            docs_enable=self._docs_enable,
            docs_prefix_url=self._docs_prefix_url,
            add_external_basic_auth=self._add_bearer_auth,
            stage=self._settings.stage.value
            if isinstance(self._settings.stage, Stage)
            else self._settings.stage,
            cors_origins=cors_config.origins if cors_config.origins else None,
            cors_allow_credentials=cors_config.allow_credentials,
            cors_allow_methods=cors_config.allow_methods if cors_config.allow_methods else None,
            cors_allow_headers=cors_config.allow_headers if cors_config.allow_headers else None,
            swagger_ui_init_oauth=self._swagger_ui_init_oauth,
        )

        # Add security headers middleware if enabled
        if self._enable_security_headers:
            from fastapi_bootstrap.middleware import SecurityHeadersMiddleware

            app.add_middleware(
                SecurityHeadersMiddleware,
                stage=self._settings.stage.value
                if isinstance(self._settings.stage, Stage)
                else self._settings.stage,
                **self._security_headers_config,
            )

        # Add request ID middleware if enabled
        if self._enable_request_id:
            from fastapi_bootstrap.middleware import RequestIDMiddleware

            app.add_middleware(RequestIDMiddleware)

        # Add request timing middleware if enabled
        if self._enable_request_timing:
            from fastapi_bootstrap.middleware import RequestTimingMiddleware

            app.add_middleware(RequestTimingMiddleware)

        # Add metrics middleware if enabled
        if self._enable_metrics:
            from fastapi_bootstrap.metrics import MetricsMiddleware, get_metrics_router

            app.add_middleware(MetricsMiddleware)
            app.include_router(
                get_metrics_router(
                    path=self._settings.metrics.endpoint,
                    include_in_schema=self._settings.metrics.include_in_schema,
                )
            )

        # Add custom middlewares
        for middleware, kwargs in self._middlewares:
            app.add_middleware(middleware, **kwargs)

        return app


# Convenient function to create a builder
def bootstrap() -> FastAPIBootstrap:
    """Create a new FastAPIBootstrap builder.

    Returns:
        FastAPIBootstrap instance for chaining

    Example:
        ```python
        from fastapi_bootstrap.builder import bootstrap

        app = bootstrap().title("My API").add_router(router).build()
        ```
    """
    return FastAPIBootstrap()


__all__ = ["FastAPIBootstrap", "bootstrap"]
