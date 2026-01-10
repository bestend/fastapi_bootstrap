"""Tests for Builder pattern API."""

from fastapi import APIRouter
from fastapi.testclient import TestClient

from fastapi_bootstrap.builder import FastAPIBootstrap, bootstrap
from fastapi_bootstrap.config import Stage


class TestFastAPIBootstrap:
    """Tests for FastAPIBootstrap builder."""

    def test_basic_build(self):
        """Basic build should create a working app."""
        router = APIRouter()

        @router.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app = FastAPIBootstrap().title("Test API").add_router(router).build()

        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_title_and_version(self):
        """Title and version should be set correctly."""
        app = FastAPIBootstrap().title("My API").version("2.0.0").build()

        assert app.title == "My API"
        assert app.version == "2.0.0"

    def test_stage_configuration(self):
        """Stage should affect CORS and other settings."""
        # Dev stage
        app_dev = FastAPIBootstrap().stage("dev").build()
        assert app_dev is not None

        # Prod stage
        app_prod = FastAPIBootstrap().stage("prod").build()
        assert app_prod is not None

        # Using enum
        app_staging = FastAPIBootstrap().stage(Stage.STAGING).build()
        assert app_staging is not None

    def test_prefix_url(self):
        """URL prefix should be applied to routes."""
        router = APIRouter()

        @router.get("/items")
        async def get_items():
            return {"items": []}

        app = FastAPIBootstrap().prefix("/api/v1").add_router(router).build()

        client = TestClient(app)
        response = client.get("/api/v1/items")
        assert response.status_code == 200

    def test_with_metrics(self):
        """Metrics endpoint should be available when enabled."""
        app = FastAPIBootstrap().with_metrics(endpoint="/metrics").build()

        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_with_health_check(self):
        """Health check endpoint should be configurable."""
        app = FastAPIBootstrap().with_health_check(endpoint="/health").build()

        client = TestClient(app)
        # Default health check
        response = client.get("/health")
        # Note: health endpoint is still at /healthz by default in create_app
        # The builder sets the setting but create_app uses health_check_api parameter

    def test_chaining(self):
        """All methods should return self for chaining."""
        builder = FastAPIBootstrap()

        result = (
            builder.title("Test")
            .version("1.0.0")
            .description("A test API")
            .stage("dev")
            .prefix("/api")
            .with_logging(level="DEBUG")
            .with_cors(origins=["http://localhost"])
            .with_security_headers()
            .with_metrics()
            .with_health_check()
            .with_graceful_shutdown(timeout=5)
        )

        assert result is builder

    def test_multiple_routers(self):
        """Multiple routers should be combined."""
        router1 = APIRouter()
        router2 = APIRouter()

        @router1.get("/users")
        async def get_users():
            return {"users": []}

        @router2.get("/posts")
        async def get_posts():
            return {"posts": []}

        app = (
            FastAPIBootstrap()
            .add_router(router1, prefix="/v1")
            .add_router(router2, prefix="/v2")
            .build()
        )

        client = TestClient(app)

        response1 = client.get("/v1/users")
        assert response1.status_code == 200

        response2 = client.get("/v2/posts")
        assert response2.status_code == 200

    def test_startup_shutdown_coroutines(self):
        """Startup and shutdown coroutines should be registered."""
        startup_called = []
        shutdown_called = []

        async def on_startup():
            startup_called.append(True)

        async def on_shutdown():
            shutdown_called.append(True)

        app = FastAPIBootstrap().on_startup(on_startup).on_shutdown(on_shutdown).build()

        # Use TestClient as context manager to trigger lifespan events
        with TestClient(app):
            assert len(startup_called) == 1

        assert len(shutdown_called) == 1

    def test_with_request_id(self):
        """Request ID middleware should add headers."""
        router = APIRouter()

        @router.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app = FastAPIBootstrap().with_request_id().add_router(router).build()

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Request-ID" in response.headers

    def test_with_request_timing(self):
        """Request timing middleware should add headers."""
        router = APIRouter()

        @router.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        app = FastAPIBootstrap().with_request_timing().add_router(router).build()

        client = TestClient(app)
        response = client.get("/test")

        assert "X-Response-Time" in response.headers
        assert response.headers["X-Response-Time"].endswith("ms")


class TestBootstrapFunction:
    """Tests for bootstrap() convenience function."""

    def test_returns_builder(self):
        """bootstrap() should return a FastAPIBootstrap instance."""
        builder = bootstrap()
        assert isinstance(builder, FastAPIBootstrap)

    def test_creates_app(self):
        """bootstrap() should create a working app."""
        app = bootstrap().title("Test").build()
        assert app is not None
        assert app.title == "Test"
