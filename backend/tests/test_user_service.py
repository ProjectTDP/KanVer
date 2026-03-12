"""
Unit tests for User Service.

Bu dosya, user_service.py fonksiyonları için unit testler içerir.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.models import User
from app.services.user_service import (
    get_user_by_id,
    get_user_by_phone,
    update_user_profile,
    update_user_location,
    soft_delete_user,
    get_user_stats,
)
from app.core.exceptions import ConflictException
from app.core.security import hash_password


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def test_user(db_session):
    """Test için bir kullanıcı oluşturur."""
    user = User(
        phone_number="+905551234567",
        password_hash=hash_password("TestPassword123"),
        full_name="Test User",
        email="test@example.com",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        hero_points=150,
        trust_score=95,
        total_donations=3,
        no_show_count=1,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def another_user(db_session):
    """Test için ikinci bir kullanıcı oluşturur (email conflict testi için)."""
    user = User(
        phone_number="+905559876543",
        password_hash=hash_password("TestPassword123"),
        full_name="Another User",
        email="another@example.com",
        date_of_birth=datetime(1995, 5, 15, tzinfo=timezone.utc),
        blood_type="B+",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_with_cooldown(db_session):
    """Cooldown'da olan bir kullanıcı oluşturur."""
    user = User(
        phone_number="+905551112223",
        password_hash=hash_password("TestPassword123"),
        full_name="Cooldown User",
        email="cooldown@example.com",
        date_of_birth=datetime(1988, 10, 20, tzinfo=timezone.utc),
        blood_type="O+",
        next_available_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# =============================================================================
# GET USER BY ID TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_by_id_exists(db_session, test_user):
    """Var olan kullanıcıyı ID ile bulur."""
    found_user = await get_user_by_id(db_session, test_user.id)

    assert found_user is not None
    assert found_user.id == test_user.id
    assert found_user.phone_number == test_user.phone_number
    assert found_user.full_name == test_user.full_name


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session):
    """Var olmayan kullanıcı ID'si ile None döner."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    found_user = await get_user_by_id(db_session, fake_id)

    assert found_user is None


# =============================================================================
# GET USER BY PHONE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_by_phone_exists(db_session, test_user):
    """Var olan kullanıcıyı telefon ile bulur."""
    found_user = await get_user_by_phone(db_session, "+905551234567")

    assert found_user is not None
    assert found_user.id == test_user.id
    assert found_user.phone_number == test_user.phone_number


@pytest.mark.asyncio
async def test_get_user_by_phone_normalization(db_session, test_user):
    """Farklı formatlarda telefon numarasını normalize eder."""
    # +905551234567 ile kayıtlı
    test_cases = [
        "05551234567",   # 0 ile başlayan
        "5551234567",    # Kısa format
        "+905551234567", # Uluslararası format
    ]

    for phone in test_cases:
        found_user = await get_user_by_phone(db_session, phone)
        assert found_user is not None
        assert found_user.id == test_user.id


@pytest.mark.asyncio
async def test_get_user_by_phone_not_found(db_session):
    """Var olmayan telefon ile None döner."""
    found_user = await get_user_by_phone(db_session, "+905999999999")

    assert found_user is None


# =============================================================================
# UPDATE USER PROFILE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_update_user_profile_full_name(db_session, test_user):
    """Kullanıcının adını günceller."""
    updated_user = await update_user_profile(
        db_session,
        test_user,
        {"full_name": "Updated Name"}
    )

    assert updated_user.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_update_user_profile_email(db_session, test_user):
    """Kullanıcının email adresini günceller."""
    updated_user = await update_user_profile(
        db_session,
        test_user,
        {"email": "updated@example.com"}
    )

    assert updated_user.email == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_profile_fcm_token(db_session, test_user):
    """Kullanıcının FCM token'ını günceller."""
    new_token = "new_fcm_token_xyz123"
    updated_user = await update_user_profile(
        db_session,
        test_user,
        {"fcm_token": new_token}
    )

    assert updated_user.fcm_token == new_token


@pytest.mark.asyncio
async def test_update_user_profile_multiple_fields(db_session, test_user):
    """Birden fazla alanı aynı anda günceller."""
    updated_user = await update_user_profile(
        db_session,
        test_user,
        {
            "full_name": "Multi Update",
            "email": "multi@example.com",
            "fcm_token": "token123"
        }
    )

    assert updated_user.full_name == "Multi Update"
    assert updated_user.email == "multi@example.com"
    assert updated_user.fcm_token == "token123"


@pytest.mark.asyncio
async def test_update_user_profile_email_to_same_value(db_session, test_user):
    """Email değerini aynı değere günceller (conflict olmamalı)."""
    # Aynı email ile tekrar güncelle
    updated_user = await update_user_profile(
        db_session,
        test_user,
        {"email": test_user.email}
    )

    assert updated_user.email == test_user.email


@pytest.mark.asyncio
async def test_update_user_profile_email_unique_conflict(db_session, test_user, another_user):
    """Başka bir kullanıcıda kullanılan email ile güncelleme conflict fırlatır."""
    with pytest.raises(ConflictException) as exc_info:
        await update_user_profile(
            db_session,
            test_user,
            {"email": another_user.email}  # another_user'ın email'i
        )

    assert "zaten kullanımda" in exc_info.value.message


@pytest.mark.asyncio
async def test_update_user_profile_ignores_invalid_fields(db_session, test_user):
    """Geçersiz alanları görmezden gelir."""
    original_name = test_user.full_name
    original_email = test_user.email

    updated_user = await update_user_profile(
        db_session,
        test_user,
        {
            "invalid_field": "should_be_ignored",
            "phone_number": "+905999999999",  # Güncellenemez
            "blood_type": "O-",  # Güncellenemez
        }
    )

    # Değerler değişmemeli
    assert updated_user.full_name == original_name
    assert updated_user.email == original_email
    assert updated_user.phone_number == test_user.phone_number
    assert updated_user.blood_type == test_user.blood_type


@pytest.mark.asyncio
async def test_update_user_profile_email_to_none(db_session, test_user):
    """Email'i None yapmak için güncelleme."""
    updated_user = await update_user_profile(
        db_session,
        test_user,
        {"email": None}
    )

    assert updated_user.email is None


# =============================================================================
# UPDATE USER LOCATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_update_user_location_success(db_session, test_user):
    """Kullanıcı konumunu başarıyla günceller."""
    lat, lng = 36.8969, 30.7133  # Antalya

    updated_user = await update_user_location(
        db_session,
        test_user,
        latitude=lat,
        longitude=lng
    )

    assert updated_user.location is not None
    assert updated_user.location_updated_at is not None
    # Konum güncelleme zamanı yakın olmalı (1 saniye içinde)
    assert (datetime.now(timezone.utc) - updated_user.location_updated_at).total_seconds() < 1


@pytest.mark.asyncio
async def test_update_user_location_boundaries(db_session, test_user):
    """Kullanıcı konumunu sınır değerlerle günceller."""
    # Enlem sınırları
    await update_user_location(db_session, test_user, latitude=-90, longitude=0)
    assert test_user.location is not None

    await update_user_location(db_session, test_user, latitude=90, longitude=0)
    assert test_user.location is not None

    # Boylam sınırları
    await update_user_location(db_session, test_user, latitude=0, longitude=-180)
    assert test_user.location is not None

    await update_user_location(db_session, test_user, latitude=0, longitude=180)
    assert test_user.location is not None


@pytest.mark.asyncio
async def test_update_user_location_invalid_latitude_too_high(db_session, test_user):
    """Geçersiz enlem (90'dan büyük) ValueError fırlatır."""
    with pytest.raises(ValueError) as exc_info:
        await update_user_location(
            db_session,
            test_user,
            latitude=91,
            longitude=0
        )

    assert "enlem" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_user_location_invalid_latitude_too_low(db_session, test_user):
    """Geçersiz enlem (-90'dan küçük) ValueError fırlatır."""
    with pytest.raises(ValueError) as exc_info:
        await update_user_location(
            db_session,
            test_user,
            latitude=-91,
            longitude=0
        )

    assert "enlem" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_user_location_invalid_longitude_too_high(db_session, test_user):
    """Geçersiz boylam (180'dan büyük) ValueError fırlatır."""
    with pytest.raises(ValueError) as exc_info:
        await update_user_location(
            db_session,
            test_user,
            latitude=0,
            longitude=181
        )

    assert "boylam" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_update_user_location_invalid_longitude_too_low(db_session, test_user):
    """Geçersiz boylam (-180'dan küçük) ValueError fırlatır."""
    with pytest.raises(ValueError) as exc_info:
        await update_user_location(
            db_session,
            test_user,
            latitude=0,
            longitude=-181
        )

    assert "boylam" in str(exc_info.value).lower()


# =============================================================================
# SOFT DELETE USER TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_soft_delete_user_sets_deleted_at(db_session, test_user):
    """Kullanıcıyı soft delete yaparak deleted_at işaretler."""
    assert test_user.deleted_at is None

    await soft_delete_user(db_session, test_user)

    assert test_user.deleted_at is not None
    # Silinme zamanı yakın olmalı
    assert (datetime.now(timezone.utc) - test_user.deleted_at).total_seconds() < 1


@pytest.mark.asyncio
async def test_soft_delete_user_sets_is_active_false(db_session, test_user):
    """Kullanıcıyı soft delete yaparak is_active False yapar."""
    assert test_user.is_active is True

    await soft_delete_user(db_session, test_user)

    assert test_user.is_active is False


@pytest.mark.asyncio
async def test_soft_delete_user_remains_in_db(db_session, test_user):
    """Soft delete yapılan kullanıcı DB'den silinmez."""
    await soft_delete_user(db_session, test_user)

    # Kullanıcı hala DB'de olmalı
    result = await db_session.execute(
        select(User).where(User.id == test_user.id)
    )
    found_user = result.scalar_one_or_none()

    assert found_user is not None
    assert found_user.deleted_at is not None
    assert found_user.is_active is False


# =============================================================================
# GET USER STATS TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_stats_correct_values(db_session, test_user):
    """Kullanıcı istatistiklerini doğru değerlerle döner."""
    stats = await get_user_stats(db_session, test_user)

    assert stats["hero_points"] == 150
    assert stats["trust_score"] == 95
    assert stats["total_donations"] == 3
    assert stats["no_show_count"] == 1
    assert stats["next_available_date"] is None
    assert stats["last_donation_date"] is None


@pytest.mark.asyncio
async def test_get_user_stats_is_in_cooldown_true(db_session, user_with_cooldown):
    """Cooldown'da olan kullanıcı için is_in_cooldown True döner."""
    stats = await get_user_stats(db_session, user_with_cooldown)

    assert stats["is_in_cooldown"] is True
    assert stats["cooldown_remaining_days"] is not None
    assert stats["cooldown_remaining_days"] > 0


@pytest.mark.asyncio
async def test_get_user_stats_is_in_cooldown_false(db_session, test_user):
    """Cooldown'da olmayan kullanıcı için is_in_cooldown False döner."""
    stats = await get_user_stats(db_session, test_user)

    assert stats["is_in_cooldown"] is False
    assert stats["cooldown_remaining_days"] is None


@pytest.mark.asyncio
async def test_get_user_stats_rank_badge_new_hero(db_session):
    """0-49 puan arası için Yeni Kahraman rozeti."""
    user = User(
        phone_number="+905550000001",
        password_hash=hash_password("TestPassword123"),
        full_name="New Hero",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=0,
    )
    db_session.add(user)
    await db_session.flush()

    stats = await get_user_stats(db_session, user)
    assert stats["rank_badge"] == "Yeni Kahraman"


@pytest.mark.asyncio
async def test_get_user_stats_rank_badge_bronze(db_session, test_user):
    """50-199 puan arası için Bronz Kahraman rozeti."""
    # test_user hero_points = 150
    stats = await get_user_stats(db_session, test_user)
    assert stats["rank_badge"] == "Bronz Kahraman"


@pytest.mark.asyncio
async def test_get_user_stats_rank_badge_silver(db_session):
    """200-499 puan arası için Gümüş Kahraman rozeti."""
    user = User(
        phone_number="+905550000002",
        password_hash=hash_password("TestPassword123"),
        full_name="Silver Hero",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=250,
    )
    db_session.add(user)
    await db_session.flush()

    stats = await get_user_stats(db_session, user)
    assert stats["rank_badge"] == "Gümüş Kahraman"


@pytest.mark.asyncio
async def test_get_user_stats_rank_badge_gold(db_session):
    """500-999 puan arası için Altın Kahraman rozeti."""
    user = User(
        phone_number="+905550000003",
        password_hash=hash_password("TestPassword123"),
        full_name="Gold Hero",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=750,
    )
    db_session.add(user)
    await db_session.flush()

    stats = await get_user_stats(db_session, user)
    assert stats["rank_badge"] == "Altın Kahraman"


@pytest.mark.asyncio
async def test_get_user_stats_rank_badge_platinum(db_session):
    """1000+ puan için Platin Kahraman rozeti."""
    user = User(
        phone_number="+905550000004",
        password_hash=hash_password("TestPassword123"),
        full_name="Platinum Hero",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=1500,
    )
    db_session.add(user)
    await db_session.flush()

    stats = await get_user_stats(db_session, user)
    assert stats["rank_badge"] == "Platin Kahraman"


@pytest.mark.asyncio
async def test_get_user_stats_rank_boundaries(db_session):
    """Rozet sınır değerlerini test eder."""
    # 49 puan -> Yeni Kahraman
    user1 = User(
        phone_number="+905550000005",
        password_hash=hash_password("TestPassword123"),
        full_name="Boundary 1",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=49,
    )
    db_session.add(user1)
    await db_session.flush()
    stats1 = await get_user_stats(db_session, user1)
    assert stats1["rank_badge"] == "Yeni Kahraman"

    # 50 puan -> Bronz Kahraman
    user2 = User(
        phone_number="+905550000006",
        password_hash=hash_password("TestPassword123"),
        full_name="Boundary 2",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=50,
    )
    db_session.add(user2)
    await db_session.flush()
    stats2 = await get_user_stats(db_session, user2)
    assert stats2["rank_badge"] == "Bronz Kahraman"

    # 199 puan -> Bronz Kahraman
    user3 = User(
        phone_number="+905550000007",
        password_hash=hash_password("TestPassword123"),
        full_name="Boundary 3",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=199,
    )
    db_session.add(user3)
    await db_session.flush()
    stats3 = await get_user_stats(db_session, user3)
    assert stats3["rank_badge"] == "Bronz Kahraman"

    # 200 puan -> Gümüş Kahraman
    user4 = User(
        phone_number="+905550000008",
        password_hash=hash_password("TestPassword123"),
        full_name="Boundary 4",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        hero_points=200,
    )
    db_session.add(user4)
    await db_session.flush()
    stats4 = await get_user_stats(db_session, user4)
    assert stats4["rank_badge"] == "Gümüş Kahraman"
