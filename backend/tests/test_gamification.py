"""
Unit tests for gamification_service.py.

Test coverage:
- get_rank_badge (5 tests: tüm rozet seviyeleri)
- award_hero_points (2 tests: whole blood ve apheresis)
- penalize_no_show (3 tests: trust score düşüşü, minimum 0, count artışı)
- get_user_rank (1 test)
- get_leaderboard (2 tests: sıralama ve limit)
"""
import pytest
from datetime import datetime, timezone

from app.services import gamification_service
from app.services.gamification_service import (
    get_rank_badge,
    award_hero_points,
    penalize_no_show,
    get_user_rank,
    get_leaderboard,
    RANK_BADGES,
)
from app.constants.status import RequestType
from app.models import User
from app.constants import UserRole


# =============================================================================
# get_rank_badge Tests
# =============================================================================

class TestGetRankBadge:
    """get_rank_badge fonksiyonu testleri."""

    def test_get_rank_badge_yeni_kahraman(self):
        """0-49 puan aralığı 'Yeni Kahraman' rozeti vermeli."""
        assert get_rank_badge(0) == "Yeni Kahraman"
        assert get_rank_badge(25) == "Yeni Kahraman"
        assert get_rank_badge(49) == "Yeni Kahraman"

    def test_get_rank_badge_bronz_kahraman(self):
        """50-199 puan aralığı 'Bronz Kahraman' rozeti vermeli."""
        assert get_rank_badge(50) == "Bronz Kahraman"
        assert get_rank_badge(100) == "Bronz Kahraman"
        assert get_rank_badge(199) == "Bronz Kahraman"

    def test_get_rank_badge_gumus_kahraman(self):
        """200-499 puan aralığı 'Gümüş Kahraman' rozeti vermeli."""
        assert get_rank_badge(200) == "Gümüş Kahraman"
        assert get_rank_badge(350) == "Gümüş Kahraman"
        assert get_rank_badge(499) == "Gümüş Kahraman"

    def test_get_rank_badge_altin_kahraman(self):
        """500-999 puan aralığı 'Altın Kahraman' rozeti vermeli."""
        assert get_rank_badge(500) == "Altın Kahraman"
        assert get_rank_badge(750) == "Altın Kahraman"
        assert get_rank_badge(999) == "Altın Kahraman"

    def test_get_rank_badge_platin_kahraman(self):
        """1000+ puan 'Platin Kahraman' rozeti vermeli."""
        assert get_rank_badge(1000) == "Platin Kahraman"
        assert get_rank_badge(5000) == "Platin Kahraman"
        assert get_rank_badge(10000) == "Platin Kahraman"


# =============================================================================
# award_hero_points Tests
# =============================================================================

class TestAwardHeroPoints:
    """award_hero_points fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_award_hero_points_whole_blood(self, db_session):
        """WHOLE_BLOOD bağışında +50 hero_points vermeli."""
        # Kullanıcı oluştur
        user = User(
            phone_number="+905551111111",
            full_name="Test Donor",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            password_hash="hash",
            blood_type="A+",
            role=UserRole.USER.value,
            hero_points=0,
        )
        db_session.add(user)
        await db_session.flush()

        # Hero points ver
        new_points = await award_hero_points(
            db_session,
            str(user.id),
            RequestType.WHOLE_BLOOD.value
        )

        assert new_points == 50
        assert user.hero_points == 50

    @pytest.mark.asyncio
    async def test_award_hero_points_apheresis(self, db_session):
        """APHERESIS bağışında +100 hero_points vermeli."""
        # Kullanıcı oluştur
        user = User(
            phone_number="+905552222222",
            full_name="Test Apheresis Donor",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            password_hash="hash",
            blood_type="B+",
            role=UserRole.USER.value,
            hero_points=50,  # Başlangıç puanı
        )
        db_session.add(user)
        await db_session.flush()

        # Hero points ver
        new_points = await award_hero_points(
            db_session,
            str(user.id),
            RequestType.APHERESIS.value
        )

        assert new_points == 150  # 50 + 100
        assert user.hero_points == 150


# =============================================================================
# penalize_no_show Tests
# =============================================================================

class TestPenalizeNoShow:
    """penalize_no_show fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_penalize_no_show_decreases_trust_score(self, db_session):
        """No-show trust_score'u 10 düşürmeli."""
        # Kullanıcı oluştur
        user = User(
            phone_number="+905553333333",
            full_name="No Show User",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            password_hash="hash",
            blood_type="O+",
            role=UserRole.USER.value,
            trust_score=100,
            no_show_count=0,
        )
        db_session.add(user)
        await db_session.flush()

        # Cezalandır
        new_trust = await penalize_no_show(db_session, str(user.id))

        assert new_trust == 90
        assert user.trust_score == 90

    @pytest.mark.asyncio
    async def test_penalize_no_show_minimum_zero(self, db_session):
        """Trust_score minimum 0'a düşmeli, negatif olmamalı."""
        # Düşük trust_score'lu kullanıcı
        user = User(
            phone_number="+905554444444",
            full_name="Low Trust User",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            password_hash="hash",
            blood_type="AB+",
            role=UserRole.USER.value,
            trust_score=5,  # Düşük skor
            no_show_count=0,
        )
        db_session.add(user)
        await db_session.flush()

        # Cezalandır
        new_trust = await penalize_no_show(db_session, str(user.id))

        assert new_trust == 0  # 5 - 10 = -5, ama minimum 0
        assert user.trust_score == 0

    @pytest.mark.asyncio
    async def test_penalize_no_show_increments_count(self, db_session):
        """No-show count her cezada 1 artmalı."""
        # Kullanıcı oluştur
        user = User(
            phone_number="+905555555555",
            full_name="Repeat No Show",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            password_hash="hash",
            blood_type="A-",
            role=UserRole.USER.value,
            trust_score=100,
            no_show_count=2,  # Zaten 2 no-show var
        )
        db_session.add(user)
        await db_session.flush()

        # Cezalandır
        await penalize_no_show(db_session, str(user.id))

        assert user.no_show_count == 3


# =============================================================================
# get_user_rank Tests
# =============================================================================

class TestGetUserRank:
    """get_user_rank fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_get_user_rank(self, db_session):
        """Kullanıcının rank bilgileri doğru dönmeli."""
        # Birden fazla kullanıcı oluştur (leaderboard için)
        users = []
        for i, (points, name) in enumerate([
            (500, "Altin User"),
            (200, "Gumus User"),
            (50, "Bronz User"),
            (0, "Yeni User"),
        ]):
            user = User(
                phone_number=f"+90555666666{i}",
                full_name=name,
                date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                password_hash="hash",
                blood_type="O+",
                role=UserRole.USER.value,
                hero_points=points,
                trust_score=100,
                total_donations=points // 50,  # Yaklaşık bağış sayısı
                no_show_count=0,
            )
            db_session.add(user)
            users.append(user)

        await db_session.flush()

        # 3. kullanıcının (50 puan) rankını kontrol et
        rank_info = await get_user_rank(db_session, str(users[2].id))

        assert rank_info["hero_points"] == 50
        assert rank_info["rank_badge"] == "Bronz Kahraman"
        assert rank_info["trust_score"] == 100
        assert rank_info["global_rank"] == 3  # 2 kişi yukarıda (500, 200)


# =============================================================================
# get_leaderboard Tests
# =============================================================================

class TestGetLeaderboard:
    """get_leaderboard fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_get_leaderboard_ordering(self, db_session):
        """Leaderboard hero_points'e göre azalan sırada dönmeli."""
        # Yüksek puanlı kullanıcılar oluştur (seed data'dan daha yüksek)
        users_data = [
            (5000, "Platin User"),
            (3000, "Altin User"),
            (2000, "Gumus User"),
            (1000, "Bronz User"),
            (500, "Yeni User"),
        ]

        for i, (points, name) in enumerate(users_data):
            user = User(
                phone_number=f"+9055577777{i}",
                full_name=name,
                date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                password_hash="hash",
                blood_type="O+",
                role=UserRole.USER.value,
                hero_points=points,
                total_donations=points // 50,
            )
            db_session.add(user)

        await db_session.flush()

        # Leaderboard'ı al (limit 5)
        leaderboard = await get_leaderboard(db_session, limit=5)

        assert len(leaderboard) == 5
        # Sıralama kontrolü (azalan)
        assert leaderboard[0]["full_name"] == "Platin User"
        assert leaderboard[0]["hero_points"] == 5000
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[0]["rank_badge"] == "Platin Kahraman"

        assert leaderboard[4]["full_name"] == "Yeni User"
        assert leaderboard[4]["rank"] == 5

    @pytest.mark.asyncio
    async def test_get_leaderboard_limit(self, db_session):
        """Leaderboard limit parametresine göre dönmeli."""
        # Yüksek puanlı 15 kullanıcı oluştur (seed data'dan yüksek puanlar)
        for i in range(15):
            user = User(
                phone_number=f"+9055588888{i:02d}",
                full_name=f"User {i}",
                date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                password_hash="hash",
                blood_type="O+",
                role=UserRole.USER.value,
                hero_points=10000 + i * 10,  # Yüksek puanlar
            )
            db_session.add(user)

        await db_session.flush()

        # Limit 5 ile leaderboard'ı al
        leaderboard = await get_leaderboard(db_session, limit=5)

        assert len(leaderboard) == 5
        # En yüksek puanlı 5 kullanıcı (sıralı)
        points = [entry["hero_points"] for entry in leaderboard]
        assert points == sorted(points, reverse=True)