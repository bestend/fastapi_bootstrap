"""Tests for metrics module."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_bootstrap.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsMiddleware,
    MetricsRegistry,
    get_metrics_registry,
    get_metrics_router,
    reset_metrics_registry,
)


class TestCounter:
    """Tests for Counter class."""

    def test_initial_value(self):
        """Counter should start at 0."""
        counter = Counter()
        assert counter.value == 0

    def test_increment(self):
        """Counter should increment correctly."""
        counter = Counter()
        counter.inc()
        assert counter.value == 1

    def test_increment_by_value(self):
        """Counter should increment by specified value."""
        counter = Counter()
        counter.inc(5)
        assert counter.value == 5

    def test_multiple_increments(self):
        """Multiple increments should accumulate."""
        counter = Counter()
        counter.inc()
        counter.inc(3)
        counter.inc(2)
        assert counter.value == 6


class TestGauge:
    """Tests for Gauge class."""

    def test_initial_value(self):
        """Gauge should start at 0."""
        gauge = Gauge()
        assert gauge.value == 0.0

    def test_set_value(self):
        """Gauge should set value correctly."""
        gauge = Gauge()
        gauge.set(42.5)
        assert gauge.value == 42.5

    def test_increment(self):
        """Gauge should increment correctly."""
        gauge = Gauge()
        gauge.set(10)
        gauge.inc(5)
        assert gauge.value == 15

    def test_decrement(self):
        """Gauge should decrement correctly."""
        gauge = Gauge()
        gauge.set(10)
        gauge.dec(3)
        assert gauge.value == 7


class TestHistogram:
    """Tests for Histogram class."""

    def test_observe(self):
        """Histogram should record observations."""
        histogram = Histogram()
        histogram.observe(0.1)
        histogram.observe(0.5)
        assert histogram.count == 2
        assert histogram.sum == 0.6

    def test_bucket_counts(self):
        """Histogram should count buckets correctly (cumulative)."""
        histogram = Histogram()
        histogram.observe(0.005)  # 1st bucket (0.005)
        histogram.observe(0.05)  # 4th bucket (0.05)
        histogram.observe(1.0)  # 8th bucket (1.0)

        buckets = histogram.get_bucket_counts()
        # Cumulative counts: each bucket includes all observations <= bucket boundary
        assert buckets[0.005] == 1  # Only the 0.005 observation
        assert buckets[0.05] == 2  # 0.005 + 0.05 observations
        assert buckets[1.0] == 3  # All three observations


class TestMetricsRegistry:
    """Tests for MetricsRegistry class."""

    def test_request_count(self):
        """Registry should track request counts."""
        registry = MetricsRegistry()
        counter = registry.get_request_count("GET", "/api/users", 200)
        counter.inc()
        counter.inc()

        same_counter = registry.get_request_count("GET", "/api/users", 200)
        assert same_counter.value == 2

    def test_request_latency(self):
        """Registry should track request latency."""
        registry = MetricsRegistry()
        histogram = registry.get_request_latency("GET", "/api/users")
        histogram.observe(0.1)
        histogram.observe(0.2)

        same_histogram = registry.get_request_latency("GET", "/api/users")
        assert same_histogram.count == 2

    def test_export_format(self):
        """Registry should export in Prometheus format."""
        registry = MetricsRegistry(app_name="test_app")
        registry.set_app_info("1.0.0", "3.12.0")
        registry.get_request_count("GET", "/api/users", 200).inc()

        output = registry.export()

        assert "# HELP" in output
        assert "# TYPE" in output
        assert "test_app_http_requests_total" in output
        assert 'method="GET"' in output


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset metrics registry before each test."""
        reset_metrics_registry()
        yield
        reset_metrics_registry()

    def test_middleware_records_requests(self):
        """Middleware should record request metrics."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware, app_name="test")

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        client = TestClient(app)

        # Make some requests
        client.get("/test")
        client.get("/test")

        # Check metrics
        registry = get_metrics_registry("test")
        # Path template might be /test
        output = registry.export()
        assert "http_requests_total" in output

    def test_middleware_excludes_paths(self):
        """Middleware should exclude configured paths."""
        app = FastAPI()
        app.add_middleware(MetricsMiddleware, exclude_paths=["/health", "/metrics"])

        @app.get("/health")
        async def health():
            return {"status": "healthy"}

        @app.get("/api/data")
        async def data():
            return {"data": []}

        client = TestClient(app)
        client.get("/health")
        client.get("/api/data")

        # Health endpoint should be excluded, api/data should be included
        registry = get_metrics_registry()
        output = registry.export()
        assert "/health" not in output and "/api/data" in output


class TestMetricsRouter:
    """Tests for metrics router."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset metrics registry before each test."""
        reset_metrics_registry()
        yield
        reset_metrics_registry()

    def test_metrics_endpoint(self):
        """Metrics endpoint should return Prometheus format."""
        app = FastAPI()
        app.include_router(get_metrics_router())

        client = TestClient(app)
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_custom_metrics_path(self):
        """Custom metrics path should work."""
        app = FastAPI()
        app.include_router(get_metrics_router(path="/custom-metrics"))

        client = TestClient(app)
        response = client.get("/custom-metrics")

        assert response.status_code == 200
