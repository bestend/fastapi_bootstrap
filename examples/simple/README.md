# Simple Example

Basic usage - logging, standardized responses, pagination

## Run

```bash
python examples/simple/app.py
# http://localhost:8000/v1/docs
```

## Code

```python
from fastapi import APIRouter
from fastapi_kit import LoggingAPIRoute, ResponseFormatter, create_app

router = APIRouter(route_class=LoggingAPIRoute, prefix="/api")

@router.get("/hello")
async def hello(name: str):
    return ResponseFormatter.success(
        data={"greeting": f"Hello, {name}!"},
        message="Greeting generated"
    )

@router.get("/users")
async def list_users(page: int = 1, page_size: int = 10):
    users = [...]  # DB query
    return ResponseFormatter.paginated(
        data=users,
        page=page,
        page_size=page_size,
        total_items=100
    )

app = create_app([router], title="Simple Example", prefix_url="/v1")
```

## Endpoints

```bash
# Hello
curl "http://localhost:8000/v1/api/hello?name=World"

# Users (paginated)
curl "http://localhost:8000/v1/api/users?page=1&page_size=5"

# Create user
curl -X POST "http://localhost:8000/v1/api/users?name=Alice&email=alice@example.com"
```

## Response Format

**Success:**
```json
{
  "success": true,
  "data": {...},
  "message": "Success"
}
```

**Paginated:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "total_pages": 10,
    "has_next": true
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```

