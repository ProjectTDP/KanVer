"""
Blood Request Router.

Kan talebi oluşturma, listeleme, detay, güncelleme ve iptal endpoint'lerini sağlar.
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import UserRole, CommitmentStatus, RequestStatus
from app.core.exceptions import BadRequestException, ForbiddenException, GeofenceException
from app.dependencies import get_db, get_current_active_user
from app.models import User, BloodRequest, Hospital, DonationCommitment
from app.schemas import (
	BloodRequestCreateRequest,
	BloodRequestUpdateRequest,
	BloodRequestResponse,
	BloodRequestListResponse,
	BloodRequestHospitalInfo,
	BloodRequestRequesterInfo,
	MessageResponse,
)
from app.services.blood_request_service import (
	create_request,
	list_requests,
	get_request,
	update_request,
	cancel_request,
)

router = APIRouter(tags=["Blood Requests"])


async def _build_response(db: AsyncSession, request_obj: BloodRequest) -> BloodRequestResponse:
	hospital_result = await db.execute(
		select(Hospital).where(Hospital.id == request_obj.hospital_id)
	)
	hospital = hospital_result.scalar_one()

	requester_result = await db.execute(
		select(User).where(User.id == request_obj.requester_id)
	)
	requester = requester_result.scalar_one()

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


@router.post(
	"",
	response_model=BloodRequestResponse,
	status_code=status.HTTP_201_CREATED,
	summary="Talep oluştur",
)
async def create_request_endpoint(
	data: BloodRequestCreateRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	try:
		request_obj = await create_request(db, current_user.id, data.model_dump())
		await db.commit()
	except GeofenceException as exc:
		raise ForbiddenException(str(exc.message)) from exc
	return await _build_response(db, request_obj)


@router.get(
	"",
	response_model=BloodRequestListResponse,
	status_code=status.HTTP_200_OK,
	summary="Talepleri listele",
)
async def list_requests_endpoint(
	status_filter: Optional[str] = Query(None, alias="status"),
	blood_type: Optional[str] = Query(None),
	request_type: Optional[str] = Query(None),
	hospital_id: Optional[str] = Query(None),
	city: Optional[str] = Query(None),
	page: int = Query(1, ge=1),
	size: int = Query(20, ge=1, le=100),
	db: AsyncSession = Depends(get_db),
	_: User = Depends(get_current_active_user),
):
	items = await list_requests(
		db,
		status=status_filter,
		blood_type=blood_type,
		request_type=request_type,
		hospital_id=hospital_id,
		city=city,
		page=page,
		size=size,
	)

	# Toplam kayıt sayısı (pagination metadata için)
	conditions = []
	if status_filter:
		conditions.append(BloodRequest.status == status_filter.upper())
	else:
		now = func.now()
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

	count_stmt = select(func.count(BloodRequest.id))
	if city:
		count_stmt = count_stmt.join(Hospital, Hospital.id == BloodRequest.hospital_id)
		conditions.append(Hospital.city.ilike(f"%{city}%"))

	total_result = await db.execute(count_stmt.where(and_(*conditions)))
	total = total_result.scalar() or 0
	pages = math.ceil(total / size) if total > 0 else 0

	response_items = [await _build_response(db, item) for item in items]

	return BloodRequestListResponse(
		items=response_items,
		total=total,
		page=page,
		size=size,
		pages=pages,
		filtered_by_status=status_filter,
		filtered_by_blood_type=blood_type,
		filtered_by_request_type=request_type,
		filtered_by_hospital_id=hospital_id,
		filtered_by_city=city,
	)


@router.get(
	"/{request_id}",
	status_code=status.HTTP_200_OK,
	summary="Talep detayı",
)
async def get_request_detail_endpoint(
	request_id: str,
	db: AsyncSession = Depends(get_db),
	_: User = Depends(get_current_active_user),
):
	request_obj = await get_request(db, request_id)
	response = await _build_response(db, request_obj)

	commitment_count_result = await db.execute(
		select(func.count(DonationCommitment.id)).where(
			DonationCommitment.blood_request_id == request_id
		)
	)
	commitment_count = commitment_count_result.scalar() or 0

	payload = response.model_dump()
	payload["commitment_count"] = commitment_count
	return payload


@router.patch(
	"/{request_id}",
	response_model=BloodRequestResponse,
	status_code=status.HTTP_200_OK,
	summary="Talep güncelle",
)
async def update_request_endpoint(
	request_id: str,
	data: BloodRequestUpdateRequest,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	request_obj = await update_request(
		db,
		request_id,
		current_user.id,
		data.model_dump(exclude_unset=True),
	)
	await db.commit()
	return await _build_response(db, request_obj)


@router.delete(
	"/{request_id}",
	response_model=MessageResponse,
	status_code=status.HTTP_200_OK,
	summary="Talep iptal et",
)
async def cancel_request_endpoint(
	request_id: str,
	db: AsyncSession = Depends(get_db),
	current_user: User = Depends(get_current_active_user),
):
	request_obj = await get_request(db, request_id)

	if current_user.role == UserRole.ADMIN.value and request_obj.requester_id != current_user.id:
		if request_obj.status in {RequestStatus.FULFILLED.value, RequestStatus.EXPIRED.value}:
			raise BadRequestException("Bu durumdaki talep iptal edilemez")

		request_obj.status = RequestStatus.CANCELLED.value
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
		await db.commit()
		return MessageResponse(message="Talep iptal edildi")

	await cancel_request(db, request_id, current_user.id)
	await db.commit()
	return MessageResponse(message="Talep iptal edildi")
