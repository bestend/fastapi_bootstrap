"""Standard response formatting utilities.

This module provides utilities for creating consistent API response formats
across all endpoints. It ensures that all responses follow a standard structure,
making it easier for clients to parse and handle responses.
"""

from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import Field

from fastapi_bootstrap.type import BaseModel

# Generic type variable for response data
T = TypeVar("T")


class SuccessResponse[T](BaseModel):
    """Standard success response format.

    All successful API responses should follow this format for consistency.

    Attributes:
        success: Always True for success responses
        data: The actual response data (can be any type)
        message: Optional success message
        timestamp: ISO 8601 formatted timestamp

    Example:
        ```python
        from fastapi import APIRouter
        from fastapi_bootstrap.response import ResponseFormatter

        router = APIRouter()

        @router.get("/users/{user_id}")
        async def get_user(user_id: int):
            user = {"id": user_id, "name": "John"}
            return ResponseFormatter.success(
                data=user,
                message="User retrieved successfully"
            )

        # Returns:
        # {
        #     "success": true,
        #     "data": {"id": 1, "name": "John"},
        #     "message": "User retrieved successfully",
        #     "timestamp": "2024-12-28T22:50:00.123456Z"
        # }
        ```
    """

    success: bool = Field(default=True, description="Indicates successful response")
    data: T = Field(description="Response data")
    message: str = Field(default="Success", description="Success message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 formatted timestamp",
    )


class ErrorDetail(BaseModel):
    """Detailed error information.

    Attributes:
        code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        details: Optional additional error details (e.g., validation errors)
    """

    code: str = Field(description="Error code")
    message: str = Field(description="Error message")
    details: Any | None = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response format.

    All error responses should follow this format for consistency.

    Attributes:
        success: Always False for error responses
        error: Error details including code, message, and optional details
        timestamp: ISO 8601 formatted timestamp

    Example:
        ```python
        from fastapi import APIRouter, HTTPException
        from fastapi_bootstrap.response import ResponseFormatter

        @router.post("/users")
        async def create_user(name: str, email: str):
            if not email:
                return ResponseFormatter.error(
                    message="Validation failed",
                    code="VALIDATION_ERROR",
                    details={"email": "Email is required"}
                )

        # Returns:
        # {
        #     "success": false,
        #     "error": {
        #         "code": "VALIDATION_ERROR",
        #         "message": "Validation failed",
        #         "details": {"email": "Email is required"}
        #     },
        #     "timestamp": "2024-12-28T22:50:00.123456Z"
        # }
        ```
    """

    success: bool = Field(default=False, description="Indicates error response")
    error: ErrorDetail = Field(description="Error details")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 formatted timestamp",
    )


class PaginatedResponse[T](BaseModel):
    """Paginated response format.

    Used for endpoints that return paginated data.

    Attributes:
        success: Always True for success responses
        data: List of items for current page
        pagination: Pagination metadata
        message: Optional success message
        timestamp: ISO 8601 formatted timestamp
    """

    class PaginationMeta(BaseModel):
        """Pagination metadata."""

        page: int = Field(description="Current page number (1-indexed)")
        page_size: int = Field(description="Number of items per page")
        total_items: int = Field(description="Total number of items")
        total_pages: int = Field(description="Total number of pages")
        has_next: bool = Field(description="Whether there is a next page")
        has_prev: bool = Field(description="Whether there is a previous page")

    success: bool = Field(default=True, description="Indicates successful response")
    data: list[T] = Field(description="List of items")
    pagination: PaginationMeta = Field(description="Pagination metadata")
    message: str = Field(default="Success", description="Success message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 formatted timestamp",
    )


class ResponseFormatter:
    """Utility class for creating standard API responses.

    This class provides static methods to create consistent response formats
    across all API endpoints.

    Example:
        ```python
        from fastapi import APIRouter
        from fastapi_bootstrap.response import ResponseFormatter

        router = APIRouter()

        @router.get("/users")
        async def list_users():
            users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
            return ResponseFormatter.success(users)

        @router.get("/users/paginated")
        async def list_users_paginated(page: int = 1, page_size: int = 10):
            users = [...]  # Get users from database
            total = 100

            return ResponseFormatter.paginated(
                data=users,
                page=page,
                page_size=page_size,
                total_items=total
            )

        @router.get("/users/{user_id}")
        async def get_user(user_id: int):
            user = get_user_from_db(user_id)
            if not user:
                return ResponseFormatter.error(
                    message="User not found",
                    code="NOT_FOUND"
                )
            return ResponseFormatter.success(user)
        ```
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
    ) -> dict[str, Any]:
        """Create a standard success response.

        Args:
            data: The response data (can be dict, list, primitive, or None)
            message: Success message (default: "Success")

        Returns:
            Dictionary with standard success response format

        Example:
            ```python
            return ResponseFormatter.success(
                data={"user_id": 123, "name": "John"},
                message="User created successfully"
            )
            ```
        """
        return SuccessResponse(data=data, message=message).model_dump()

    @staticmethod
    def error(
        message: str,
        code: str = "ERROR",
        details: Any = None,
    ) -> dict[str, Any]:
        """Create a standard error response.

        Args:
            message: Error message
            code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
            details: Optional additional error details

        Returns:
            Dictionary with standard error response format

        Example:
            ```python
            return ResponseFormatter.error(
                message="Invalid email format",
                code="VALIDATION_ERROR",
                details={"field": "email", "value": "invalid"}
            )
            ```
        """
        error_detail = ErrorDetail(code=code, message=message, details=details)
        return ErrorResponse(error=error_detail).model_dump()

    @staticmethod
    def paginated(
        data: list[Any],
        page: int,
        page_size: int,
        total_items: int,
        message: str = "Success",
    ) -> dict[str, Any]:
        """Create a standard paginated response.

        Args:
            data: List of items for current page
            page: Current page number (1-indexed)
            page_size: Number of items per page
            total_items: Total number of items across all pages
            message: Optional success message

        Returns:
            Dictionary with standard paginated response format

        Example:
            ```python
            return ResponseFormatter.paginated(
                data=users,
                page=2,
                page_size=10,
                total_items=95,
                message="Users retrieved successfully"
            )
            ```
        """
        total_pages = (total_items + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        pagination = PaginatedResponse.PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

        return PaginatedResponse(data=data, pagination=pagination, message=message).model_dump()

    @staticmethod
    def created(
        data: Any = None,
        message: str = "Created successfully",
    ) -> dict[str, Any]:
        """Create a standard response for resource creation.

        Convenience method for POST requests that create resources.

        Args:
            data: The created resource data
            message: Success message (default: "Created successfully")

        Returns:
            Dictionary with standard success response format
        """
        return ResponseFormatter.success(data=data, message=message)

    @staticmethod
    def updated(
        data: Any = None,
        message: str = "Updated successfully",
    ) -> dict[str, Any]:
        """Create a standard response for resource updates.

        Convenience method for PUT/PATCH requests.

        Args:
            data: The updated resource data
            message: Success message (default: "Updated successfully")

        Returns:
            Dictionary with standard success response format
        """
        return ResponseFormatter.success(data=data, message=message)

    @staticmethod
    def deleted(message: str = "Deleted successfully") -> dict[str, Any]:
        """Create a standard response for resource deletion.

        Convenience method for DELETE requests.

        Args:
            message: Success message (default: "Deleted successfully")

        Returns:
            Dictionary with standard success response format
        """
        return ResponseFormatter.success(data=None, message=message)
