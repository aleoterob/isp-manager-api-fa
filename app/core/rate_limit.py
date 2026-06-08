import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    _hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        limit = 120
        if request.url.path == "/auth/signup" and request.method == "POST":
            limit = 5
        elif request.url.path == "/auth/login" and request.method == "POST":
            limit = 10
        elif request.url.path == "/auth/refresh" and request.method == "POST":
            limit = 30

        key = (
            f"{request.client.host if request.client else 'unknown'}:"
            f"{request.method}:{request.url.path}"
        )
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= limit:
            return Response(status_code=429)
        bucket.append(now)
        return await call_next(request)
