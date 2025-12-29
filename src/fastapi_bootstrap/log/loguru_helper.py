import functools
import json
import logging
import os
import sys

from loguru import logger
from loguru._handler import Handler

from fastapi_bootstrap.util.etc import str2bool

sys.tracebacklimit = int(os.getenv("TRACEBACKLIMIT", 10))


def truncate_strings_in_structure(struct):
    if isinstance(struct, str) and len(struct) > 2000:
        return "[[truncated]]"

    elif isinstance(struct, dict):
        for k, v in struct.items():
            struct[k] = truncate_strings_in_structure(v)

    elif isinstance(struct, list):
        for idx, item in enumerate(struct):
            struct[idx] = truncate_strings_in_structure(item)

    return struct


# TODO fluentd의 time 파싱하는 부분과 충돌로 인해서 제거
def _serialize_record(self, text, record):
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
            # "time": {"repr": record["time"], "timestamp": record["time"].timestamp()},
        },
    }
    return json.dumps(serializable, default=str, ensure_ascii=False) + "\n"


Handler._serialize_record = _serialize_record  # type: ignore[assignment]


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        try:
            import sentry_sdk

            sentry_file = sentry_sdk.integrations.logging.__file__
        except Exception:
            sentry_file = None

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename in tuple(
            p for p in (logging.__file__, sentry_file) if p is not None
        ):
            frame = frame.f_back
            depth += 1

        msgs_to_filter = ["GET /healthz"]  # healthcheck calls

        for msg in msgs_to_filter:
            if msg not in record.getMessage():
                logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def intercept_standard_logging():
    # logging
    log_level_no = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO").upper())

    logging.captureWarnings(True)
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level_no)

    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # global except hook
    def excepthook(exc_type, value, exc_traceback):
        logger.opt(exception=(exc_type, value, exc_traceback)).error(value)

    sys.excepthook = excepthook


def setup_logging():
    intercept_standard_logging()

    log_json = str2bool(os.environ.get("LOG_JSON", "false"))
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <5}</level> | "
        "<cyan>{file}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>\n{exception}"
    )

    def limit_message_format(record, log_format):
        # TODO: fix hard coding limit size
        try:
            data = json.loads(record["message"])
            record["message"] = json.dumps(truncate_strings_in_structure(data), ensure_ascii=False)
        except Exception:
            record["message"] = record["message"][:5000]

        return log_format

    def log_level_filter(record):
        return record["level"].no >= logger.level(log_level).no

    config = {
        "handlers": [
            {
                "sink": sys.stderr,
                "format": functools.partial(limit_message_format, log_format=log_format),
                "serialize": log_json,
                "enqueue": False,
                "backtrace": True,
                "diagnose": True,
                "filter": log_level_filter,
            }
        ]
    }

    logger.configure(**config)


@functools.lru_cache
def get_logger():
    setup_logging()

    return logger
