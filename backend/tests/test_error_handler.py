"""
Tests for global error handler middleware.

Tests verify:
- KanVerException handling with proper error codes
- RequestValidationError handling with field-level details
- HTTPException handling
- Generic exception handling
- Consistent error response format
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.exceptions import (
    KanVerException,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    ConflictException,
    UnauthorizedException,
    CooldownActiveException,
    GeofenceException,
    ActiveCommitmentExistsException,
    SlotFullException,
    RateLimitException,
)
from app.middleware.error_handler import (
    kanver_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
    ERROR_CODES,
    _build_error_response,
)


class TestBuildErrorResponse:
    """Test error response builder."""

    def test_build_error_response_basic(self):
        """Basic error response should have correct structure."""
        response = _build_error_response(
            code="TEST_ERROR",
            message="Test error message"
        )
        assert "error" in response
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test error message"
        assert response["error"]["details"] == {}

    def test_build_error_response_with_details(self):
        """Error response should include details when provided."""
        response = _build_error_response(
            code="VALIDATION_ERROR",
            message="Validation failed",
            details={"field": "email", "reason": "invalid format"}
        )
        assert response["error"]["details"]["field"] == "email"
        assert response["error"]["details"]["reason"] == "invalid format"


class TestErrorCodes:
    """Test error code mapping."""

    def test_error_codes_exist(self):
        """All KanVerException subclasses should have error codes."""
        expected_codes = [
            "NotFoundException",
            "ForbiddenException",
            "BadRequestException",
            "ConflictException",
            "UnauthorizedException",
            "CooldownActiveException",
            "GeofenceException",
            "ActiveCommitmentExistsException",
            "SlotFullException",
            "RateLimitException",
        ]
        for exc_name in expected_codes:
            assert exc_name in ERROR_CODES, f"Missing error code for {exc_name}"

    def test_error_codes_values(self):
        """Error codes should follow naming convention."""
        assert ERROR_CODES["NotFoundException"] == "NOT_FOUND"
        assert ERROR_CODES["ForbiddenException"] == "FORBIDDEN"
        assert ERROR_CODES["BadRequestException"] == "BAD_REQUEST"
        assert ERROR_CODES["ConflictException"] == "CONFLICT"
        assert ERROR_CODES["UnauthorizedException"] == "UNAUTHORIZED"
        assert ERROR_CODES["CooldownActiveException"] == "COOLDOWN_ACTIVE"
        assert ERROR_CODES["GeofenceException"] == "GEOFENCE_VIOLATION"
        assert ERROR_CODES["ActiveCommitmentExistsException"] == "ACTIVE_COMMITMENT_EXISTS"
        assert ERROR_CODES["SlotFullException"] == "SLOT_FULL"
        assert ERROR_CODES["RateLimitException"] == "RATE_LIMIT_EXCEEDED"


class TestKanverExceptionHandler:
    """Test KanVerException handler."""

    @pytest.mark.asyncio
    async def test_handle_not_found_exception(self):
        """NotFoundException should return 404 with NOT_FOUND code."""
        request = MagicMock(spec=Request)
        exc = NotFoundException("User not found")

        response = await kanver_exception_handler(request, exc)

        assert response.status_code == 404
        # Parse JSON body
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["message"] == "User not found"

    @pytest.mark.asyncio
    async def test_handle_forbidden_exception(self):
        """ForbiddenException should return 403 with FORBIDDEN code."""
        request = MagicMock(spec=Request)
        exc = ForbiddenException("Access denied")

        response = await kanver_exception_handler(request, exc)

        assert response.status_code == 403
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_handle_bad_request_exception(self):
        """BadRequestException should return 400 with BAD_REQUEST code."""
        request = MagicMock(spec=Request)
        exc = BadRequestException("Invalid input", detail={"field": "email"})

        response = await kanver_exception_handler(request, exc)

        assert response.status_code == 400
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "BAD_REQUEST"
        assert body["error"]["details"]["field"] == "email"

    @pytest.mark.asyncio
    async def test_handle_conflict_exception(self):
        """ConflictException should return 409 with CONFLICT code."""
        request = MagicMock(spec=Request)
        exc = ConflictException("Resource already exists")

        response = await kanver_exception_handler(request, exc)

        assert response.status_code == 409
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_handle_rate_limit_exception(self):
        """RateLimitException should return 429 with retry_after detail."""
        request = MagicMock(spec=Request)
        exc = RateLimitException(retry_after=60)

        response = await kanver_exception_handler(request, exc)

        assert response.status_code == 429
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert body["error"]["details"]["retry_after"] == 60


class TestValidationExceptionHandler:
    """Test RequestValidationError handler."""

    @pytest.mark.asyncio
    async def test_handle_validation_error(self):
        """Validation errors should return 422 with field details."""
        request = MagicMock(spec=Request)

        # Create a mock validation error
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "email"), "msg": "Invalid email format", "type": "value_error.email"},
            {"loc": ("body", "password"), "msg": "Password too short", "type": "value_error.any_str.min_length"}
        ]

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert body["error"]["message"] == "Validation failed"
        assert len(body["error"]["details"]["errors"]) == 2

    @pytest.mark.asyncio
    async def test_validation_error_field_paths(self):
        """Field paths should be formatted correctly."""
        request = MagicMock(spec=Request)
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "user", "email"), "msg": "Required field", "type": "value_error.missing"}
        ]

        response = await validation_exception_handler(request, exc)

        import json
        body = json.loads(response.body.decode())
        # "body" prefix is filtered out for cleaner field paths
        assert body["error"]["details"]["errors"][0]["field"] == "user.email"


class TestHTTPExceptionHandler:
    """Test HTTPException handler."""

    @pytest.mark.asyncio
    async def test_handle_404_http_exception(self):
        """HTTP 404 should return NOT_FOUND code."""
        request = MagicMock(spec=Request)
        exc = StarletteHTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_handle_401_http_exception(self):
        """HTTP 401 should return UNAUTHORIZED code."""
        request = MagicMock(spec=Request)
        exc = StarletteHTTPException(status_code=401, detail="Not authenticated")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 401
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_handle_500_http_exception(self):
        """HTTP 500 should return INTERNAL_ERROR code."""
        request = MagicMock(spec=Request)
        exc = StarletteHTTPException(status_code=500, detail="Internal error")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "INTERNAL_ERROR"


class TestGenericExceptionHandler:
    """Test generic exception handler."""

    @pytest.mark.asyncio
    async def test_handle_generic_exception(self):
        """Generic exceptions should return 500 with generic message."""
        request = MagicMock(spec=Request)
        exc = ValueError("Unexpected error")

        response = await generic_exception_handler(request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body.decode())
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert body["error"]["message"] == "An unexpected error occurred"

    @pytest.mark.asyncio
    async def test_generic_exception_logs_error(self):
        """Generic exceptions should be logged."""
        request = MagicMock(spec=Request)
        exc = RuntimeError("Something went wrong")

        with pytest.MonkeyPatch.context() as m:
            mock_logger = MagicMock()
            m.setattr("app.middleware.error_handler.logger", mock_logger)
            await generic_exception_handler(request, exc)
            assert mock_logger.exception.called


class TestErrorHandlerIntegration:
    """Integration tests with FastAPI app."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with error handlers."""
        app = FastAPI()
        app.add_exception_handler(KanVerException, kanver_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(Exception, generic_exception_handler)

        @app.get("/not-found")
        async def not_found():
            raise NotFoundException("Resource not found")

        @app.get("/forbidden")
        async def forbidden():
            raise ForbiddenException("Access denied")

        @app.get("/rate-limited")
        async def rate_limited():
            raise RateLimitException(retry_after=30)

        @app.get("/error")
        async def error():
            raise RuntimeError("Unexpected error")

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        # Set raise_server_exceptions=False to capture error responses
        return TestClient(app, raise_server_exceptions=False)

    def test_not_found_endpoint(self, client):
        """Not found endpoint should return proper error format."""
        response = client.get("/not-found")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    def test_forbidden_endpoint(self, client):
        """Forbidden endpoint should return proper error format."""
        response = client.get("/forbidden")
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"

    def test_rate_limited_endpoint(self, client):
        """Rate limited endpoint should return proper error format."""
        response = client.get("/rate-limited")
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert response.json()["error"]["details"]["retry_after"] == 30

    def test_generic_error_endpoint(self, client):
        """Generic error endpoint should return proper error format."""
        response = client.get("/error")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"