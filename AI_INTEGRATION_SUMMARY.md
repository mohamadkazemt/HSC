# خلاصه یکپارچه‌سازی هوش مصنوعی در سیستم HSC

## ✅ کارهای انجام شده

### 1. سرویس اصلی AI (`core/ai_service.py`)
- پشتیبانی از چندین provider (OpenAI, Anthropic, Local/Ollama)
- سیستم کش برای کاهش هزینه‌ها
- تولید متن و JSON
- مدیریت خطا و retry

### 2. سرویس اختصاصی اقدام اصلاحی (`corrective_actions/ai_helper.py`)
- تولید خودکار داده‌های فرم اقدام اصلاحی
- تحلیل علل ریشه‌ای
- پیشنهاد مراحل اقدام
- شناسایی ریسک‌های ناشی از اقدام
- استفاده از اطلاعات مرتبط (آنومالی، حادثه، ریسک)

### 3. API Endpoints (`corrective_actions/views.py`)
- `/corrective-actions/api/ai/generate-suggestions/` - تولید پیشنهادات کامل
- `/corrective-actions/api/ai/generate-root-cause/` - تولید تحلیل علل ریشه‌ای

### 4. رابط کاربری (`corrective_actions/templates/corrective_actions/corrective_action_form.html`)
- دکمه "کمک هوش مصنوعی" برای پر کردن خودکار فرم
- دکمه "تولید تحلیل علل ریشه‌ای" برای تولید تحلیل
- JavaScript برای ارتباط با API و پر کردن فرم

### 5. تنظیمات (`HSCprojects/settings/base.py`)
- تنظیمات کامل برای AI Service
- پشتیبانی از environment variables
- تنظیمات پیش‌فرض و قابل تغییر

## 🚀 نحوه استفاده

### راه‌اندازی اولیه:

1. تنظیم API Key در environment variables:
```bash
export AI_API_KEY="your-api-key"
export AI_API_BASE_URL="https://api.openai.com/v1"
export AI_MODEL="gpt-4"
export AI_PROVIDER="openai"
```

2. استفاده در فرم:
   - باز کردن فرم ایجاد اقدام اصلاحی
   - کلیک روی دکمه "کمک هوش مصنوعی"
   - بررسی و ویرایش پیشنهادات

### استفاده برنامه‌نویسی:

```python
from corrective_actions.ai_helper import CorrectiveActionAIHelper

ai_helper = CorrectiveActionAIHelper()
suggestions = ai_helper.generate_corrective_action_data(
    related_anomaly_id=123
)
```

## 📁 فایل‌های ایجاد/تغییر یافته

### فایل‌های جدید:
- `core/ai_service.py` - سرویس اصلی AI
- `corrective_actions/ai_helper.py` - سرویس اختصاصی اقدام اصلاحی
- `corrective_actions/AI_INTEGRATION_README.md` - راهنمای کامل

### فایل‌های تغییر یافته:
- `corrective_actions/views.py` - افزودن API endpoints
- `corrective_actions/urls.py` - افزودن URL patterns
- `corrective_actions/templates/corrective_actions/corrective_action_form.html` - افزودن UI
- `HSCprojects/settings/base.py` - افزودن تنظیمات AI

## 🔧 تنظیمات پیشرفته

برای جزئیات بیشتر، به فایل `corrective_actions/AI_INTEGRATION_README.md` مراجعه کنید.

## ⚠️ نکات مهم

1. API Key را در environment variables تنظیم کنید
2. نتایج AI باید همیشه بررسی شوند
3. کش برای کاهش هزینه‌ها فعال است
4. در صورت خطا، پیشنهادات پیش‌فرض استفاده می‌شوند

## 🎯 قابلیت‌های آینده

- یکپارچه‌سازی با سایر فرم‌ها (ریسک، حادثه، آنومالی)
- یادگیری از اقدامات قبلی
- پیشنهادات شخصی‌سازی شده بر اساس تاریخچه
- پشتیبانی از چندین زبان
