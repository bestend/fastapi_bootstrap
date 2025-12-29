"""Test basic app creation."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_bootstrap import LoggingAPIRoute, create_app


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
