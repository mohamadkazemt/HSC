# راهنمای مدیریت سرویس‌های HSC

این راهنما شامل اسکریپت‌های مدیریت و تست سرویس‌های پروژه HSC است.

## سرویس‌های پروژه

- `gunicorn.service` - سرور WSGI برای Django
- `nginx` - وب سرور
- `celery-worker` - پردازشگر تسک‌های Celery
- `celery-beat` - زمان‌بند تسک‌های Celery
- `rubika-bot` - ربات Rubika

## اسکریپت‌های موجود

### 1. `check_services_status.sh`
بررسی وضعیت تمام سرویس‌ها

```bash
sudo bash check_services_status.sh
```

**خروجی:**
- ✓ برای سرویس‌های فعال
- ✗ برای سرویس‌های غیرفعال
- کد خروجی 0 اگر همه فعال باشند
- کد خروجی 1 اگر برخی غیرفعال باشند

---

### 2. `restart_all_services.sh`
راه‌اندازی مجدد تمام سرویس‌ها

```bash
sudo bash restart_all_services.sh
```

**عملکرد:**
- راه‌اندازی مجدد تمام سرویس‌ها
- بررسی وضعیت بعد از راه‌اندازی مجدد
- نمایش خلاصه نتایج

---

### 3. `test_services.sh`
تست پیشرفته و جامع سرویس‌ها

```bash
sudo bash test_services.sh
```

**بررسی‌ها:**
- وضعیت فعال بودن سرویس
- بررسی وجود پروسه‌های مربوطه
- بررسی خطاهای اخیر در لاگ‌ها
- تست کانفیگ nginx
- نمایش خلاصه کامل نتایج

---

### 4. `service_manager.sh`
اسکریپت جامع مدیریت سرویس‌ها

```bash
# بررسی وضعیت
sudo bash service_manager.sh status

# راه‌اندازی مجدد
sudo bash service_manager.sh restart

# شروع سرویس‌ها
sudo bash service_manager.sh start

# توقف سرویس‌ها
sudo bash service_manager.sh stop

# مشاهده لاگ‌ها
sudo bash service_manager.sh logs
```

## دستورات سریع

### بررسی وضعیت
```bash
sudo systemctl status gunicorn.service nginx celery-worker celery-beat rubika-bot
```

### راه‌اندازی مجدد
```bash
sudo systemctl restart gunicorn.service
sudo systemctl restart nginx
sudo systemctl restart celery-worker celery-beat rubika-bot
```

### مشاهده لاگ‌ها
```bash
# لاگ Gunicorn
sudo journalctl -u gunicorn.service -f

# لاگ Nginx
sudo journalctl -u nginx -f

# لاگ Celery Worker
sudo journalctl -u celery-worker -f

# لاگ Celery Beat
sudo journalctl -u celery-beat -f

# لاگ Rubika Bot
sudo journalctl -u rubika-bot -f
```

### مشاهده آخرین خطاها
```bash
# آخرین 50 خط لاگ هر سرویس
sudo journalctl -u gunicorn.service -n 50
sudo journalctl -u celery-worker -n 50
sudo journalctl -u celery-beat -n 50
sudo journalctl -u rubika-bot -n 50
```

## نصب و راه‌اندازی

### 1. کپی اسکریپت‌ها به سرور
```bash
# از سیستم محلی به سرور
scp *.sh user@server:/var/www/HSC/
```

### 2. تنظیم مجوز اجرا
```bash
# در سرور
cd /var/www/HSC
sudo chmod +x *.sh
```

### 3. تست اولیه
```bash
# بررسی وضعیت
sudo bash check_services_status.sh

# تست کامل
sudo bash test_services.sh
```

## عیب‌یابی

### اگر سرویسی راه‌اندازی نمی‌شود:

1. **بررسی وضعیت:**
   ```bash
   sudo systemctl status <service-name>
   ```

2. **بررسی لاگ‌ها:**
   ```bash
   sudo journalctl -u <service-name> -n 100
   ```

3. **بررسی کانفیگ:**
   ```bash
   # برای nginx
   sudo nginx -t
   
   # برای systemd services
   sudo systemctl daemon-reload
   ```

4. **راه‌اندازی مجدد:**
   ```bash
   sudo bash restart_all_services.sh
   ```

### مشکلات رایج

**Celery Worker/Beat راه‌اندازی نمی‌شود:**
- بررسی اتصال به Redis: `redis-cli ping`
- بررسی مسیر virtual environment
- بررسی متغیرهای محیطی

**Gunicorn راه‌اندازی نمی‌شود:**
- بررسی مسیر پروژه
- بررسی دسترسی‌های فایل
- بررسی پورت در حال استفاده

**Rubika Bot راه‌اندازی نمی‌شود:**
- بررسی تنظیمات Django
- بررسی اتصال به API Rubika
- بررسی لاگ‌های Django

## خودکارسازی

### Cron Job برای بررسی منظم

```bash
# ویرایش crontab
sudo crontab -e

# اضافه کردن این خط برای بررسی هر 5 دقیقه
*/5 * * * * /var/www/HSC/check_services_status.sh >> /var/www/HSC/logs/service_check.log 2>&1
```

### Alert Script

می‌توانید اسکریپت `check_services_status.sh` را با سیستم اطلاع‌رسانی (مثل ایمیل یا Telegram) ادغام کنید.

## نکات مهم

1. **همیشه از sudo استفاده کنید** - تمام دستورات نیاز به دسترسی root دارند
2. **قبل از راه‌اندازی مجدد، وضعیت را بررسی کنید** - ممکن است مشکل دیگری وجود داشته باشد
3. **لاگ‌ها را به طور منظم بررسی کنید** - برای شناسایی مشکلات احتمالی
4. **بعد از تغییر کانفیگ، systemd را reload کنید:**
   ```bash
   sudo systemctl daemon-reload
   ```

## پشتیبانی

در صورت بروز مشکل:
1. خروجی `test_services.sh` را بررسی کنید
2. لاگ‌های مربوطه را بررسی کنید
3. وضعیت systemd را بررسی کنید

