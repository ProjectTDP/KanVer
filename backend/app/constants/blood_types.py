"""
Kan grubu sabitleri ve uyumluluk matrisi.

Tıbbi Gerçekler:
- O- (Universal Donor): Herkese verebilir, SADECE O-'den alabilir
- AB+ (Universal Recipient): Herkesten alabilir, SADECE AB+'ya verebilir

Matris Formatı: Recipient (Alıcı) → Compatible Donors (Verenler)
"""

from enum import Enum
from typing import Dict, List


class BloodType(str, Enum):
    """Kan grupları enum'ı."""

    A_PLUS = "A+"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B_MINUS = "B-"
    AB_PLUS = "AB+"
    AB_MINUS = "AB-"
    O_PLUS = "O+"
    O_MINUS = "O-"

    @classmethod
    def all_values(cls) -> List[str]:
        """Tüm kan gruplarını döndürür."""
        return [bt.value for bt in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Verilen değerin geçerli bir kan grubu olup olmadığını kontrol eder."""
        return value in cls.all_values()


# Kan grubu uyumluluk matrisi (Recipient → Compatible Donors)
# Anahtar: Alıcı kan grubu
# Değer: Bu alıcıya bağış yapabilecek kan grupları listesi
DONATION_COMPATIBILITY: Dict[str, List[str]] = {
    "O-": ["O-"],                                    # Sadece O-'den alabilir
    "O+": ["O-", "O+"],                              # O- ve O+'dan alabilir
    "A-": ["O-", "A-"],                              # O- ve A-'den alabilir
    "A+": ["O-", "O+", "A-", "A+"],                  # O-, O+, A- ve A+'dan alabilir
    "B-": ["O-", "B-"],                              # O- ve B-'den alabilir
    "B+": ["O-", "O+", "B-", "B+"],                  # O-, O+, B- ve B+'dan alabilir
    "AB-": ["O-", "A-", "B-", "AB-"],                # O-, A-, B- ve AB-'den alabilir
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],  # Herkesten alabilir (Universal Recipient)
}


def can_donate(donor: str, recipient: str) -> bool:
    """
    Verenin, alıcıya bağış yapıp yapamayacağını kontrol eder.

    Args:
        donor: Bağışçının kan grubu
        recipient: Alıcının kan grubu

    Returns:
        True if donor can donate to recipient, False otherwise

    Examples:
        >>> can_donate("O-", "AB+")  # O- herkese verebilir
        True
        >>> can_donate("A+", "O-")  # A+ O-'ye veremez
        False
        >>> can_donate("AB+", "O-")  # AB+ sadece AB+'ya verir
        False
    """
    if not BloodType.is_valid(donor) or not BloodType.is_valid(recipient):
        return False

    # Alıcının kabul edebildiği bağışçı listesini al
    compatible_donors = DONATION_COMPATIBILITY.get(recipient, [])
    # Bağışçı bu listede var mı?
    return donor in compatible_donors


def get_compatible_donors(recipient: str) -> List[str]:
    """
    Belirli bir alıcı kan grubu için uygun bağışçı kan gruplarını döndürür.

    Args:
        recipient: Alıcının kan grubu

    Returns:
        Bu alıcıya bağış yapabilecek kan grupları listesi

    Examples:
        >>> get_compatible_donors("O-")  # O- sadece O-'den alabilir
        ['O-']
        >>> get_compatible_donors("AB+")  # AB+ herkesten alabilir
        ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']
        >>> get_compatible_donors("A+")  # A+ 4 gruptan alabilir
        ['O-', 'O+', 'A-', 'A+']
    """
    if not BloodType.is_valid(recipient):
        return []

    # Matris zaten Recipient → Donors formatında olduğu için
    # doğrudan ilgili listeyi döndürmek yeterli
    return DONATION_COMPATIBILITY.get(recipient, []).copy()


# Kan grubu açıklamaları (opsiyonel UI için)
BLOOD_TYPE_DESCRIPTIONS: Dict[str, str] = {
    "A+": "A Pozitif",
    "A-": "A Negatif",
    "B+": "B Pozitif",
    "B-": "B Negatif",
    "AB+": "AB Pozitif (Universal Recipient)",
    "AB-": "AB Negatif",
    "O+": "O Pozitif",
    "O-": "O Negatif (Universal Donor)",
}
