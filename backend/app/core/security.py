"""
Security modülü - Şifre hashing ve doğrulama.

Bu modül, bcrypt kullanarak şifre hashing ve doğrulama işlemlerini sağlar.
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Verilen plain text şifreyi bcrypt ile hash'ler.

    Args:
        password: Plain text şifre

    Returns:
        Bcrypt hashlenmiş şifre (string formatında)

    Examples:
        >>> hash_password("myPassword123")
        '$2b$12$abc...xyz'
    """
    # Password'u bytes'a çevir ve hash'le
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Plain text şifre ile hashlenmiş şifreyi karşılaştırır.

    Args:
        plain_password: Kullanıcının girdiği şifre
        hashed_password: Veritabanından gelen hash

    Returns:
        True if passwords match, False otherwise

    Examples:
        >>> hashed = hash_password("myPassword123")
        >>> verify_password("myPassword123", hashed)
        True
        >>> verify_password("wrongPassword", hashed)
        False
    """
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)
