"""Custom exception types for API error handling.

This module defines custom exception classes that are automatically
handled by the exception handler and converted to appropriate HTTP responses.
"""

from __future__ import annotations


class BadRequestHeaderError(Exception):
    """Exception raised when request headers are invalid or malformed.

    This exception is typically raised when:
    - Required headers are missing
    - Header values are in incorrect format
    - Header values fail validation

    Returns HTTP 400 Bad Request when raised.

    Example:
        ```python
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise BadRequestHeaderError("Missing or invalid Authorization header")
        ```
    """

    def __init__(self, exception: Exception | str = "") -> None:
        """Initialize the exception.

        Args:
            exception: Error message or underlying exception
        """
        self.exception = exception

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return str(self.exception)


class InvalidAccessTokenError(Exception):
    """Exception raised when access token is invalid, expired, or malformed.

    This exception is typically raised when:
    - Token signature validation fails
    - Token has expired
    - Token format is incorrect
    - Token has been revoked

    Returns HTTP 401 Unauthorized when raised.

    Example:
        ```python
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise InvalidAccessTokenError("Access token has expired")
        except jwt.InvalidTokenError:
            raise InvalidAccessTokenError("Invalid access token format")
        ```
    """

    def __init__(self, exception: Exception | str = "") -> None:
        """Initialize the exception.

        Args:
            exception: Error message or underlying exception
        """
        self.exception = exception

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return str(self.exception)
