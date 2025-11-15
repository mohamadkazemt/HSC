# راهنمای تنظیمات سرور برای آپلود فیش‌های حقوقی

## مشکل
هنگام آپلود تعداد زیاد فیش حقوقی در سرور، خطا رخ می‌دهد.

## راه‌حل‌های پیاده‌سازی شده

### ۱. تنظیمات Django (انجام شده)

در فایل `HSCprojects/settings/base.py` تنظیمات زیر اضافه شده:

```python
# File Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # افزایش تعداد فیلدهای مجاز
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
```

### ۲. بهبود View (انجام شده)

در `accounts/views.py` در تابع `batch_payslip_upload`:
- محدودیت تعداد فایل: **حداکثر 200 فایل** در هر batch
- محدودیت حجم فایل: **حداکثر 10MB** برای هر فایل
- استفاده از `transaction.atomic()` برای عملیات دیتابیس
- استفاده از `select_for_update()` برای جلوگیری از race condition

### ۳. بهبود Frontend (انجام شده)

در `templates/accounts/payslip_management.html`:
- اضافه کردن بررسی محدودیت تعداد فایل (200)
- بهبود پیام خطا برای timeout و مشکلات سرور
- اضافه کردن progress tracking بهتر

---

## تنظیمات سرور (نیاز به اعمال دستی)

### ۱. Nginx Configuration

در فایل nginx config سایت خود (`/etc/nginx/sites-available/hsc` یا مشابه):

```nginx
server {
    # ... تنظیمات دیگر ...
    
    # افزایش محدودیت حجم آپلود
    client_max_body_size 100M;
    
    # افزایش timeout برای درخواست‌های طولانی
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;
    
    # افزایش buffer size
    client_body_buffer_size 1M;
    proxy_buffers 16 16k;
    proxy_buffer_size 16k;
    
    location / {
        proxy_pass http://127.0.0.1:8000;  # یا هر پورتی که gunicorn روی آن است
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ... تنظیمات دیگر ...
}
```

**دستور اعمال تغییرات:**
```bash
sudo nginx -t  # تست تنظیمات
sudo systemctl reload nginx  # اعمال تغییرات
```

---

### ۲. Gunicorn Configuration

در فایل سرویس Gunicorn یا اسکریپت اجرا:

```bash
gunicorn HSCprojects.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --worker-class sync \
    --worker-connections 1000 \
    --limit-request-line 8190 \
    --limit-request-fields 200 \
    --limit-request-field-size 16384
```

اگر از systemd استفاده می‌کنید (`/etc/systemd/system/gunicorn.service`):

```ini
[Unit]
Description=Gunicorn daemon for HSC project
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/HSC
Environment="DJANGO_SETTINGS_MODULE=HSCprojects.settings.production"
ExecStart=/var/www/HSC/venv/bin/gunicorn \
    --workers 4 \
    --timeout 300 \
    --max-requests 1000 \
    --bind 127.0.0.1:8000 \
    HSCprojects.wsgi:application

[Install]
WantedBy=multi-user.target
```

**دستور اعمال تغییرات:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

---

### ۳. PostgreSQL Configuration (اختیاری)

اگر با تعداد زیاد connection مواجه هستید، در `/etc/postgresql/*/main/postgresql.conf`:

```conf
max_connections = 200
shared_buffers = 256MB
work_mem = 16MB
maintenance_work_mem = 128MB
effective_cache_size = 1GB
```

**دستور اعمال تغییرات:**
```bash
sudo systemctl restart postgresql
```

---

## نکات مهم

### محدودیت‌های تعیین شده:

1. **تعداد فایل در هر batch**: حداکثر 200 فایل
2. **حجم هر فایل**: حداکثر 10MB
3. **مجموع حجم request**: حداکثر 50MB

### توصیه‌ها برای کاربران:

اگر تعداد فیش‌ها بیشتر از 200 عدد است:
- فایل‌ها را به دسته‌های کوچک‌تر تقسیم کنید
- هر بار 100-150 فایل آپلود کنید
- بین آپلودها چند ثانیه صبر کنید

### مانیتورینگ:

برای بررسی مشکلات احتمالی:

```bash
# بررسی لاگ‌های nginx
sudo tail -f /var/log/nginx/error.log

# بررسی لاگ‌های gunicorn
sudo journalctl -u gunicorn -f

# بررسی لاگ‌های Django
tail -f /var/www/HSC/logs/production.log
tail -f /var/www/HSC/logs/errors.log
```

---

## تست در سرور

بعد از اعمال تغییرات، می‌توانید تست کنید:

1. وارد صفحه مدیریت فیش حقوقی شوید
2. سال و ماه را انتخاب کنید
3. ابتدا 50 فایل آپلود کنید (تست)
4. اگر موفق بود، 100 فایل آپلود کنید
5. در صورت موفقیت، تا 200 فایل آپلود کنید

---

## عیب‌یابی رایج

### خطا: "413 Request Entity Too Large"
- **علت**: محدودیت `client_max_body_size` در nginx
- **راه‌حل**: افزایش `client_max_body_size` در nginx config

### خطا: "504 Gateway Timeout"
- **علت**: timeout کم در nginx یا gunicorn
- **راه‌حل**: افزایش timeout در هر دو

### خطا: "Connection reset by peer"
- **علت**: worker های gunicorn timeout شده‌اند
- **راه‌حل**: افزایش `--timeout` در gunicorn

### خطا: "Too many open files"
- **علت**: محدودیت سیستمی
- **راه‌حل**:
```bash
ulimit -n 65535
# یا در /etc/security/limits.conf:
* soft nofile 65535
* hard nofile 65535
```

---

## چک‌لیست نهایی

- [ ] تنظیمات Django اعمال شده (✓ انجام شده)
- [ ] nginx config به‌روزرسانی شده
- [ ] nginx restart شده
- [ ] gunicorn config به‌روزرسانی شده
- [ ] gunicorn restart شده
- [ ] تست با 50 فایل انجام شده
- [ ] تست با 100 فایل انجام شده
- [ ] تست با 200 فایل انجام شده

---

## پشتیبانی

در صورت مواجهه با مشکل:
1. لاگ‌های nginx را بررسی کنید
2. لاگ‌های gunicorn را بررسی کنید
3. لاگ‌های Django را بررسی کنید (`logs/errors.log`)
4. از Developer Tools مرورگر (Network tab) استفاده کنید
