"""
Tests for custom KanVer exceptions.

Tests verify that all exception classes have correct status codes
and appropriate error messages.
"""
import pytest
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
)


class TestKanVerException:
    """Test base KanVerException class."""

    def test_kanver_exception_base_class(self):
        """KanVerException Exception sınıfından türemeli."""
        exc = KanVerException("Test error", status_code=500)
        assert isinstance(exc, Exception)
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.detail is None

    def test_kanver_exception_with_detail(self):
        """KanVerException detay ile oluşturulabilmeli."""
        exc = KanVerException(
            message="Test error",
            status_code=400,
            detail="Additional details"
        )
        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.detail == "Additional details"


class TestNotFoundException:
    """Test NotFoundException class."""

    def test_not_found_exception_status_code(self):
        """NotFoundException 404 status koduna sahip olmalı."""
        exc = NotFoundException()
        assert exc.status_code == 404

    def test_not_found_exception_default_message(self):
        """NotFoundException varsayılan mesaja sahip olmalı."""
        exc = NotFoundException()
        assert exc.message == "Resource not found"

    def test_not_found_exception_custom_message(self):
        """NotFoundException özel mesaj alabilmeli."""
        exc = NotFoundException("User not found")
        assert exc.message == "User not found"


class TestForbiddenException:
    """Test ForbiddenException class."""

    def test_forbidden_exception_status_code(self):
        """ForbiddenException 403 status koduna sahip olmalı."""
        exc = ForbiddenException()
        assert exc.status_code == 403

    def test_forbidden_exception_default_message(self):
        """ForbiddenException varsayılan mesaja sahip olmalı."""
        exc = ForbiddenException()
        assert exc.message == "Access forbidden"


class TestBadRequestException:
    """Test BadRequestException class."""

    def test_bad_request_exception_status_code(self):
        """BadRequestException 400 status koduna sahip olmalı."""
        exc = BadRequestException()
        assert exc.status_code == 400

    def test_bad_request_exception_default_message(self):
        """BadRequestException varsayılan mesaja sahip olmalı."""
        exc = BadRequestException()
        assert exc.message == "Bad request"


class TestConflictException:
    """Test ConflictException class."""

    def test_conflict_exception_status_code(self):
        """ConflictException 409 status koduna sahip olmalı."""
        exc = ConflictException()
        assert exc.status_code == 409

    def test_conflict_exception_default_message(self):
        """ConflictException varsayılan mesaja sahip olmalı."""
        exc = ConflictException()
        assert exc.message == "Resource conflict"


class TestUnauthorizedException:
    """Test UnauthorizedException class."""

    def test_unauthorized_exception_status_code(self):
        """UnauthorizedException 401 status koduna sahip olmalı."""
        exc = UnauthorizedException()
        assert exc.status_code == 401

    def test_unauthorized_exception_default_message(self):
        """UnauthorizedException varsayılan mesaja sahip olmalı."""
        exc = UnauthorizedException()
        assert exc.message == "Unauthorized"


class TestCooldownActiveException:
    """Test CooldownActiveException class."""

    def test_cooldown_active_exception_status_code(self):
        """CooldownActiveException 400 status koduna sahip olmalı."""
        exc = CooldownActiveException("2024-12-31")
        assert exc.status_code == 400

    def test_cooldown_active_exception_message(self):
        """CooldownActiveException tarih içeren mesaj içermeli."""
        exc = CooldownActiveException("2024-12-31")
        assert "2024-12-31" in exc.message
        assert "Bağışlık oldunuz" in exc.message


class TestGeofenceException:
    """Test GeofenceException class."""

    def test_geofence_exception_status_code(self):
        """GeofenceException 400 status koduna sahip olmalı."""
        exc = GeofenceException()
        assert exc.status_code == 400

    def test_geofence_exception_default_message(self):
        """GeofenceException varsayılan Türkçe mesaja sahip olmalı."""
        exc = GeofenceException()
        assert exc.message == "Hastane sınırları dışındasınız"

    def test_geofence_exception_custom_message(self):
        """GeofenceException özel mesaj alabilmeli."""
        exc = GeofenceException("Konum hastane bölgesi dışında")
        assert exc.message == "Konum hastane bölgesi dışında"


class TestActiveCommitmentExistsException:
    """Test ActiveCommitmentExistsException class."""

    def test_active_commitment_exists_exception_status_code(self):
        """ActiveCommitmentExistsException 409 status koduna sahip olmalı."""
        exc = ActiveCommitmentExistsException()
        assert exc.status_code == 409

    def test_active_commitment_exists_exception_message(self):
        """ActiveCommitmentExistsException doğru mesaja sahip olmalı."""
        exc = ActiveCommitmentExistsException()
        assert "aktif" in exc.message.lower()
        assert "taahhüd" in exc.message.lower()


class TestSlotFullException:
    """Test SlotFullException class."""

    def test_slot_full_exception_status_code(self):
        """SlotFullException 409 status koduna sahip olmalı."""
        exc = SlotFullException()
        assert exc.status_code == 409

    def test_slot_full_exception_default_message(self):
        """SlotFullException varsayılan Türkçe mesaja sahip olmalı."""
        exc = SlotFullException()
        assert "slot" in exc.message.lower() or "doldu" in exc.message.lower()

    def test_slot_full_exception_custom_message(self):
        """SlotFullException özel mesaj alabilmeli."""
        exc = SlotFullException("Bu talep için tüm bağışçı slotları dolu")
        assert exc.message == "Bu talep için tüm bağışçı slotları dolu"
