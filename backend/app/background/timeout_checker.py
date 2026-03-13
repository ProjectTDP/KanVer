"""Background task for checking commitment timeouts."""
import asyncio

from app.config import settings
from app.core.logging import get_logger
from app.database import AsyncSessionLocal
from app.services.donation_service import check_timeouts

logger = get_logger(__name__)

# Configuration
TIMEOUT_CHECK_INTERVAL_MINUTES = 5  # Her 5 dakikada bir kontrol et
TASK_RUNNING = False  # Task durumunu takip et


async def run_timeout_checker():
    """
    Periyodik olarak timeout kontrolü yapar.

    FastAPI lifespan'da başlatılır.
    """
    global TASK_RUNNING
    TASK_RUNNING = True
    logger.info(f"Timeout checker started - checking every {TIMEOUT_CHECK_INTERVAL_MINUTES} minutes")

    while TASK_RUNNING:
        try:
            async with AsyncSessionLocal() as db:
                count = await check_timeouts(db)
                await db.commit()
                if count > 0:
                    logger.info(f"Timeout checker: {count} commitment(s) timed out")
        except Exception as e:
            logger.error(f"Timeout checker error: {e}")

        await asyncio.sleep(TIMEOUT_CHECK_INTERVAL_MINUTES * 60)


def stop_timeout_checker():
    """Task'ı durdur (shutdown için)."""
    global TASK_RUNNING
    TASK_RUNNING = False
    logger.info("Timeout checker stopped")