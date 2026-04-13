"""Tests for background timeout checker task."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.background.timeout_checker import (
    run_timeout_checker,
    stop_timeout_checker,
    TIMEOUT_CHECK_INTERVAL_MINUTES,
)


class TestTimeoutChecker:
    """Timeout checker background task testleri."""

    @pytest.mark.asyncio
    async def test_timeout_checker_runs_periodically(self):
        """Task'ın periyodik çalıştığını verify et."""
        # Arrange - Mock'ları hazırla
        call_count = 0

        async def mock_check_timeouts(db):
            nonlocal call_count
            call_count += 1
            return 0

        # Sleep'i hızlandırmak için kısalt
        original_sleep = asyncio.sleep
        sleep_calls = []

        async def fast_sleep(seconds):
            sleep_calls.append(seconds)
            if len(sleep_calls) >= 2:  # 2 döngü sonra durdur
                stop_timeout_checker()
            await original_sleep(0.01)  # Çok kısa bekleme

        with patch("app.background.timeout_checker.check_timeouts", side_effect=mock_check_timeouts):
            with patch("app.background.timeout_checker.AsyncSessionLocal") as mock_session_local:
                # Mock session context manager
                mock_session = AsyncMock()
                mock_session.commit = AsyncMock()
                mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

                with patch("asyncio.sleep", side_effect=fast_sleep):
                    # Act - Task'ı başlat
                    await run_timeout_checker()

        # Assert - En az 2 kez check_timeouts çağrıldı
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_timeout_checker_can_be_stopped(self):
        """stop_timeout_checker çalışıyor mu."""
        # Arrange
        from app.background import timeout_checker

        # Reset state
        timeout_checker.TASK_RUNNING = False

        # Act - Task'ı başlat ve durdur
        timeout_checker.TASK_RUNNING = True
        stop_timeout_checker()

        # Assert
        assert timeout_checker.TASK_RUNNING is False

    @pytest.mark.asyncio
    async def test_timeout_checker_handles_db_errors(self):
        """DB hatası durumunda continue ediyor mu."""
        # Arrange
        call_count = 0

        async def mock_check_timeouts_error(db):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Database connection error")
            return 0

        original_sleep = asyncio.sleep
        sleep_calls = []

        async def fast_sleep(seconds):
            sleep_calls.append(seconds)
            if len(sleep_calls) >= 2:
                stop_timeout_checker()
            await original_sleep(0.01)

        with patch("app.background.timeout_checker.check_timeouts", side_effect=mock_check_timeouts_error):
            with patch("app.background.timeout_checker.AsyncSessionLocal") as mock_session_local:
                mock_session = AsyncMock()
                mock_session.commit = AsyncMock()
                mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

                with patch("asyncio.sleep", side_effect=fast_sleep):
                    # Act
                    await run_timeout_checker()

        # Assert - Hata sonrası da devam etti
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_timeout_checker_logs_timeouts(self, caplog):
        """Timeout bulunduğunda log yazıyor mu."""
        import logging
        caplog.set_level(logging.INFO)

        async def mock_check_timeouts_with_timeouts(db):
            return 3  # 3 timeout bulundu

        sleep_count = 0

        async def stop_on_first_sleep(seconds):
            nonlocal sleep_count
            sleep_count += 1
            if sleep_count >= 1:
                stop_timeout_checker()
            return None  # Sleep yerine direkt dön

        with patch("app.background.timeout_checker.check_timeouts", side_effect=mock_check_timeouts_with_timeouts):
            with patch("app.background.timeout_checker.AsyncSessionLocal") as mock_session_local:
                mock_session = AsyncMock()
                mock_session.commit = AsyncMock()
                mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

                with patch("asyncio.sleep", side_effect=stop_on_first_sleep):
                    await run_timeout_checker()

        # Assert
        assert any("3 commitment(s) timed out" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_timeout_checker_interval_configuration(self):
        """Interval konfigürasyonu doğru mu."""
        # Assert
        assert TIMEOUT_CHECK_INTERVAL_MINUTES == 5

    # Not: check_timeouts fonksiyonunun DB entegrasyonu test_donations.py'de zaten test edildi
    # Bu dosya sadece background task runner'ı test eder