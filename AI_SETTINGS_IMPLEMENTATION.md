# پیاده‌سازی رابط کاربری مدیریت AI

## ✅ کارهای انجام شده

### 1. مدل AISettings (`core/ai_models.py`)
- مدل Singleton برای ذخیره تنظیمات AI
- پشتیبانی از چندین provider (OpenAI, Anthropic, Google, Local)
- رمزگذاری API Key با django-cryptography
- ذخیره اطلاعات تست اتصال

### 2. فرم تنظیمات (`core/ai_forms.py`)
- فرم کامل برای مدیریت تنظیمات
- اعتبارسنجی فیلدها
- مدیریت API Key (نمایش placeholder در صورت وجود)

### 3. Views (`core/views.py`)
- `ai_settings_view`: صفحه تنظیمات AI
- `ai_test_connection`: تست اتصال به API

### 4. URLs (`core/urls.py`)
- `/core/ai-settings/` - صفحه تنظیمات
- `/core/ai-settings/test-connection/` - تست اتصال

### 5. Template (`templates/core/ai_settings.html`)
- رابط کاربری کامل و زیبا
- نمایش وضعیت آخرین تست
- دکمه تست اتصال با modal
- لینک به Google AI Studio
- به‌روزرسانی خودکار API Base URL بر اساس provider

### 6. Header Integration (`templates/partials/header.html`)
- افزودن لینک "تنظیمات هوش مصنوعی" در dropdown تنظیمات superuser
- نمایش با آیکون ربات

### 7. Admin Panel (`core/admin.py`)
- ثبت مدل AISettings در admin
- نمایش فیلدهای مهم
- readonly fields برای اطلاعات تست

### 8. پشتیبانی از Google AI Studio
- افزودن متد `_call_google_api` در `ai_service.py`
- پشتیبانی از فرمت Gemini API
- لینک مستقیم به https://aistudio.google.com/

## 🚀 نحوه استفاده

### 1. اجرای Migration
```bash
python manage.py makemigrations core
python manage.py migrate
```

### 2. دسترسی به تنظیمات
- ورود به سیستم به عنوان superuser
- کلیک روی عکس کاربر در header
- انتخاب "تنظیمات" از dropdown
- کلیک روی "تنظیمات هوش مصنوعی"

### 3. تنظیم API Key از Google AI Studio
1. رفتن به https://aistudio.google.com/
2. دریافت API Key
3. وارد کردن در فرم تنظیمات
4. انتخاب provider: "Google AI Studio (Gemini)"
5. مدل: "gemini-pro" (یا مدل‌های دیگر)
6. کلیک روی "تست اتصال" برای بررسی
7. ذخیره تنظیمات

## 📋 فایل‌های ایجاد/تغییر یافته

### فایل‌های جدید:
- `core/ai_models.py` - مدل AISettings
- `core/ai_forms.py` - فرم تنظیمات
- `templates/core/ai_settings.html` - template تنظیمات

### فایل‌های تغییر یافته:
- `core/views.py` - افزودن views
- `core/urls.py` - افزودن URLs
- `core/admin.py` - ثبت مدل در admin
- `core/ai_service.py` - پشتیبانی از Google AI و تنظیمات دیتابیس
- `templates/partials/header.html` - افزودن لینک

## 🔧 ویژگی‌ها

1. **امنیت**: API Key به صورت رمزگذاری‌شده ذخیره می‌شود
2. **تست اتصال**: امکان تست فوری اتصال به API
3. **چند Provider**: پشتیبانی از OpenAI, Anthropic, Google, Local
4. **رابط کاربری**: طراحی زیبا و کاربرپسند
5. **Auto-fill**: پر کردن خودکار API Base URL بر اساس provider
6. **وضعیت تست**: نمایش آخرین نتیجه تست

## ⚠️ نکات مهم

1. بعد از تغییر تنظیمات، instance سرویس AI reset می‌شود
2. API Key در صورت عدم تغییر، حفظ می‌شود
3. تست اتصال، نتیجه را در دیتابیس ذخیره می‌کند
4. برای Google AI Studio، API Key را از https://aistudio.google.com/ دریافت کنید

## 🎯 مراحل بعدی (اختیاری)

- [ ] افزودن لاگ استفاده از AI
- [ ] نمایش آمار استفاده
- [ ] محدودیت تعداد درخواست
- [ ] پشتیبانی از چندین API Key (fallback)
