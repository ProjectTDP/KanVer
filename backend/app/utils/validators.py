"""Kan grubu uyumluluk doğrulama yardımcıları."""

from typing import List

from app.constants import BloodType
from app.constants.blood_types import can_donate, get_compatible_donors as get_compatible_donors_from_constants


def _normalize_blood_type(value: str) -> str:
	"""Kan grubu değerini normalize eder (örn: ab+ -> AB+)."""
	return value.strip().upper()


def get_compatible_donors(blood_type: str) -> List[str]:
	"""Verilen alıcı kan grubu için uyumlu bağışçı gruplarını döndürür."""
	normalized_type = _normalize_blood_type(blood_type)

	if not BloodType.is_valid(normalized_type):
		return []

	return get_compatible_donors_from_constants(normalized_type)


def can_donate_to(donor_type: str, recipient_type: str) -> bool:
	"""Donörün alıcıya bağış yapıp yapamayacağını kontrol eder."""
	normalized_donor = _normalize_blood_type(donor_type)
	normalized_recipient = _normalize_blood_type(recipient_type)

	if not BloodType.is_valid(normalized_donor) or not BloodType.is_valid(normalized_recipient):
		return False

	return can_donate(normalized_donor, normalized_recipient)
