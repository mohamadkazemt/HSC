import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings')

app = Celery('meetings')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tehran',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    broker_connection_retry_on_startup=True,
    worker_pool_restarts=True,
    worker_concurrency=1,
    worker_pool='prefork',
) 