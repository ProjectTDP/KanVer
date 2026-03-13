"""
Cooldown utility functions for KanVer API.

Bu modül, bağış sonrası biyolojik bekleme süresi hesaplarını içerir.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import RequestType
from app.core.exceptions import BadRequestException, NotFoundException
from app.models import User


def _ensure_utc(value: datetime) -> datetime:
	"""Naive datetime değerlerini UTC kabul ederek normalize eder."""
	if value.tzinfo is None:
		return value.replace(tzinfo=timezone.utc)
	return value


def is_in_cooldown(user: User) -> bool:
	"""Kullanıcının aktif cooldown sürecinde olup olmadığını döndürür."""
	if user.next_available_date is None:
		return False
	return _ensure_utc(user.next_available_date) > datetime.now(timezone.utc)


def get_cooldown_end(user: User) -> Optional[datetime]:
	"""Cooldown bitiş tarihini döndürür."""
	return user.next_available_date


def calculate_next_available(donation_type: str, donation_date: datetime) -> datetime:
	"""Bağış tipine göre bir sonraki uygun bağış tarihini hesaplar."""
	normalized_type = donation_type.upper()
	donation_date = _ensure_utc(donation_date)

	if normalized_type == RequestType.WHOLE_BLOOD.value:
		return donation_date + timedelta(days=settings.WHOLE_BLOOD_COOLDOWN_DAYS)
	if normalized_type == RequestType.APHERESIS.value:
		return donation_date + timedelta(hours=settings.APHERESIS_COOLDOWN_HOURS)

	raise BadRequestException("Geçersiz bağış türü")


async def set_cooldown(db: AsyncSession, user_id: str, donation_type: str) -> User:
	"""Kullanıcının cooldown alanlarını günceller."""
	result = await db.execute(select(User).where(User.id == user_id))
	user = result.scalar_one_or_none()
	if user is None:
		raise NotFoundException("Kullanıcı bulunamadı")

	donation_date = datetime.now(timezone.utc)
	user.last_donation_date = donation_date
	user.next_available_date = calculate_next_available(donation_type, donation_date)

	await db.flush()
	await db.refresh(user)
	return user
