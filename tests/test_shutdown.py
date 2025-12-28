"""Test graceful shutdown timing."""
import asyncio
import time

import pytest

from fastapi import APIRouter
from fastapi_kit import create_app


@pytest.mark.asyncio
async def test_graceful_shutdown_zero():
    """Test that graceful_timeout=0 results in fast shutdown."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    app = create_app([router], graceful_timeout=0)

    # Simulate shutdown
    start = time.time()

    async with app.router.lifespan_context(app):
        pass  # This triggers startup and shutdown

    elapsed = time.time() - start

    # Should be very fast (< 0.5 seconds)
    assert elapsed < 0.5, f"Shutdown took {elapsed:.2f}s, expected < 0.5s"


@pytest.mark.asyncio
async def test_graceful_shutdown_with_delay():
    """Test that graceful_timeout works as expected."""
    router = APIRouter()

    @router.get("/test")
    def test():
        return {"ok": True}

    timeout = 2
    app = create_app([router], graceful_timeout=timeout)

    start = time.time()

    async with app.router.lifespan_context(app):
        pass

    elapsed = time.time() - start

    # Should wait for the graceful timeout
    assert elapsed >= timeout, f"Expected >= {timeout}s, got {elapsed:.2f}s"
    assert elapsed < timeout + 0.5, f"Too slow: {elapsed:.2f}s"

