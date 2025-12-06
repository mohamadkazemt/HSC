# راهنمای راه‌اندازی Celery و Celery Beat

## 🔴 مشکلات رایج

### مشکل 1: `Resource temporarily unavailable: 'celerybeat-schedule'`

این خطا معمولاً به این دلایل رخ می‌دهد:
1. فایل `celerybeat-schedule` خراب شده است
2. یک instance دیگر از celery beat در حال اجرا است
3. فایل در حال استفاده است

### مشکل 2: `RuntimeError: Timeout context manager should be used inside a task`

این خطا به این دلیل است که:
- Celery Worker با `-P gevent` اجرا می‌شود
- کد از `aiohttp` (async) استفاده می‌کند
- `gevent` با `aiohttp` سازگار نیست

**راه‌حل**: تغییر pool از `gevent` به `prefork` یا `threads`

## ✅ راه‌حل

### گام 1: توقف تمام instance های Celery

```bash
# توقف celery beat
sudo systemctl stop celery-beat.service

# توقف celery worker
sudo systemctl stop celery.service

# بررسی اینکه آیا process دیگری در حال اجرا است
ps aux | grep celery

# اگر process پیدا شد، kill کنید
sudo pkill -f celery
```

### گام 2: حذف فایل schedule خراب

```bash
cd /var/www/HSC

# بکاپ از فایل (در صورت نیاز)
cp celerybeat-schedule celerybeat-schedule.backup

# حذف فایل
rm celerybeat-schedule

# یا اگر فایل lock وجود دارد
rm celerybeat-schedule.lock
```

### گام 3: راه‌اندازی مجدد

```bash
# راه‌اندازی celery worker
sudo systemctl start celery.service

# راه‌اندازی celery beat
sudo systemctl start celery-beat.service

# بررسی وضعیت
sudo systemctl status celery.service
sudo systemctl status celery-beat.service
```

## 🔧 راه‌اندازی دستی (برای تست)

اگر می‌خواهید دستی تست کنید:

### Terminal 1: Celery Worker
```bash
cd /var/www/HSC
source venv/bin/activate
celery -A HSCprojects worker -l info
```

### Terminal 2: Celery Beat
```bash
cd /var/www/HSC
source venv/bin/activate
celery -A HSCprojects beat -l info
```

## 📝 تنظیمات Systemd Service

### فایل `/etc/systemd/system/celery.service`:

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

**⚠️ مهم**: از `--pool=prefork` استفاده کنید، نه `-P gevent` (چون با aiohttp سازگار نیست)

### فایل `/etc/systemd/system/celery-beat.service`:

```ini
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/HSC
Environment="PATH=/var/www/HSC/venv/bin"
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects beat \
    --loglevel=info \
    --schedule=/var/www/HSC/celerybeat-schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

### فایل `/etc/default/celery`:

```bash
CELERYD_NODES="worker1"
CELERYD_OPTS="--time-limit=300 --concurrency=8"
CELERYD_CHDIR="/var/www/HSC"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_USER="www-data"
CELERYD_GROUP="www-data"
CELERY_CREATE_DIRS=1
```

## 🔄 راه‌اندازی مجدد

```bash
# Reload systemd
sudo systemctl daemon-reload

# فعال کردن سرویس‌ها
sudo systemctl enable celery.service
sudo systemctl enable celery-beat.service

# راه‌اندازی
sudo systemctl start celery.service
sudo systemctl start celery-beat.service

# بررسی وضعیت
sudo systemctl status celery.service
sudo systemctl status celery-beat.service
```

## 🐛 عیب‌یابی

### مشکل: فایل schedule هنوز قفل است

```bash
# پیدا کردن process که فایل را قفل کرده
lsof | grep celerybeat-schedule

# kill کردن process
sudo kill -9 <PID>
```

### مشکل: Permission denied

```bash
# تغییر مالکیت
sudo chown -R www-data:www-data /var/www/HSC
sudo chmod -R 755 /var/www/HSC
```

### مشکل: RabbitMQ در دسترس نیست

```bash
# بررسی وضعیت RabbitMQ
sudo systemctl status rabbitmq-server

# راه‌اندازی RabbitMQ
sudo systemctl start rabbitmq-server
```

## 📊 بررسی لاگ‌ها

```bash
# لاگ Celery Worker
tail -f /var/log/celery/worker1.log

# لاگ Celery Beat
journalctl -u celery-beat.service -f

# یا
tail -f /var/log/celery/beat.log
```

## ✅ تست

```bash
# تست اتصال
celery -A HSCprojects inspect active

# تست tasks
celery -A HSCprojects inspect registered
```

## 🎯 نکات مهم

1. **همیشه ابتدا worker را راه‌اندازی کنید**، سپس beat
2. **فایل schedule را در git ignore قرار دهید**
3. **از systemd برای production استفاده کنید**
4. **لاگ‌ها را به طور منظم بررسی کنید**
