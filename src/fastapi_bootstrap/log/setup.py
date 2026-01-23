"""Logging setup and configuration for fastapi_bootstrap.

This module provides a unified logging setup using loguru with support for:
- Standard logging interception
- JSON and text output formats
- OpenTelemetry trace context integration
- Request/response logging with custom formats
- Message truncation for large payloads
"""

import functools
import json
import logging
import os
import sys
import traceback
from functools import lru_cache, partial
from typing import Any

from loguru import logger
from loguru._handler import Handler

try:
    from opentelemetry.trace import (
        INVALID_SPAN,
        INVALID_SPAN_CONTEXT,
        get_current_span,
        get_tracer_provider,
    )

    OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    OTEL_AVAILABLE = False
    INVALID_SPAN = None  # type: ignore
    INVALID_SPAN_CONTEXT = None  # type: ignore

    def get_current_span(context: Any | None = None) -> Any:
        raise RuntimeError("OpenTelemetry is not available")

    def get_tracer_provider() -> Any:
        raise RuntimeError("OpenTelemetry is not available")


from fastapi_bootstrap.util.etc import str2bool

# Configuration from environment
sys.tracebacklimit = int(os.getenv("TRACEBACKLIMIT", "10"))
LOG_STRING_LENGTH = int(os.environ.get("LOG_STRING_LENGTH", "5000"))
LOG_JSON = str2bool(os.environ.get("LOG_JSON", "false"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def truncate_strings_in_structure(struct: Any) -> Any:
    """Recursively truncate long strings in nested data structures.

    This function is **pure** (does not mutate the input).

    Args:
        struct: Any data structure (dict, list, str, etc.)

    Returns:
        A new structure with long strings replaced with "[[truncated]]".
    """
    if isinstance(struct, str):
        return "[[truncated]]" if len(struct) > 2000 else struct

    if isinstance(struct, dict):
        return {k: truncate_strings_in_structure(v) for k, v in struct.items()}

    if isinstance(struct, list):
        return [truncate_strings_in_structure(item) for item in struct]

    return struct


# Patch loguru's Handler to customize JSON serialization for fluentd compatibility
def _serialize_record(self, text, record):
    """Custom serialize_record that avoids time parsing conflicts with fluentd."""
    exception = record["exception"]

    if exception is not None:
        exception = {
            "type": None if exception.type is None else exception.type.__name__,
            "value": exception.value,
            "traceback": bool(exception.traceback),
        }

    serializable = {
        "text": text,
        "record": {
            "elapsed": {
                "repr": record["elapsed"],
                "seconds": record["elapsed"].total_seconds(),
            },
            "exception": exception,
            "extra": record["extra"],
            "file": {"name": record["file"].name, "path": record["file"].path},
            "function": record["function"],
            "level": {
                "icon": record["level"].icon,
                "name": record["level"].name,
                "no": record["level"].no,
            },
            "line": record["line"],
            "message": record["message"],
            "module": record["module"],
            "name": record["name"],
            "process": {"id": record["process"].id, "name": record["process"].name},
            "thread": {"id": record["thread"].id, "name": record["thread"].name},
            # time field removed to avoid fluentd parsing conflicts
        },
    }
    return json.dumps(serializable, default=str, ensure_ascii=False) + "\n"


Handler._serialize_record = _serialize_record  # type: ignore[assignment]


class InterceptHandler(logging.Handler):
    """Logging handler that intercepts standard logging and redirects to loguru."""

    def emit(self, record):
        """Emit a log record by forwarding to loguru."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Get the calling frame, skipping logging and sentry frames
        try:
            import sentry_sdk  # type: ignore

            sentry_file = sentry_sdk.integrations.logging.__file__
        except ImportError:
            sentry_file = None
        except Exception:
            sentry_file = None

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename in tuple(
            p for p in (logging.__file__, sentry_file) if p is not None
        ):
            frame = frame.f_back
            depth += 1

        # Filter out noise from healthcheck calls
        msgs_to_filter = ["GET /healthz"]
        message = record.getMessage()

        for msg in msgs_to_filter:
            if msg in message:
                return

        logger.opt(depth=depth, exception=record.exc_info).log(level, message)


def intercept_standard_logging():
    """Intercept all standard logging and redirect to loguru."""
    log_level_no = logging.getLevelName(LOG_LEVEL)

    logging.captureWarnings(True)
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level_no)

    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Global exception hook
    def excepthook(exc_type, value, exc_traceback):
        logger.opt(exception=(exc_type, value, exc_traceback)).error(value)

    sys.excepthook = excepthook


def sink_serializer(message):
    """Custom sink that outputs JSON or text format based on LOG_JSON setting."""
    if LOG_JSON:
        exception = message.record["exception"]
        if exception is not None:
            message.record["exception"] = {
                "type": None if exception.type is None else exception.type.__name__,
                "value": exception.value,
                "traceback": traceback.format_exc(),
            }
        message.record["file"] = message.record["file"].path
        # Lift extra fields to top level for easier parsing
        message.record.update(message.record["extra"])
        del message.record["extra"]
        del message.record["process"]
        del message.record["thread"]
        out_str = json.dumps(message.record, default=str, ensure_ascii=False) + "\n"
    else:
        out_str = str(message)
    print(out_str, file=sys.stderr, end="")


def transform_record(record, log_format):
    """Transform log record to apply message truncation and formatting.

    Args:
        record: The log record
        log_format: The format string to use

    Returns:
        The format string (loguru uses this as the template)
    """
    record["level"] = record["level"].name.lower()
    try:
        data = json.loads(record["message"])
        record["message"] = json.dumps(truncate_strings_in_structure(data), ensure_ascii=False)
    except Exception:
        record["message"] = record["message"][:LOG_STRING_LENGTH]

    return log_format


def setup_logging(*, use_fastapi_format: bool = True):
    """Setup loguru logging with optional FastAPI request/response formatting.

    Args:
        use_fastapi_format: If True, use separate request/response log formats
                          with trace context. If False, use simple format.
    """
    intercept_standard_logging()

    if use_fastapi_format:
        _setup_fastapi_logging()
    else:
        _setup_simple_logging()


def _setup_simple_logging():
    """Setup simple logging format (for non-FastAPI usage)."""
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <5}</level> | "
        "<cyan>{file}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>\n{exception}"
    )

    def limit_message_format(record, log_format):
        try:
            data = json.loads(record["message"])
            record["message"] = json.dumps(truncate_strings_in_structure(data), ensure_ascii=False)
        except Exception:
            record["message"] = record["message"][:LOG_STRING_LENGTH]
        return log_format

    def log_level_filter(record):
        return record["level"].no >= logger.level(LOG_LEVEL).no

    config = {
        "handlers": [
            {
                "sink": sys.stderr,
                "format": functools.partial(limit_message_format, log_format=log_format),
                "serialize": LOG_JSON,
                "enqueue": False,
                "backtrace": True,
                "diagnose": True,
                "filter": log_level_filter,
            }
        ]
    }

    logger.configure(**config)  # type: ignore


def _setup_fastapi_logging():
    """Setup FastAPI-specific logging with request/response formats and trace context."""
    request_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <5}</level> | "
        "<cyan>{file}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<red>{extra[message_type]}</red> | "
        "<green>{trace_id}</green> | "
        "<blue>{extra[method]}</blue> | "
        "<yellow>{extra[path]}</yellow> | "
        "<level>{message}</level>\n{exception}"
    )
    response_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <5}</level> | "
        "<cyan>{file}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<red>{extra[message_type]}</red> | "
        "<green>{trace_id}</green> | "
        "<blue>{extra[method]}</blue> | "
        "<yellow>{extra[path]}</yellow> | "
        "{extra[status_code]} | "
        "<level>{message}</level>\n{exception}"
    )

    def log_level_filter(record):
        return record["level"].no >= logger.level(LOG_LEVEL).no

    config = {
        "handlers": [
            {
                "sink": sink_serializer,
                "format": partial(transform_record, log_format=request_format),
                "filter": lambda record: "status_code" not in record["extra"]
                and log_level_filter(record),
                "enqueue": False,
                "backtrace": True,
                "diagnose": True,
            },
            {
                "sink": sink_serializer,
                "format": partial(transform_record, log_format=response_format),
                "filter": lambda record: "status_code" in record["extra"]
                and log_level_filter(record),
                "enqueue": False,
                "backtrace": True,
                "diagnose": True,
            },
        ],
        "extra": {"message_type": "request", "method": "", "path": "", "status_code": 0},
    }

    if OTEL_AVAILABLE:
        patcher = _create_otel_patcher()
        logger.configure(**config, patcher=patcher)  # type: ignore
    else:
        # Add dummy trace context when OpenTelemetry is not available
        def add_dummy_trace_context(record):
            record["trace_id"] = "0"
            record["span_id"] = "0"
            record["trace_sampled"] = False
            record["service_name"] = ""

        logger.configure(**config, patcher=add_dummy_trace_context)  # type: ignore


def _create_otel_patcher():
    """Create OpenTelemetry trace context patcher for log records."""
    provider = get_tracer_provider()
    service_name = None

    def add_trace_context(record):
        record["trace_id"] = "0"
        record["span_id"] = "0"
        record["trace_sampled"] = False

        nonlocal service_name
        if service_name is None:
            resource = getattr(provider, "resource", None)
            service_name = resource.attributes.get("service.name") or "" if resource else ""

        record["service_name"] = service_name

        span = get_current_span()
        if span != INVALID_SPAN:
            ctx = span.get_span_context()
            if ctx != INVALID_SPAN_CONTEXT:
                record["trace_id"] = format(ctx.trace_id, "032x")
                record["span_id"] = format(ctx.span_id, "016x")
                record["trace_sampled"] = ctx.trace_flags.sampled

    return add_trace_context


@lru_cache
def get_logger():
    """Get the configured logger instance.

    This function is cached so logging is only setup once.

    Returns:
        The configured loguru logger
    """
    setup_logging(use_fastapi_format=False)
    return logger
