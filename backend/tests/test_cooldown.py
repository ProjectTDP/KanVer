"""
Unit tests for cooldown utility.

Task 7.1 kapsaminda cooldown hesaplama ve uygulama fonksiyonlarini dogrular.
"""
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

from app.constants import RequestType, UserRole
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import hash_password
from app.models import User
from app.utils.cooldown import (
    calculate_next_available,
    get_cooldown_end,
    is_in_cooldown,
    set_cooldown,
)


@pytest_asyncio.fixture
async def cooldown_user(db_session):
    user = User(
        phone_number="+905550001122",
        password_hash=hash_password("TestPassword123"),
        full_name="Cooldown Test User",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


def _build_user() -> User:
    return User(
        phone_number="+905550001133",
        password_hash=hash_password("TestPassword123"),
        full_name="Cooldown Plain User",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
    )


def test_whole_blood_cooldown_90_days():
    donation_date = datetime(2026, 3, 13, 10, 0, tzinfo=timezone.utc)

    next_available = calculate_next_available(
        RequestType.WHOLE_BLOOD.value,
        donation_date,
    )

    assert next_available == donation_date + timedelta(days=90)


def test_apheresis_cooldown_48_hours():
    donation_date = datetime(2026, 3, 13, 10, 0, tzinfo=timezone.utc)

    next_available = calculate_next_available(
        RequestType.APHERESIS.value,
        donation_date,
    )

    assert next_available == donation_date + timedelta(hours=48)


def test_not_in_cooldown():
    cooldown_user = _build_user()
    cooldown_user.next_available_date = datetime.now(timezone.utc) - timedelta(days=1)

    assert is_in_cooldown(cooldown_user) is False


def test_not_in_cooldown_when_date_missing():
    cooldown_user = _build_user()
    cooldown_user.next_available_date = None

    assert is_in_cooldown(cooldown_user) is False


def test_in_cooldown():
    cooldown_user = _build_user()
    cooldown_user.next_available_date = datetime.now(timezone.utc) + timedelta(hours=1)

    assert is_in_cooldown(cooldown_user) is True


def test_get_cooldown_end_returns_next_available_date():
    cooldown_user = _build_user()
    expected = datetime.now(timezone.utc) + timedelta(days=10)
    cooldown_user.next_available_date = expected

    assert get_cooldown_end(cooldown_user) == expected


def test_get_cooldown_end_returns_none_when_not_set():
    cooldown_user = _build_user()
    cooldown_user.next_available_date = None

    assert get_cooldown_end(cooldown_user) is None


def test_calculate_next_available_invalid_type_raises():
    donation_date = datetime.now(timezone.utc)

    with pytest.raises(BadRequestException):
        calculate_next_available("INVALID", donation_date)


def test_calculate_next_available_with_naive_datetime_treats_as_utc():
    donation_date = datetime(2026, 3, 13, 10, 0)

    next_available = calculate_next_available(
        RequestType.WHOLE_BLOOD.value,
        donation_date,
    )

    assert next_available == datetime(2026, 6, 11, 10, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_set_cooldown_updates_user_for_whole_blood(db_session, cooldown_user):
    before = datetime.now(timezone.utc)

    updated_user = await set_cooldown(
        db_session,
        cooldown_user.id,
        RequestType.WHOLE_BLOOD.value,
    )

    after = datetime.now(timezone.utc)

    assert updated_user.last_donation_date is not None
    assert before <= updated_user.last_donation_date <= after
    assert updated_user.next_available_date is not None
    assert updated_user.next_available_date == updated_user.last_donation_date + timedelta(days=90)


@pytest.mark.asyncio
async def test_set_cooldown_updates_user_for_apheresis(db_session, cooldown_user):
    updated_user = await set_cooldown(
        db_session,
        cooldown_user.id,
        RequestType.APHERESIS.value,
    )

    assert updated_user.last_donation_date is not None
    assert updated_user.next_available_date is not None
    assert updated_user.next_available_date == updated_user.last_donation_date + timedelta(hours=48)


@pytest.mark.asyncio
async def test_set_cooldown_user_not_found_raises(db_session):
    with pytest.raises(NotFoundException):
        await set_cooldown(
            db_session,
            "00000000-0000-0000-0000-000000000000",
            RequestType.WHOLE_BLOOD.value,
        )


@pytest.mark.asyncio
async def test_set_cooldown_invalid_type_raises(db_session, cooldown_user):
    with pytest.raises(BadRequestException):
        await set_cooldown(db_session, cooldown_user.id, "INVALID")