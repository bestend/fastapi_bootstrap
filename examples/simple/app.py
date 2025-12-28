"""Simple example of using FastAPI Kit.

This example shows the basic usage of FastAPI Kit with minimal configuration.
"""

import uvicorn
from fastapi import APIRouter

from fastapi_kit import LoggingAPIRoute, ResponseFormatter, create_app, get_logger

# Create logger
logger = get_logger()

# Create API router with automatic logging
router = APIRouter(route_class=LoggingAPIRoute, prefix="/api", tags=["demo"])


@router.get("/hello")
async def hello(name: str = "World"):
    """Say hello with standard response format."""
    logger.info(f"Hello endpoint called with name: {name}")
    return ResponseFormatter.success(
        data={"greeting": f"Hello, {name}!"}, message="Greeting generated successfully"
    )


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID with standard response format."""
    logger.info(f"Fetching user {user_id}")

    # Simulate user not found
    if user_id > 100:
        return ResponseFormatter.error(message="User not found", code="NOT_FOUND")

    user = {"id": user_id, "name": "John Doe", "email": "john@example.com"}
    return ResponseFormatter.success(data=user, message="User retrieved successfully")


@router.get("/users")
async def list_users(page: int = 1, page_size: int = 10):
    """List users with pagination."""
    logger.info(f"Listing users - page {page}, size {page_size}")

    # Simulate paginated data
    total_users = 95
    start = (page - 1) * page_size
    end = start + page_size

    users = [
        {"id": i, "name": f"User {i}", "email": f"user{i}@example.com"}
        for i in range(start + 1, min(end + 1, total_users + 1))
    ]

    return ResponseFormatter.paginated(
        data=users,
        page=page,
        page_size=page_size,
        total_items=total_users,
        message="Users retrieved successfully",
    )


@router.post("/users")
async def create_user(name: str, email: str):
    """Create a new user with standard response format."""
    logger.info(f"Creating user: {name}")

    # Validate input
    if not email or "@" not in email:
        return ResponseFormatter.error(
            message="Invalid email format",
            code="VALIDATION_ERROR",
            details={"field": "email", "value": email},
        )

    user = {"id": 1, "name": name, "email": email}
    return ResponseFormatter.created(data=user, message="User created successfully")


# Create FastAPI app with all features
app = create_app(
    api_list=[router],
    title="FastAPI Kit Demo",
    version="1.0.0",
    prefix_url="/v1",
    docs_enable=True,
    health_check_api="/healthz",
    graceful_timeout=0,  # No delay on shutdown for dev
    stage="dev",  # dev, staging, or prod
)

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

