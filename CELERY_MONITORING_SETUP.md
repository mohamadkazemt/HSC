# راهنمای نصب مانیتورینگ Celery

## آپدیت: مشکل برطرف شد! ✅

بعد از restart کردن سرویس‌های Celery، مشکل خطای 500 برطرف شد.

## چرا مشکل رخ داده بود؟

1. **Celery Worker اجرا نبود یا hang شده بود**
2. Task های webhook در صف Redis جمع شده بودند
3. Django فقط task را queue می‌کرد اما پردازش نمی‌شد
4. در نتیجه خطای 500 رخ می‌داد

## برای جلوگیری از تکرار مشکل:

### 1. فعال‌سازی Auto-Restart

بررسی کنید که فایل `/etc/systemd/system/celery.service` این تنظیمات را دارد:

```ini
[Service]
# ... سایر تنظیمات ...
Restart=always
RestartSec=10s
KillMode=mixed
TimeoutStopSec=30
```

اگر ندارد:

```bash
sudo nano /etc/systemd/system/celery.service
# اضافه کردن تنظیمات بالا
sudo systemctl daemon-reload
sudo systemctl restart celery.service
```

همین کار را برای `celery-beat.service` هم انجام دهید.

### 2. نصب اسکریپت مانیتورینگ

اسکریپت `monitor_celery.sh` را در سرور کپی کنید:

```bash
# کپی فایل به سرور
scp monitor_celery.sh root@miepco:/usr/local/bin/

# در سرور:
sudo chmod +x /usr/local/bin/monitor_celery.sh

# تست اسکریپت
sudo /usr/local/bin/monitor_celery.sh
```

### 3. افزودن به Crontab

برای اجرای خودکار هر 5 دقیقه:

```bash
sudo crontab -e
```

اضافه کردن این خط:

```
*/5 * * * * /usr/local/bin/monitor_celery.sh
```

### 4. استفاده از Health Check Endpoint

یک endpoint جدید اضافه شده: `/rubika-bot/health/`

**تست دستی:**

```bash
curl http://localhost/rubika-bot/health/
```

**خروجی نمونه:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-15T12:00:00+03:30",
  "checks": {
    "database": "ok",
    "celery_workers": "ok (4 workers)",
    "rubpy_service": "ok"
  }
}
```

**استفاده با مانیتورینگ خارجی:**

می‌توانید از سرویس‌هایی مثل:
- UptimeRobot (uptimerobot.com)
- Pingdom
- StatusCake

برای چک کردن این endpoint استفاده کنید.

### 5. مانیتورینگ دستی

**بررسی وضعیت سرویس‌ها:**

```bash
# وضعیت Celery Worker
sudo systemctl status celery.service

# وضعیت Celery Beat
sudo systemctl status celery-beat.service

# وضعیت Redis
sudo systemctl status redis

# لاگ‌های اخیر
sudo journalctl -u celery.service -n 50
sudo journalctl -u celery-beat.service -n 50
```

**بررسی صف Redis:**

```bash
# تعداد task های در صف
redis-cli LLEN celery

# نمایش 10 task اول (بدون حذف)
redis-cli LRANGE celery 0 9

# بررسی حافظه Redis
redis-cli INFO memory
```

**بررسی Worker های فعال:**

```bash
cd /var/www/HSC
source venv/bin/activate
celery -A HSCprojects inspect active
celery -A HSCprojects inspect stats
```

### 6. لاگ‌های مانیتورینگ

اسکریپت مانیتورینگ در این فایل‌ها لاگ می‌گذارد:

```bash
# لاگ معمولی (هر 5 دقیقه)
tail -f /var/log/celery-monitor.log

# لاگ هشدارها (فقط مشکلات)
tail -f /var/log/celery-alerts.log
```

### 7. دستورات سریع عیب‌یابی

**اگر دوباره خطای 500 داشتید:**

```bash
# 1. بررسی وضعیت
sudo systemctl status celery.service
sudo systemctl status redis

# 2. بررسی لاگ‌های خطا
sudo journalctl -u celery.service --since "10 minutes ago"
sudo journalctl -u gunicorn.service --since "10 minutes ago"

# 3. بررسی صف Redis
redis-cli LLEN celery

# 4. اگر لازم بود، restart
sudo systemctl restart celery.service
sudo systemctl restart celery-beat.service

# 5. بررسی مجدد
curl http://localhost/rubika-bot/health/
```

### 8. Alerting (پیشرفته)

اگر می‌خواهید هنگام خطا اطلاع‌رسانی شوید:

**نصب mailutils:**

```bash
sudo apt-get install mailutils
```

**ویرایش اسکریپت مانیتورینگ:**

```bash
sudo nano /usr/local/bin/monitor_celery.sh
```

اضافه کردن در بخش alert:

```bash
# در قسمت‌های alert، اضافه کنید:
echo "Alert message" | mail -s "Celery Alert" your-email@example.com
```

یا استفاده از Telegram Bot API برای ارسال پیام.

---

## چک‌لیست نهایی

در سرور این دستورات را اجرا کنید:

```bash
# 1. بررسی همه سرویس‌ها
sudo systemctl status redis celery.service celery-beat.service gunicorn.service

# 2. بررسی health endpoint
curl http://localhost/rubika-bot/health/

# 3. ارسال پیام تست به ربات روبیکا
# (از طریق اپلیکیشن روبیکا)

# 4. بررسی لاگ‌های webhook
tail -f /var/www/HSC/logs/application.log

# 5. بررسی لاگ Celery
tail -f /var/www/HSC/logs/celery-worker.log
```

اگر همه این موارد OK بود، سیستم شما سالم است! ✅

---

## نکات مهم

1. **همیشه بعد از restart سرور، سرویس‌ها را چک کنید**
2. **لاگ‌های Celery را به صورت دوره‌ای بررسی کنید**
3. **از Health Check برای مانیتورینگ خارجی استفاده کنید**
4. **صف Redis را زیر نظر داشته باشید (نباید خیلی بزرگ شود)**

---

## پشتیبانی

اگر دوباره مشکل داشتید:

1. لاگ‌های `/var/log/celery-monitor.log` و `/var/log/celery-alerts.log` را چک کنید
2. `sudo journalctl -u celery.service -n 100` را بررسی کنید
3. Redis را restart کنید: `sudo systemctl restart redis`
4. Celery را restart کنید: `sudo systemctl restart celery.service celery-beat.service`
