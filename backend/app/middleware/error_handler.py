"""
Global error handler middleware for KanVer API.

Provides consistent error response format for all exceptions:
- KanVerException (custom exceptions)
- RequestValidationError (Pydantic validation errors)
- HTTPException (FastAPI/Starlette HTTP errors)
- Generic Exception (unexpected errors)

Error Response Format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": {...}
    }
}
"""
from typing import Dict, Any

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import KanVerException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Error code mapping for KanVer exceptions
ERROR_CODES: Dict[str, str] = {
    "NotFoundException": "NOT_FOUND",
    "ForbiddenException": "FORBIDDEN",
    "BadRequestException": "BAD_REQUEST",
    "ConflictException": "CONFLICT",
    "UnauthorizedException": "UNAUTHORIZED",
    "CooldownActiveException": "COOLDOWN_ACTIVE",
    "GeofenceException": "GEOFENCE_VIOLATION",
    "ActiveCommitmentExistsException": "ACTIVE_COMMITMENT_EXISTS",
    "SlotFullException": "SLOT_FULL",
    "RateLimitException": "RATE_LIMIT_EXCEEDED",
}


def _build_error_response(
    code: str,
    message: str,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Build consistent error response structure.

    Args:
        code: Error code string
        message: Human-readable error message
        details: Optional additional details

    Returns:
        Error response dictionary
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }


async def kanver_exception_handler(request: Request, exc: KanVerException) -> JSONResponse:
    """
    Handle all KanVer custom exceptions.

    Args:
        request: The incoming request
        exc: The KanVerException instance

    Returns:
        JSONResponse with error details
    """
    error_code = ERROR_CODES.get(type(exc).__name__, "INTERNAL_ERROR")

    logger.warning(
        f"KanVerException: {type(exc).__name__} - {exc.message}",
        extra={
            "error_code": error_code,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_response(
            code=error_code,
            message=exc.message,
            details=exc.detail
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Formats validation errors into a structured format with field-level details.

    Args:
        request: The incoming request
        exc: The RequestValidationError instance

    Returns:
        JSONResponse with validation error details
    """
    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        # Build field path from location tuple
        loc = error.get("loc", [])
        field_path = ".".join(str(loc_item) for loc_item in loc if loc_item != "body")

        formatted_errors.append({
            "field": field_path,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "validation_error")
        })

    logger.warning(
        f"Validation error: {len(formatted_errors)} field(s) failed validation",
        extra={"errors": formatted_errors}
    )

    return JSONResponse(
        status_code=422,
        content=_build_error_response(
            code="VALIDATION_ERROR",
            message="Validation failed",
            details={"errors": formatted_errors}
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle Starlette HTTPException errors.

    Args:
        request: The incoming request
        exc: The HTTPException instance

    Returns:
        JSONResponse with error details
    """
    # Map common HTTP status codes to error codes
    status_to_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }

    error_code = status_to_code.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if exc.detail else "An error occurred"

    logger.warning(
        f"HTTPException: {exc.status_code} - {message}",
        extra={"error_code": error_code}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_response(
            code=error_code,
            message=message,
            details={}
        )
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Logs the full exception for debugging but returns a generic error
    to the client to avoid leaking internal details.

    Args:
        request: The incoming request
        exc: The Exception instance

    Returns:
        JSONResponse with generic error message
    """
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={"exception_type": type(exc).__name__}
    )

    return JSONResponse(
        status_code=500,
        content=_build_error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={}
        )
    )