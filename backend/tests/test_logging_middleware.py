"""
Tests for logging middleware.

Tests verify:
- Request ID generation and propagation
- Client IP extraction
- User-agent logging
- Sensitive header masking
- Access log generation
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from app.middleware.logging_middleware import (
    LoggingMiddleware,
    mask_sensitive_headers,
    mask_sensitive_body,
)


class TestMaskSensitiveHeaders:
    """Test sensitive header masking functionality."""

    def test_mask_authorization_bearer(self):
        """Authorization header with Bearer should be masked."""
        headers = {"Authorization": "Bearer secret-token-12345"}
        masked = mask_sensitive_headers(headers)
        assert masked["Authorization"] == "Bearer ***"

    def test_mask_authorization_without_bearer(self):
        """Authorization header without Bearer prefix should be fully masked."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        masked = mask_sensitive_headers(headers)
        assert masked["Authorization"] == "***"

    def test_mask_cookie(self):
        """Cookie header should be masked."""
        headers = {"Cookie": "session=abc123; user=test"}
        masked = mask_sensitive_headers(headers)
        assert masked["Cookie"] == "***"

    def test_mask_set_cookie(self):
        """Set-Cookie header should be masked."""
        headers = {"Set-Cookie": "session=abc123; Path=/"}
        masked = mask_sensitive_headers(headers)
        assert masked["Set-Cookie"] == "***"

    def test_mask_x_api_key(self):
        """X-API-Key header should be masked."""
        headers = {"X-API-Key": "my-secret-key"}
        masked = mask_sensitive_headers(headers)
        assert masked["X-API-Key"] == "***"

    def test_preserve_non_sensitive_headers(self):
        """Non-sensitive headers should be preserved."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        masked = mask_sensitive_headers(headers)
        assert masked["Content-Type"] == "application/json"
        assert masked["User-Agent"] == "Mozilla/5.0"
        assert masked["Accept"] == "application/json"

    def test_case_insensitive_matching(self):
        """Header matching should be case-insensitive."""
        headers = {"AUTHORIZATION": "Bearer token123"}
        masked = mask_sensitive_headers(headers)
        assert masked["AUTHORIZATION"] == "Bearer ***"


class TestMaskSensitiveBody:
    """Test sensitive body field masking."""

    def test_mask_password_field(self):
        """Password field should be masked in JSON body."""
        body = '{"username": "test", "password": "secret123"}'
        masked = mask_sensitive_body(body)
        assert '"password": "***"' in masked
        assert "secret123" not in masked

    def test_mask_password_confirm_field(self):
        """password_confirm field should be masked."""
        body = '{"password_confirm": "secret123"}'
        masked = mask_sensitive_body(body)
        assert '"password_confirm": "***"' in masked

    def test_mask_token_field(self):
        """token field should be masked."""
        body = '{"token": "abc123xyz"}'
        masked = mask_sensitive_body(body)
        assert '"token": "***"' in masked

    def test_preserve_non_sensitive_fields(self):
        """Non-sensitive fields should be preserved."""
        body = '{"username": "testuser", "email": "test@example.com"}'
        masked = mask_sensitive_body(body)
        assert "testuser" in masked
        assert "test@example.com" in masked

    def test_empty_body(self):
        """Empty body should return unchanged."""
        body = ""
        masked = mask_sensitive_body(body)
        assert masked == ""

    def test_multiple_sensitive_fields(self):
        """Multiple sensitive fields should all be masked."""
        body = '{"password": "pass1", "token": "tok1", "secret": "sec1"}'
        masked = mask_sensitive_body(body)
        assert '"password": "***"' in masked
        assert '"token": "***"' in masked
        assert '"secret": "***"' in masked


class TestLoggingMiddleware:
    """Test LoggingMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with logging middleware."""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.post("/echo")
        async def echo_endpoint(request: Request):
            body = await request.body()
            return {"body": body.decode()}

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_request_id_generated(self, client):
        """Request ID should be generated if not provided."""
        response = client.get("/test")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] != ""

    def test_request_id_propagated(self, client):
        """Request ID should be propagated from header if provided."""
        custom_id = "custom-request-id-12345"
        response = client.get("/test", headers={"X-Request-ID": custom_id})
        assert response.headers["X-Request-ID"] == custom_id

    def test_successful_request_logs(self, client):
        """Successful requests should be logged."""
        with patch("app.middleware.logging_middleware.logger") as mock_logger, \
             patch("app.middleware.logging_middleware.access_logger") as mock_access:
            response = client.get("/test")
            assert response.status_code == 200
            # Verify logging was called
            assert mock_access.info.called

    def test_get_client_ip_direct(self, app):
        """Client IP should be extracted from request.client."""
        middleware = LoggingMiddleware(app)

        # Create mock request
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_forwarded_for(self, app):
        """Client IP should be extracted from X-Forwarded-For header."""
        middleware = LoggingMiddleware(app)

        # Create mock request with X-Forwarded-For
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"x-forwarded-for": "203.0.113.1, 70.41.3.18"}

        ip = middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.1"  # First IP in chain

    def test_get_client_ip_unknown(self, app):
        """Client IP should be 'unknown' when not available."""
        middleware = LoggingMiddleware(app)

        # Create mock request without client info
        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers = {}

        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"

    def test_get_user_agent(self, app):
        """User-agent should be extracted from headers."""
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock()
        mock_request.headers = {"user-agent": "TestClient/1.0"}

        ua = middleware._get_user_agent(mock_request)
        assert ua == "TestClient/1.0"

    def test_get_user_agent_missing(self, app):
        """User-agent should be '-' when not provided."""
        middleware = LoggingMiddleware(app)

        mock_request = MagicMock()
        mock_request.headers = {}

        ua = middleware._get_user_agent(mock_request)
        assert ua == "-"