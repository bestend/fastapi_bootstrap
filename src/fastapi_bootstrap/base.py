"""FastAPI application factory and configuration.

This module provides the main `create_app()` function that creates a fully
configured FastAPI application with logging, error handling, CORS, and more.
"""

import asyncio
import inspect
import logging
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

from fastapi_bootstrap.config import BootstrapSettings
from fastapi_bootstrap.exception.handler import add_exception_handler
from fastapi_bootstrap.log import get_logger, setup_logging

logger = get_logger()


def _suppress_uvicorn_loggers() -> None:
    """Suppress uvicorn and fastapi default loggers.

    This prevents duplicate log entries since we use our own logging setup.
    """
    loggers_to_suppress = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith("uvicorn.") or name.startswith("fastapi.")
    )
    for logger_instance in loggers_to_suppress:
        logger_instance.handlers = []


def _configure_openapi_security(
    schema: dict, add_bearer_auth: bool, swagger_ui_init_oauth: dict | None = None
) -> dict:
    """Add security schemes to OpenAPI schema.

    Args:
        schema: The OpenAPI schema dictionary
        add_bearer_auth: Whether to add bearer token authentication
        swagger_ui_init_oauth: OAuth2 configuration for Swagger UI

    Returns:
        Modified schema with security configuration
    """
    if not add_bearer_auth and not swagger_ui_init_oauth:
        return schema

    if "components" not in schema:
        schema["components"] = {}

    if "securitySchemes" not in schema["components"]:
        schema["components"]["securitySchemes"] = {}

    # Add Bearer Auth (for manual JWT token input)
    if add_bearer_auth or swagger_ui_init_oauth:
        schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token (from Keycloak or other OIDC provider)",
        }

    # OAuth2는 OIDCAuth가 자동으로 추가함 (auth.py의 OAuth2AuthorizationCodeBearer)
    # 여기서는 global security를 설정하지 않음 (각 엔드포인트가 선택)

    return schema


def _handle_path_rewrite(schema: dict, request: Request) -> dict:
    """Handle path rewriting for reverse proxy scenarios.

    When behind a reverse proxy, the X-Origin-Path header can be used
    to rewrite API paths in the OpenAPI schema.

    Args:
        schema: The OpenAPI schema dictionary
        request: The incoming request

    Returns:
        Modified schema with rewritten paths if applicable
    """
    if "X-Origin-Path" not in request.headers:
        return schema

    # Create a copy to avoid modifying the cached schema
    schema_copy = dict(schema)
    old_pattern = os.path.dirname(request.url.path)
    new_pattern = request.headers["X-Origin-Path"]

    # Rewrite all paths
    new_paths = {}
    for path, methods in schema_copy["paths"].items():
        new_paths[path.replace(old_pattern, new_pattern)] = methods
    schema_copy["paths"] = new_paths

    return schema_copy


def create_app(
    api_list: list[APIRouter],
    title: str = "",
    version: str = "",
    prefix_url: str = "",
    graceful_timeout: int = 10,
    *,
    settings: BootstrapSettings | None = None,
    dependencies: list[Any] | None = None,
    middlewares: list | None = None,
    startup_coroutines: list[Callable] | None = None,
    shutdown_coroutines: list[Callable] | None = None,
    health_check_api: str = "/healthz",
    metrics_api: str = "/metrics",
    docs_enable: bool = True,
    docs_prefix_url: str = "",
    add_external_basic_auth: bool = False,
    stage: str = "dev",
    cors_origins: list[str] | None = None,
    cors_allow_credentials: bool = True,
    cors_allow_methods: list[str] | None = None,
    cors_allow_headers: list[str] | None = None,
    swagger_ui_init_oauth: dict[str, Any] | None = None,
) -> FastAPI:
    """Create a FastAPI application with pre-configured features.

    This function creates a production-ready FastAPI app with:
    - Automatic request/response logging with trace IDs
    - Centralized exception handling
    - Health check endpoint
    - CORS middleware
    - Auto-generated API documentation
    - Graceful shutdown support

    Args:
        api_list: List of FastAPI APIRouter instances to include
        title: API title for documentation
        version: API version string
        prefix_url: URL prefix for all API routes (e.g., "/api/v1")
        graceful_timeout: Seconds to wait during graceful shutdown (default: 10)
        settings: Optional BootstrapSettings. If provided, its values are used as defaults
            and override per-argument values when explicitly set.
        dependencies: List of FastAPI dependencies to apply globally
        middlewares: List of Starlette middleware classes to add
        startup_coroutines: List of async functions to run on app startup
        shutdown_coroutines: List of async functions to run on app shutdown
        health_check_api: Path for health check endpoint (default: "/healthz")
        metrics_api: Path for metrics endpoint (default: "/metrics")
        docs_enable: Enable automatic API documentation (default: True)
        docs_prefix_url: URL prefix for docs (defaults to prefix_url)
        add_external_basic_auth: Add bearer auth to OpenAPI schema (default: False)
        stage: Environment stage - "dev", "staging", or "prod" (default: "dev")
        cors_origins: List of allowed origins. None = auto-configure by stage
        cors_allow_credentials: Allow credentials in CORS requests (default: True)
        cors_allow_methods: Allowed HTTP methods. None = auto-configure by stage
        cors_allow_headers: Allowed headers. None = auto-configure by stage
        swagger_ui_init_oauth: OAuth2 configuration for Swagger UI (default: None)
            Example: {"clientId": "my-client", "usePkceWithAuthorizationCodeGrant": True}

    Returns:
        Configured FastAPI application instance

    Example:
        ```python
        from fastapi import APIRouter
        from fastapi_bootstrap import create_app, LoggingAPIRoute

        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/hello")
        async def hello():
            return {"message": "Hello, World!"}

        # Development - permissive CORS
        app = create_app(
            [router],
            title="My API",
            version="1.0.0",
            stage="dev"
        )

        # Production - strict CORS
        app = create_app(
            [router],
            title="My API",
            version="1.0.0",
            stage="prod",
            cors_origins=["https://myapp.com", "https://www.myapp.com"]
        )
        ```
    """
    if settings is not None:
        title = settings.title
        version = settings.version
        stage = settings.stage
        health_check_api = settings.health_check.endpoint
        graceful_timeout = settings.graceful_shutdown.timeout

        cors_config = settings.get_cors_config_for_stage()
        cors_origins = cors_config.origins
        cors_allow_credentials = cors_config.allow_credentials
        cors_allow_methods = cors_config.allow_methods
        cors_allow_headers = cors_config.allow_headers

    # Initialize default values for mutable arguments
    if dependencies is None:
        dependencies = []
    if middlewares is None:
        middlewares = []
    if startup_coroutines is None:
        startup_coroutines = []
    if shutdown_coroutines is None:
        shutdown_coroutines = []

    # Configure CORS settings based on environment stage if not explicitly set
    if cors_origins is None:
        if stage == "prod":
            # Production: Require explicit origin configuration
            cors_origins = []
            logger.warning(
                "CORS origins not specified for production. "
                "Please set cors_origins explicitly for security. "
                "No origins will be allowed by default."
            )
        elif stage == "staging":
            # Staging: Allow specific common patterns but warn
            cors_origins = ["https://*.staging.example.com"]
            logger.info("CORS origins auto-configured for staging environment")
        else:  # dev
            # Development: Allow all origins for convenience
            cors_origins = ["*"]
            logger.info("CORS origins set to '*' for development (not for production!)")

    if cors_allow_methods is None:
        # Production: Only common safe methods; Development/Staging: All methods
        cors_allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"] if stage == "prod" else ["*"]

    if cors_allow_headers is None:
        # Production: Only common headers; Development/Staging: All headers
        cors_allow_headers = (
            ["Content-Type", "Authorization", "X-Request-ID"] if stage == "prod" else ["*"]
        )

    # Set docs prefix to match API prefix if not specified
    if docs_prefix_url == "":
        docs_prefix_url = prefix_url

    # Calculate documentation endpoint URLs
    docs_api = f"{docs_prefix_url}/docs" if docs_prefix_url else "/docs"
    redoc_api = f"{docs_prefix_url}/redoc" if docs_prefix_url else "/redoc"
    openapi_api = f"{docs_prefix_url}/openapi.json" if docs_prefix_url else "/openapi.json"
    oauth2_redirect = (
        f"{docs_prefix_url}/docs/oauth2-redirect" if docs_prefix_url else "/docs/oauth2-redirect"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager.

        Handles startup and shutdown events:
        - Suppresses default loggers
        - Sets up custom logging
        - Runs user-defined startup coroutines
        - Waits for graceful shutdown
        - Runs user-defined shutdown coroutines
        """
        # Suppress default uvicorn/fastapi loggers
        _suppress_uvicorn_loggers()

        # Setup custom logging with FastAPI request/response format
        setup_logging(use_fastapi_format=True)

        # Run user-defined startup coroutines
        for coroutine in startup_coroutines:
            # Check if the coroutine accepts an app parameter
            sig = inspect.signature(coroutine)
            if len(sig.parameters) > 0:
                await coroutine(app)
            else:
                await coroutine()

        yield

        # Graceful shutdown - wait for in-flight requests to complete
        if graceful_timeout > 0:
            logger.info(f"Graceful shutdown initiated, waiting {graceful_timeout}s...")
            await asyncio.sleep(graceful_timeout)
        else:
            logger.info("Graceful shutdown initiated (no delay)")

        # Run user-defined shutdown coroutines
        for coroutine in shutdown_coroutines:
            # Check if the coroutine accepts an app parameter
            sig = inspect.signature(coroutine)
            if len(sig.parameters) > 0:
                await coroutine(app)
            else:
                await coroutine()

    # Create FastAPI application instance
    app = FastAPI(
        title=title,
        version=version,
        openapi_url="",  # Disable default OpenAPI URL (we'll set it up manually)
        docs_url="",  # Disable default docs URL (we'll set it up manually)
        redoc_url="",  # Disable default redoc URL (we'll set it up manually)
        lifespan=lifespan,
        swagger_ui_oauth2_redirect_url=oauth2_redirect,  # Use calculated redirect URL
    )

    # Include all API routers with optional dependencies and URL prefix
    for api in api_list:
        app.include_router(api, dependencies=dependencies, prefix=prefix_url)

    # Add CORS middleware with environment-aware defaults
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_allow_credentials,
        allow_methods=cors_allow_methods,
        allow_headers=cors_allow_headers,
    )

    # Add centralized exception handler
    add_exception_handler(app, stage)

    # Add custom middlewares (processed in reverse order)
    for middleware in middlewares:
        app.add_middleware(middleware)

    # Health check endpoint (not included in API documentation)
    @app.get(health_check_api, include_in_schema=False)
    async def healthcheck():
        """Simple health check endpoint.

        Returns:
            Plain text "OK" response
        """
        return Response(content="OK", media_type="text/plain")

    # Setup API documentation if enabled
    if docs_enable:
        # Redirect root or prefix URL to Swagger docs
        if docs_prefix_url:

            @app.get(docs_prefix_url, include_in_schema=False)
            async def docs_redirect():
                """Redirect prefix URL to Swagger documentation."""
                return RedirectResponse(docs_api)
        else:

            @app.get("/", include_in_schema=False)
            async def root_docs_redirect():
                """Redirect root URL to Swagger documentation."""
                return RedirectResponse(docs_api)

        # Swagger UI endpoint
        @app.get(docs_api, include_in_schema=False)
        async def custom_swagger_ui_html():
            """Serve Swagger UI for interactive API documentation."""
            return get_swagger_ui_html(
                openapi_url="openapi.json",
                title=app.title + " - Swagger UI",
                oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                init_oauth=swagger_ui_init_oauth,  # OAuth2 configuration
            )

        # OAuth2 redirect for Swagger UI
        if app.swagger_ui_oauth2_redirect_url:

            @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
            async def swagger_ui_redirect():
                """Handle OAuth2 redirect for Swagger UI."""
                return get_swagger_ui_oauth2_redirect_html()

        # ReDoc endpoint (alternative documentation UI)
        @app.get(redoc_api, include_in_schema=False)
        async def redoc_html():
            """Serve ReDoc for alternative API documentation."""
            return get_redoc_html(
                openapi_url="openapi.json",
                title=app.title + " - ReDoc",
            )

        # Generate OpenAPI schema
        raw_openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=app.servers,
        )

        # Add security schemes if requested
        raw_openapi_schema = _configure_openapi_security(
            raw_openapi_schema, add_external_basic_auth, swagger_ui_init_oauth
        )

        # OpenAPI JSON endpoint
        @app.get(openapi_api, include_in_schema=False)
        async def openapi_json(request: Request):
            """Serve OpenAPI schema as JSON.

            Supports path rewriting via X-Origin-Path header for reverse proxy scenarios.
            """
            openapi_schema = _handle_path_rewrite(raw_openapi_schema, request)
            return JSONResponse(openapi_schema)

    return app
