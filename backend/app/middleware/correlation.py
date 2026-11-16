"""Request correlation and HTTP metrics middleware.

Following architectural rules:
- Injects or propagates X-Request-ID across all requests and responses.
- Binds correlation ID to contextvars for structured logging across async calls.
- Bounds metric label cardinality by using FastAPI route templates (e.g. '/api/products/{id}')
  rather than raw request paths with high-cardinality IDs.
- Measures and records request processing duration.
"""

import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import set_correlation_id
from app.core.metrics import metrics

logger = logging.getLogger(__name__)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware attaching correlation ID and recording HTTP request metrics."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 1. Extract or generate request correlation ID
        correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = uuid.uuid4().hex
        set_correlation_id(correlation_id)
        request.state.request_id = correlation_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            # Record failed request
            metrics.record_http_request(
                method=request.method,
                route="/unhandled_exception",
                status_code=500,
                duration_seconds=duration,
            )
            logger.error("Unhandled error processing request: %s", exc, exc_info=True)
            raise

        duration = time.perf_counter() - start_time

        # 2. Extract bounded route template to prevent unbounded metric cardinality
        route = request.scope.get("route")
        if route and hasattr(route, "path"):
            route_template = getattr(route, "path")
        elif response.status_code == 404:
            route_template = "/unmatched_path"
        else:
            route_template = request.url.path

        # 3. Record Prometheus metrics
        metrics.record_http_request(
            method=request.method,
            route=route_template,
            status_code=response.status_code,
            duration_seconds=duration,
        )

        # 4. Attach correlation ID to response headers
        response.headers["X-Request-ID"] = correlation_id

        # 5. Log structured request outcome
        logger.info(
            "HTTP %s %s -> %d (%.2fms)",
            request.method,
            route_template,
            response.status_code,
            duration * 1000,
        )

        return response
