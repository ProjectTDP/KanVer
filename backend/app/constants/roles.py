"""
Kullanıcı rolleri ve yetki seviyeleri.

Roller:
- USER: Standart kullanıcı (bağışçı veya hasta yakını)
- NURSE: Hastane personeli (hemşire) - QR kod okutma, bağış doğrulama
- ADMIN: Sistem yöneticisi - Hastane ekleme, personel atama, istatistikler
"""

from enum import Enum
from typing import List


class UserRole(str, Enum):
    """Kullanıcı rolleri enum'ı."""

    USER = "USER"
    NURSE = "NURSE"
    ADMIN = "ADMIN"

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm kullanıcı rollerini döndürür."""
        return [role.value for role in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir kullanıcı rolü olup olmadığını kontrol eder."""
        return value in cls.all_values()

    def has_privilege(self) -> bool:
        """Bu rolün özel yetkilere sahip olup olmadığını kontrol eder."""
        return self in {UserRole.NURSE, UserRole.ADMIN}

    def is_staff(self) -> bool:
        """Bu rolün personel olup olmadığını kontrol eder."""
        return self in {UserRole.NURSE, UserRole.ADMIN}

    def can_manage_hospitals(self) -> bool:
        """Hastane yönetimi yetkisi."""
        return self == UserRole.ADMIN

    def can_verify_donations(self) -> bool:
        """Bağış doğrulama yetkisi."""
        return self == UserRole.NURSE


# Rol açıklamaları (UI için)
ROLE_DESCRIPTIONS: dict[str, str] = {
    "USER": "Standart Kullanıcı",
    "NURSE": "Hemşire",
    "ADMIN": "Yönetici",
}
