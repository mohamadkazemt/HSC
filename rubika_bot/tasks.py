# rubika_bot/tasks.py

import logging
from typing import Any, Dict

from celery import shared_task

from .constants import LOG_CLEANUP_DAYS
from .models import WebhookLog
from .services import RubPyIntegrationService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_rubika_message(self, chat_id: str, text: str) -> None:
    """
    Sends a text message using the RubPy service. This task is designed to be
    called from synchronous parts of the app (e.g., signals, admin views).
    """
    try:
        # Get the singleton instance of the service within the task
        service = RubPyIntegrationService.get_instance()

        # The service method handles the sync/async wrapping internally
        service.send_text_message(chat_id, text)

        logger.info(
            "Task 'send_rubika_message' successfully sent message to %s.",
            chat_id,
        )

    except Exception as exc:
        logger.error(
            "Error in 'send_rubika_message' task for %s: %s",
            chat_id,
            exc,
            exc_info=True,
        )
        # Retry the task if an exception occurs
        raise self.retry(exc=exc)


@shared_task
def cleanup_webhook_logs() -> int:
    """Periodically cleans up old webhook logs."""
    deleted, _ = WebhookLog.cleanup_old_logs(days=LOG_CLEANUP_DAYS)
    logger.info("Cleaned up %s old webhook logs.", deleted)
    return deleted


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_webhook_task(self, payload: Dict[str, Any]) -> None:
    """
    Processes an incoming webhook payload in the background.
    """
    logger.info(
        "Task 'process_webhook_task' started for payload: %s",
        payload.get("update", {}).get("type"),
    )
    try:
        service = RubPyIntegrationService.get_instance()
        service.handle_webhook_payload(payload)
        logger.info("Task 'process_webhook_task' succeeded.")
    except Exception as exc:
        logger.error(
            "Error in 'process_webhook_task': %s",
            exc,
            exc_info=True,
        )
        raise self.retry(exc=exc)