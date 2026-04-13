"""Donors router for donor-facing nearby request listing and commitment management."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import BloodType, CommitmentStatus, RequestStatus
from app.core.exceptions import BadRequestException
from app.dependencies import get_current_active_user, get_db
from app.models import BloodRequest, DonationCommitment, Hospital, User
from app.schemas import (
	BloodRequestHospitalInfo,
	BloodRequestListResponse,
	BloodRequestRequesterInfo,
	BloodRequestResponse,
	CommitmentCreateRequest,
	CommitmentResponse,
	CommitmentStatusUpdateRequest,
	CommitmentListResponse,
	CommitmentDonorInfo,
	CommitmentRequestInfo,
	QRCodeInfo,
)
from app.services.donation_service import (
	create_commitment,
	update_commitment_status,
	get_active_commitment,
	get_commitment_by_id,
)
from app.utils.cooldown import is_in_cooldown
from app.utils.validators import can_donate_to
from app.utils.qr_code import format_qr_content

router = APIRouter(tags=["Donors"])


def _compatible_request_blood_types(donor_blood_type: str) -> list[str]:
	return [
		recipient
		for recipient in BloodType.all_values()
		if can_donate_to(donor_blood_type, recipient)
	]


def _build_request_response(
	request_obj: BloodRequest,
	hospital: Hospital,
	requester: User,
) -> BloodRequestResponse:
	hospital_info = BloodRequestHospitalInfo(
		id=hospital.id,
		name=hospital.name,
		hospital_code=hospital.hospital_code,
		district=hospital.district,
		city=hospital.city,
		phone_number=hospital.phone_number,
	)
	requester_info = BloodRequestRequesterInfo(
		id=requester.id,
		full_name=requester.full_name,
		phone_number=requester.phone_number,
	)

	return BloodRequestResponse(
		id=request_obj.id,
		request_code=request_obj.request_code,
		blood_type=request_obj.blood_type,
		request_type=request_obj.request_type,
		priority=request_obj.priority,
		units_needed=request_obj.units_needed,
		units_collected=request_obj.units_collected,
		status=request_obj.status,
		expires_at=request_obj.expires_at,
		patient_name=request_obj.patient_name,
		notes=request_obj.notes,
		hospital=hospital_info,
		requester=requester_info,
		distance_km=getattr(request_obj, "distance_km", None),
		created_at=request_obj.created_at,
		updated_at=request_obj.updated_at,
	)


@router.get(
	"/nearby",
	response_model=BloodRequestListResponse,
	status_code=status.HTTP_200_OK,
	summary="Yakındaki talepleri listele",
)
async def list_nearby_requests_for_donor(
	page: int = Query(1, ge=1),
	size: int = Query(20, ge=1, le=100),
	radius_km: float = Query(settings.DEFAULT_SEARCH_RADIUS_KM, gt=0),
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	if current_user.location is None:
		raise BadRequestException("Yakindaki talepleri gormek icin once konum bilginizi guncelleyin")

	if is_in_cooldown(current_user):
		return BloodRequestListResponse(
			items=[],
			total=0,
			page=page,
			size=size,
			pages=0,
		)

	active_commitment_result = await db.execute(
		select(DonationCommitment.id)
		.where(
			DonationCommitment.donor_id == current_user.id,
			DonationCommitment.status.in_(
				[CommitmentStatus.ON_THE_WAY.value, CommitmentStatus.ARRIVED.value]
			),
		)
		.limit(1)
	)
	if active_commitment_result.scalar_one_or_none() is not None:
		return BloodRequestListResponse(
			items=[],
			total=0,
			page=page,
			size=size,
			pages=0,
		)

	compatible_blood_types = _compatible_request_blood_types(current_user.blood_type or "")
	if not compatible_blood_types:
		return BloodRequestListResponse(
			items=[],
			total=0,
			page=page,
			size=size,
			pages=0,
		)

	now = func.now()
	radius_meters = radius_km * 1000
	distance_expr = func.ST_Distance(BloodRequest.location, current_user.location).label("distance_meters")

	conditions = [
		BloodRequest.status == RequestStatus.ACTIVE.value,
		BloodRequest.blood_type.in_(compatible_blood_types),
		BloodRequest.requester_id != current_user.id,
		or_(BloodRequest.expires_at.is_(None), BloodRequest.expires_at >= now),
		func.ST_DWithin(BloodRequest.location, current_user.location, radius_meters),
	]

	offset = (page - 1) * size
	stmt = (
		select(BloodRequest, Hospital, User, distance_expr)
		.join(Hospital, Hospital.id == BloodRequest.hospital_id)
		.join(User, User.id == BloodRequest.requester_id)
		.where(and_(*conditions))
		.order_by(distance_expr)
		.offset(offset)
		.limit(size)
	)
	result = await db.execute(stmt)
	rows = result.all()

	count_result = await db.execute(select(func.count(BloodRequest.id)).where(and_(*conditions)))
	total = count_result.scalar() or 0
	pages = math.ceil(total / size) if total > 0 else 0

	requests_with_context: list[tuple[BloodRequest, Hospital, User]] = []
	for req, hospital, requester, distance_meters in rows:
		req.distance_km = round((distance_meters or 0) / 1000, 3)
		requests_with_context.append((req, hospital, requester))

	items = [
		_build_request_response(req, hospital, requester)
		for req, hospital, requester in requests_with_context
	]

	return BloodRequestListResponse(
		items=items,
		total=total,
		page=page,
		size=size,
		pages=pages,
	)


# =============================================================================
# COMMITMENT HELPER FUNCTIONS
# =============================================================================


async def _build_commitment_response(
	db: AsyncSession,
	commitment: DonationCommitment,
) -> CommitmentResponse:
	"""
	Build a CommitmentResponse from a DonationCommitment model.

	Fetches related entities (donor, blood_request, hospital) and
	constructs nested schemas.

	Args:
		db: AsyncSession
		commitment: DonationCommitment model instance

	Returns:
		CommitmentResponse with nested donor and request info
	"""
	# Fetch related entities
	donor_result = await db.execute(
		select(User).where(User.id == commitment.donor_id)
	)
	donor = donor_result.scalar_one()

	request_result = await db.execute(
		select(BloodRequest).where(BloodRequest.id == commitment.blood_request_id)
	)
	blood_request = request_result.scalar_one()

	hospital_result = await db.execute(
		select(Hospital).where(Hospital.id == blood_request.hospital_id)
	)
	hospital = hospital_result.scalar_one()

	# Build nested schemas
	donor_info = CommitmentDonorInfo(
		id=donor.id,
		full_name=donor.full_name,
		blood_type=donor.blood_type or "",
		phone_number=donor.phone_number,
	)

	request_info = CommitmentRequestInfo(
		id=blood_request.id,
		request_code=blood_request.request_code,
		blood_type=blood_request.blood_type,
		request_type=blood_request.request_type,
		hospital_name=hospital.name,
		hospital_district=hospital.district,
		hospital_city=hospital.city,
	)

	# QR code info - query separately for async compatibility
	qr_code_info: Optional[QRCodeInfo] = None
	from app.models import QRCode
	qr_result = await db.execute(
		select(QRCode).where(QRCode.commitment_id == commitment.id)
	)
	qr_code = qr_result.scalar_one_or_none()
	if qr_code:
		qr_code_info = QRCodeInfo(
			token=qr_code.token,
			signature=qr_code.signature,
			expires_at=qr_code.expires_at,
			is_used=qr_code.is_used,
			qr_content=format_qr_content(qr_code.token, qr_code.commitment_id, qr_code.signature),
		)

	return CommitmentResponse(
		id=commitment.id,
		donor=donor_info,
		blood_request=request_info,
		status=commitment.status,
		timeout_minutes=commitment.timeout_minutes,
		committed_at=commitment.created_at,
		arrived_at=commitment.arrived_at,
		qr_code=qr_code_info,
		created_at=commitment.created_at,
		updated_at=commitment.updated_at,
	)


# =============================================================================
# COMMITMENT ENDPOINTS
# =============================================================================


@router.post(
	"/accept",
	response_model=CommitmentResponse,
	status_code=status.HTTP_201_CREATED,
	summary="Bağış taahhüdü ver (Geliyorum)",
)
async def accept_commitment(
	data: CommitmentCreateRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	"""
	Bağışçı "Geliyorum" taahhüdü verir.

	İş Akışı:
	1. Kan talebinin aktif olduğunu kontrol eder
	2. Bağışçının cooldown'da olmadığını doğrular
	3. Bağışçının başka aktif taahhüdü olmadığını kontrol eder
	4. Kan grubu uyumluluğunu doğrular
	5. N+1 kuralı kontrolü yapar
	6. Yeni taahhüt oluşturur (ON_THE_WAY durumu)

	Returns:
		201 Created: Oluşturulan taahhüt bilgileri

	Errors:
		400: Cooldown aktif, talep expire olmuş, kan grubu uyumsuz
		404: Talep bulunamadı
		409: Zaten aktif taahhüt var, slot dolu (N+1)
	"""
	commitment = await create_commitment(db, current_user.id, data.request_id)
	await db.commit()
	await db.refresh(commitment)

	return await _build_commitment_response(db, commitment)


@router.get(
	"/me/commitment",
	response_model=Optional[CommitmentResponse],
	status_code=status.HTTP_200_OK,
	summary="Aktif taahhüdümü getir",
)
async def get_my_active_commitment(
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	"""
	Bağışçının aktif taahhüdünü getirir.

	Aktif durumlar: ON_THE_WAY, ARRIVED

	Returns:
		200 OK: Aktif taahhüt bilgileri veya null
	"""
	commitment = await get_active_commitment(db, current_user.id)

	if not commitment:
		return None

	return await _build_commitment_response(db, commitment)


@router.patch(
	"/me/commitment/{commitment_id}",
	response_model=CommitmentResponse,
	status_code=status.HTTP_200_OK,
	summary="Taahhüt durumunu güncelle",
)
async def update_my_commitment_status(
	commitment_id: str,
	data: CommitmentStatusUpdateRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	"""
	Taahhüt durumunu günceller.

	İzin verilen status'lar: ARRIVED, CANCELLED

	Args:
		commitment_id: Taahhüt UUID'si
		data: Yeni durum ve iptal nedeni (CANCELLED için)

	Returns:
		200 OK: Güncellenmiş taahhüt bilgileri

	Errors:
		403: Taahhüt size ait değil
		404: Taahhüt bulunamadı
		400: Terminal durumdaki taahhüt güncellenemez
	"""
	commitment = await update_commitment_status(
		db,
		commitment_id,
		current_user.id,
		data.status,
		data.cancel_reason,
	)
	await db.commit()
	await db.refresh(commitment)

	return await _build_commitment_response(db, commitment)


@router.get(
	"/history",
	response_model=CommitmentListResponse,
	status_code=status.HTTP_200_OK,
	summary="Bağış geçmişimi listele",
)
async def get_donor_history(
	page: int = Query(1, ge=1),
	size: int = Query(20, ge=1, le=100),
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	"""
	Bağışçının tüm taahhüt geçmişini listeler.

	Tüm durumlar dahil: ON_THE_WAY, ARRIVED, COMPLETED, CANCELLED, TIMEOUT
	Tarihe göre descending sıralı.

	Args:
		page: Sayfa numarası (1'den başlar)
		size: Sayfa başına kayıt sayısı

	Returns:
		Pagination metadata ile birlikte taahhüt listesi
	"""
	# Count total
	count_result = await db.execute(
		select(func.count(DonationCommitment.id)).where(
			DonationCommitment.donor_id == current_user.id
		)
	)
	total = count_result.scalar() or 0
	pages = math.ceil(total / size) if total > 0 else 0

	# Fetch commitments with pagination
	offset = (page - 1) * size
	result = await db.execute(
		select(DonationCommitment)
		.where(DonationCommitment.donor_id == current_user.id)
		.order_by(desc(DonationCommitment.created_at))
		.offset(offset)
		.limit(size)
	)
	commitments = list(result.scalars().all())

	# Build response items
	items = []
	for commitment in commitments:
		response = await _build_commitment_response(db, commitment)
		items.append(response)

	return CommitmentListResponse(
		items=items,
		total=total,
		page=page,
		size=size,
		pages=pages,
	)
