# راهنمای امنیتی فیش‌های حقوقی

## بررسی‌های امنیتی اعمال شده

### 1. بررسی دسترسی در View
- در ویو `payslip_download` بررسی می‌شود که فقط کاربر مربوطه یا superuser می‌تواند فیش را دانلود کند
- تلاش‌های غیرمجاز لاگ می‌شوند

### 2. نام فایل تصادفی
- فایل‌ها با UUID ذخیره می‌شوند تا حدس زدن مسیر فایل غیرممکن شود
- مسیر واقعی فایل: `payslips/YYYY/MM/uuid-hex.pdf`
- نام فایل نمایش داده شده به کاربر: `payslip_PERSONNEL_CODE_YYYY_MM.pdf`

### 3. جلوگیری از Cache
- هدرهای HTTP برای جلوگیری از cache کردن فایل‌های حساس اضافه شده‌اند

## تنظیمات Apache/Nginx برای امنیت بیشتر

### برای Apache:
در فایل تنظیمات Apache (مثلاً `/etc/apache2/sites-available/your-site.conf`) اضافه کنید:

```apache
# محافظت از دایرکتوری payslips - جلوگیری از دسترسی مستقیم
<Directory "/home/miepcoj/HSC/media/payslips">
    Require all denied
</Directory>

# یا اگر می‌خواهید فقط از طریق Django سرو شود:
Alias /media/payslips /dev/null
<Location /media/payslips>
    Require all denied
</Location>
```

### برای Nginx:
در فایل تنظیمات Nginx (مثلاً `/etc/nginx/sites-available/your-site`) اضافه کنید:

```nginx
# محافظت از دایرکتوری payslips
location /media/payslips/ {
    deny all;
    return 403;
}
```

## نکات مهم

1. **همیشه از Django View استفاده کنید**: فایل‌ها فقط باید از طریق `/accounts/payslips/<id>/download/` قابل دسترسی باشند
2. **بررسی دسترسی**: در هر درخواست دانلود، بررسی می‌شود که کاربر مجاز است یا نه
3. **لاگ تلاش‌های غیرمجاز**: تمام تلاش‌های غیرمجاز در لاگ ثبت می‌شوند
4. **نام فایل تصادفی**: با استفاده از UUID، حدس زدن مسیر فایل غیرممکن است

## تست امنیتی

برای اطمینان از امنیت:

1. سعی کنید با یک کاربر عادی به فیش کاربر دیگر دسترسی پیدا کنید
2. بررسی کنید که دسترسی مستقیم به `/media/payslips/...` غیرممکن است
3. بررسی لاگ‌ها برای تلاش‌های غیرمجاز

## پس از اعمال تغییرات

پس از تغییر `upload_to` در مدل `Payslip`:
1. Migration جدید ایجاد کنید: `python manage.py makemigrations accounts`
2. Migration را اعمال کنید: `python manage.py migrate accounts`
3. فایل‌های قدیمی را به ساختار جدید منتقل کنید (در صورت نیاز)

