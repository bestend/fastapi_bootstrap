# Simple Example

Basic usage - logging, standardized responses, pagination

## Run

```bash
python examples/simple/app.py
# http://localhost:8000/docs
```

## Code

```python
import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, create_app, get_logger

logger = get_logger()
router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/hello")
async def hello(name: str = "World"):
    logger.info("Hello endpoint called", name=name)
    return {"message": f"Hello, {name}!"}


app = create_app(
    api_list=[router],
    title="Simple Example",
    version="1.0.0",
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Endpoints

```bash
# Hello
curl "http://localhost:8000/hello?name=World"
```

## Response Format

**Success:**
```json
{
  "message": "Hello, World!"
}
```

