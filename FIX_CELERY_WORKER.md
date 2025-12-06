# رفع مشکل Celery Worker

## 🔴 مشکل

خطا: `RuntimeError: Timeout context manager should be used inside a task`

این خطا به این دلیل است که:
- Celery Worker با `-P gevent` (greenlet pool) اجرا می‌شود
- کد RubPy از `aiohttp` (async) استفاده می‌کند
- `gevent` با `aiohttp` سازگار نیست

## ✅ راه‌حل

### گام 1: ویرایش فایل systemd service

فایل `/etc/systemd/system/celery.service` را ویرایش کنید:

```bash
sudo nano /etc/systemd/system/celery.service
```

### گام 2: تغییر pool از gevent به prefork

**قبل (اشتباه):**
```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker -P gevent -c 100 -l info
```

**بعد (درست):**
```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker -P prefork -c 8 -l info
```

یا اگر می‌خواهید از threads استفاده کنید:

```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker -P threads -c 8 -l info
```

### گام 3: Reload و Restart

```bash
# Reload systemd
sudo systemctl daemon-reload

# Restart celery
sudo systemctl restart celery.service

# بررسی وضعیت
sudo systemctl status celery.service
```

## 📝 فایل کامل celery.service (پیشنهادی)

```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/HSC
Environment="PATH=/var/www/HSC/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=HSCprojects.settings.production"
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --pool=prefork \
    --concurrency=8 \
    --loglevel=info \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🔧 گزینه‌های Pool

### 1. prefork (پیشنهادی برای production)
- سازگار با async/await
- پایدار و قابل اعتماد
- استفاده از CPU cores
- **توصیه می‌شود**: `-P prefork -c 8`

### 2. threads
- سبک‌تر از prefork
- مناسب برای I/O-bound tasks
- **توصیه می‌شود**: `-P threads -c 8`

### 3. gevent (❌ استفاده نکنید)
- با aiohttp سازگار نیست
- فقط برای sync code

## 📊 تنظیمات پیشنهادی

### برای سرور کوچک (2-4 CPU cores):
```bash
celery -A HSCprojects worker -P prefork -c 4 -l info
```

### برای سرور متوسط (4-8 CPU cores):
```bash
celery -A HSCprojects worker -P prefork -c 8 -l info
```

### برای سرور بزرگ (8+ CPU cores):
```bash
celery -A HSCprojects worker -P prefork -c 16 -l info
```

## ✅ تست

بعد از تغییر، بررسی کنید:

```bash
# بررسی وضعیت
sudo systemctl status celery.service

# بررسی لاگ‌ها
tail -f /var/log/celery/worker.log

# تست tasks
celery -A HSCprojects inspect active
```

## 🎯 نکات مهم

1. **همیشه از prefork یا threads استفاده کنید** اگر از async code دارید
2. **concurrency را بر اساس CPU cores تنظیم کنید** (معمولاً 2x تعداد cores)
3. **لاگ‌ها را بررسی کنید** تا مطمئن شوید خطا برطرف شده است
