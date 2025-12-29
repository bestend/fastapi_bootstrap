import json
import os
import sys
import traceback
from functools import partial

from loguru import logger
from opentelemetry.trace import (
    INVALID_SPAN,
    INVALID_SPAN_CONTEXT,
    get_current_span,
    get_tracer_provider,
)

from fastapi_bootstrap.log import truncate_strings_in_structure
from fastapi_bootstrap.util import str2bool

LOG_STRING_LENGTH = int(os.environ.get("LOG_STRING_LENGTH", "5000"))
LOG2JSON = str2bool(os.environ.get("LOG_JSON", "true"))


def sink_serializer(message):
    if LOG2JSON:
        exception = message.record["exception"]
        if exception is not None:
            message.record["exception"] = {
                "type": None if exception.type is None else exception.type.__name__,
                "value": exception.value,
                "traceback": traceback.format_exc(),
            }
        message.record["file"] = message.record["file"].path
        # lift extra
        message.record.update(message.record["extra"])
        del message.record["extra"]
        del message.record["process"]
        del message.record["thread"]
        out_str = json.dumps(message.record, default=str, ensure_ascii=False) + "\n"
    else:
        out_str = str(message)
    print(out_str, file=sys.stderr, end="")


def transform_record(record, log_format):
    # TODO: fix hard coding limit size

    record["level"] = record["level"].name.lower()
    try:
        data = json.loads(record["message"])
        record["message"] = json.dumps(truncate_strings_in_structure(data), ensure_ascii=False)
    except Exception:
        record["message"] = record["message"][:LOG_STRING_LENGTH]

    return log_format


def setup_logging():
    request_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <5}</level> | "
        "<cyan>{file}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<red>{extra[message_type]}</red> | "
        # "<magenta>{extra[client_ip]}</magenta> | "
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
        # "<magenta>{extra[client_ip]}</magenta> | "
        "<green>{trace_id}</green> | "
        "<blue>{extra[method]}</blue> | "
        "<yellow>{extra[path]}</yellow> | "
        "{extra[status_code]} | "
        "<level>{message}</level>\n{exception}"
    )

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    def log_level_filter(record):
        return record["level"].no >= logger.level(log_level).no

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

    logger.configure(**config, patcher=add_trace_context)
