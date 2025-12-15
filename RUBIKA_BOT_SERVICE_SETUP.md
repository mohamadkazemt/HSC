# نصب سریع سرویس ربات روبیکا

## مشکل فعلی
Celery Worker و Beat درست کار می‌کنند، اما **ربات روبیکا نیاز به سرویس جداگانه‌ای دارد**.

## فایل‌های جدید ایجاد شده

1. ✅ [rubika_bot/management/commands/run_rubika_bot.py](rubika_bot/management/commands/run_rubika_bot.py) - دستور Django برای اجرای ربات
2. ✅ [rubika-bot.service](rubika-bot.service) - فایل سرویس systemd
3. ✅ [install_celery_services.sh](install_celery_services.sh) - بروزرسانی شده برای نصب ربات

## نصب سریع

### گام 1: آپلود فایل‌ها به سرور

```bash
# از ویندوز
scp rubika_bot/management/commands/run_rubika_bot.py hsc_admin@your-server:/var/www/HSC/rubika_bot/management/commands/
scp rubika-bot.service hsc_admin@your-server:/var/www/HSC/
scp install_celery_services.sh hsc_admin@your-server:/var/www/HSC/
```

### گام 2: نصب سرویس

```bash
# اتصال به سرور
ssh hsc_admin@your-server

# رفتن به دایرکتوری پروژه
cd /var/www/HSC

# کپی فایل سرویس
sudo cp rubika-bot.service /etc/systemd/system/

# فعال‌سازی و شروع سرویس
sudo systemctl daemon-reload
sudo systemctl enable rubika-bot
sudo systemctl start rubika-bot

# بررسی وضعیت
sudo systemctl status rubika-bot
```

### گام 3: مشاهده لاگ‌ها

```bash
# مشاهده لاگ‌های زنده
sudo journalctl -u rubika-bot -f

# 100 خط آخر
sudo journalctl -u rubika-bot -n 100

# لاگ‌های امروز
sudo journalctl -u rubika-bot --since today
```

## بررسی عملکرد

```bash
# وضعیت همه سرویس‌ها
sudo systemctl status celery-worker celery-beat rubika-bot

# اگر نیاز به راه‌اندازی مجدد بود
sudo systemctl restart rubika-bot
```

## حل مشکلات احتمالی

### 1. سرویس شروع نمی‌شود

```bash
# بررسی لاگ‌ها
sudo journalctl -u rubika-bot -n 50

# تست دستی
cd /var/www/HSC
source venv/bin/activate
python manage.py run_rubika_bot
```

### 2. خطای Permission Denied

```bash
# تنظیم مالکیت فایل‌ها
sudo chown -R hsc_admin:hsc_admin /var/www/HSC
sudo chmod +x rubika_bot/management/commands/run_rubika_bot.py
```

### 3. ربات پیام‌ها را دریافت نمی‌کند

```bash
# بررسی تنظیمات Webhook در Django Admin
# به /admin/rubika_bot/rubikabotsettings/ بروید

# یا از shell بررسی کنید:
python manage.py shell
>>> from rubika_bot.models import RubikaBotSettings
>>> settings = RubikaBotSettings.get_settings()
>>> print(settings.bot_token)
>>> print(settings.webhook_url)
```

## نصب خودکار همه سرویس‌ها (اختیاری)

اگر می‌خواهید همه سرویس‌ها را دوباره نصب کنید:

```bash
cd /var/www/HSC
sudo bash install_celery_services.sh
```

این اسکریپت:
- ✅ Celery Worker را نصب می‌کند
- ✅ Celery Beat را نصب می‌کند
- ✅ Rubika Bot را نصب می‌کند
- ✅ همه را فعال و شروع می‌کند

## دستورات مفید

```bash
# مشاهده وضعیت
sudo systemctl status rubika-bot

# راه‌اندازی مجدد
sudo systemctl restart rubika-bot

# توقف
sudo systemctl stop rubika-bot

# شروع
sudo systemctl start rubika-bot

# غیرفعال کردن
sudo systemctl disable rubika-bot

# مشاهده لاگ‌های خطا
sudo journalctl -u rubika-bot -p err

# پاک کردن لاگ‌های قدیمی
sudo journalctl --vacuum-time=7d
```

## ساختار نهایی سرویس‌ها

```
/etc/systemd/system/
├── celery-worker.service   ✅ اجرای تسک‌های background
├── celery-beat.service     ✅ زمان‌بند تسک‌ها
└── rubika-bot.service      ✅ ربات روبیکا
```

همه سرویس‌ها به صورت خودکار با بوت سرور شروع می‌شوند! 🚀
