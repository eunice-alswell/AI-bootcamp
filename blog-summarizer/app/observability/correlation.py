from contextvars import ContextVar
from uuid import uuid4

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_request_id() -> str | None:
    return request_id_context.get()


def get_trace_id() -> str | None:
    return trace_id_context.get()


def new_request_id() -> str:
    return str(uuid4())


def set_correlation_ids(request_id: str | None = None, trace_id: str | None = None):
    resolved_request_id = request_id or new_request_id()
    resolved_trace_id = trace_id or resolved_request_id
    request_token = request_id_context.set(resolved_request_id)
    trace_token = trace_id_context.set(resolved_trace_id)
    return request_token, trace_token


def reset_correlation_ids(request_token, trace_token) -> None:
    request_id_context.reset(request_token)
    trace_id_context.reset(trace_token)
