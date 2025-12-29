"""Test ResponseFormatter utility."""

from fastapi_bootstrap.response import ResponseFormatter


def test_success_response():
    """Test basic success response."""
    response = ResponseFormatter.success(data={"id": 1, "name": "John"}, message="User retrieved")

    assert response["success"] is True
    assert response["data"] == {"id": 1, "name": "John"}
    assert response["message"] == "User retrieved"
    assert "timestamp" in response


def test_success_response_default_message():
    """Test success response with default message."""
    response = ResponseFormatter.success(data={"test": "data"})

    assert response["success"] is True
    assert response["message"] == "Success"


def test_success_response_with_list():
    """Test success response with list data."""
    users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
    response = ResponseFormatter.success(data=users)

    assert response["success"] is True
    assert len(response["data"]) == 2


def test_success_response_with_none():
    """Test success response with None data."""
    response = ResponseFormatter.success(data=None)

    assert response["success"] is True
    assert response["data"] is None


def test_error_response():
    """Test basic error response."""
    response = ResponseFormatter.error(
        message="Validation failed", code="VALIDATION_ERROR", details={"field": "email"}
    )

    assert response["success"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"
    assert response["error"]["message"] == "Validation failed"
    assert response["error"]["details"] == {"field": "email"}
    assert "timestamp" in response


def test_error_response_without_details():
    """Test error response without details."""
    response = ResponseFormatter.error(message="Not found", code="NOT_FOUND")

    assert response["success"] is False
    assert response["error"]["code"] == "NOT_FOUND"
    assert response["error"]["details"] is None


def test_paginated_response():
    """Test paginated response."""
    items = [{"id": i} for i in range(1, 11)]
    response = ResponseFormatter.paginated(data=items, page=1, page_size=10, total_items=25)

    assert response["success"] is True
    assert len(response["data"]) == 10
    assert response["pagination"]["page"] == 1
    assert response["pagination"]["page_size"] == 10
    assert response["pagination"]["total_items"] == 25
    assert response["pagination"]["total_pages"] == 3
    assert response["pagination"]["has_next"] is True
    assert response["pagination"]["has_prev"] is False


def test_paginated_response_last_page():
    """Test paginated response on last page."""
    items = [{"id": i} for i in range(21, 26)]
    response = ResponseFormatter.paginated(data=items, page=3, page_size=10, total_items=25)

    assert response["pagination"]["page"] == 3
    assert response["pagination"]["has_next"] is False
    assert response["pagination"]["has_prev"] is True


def test_created_response():
    """Test created response convenience method."""
    response = ResponseFormatter.created(data={"id": 1, "name": "John"})

    assert response["success"] is True
    assert response["message"] == "Created successfully"
    assert response["data"]["id"] == 1


def test_updated_response():
    """Test updated response convenience method."""
    response = ResponseFormatter.updated(data={"id": 1, "name": "Jane"})

    assert response["success"] is True
    assert response["message"] == "Updated successfully"


def test_deleted_response():
    """Test deleted response convenience method."""
    response = ResponseFormatter.deleted()

    assert response["success"] is True
    assert response["message"] == "Deleted successfully"
    assert response["data"] is None


def test_deleted_response_custom_message():
    """Test deleted response with custom message."""
    response = ResponseFormatter.deleted(message="User deleted")

    assert response["message"] == "User deleted"
