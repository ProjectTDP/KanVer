"""
Custom exceptions for KanVer API.

All exceptions inherit from KanVerException base class,
which provides consistent error response structure.
"""
from typing import Optional


class KanVerException(Exception):
    """
    Base exception for all KanVer errors.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return
        detail: Optional additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundException(KanVerException):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found", detail: Optional[str] = None):
        super().__init__(message, status_code=404, detail=detail)


class ForbiddenException(KanVerException):
    """Access forbidden (403)."""

    def __init__(self, message: str = "Access forbidden", detail: Optional[str] = None):
        super().__init__(message, status_code=403, detail=detail)


class BadRequestException(KanVerException):
    """Bad request (400)."""

    def __init__(self, message: str = "Bad request", detail: Optional[str] = None):
        super().__init__(message, status_code=400, detail=detail)


class ConflictException(KanVerException):
    """Resource conflict (409)."""

    def __init__(self, message: str = "Resource conflict", detail: Optional[str] = None):
        super().__init__(message, status_code=409, detail=detail)


class UnauthorizedException(KanVerException):
    """Unauthorized access (401)."""

    def __init__(self, message: str = "Unauthorized", detail: Optional[str] = None):
        super().__init__(message, status_code=401, detail=detail)


class CooldownActiveException(KanVerException):
    """
    Donor cooldown active.

    Raised when a user tries to donate but is still in cooldown period.
    """

    def __init__(self, next_available_date: str):
        message = f"Bağışlık oldunuz, bir sonraki bağış tarihiniz: {next_available_date}"
        super().__init__(message, status_code=400)


class GeofenceException(KanVerException):
    """
    Location outside hospital geofence.

    Raised when trying to create a blood request outside hospital boundaries.
    """

    def __init__(self, message: str = "Hastane sınırları dışındasınız"):
        super().__init__(message, status_code=400)


class ActiveCommitmentExistsException(KanVerException):
    """
    User already has an active donation commitment.

    Raised when a user tries to make a new commitment while having
    an active one (ON_THE_WAY or ARRIVED status).
    """

    def __init__(self, message: str = "Zaten aktif bir taahhüdünüz var"):
        super().__init__(message, status_code=409)


class SlotFullException(KanVerException):
    """
    All donation slots are filled.

    Raised when more donors try to commit than available slots
    (N+1 rule: units_needed + 1 maximum).
    """

    def __init__(self, message: str = "Tüm slotlar doldu, daha sonra tekrar deneyin"):
        super().__init__(message, status_code=409)
