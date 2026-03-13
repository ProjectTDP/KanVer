"""Donors router for donor-facing nearby request listing."""

import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func, and_, or_
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
)
from app.utils.cooldown import is_in_cooldown
from app.utils.validators import can_donate_to

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
