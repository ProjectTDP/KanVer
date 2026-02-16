"""
Custom exceptions for KanVer application
"""

from fastapi import HTTPException, status


class KanVerException(HTTPException):
    """Base exception for all KanVer custom exceptions"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(KanVerException):
    """Exception raised when a resource is not found (404)"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ForbiddenException(KanVerException):
    """Exception raised when access is forbidden (403)"""
    
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class BadRequestException(KanVerException):
    """Exception raised for bad requests (400)"""
    
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ConflictException(KanVerException):
    """Exception raised when there's a conflict (409)"""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class CooldownActiveException(KanVerException):
    """Exception raised when donor is in cooldown period"""
    
    def __init__(self, detail: str = "Donor is in cooldown period", next_available_date: str = None):
        if next_available_date:
            detail = f"{detail}. Next available date: {next_available_date}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class GeofenceException(KanVerException):
    """Exception raised when geofence validation fails"""
    
    def __init__(self, detail: str = "Location validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class UnauthorizedException(KanVerException):
    """Exception raised when authentication fails (401)"""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ValidationException(KanVerException):
    """Exception raised for validation errors (422)"""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
