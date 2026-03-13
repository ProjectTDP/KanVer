"""
Blood Request Service for KanVer API.

Bu dosya, kan talebi yönetimi ile ilgili business logic fonksiyonlarını içerir.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_, or_, update, func, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import RequestStatus, RequestType, CommitmentStatus
from app.config import settings
from app.core.exceptions import (
	NotFoundException,
	ForbiddenException,
	BadRequestException,
	GeofenceException,
)
from app.models import BloodRequest, Hospital, DonationCommitment, User
from app.utils.helpers import generate_request_code
from app.utils.location import validate_geofence, create_point
from app.utils.validators import get_compatible_donors


async def create_request(db: AsyncSession, requester_id: str, data: dict) -> BloodRequest:
	"""
	Yeni kan talebi oluşturur.

	İş kuralları:
	- Kullanıcı hastane geofence içinde olmalı
	- Request code #KAN-XXX formatında üretilmeli
	- expires_at request_type'a göre belirlenmeli
	- Talep konumu hastane konumu olarak kaydedilmeli
	"""
	hospital_result = await db.execute(
		select(Hospital).where(Hospital.id == data["hospital_id"])
	)
	hospital = hospital_result.scalar_one_or_none()
	if not hospital:
		raise NotFoundException("Hastane bulunamadı")

	inside_geofence = await validate_geofence(
		db,
		user_lat=data["latitude"],
		user_lng=data["longitude"],
		hospital_id=data["hospital_id"],
	)
	if not inside_geofence:
		raise GeofenceException()

	request_type = data["request_type"].upper()
	now = datetime.now(timezone.utc)
	if request_type == RequestType.WHOLE_BLOOD.value:
		expires_at = now + timedelta(hours=24)
	else:
		expires_at = now + timedelta(hours=6)

	location_result = await db.execute(
		select(func.ST_AsText(Hospital.location)).where(Hospital.id == hospital.id)
	)
	location_wkt = location_result.scalar_one_or_none()

	request_location = create_point(data["latitude"], data["longitude"])
	if location_wkt and location_wkt.startswith("POINT(") and location_wkt.endswith(")"):
		point_str = location_wkt[6:-1]
		lng_str, lat_str = point_str.split(" ")
		request_location = create_point(float(lat_str), float(lng_str))

	blood_request = BloodRequest(
		request_code=await generate_request_code(db),
		requester_id=requester_id,
		hospital_id=data["hospital_id"],
		blood_type=data["blood_type"],
		request_type=request_type,
		priority=data.get("priority", "NORMAL"),
		units_needed=data["units_needed"],
		units_collected=0,
		status=RequestStatus.ACTIVE.value,
		expires_at=expires_at,
		patient_name=data.get("patient_name"),
		notes=data.get("notes"),
		location=request_location,
	)

	db.add(blood_request)
	await db.flush()
	await db.refresh(blood_request)
	return blood_request


async def get_request(db: AsyncSession, request_id: str) -> BloodRequest:
	"""ID ile kan talebi getirir, bulunamazsa 404 fırlatır."""
	result = await db.execute(
		select(BloodRequest).where(BloodRequest.id == request_id)
	)
	blood_request = result.scalar_one_or_none()
	if not blood_request:
		raise NotFoundException("Kan talebi bulunamadı")
	return blood_request


async def list_requests(
	db: AsyncSession,
	status: Optional[str] = None,
	blood_type: Optional[str] = None,
	request_type: Optional[str] = None,
	hospital_id: Optional[str] = None,
	city: Optional[str] = None,
	page: int = 1,
	size: int = 20,
) -> list[BloodRequest]:
	"""
	Kan taleplerini filtreleyerek ve sayfalayarak döndürür.

	Varsayılan davranış: expired olmayan kayıtlar döner.
	"""
	conditions = []
	now = datetime.now(timezone.utc)

	if status:
		conditions.append(BloodRequest.status == status.upper())
	else:
		conditions.append(BloodRequest.status != RequestStatus.EXPIRED.value)
		conditions.append(
			or_(
				BloodRequest.expires_at.is_(None),
				BloodRequest.expires_at >= now,
			)
		)

	if blood_type:
		conditions.append(BloodRequest.blood_type == blood_type.upper())
	if request_type:
		conditions.append(BloodRequest.request_type == request_type.upper())
	if hospital_id:
		conditions.append(BloodRequest.hospital_id == hospital_id)

	stmt = select(BloodRequest)
	if city:
		stmt = stmt.join(Hospital, Hospital.id == BloodRequest.hospital_id)
		conditions.append(Hospital.city.ilike(f"%{city}%"))

	offset = (page - 1) * size
	stmt = (
		stmt.where(and_(*conditions))
		.order_by(BloodRequest.created_at.desc())
		.offset(offset)
		.limit(size)
	)

	result = await db.execute(stmt)
	return list(result.scalars().all())


async def find_nearby_donors(db: AsyncSession, request_id: str) -> list[User]:
	"""Verilen talep için yakındaki uygun bağışçıları döndürür."""
	request_row = await db.execute(
		select(BloodRequest, Hospital)
		.join(Hospital, Hospital.id == BloodRequest.hospital_id)
		.where(BloodRequest.id == request_id)
	)
	row = request_row.first()
	if row is None:
		raise NotFoundException("Kan talebi bulunamadı")

	blood_request, hospital = row
	compatible_donors = get_compatible_donors(blood_request.blood_type)
	if not compatible_donors:
		return []

	now = datetime.now(timezone.utc)
	radius_meters = (
		hospital.geofence_radius_meters
		if hospital.geofence_radius_meters
		else settings.DEFAULT_SEARCH_RADIUS_KM * 1000
	)

	active_commitment_exists = exists(
		select(DonationCommitment.id).where(
			DonationCommitment.donor_id == User.id,
			DonationCommitment.status.in_(
				[CommitmentStatus.ON_THE_WAY.value, CommitmentStatus.ARRIVED.value]
			),
		)
	)

	distance_expr = func.ST_Distance(User.location, blood_request.location).label("distance_meters")

	stmt = (
		select(User, distance_expr)
		.where(
			User.deleted_at.is_(None),
			User.is_active == True,
			User.id != blood_request.requester_id,
			User.location.is_not(None),
			User.fcm_token.is_not(None),
			User.blood_type.in_(compatible_donors),
			or_(User.next_available_date.is_(None), User.next_available_date <= now),
			~active_commitment_exists,
			func.ST_DWithin(User.location, blood_request.location, radius_meters),
		)
		.order_by(distance_expr)
		.limit(50)
	)

	result = await db.execute(stmt)
	rows = result.all()

	donors: list[User] = []
	for donor, distance_meters in rows:
		donor.distance_km = round((distance_meters or 0) / 1000, 3)
		donors.append(donor)

	return donors


async def update_request(
	db: AsyncSession,
	request_id: str,
	requester_id: str,
	data: dict,
) -> BloodRequest:
	"""
	Kan talebini günceller.

	İş kuralları:
	- Sadece talep sahibi güncelleyebilir
	- Terminal durumdaki talepler güncellenemez
	"""
	blood_request = await get_request(db, request_id)

	if blood_request.requester_id != requester_id:
		raise ForbiddenException("Bu talebi güncelleme yetkiniz yok")

	if blood_request.status in {
		RequestStatus.FULFILLED.value,
		RequestStatus.CANCELLED.value,
		RequestStatus.EXPIRED.value,
	}:
		raise BadRequestException("Bu durumdaki talep güncellenemez")

	if "units_needed" in data and data["units_needed"] < blood_request.units_collected:
		raise BadRequestException("units_needed, units_collected değerinden küçük olamaz")

	updatable_fields = {"units_needed", "priority", "status", "patient_name", "notes"}
	for field, value in data.items():
		if field in updatable_fields:
			setattr(blood_request, field, value)

	await db.flush()
	await db.refresh(blood_request)
	return blood_request


async def cancel_request(db: AsyncSession, request_id: str, requester_id: str) -> BloodRequest:
	"""
	Kan talebini iptal eder ve aktif commitment'ları da iptal eder.
	"""
	blood_request = await get_request(db, request_id)

	if blood_request.requester_id != requester_id:
		raise ForbiddenException("Bu talebi iptal etme yetkiniz yok")

	if blood_request.status in {RequestStatus.FULFILLED.value, RequestStatus.EXPIRED.value}:
		raise BadRequestException("Bu durumdaki talep iptal edilemez")

	blood_request.status = RequestStatus.CANCELLED.value

	await db.execute(
		update(DonationCommitment)
		.where(
			DonationCommitment.blood_request_id == request_id,
			DonationCommitment.status.in_(
				[CommitmentStatus.ON_THE_WAY.value, CommitmentStatus.ARRIVED.value]
			),
		)
		.values(status=CommitmentStatus.CANCELLED.value)
	)

	await db.flush()
	await db.refresh(blood_request)
	return blood_request


async def expire_stale_requests(db: AsyncSession) -> int:
	"""
	Süresi dolmuş ACTIVE talepleri EXPIRED yapar.

	Returns:
		Expire edilen talep sayısı
	"""
	now = datetime.now(timezone.utc)
	result = await db.execute(
		update(BloodRequest)
		.where(
			BloodRequest.status == RequestStatus.ACTIVE.value,
			BloodRequest.expires_at.is_not(None),
			BloodRequest.expires_at < now,
		)
		.values(status=RequestStatus.EXPIRED.value)
	)
	await db.flush()
	return result.rowcount or 0
