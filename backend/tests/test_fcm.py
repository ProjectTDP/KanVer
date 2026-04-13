"""
FCM (Firebase Cloud Messaging) utility tests.

Bu dosya, FCM push notification fonksiyonlarını test eder.
"""
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from app.utils.fcm import (
    get_firebase_app,
    send_push_notification,
    send_push_to_multiple,
    reset_firebase_app,
)
from app.services.notification_service import create_notification


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_firebase():
    """Her testten önce Firebase app'i sıfırla."""
    reset_firebase_app()
    yield
    reset_firebase_app()


# =============================================================================
# TESTS
# =============================================================================

class TestSendPushNotification:
    """send_push_notification fonksiyonu testleri."""

    @patch("app.utils.fcm.os.path.exists")
    @patch("app.utils.fcm.credentials.Certificate")
    @patch("app.utils.fcm.initialize_app")
    @patch("app.utils.fcm.messaging.send")
    def test_send_push_notification_success(
        self,
        mock_send,
        mock_init_app,
        mock_cert,
        mock_exists
    ):
        """Firebase mock ile başarılı gönderim."""
        # Arrange
        mock_exists.return_value = True
        mock_app = MagicMock()
        mock_init_app.return_value = mock_app
        mock_send.return_value = "message_id_123"

        # Act
        result = send_push_notification(
            fcm_token="test_token_123",
            title="Test Başlık",
            body="Test mesaj içeriği"
        )

        # Assert
        assert result is True
        mock_send.assert_called_once()

    @patch("app.utils.fcm.os.path.exists")
    @patch("app.utils.fcm.credentials.Certificate")
    @patch("app.utils.fcm.initialize_app")
    @patch("app.utils.fcm.messaging.send")
    def test_send_push_invalid_token_handled(
        self,
        mock_send,
        mock_init_app,
        mock_cert,
        mock_exists
    ):
        """Invalid token hatası yakalanmalı."""
        # Arrange
        from firebase_admin.exceptions import FirebaseError

        mock_exists.return_value = True
        mock_app = MagicMock()
        mock_init_app.return_value = mock_app

        # Simulate FirebaseError for invalid token
        mock_send.side_effect = FirebaseError(
            code="invalid-registration-token",
            message="Invalid registration token"
        )

        # Act
        result = send_push_notification(
            fcm_token="invalid_token",
            title="Test",
            body="Test"
        )

        # Assert - Should return False, not raise
        assert result is False

    def test_graceful_skip_without_credentials(self):
        """Credentials yoksa graceful skip."""
        # Act - settings.FIREBASE_CREDENTIALS points to non-existent file
        result = send_push_notification(
            fcm_token="test_token",
            title="Test",
            body="Test"
        )

        # Assert - Should return False without crashing
        assert result is False


class TestSendPushToMultiple:
    """send_push_to_multiple fonksiyonu testleri."""

    @patch("app.utils.fcm.os.path.exists")
    @patch("app.utils.fcm.credentials.Certificate")
    @patch("app.utils.fcm.initialize_app")
    @patch("app.utils.fcm.messaging.send_each")
    def test_send_push_to_multiple_tokens(
        self,
        mock_send_each,
        mock_init_app,
        mock_cert,
        mock_exists
    ):
        """Toplu gönderim."""
        # Arrange
        mock_exists.return_value = True
        mock_app = MagicMock()
        mock_init_app.return_value = mock_app

        mock_response = MagicMock()
        mock_response.success_count = 3
        mock_response.failure_count = 0
        mock_send_each.return_value = mock_response

        # Act
        result = send_push_to_multiple(
            fcm_tokens=["token1", "token2", "token3"],
            title="Test",
            body="Test"
        )

        # Assert
        assert result["success_count"] == 3
        assert result["failure_count"] == 0
        mock_send_each.assert_called_once()

    @patch("app.utils.fcm.os.path.exists")
    @patch("app.utils.fcm.credentials.Certificate")
    @patch("app.utils.fcm.initialize_app")
    @patch("app.utils.fcm.messaging.send_each")
    def test_send_push_partial_failure_report(
        self,
        mock_send_each,
        mock_init_app,
        mock_cert,
        mock_exists
    ):
        """Kısmi başarısızlık raporu."""
        # Arrange
        mock_exists.return_value = True
        mock_app = MagicMock()
        mock_init_app.return_value = mock_app

        mock_response = MagicMock()
        mock_response.success_count = 2
        mock_response.failure_count = 1
        mock_send_each.return_value = mock_response

        # Act
        result = send_push_to_multiple(
            fcm_tokens=["token1", "token2", "invalid_token"],
            title="Test",
            body="Test"
        )

        # Assert
        assert result["success_count"] == 2
        assert result["failure_count"] == 1

    def test_send_push_empty_token_list(self):
        """Boş token listesi."""
        # Act
        result = send_push_to_multiple(
            fcm_tokens=[],
            title="Test",
            body="Test"
        )

        # Assert
        assert result["success_count"] == 0
        assert result["failure_count"] == 0


class TestFirebaseAppSingleton:
    """Firebase app singleton pattern testleri."""

    @patch("app.utils.fcm.os.path.exists")
    @patch("app.utils.fcm.credentials.Certificate")
    @patch("app.utils.fcm.initialize_app")
    def test_firebase_app_singleton(
        self,
        mock_init_app,
        mock_cert,
        mock_exists
    ):
        """Singleton pattern - sadece bir kez initialize edilmeli."""
        # Arrange
        mock_exists.return_value = True
        mock_app = MagicMock()
        mock_init_app.return_value = mock_app

        # Act - Call get_firebase_app multiple times
        app1 = get_firebase_app()
        app2 = get_firebase_app()
        app3 = get_firebase_app()

        # Assert - initialize_app should only be called once
        assert app1 is app2
        assert app2 is app3
        mock_init_app.assert_called_once()


class TestNotificationWithPush:
    """Notification service FCM entegrasyon testleri."""

    @pytest.mark.asyncio
    @patch("app.utils.fcm.send_push_notification")
    async def test_notification_with_push_updates_flags(
        self,
        mock_send_push,
        db_session,
        test_user
    ):
        """is_push_sent güncellenmeli."""
        # Arrange
        mock_send_push.return_value = True

        # Act
        notification = await create_notification(
            db=db_session,
            user_id=test_user.id,
            notification_type="NEW_REQUEST",
            context={
                "blood_type": "A+",
                "hospital_name": "Test Hastanesi",
                "request_code": "KAN-001"
            },
            fcm_token="test_fcm_token_123"
        )

        # Assert
        assert notification.is_push_sent is True
        assert notification.push_sent_at is not None
        mock_send_push.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.utils.fcm.send_push_notification")
    async def test_notification_without_token_no_push(
        self,
        mock_send_push,
        db_session,
        test_user
    ):
        """FCM token yoksa push gönderilmemeli."""
        # Act
        notification = await create_notification(
            db=db_session,
            user_id=test_user.id,
            notification_type="NEW_REQUEST",
            context={
                "blood_type": "A+",
                "hospital_name": "Test Hastanesi",
                "request_code": "KAN-002"
            },
            fcm_token=None
        )

        # Assert
        assert notification.is_push_sent is False
        assert notification.push_sent_at is None
        mock_send_push.assert_not_called()