"""Example application using the Builder pattern.

This example demonstrates the new fluent Builder API for creating
FastAPI applications with fastapi_bootstrap.

Run:
    uvicorn app:app --reload
"""

from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, bootstrap

# Create router with automatic request/response logging
router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello from Builder Pattern!"}


@router.get("/users")
async def list_users():
    """List all users."""
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
    }


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user."""
    return {"id": user_id, "name": "User"}


# Build the application using the fluent builder pattern
app = (
    bootstrap()
    .title("Builder Pattern Example")
    .version("1.0.0")
    .stage("dev")  # Use "prod" for production
    # Configure logging
    .with_logging(level="DEBUG", json_output=False)
    # Enable CORS (auto-configured for dev stage)
    .with_cors()
    # Add security headers (skipped in dev by default)
    .with_security_headers()
    # Enable Prometheus metrics
    .with_metrics(endpoint="/metrics")
    # Add request ID and timing headers
    .with_request_id()
    .with_request_timing()
    # Configure health check
    .with_health_check(endpoint="/health")
    # Add the router
    .add_router(router)
    .build()
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
