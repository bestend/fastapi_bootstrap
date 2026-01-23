import contextlib
import time
from collections.abc import Callable

from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from loguru import logger
from uvicorn.protocols.utils import get_path_with_query_string

from fastapi_bootstrap.exception import generate_error_response
from fastapi_bootstrap.util import get_trace_id


def get_client_ip(request: Request) -> str:
    """Get client IP address from request, checking X-Forwarded-For header first."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for is not None:
        return forwarded_for
    return request.scope["client"][0]


class LoggingAPIRoute(APIRoute):
    """Enhanced APIRoute with automatic request/response logging.

    This custom route class automatically logs all incoming requests and outgoing
    responses with structured logging. It also:
    - Adds trace IDs to all responses
    - Logs request/response bodies (when applicable)
    - Tracks request duration
    - Captures exceptions and generates proper error responses

    Usage:
        ```python
        from fastapi import APIRouter
        from fastapi_bootstrap import LoggingAPIRoute

        router = APIRouter(route_class=LoggingAPIRoute)

        @router.get("/users")
        async def get_users():
            return {"users": []}
        ```

    The logging output includes:
    - Timestamp
    - Log level
    - Request method and path
    - Client IP address
    - Trace ID for request correlation
    - Request/response bodies
    - Response status code
    - Request duration
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()

            info = await self.extract_request_info(request)
            with logger.contextualize(**info):
                await self._request_logging(request)
                try:
                    response = await original_route_handler(request)
                except HTTPException:
                    raise  # Allow app-level exception handlers to process
                except Exception as exc:
                    response = await generate_error_response(exc)

                response.headers["x-trace-id"] = get_trace_id()
                end_time = time.time()
                extra = request.state.extra if hasattr(request.state, "extra") else {}
                extra["duration"] = end_time - start_time

                with logger.contextualize(**info, **extra):
                    await self._response_logging(request, response)
                return response

        return custom_route_handler

    @staticmethod
    def _has_json_body(request: Request) -> bool:
        return bool(
            request.method in ("POST", "PUT", "PATCH")
            and request.headers.get("content-type") == "application/json"
        )

    async def _request_logging(self, request: Request):
        if self._has_json_body(request):
            request_body = await request.body()
            msg = request_body.decode("UTF-8")
        else:
            msg = "binary"
        logger.bind(message_type="request").info(msg)

    async def _response_logging(self, request: Request, response: Response):
        def log_response(msg, status_code):
            cur_logger = logger.bind(message_type="response", status_code=str(status_code))
            if 200 <= status_code < 300:
                log_func = cur_logger.info
            elif 300 <= status_code < 500:
                log_func = cur_logger.warning
            else:
                log_func = cur_logger.error
            log_func(msg)

        msg = "binary"
        if isinstance(response, JSONResponse):
            response_body = response.body
            with contextlib.suppress(UnicodeDecodeError):
                # Convert memoryview to bytes if needed
                body_bytes = (
                    bytes(response_body) if isinstance(response_body, memoryview) else response_body
                )
                msg = body_bytes.decode("utf-8")

        log_response(msg, response.status_code)

    async def extract_request_info(self, request: Request):
        return {
            "uri": request.scope["path"],
            "path": get_path_with_query_string(request.scope),  # type: ignore[arg-type]
            "method": request.scope["method"],
            "client_ip": get_client_ip(request),
        }
