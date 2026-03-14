"""
FCM (Firebase Cloud Messaging) utility module.

Bu modül, Firebase Cloud Messaging üzerinden push notification göndermek için
gerekli fonksiyonları içerir.
"""
import os
from typing import Optional, List, Dict, Any
import logging

from firebase_admin import initialize_app, messaging, App, credentials
from firebase_admin.exceptions import FirebaseError

from app.config import settings

logger = logging.getLogger(__name__)

# Firebase App instance (singleton)
_firebase_app: Optional[App] = None


def get_firebase_app() -> Optional[App]:
    """
    Firebase App instance'ı döner veya oluşturur.

    Returns:
        Firebase App instance veya None (credentials yoksa)
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    # Credentials dosyası var mı kontrol et
    cred_path = settings.FIREBASE_CREDENTIALS
    if not os.path.exists(cred_path):
        logger.warning(f"Firebase credentials not found at {cred_path}. Push notifications disabled.")
        return None

    try:
        cred = credentials.Certificate(cred_path)
        _firebase_app = initialize_app(cred)
        logger.info("Firebase app initialized successfully")
        return _firebase_app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase app: {e}")
        return None


def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> bool:
    """
    Tek bir cihaza push notification gönderir.

    Args:
        fcm_token: Hedef cihazın FCM token'ı
        title: Bildirim başlığı
        body: Bildirim içeriği
        data: Opsiyonel data payload

    Returns:
        Başarılı ise True, değilse False
    """
    app = get_firebase_app()
    if app is None:
        logger.debug("Firebase not initialized, skipping push notification")
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=fcm_token,
        )

        response = messaging.send(message, app=app)
        logger.info(f"Push notification sent successfully: {response}")
        return True

    except FirebaseError as e:
        # Invalid token, expired token, etc.
        logger.warning(f"Failed to send push notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending push notification: {e}")
        return False


def send_push_to_multiple(
    fcm_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    """
    Birden fazla cihaza push notification gönderir.

    Args:
        fcm_tokens: Hedef cihazların FCM token listesi
        title: Bildirim başlığı
        body: Bildirim içeriği
        data: Opsiyonel data payload

    Returns:
        {"success_count": int, "failure_count": int}
    """
    app = get_firebase_app()
    if app is None:
        logger.debug("Firebase not initialized, skipping push notification")
        return {"success_count": 0, "failure_count": len(fcm_tokens)}

    if not fcm_tokens:
        return {"success_count": 0, "failure_count": 0}

    try:
        # Her token için ayrı message oluştur
        messages = [
            messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )
            for token in fcm_tokens
        ]

        # Toplu gönderim
        response = messaging.send_each(messages, app=app)

        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
        }

    except Exception as e:
        logger.error(f"Error sending bulk push notifications: {e}")
        return {"success_count": 0, "failure_count": len(fcm_tokens)}


def reset_firebase_app() -> None:
    """
    Firebase app instance'ı sıfırlar.

    Bu fonksiyon sadece test amaçlı kullanılmalıdır.
    """
    global _firebase_app
    _firebase_app = None