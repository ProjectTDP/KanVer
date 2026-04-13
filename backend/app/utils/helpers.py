"""
Helper utilities for KanVer API.

Bu dosya, genel yardımcı fonksiyonları içerir.
Request code generation, token generation ve telefon normalizasyonu.
"""
import secrets
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_phone(phone_number: str) -> str:
    """
    Telefon numarasını Türkiye standart formatina (+90...) normalize eder.

    Desteklenen input formatlari:
    - +905551234567 -> +905551234567 (degismez)
    - 05551234567 -> +905551234567
    - 5551234567 -> +905551234567
    - 905551234567 -> +905551234567 (90 prefix'i duzeltilir)

    Args:
        phone_number: Normalize edilecek telefon numarasi

    Returns:
        +90 ile baslayan 13 karakterlik Turk telefon numarasi

    Examples:
        >>> normalize_phone("+905551234567")
        '+905551234567'
        >>> normalize_phone("05551234567")
        '+905551234567'
        >>> normalize_phone("5551234567")
        '+905551234567'
        >>> normalize_phone("905551234567")
        '+905551234567'
    """
    phone = phone_number.strip().replace(" ", "")

    # Zaten +90 ile basliyorsa, oldugu gibi birak
    if phone.startswith("+90"):
        return phone

    # 90 ile basliyorsa (+ olmadan), + ekle
    if phone.startswith("90"):
        return "+90" + phone[2:]

    # 0 ile basliyorsa, 0'i +90 ile degistir
    if phone.startswith("0"):
        return "+90" + phone[1:]

    # Hiçbiri yoksa, basina +90 ekle
    return "+90" + phone


async def generate_request_code(db: AsyncSession) -> str:
    """
    Benzersiz kan talebi kodu üretir.

    Format: #KAN-XXX (örn: #KAN-001, #KAN-102)
    
    Veritabanı sequence'i kullanarak yarış durumlarını (race condition)
    uygulama katmanına bırakmadan önler.

    Args:
        db: Async database session

    Returns:
        str: Request code (örn: "#KAN-001")
    """
    result = await db.execute(text("SELECT nextval('blood_request_code_seq')"))
    next_number = int(result.scalar_one())

    # Format: #KAN-001 (3 digit zero-padded)
    return f"#KAN-{next_number:03d}"


def generate_unique_token(length: int = 32) -> str:
    """
    Güvenli rastgele token üretir.

    QR kod token'ları için kullanılır.
    secrets.token_urlsafe kullanarak kriptografik olarak güvenli token oluşturur.
    
    URL-safe base64 encoding kullanır: A-Z, a-z, 0-9, - ve _ karakterleri.
    Her karakter ~6 bit entropi sağlar (64 olası değer).

    Args:
        length: Token uzunluğu (byte cinsinden, default 32)
                Dönen string ~1.33x daha uzun olur (base64 encoding)

    Returns:
        str: URL-safe base64 encoded token (örn: "xPq3nR7s...")

    Examples:
        >>> token = generate_unique_token(32)
        >>> len(token) >= 32  # Base64 encoding nedeniyle daha uzun
        True
        >>> token2 = generate_unique_token(32)
        >>> token != token2  # Her seferinde farklı
        True
    """
    return secrets.token_urlsafe(length)
