import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, create_app, get_logger
from fastapi_bootstrap.config import BootstrapSettings

logger = get_logger()
router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/hello")
async def hello(name: str = "World"):
    logger.info("Hello endpoint called", name=name)
    return {"message": f"Hello, {name}!"}


settings = BootstrapSettings(title="Simple Example", version="1.0.0")
app = create_app(routers=[router], settings=settings)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
