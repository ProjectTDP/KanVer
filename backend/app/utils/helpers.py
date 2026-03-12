"""
Helper utilities for KanVer API.

Bu dosya, genel yardımcı fonksiyonları içerir.
"""


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
