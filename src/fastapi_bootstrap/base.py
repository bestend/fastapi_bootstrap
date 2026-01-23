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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

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
    routers: list[APIRouter],
    settings: BootstrapSettings | None = None,
    *,
    dependencies: list[Any] | None = None,
    middlewares: list | None = None,
    startup_coroutines: list[Callable] | None = None,
    shutdown_coroutines: list[Callable] | None = None,
    exception_handlers: dict[type[Exception] | int, Callable] | None = None,
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
        routers: List of FastAPI APIRouter instances to include
        settings: BootstrapSettings for configuration. If None, uses defaults.
        dependencies: List of FastAPI dependencies to apply globally
        middlewares: List of Starlette middleware classes to add
        startup_coroutines: List of async functions to run on app startup
        shutdown_coroutines: List of async functions to run on app shutdown
        exception_handlers: Dictionary mapping exception types or HTTP status codes
            to handler functions. These handlers take precedence over default handlers.
            Example: {HTTPException: my_http_exception_handler, 404: my_404_handler}

    Returns:
        Configured FastAPI application instance

    Example:
        ```python
        from fastapi import APIRouter
        from fastapi_bootstrap import create_app, LoggingAPIRoute
        from fastapi_bootstrap.config import BootstrapSettings, CORSSettings, Stage

        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/hello")
        async def hello():
            return {"message": "Hello, World!"}

        # Development - permissive CORS (default)
        app = create_app(routers=[router])

        # Production - strict CORS
        settings = BootstrapSettings(
            title="My API",
            version="1.0.0",
            stage=Stage.PROD,
            cors=CORSSettings(origins=["https://myapp.com"]),
        )
        app = create_app(routers=[router], settings=settings)
        ```
    """
    if settings is None:
        settings = BootstrapSettings()

    title = settings.title
    version = settings.version
    stage = settings.stage
    prefix_url = settings.prefix_url
    health_check_api = settings.health_check.endpoint
    graceful_timeout = settings.graceful_shutdown.timeout
    docs_enable = settings.docs.enabled
    docs_prefix_url = settings.docs.prefix_url
    swagger_ui_init_oauth = settings.docs.swagger_oauth
    add_external_basic_auth = settings.security.add_external_basic_auth

    cors_config = settings.get_cors_config_for_stage()
    cors_origins = cors_config.origins
    cors_allow_credentials = cors_config.allow_credentials
    cors_allow_methods = cors_config.allow_methods
    cors_allow_headers = cors_config.allow_headers

    if dependencies is None:
        dependencies = []
    if middlewares is None:
        middlewares = []
    if startup_coroutines is None:
        startup_coroutines = []
    if shutdown_coroutines is None:
        shutdown_coroutines = []

    if not cors_origins and stage == "prod":
        logger.warning(
            "CORS origins not specified for production. "
            "Please set cors.origins explicitly for security."
        )

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

        # Setup custom logging via loguru-kit
        setup_logging()

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

    for router in routers:
        app.include_router(router, dependencies=dependencies, prefix=prefix_url)

    # Add CORS middleware with environment-aware defaults
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=cors_origins,
        allow_credentials=cors_allow_credentials,
        allow_methods=cors_allow_methods,
        allow_headers=cors_allow_headers,
    )

    # Add centralized exception handler
    add_exception_handler(app, stage, exception_handlers)

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
