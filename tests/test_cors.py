"""Test CORS configuration."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_bootstrap import create_app
from fastapi_bootstrap.config import BootstrapSettings, CORSSettings, Stage


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
    settings = BootstrapSettings(stage=Stage.DEV)
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

    response = client.get("/test", headers={"Origin": "https://random-domain.com"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_cors_prod_restrictive(simple_router):
    """Test that prod stage is restrictive by default."""
    settings = BootstrapSettings(stage=Stage.PROD)
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

    response = client.get("/test", headers={"Origin": "https://random-domain.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_prod_explicit_origins(simple_router):
    """Test explicit CORS origins in production."""
    allowed_origins = ["https://myapp.com", "https://www.myapp.com"]
    settings = BootstrapSettings(
        stage=Stage.PROD,
        cors=CORSSettings(origins=allowed_origins),
    )
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

    response = client.get("/test", headers={"Origin": "https://myapp.com"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://myapp.com"

    response = client.get("/test", headers={"Origin": "https://evil-site.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_custom_methods(simple_router):
    """Test custom allowed methods."""
    settings = BootstrapSettings(
        stage=Stage.PROD,
        cors=CORSSettings(
            origins=["https://myapp.com"],
            allow_methods=["GET", "POST"],
        ),
    )
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

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
    settings = BootstrapSettings(
        stage=Stage.PROD,
        cors=CORSSettings(
            origins=["https://myapp.com"],
            allow_headers=["Content-Type", "Authorization"],
        ),
    )
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

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
    settings = BootstrapSettings(stage=Stage.STAGING)
    app = create_app(routers=[simple_router], settings=settings)
    client = TestClient(app)

    response = client.get("/test", headers={"Origin": "https://app.staging.example.com"})
    assert response.status_code == 200
