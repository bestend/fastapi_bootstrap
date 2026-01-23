"""Logging setup and configuration for fastapi_bootstrap.

This module provides a unified logging setup using loguru-kit with support for:
- Standard logging interception
- JSON and text output formats
- OpenTelemetry trace context integration
- Message truncation for large payloads
"""

from __future__ import annotations

import os
import sys

from loguru_kit import get_logger as _get_logger
from loguru_kit import setup as _setup

from fastapi_bootstrap.util.etc import str2bool

sys.tracebacklimit = int(os.getenv("TRACEBACKLIMIT", "10"))
LOG_STRING_LENGTH = int(os.environ.get("LOG_STRING_LENGTH", "5000"))
LOG_JSON = str2bool(os.environ.get("LOG_JSON", "false"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging(*, use_fastapi_format: bool = True) -> None:
    """Setup loguru logging via loguru-kit.

    Args:
        use_fastapi_format: Ignored for backward compatibility.
            Request/response logging is handled by LoggingAPIRoute.
    """
    # Determine intercept targets
    intercept_loggers = ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]

    # Setup via loguru-kit
    _setup(
        level=LOG_LEVEL,
        json=LOG_JSON,
        truncate=LOG_STRING_LENGTH,
        intercept=intercept_loggers,
        otel=True,  # Enable OpenTelemetry trace context
        force=True,  # Allow reconfiguration
    )


def get_logger(name: str | None = None):
    """Get a logger instance.

    Args:
        name: Module name for context (typically __name__)

    Returns:
        Logger instance from loguru-kit
    """
    return _get_logger(name)
