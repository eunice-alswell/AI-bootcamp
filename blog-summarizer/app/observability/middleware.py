from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.correlation import (
    get_request_id,
    get_trace_id,
    new_request_id,
    reset_correlation_ids,
    set_correlation_ids,
)
from app.observability.metrics import metrics


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        trace_id = request.headers.get("X-Trace-ID") or request_id
        request_token, trace_token = set_correlation_ids(request_id, trace_id)
        start_time = perf_counter()

        response = None
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = get_request_id() or request_id
            response.headers["X-Trace-ID"] = get_trace_id() or trace_id
            return response
        finally:
            duration_ms = (perf_counter() - start_time) * 1000
            route = request.url.path
            metrics.increment("http.requests.total", method=request.method, path=route)
            metrics.observe_ms("http.request.duration", duration_ms, method=request.method, path=route)
            reset_correlation_ids(request_token, trace_token)
