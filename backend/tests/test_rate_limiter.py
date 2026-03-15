"""
Tests for rate limiter middleware.

Tests verify:
- Rate limiting with configurable limits
- Stricter limits for auth endpoints
- Rate limit headers in response
- RateLimitException on limit exceeded
- IP-based tracking
"""
import pytest
import time
import os
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.middleware.rate_limiter import RateLimiterMiddleware
from app.core.exceptions import RateLimitException


# Enable rate limiting for these tests
@pytest.fixture(autouse=True, scope="module")
def enable_rate_limiting():
    """Enable rate limiting for rate limiter tests."""
    with patch("app.middleware.rate_limiter.settings.RATE_LIMIT_ENABLED", True):
        yield


class TestRateLimiterMiddleware:
    """Test RateLimiterMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with rate limiter."""
        app = FastAPI()
        app.add_middleware(
            RateLimiterMiddleware,
            requests_per_minute=5,
            auth_requests_per_minute=2
        )

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.post("/api/auth/login")
        async def login():
            return {"token": "test-token"}

        @app.post("/api/auth/refresh")
        async def refresh():
            return {"token": "refreshed-token"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_rate_limit_headers_present(self, client):
        """Rate limit headers should be present in response."""
        response = client.get("/test")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert int(response.headers["X-RateLimit-Limit"]) == 5

    def test_rate_limit_remaining_decreases(self, client):
        """Remaining count should decrease with each request."""
        response1 = client.get("/test")
        response2 = client.get("/test")

        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])

        assert remaining2 == remaining1 - 1

    def test_rate_limit_exceeded(self, client):
        """Should return 429 when rate limit exceeded."""
        # Make 6 requests (limit is 5)
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200

        # 6th request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_auth_endpoint_stricter_limit(self, client):
        """Auth endpoints should have stricter rate limit."""
        # Auth limit is 2
        for _ in range(2):
            response = client.post("/api/auth/login")
            assert response.status_code == 200
            assert int(response.headers["X-RateLimit-Limit"]) == 2

        # 3rd request should be rate limited
        response = client.post("/api/auth/login")
        assert response.status_code == 429

    def test_auth_refresh_endpoint_stricter_limit(self, client):
        """Auth refresh endpoint should have stricter rate limit."""
        for _ in range(2):
            response = client.post("/api/auth/refresh")
            assert response.status_code == 200

        response = client.post("/api/auth/refresh")
        assert response.status_code == 429


class TestRateLimiterGetClientIP:
    """Test client IP extraction."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        app = FastAPI()
        return RateLimiterMiddleware(app)

    def test_get_client_ip_direct(self, middleware):
        """IP should be extracted from request.client."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_forwarded_for(self, middleware):
        """IP should be extracted from X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"x-forwarded-for": "203.0.113.1, 70.41.3.18"}

        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_unknown(self, middleware):
        """IP should be 'unknown' when not available."""
        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers = {}

        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"


class TestRateLimiterInternalMethods:
    """Test internal rate limiting methods."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        app = FastAPI()
        return RateLimiterMiddleware(app, requests_per_minute=10, auth_requests_per_minute=3)

    def test_is_rate_limited_within_limit(self, middleware):
        """Requests within limit should not be limited."""
        is_limited, retry_after, remaining = middleware._is_rate_limited("192.168.1.1", 10)
        assert is_limited is False
        assert retry_after == 0
        assert remaining == 9  # 10 - 1 (current request) - 0 (previous)

    def test_is_rate_limited_exceeded(self, middleware):
        """Requests exceeding limit should be limited."""
        ip = "192.168.1.2"
        limit = 5

        # Make 5 requests
        for _ in range(5):
            middleware._is_rate_limited(ip, limit)

        # 6th request should be limited
        is_limited, retry_after, remaining = middleware._is_rate_limited(ip, limit)
        assert is_limited is True
        assert retry_after > 0

    def test_get_limit_for_path_regular(self, middleware):
        """Regular paths should return regular limit."""
        assert middleware._get_limit_for_path("/api/users") == 10
        assert middleware._get_limit_for_path("/api/hospitals") == 10
        assert middleware._get_limit_for_path("/health") == 10

    def test_get_limit_for_path_auth(self, middleware):
        """Auth paths should return auth limit."""
        assert middleware._get_limit_for_path("/api/auth/login") == 3
        assert middleware._get_limit_for_path("/api/auth/refresh") == 3

    def test_cleanup_old_entries(self, middleware):
        """Cleanup should remove old entries."""
        # Add some old entries
        middleware._requests["old_ip"] = [time.time() - 7200]  # 2 hours ago
        middleware._requests["new_ip"] = [time.time()]

        removed = middleware.cleanup_old_entries(max_age_seconds=3600)

        assert removed == 1
        assert "old_ip" not in middleware._requests
        assert "new_ip" in middleware._requests


class TestRateLimiterDisabled:
    """Test rate limiter when disabled."""

    def test_rate_limit_disabled_no_headers(self):
        """When disabled, rate limit headers should not be added."""
        with patch("app.middleware.rate_limiter.settings.RATE_LIMIT_ENABLED", False):
            app = FastAPI()
            app.add_middleware(RateLimiterMiddleware, requests_per_minute=2)

            @app.get("/test")
            async def test_endpoint():
                return {"status": "ok"}

            client = TestClient(app)

            # Make many requests - none should be limited
            for _ in range(10):
                response = client.get("/test")
                assert response.status_code == 200


class TestRateLimiterExceptionFormat:
    """Test RateLimitException format in responses."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.add_middleware(
            RateLimiterMiddleware,
            requests_per_minute=2
        )

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_rate_limit_error_format(self, client):
        """Rate limit error should have correct format."""
        # Make requests to hit limit
        client.get("/test")
        client.get("/test")

        response = client.get("/test")
        assert response.status_code == 429

        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after" in body["error"]["details"]
        assert body["error"]["details"]["retry_after"] > 0