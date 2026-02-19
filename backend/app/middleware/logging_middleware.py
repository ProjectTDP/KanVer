"""
Logging middleware for request/response tracking.

Provides:
- Request ID generation and tracking
- Request timing
- Request/response logging
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/Response logging middleware with Request ID tracking.

    Each request gets a unique ID (from X-Request-ID header or generated)
    that is logged and returned in response headers for tracing.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the logging middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log with timing information.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Request-ID header
        """
        # Generate or get Request ID from header
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Attach request_id to request state for access in routes
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration in milliseconds
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
                extra={"request_id": request_id}
            )

            # Add Request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration_ms:.2f}ms",
                extra={"request_id": request_id},
                exc_info=True
            )
            raise
