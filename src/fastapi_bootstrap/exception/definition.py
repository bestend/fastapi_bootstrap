"""Exception definitions and mappings.

This module defines the mapping between exception types and their
corresponding error information (status code, message, log level).
"""

import functools

from fastapi import status
from fastapi.exceptions import HTTPException, RequestValidationError

from fastapi_bootstrap.exception.error_info import ErrorInfo
from fastapi_bootstrap.exception.type import BadRequestHeaderError, InvalidAccessTokenError


@functools.lru_cache
def get_exception_definitions():
    """Get the exception-to-error-info mapping.

    This function returns a dictionary mapping exception types to ErrorInfo objects.
    It's cached to avoid recreating the dictionary on each call.

    Returns:
        Dictionary mapping exception types to ErrorInfo

    Example:
        ```python
        # Add custom exception
        from fastapi_bootstrap.exception import ErrorInfo, get_exception_definitions

        class CustomError(Exception):
            pass

        # Register custom exception
        get_exception_definitions()[CustomError] = ErrorInfo(
            status_code=418,
            msg="I'm a teapot",
            log_level="info"
        )
        ```
    """
    return {
        # Pydantic validation errors (malformed request data)
        RequestValidationError: ErrorInfo(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            msg="bad request",
            log_level="warning",
        ),
        # Invalid request headers
        BadRequestHeaderError: ErrorInfo(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="invalid request header",
            log_level="warning",
        ),
        # Request timeout
        TimeoutError: ErrorInfo(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            msg="request timeout",
            log_level="error",
        ),
        # Runtime errors (unexpected errors during execution)
        RuntimeError: ErrorInfo(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="internal server error",
            log_level="error",
        ),
        # Generic exception (catch-all)
        Exception: ErrorInfo(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="internal server error",
            log_level="error",
        ),
        # Invalid or expired access token
        InvalidAccessTokenError: ErrorInfo(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="invalid access token",
            log_level="warning",
        ),
        # FastAPI HTTP exceptions (used for custom error responses)
        HTTPException: ErrorInfo(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="bad request",
            log_level="warning",
        ),
    }
