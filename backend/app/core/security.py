"""
Security modülü - Şifre hashing ve doğrulama.

Bu modül, doğrudan bcrypt kütüphanesini kullanarak şifre hashing 
ve doğrulama işlemlerini sağlar. Passlib/CryptContext yerine 
performans ve stabilite nedeniyle saf bcrypt tercih edilmiştir.
"""
import re
import bcrypt


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """
    Şifre gücünü doğrular.

    Kurallar:
    - Minimum 8 karakter
    - En az 1 küçük harf
    - En az 1 büyük harf
    - En az 1 rakam

    Args:
        password: Doğrulanacak şifre

    Returns:
        (is_valid, error_message) tuple'u
    """
    if not password:
        return False, "Şifre boş olamaz"

    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalı"

    if not re.search(r"[a-z]", password):
        return False, "Şifre en az bir küçük harf içermeli"

    if not re.search(r"[A-Z]", password):
        return False, "Şifre en az bir büyük harf içermeli"

    if not re.search(r"\d", password):
        return False, "Şifre en az bir rakam içermeli"

    return True, None


def hash_password(password: str) -> str:
    """
    Verilen plain text şifreyi saf bcrypt ile hash'ler.

    Args:
        password: Plain text şifre

    Returns:
        Hashlenmiş şifre (string formatında)
    """
    # Bcrypt 72 byte limitini aşmamak için truncate yapıyoruz.
    pwd_bytes = password[:72].encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Plain text şifre ile hashlenmiş şifreyi karşılaştırır.

    Args:
        plain_password: Kullanıcının girdiği şifre
        hashed_password: Veritabanından gelen hash

    Returns:
        True if passwords match, False otherwise
    """
    try:
        pwd_bytes = plain_password[:72].encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False
