"""Test CORS configuration."""
import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_kit import create_app


@pytest.fixture
def simple_router():
    """Create a simple test router."""
    router = APIRouter()

    @router.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return router


def test_cors_dev_default(simple_router):
    """Test that dev stage allows all origins by default."""
    app = create_app([simple_router], stage="dev")
    client = TestClient(app)

    response = client.get(
        "/test", headers={"Origin": "https://random-domain.com"}
    )

    # Should allow any origin in dev
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_cors_prod_restrictive(simple_router):
    """Test that prod stage is restrictive by default."""
    app = create_app([simple_router], stage="prod")
    client = TestClient(app)

    response = client.get(
        "/test", headers={"Origin": "https://random-domain.com"}
    )

    # Should not allow random origins in prod
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_prod_explicit_origins(simple_router):
    """Test explicit CORS origins in production."""
    allowed_origins = ["https://myapp.com", "https://www.myapp.com"]
    app = create_app(
        [simple_router], stage="prod", cors_origins=allowed_origins
    )
    client = TestClient(app)

    # Test allowed origin
    response = client.get("/test", headers={"Origin": "https://myapp.com"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://myapp.com"

    # Test disallowed origin
    response = client.get(
        "/test", headers={"Origin": "https://evil-site.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_custom_methods(simple_router):
    """Test custom allowed methods."""
    app = create_app(
        [simple_router],
        stage="prod",
        cors_origins=["https://myapp.com"],
        cors_allow_methods=["GET", "POST"],
    )
    client = TestClient(app)

    # Preflight request
    response = client.options(
        "/test",
        headers={
            "Origin": "https://myapp.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-methods" in response.headers
    allowed_methods = response.headers["access-control-allow-methods"]
    assert "GET" in allowed_methods
    assert "POST" in allowed_methods


def test_cors_custom_headers(simple_router):
    """Test custom allowed headers."""
    app = create_app(
        [simple_router],
        stage="prod",
        cors_origins=["https://myapp.com"],
        cors_allow_headers=["Content-Type", "Authorization"],
    )
    client = TestClient(app)

    # Preflight request
    response = client.options(
        "/test",
        headers={
            "Origin": "https://myapp.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert "access-control-allow-headers" in response.headers
    allowed_headers = response.headers["access-control-allow-headers"]
    assert "content-type" in allowed_headers.lower()


def test_cors_staging_environment(simple_router):
    """Test staging environment CORS configuration."""
    app = create_app([simple_router], stage="staging")
    client = TestClient(app)

    # Staging should have some restrictions
    response = client.get("/test", headers={"Origin": "https://app.staging.example.com"})

    # Response should be successful
    assert response.status_code == 200

