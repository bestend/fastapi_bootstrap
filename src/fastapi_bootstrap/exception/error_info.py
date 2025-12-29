"""Error information model for exception handling.

This module defines the ErrorInfo model that describes how exceptions
should be converted to HTTP error responses.
"""

from pydantic import Field

from fastapi_bootstrap.type import BaseModel


class ErrorInfo(BaseModel):
    """Error information for exception-to-response mapping.

    This model defines how an exception should be converted to an HTTP response,
    including the status code, message, and logging level.

    Attributes:
        response_id: Unique identifier for the response (aliased as "id" in JSON)
        status_code: HTTP status code to return (default: 500)
        msg: Human-readable error message
        detail: Detailed error information (usually empty, filled at runtime)
        log_level: Logging level for this error ("debug", "info", "warning", "error", "critical")

    Example:
        ```python
        from fastapi_bootstrap.exception import ErrorInfo

        custom_error_info = ErrorInfo(
            status_code=404,
            msg="Resource not found",
            detail="The requested user ID does not exist",
            log_level="warning"
        )
        ```
    """

    response_id: str = Field(default="response_id", alias="id")
    status_code: int = 500
    msg: str = "Internal Server Error"
    detail: str = ""
    log_level: str = "error"
