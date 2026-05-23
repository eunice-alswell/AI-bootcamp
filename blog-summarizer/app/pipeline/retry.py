import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    attempts: int,
    backoff_seconds: float,
    retryable_exceptions: tuple[type[Exception], ...],
) -> T:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return await operation()
        except retryable_exceptions as exc:
            last_error = exc
            if attempt == attempts - 1:
                break
            await asyncio.sleep(backoff_seconds * (2**attempt))
    raise last_error or RuntimeError("Retry operation failed without an exception.")
