# راهنمای عیب‌یابی Celery

## مشکلات شناسایی شده

### 1. مشکل اصلی: Celery Worker به Redis متصل نیست

**علائم:**
- `celery inspect ping` خطای `Connection refused` می‌دهد
- Broker و Backend در Celery app برابر `None` هستند
- خطای `[Errno 111] Connection refused` در لاگ‌ها

**علت:**
تنظیمات Celery از Django لود نشده است. احتمالاً:
- `DJANGO_SETTINGS_MODULE` در service file درست تنظیم نشده
- یا Worker با تنظیمات اشتباه اجرا می‌شود

## راه‌حل‌ها

### مرحله 1: بررسی تنظیمات Service

```bash
# بررسی فایل service
cat /etc/systemd/system/celery-worker.service | grep -E "DJANGO_SETTINGS_MODULE|Environment"
```

باید این خط را ببینید:
```
Environment="DJANGO_SETTINGS_MODULE=HSCprojects.settings.production"
```

اگر نیست، باید اضافه کنید.

### مرحله 2: بررسی تنظیمات Django

```bash
cd /var/www/HSC
sudo -u hsc_admin venv/bin/python manage.py shell -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
import django
django.setup()
from django.conf import settings
print('CELERY_BROKER_URL:', getattr(settings, 'CELERY_BROKER_URL', 'NOT SET'))
print('CELERY_RESULT_BACKEND:', getattr(settings, 'CELERY_RESULT_BACKEND', 'NOT SET'))
"
```

باید ببینید:
```
CELERY_BROKER_URL: redis://localhost:6379/0
CELERY_RESULT_BACKEND: django-db
```

### مرحله 3: بررسی Celery App

```bash
cd /var/www/HSC
sudo -u hsc_admin venv/bin/python manage.py shell -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings.production')
import django
django.setup()
from HSCprojects.celery import app
print('Broker:', app.conf.broker_url)
print('Backend:', app.conf.result_backend)
"
```

اگر `None` است، مشکل از لود نشدن تنظیمات است.

### مرحله 4: راه‌اندازی مجدد Worker

```bash
sudo systemctl restart celery-worker celery-beat
sudo systemctl status celery-worker
```

### مرحله 5: تست اتصال

```bash
# تست Redis
redis-cli ping
# باید PONG برگرداند

# تست Celery
cd /var/www/HSC
sudo -u hsc_admin venv/bin/celery -A HSCprojects inspect ping
# باید pong از worker برگرداند
```

## مشکلات دیگر

### 2. باگ در اسکریپت تست

خطای `integer expression expected` در اسکریپت `test_celery_tasks.sh` اصلاح شد.

### 3. خطاهای لاگ Worker

9 خطا در لاگ Worker - باید بررسی شود:

```bash
sudo journalctl -u celery-worker --since "1 hour ago" | grep -i error
```

### 4. تسک‌های Fail شده

1479 تسک Fail شده در کل دیتابیس (اما در 24 ساعت گذشته هیچی نبوده) - این طبیعی است اگر قبلاً مشکلاتی بوده.

برای مشاهده:
```bash
sudo bash view_failed_tasks.sh
```

## دستورات مفید

### بررسی وضعیت
```bash
sudo bash test_celery_simple.sh
sudo bash check_celery_config.sh
```

### مشاهده لاگ‌ها
```bash
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-beat -f
```

### تست دستی
```bash
cd /var/www/HSC
sudo -u hsc_admin venv/bin/celery -A HSCprojects inspect ping
sudo -u hsc_admin venv/bin/celery -A HSCprojects inspect active
sudo -u hsc_admin venv/bin/celery -A HSCprojects inspect registered
```

## اگر مشکل حل نشد

1. بررسی کنید که Redis در حال اجرا است:
   ```bash
   sudo systemctl status redis-server
   ```

2. بررسی کنید که Worker در حال اجرا است:
   ```bash
   sudo systemctl status celery-worker
   ps aux | grep celery
   ```

3. بررسی لاگ‌های کامل:
   ```bash
   sudo journalctl -u celery-worker -n 100
   tail -100 /var/www/HSC/logs/celery-worker.log
   ```

4. تست اتصال Redis از Python:
   ```bash
   cd /var/www/HSC
   sudo -u hsc_admin venv/bin/python -c "
   import redis
   r = redis.Redis(host='localhost', port=6379, db=0)
   print(r.ping())
   "
   ```

