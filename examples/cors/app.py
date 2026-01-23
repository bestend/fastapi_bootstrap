import os

import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, create_app
from fastapi_bootstrap.config import BootstrapSettings, CORSSettings, Stage

router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/data")
async def get_data():
    return {"message": "CORS-enabled endpoint"}


stage_str = os.getenv("STAGE", "dev")
stage = Stage(stage_str) if stage_str in [s.value for s in Stage] else Stage.DEV

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
cors_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()] or None

settings = BootstrapSettings(
    title="CORS Example",
    stage=stage,
    cors=CORSSettings(origins=cors_origins or []),
)
app = create_app(routers=[router], settings=settings)

if __name__ == "__main__":
    print(f"Stage: {stage}")
    print(f"Allowed origins: {cors_origins or '*'}")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
