"""Test exception handling."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_bootstrap import create_app
from fastapi_bootstrap.config import BootstrapSettings, Stage
from fastapi_bootstrap.exception import (
    BadRequestHeaderError,
    ErrorInfo,
    InvalidAccessTokenError,
)


@pytest.fixture
def error_router():
    """Create a router with error endpoints."""
    router = APIRouter()

    @router.get("/bad-header")
    async def bad_header():
        raise BadRequestHeaderError("Invalid header")

    @router.get("/invalid-token")
    async def invalid_token():
        raise InvalidAccessTokenError("Token expired")

    @router.get("/server-error")
    async def server_error():
        raise RuntimeError("Something went wrong")

    return router


def test_bad_request_header_error(error_router):
    """Test BadRequestHeaderError handling."""
    settings = BootstrapSettings(stage=Stage.DEV)
    app = create_app(routers=[error_router], settings=settings)
    client = TestClient(app)

    response = client.get("/bad-header")
    assert response.status_code == 400
    assert "msg" in response.json()


def test_invalid_token_error(error_router):
    """Test InvalidAccessTokenError handling."""
    settings = BootstrapSettings(stage=Stage.DEV)
    app = create_app(routers=[error_router], settings=settings)
    client = TestClient(app)

    response = client.get("/invalid-token")
    assert response.status_code == 401
    assert "msg" in response.json()


def test_server_error(error_router):
    """Test RuntimeError handling."""
    settings = BootstrapSettings(stage=Stage.DEV)
    app = create_app(routers=[error_router], settings=settings)
    client = TestClient(app)

    response = client.get("/server-error")
    assert response.status_code == 500
    assert "msg" in response.json()


def test_error_info():
    """Test ErrorInfo model."""
    error = ErrorInfo(
        status_code=404,
        msg="Not found",
        detail="Resource not found",
        log_level="warning",
    )

    assert error.status_code == 404
    assert error.msg == "Not found"
    assert error.detail == "Resource not found"
    assert error.log_level == "warning"
