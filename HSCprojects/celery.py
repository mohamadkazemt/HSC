import os
import sys

try:
    from celery import Celery
    from celery.signals import task_postrun, task_prerun
    from django.db import close_old_connections, connections
except ImportError:
    # اگر makemigrations یا migrate اجرا می‌شود، celery اختیاری است
    if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
        Celery = None
    else:
        raise

# تنظیم متغیر محیطی برای تنظیمات جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings')

# ایجاد نمونه Celery
if Celery is not None:
    app = Celery('HSCprojects')
    
    # استفاده از تنظیمات جنگو برای Celery
    app.config_from_object('django.conf:settings', namespace='CELERY')
    
    # جستجوی خودکار تسک‌ها در تمام اپ‌های نصب شده
    app.autodiscover_tasks()

    @task_prerun.connect
    def _close_stale_connections_before_task(*args, **kwargs):
        """Do not carry a stale Django connection into the next task."""

        close_old_connections()

    @task_postrun.connect
    def _close_connections_after_task(*args, **kwargs):
        """Release the Celery worker-thread connection at task boundaries."""

        close_old_connections()
        connections.close_all()
    
    @app.task(bind=True)
    def debug_task(self):
        print(f'Request: {self.request!r}')
else:
    app = None
