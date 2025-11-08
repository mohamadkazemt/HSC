from celery import shared_task
from .constants import LOG_CLEANUP_DAYS
from .models import WebhookLog
from .services import RubPyIntegrationService


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_rubika_message(self, chat_id: str, text: str) -> None:
    service = RubPyIntegrationService.get_instance()
    try:
        service.send_text_message(chat_id, text)
    except Exception as exc:  # pragma: no cover - retries exercised by Celery worker
        raise self.retry(exc=exc)


@shared_task
def cleanup_webhook_logs() -> int:
    deleted, _ = WebhookLog.cleanup_old_logs(days=LOG_CLEANUP_DAYS)
    return deleted