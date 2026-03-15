"""
Logging middleware for request/response tracking.

Provides:
- Request ID generation and tracking
- Request timing
- Request/response logging with client IP and user-agent
- Sensitive data masking
- Separate access log file
"""
import re
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger, get_access_logger

logger = get_logger(__name__)
access_logger = get_access_logger()

# Sensitive headers to mask
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}

# Sensitive field patterns in request body (if logged)
SENSITIVE_FIELDS = {"password", "password_confirm", "current_password", "new_password", "token", "secret"}


def mask_sensitive_headers(headers: dict) -> dict:
    """
    Mask sensitive header values.

    Args:
        headers: Dictionary of headers

    Returns:
        Headers dict with sensitive values masked
    """
    masked = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            if key.lower() == "authorization":
                # Keep "Bearer" prefix but mask token
                if value.startswith("Bearer "):
                    masked[key] = "Bearer ***"
                else:
                    masked[key] = "***"
            else:
                masked[key] = "***"
        else:
            masked[key] = value
    return masked


def mask_sensitive_body(body: str) -> str:
    """
    Mask sensitive fields in request body.

    Args:
        body: JSON string of request body

    Returns:
        Body string with sensitive fields masked
    """
    if not body:
        return body

    # Simple regex-based masking for JSON fields
    for field in SENSITIVE_FIELDS:
        # Match "field": "value" patterns
        pattern = rf'("{field}"\s*:\s*")[^"]*(")'
        body = re.sub(pattern, r'\1***\2', body, flags=re.IGNORECASE)

    return body


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/Response logging middleware with Request ID tracking.

    Each request gets a unique ID (from X-Request-ID header or generated)
    that is logged and returned in response headers for tracing.

    Features:
    - Request ID generation and tracking
    - Client IP logging
    - User-agent logging
    - Sensitive header masking
    - Access log file
    - Request timing
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the logging middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.

        Checks X-Forwarded-For header first (for reverse proxy setups),
        then falls back to request.client.host.

        Args:
            request: Incoming request

        Returns:
            Client IP address or "unknown"
        """
        # Check X-Forwarded-For header (for reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client host
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_agent(self, request: Request) -> str:
        """
        Get user-agent from request headers.

        Args:
            request: Incoming request

        Returns:
            User-agent string or "-"
        """
        return request.headers.get("user-agent", "-")

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

        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = self._get_user_agent(request)

        # Mask sensitive headers for logging
        headers_to_log = mask_sensitive_headers(dict(request.headers))

        # Start timing
        start_time = time.time()

        # Log request start
        logger.debug(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id, "client_ip": client_ip}
        )

        # Access log entry (request)
        access_logger.info(
            f"[{request_id}] --> {client_ip} \"{request.method} {request.url.path} HTTP/{request.scope.get('http_version', '1.1')}\" "
            f"User-Agent: \"{user_agent}\""
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration in milliseconds
            duration_ms = (time.time() - start_time) * 1000

            # Log response completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
                extra={"request_id": request_id, "client_ip": client_ip}
            )

            # Access log entry (response)
            access_logger.info(
                f"[{request_id}] <-- {client_ip} \"{request.method} {request.url.path}\" "
                f"Status: {response.status_code} Duration: {duration_ms:.2f}ms"
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
                extra={"request_id": request_id, "client_ip": client_ip},
                exc_info=True
            )

            # Access log entry (error)
            access_logger.error(
                f"[{request_id}] <-- {client_ip} \"{request.method} {request.url.path}\" "
                f"Error: {type(e).__name__} Duration: {duration_ms:.2f}ms"
            )
            raise