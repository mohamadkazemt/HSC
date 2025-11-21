# 📝 خلاصه تغییرات: سیستم فشرده‌سازی تصاویر آنومالی

## 🎯 هدف
کاهش حجم تصاویر آپلود شده توسط کاربران برای جلوگیری از پر شدن فضای ذخیره‌سازی سرور

## ✅ تغییرات انجام شده

### 1. فایل‌های جدید ایجاد شده

#### 📄 `anomalis/utils.py`
- **تابع `compress_image()`**: فشرده‌سازی تصاویر با استفاده از Pillow
  - حداکثر حجم: 1 مگابایت (قابل تنظیم)
  - حداکثر ابعاد: 1920 پیکسل
  - کیفیت: 85% (قابل تنظیم)
  - تبدیل خودکار RGBA به RGB
  - فرمت خروجی: JPEG

- **تابع `validate_image_file()`**: اعتبارسنجی فایل‌های تصویری
  - بررسی حجم (حداکثر 10 مگابایت)
  - بررسی نوع فایل
  - بررسی صحت تصویر

#### 📄 `anomalis/management/commands/optimize_anomaly_images.py`
Django Management Command برای بهینه‌سازی تصاویر موجود در دیتابیس:
```bash
python manage.py optimize_anomaly_images
python manage.py optimize_anomaly_images --dry-run
python manage.py optimize_anomaly_images --max-size 0.5 --quality 80
```

#### 📄 فایل‌های راهنما
- `IMAGE_COMPRESSION_GUIDE.md`: راهنمای کامل سیستم فشرده‌سازی
- `MANAGEMENT_COMMAND_GUIDE.md`: راهنمای استفاده از دستور بهینه‌سازی
- `SUMMARY.md`: این فایل

#### 📄 `anomalis/test_image_compression.py`
تست‌های یونیت برای بررسی عملکرد سیستم فشرده‌سازی

#### 📄 `anomalis/optimize_existing_images.py`
اسکریپت Python برای بهینه‌سازی تصاویر موجود

### 2. فایل‌های تغییر یافته

#### 🔧 `anomalis/models.py`
- اضافه شدن import: `from .utils import compress_image`
- اضافه شدن متد `save()` به مدل `Anomaly`:
  - فشرده‌سازی خودکار تصویر قبل از ذخیره
  - فراخوانی `compress_image()` برای هر تصویر جدید

#### 🔧 `anomalis/forms.py`
- اضافه شدن import: `from .utils import validate_image_file`
- بروزرسانی متد `clean_image()`:
  - استفاده از `validate_image_file()` برای اعتبارسنجی کامل
  - افزایش محدودیت حجم از 5MB به 10MB

#### 🔧 `templates/anomalis/new-anomalie.html`
- اضافه شدن کتابخانه `browser-image-compression` از CDN
- پیاده‌سازی تابع `compressImage()` در JavaScript:
  - فشرده‌سازی تصویر قبل از ارسال فرم
  - نمایش پیام "در حال فشرده‌سازی..." به کاربر
  - استفاده از Web Worker برای بهبود کارایی
- بروزرسانی event handler فرم برای فشرده‌سازی خودکار

## 🔄 جریان کار (Workflow)

### 1. کاربر تصویر را انتخاب می‌کند
```
کاربر → انتخاب فایل → پیش‌نمایش
```

### 2. کاربر فرم را ارسال می‌کند
```
کلیک روی "ثبت" → فشرده‌سازی در مرورگر → ارسال به سرور
```

### 3. سرور تصویر را دریافت می‌کند
```
دریافت → اعتبارسنجی فرم → فشرده‌سازی مجدد → ذخیره در دیتابیس
```

## 📊 نتایج انتظاری

### قبل از پیاده‌سازی
- تصویر 5 مگابایتی → ذخیره 5 مگابایت
- 1000 تصویر → ~5 گیگابایت

### بعد از پیاده‌سازی
- تصویر 5 مگابایتی → فشرده به ~0.8 مگابایت
- 1000 تصویر → ~800 مگابایت
- **صرفه‌جویی: ~84%** 🎉

## 🧪 تست کردن

### 1. تست سریع در مرورگر
1. صفحه ثبت آنومالی را باز کنید
2. Console مرورگر را باز کنید (F12)
3. تصویری با حجم بالا (مثلاً 3MB) انتخاب کنید
4. فرم را ارسال کنید
5. پیام‌های "حجم اصلی" و "حجم فشرده شده" را در Console مشاهده کنید

### 2. تست با Django Check
```bash
python manage.py check anomalis
```

### 3. اجرای تست‌های یونیت
```bash
python manage.py test anomalis.test_image_compression
```

### 4. تست بهینه‌سازی تصاویر موجود
```bash
# ابتدا با dry-run تست کنید
python manage.py optimize_anomaly_images --dry-run --limit 5

# سپس واقعی اجرا کنید
python manage.py optimize_anomaly_images --limit 5
```

## ⚙️ تنظیمات قابل تغییر

### در Backend (`models.py`):
```python
self.image = compress_image(
    self.image, 
    max_size_mb=1,      # حجم نهایی (پیش‌فرض: 1MB)
    quality=85,         # کیفیت (پیش‌فرض: 85)
    max_dimension=1920  # حداکثر ابعاد (پیش‌فرض: 1920px)
)
```

### در Frontend (`new-anomalie.html`):
```javascript
const options = {
  maxSizeMB: 1,              // حجم نهایی
  maxWidthOrHeight: 1920,    // حداکثر ابعاد
  useWebWorker: true,        // استفاده از Web Worker
  fileType: 'image/jpeg',    // فرمت خروجی
  initialQuality: 0.85       // کیفیت اولیه
};
```

## 📋 چک‌لیست پس از استقرار

- [ ] بررسی کردن خطاهای Django: `python manage.py check`
- [ ] تست آپلود تصویر در محیط Development
- [ ] بررسی Console مرورگر برای پیام‌های فشرده‌سازی
- [ ] تست با تصاویر مختلف (PNG, JPG, بزرگ، کوچک)
- [ ] اجرای `optimize_anomaly_images` با `--dry-run`
- [ ] پشتیبان‌گیری از فولدر `media`
- [ ] اجرای واقعی `optimize_anomaly_images` برای تصاویر موجود
- [ ] مانیتور کردن فضای دیسک سرور
- [ ] آموزش کاربران (در صورت نیاز)

## 🚀 دستورات مفید

### بررسی سلامت سیستم
```bash
python manage.py check anomalis
```

### بهینه‌سازی تصاویر موجود
```bash
# تست اولیه
python manage.py optimize_anomaly_images --dry-run

# اجرای واقعی
python manage.py optimize_anomaly_images

# با تنظیمات سفارشی
python manage.py optimize_anomaly_images --max-size 0.8 --quality 80
```

### مشاهده لاگ‌ها
```bash
# در صورت استفاده از systemd
journalctl -u gunicorn -f

# یا در صورت استفاده از فایل لاگ
tail -f logs/django.log
```

### بررسی فضای دیسک
```bash
# لینوکس
du -sh media/anomalies/

# ویندوز
dir /s media\\anomalies\\
```

## 🔍 عیب‌یابی

### مشکل: تصویر فشرده نمی‌شود
- ✅ Pillow نصب است؟ `pip list | grep -i pillow`
- ✅ Console مرورگر خطایی نشان می‌دهد؟
- ✅ حجم تصویر از 1MB بیشتر است؟

### مشکل: خطای "Module not found: PIL"
```bash
pip install Pillow==10.4.0
```

### مشکل: Management Command کار نمی‌کند
- ✅ فولدر `management/commands` دارای `__init__.py` است؟
- ✅ نام فایل درست است؟ `optimize_anomaly_images.py`

## 📞 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌های Django را بررسی کنید
2. Console مرورگر را چک کنید
3. تست‌های یونیت را اجرا کنید
4. به فایل‌های راهنما مراجعه کنید

## 🎓 منابع

- [Pillow Documentation](https://pillow.readthedocs.io/)
- [browser-image-compression](https://github.com/Donaldcwl/browser-image-compression)
- [Django File Handling](https://docs.djangoproject.com/en/4.2/topics/files/)

---

**تاریخ پیاده‌سازی**: نوامبر 2025  
**نسخه**: 1.0  
**وضعیت**: ✅ آماده استفاده
