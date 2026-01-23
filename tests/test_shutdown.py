"""Test graceful shutdown timing."""

import time

import pytest
from fastapi import APIRouter

from fastapi_bootstrap import create_app
from fastapi_bootstrap.config import BootstrapSettings, GracefulShutdownSettings


@pytest.mark.asyncio
async def test_graceful_shutdown_zero():
    """Test that graceful_timeout=0 results in fast shutdown."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    settings = BootstrapSettings(graceful_shutdown=GracefulShutdownSettings(timeout=0))
    app = create_app(routers=[router], settings=settings)

    start = time.time()

    async with app.router.lifespan_context(app):
        pass

    elapsed = time.time() - start
    assert elapsed < 0.5, f"Shutdown took {elapsed:.2f}s, expected < 0.5s"


@pytest.mark.asyncio
async def test_graceful_shutdown_with_delay():
    """Test that graceful_timeout works as expected."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    timeout = 2
    settings = BootstrapSettings(graceful_shutdown=GracefulShutdownSettings(timeout=timeout))
    app = create_app(routers=[router], settings=settings)

    start = time.time()

    async with app.router.lifespan_context(app):
        pass

    elapsed = time.time() - start
    assert elapsed >= timeout, f"Expected >= {timeout}s, got {elapsed:.2f}s"
    assert elapsed < timeout + 0.5, f"Too slow: {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_startup_shutdown_with_app_parameter():
    """Test startup/shutdown coroutines that accept app parameter."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    startup_called = []
    shutdown_called = []

    async def startup_with_app(app):
        startup_called.append(app)

    async def shutdown_with_app(app):
        shutdown_called.append(app)

    settings = BootstrapSettings(graceful_shutdown=GracefulShutdownSettings(timeout=0))
    app = create_app(
        routers=[router],
        settings=settings,
        startup_coroutines=[startup_with_app],
        shutdown_coroutines=[shutdown_with_app],
    )

    async with app.router.lifespan_context(app):
        pass

    assert len(startup_called) == 1
    assert len(shutdown_called) == 1
    assert startup_called[0] is app
    assert shutdown_called[0] is app


@pytest.mark.asyncio
async def test_startup_shutdown_without_app_parameter():
    """Test startup/shutdown coroutines that don't accept any parameters."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    startup_called = []
    shutdown_called = []

    async def startup_no_param():
        startup_called.append(True)

    async def shutdown_no_param():
        shutdown_called.append(True)

    settings = BootstrapSettings(graceful_shutdown=GracefulShutdownSettings(timeout=0))
    app = create_app(
        routers=[router],
        settings=settings,
        startup_coroutines=[startup_no_param],
        shutdown_coroutines=[shutdown_no_param],
    )

    async with app.router.lifespan_context(app):
        pass

    assert len(startup_called) == 1
    assert len(shutdown_called) == 1
    assert startup_called[0] is True
    assert shutdown_called[0] is True


@pytest.mark.asyncio
async def test_mixed_startup_shutdown_coroutines():
    """Test mixed startup/shutdown coroutines with and without app parameter."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    calls = []

    async def startup_with_app(app):
        calls.append(("startup_with_app", app))

    async def startup_no_param():
        calls.append(("startup_no_param", None))

    async def shutdown_with_app(app):
        calls.append(("shutdown_with_app", app))

    async def shutdown_no_param():
        calls.append(("shutdown_no_param", None))

    settings = BootstrapSettings(graceful_shutdown=GracefulShutdownSettings(timeout=0))
    app = create_app(
        routers=[router],
        settings=settings,
        startup_coroutines=[startup_with_app, startup_no_param],
        shutdown_coroutines=[shutdown_with_app, shutdown_no_param],
    )

    async with app.router.lifespan_context(app):
        pass

    assert len(calls) == 4
    assert calls[0] == ("startup_with_app", app)
    assert calls[1] == ("startup_no_param", None)
    assert calls[2] == ("shutdown_with_app", app)
    assert calls[3] == ("shutdown_no_param", None)
