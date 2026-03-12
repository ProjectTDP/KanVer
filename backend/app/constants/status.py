"""
Durum enum'ları için sabitler.

Bu dosya, tüm modellerde kullanılan status enum'larını içerir:
- RequestStatus: Kan talebi durumu
- RequestType: Bağış türü (tam kan / aferez)
- Priority: Aciliyet seviyesi
- CommitmentStatus: Bağış taahhüdü durumu
- DonationStatus: Tamamlanan bağış durumu
- NotificationType: Bildirim türü
"""

from enum import Enum
from typing import List


class RequestStatus(str, Enum):
    """Kan talebi durumu."""

    ACTIVE = "ACTIVE"           # Aktif talep (bekleniyor)
    FULFILLED = "FULFILLED"     # Tamamlandı (yeterli bağış toplandı)
    CANCELLED = "CANCELLED"     # İptal edildi
    EXPIRED = "EXPIRED"         # Süresi doldu

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm durumları döndürür."""
        return [status.value for status in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir durum olup olmadığını kontrol eder."""
        return value in cls.all_values()

    def is_terminal(self) -> bool:
        """Bu durumun terminal (değiştirilemez) olup olmadığını kontrol eder."""
        return self in {RequestStatus.FULFILLED, RequestStatus.CANCELLED, RequestStatus.EXPIRED}

    def is_active(self) -> bool:
        """Talebin hala aktif olup olmadığını kontrol eder."""
        return self == RequestStatus.ACTIVE


class RequestType(str, Enum):
    """Kan bağışı türü."""

    WHOLE_BLOOD = "WHOLE_BLOOD"   # Tam kan (stok takası için) - 90 gün cooldown
    APHERESIS = "APHERESIS"       # Aferez (trombosit/taze kan) - 48 saat cooldown

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm bağış türlerini döndürür."""
        return [rt.value for rt in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir bağış türü olup olmadığını kontrol eder."""
        return value in cls.all_values()

    def cooldown_days(self) -> int:
        """Bu bağış türü için cooldown süresini (gün) döndürür."""
        return 90 if self == RequestType.WHOLE_BLOOD else 0  # Aferez saat cinsinden

    def hero_points(self) -> int:
        """Bu bağış türü için verilen kahramanlık puanını döndürür."""
        return 50 if self == RequestType.WHOLE_BLOOD else 100


class Priority(str, Enum):
    """Aciliyet seviyesi."""

    LOW = "LOW"                   # Düşük aciliyet
    NORMAL = "NORMAL"             # Normal aciliyet (varsayılan)
    URGENT = "URGENT"             # Acil
    CRITICAL = "CRITICAL"         # Kritik (hayati önem)

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm aciliyet seviyelerini döndürür."""
        return [p.value for p in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir aciliyet seviyesi olup olmadığını kontrol eder."""
        return value in cls.all_values()

    def severity_score(self) -> int:
        """Bu aciliyet seviyesinin önem skorunu döndürür (sıralama için)."""
        scores = {
            Priority.LOW: 1,
            Priority.NORMAL: 2,
            Priority.URGENT: 3,
            Priority.CRITICAL: 4,
        }
        return scores[self]


class CommitmentStatus(str, Enum):
    """Bağış taahhüdü durumu."""

    ON_THE_WAY = "ON_THE_WAY"     # Yolda
    ARRIVED = "ARRIVED"           # Hastaneye vardı
    COMPLETED = "COMPLETED"       # Tamamlandı (bağış gerçekleştirildi)
    CANCELLED = "CANCELLED"       # İptal edildi (bağışçı tarafından)
    TIMEOUT = "TIMEOUT"           # Timeout (60 dakika içinde gelmedi)

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm taahhüt durumlarını döndürür."""
        return [cs.value for cs in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir taahhüt durumu olup olmadığını kontrol eder."""
        return value in cls.all_values()

    def is_active(self) -> bool:
        """Taahhüdün hala aktif olup olmadığını kontrol eder."""
        return self in {CommitmentStatus.ON_THE_WAY, CommitmentStatus.ARRIVED}

    def is_terminal(self) -> bool:
        """Bu durumun terminal (değiştirilemez) olup olmadığını kontrol eder."""
        return self in {CommitmentStatus.COMPLETED, CommitmentStatus.CANCELLED, CommitmentStatus.TIMEOUT}


class DonationStatus(str, Enum):
    """Tamamlanan bağış durumu."""

    COMPLETED = "COMPLETED"       # Başarıyla tamamlandı
    CANCELLED = "CANCELLED"       # İptal edildi
    REJECTED = "REJECTED"         # Reddedildi (tıbbi nedenlerle)

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm bağış durumlarını döndürür."""
        return [ds.value for ds in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir bağış durumu olup olmadığını kontrol eder."""
        return value in cls.all_values()

    def awards_points(self) -> bool:
        """Bu durumun puan kazandırıp kazandırmadığını kontrol eder."""
        return self == DonationStatus.COMPLETED


class NotificationType(str, Enum):
    """Bildirim türü."""

    NEW_REQUEST = "NEW_REQUEST"                     # Yeni kan talebi oluşturuldu
    DONOR_FOUND = "DONOR_FOUND"                     # Bağışçı bulundu
    DONOR_ON_WAY = "DONOR_ON_WAY"                   # Bağışçı yolda
    DONATION_COMPLETE = "DONATION_COMPLETE"         # Bağış tamamlandı
    TIMEOUT_WARNING = "TIMEOUT_WARNING"             # Timeout uyarısı
    NO_SHOW = "NO_SHOW"                             # Bağışçı gelmedi

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm bildirim türlerini döndürür."""
        return [nt.value for nt in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir bildirim türü olup olmadığını kontrol eder."""
        return value in cls.all_values()


# Status açıklamaları (UI için)
REQUEST_STATUS_DESCRIPTIONS: dict[str, str] = {
    "ACTIVE": "Aktif",
    "FULFILLED": "Tamamlandı",
    "CANCELLED": "İptal Edildi",
    "EXPIRED": "Süresi Doldu",
}

REQUEST_TYPE_DESCRIPTIONS: dict[str, str] = {
    "WHOLE_BLOOD": "Tam Kan",
    "APHERESIS": "Aferez",
}

PRIORITY_DESCRIPTIONS: dict[str, str] = {
    "LOW": "Düşük",
    "NORMAL": "Normal",
    "URGENT": "Acil",
    "CRITICAL": "Kritik",
}

COMMITMENT_STATUS_DESCRIPTIONS: dict[str, str] = {
    "ON_THE_WAY": "Yolda",
    "ARRIVED": "Hastanede",
    "COMPLETED": "Tamamlandı",
    "CANCELLED": "İptal Edildi",
    "TIMEOUT": "Süresi Doldu",
}

DONATION_STATUS_DESCRIPTIONS: dict[str, str] = {
    "COMPLETED": "Tamamlandı",
    "CANCELLED": "İptal Edildi",
    "REJECTED": "Reddedildi",
}

NOTIFICATION_TYPE_DESCRIPTIONS: dict[str, str] = {
    "NEW_REQUEST": "Yeni Talep",
    "DONOR_FOUND": "Bağışçı Bulundu",
    "DONOR_ON_WAY": "Bağışçı Yolda",
    "DONATION_COMPLETE": "Bağış Tamamlandı",
    "TIMEOUT_WARNING": "Süre Uyarısı",
    "NO_SHOW": "Gelmedi",
}
