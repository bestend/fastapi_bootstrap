"""Tests for security middleware."""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from fastapi_bootstrap.middleware import (
    MaxRequestSizeMiddleware,
    RequestIDMiddleware,
    RequestTimingMiddleware,
    SecurityHeadersMiddleware,
)


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def test_adds_security_headers_in_prod(self):
        """Security headers should be added in production (except HSTS on HTTP)."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, stage="prod")  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        # HSTS is only added for HTTPS connections, TestClient uses HTTP
        assert "Strict-Transport-Security" not in response.headers
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_adds_hsts_on_https(self):
        """HSTS header should be added when X-Forwarded-Proto is https."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, stage="prod")  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        # Simulate HTTPS via proxy header
        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers

    def test_skips_headers_in_dev_by_default(self):
        """Security headers should be skipped in dev by default."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, stage="dev", enable_in_dev=False)  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "Strict-Transport-Security" not in response.headers

    def test_enables_headers_in_dev_when_configured(self):
        """Security headers should be enabled in dev when configured."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware, stage="dev", enable_in_dev=True)  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        # Simulate HTTPS via proxy header
        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        assert "Strict-Transport-Security" in response.headers

    def test_custom_csp(self):
        """Custom CSP should be applied."""
        app = FastAPI()
        app.add_middleware(
            SecurityHeadersMiddleware,  # type: ignore[arg-type]
            stage="prod",
            content_security_policy="default-src 'self'; script-src 'unsafe-inline'",
        )

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        assert "script-src" in response.headers["Content-Security-Policy"]

    def test_hsts_configuration(self):
        """HSTS should be configurable."""
        app = FastAPI()
        app.add_middleware(
            SecurityHeadersMiddleware,  # type: ignore[arg-type]
            stage="prod",
            hsts_max_age=3600,
            hsts_include_subdomains=True,
            hsts_preload=True,
        )

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        # Simulate HTTPS via proxy header
        response = client.get("/test", headers={"X-Forwarded-Proto": "https"})

        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=3600" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware."""

    def test_generates_request_id(self):
        """Middleware should generate a request ID."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": request.state.request_id}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID format

    def test_uses_existing_request_id(self):
        """Middleware should use existing request ID from header."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": request.state.request_id}

        client = TestClient(app)
        response = client.get("/test", headers={"X-Request-ID": "custom-id-123"})

        assert response.headers["X-Request-ID"] == "custom-id-123"
        assert response.json()["request_id"] == "custom-id-123"

    def test_custom_header_name(self):
        """Middleware should support custom header name."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware, header_name="X-Correlation-ID")  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Correlation-ID" in response.headers

    def test_custom_generator(self):
        """Middleware should support custom ID generator."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware, generator=lambda: "fixed-id")  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.headers["X-Request-ID"] == "fixed-id"


class TestRequestTimingMiddleware:
    """Tests for RequestTimingMiddleware."""

    def test_adds_timing_header(self):
        """Middleware should add timing header."""
        app = FastAPI()
        app.add_middleware(RequestTimingMiddleware)  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Response-Time" in response.headers
        # Should be in format like "1.23ms"
        timing = response.headers["X-Response-Time"]
        assert timing.endswith("ms")
        # Parse the number part
        time_value = float(timing.replace("ms", ""))
        assert time_value >= 0

    def test_custom_header_name(self):
        """Middleware should support custom header name."""
        app = FastAPI()
        app.add_middleware(RequestTimingMiddleware, header_name="X-Processing-Time")  # type: ignore[arg-type]

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Processing-Time" in response.headers


class TestMaxRequestSizeMiddleware:
    """Tests for MaxRequestSizeMiddleware."""

    def test_allows_small_requests(self):
        """Small requests should be allowed."""
        app = FastAPI()
        app.add_middleware(MaxRequestSizeMiddleware, max_size=1024)  # type: ignore[arg-type] # 1KB

        @app.post("/test")
        async def test_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body)}

        client = TestClient(app)
        response = client.post("/test", content="small data")

        assert response.status_code == 200

    def test_rejects_large_requests(self):
        """Large requests should be rejected."""
        app = FastAPI()
        app.add_middleware(MaxRequestSizeMiddleware, max_size=100)  # type: ignore[arg-type] # 100 bytes

        @app.post("/test")
        async def test_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body)}

        client = TestClient(app)
        large_content = "x" * 200
        response = client.post(
            "/test",
            content=large_content,
            headers={"Content-Length": str(len(large_content))},
        )

        assert response.status_code == 413
        assert "too large" in response.text.lower()

    def test_rejects_large_requests_without_content_length(self):
        app = FastAPI()
        app.add_middleware(MaxRequestSizeMiddleware, max_size=100)  # type: ignore[arg-type]

        @app.post("/test")
        async def test_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body)}

        client = TestClient(app)

        request = client.build_request("POST", "/test", content=("x" * 200))
        request.headers.pop("Content-Length", None)

        response = client.send(request)
        assert response.status_code == 413
        assert "too large" in response.text.lower()
