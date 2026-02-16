"""
Core utilities package
"""

from .logging import setup_logging, get_logger
from .exceptions import (
    KanVerException,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    ConflictException,
    CooldownActiveException,
    GeofenceException,
    UnauthorizedException,
    ValidationException,
)

__version__ = "1.0.0"

__all__ = [
    "setup_logging",
    "get_logger",
    "KanVerException",
    "NotFoundException",
    "ForbiddenException",
    "BadRequestException",
    "ConflictException",
    "CooldownActiveException",
    "GeofenceException",
    "UnauthorizedException",
    "ValidationException",
]
