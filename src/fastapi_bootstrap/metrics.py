"""Prometheus metrics for FastAPI Bootstrap.

This module provides Prometheus-compatible metrics collection and export,
including request counts, latencies, and error rates.

Example:
    ```python
    from fastapi_bootstrap.metrics import MetricsMiddleware, get_metrics_router

    app.add_middleware(MetricsMiddleware)
    app.include_router(get_metrics_router())
    ```
"""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock

from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match
from starlette.types import ASGIApp


@dataclass
class Histogram:
    """A simple histogram implementation for tracking distributions.

    Tracks count, sum, and bucket counts for Prometheus histogram format.
    """

    buckets: tuple[float, ...] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    _counts: dict[float, int] = field(default_factory=lambda: defaultdict(int))
    _sum: float = 0.0
    _count: int = 0
    _lock: Lock = field(default_factory=Lock)

    def observe(self, value: float) -> None:
        """Record an observation."""
        with self._lock:
            self._sum += value
            self._count += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[bucket] += 1

    @property
    def sum(self) -> float:
        """Total sum of all observations."""
        return self._sum

    @property
    def count(self) -> int:
        """Total count of observations."""
        return self._count

    def get_bucket_counts(self) -> dict[float, int]:
        """Get cumulative bucket counts."""
        cumulative = {}
        total = 0
        for bucket in sorted(self.buckets):
            total += self._counts.get(bucket, 0)
            cumulative[bucket] = total
        return cumulative


@dataclass
class Counter:
    """A simple counter implementation."""

    _value: int = 0
    _lock: Lock = field(default_factory=Lock)

    def inc(self, value: int = 1) -> None:
        """Increment the counter."""
        with self._lock:
            self._value += value

    @property
    def value(self) -> int:
        """Current counter value."""
        return self._value


@dataclass
class Gauge:
    """A simple gauge implementation."""

    _value: float = 0.0
    _lock: Lock = field(default_factory=Lock)

    def set(self, value: float) -> None:
        """Set the gauge value."""
        with self._lock:
            self._value = value

    def inc(self, value: float = 1.0) -> None:
        """Increment the gauge."""
        with self._lock:
            self._value += value

    def dec(self, value: float = 1.0) -> None:
        """Decrement the gauge."""
        with self._lock:
            self._value -= value

    @property
    def value(self) -> float:
        """Current gauge value."""
        return self._value


class MetricsRegistry:
    """Central registry for all application metrics.

    This class maintains all metrics and provides export functionality
    in Prometheus text format.

    Example:
        ```python
        registry = MetricsRegistry()
        registry.request_count.labels(method="GET", path="/api/users").inc()
        ```
    """

    def __init__(self, app_name: str = "fastapi_bootstrap"):
        """Initialize the metrics registry.

        Args:
            app_name: Application name prefix for metrics
        """
        self.app_name = app_name
        self._lock = Lock()

        # Request metrics
        self._request_count: dict[tuple, Counter] = {}
        self._request_latency: dict[tuple, Histogram] = {}
        self._request_in_progress: dict[tuple, Gauge] = {}

        # Error metrics
        self._error_count: dict[tuple, Counter] = {}

        # App info
        self._app_info: dict[str, str] = {}

    def set_app_info(self, version: str, python_version: str) -> None:
        """Set application info for info metric."""
        self._app_info = {
            "version": version,
            "python_version": python_version,
        }

    def get_request_count(self, method: str, path: str, status: int) -> Counter:
        """Get or create a request counter."""
        key = (method, path, status)
        if key not in self._request_count:
            with self._lock:
                if key not in self._request_count:
                    self._request_count[key] = Counter()
        return self._request_count[key]

    def get_request_latency(self, method: str, path: str) -> Histogram:
        """Get or create a request latency histogram."""
        key = (method, path)
        if key not in self._request_latency:
            with self._lock:
                if key not in self._request_latency:
                    self._request_latency[key] = Histogram()
        return self._request_latency[key]

    def get_requests_in_progress(self, method: str, path: str) -> Gauge:
        """Get or create an in-progress requests gauge."""
        key = (method, path)
        if key not in self._request_in_progress:
            with self._lock:
                if key not in self._request_in_progress:
                    self._request_in_progress[key] = Gauge()
        return self._request_in_progress[key]

    def get_error_count(self, method: str, path: str, error_type: str) -> Counter:
        """Get or create an error counter."""
        key = (method, path, error_type)
        if key not in self._error_count:
            with self._lock:
                if key not in self._error_count:
                    self._error_count[key] = Counter()
        return self._error_count[key]

    def export(self) -> str:
        """Export all metrics in Prometheus text format.

        Returns:
            Prometheus-compatible metrics text
        """
        lines: list[str] = []

        # App info
        if self._app_info:
            lines.append(f"# HELP {self.app_name}_app_info Application information")
            lines.append(f"# TYPE {self.app_name}_app_info gauge")
            labels = ",".join(f'{k}="{v}"' for k, v in self._app_info.items())
            lines.append(f"{self.app_name}_app_info{{{labels}}} 1")
            lines.append("")

        # Request count
        if self._request_count:
            lines.append(f"# HELP {self.app_name}_http_requests_total Total HTTP requests")
            lines.append(f"# TYPE {self.app_name}_http_requests_total counter")
            for (method, path, status), counter in sorted(self._request_count.items()):
                lines.append(
                    f'{self.app_name}_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {counter.value}'
                )
            lines.append("")

        # Request latency histogram
        if self._request_latency:
            lines.append(
                f"# HELP {self.app_name}_http_request_duration_seconds HTTP request duration"
            )
            lines.append(f"# TYPE {self.app_name}_http_request_duration_seconds histogram")
            for (method, path), histogram in sorted(self._request_latency.items()):
                bucket_counts = histogram.get_bucket_counts()
                for bucket, count in bucket_counts.items():
                    lines.append(
                        f'{self.app_name}_http_request_duration_seconds_bucket{{method="{method}",path="{path}",le="{bucket}"}} {count}'
                    )
                lines.append(
                    f'{self.app_name}_http_request_duration_seconds_bucket{{method="{method}",path="{path}",le="+Inf"}} {histogram.count}'
                )
                lines.append(
                    f'{self.app_name}_http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {histogram.sum}'
                )
                lines.append(
                    f'{self.app_name}_http_request_duration_seconds_count{{method="{method}",path="{path}"}} {histogram.count}'
                )
            lines.append("")

        # Requests in progress
        if self._request_in_progress:
            lines.append(
                f"# HELP {self.app_name}_http_requests_in_progress Current in-progress requests"
            )
            lines.append(f"# TYPE {self.app_name}_http_requests_in_progress gauge")
            for (method, path), gauge in sorted(self._request_in_progress.items()):
                lines.append(
                    f'{self.app_name}_http_requests_in_progress{{method="{method}",path="{path}"}} {gauge.value}'
                )
            lines.append("")

        # Error count
        if self._error_count:
            lines.append(f"# HELP {self.app_name}_http_errors_total Total HTTP errors")
            lines.append(f"# TYPE {self.app_name}_http_errors_total counter")
            for (method, path, error_type), counter in sorted(self._error_count.items()):
                lines.append(
                    f'{self.app_name}_http_errors_total{{method="{method}",path="{path}",error_type="{error_type}"}} {counter.value}'
                )
            lines.append("")

        return "\n".join(lines)


# Global metrics registries keyed by app_name
_metrics_registries: dict[str, MetricsRegistry] = {}


def get_metrics_registry(app_name: str = "fastapi_bootstrap") -> MetricsRegistry:
    """Get the global metrics registry for an app.

    Args:
        app_name: Application name for metric prefixes

    Returns:
        The MetricsRegistry instance for the given app_name
    """
    global _metrics_registries
    if app_name not in _metrics_registries:
        _metrics_registries[app_name] = MetricsRegistry(app_name)
    return _metrics_registries[app_name]


def reset_metrics_registry() -> None:
    """Reset all global metrics registries (for testing)."""
    global _metrics_registries
    _metrics_registries = {}


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that collects HTTP request metrics.

    Collects:
    - Request count by method, path, and status code
    - Request duration histogram
    - In-progress requests gauge
    - Error counts by type

    Example:
        ```python
        from fastapi_bootstrap.metrics import MetricsMiddleware

        app.add_middleware(MetricsMiddleware)
        ```
    """

    def __init__(
        self,
        app: ASGIApp,
        app_name: str = "fastapi_bootstrap",
        exclude_paths: list[str] | None = None,
    ):
        """Initialize the metrics middleware.

        Args:
            app: The ASGI application
            app_name: Application name for metric prefixes
            exclude_paths: Paths to exclude from metrics (e.g., ["/healthz", "/metrics"])
        """
        super().__init__(app)
        self.registry = get_metrics_registry(app_name)
        self.exclude_paths = set(exclude_paths or ["/healthz", "/metrics", "/docs", "/redoc"])

    def _get_path_template(self, request: Request) -> str:
        """Get the path template for the request (uses route pattern, not actual path).

        This ensures /users/123 and /users/456 are grouped as /users/{id}
        """
        # Try to find matching route
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return getattr(route, "path", request.url.path)
        return request.url.path

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and collect metrics."""
        path = request.url.path

        # Skip excluded paths
        if path in self.exclude_paths:
            return await call_next(request)

        method = request.method
        path_template = self._get_path_template(request)

        # Track in-progress requests
        in_progress = self.registry.get_requests_in_progress(method, path_template)
        in_progress.inc()

        start_time = time.perf_counter()
        status_code = 500
        error_type = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            error_type = type(e).__name__
            raise
        finally:
            # Record duration
            duration = time.perf_counter() - start_time
            self.registry.get_request_latency(method, path_template).observe(duration)

            # Record request count
            self.registry.get_request_count(method, path_template, status_code).inc()

            # Record errors
            if error_type or status_code >= 500:
                error_label = error_type or "http_5xx"
                self.registry.get_error_count(method, path_template, error_label).inc()

            # Decrement in-progress
            in_progress.dec()


def get_metrics_router(
    path: str = "/metrics",
    include_in_schema: bool = False,
    tags: list[str] | None = None,
) -> APIRouter:
    """Create a router with the metrics endpoint.

    Args:
        path: Path for the metrics endpoint
        include_in_schema: Include in OpenAPI schema
        tags: Tags for the endpoint

    Returns:
        FastAPI APIRouter with metrics endpoint

    Example:
        ```python
        from fastapi_bootstrap.metrics import get_metrics_router

        app.include_router(get_metrics_router())
        # Metrics available at GET /metrics
        ```
    """
    router = APIRouter(tags=tags or ["monitoring"])

    @router.get(path, include_in_schema=include_in_schema)
    async def metrics() -> Response:
        """Export Prometheus metrics."""
        registry = get_metrics_registry()
        return Response(
            content=registry.export(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return router


__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "MetricsMiddleware",
    "MetricsRegistry",
    "get_metrics_registry",
    "get_metrics_router",
    "reset_metrics_registry",
]
