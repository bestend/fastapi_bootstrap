from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Get client IP address from request, checking X-Forwarded-For header first."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for is not None:
        return forwarded_for
    return request.scope["client"][0]
