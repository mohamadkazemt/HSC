import os

# اجازه اجرای عملیات همگام جنگو در محیطی که حلقه asyncio فعال است (کلاینت RubPy)
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

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