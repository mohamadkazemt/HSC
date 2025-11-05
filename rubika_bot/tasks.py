from celery import shared_task
from .services import RubikaClient


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_rubika_message(self, chat_id: str, text: str):
    client = RubikaClient()
    try:
        client.send_message(chat_id, text)
    except Exception as exc:
        raise self.retry(exc=exc)