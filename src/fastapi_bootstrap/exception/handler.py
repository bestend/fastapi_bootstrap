"""Centralized exception handling for FastAPI applications.

This module provides exception handlers that convert Python exceptions
into properly formatted JSON error responses with consistent structure.
"""

import functools
import json
import traceback

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from fastapi_bootstrap.exception import ErrorInfo
from fastapi_bootstrap.exception.definition import get_exception_definitions
from fastapi_bootstrap.log import get_logger
from fastapi_bootstrap.response import ResponseFormatter
from fastapi_bootstrap.util import get_trace_id

logger = get_logger()


def exception_message(e: Exception) -> str:
    """Format exception as a readable message.

    Args:
        e: The exception to format

    Returns:
        Formatted string with exception type and message
    """
    return f"{type(e).__name__}: {e!s}"


def error_to_json(obj):
    """Convert error objects to JSON-serializable format.

    Args:
        obj: The object to convert

    Returns:
        JSON-serializable representation
    """
    if isinstance(obj, ValueError):
        return str(obj)
    return obj


async def _generate_error_response_core(
    error_info: ErrorInfo, exc: Exception, do_error_log_detail: bool = True
):
    """Generate error response with logging.

    This is the core function that creates error responses with appropriate
    logging level and detail based on the exception type and environment.

    Args:
        error_info: Error information (status code, message, log level)
        exc: The exception that occurred
        do_error_log_detail: Whether to include detailed error information
                            (usually False in production)

    Returns:
        JSONResponse with error details and trace ID header
    """
    # Log the exception with the specified log level
    getattr(logger.opt(exception=exc), error_info.log_level)(str(exc))

    details: object | None = None

    if isinstance(exc, HTTPException):
        message = str(exc.detail)
        status_code = exc.status_code
    else:
        message = error_info.msg
        status_code = error_info.status_code

        if do_error_log_detail:
            if isinstance(exc, RequestValidationError):
                error_json = json.dumps(exc.errors(), default=error_to_json)
                details = json.loads(error_json)
                logger.error(details)
            else:
                details = exception_message(exc)
                logger.error(traceback.format_exc())

    content = ResponseFormatter.error(message=message, details=details)
    content["msg"] = message
    if details is not None:
        content["detail"] = details

    return JSONResponse(
        headers={"x-trace-id": get_trace_id()}, status_code=status_code, content=content
    )


@functools.lru_cache
def get_responses_for_exception():
    """Get OpenAPI response schemas for all registered exceptions.

    This is used to automatically document error responses in OpenAPI/Swagger.

    Returns:
        Dictionary mapping status codes to response schemas
    """
    responses = {}
    for _exception, error_info in get_exception_definitions().items():
        responses[error_info.status_code] = {
            "description": error_info.msg,
            "content": {"application/json": {"example": error_info}},
        }
    return responses


def add_exception_handler(app: FastAPI, stage: str):
    """Add exception handlers to FastAPI application.

    Registers handlers for all exceptions defined in exception_definitions.
    In production (stage="prod"), detailed error information is suppressed.

    Args:
        app: The FastAPI application instance
        stage: Environment stage ("dev", "staging", or "prod")
    """
    # Suppress detailed errors in production
    do_error_log_detail = stage != "prod"

    exception_definitions = get_exception_definitions()

    # Register handler for each exception type
    for exception, error_info in exception_definitions.items():

        @app.exception_handler(exception)
        async def exception_handler_func(request: Request, exc: Exception, error_info=error_info):
            """Handle specific exception type.

            Args:
                request: The incoming request (unused but required by FastAPI)
                exc: The exception that was raised
                error_info: Error information for this exception type

            Returns:
                JSON error response
            """
            return await _generate_error_response_core(error_info, exc, do_error_log_detail)


async def generate_error_response(exc: Exception, stage: str = "dev"):
    """Generate error response for an exception.

    This is used to manually generate error responses, typically from
    within route handlers or middleware.

    Args:
        exc: The exception that occurred
        stage: Environment stage ("dev", "staging", or "prod")

    Returns:
        JSON error response
    """
    # Suppress detailed errors in production
    do_error_log_detail = stage != "prod"

    exception_definitions = get_exception_definitions()

    # Default to generic Exception handler
    error_info = exception_definitions[Exception]

    # Find specific handler for this exception type
    for exception, cur_error_info in exception_definitions.items():
        if type(exc) is Exception:
            continue
        if type(exc) is exception:
            error_info = cur_error_info
            break

    return await _generate_error_response_core(error_info, exc, do_error_log_detail)
