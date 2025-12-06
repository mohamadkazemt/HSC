# عیب‌یابی خطای Celery Worker

## 🔴 مشکل

Celery Worker با خطا restart می‌شود: `exit-code, status=1/FAILURE`

## ✅ گام‌های عیب‌یابی

### گام 1: بررسی لاگ‌های systemd

```bash
# بررسی لاگ‌های systemd
sudo journalctl -u celery.service -n 50 --no-pager

# یا
sudo journalctl -u celery.service -f
```

### گام 2: بررسی لاگ‌های Celery

```bash
# اگر فایل لاگ وجود دارد
tail -f /var/log/celery/worker.log

# یا بررسی خطاهای اخیر
sudo journalctl -u celery.service --since "5 minutes ago" | tail -50
```

### گام 3: تست دستی اجرا

```bash
cd /var/www/HSC
source venv/bin/activate

# تست دستی اجرا (برای دیدن خطا)
celery -A HSCprojects worker --pool=prefork --concurrency=8 -l info
```

## 🔧 مشکلات احتمالی و راه‌حل

### مشکل 1: Permission denied برای لاگ یا pid file

```bash
# ایجاد پوشه‌ها با permission صحیح
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown -R hsc_admin:hsc_admin /var/log/celery /var/run/celery
sudo chmod -R 755 /var/log/celery /var/run/celery
```

### مشکل 2: مسیر venv اشتباه است

```bash
# بررسی مسیر venv
ls -la /var/www/HSC/venv/bin/celery

# اگر وجود ندارد، مسیر صحیح را پیدا کنید
which celery
```

### مشکل 3: Django settings module اشتباه است

```bash
# تست import settings
cd /var/www/HSC
source venv/bin/activate
python manage.py check --settings=HSCprojects.settings.production
```

### مشکل 4: Redis در دسترس نیست

```bash
# بررسی Redis
sudo systemctl status redis-server

# یا
redis-cli ping
```

## 📝 فایل service اصلاح شده (بدون logfile و pidfile برای تست)

اگر مشکل از logfile یا pidfile است، ابتدا بدون آنها تست کنید:

```ini
[Unit]
Description=Celery Worker Service
After=network.target redis-server.service

[Service]
Type=simple
User=hsc_admin
Group=hsc_admin
WorkingDirectory=/var/www/HSC
Environment="DJANGO_SETTINGS_MODULE=HSCprojects.settings.production"
Environment="PATH=/var/www/HSC/venv/bin"
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --pool=prefork \
    --concurrency=8 \
    --loglevel=info
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10s
KillMode=mixed
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**توجه**: `StandardOutput=journal` و `StandardError=journal` اضافه شده تا لاگ‌ها در journalctl نمایش داده شوند.

## 🔍 دستورات عیب‌یابی

```bash
# 1. بررسی لاگ‌های systemd
sudo journalctl -u celery.service -n 100 --no-pager

# 2. تست دستی
cd /var/www/HSC
source venv/bin/activate
celery -A HSCprojects worker --pool=prefork --concurrency=2 -l debug

# 3. بررسی permission
ls -la /var/log/celery /var/run/celery

# 4. بررسی Redis
redis-cli ping

# 5. بررسی Django
python manage.py check --settings=HSCprojects.settings.production
```

## ✅ بعد از پیدا کردن مشکل

بعد از پیدا کردن خطا از لاگ‌ها، فایل service را اصلاح کنید و:

```bash
sudo systemctl daemon-reload
sudo systemctl restart celery.service
sudo systemctl status celery.service
```
