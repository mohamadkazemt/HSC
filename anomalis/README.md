# 🖼️ سیستم فشرده‌سازی خودکار تصاویر آنومالی

## 📌 خلاصه
این سیستم به صورت خودکار تصاویر آپلود شده در فرم ثبت آنومالی را فشرده می‌کند تا از پر شدن فضای ذخیره‌سازی سرور جلوگیری کند.

## ✨ ویژگی‌ها

### 🔄 فشرده‌سازی دو لایه‌ای
1. **در مرورگر (Frontend)**: قبل از ارسال به سرور
2. **در سرور (Backend)**: قبل از ذخیره در دیتابیس

### 📊 نتایج
- **کاهش حجم**: تا 80-85% کاهش حجم
- **حفظ کیفیت**: تصاویر همچنان واضح و قابل استفاده
- **صرفه‌جویی فضا**: هزاران مگابایت فضای ذخیره‌سازی

### 🎯 تنظیمات پیش‌فرض
- حداکثر حجم نهایی: **1 مگابایت**
- حداکثر ابعاد: **1920 پیکسل**
- کیفیت: **85%**
- فرمت خروجی: **JPEG**

## 🚀 شروع سریع

### 1. نصب وابستگی‌ها
```bash
# Pillow از قبل نصب است
pip install Pillow==10.4.0
```

### 2. بررسی سلامت سیستم
```bash
python manage.py check anomalis
```

### 3. اجرای تست‌ها
```bash
# تست سریع
python anomalis/test_quick.py

# تست‌های کامل
python manage.py test anomalis.test_image_compression
```

### 4. بهینه‌سازی تصاویر موجود
```bash
# ابتدا شبیه‌سازی کنید
python manage.py optimize_anomaly_images --dry-run

# سپس واقعی اجرا کنید
python manage.py optimize_anomaly_images
```

## 📁 ساختار فایل‌ها

```
anomalis/
├── utils.py                          # توابع فشرده‌سازی و اعتبارسنجی
├── models.py                         # مدل Anomaly با متد save بهبود یافته
├── forms.py                          # فرم با اعتبارسنجی بهینه شده
├── test_quick.py                     # تست سریع
├── test_image_compression.py         # تست‌های کامل
├── optimize_existing_images.py       # اسکریپت بهینه‌سازی
├── management/
│   └── commands/
│       └── optimize_anomaly_images.py  # دستور Django
└── docs/
    ├── IMAGE_COMPRESSION_GUIDE.md      # راهنمای کامل
    ├── MANAGEMENT_COMMAND_GUIDE.md     # راهنمای دستور
    ├── SUMMARY.md                      # خلاصه تغییرات
    └── README.md                       # این فایل

templates/anomalis/
└── new-anomalie.html                 # فرم با فشرده‌سازی Frontend
```

## 🔧 تنظیمات

### Backend (models.py)
```python
# تغییر تنظیمات در models.py
self.image = compress_image(
    self.image,
    max_size_mb=0.5,    # کاهش به 0.5 مگابایت
    quality=75,         # کاهش کیفیت به 75%
    max_dimension=1600  # کاهش ابعاد به 1600px
)
```

### Frontend (new-anomalie.html)
```javascript
// تغییر تنظیمات در JavaScript
const options = {
  maxSizeMB: 0.8,
  maxWidthOrHeight: 1600,
  initialQuality: 0.80
};
```

## 📖 مستندات کامل

- [**IMAGE_COMPRESSION_GUIDE.md**](IMAGE_COMPRESSION_GUIDE.md): راهنمای کامل فشرده‌سازی
- [**MANAGEMENT_COMMAND_GUIDE.md**](MANAGEMENT_COMMAND_GUIDE.md): راهنمای دستورات
- [**SUMMARY.md**](SUMMARY.md): خلاصه تغییرات و چک‌لیست

## 🧪 تست و تأیید

### ✅ تست انجام شده
```bash
$ python anomalis/test_quick.py
🔍 شروع تست‌های سیستم فشرده‌سازی تصویر

تست 1: اعتبارسنجی تصویر        ✅ موفق
تست 2: فشرده‌سازی تصویر         ✅ موفق (83% کاهش)
تست 3: تصاویر کوچک              ✅ موفق
تست 4: تبدیل RGBA→RGB          ✅ موفق

نتیجه کلی: 4/4 تست موفق ✅
```

### ✅ بررسی سیستم
```bash
$ python manage.py check anomalis
System check identified no issues (0 silenced). ✅
```

## 📞 پشتیبانی

### خطاهای رایج

#### خطا: "Module not found: PIL"
```bash
pip install Pillow==10.4.0
```

#### خطا: "Permission denied"
```bash
# لینوکس
sudo chown -R www-data:www-data media/

# یا
chmod 755 media/
```

#### تصویر فشرده نمی‌شود
1. مطمئن شوید حجم تصویر بیش از 1MB است
2. Console مرورگر را بررسی کنید
3. لاگ Django را چک کنید

### لاگ‌گیری
```python
# در views.py یا models.py
import logging
logger = logging.getLogger(__name__)
logger.info(f"فشرده‌سازی تصویر: قبل={size_before}MB بعد={size_after}MB")
```

## 🎓 یادگیری بیشتر

### منابع
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [browser-image-compression](https://github.com/Donaldcwl/browser-image-compression)
- [Django File Handling](https://docs.djangoproject.com/en/4.2/topics/files/)

### الگوریتم فشرده‌سازی
1. تبدیل فرمت به JPEG (اگر لازم باشد)
2. تغییر اندازه (اگر بزرگتر از 1920px باشد)
3. کاهش کیفیت تا رسیدن به حجم هدف
4. ذخیره فایل فشرده شده

## 🔐 امنیت

### اعتبارسنجی فایل
- ✅ بررسی نوع فایل
- ✅ بررسی حجم (حداکثر 10MB قبل از فشرده‌سازی)
- ✅ بررسی صحت تصویر با Pillow
- ✅ جلوگیری از آپلود فایل‌های مخرب

### محدودیت‌ها
- حداکثر حجم آپلود: **10 مگابایت**
- فرمت‌های مجاز: **JPG, PNG, GIF, WebP**
- حداکثر ابعاد: **نامحدود** (تغییر اندازه خودکار)

## 🌟 ویژگی‌های آینده

- [ ] تولید خودکار Thumbnail
- [ ] پشتیبانی از WebP
- [ ] فشرده‌سازی پیشرفته با AI
- [ ] نمایش Progress Bar در مرورگر
- [ ] آپلود چندین تصویر همزمان
- [ ] Lazy Loading برای لیست تصاویر

## 📄 مجوز
این کد بخشی از پروژه HSC است.

---

**تاریخ ایجاد**: نوامبر 2025  
**نسخه**: 1.0.0  
**وضعیت**: ✅ تولید آماده  
**توسعه‌دهنده**: GitHub Copilot
