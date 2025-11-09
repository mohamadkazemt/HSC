# rubika_bot/tasks.py

from celery import shared_task
from .constants import LOG_CLEANUP_DAYS
from .models import WebhookLog
from .services import RubPyIntegrationService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_rubika_message(self, chat_id: str, text: str) -> None:
    """Sends a simple text message via Rubika bot."""
    try:
        service = RubPyIntegrationService.get_instance()
        service.send_text_message(chat_id, text)
    except Exception as exc:
        logger.warning(f"Failed to send message to {chat_id}, retrying... Error: {exc}")
        raise self.retry(exc=exc)

@shared_task
def cleanup_webhook_logs() -> int:
    """Periodically cleans up old webhook logs."""
    deleted, _ = WebhookLog.cleanup_old_logs(days=LOG_CLEANUP_DAYS)
    logger.info(f"Cleaned up {deleted} old webhook logs.")
    return deleted

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_webhook_task(self, payload: Dict[str, Any]) -> None:
    """
    Processes an incoming webhook payload in the background using Celery.
    This avoids blocking the web server and resolves asyncio loop issues.
    """
    try:
        service = RubPyIntegrationService.get_instance()
        service.handle_webhook_payload(payload)
    except Exception as exc:
        logger.error(f"Error processing webhook payload: {exc}", exc_info=True)
        # We retry in case of temporary issues (e.g., DB connection)
        raise self.retry(exc=exc)