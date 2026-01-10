"""Test basic app creation."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_bootstrap import LoggingAPIRoute, create_app
from fastapi_bootstrap.config import (
    BootstrapSettings,
    CORSSettings,
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
    """Test basic app creation."""
    app = create_app(
        [simple_router],
        title="Test API",
        version="1.0.0",
    )

    assert app.title == "Test API"
    assert app.version == "1.0.0"


def test_health_check(simple_router):
    """Test health check endpoint."""
    app = create_app([simple_router], health_check_api="/healthz")
    client = TestClient(app)

    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.text == "OK"


def test_api_endpoint(simple_router):
    """Test API endpoint with logging."""
    app = create_app([simple_router])
    client = TestClient(app)

    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_api_with_prefix(simple_router):
    """Test API with URL prefix."""
    app = create_app([simple_router], prefix_url="/api/v1")
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

    app = create_app([router], docs_enable=False)
    client = TestClient(app)

    # Docs should not be accessible
    response = client.get("/docs")
    assert response.status_code == 404


def test_trace_id_in_response(simple_router):
    """Test that trace ID is included in response headers."""
    app = create_app([simple_router])
    client = TestClient(app)

    response = client.get("/test")
    assert "x-trace-id" in response.headers


class TestCreateAppWithSettings:
    """Tests for create_app with BootstrapSettings."""

    def test_create_app_with_settings_basic(self, simple_router):
        """Test app creation with BootstrapSettings."""
        settings = BootstrapSettings(
            title="Settings API",
            version="2.0.0",
        )
        app = create_app([simple_router], settings=settings)

        assert app.title == "Settings API"
        assert app.version == "2.0.0"

    def test_create_app_with_settings_overrides_params(self, simple_router):
        """Settings should override individual parameters."""
        settings = BootstrapSettings(
            title="From Settings",
            version="3.0.0",
        )
        app = create_app(
            [simple_router],
            title="From Param",
            version="1.0.0",
            settings=settings,
        )

        assert app.title == "From Settings"
        assert app.version == "3.0.0"

    def test_create_app_with_settings_stage(self, simple_router):
        """Test app creation with different stages via settings."""
        settings = BootstrapSettings(
            title="Prod API",
            stage=Stage.PROD,
            cors=CORSSettings(origins=["https://example.com"]),
        )
        app = create_app([simple_router], settings=settings)
        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200

    def test_create_app_with_settings_health_check(self, simple_router):
        """Test custom health check endpoint via settings."""
        settings = BootstrapSettings(
            health_check=HealthCheckSettings(endpoint="/health"),
        )
        app = create_app([simple_router], settings=settings)
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"

    def test_create_app_with_settings_graceful_shutdown(self, simple_router):
        """Test graceful shutdown configuration via settings."""
        settings = BootstrapSettings(
            graceful_shutdown=GracefulShutdownSettings(timeout=5),
        )
        app = create_app([simple_router], settings=settings)

        assert app is not None

    def test_create_app_legacy_params_still_work(self, simple_router):
        """Test that legacy parameter-based configuration still works."""
        app = create_app(
            [simple_router],
            title="Legacy API",
            version="1.0.0",
            stage="dev",
            health_check_api="/healthz",
            cors_origins=["*"],
        )
        client = TestClient(app)

        assert app.title == "Legacy API"
        response = client.get("/healthz")
        assert response.status_code == 200
