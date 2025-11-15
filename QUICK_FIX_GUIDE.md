# 🚀 راهنمای سریع حل مشکل آپلود فیش‌های حقوقی

## ✅ تغییرات انجام شده در کد

### 1. تنظیمات Django
- ✓ افزایش محدودیت آپلود به 50MB
- ✓ افزایش تعداد فیلدهای مجاز
- ✓ بهینه‌سازی File Upload Handlers

### 2. بهبود Backend
- ✓ محدودیت 200 فایل در هر batch
- ✓ بررسی حجم فایل (حداکثر 10MB)
- ✓ استفاده از Transaction برای امنیت
- ✓ بهبود مدیریت خطا

### 3. بهبود Frontend
- ✓ اعلان محدودیت تعداد فایل
- ✓ هشدار بصری برای تعداد زیاد
- ✓ Progress tracking بهتر
- ✓ مدیریت خطاهای timeout

---

## 🔧 اقدامات لازم در سرور

### گام 1️⃣: آپلود فایل‌ها به سرور

```bash
# از ویندوز به سرور
scp nginx_config_updated.conf root@65.109.220.72:/root/
scp apply_server_config.sh root@65.109.220.72:/root/
scp check_personnel_codes.py root@65.109.220.72:/var/www/HSC/
```

### گام 2️⃣: اعمال تنظیمات Nginx

```bash
# اتصال به سرور
ssh root@65.109.220.72

# اجرای اسکریپت
cd /root
chmod +x apply_server_config.sh
./apply_server_config.sh
```

یا به صورت دستی:

```bash
# پشتیبان‌گیری
cp /etc/nginx/sites-available/miepcoj.ir /etc/nginx/sites-available/miepcoj.ir.backup

# کپی فایل جدید
cp nginx_config_updated.conf /etc/nginx/sites-available/miepcoj.ir

# تست
nginx -t

# اعمال
systemctl reload nginx
```

### گام 3️⃣: بهبود Gunicorn

```bash
# ویرایش فایل سرویس
nano /etc/systemd/system/gunicorn.service

# در بخش ExecStart، timeout را افزایش دهید:
ExecStart=/var/www/HSC/venv/bin/gunicorn \
    --workers 4 \
    --timeout 300 \
    --max-requests 1000 \
    --bind unix:/run/gunicorn/gunicorn.sock \
    HSCprojects.wsgi:application

# اعمال تغییرات
systemctl daemon-reload
systemctl restart gunicorn
```

### گام 4️⃣: Deploy کد جدید Django

```bash
cd /var/www/HSC

# Pull تغییرات
git pull origin mkt

# فعال‌سازی محیط مجازی
source venv/bin/activate

# Migrate (در صورت نیاز)
python manage.py migrate

# جمع‌آوری فایل‌های استاتیک
python manage.py collectstatic --noinput

# Restart
systemctl restart gunicorn
```

---

## 🔍 بررسی کدهای پرسنلی

برای بررسی کدهای پرسنلی که در تصویر "یافت نشد" نشان می‌دهد:

```bash
cd /var/www/HSC
source venv/bin/activate

# نمایش تمام کدهای موجود
python check_personnel_codes.py --list

# یا بررسی فایل‌های خاص
python check_personnel_codes.py 11003.pdf 11004.pdf 11005.pdf 11057.pdf 11058.pdf
```

این اسکریپت به شما می‌گوید:
- ✓ کدام کدها در سیستم وجود دارند
- ✗ کدام کدها یافت نمی‌شوند
- 💡 کدهای مشابه موجود در دیتابیس

---

## 📊 تست عملکرد

پس از اعمال تنظیمات:

### تست 1: آپلود تعداد کم
```
1. وارد مدیریت فیش حقوقی شوید
2. سال و ماه را انتخاب کنید
3. 10-20 فایل آپلود کنید
4. بررسی موفقیت
```

### تست 2: آپلود تعداد متوسط
```
1. 50-100 فایل آپلود کنید
2. زمان را بررسی کنید (باید کمتر از 1 دقیقه باشد)
3. گزارش نتایج را بررسی کنید
```

### تست 3: آپلود تعداد زیاد
```
1. 150-200 فایل آپلود کنید
2. مانیتور لاگ‌ها را داشته باشید
3. بررسی موفقیت
```

---

## 🐛 عیب‌یابی

### اگر خطای 413 می‌گیرید:
```bash
# بررسی nginx config
grep client_max_body_size /etc/nginx/sites-available/miepcoj.ir
# باید 100M باشد
```

### اگر خطای 504 (Timeout) می‌گیرید:
```bash
# بررسی timeout nginx
grep timeout /etc/nginx/sites-available/miepcoj.ir

# بررسی timeout gunicorn
systemctl cat gunicorn | grep timeout
```

### اگر خطای "کد پرسنلی یافت نشد":
```bash
# بررسی کدهای موجود
cd /var/www/HSC
python check_personnel_codes.py --list | grep 11003
```

---

## 📝 لاگ‌ها

### مانیتور لاگ‌ها در زمان آپلود:

```bash
# Terminal 1: Nginx
tail -f /var/log/nginx/miepcoj.ir.error.log

# Terminal 2: Gunicorn
journalctl -u gunicorn -f

# Terminal 3: Django
tail -f /var/www/HSC/logs/errors.log
```

---

## 📞 خلاصه فایل‌های ایجاد شده

| فایل | توضیح | استفاده |
|------|-------|---------|
| `nginx_config_updated.conf` | تنظیمات بهبود یافته Nginx | کپی به `/etc/nginx/sites-available/` |
| `apply_server_config.sh` | اسکریپت خودکار اعمال تنظیمات | اجرا در سرور |
| `check_personnel_codes.py` | بررسی کدهای پرسنلی | اجرا در Django environment |
| `PAYSLIP_UPLOAD_SERVER_CONFIG.md` | مستندات کامل | مرجع |

---

## ✨ نکات مهم

1. **قبل از آپلود تعداد زیاد:**
   - فایل‌ها را دسته‌بندی کنید (100-150 تایی)
   - نام فایل‌ها را با کدهای موجود تطبیق دهید
   - از اتصال اینترنت پایدار استفاده کنید

2. **در حین آپلود:**
   - صفحه را refresh نکنید
   - منتظر پایان progress bar بمانید
   - گزارش نتایج را بررسی کنید

3. **بعد از آپلود:**
   - فایل‌های خطا را جداگانه بررسی کنید
   - از قسمت آرشیو، موفقیت آپلود را تأیید کنید

---

## 🎯 اولویت اقدامات

1. **فوری** (الان):
   - [ ] Deploy کد جدید Django
   - [ ] بررسی کدهای پرسنلی مفقود

2. **مهم** (امروز):
   - [ ] اعمال تنظیمات Nginx
   - [ ] Restart Gunicorn
   - [ ] تست با 50 فایل

3. **توصیه شده**:
   - [ ] اضافه کردن کدهای پرسنلی مفقود
   - [ ] تست با 200 فایل
   - [ ] مستندسازی فرآیند برای تیم
