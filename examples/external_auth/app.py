import uvicorn
from fastapi import APIRouter, Header

from fastapi_bootstrap import LoggingAPIRoute, create_app
from fastapi_bootstrap.config import BootstrapSettings, SecuritySettings

router = APIRouter(route_class=LoggingAPIRoute)


@router.get("/public")
async def public():
    return {"message": "Public endpoint"}


@router.get("/protected")
async def protected(
    x_user_email: str = Header(None),
    x_user_id: str = Header(None),
):
    return {
        "message": "Protected by external auth",
        "email": x_user_email,
        "user_id": x_user_id,
    }


settings = BootstrapSettings(
    title="External Auth Example",
    security=SecuritySettings(add_external_basic_auth=True),
)
app = create_app(routers=[router], settings=settings)

if __name__ == "__main__":
    print("External auth example - Gateway/Ingress handles authentication")
    print("Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
