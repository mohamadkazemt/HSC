# راهنمای نصب و استفاده از سرویس‌های HSC

## فایل‌های سرویس

چهار فایل سرویس systemd ایجاد شده است:

1. **celery-worker.service** - Worker اصلی برای اجرای تسک‌های Celery
2. **celery-beat.service** - Scheduler برای تسک‌های زمان‌بندی شده
3. **rubika-bot.service** - ربات روبیکا
4. **celery.service** - فایل قدیمی (می‌توانید حذف کنید)

## نصب سرویس‌ها

### روش 1: استفاده از اسکریپت خودکار

```bash
cd /var/www/HSC
sudo bash install_celery_services.sh
```

### روش 2: نصب دستی

```bash
# کپی فایل‌های سرویس
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/
sudo cp rubika-bot.service /etc/systemd/system/

# ایجاد دایرکتوری لاگ
sudo mkdir -p /var/www/HSC/logs
sudo chown hsc_admin:hsc_admin /var/www/HSC/logs

# فعال‌سازی سرویس‌ها
sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl enable celery-beat
sudo systemctl enable rubika-bot

# شروع سرویس‌ها
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl start rubika-bot
```

## مدیریت سرویس‌ها

### بررسی وضعیت

```bash
# وضعیت Worker
sudo systemctl status celery-worker

# وضعیت ربات روبیکا
sudo systemctl status rubika-bot

# بررسی همه سرویس‌ها
sudo systemctl status 'celery*' 'rubikabeat

# بررسی همه سرویس‌های Celery
sudo systemctl status 'celery*'
```

### مشاهده لاگ‌ها

```bash
# لاگ‌های Worker (به صورت زنده)
sudo journalctl -u celery-worker -f

# لاگ‌های ربات روبیکا (به صورت زنده)
sudo journalctl -u rubika-bot -f

# لاگ‌های امروز
sudo journalctl -u celery-worker --since today
sudo journalctl -u rubika-bot --since today

# 100 خط آخر لاگ
sudo journalctl -u celery-worker -n 100
sudo journalctl -u rubika-bot -n 100

# مشاهده همه لاگ‌ها با هم
sudo journalctl -u celery-worker -u celery-beat -u rubika-bot -fe today

# 100 خط آخر لاگ
sudo journalctl -u celery-worker -n 100

# لاگ فایل‌هاسرویس‌ها
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
sudo systemctl restart rubika-bot

# توقف سرویس‌ها
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat
sudo systemctl stop rubika-bot

# شروع سرویس‌ها
sudo systemctl start celery-worker
sudo systemctl start celery-beat
sudo systemctl start rubika-bot

# راه‌اندازی مجدد همه با هم
sudo systemctl restart celery-worker celery-beat rubika-boeat

# توقف
sudo systemctl stop celery-worker
sudo systemctl stop celery-beat

# شروع
sudo systemctl start celery-worker
sudo systemctl start celery-beat

# بارگذاری مجدد بدون قطع اتصال
sudo systemctl reload celery-worker
```

### غیرفعال‌سازی

```bash
# غیرفعال کردن (اجرا نمی‌شود در بوت)
sudo systemctl disable celery-worker
sudo systemctl disable celery-beat

# حذف سرویس
sudo systemctl stop celery-worker
sudo systemctl disable celery-worker
sudo rm /etc/systemd/system/celery-worker.service
sudo systemctl daemon-reload
```

## تنظیمات پیشرفته

### تغییر تعداد Worker ها

فایل `/etc/systemd/system/celery-worker.service` را ویرایش کنید:

```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --pool=prefork \
    --concurrency=16 \  # تغییر از 8 به 16
```

سپس:
```bash
sudo systemctl daemon-reload
sudo systemctl restart celery-worker
```

### تغییر سطح لاگ

گزینه‌ها: `debug`, `info`, `warning`, `error`, `critical`

```ini
--loglevel=debug \
```

### افزودن Queue خاص

```ini
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker \
    --pool=prefork \
    --concurrency=8 \
    --queues=celery,priority_queue \
    --loglevel=info
```

## 

### ربات روبیکا کار نمی‌کند

```bash
# بررسی خطاها
sudo journalctl -u rubika-bot -n 100

# تست دستی
cd /var/www/HSC
source venv/bin/activate
python manage.py run_rubika_bot

# بررسی تنظیمات ربات در Django Admin
# به /admin/rubika_bot/rubikabotsettings/ بروید
```عیب‌یابی

### Worker شروع نمی‌شود

```bash
# بررسی خطاها
sudo journalctl -u celery-worker -n 50

# تست دستی
cd /var/www/HSC
source venv/bin/activate
celery -A HSCprojects worker --loglevel=debug
```

### مشکل دسترسی به Redis

```bash
# بررسی وضعیت Redis
sudo systemctl status redis-server

# تست اتصال
redis-cli ping
```

### تسک‌ها اجرا نمی‌شوند

```bash
# بررسی تسک‌های در صف
cd /var/www/HSC
source venv/bin/activate
python manage.py shell

# در shell:
from celery import current_app
inspect = current_app.control.inspect()
print(inspect.active())
print(inspect.scheduled())
print(inspect.reserved())
```

### خطاهای Permission

```bash
# تنظیم مالکیت
sudo chown -R hsc_admin:hsc_admin /var/www/HSC
sudo chmod -R 755 /var/www/HSC

# بررسی کاربر سرویس
ps aux | grep celery
```

## مانیتورینگ

### Flower (رابط وب)

```bash
# نصب Flower
pip install flower

# اجرا
celery -A HSCprojects flower --port=5555

# دسترسی از مرورگر
http://your-server-ip:5555
```

### آمار Worker

```bash
celery -A HSCprojects inspect stats
celery -A HSCprojects inspect active
celery -A HSCprojects inspect registered
```

## Backup و Restore

### Backup تنظیمات Beat

```bash
# فایل‌های مهم:
/var/www/HSC/logs/celerybeat-schedule.db
/var/www/HSC/logs/celerybeat.pid

# Backup
sudo cp /var/www/HSC/logs/celerybeat-schedule.db /backup/
```

### Restore

```bash
sudo systemctl stop celery-beat
sudo cp /backup/celerybeat-schedule.db /var/www/HSC/logs/
sudo chown hsc_admin:hsc_admin /var/www/HSC/logs/celerybeat-schedule.db
sudo systemctl start celery-beat
```

## نکات امنیتی

1. **کاربر جداگانه**: سرویس با کاربر `hsc_admin` اجرا می‌شود (نه root)
2. **PrivateTmp**: دایرکتوری موقت ایزوله
3. **NoNewPrivileges**: جلوگیری از escalation
4. **محدودیت منابع**: تنظیم شده در فایل سرویس

## بهینه‌سازی عملکرد

### برای سرور قدرتمند

```ini
--concurrency=16 \
--max-tasks-per-child=500 \
```

### برای سرور ضعیف

```ini
--concurrency=4 \
--max-tasks-per-child=2000 \
```

### استفاده از Gevent (برای I/O بیشتر)

```ini
--pool=gevent \
--concurrency=200 \
```

## ارتقا و بروزرسانی

```bash
# توقف سرویس‌ها
sudo systemctl stop celery-worker celery-beat

# بروزرسانی کد
cd /var/www/HSC
git pull
source venv/bin/activate
pip install -r requirements.txt

# اجرای migrations
python manage.py migrate

# شروع مجدد
sudo systemctl start celery-worker celery-beat
```

## لینک‌های مفید

- [مستندات رسمی Celery](https://docs.celeryproject.org/)
- [راهنمای Systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#tips-and-best-practices)
