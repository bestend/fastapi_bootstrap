import os

import uvicorn
from fastapi import APIRouter

from fastapi_bootstrap import LoggingAPIRoute, create_app

router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/data")
async def get_data():
    return {"message": "CORS-enabled endpoint"}


app = create_app(
    api_list=[router],
    title="CORS Example",
    stage=os.getenv("STAGE", "dev"),
    cors_origins=os.getenv("ALLOWED_ORIGINS", "").split(",") or None,
)

if __name__ == "__main__":
    print(f"Stage: {os.getenv('STAGE', 'dev')}")
    print(f"Allowed origins: {os.getenv('ALLOWED_ORIGINS', '*')}")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
