"""
Custom ASGI middleware.

RequestIDMiddleware: Generates a unique X-Request-ID for every request,
attaches it to the response, and makes it available on request.state for
all log calls within that request's lifecycle.
"""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Attach a unique request ID to every incoming request.

    - Reads X-Request-ID from the incoming request if provided (e.g. by a
      load balancer), otherwise generates a new UUID4.
    - Stores it on `request.state.request_id` for downstream use.
    - Echoes it back in the response header X-Request-ID.
    - Emits a structured access log entry on completion with latency.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "HTTP request handled",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
            },
        )

        return response
