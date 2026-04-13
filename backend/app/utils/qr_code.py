"""QR Code utility for secure donation verification.

Bu modül, bağışçı hastaneye vardığında (ARRIVED status) oluşturulan
güvenli QR kod sistemi için gerekli fonksiyonları içerir.

Güvenlik Özellikleri:
- Kriptografik olarak güvenli token (secrets.token_urlsafe)
- HMAC-SHA256 imza ile bütünlük kontrolü
- Timing attack koruması (hmac.compare_digest)
- 2 saat geçerlilik süresi
- Tek kullanımlık (is_used flag)
"""

import secrets
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import QRCode, DonationCommitment
from app.constants import CommitmentStatus
from app.core.exceptions import NotFoundException, BadRequestException


# QR kod geçerlilik süresi (saat)
QR_CODE_EXPIRY_HOURS = 2


def generate_qr_token() -> str:
    """
    Kriptografik olarak güvenli token üretir.

    Returns:
        43 karakterlik URL-safe token (secrets.token_urlsafe(32))
        32 byte = 256-bit entropy
    """
    return secrets.token_urlsafe(32)


def generate_signature(token: str, commitment_id: str) -> str:
    """
    HMAC-SHA256 imza oluşturur.

    İmza, token ve commitment_id'yi birleştirerek oluşturulur.
    Bu sayede token başka bir commitment ile kullanılamaz.

    Args:
        token: QR token
        commitment_id: Taahhüt ID

    Returns:
        Hex-encoded signature (64 karakter)
    """
    message = f"{token}:{commitment_id}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(token: str, commitment_id: str, signature: str) -> bool:
    """
    İmza doğrulaması yapar (timing attack korumalı).

    hmac.compare_digest kullanarak timing attack'lere karşı koruma sağlar.
    Normal == operatörü, karşılaştırma süresine göre bilgi sızdırabilir.

    Args:
        token: QR token
        commitment_id: Taahhüt ID
        signature: Doğrulanacak imza

    Returns:
        True if valid, False otherwise
    """
    expected = generate_signature(token, commitment_id)
    return hmac.compare_digest(signature, expected)


def create_qr_data(commitment_id: str) -> dict:
    """
    QR kod verisi oluşturur.

    Args:
        commitment_id: Taahhüt ID

    Returns:
        {token, signature, expires_at} dict'i
    """
    token = generate_qr_token()
    signature = generate_signature(token, commitment_id)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=QR_CODE_EXPIRY_HOURS)

    return {
        "token": token,
        "signature": signature,
        "expires_at": expires_at
    }


async def validate_qr(db: AsyncSession, token: str) -> QRCode:
    """
    QR kodunu doğrular.

    Sırasıyla şu kontrolleri yapar:
    1. Token veritabanında var mı?
    2. Süresi dolmuş mu?
    3. Daha önce kullanılmış mı?
    4. İmza geçerli mi?

    Args:
        db: AsyncSession
        token: QR token

    Returns:
        QRCode objesi

    Raises:
        NotFoundException: QR kod bulunamadı
        BadRequestException: QR kod geçersiz (expired, used, invalid signature)
    """
    # Token'ı bul
    result = await db.execute(
        select(QRCode).where(QRCode.token == token)
    )
    qr_code = result.scalar_one_or_none()

    if not qr_code:
        raise NotFoundException("QR kod bulunamadı")

    # Expire kontrolü
    if qr_code.expires_at < datetime.now(timezone.utc):
        raise BadRequestException("QR kodun süresi dolmuş")

    # is_used kontrolü
    if qr_code.is_used:
        raise BadRequestException("QR kod zaten kullanılmış")

    # Signature doğrula
    if not verify_signature(qr_code.token, qr_code.commitment_id, qr_code.signature):
        raise BadRequestException("QR kod imzası geçersiz")

    return qr_code


def format_qr_content(token: str, commitment_id: str, signature: str) -> str:
    """
    Frontend için QR içerik formatı.

    QR kod içeriği bu formatta encode edilir.
    Frontend bu string'i QR kod olarak gösterebilir.

    Format: {token}:{commitment_id}:{signature}

    Args:
        token: QR token
        commitment_id: Taahhüt ID
        signature: İmza

    Returns:
        QR içerik string'i
    """
    return f"{token}:{commitment_id}:{signature}"


def parse_qr_content(content: str) -> Optional[dict]:
    """
    QR kod içeriğini parse eder.

    Args:
        content: QR kod içeriği (format: token:commitment_id:signature)

    Returns:
        {token, commitment_id, signature} dict'i veya None (geçersiz format)
    """
    parts = content.split(":")
    if len(parts) != 3:
        return None

    token, commitment_id, signature = parts
    return {
        "token": token,
        "commitment_id": commitment_id,
        "signature": signature
    }