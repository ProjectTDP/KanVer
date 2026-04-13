"""
Rate limiter middleware for KanVer API.

Provides IP-based rate limiting with:
- Configurable requests per minute
- Stricter limits for authentication endpoints
- Rate limit headers in response
- In-memory tracking (suitable for MVP, Redis for production)

Headers Added:
- X-RateLimit-Limit: Maximum requests allowed per period
- X-RateLimit-Remaining: Remaining requests in current period
- Retry-After: Seconds until rate limit resets (when limited)
"""
import time
from collections import defaultdict
from typing import Callable, Dict, List, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory rate limiter with IP-based tracking.

    Features:
    - Tracks requests per IP within a sliding time window
    - Stricter limits for authentication endpoints
    - Returns rate limit headers in response
    - Logs rate limit violations

    Note: This is an in-memory implementation suitable for MVP.
    For production with multiple workers/servers, use Redis.
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 100,
        auth_requests_per_minute: int = 10
    ):
        """
        Initialize the rate limiter middleware.

        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute for regular endpoints
            auth_requests_per_minute: Maximum requests per minute for auth endpoints
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        self.period_seconds = settings.RATE_LIMIT_PERIOD_SECONDS

        # IP -> List of timestamps
        # Using defaultdict to automatically create empty lists
        self._requests: Dict[str, List[float]] = defaultdict(list)

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
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def _is_rate_limited(
        self,
        ip: str,
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check if IP has exceeded rate limit.

        Uses a sliding window approach - removes old timestamps
        outside the current window before checking.

        Args:
            ip: Client IP address
            limit: Maximum requests allowed

        Returns:
            Tuple of (is_limited, retry_after_seconds, remaining_requests)
        """
        now = time.time()
        window_start = now - self.period_seconds

        # Clean old requests outside the window
        self._requests[ip] = [ts for ts in self._requests[ip] if ts > window_start]

        current_count = len(self._requests[ip])

        if current_count >= limit:
            # Calculate retry_after based on oldest request in window
            oldest_request = self._requests[ip][0] if self._requests[ip] else now
            retry_after = int(oldest_request - window_start) + 1
            return True, retry_after, 0

        # Add current request timestamp
        self._requests[ip].append(now)
        remaining = limit - current_count - 1

        return False, 0, remaining

    def _get_limit_for_path(self, path: str) -> int:
        """
        Get rate limit based on request path.

        Auth endpoints have stricter limits to prevent brute force attacks.

        Args:
            path: Request path

        Returns:
            Rate limit for the path
        """
        # Stricter limit for authentication endpoints
        if path.startswith("/api/auth/login") or path.startswith("/api/auth/refresh"):
            return self.auth_requests_per_minute

        # Regular limit for other endpoints
        return self.requests_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with rate limit headers

        Raises:
            RateLimitException: When rate limit is exceeded
        """
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            response = await call_next(request)
            return response

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get appropriate limit for this path
        limit = self._get_limit_for_path(request.url.path)

        # Check rate limit
        is_limited, retry_after, remaining = self._is_rate_limited(client_ip, limit)

        if is_limited:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip} on path: {request.url.path}",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "limit": limit,
                    "retry_after": retry_after
                }
            )
            # Return JSONResponse directly since middleware exceptions
            # aren't caught by exception handlers
            response = JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "details": {"retry_after": retry_after}
                    }
                }
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def cleanup_old_entries(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old entries to prevent memory leaks.

        This should be called periodically in production.

        Args:
            max_age_seconds: Maximum age of entries to keep

        Returns:
            Number of IPs removed
        """
        now = time.time()
        cutoff = now - max_age_seconds

        ips_to_remove = []
        for ip, timestamps in self._requests.items():
            # Remove old timestamps
            self._requests[ip] = [ts for ts in timestamps if ts > cutoff]
            # Mark empty entries for removal
            if not self._requests[ip]:
                ips_to_remove.append(ip)

        # Remove empty entries
        for ip in ips_to_remove:
            del self._requests[ip]

        return len(ips_to_remove)