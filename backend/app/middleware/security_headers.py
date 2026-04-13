"""
Security Headers Middleware for KanVer API.

Adds security-related HTTP headers to all responses:
- X-Content-Type-Options: nosniff (prevents MIME sniffing)
- X-Frame-Options: DENY (prevents clickjacking)
- X-XSS-Protection: 1; mode=block (XSS protection)
- Strict-Transport-Security: HSTS (HTTPS only, production only)

These headers help protect against common web vulnerabilities.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Security headers protect against:
    - MIME type sniffing attacks
    - Clickjacking attacks
    - XSS attacks
    - Man-in-the-middle attacks (HSTS)

    HSTS is only enabled in production (DEBUG=False) because it requires HTTPS.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the security headers middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with security headers added
        """
        # Process the request
        response = await call_next(request)

        # Add security headers
        # Prevents browser from MIME-sniffing the response
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevents the page from being embedded in an iframe (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"

        # Enables browser's XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - Only in production (requires HTTPS)
        # max-age=31536000 = 1 year
        # includeSubDomains applies to all subdomains
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response