import os
from celery import Celery

# تنظیم متغیر محیطی برای تنظیمات جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings')

# ایجاد نمونه Celery
app = Celery('HSCprojects')

# استفاده از تنظیمات جنگو برای Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# جستجوی خودکار تسک‌ها در تمام اپ‌های نصب شده
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 