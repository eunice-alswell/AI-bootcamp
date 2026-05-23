import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import Settings


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        content_length = int(request.headers.get("content-length") or 0)

        if content_length > self._settings.security_max_request_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body is too large."},
            )

        if not self._allow_request(client_host):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded."},
                headers={"Retry-After": str(self._settings.security_rate_limit_window_seconds)},
            )

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    def _allow_request(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self._settings.security_rate_limit_window_seconds
        timestamps = self._requests[key]

        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= self._settings.security_rate_limit_requests:
            return False

        timestamps.append(now)
        return True
