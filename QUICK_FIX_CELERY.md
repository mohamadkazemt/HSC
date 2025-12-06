# رفع سریع مشکل Celery Worker

## 🔴 مشکل

فایل systemd service شما از `-P gevent` استفاده می‌کند که با `aiohttp` سازگار نیست.

## ✅ راه‌حل سریع

### گام 1: کپی فایل جدید

فایل `celery.service` را در پروژه ایجاد شده است. آن را کپی کنید:

```bash
sudo cp /var/www/HSC/celery.service /etc/systemd/system/celery.service
```

یا دستی ویرایش کنید:

```bash
sudo nano /etc/systemd/system/celery.service
```

### گام 2: تغییرات لازم

**این خط را:**
```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker -P gevent -c 100 -l info
```

**به این تغییر دهید:**
```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --pool=prefork \
    --concurrency=8 \
    --loglevel=info \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid
```

**و این خط را اضافه کنید:**
```ini
Environment="PATH=/var/www/HSC/venv/bin"
ExecStop=/bin/kill -s TERM $MAINPID
```

### گام 3: ایجاد پوشه‌های لازم

```bash
# ایجاد پوشه لاگ
sudo mkdir -p /var/log/celery
sudo chown hsc_admin:hsc_admin /var/log/celery

# ایجاد پوشه pid
sudo mkdir -p /var/run/celery
sudo chown hsc_admin:hsc_admin /var/run/celery
```

### گام 4: Reload و Restart

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart celery
sudo systemctl restart celery.service

# بررسی وضعیت
sudo systemctl status celery.service
```

## 📝 فایل کامل (کپی کنید)

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
    --loglevel=info \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10s
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

## 🔑 تغییرات کلیدی

1. ✅ `-P gevent` → `--pool=prefork`
2. ✅ `-c 100` → `--concurrency=8` (برای سرور متوسط)
3. ✅ اضافه کردن `--logfile` و `--pidfile`
4. ✅ اضافه کردن `ExecStop` برای توقف صحیح
5. ✅ اضافه کردن `Environment="PATH=..."`

## ✅ تست

بعد از تغییر:

```bash
# بررسی وضعیت
sudo systemctl status celery.service

# بررسی لاگ‌ها
tail -f /var/log/celery/worker.log

# تست tasks
celery -A HSCprojects inspect active
```

## 🎯 تنظیم concurrency

بر اساس تعداد CPU cores:
- **2-4 cores**: `--concurrency=4`
- **4-8 cores**: `--concurrency=8` (پیشنهادی)
- **8+ cores**: `--concurrency=16`
