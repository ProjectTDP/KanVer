"""
Gamification Service for KanVer API.

Bu dosya, oyunlaştırma (gamification) ile ilgili business logic fonksiyonlarını içerir.
Hero points, trust score, rank badge ve leaderboard işlemleri.
"""
from typing import List, Dict, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.constants.status import RequestType
from app.config import settings


# Rank Badge Thresholds
RANK_BADGES = {
    (0, 49): "Yeni Kahraman",
    (50, 199): "Bronz Kahraman",
    (200, 499): "Gümüş Kahraman",
    (500, 999): "Altın Kahraman",
    (1000, float('inf')): "Platin Kahraman",
}


def get_rank_badge(hero_points: int) -> str:
    """
    Hero points'e göre rozet döner.

    Args:
        hero_points: Kullanıcının toplam hero points'i

    Returns:
        Rank badge ismi (örn: "Bronz Kahraman")
    """
    for (min_p, max_p), badge in RANK_BADGES.items():
        if min_p <= hero_points <= max_p:
            return badge
    return "Yeni Kahraman"


async def award_hero_points(
    db: AsyncSession,
    user_id: str,
    donation_type: str
) -> int:
    """
    Bağış türüne göre hero points verir.

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si
        donation_type: WHOLE_BLOOD veya APHERESIS

    Returns:
        Yeni toplam hero_points
    """
    # Kullanıcıyı getir
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return 0

    # Puanı hesapla
    if donation_type == RequestType.WHOLE_BLOOD.value:
        points = settings.HERO_POINTS_WHOLE_BLOOD  # 50
    else:
        points = settings.HERO_POINTS_APHERESIS    # 100

    # Ekle ve kaydet
    user.hero_points += points
    await db.flush()

    return user.hero_points


async def penalize_no_show(
    db: AsyncSession,
    user_id: str
) -> int:
    """
    No-show durumunda trust score düşürür ve no_show_count artırır.

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si

    Returns:
        Yeni trust_score (minimum 0)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return 0

    # no_show_count artır
    user.no_show_count = (user.no_show_count or 0) + 1

    # trust_score düşür (minimum 0)
    user.trust_score = max(0, user.trust_score + settings.NO_SHOW_PENALTY)  # -10

    await db.flush()
    return user.trust_score


async def get_user_rank(
    db: AsyncSession,
    user_id: str
) -> Dict:
    """
    Kullanıcının rank bilgilerini döner.

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si

    Returns:
        {
            "hero_points": int,
            "rank_badge": str,
            "trust_score": int,
            "total_donations": int,
            "no_show_count": int,
            "global_rank": int
        }
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return {}

    # Global sıralama hesapla (hero_points'e göre)
    rank_result = await db.execute(
        select(func.count()).select_from(User).where(
            User.hero_points > user.hero_points
        )
    )
    users_above = rank_result.scalar() or 0
    global_rank = users_above + 1

    return {
        "hero_points": user.hero_points,
        "rank_badge": get_rank_badge(user.hero_points),
        "trust_score": user.trust_score,
        "total_donations": user.total_donations,
        "no_show_count": user.no_show_count or 0,
        "global_rank": global_rank,
    }


async def get_leaderboard(
    db: AsyncSession,
    limit: int = 10
) -> List[Dict]:
    """
    Hero points'e göre top N kullanıcıyı döner.

    Args:
        db: AsyncSession
        limit: Maksimum kullanıcı sayısı

    Returns:
        [{"rank", "user_id", "full_name", "hero_points", "rank_badge", "total_donations"}, ...]
    """
    result = await db.execute(
        select(User)
        .where(User.deleted_at.is_(None))
        .order_by(desc(User.hero_points))
        .limit(limit)
    )
    users = list(result.scalars().all())

    leaderboard = []
    for idx, user in enumerate(users, start=1):
        leaderboard.append({
            "rank": idx,
            "user_id": str(user.id),
            "full_name": user.full_name,
            "hero_points": user.hero_points,
            "rank_badge": get_rank_badge(user.hero_points),
            "total_donations": user.total_donations,
        })

    return leaderboard