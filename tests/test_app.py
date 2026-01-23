"""Test basic app creation."""

import pytest
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from fastapi_bootstrap import LoggingAPIRoute, create_app
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
    DocsSettings,
    GracefulShutdownSettings,
    HealthCheckSettings,
    Stage,
)


@pytest.fixture
def simple_router():
    """Create a simple test router."""
    router = APIRouter(route_class=LoggingAPIRoute)

    @router.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return router


def test_create_app_basic(simple_router):
    """Test basic app creation with new signature."""
    settings = BootstrapSettings(title="Test API", version="1.0.0")
    app = create_app(routers=[simple_router], settings=settings)

    assert app.title == "Test API"
    assert app.version == "1.0.0"


def test_create_app_minimal(simple_router):
    """Test app creation with minimal arguments."""
    app = create_app(routers=[simple_router])
    client = TestClient(app)

    response = client.get("/test")
    assert response.status_code == 200


def test_health_check(simple_router):
    """Test health check endpoint."""
    settings = BootstrapSettings(health_check=HealthCheckSettings(endpoint="/healthz"))
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "OK"


def test_api_endpoint(simple_router):
    """Test API endpoint with logging."""
    app = create_app(routers=[simple_router])
    client = TestClient(app)

    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_api_with_prefix(simple_router):
    """Test API with URL prefix."""
    settings = BootstrapSettings(prefix_url="/api/v1")
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

    response = client.get("/api/v1/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_docs_disabled():
    """Test with docs disabled."""
    router = APIRouter()

    @router.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    settings = BootstrapSettings(docs=DocsSettings(enabled=False))
    app = create_app(routers=[router], settings=settings)
    client = TestClient(app)

    response = client.get("/docs")
    assert response.status_code == 404


def test_trace_id_in_response(simple_router):
    """Test that trace ID is included in response headers."""
    app = create_app(routers=[simple_router])
    client = TestClient(app)

    response = client.get("/test")
    assert "x-trace-id" in response.headers


class TestCreateAppWithSettings:
    """Tests for create_app with BootstrapSettings."""

    def test_create_app_with_settings_basic(self, simple_router):
        """Test app creation with BootstrapSettings."""
        settings = BootstrapSettings(title="Settings API", version="2.0.0")
        app = create_app(routers=[simple_router], settings=settings)

        assert app.title == "Settings API"
        assert app.version == "2.0.0"

    def test_create_app_with_settings_stage(self, simple_router):
        """Test app creation with different stages via settings."""
        settings = BootstrapSettings(
            title="Prod API",
            stage=Stage.PROD,
            cors=CORSSettings(origins=["https://example.com"]),
        )
        app = create_app(routers=[simple_router], settings=settings)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200

    def test_create_app_with_settings_health_check(self, simple_router):
        """Test custom health check endpoint via settings."""
        settings = BootstrapSettings(health_check=HealthCheckSettings(endpoint="/health"))
        app = create_app(routers=[simple_router], settings=settings)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"

    def test_create_app_with_settings_graceful_shutdown(self, simple_router):
        """Test graceful shutdown configuration via settings."""
        settings = BootstrapSettings(graceful_shutdown=GracefulShutdownSettings(timeout=5))
        app = create_app(routers=[simple_router], settings=settings)
        assert app is not None

    def test_create_app_with_prefix_url(self, simple_router):
        """Test API prefix URL configuration via settings."""
        settings = BootstrapSettings(prefix_url="/api/v2")
        app = create_app(routers=[simple_router], settings=settings)
        client = TestClient(app)

        response = client.get("/api/v2/test")
        assert response.status_code == 200

    def test_create_app_with_docs_settings(self, simple_router):
        """Test docs configuration via settings."""
        settings = BootstrapSettings(docs=DocsSettings(enabled=True, prefix_url="/api"))
        app = create_app(routers=[simple_router], settings=settings)
        client = TestClient(app)

        response = client.get("/api/docs")
        assert response.status_code == 200

    def test_create_app_with_swagger_oauth(self, simple_router):
        """Test Swagger OAuth configuration via settings."""
        oauth_config = {"clientId": "test-client", "usePkceWithAuthorizationCodeGrant": True}
        settings = BootstrapSettings(docs=DocsSettings(swagger_oauth=oauth_config))
        app = create_app(routers=[simple_router], settings=settings)
        assert app is not None


class TestLoggingAPIRouteHTTPException:
    def test_http_exception_propagates_to_app_handler(self):
        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/protected")
        async def protected():
            raise HTTPException(status_code=401, detail="Not authenticated")

        app = create_app(routers=[router])

        @app.exception_handler(HTTPException)
        async def custom_handler(request: Request, exc: HTTPException):
            if exc.status_code == 401:
                return RedirectResponse(url="/login", status_code=302)
            raise exc

        client = TestClient(app, follow_redirects=False)

        response = client.get("/protected")
        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_regular_exception_still_handled_by_route(self):
        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/error")
        async def error_endpoint():
            raise ValueError("Something went wrong")

        app = create_app(routers=[router])
        client = TestClient(app)

        response = client.get("/error")
        assert response.status_code == 500
        assert response.json()["success"] is False


class TestCustomExceptionHandlers:
    def test_custom_handler_via_parameter(self):
        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/protected")
        async def protected():
            raise HTTPException(status_code=401, detail="Not authenticated")

        async def custom_401_handler(request: Request, exc: HTTPException):
            if exc.status_code == 401:
                return RedirectResponse(url="/login", status_code=302)
            from fastapi.responses import JSONResponse

            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        app = create_app(
            routers=[router],
            exception_handlers={HTTPException: custom_401_handler},
        )

        client = TestClient(app, follow_redirects=False)

        response = client.get("/protected")
        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_custom_handler_does_not_affect_other_exceptions(self):
        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/error")
        async def error_endpoint():
            raise ValueError("Something went wrong")

        async def custom_401_handler(request: Request, exc: HTTPException):
            return RedirectResponse(url="/login", status_code=302)

        app = create_app(
            routers=[router],
            exception_handlers={HTTPException: custom_401_handler},
        )
        client = TestClient(app)

        response = client.get("/error")
        assert response.status_code == 500
        assert response.json()["success"] is False
