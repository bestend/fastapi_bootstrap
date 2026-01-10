"""Security middleware for FastAPI Bootstrap.

This module provides security-related middleware including:
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Request size limiting
- Request ID injection
"""

import time
import uuid
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to all responses.

    This middleware adds the following security headers:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy

    Example:
        ```python
        from fastapi_bootstrap.middleware import SecurityHeadersMiddleware

        app.add_middleware(
            SecurityHeadersMiddleware,
            hsts_max_age=31536000,
            content_security_policy="default-src 'self'",
        )
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        content_security_policy: str | None = None,
        x_frame_options: str = "DENY",
        x_content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str | None = None,
        enable_in_dev: bool = False,
        stage: str = "dev",
    ):
        """Initialize the security headers middleware.

        Args:
            app: The ASGI application
            hsts_max_age: Max age for HSTS in seconds (0 to disable)
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
            content_security_policy: CSP header value (None to disable)
            x_frame_options: X-Frame-Options value (DENY, SAMEORIGIN, or None)
            x_content_type_options: X-Content-Type-Options value
            referrer_policy: Referrer-Policy value
            permissions_policy: Permissions-Policy value (None for default)
            enable_in_dev: Enable security headers in development mode
            stage: Current application stage (dev, staging, prod)
        """
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.content_security_policy = content_security_policy
        self.x_frame_options = x_frame_options
        self.x_content_type_options = x_content_type_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or "geolocation=(), microphone=(), camera=()"
        self.enable_in_dev = enable_in_dev
        self.stage = stage

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add security headers to response."""
        response = await call_next(request)

        # Skip security headers in dev unless explicitly enabled
        if self.stage == "dev" and not self.enable_in_dev:
            return response

        # HSTS (only for HTTPS)
        if self.hsts_max_age > 0:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        if self.content_security_policy:
            response.headers["Content-Security-Policy"] = self.content_security_policy

        # X-Frame-Options
        if self.x_frame_options:
            response.headers["X-Frame-Options"] = self.x_frame_options

        # X-Content-Type-Options
        if self.x_content_type_options:
            response.headers["X-Content-Type-Options"] = self.x_content_type_options

        # X-XSS-Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        if self.referrer_policy:
            response.headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has a unique ID.

    If the request includes an X-Request-ID header, it's used.
    Otherwise, a new UUID is generated. The request ID is added
    to both the request state and response headers.

    Example:
        ```python
        from fastapi_bootstrap.middleware import RequestIDMiddleware

        app.add_middleware(RequestIDMiddleware)

        @app.get("/")
        async def root(request: Request):
            return {"request_id": request.state.request_id}
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
        generator: Callable[[], str] | None = None,
    ):
        """Initialize the request ID middleware.

        Args:
            app: The ASGI application
            header_name: Header name for request ID
            generator: Custom ID generator function (defaults to UUID4)
        """
        super().__init__(app)
        self.header_name = header_name
        self.generator = generator or (lambda: str(uuid.uuid4()))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and inject request ID."""
        # Get existing request ID or generate new one
        request_id = request.headers.get(self.header_name) or self.generator()

        # Store in request state for access in handlers
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.header_name] = request_id

        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks request processing time.

    Adds X-Response-Time header with the time taken to process
    the request in milliseconds.

    Example:
        ```python
        from fastapi_bootstrap.middleware import RequestTimingMiddleware

        app.add_middleware(RequestTimingMiddleware)
        # Response will include: X-Response-Time: 123.45ms
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Response-Time",
    ):
        """Initialize the timing middleware.

        Args:
            app: The ASGI application
            header_name: Header name for response time
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and measure timing."""
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = (time.perf_counter() - start_time) * 1000
        response.headers[self.header_name] = f"{process_time:.2f}ms"

        return response


class MaxRequestSizeMiddleware:
    """Middleware that limits request body size.

    Returns 413 Payload Too Large if request body exceeds the limit.

    Example:
        ```python
        from fastapi_bootstrap.middleware import MaxRequestSizeMiddleware

        app.add_middleware(MaxRequestSizeMiddleware, max_size=10 * 1024 * 1024)  # 10MB
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        max_size: int = 10 * 1024 * 1024,  # 10MB default
    ):
        """Initialize the max size middleware.

        Args:
            app: The ASGI application
            max_size: Maximum request body size in bytes
        """
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Process the request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check Content-Length header
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")

        if content_length:
            try:
                length = int(content_length.decode())
                if length > self.max_size:
                    response = Response(
                        content=f"Request body too large. Max size: {self.max_size} bytes",
                        status_code=413,
                    )
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass  # Invalid Content-Length, let the request proceed

        await self.app(scope, receive, send)


# Export all middleware classes
__all__ = [
    "SecurityHeadersMiddleware",
    "RequestIDMiddleware",
    "RequestTimingMiddleware",
    "MaxRequestSizeMiddleware",
]
