# راهنمای راه‌اندازی Celery در سرور

## مشکل فعلی
ربات روبیکا خطای 500 می‌دهد چون:
- Webhook به درستی دریافت می‌شود
- Task به صف Redis اضافه می‌شود
- **اما Celery Worker اجرا نشده و task ها پردازش نمی‌شوند**

## بررسی وضعیت

### 1. بررسی Redis
```bash
# بررسی اینکه Redis در حال اجرا است
sudo systemctl status redis

# اگر نصب نیست، نصب کنید
sudo apt-get update
sudo apt-get install redis-server

# راه‌اندازی Redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 2. بررسی Celery Worker
```bash
# بررسی وضعیت Celery Worker
sudo systemctl status celery-worker

# یا بررسی دستی
ps aux | grep celery
```

---

## راه‌اندازی Celery Worker

### روش 1: استفاده از systemd (توصیه می‌شود)

#### ایجاد فایل سرویس Celery Worker

**فایل: `/etc/systemd/system/celery-worker.service`**

```ini
[Unit]
Description=Celery Worker for HSC Project
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/HSC
Environment="DJANGO_SETTINGS_MODULE=HSCprojects.settings.production"
Environment="DJANGO_ALLOW_ASYNC_UNSAFE=true"
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --loglevel=info \
    --logfile=/var/www/HSC/logs/celery-worker.log \
    --pidfile=/var/run/celery/worker.pid \
    --concurrency=4 \
    --detach

ExecStop=/var/www/HSC/venv/bin/celery -A HSCprojects control shutdown
ExecReload=/bin/kill -s HUP $MAINPID

# دایرکتوری برای PID file
RuntimeDirectory=celery
RuntimeDirectoryMode=0755

# Restart policy
Restart=always
RestartSec=10s

# محدودیت‌های امنیتی
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

#### ایجاد فایل سرویس Celery Beat

**فایل: `/etc/systemd/system/celery-beat.service`**

```ini
[Unit]
Description=Celery Beat Scheduler for HSC Project
After=network.target redis.service celery-worker.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/HSC
Environment="DJANGO_SETTINGS_MODULE=HSCprojects.settings.production"
Environment="DJANGO_ALLOW_ASYNC_UNSAFE=true"
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects beat \
    --loglevel=info \
    --logfile=/var/www/HSC/logs/celery-beat.log \
    --pidfile=/var/run/celery/beat.pid \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

# دایرکتوری برای PID file
RuntimeDirectory=celery
RuntimeDirectoryMode=0755

# Restart policy
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

#### دستورات راه‌اندازی

```bash
# ایجاد دایرکتوری لاگ اگر وجود ندارد
sudo mkdir -p /var/www/HSC/logs
sudo chown www-data:www-data /var/www/HSC/logs

# ایجاد دایرکتوری برای PID files
sudo mkdir -p /var/run/celery
sudo chown www-data:www-data /var/run/celery

# بارگذاری مجدد systemd
sudo systemctl daemon-reload

# فعال‌سازی سرویس‌ها
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat

# راه‌اندازی سرویس‌ها
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# بررسی وضعیت
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

---

### روش 2: راه‌اندازی دستی (برای تست)

```bash
# فعال‌سازی محیط مجازی
cd /var/www/HSC
source venv/bin/activate

# راه‌اندازی Worker
celery -A HSCprojects worker --loglevel=info --concurrency=4

# در ترمینال دیگر، راه‌اندازی Beat
celery -A HSCprojects beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## بررسی و عیب‌یابی

### 1. بررسی لاگ‌های Celery

```bash
# لاگ Worker
sudo tail -f /var/www/HSC/logs/celery-worker.log

# لاگ Beat
sudo tail -f /var/www/HSC/logs/celery-beat.log

# لاگ systemd
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-beat -f
```

### 2. بررسی اتصال به Redis

```bash
# تست اتصال به Redis
redis-cli ping
# باید "PONG" برگرداند

# بررسی task های در صف
redis-cli
> KEYS celery*
> LLEN celery
```

### 3. تست ارسال Task

در shell Django:

```python
python manage.py shell

from rubika_bot.tasks import send_rubika_message

# ارسال task تستی
result = send_rubika_message.delay("test_chat_id", "تست پیام")
print(result.id)
```

### 4. مانیتورینگ Celery

```bash
# نمایش worker های فعال
celery -A HSCprojects inspect active

# نمایش task های ثبت شده
celery -A HSCprojects inspect registered

# نمایش آمار
celery -A HSCprojects inspect stats
```

---

## مشکلات رایج و راه‌حل‌ها

### خطا: "Cannot connect to redis"

```bash
# بررسی Redis
sudo systemctl status redis

# اگر خاموش است
sudo systemctl start redis

# بررسی پورت
sudo netstat -tulpn | grep 6379
```

### خطا: "Permission denied"

```bash
# تنظیم مجوزها
sudo chown -R www-data:www-data /var/www/HSC
sudo chown -R www-data:www-data /var/run/celery
```

### خطا: "Module not found"

```bash
# نصب مجدد وابستگی‌ها در محیط مجازی
cd /var/www/HSC
source venv/bin/activate
pip install -r requirements.txt
```

### Worker اجرا می‌شود اما Task پردازش نمی‌شود

```bash
# بررسی اینکه Worker task ها را می‌بیند
celery -A HSCprojects inspect registered

# بررسی صف
redis-cli
> LLEN celery
> LPOP celery
```

---

## راه‌حل موقت (اگر Celery مشکل دارد)

اگر نمی‌خواهید Celery راه‌اندازی کنید، می‌توانید webhook را به صورت همگام پردازش کنید:

**فایل: `rubika_bot/views.py`**

تغییر از:
```python
process_webhook_task.delay(payload)
return JsonResponse({'ok': True, 'status': 'queued'})
```

به:
```python
# پردازش همگام (بدون Celery)
from .services import RubPyIntegrationService

try:
    service = RubPyIntegrationService.get_instance()
    service.handle_webhook_payload(payload)
    return JsonResponse({'ok': True, 'status': 'processed'})
except Exception as exc:
    logger.error(f"Webhook processing error: {exc}", exc_info=True)
    return JsonResponse({'ok': False, 'error': str(exc)}, status=500)
```

**⚠️ توجه:** این راه‌حل برای ترافیک کم مناسب است. برای تعداد زیاد پیام، حتماً Celery را راه‌اندازی کنید.

---

## تست نهایی

بعد از راه‌اندازی Celery:

1. **بررسی Worker:**
```bash
sudo systemctl status celery-worker
```

2. **ارسال پیام تست به ربات روبیکا**

3. **بررسی لاگ‌ها:**
```bash
# لاگ Celery
tail -f /var/www/HSC/logs/celery-worker.log

# لاگ Gunicorn
sudo journalctl -u gunicorn -f

# لاگ Django
tail -f /var/www/HSC/logs/application.log
```

4. **بررسی WebhookLog در Admin Panel**

---

## چک‌لیست راه‌اندازی

- [ ] Redis نصب و اجرا شده است
- [ ] فایل `celery-worker.service` ایجاد شده
- [ ] فایل `celery-beat.service` ایجاد شده
- [ ] دایرکتوری `/var/run/celery` با مجوزهای صحیح ایجاد شده
- [ ] دایرکتوری `/var/www/HSC/logs` با مجوزهای صحیح ایجاد شده
- [ ] سرویس‌های Celery فعال و اجرا شده‌اند
- [ ] تست ارسال پیام به ربات موفقیت‌آمیز بوده است
- [ ] لاگ‌ها خطایی نشان نمی‌دهند

---

## منابع بیشتر

- [مستندات Celery](https://docs.celeryproject.org/)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
