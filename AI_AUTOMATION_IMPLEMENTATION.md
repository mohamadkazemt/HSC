# پیاده‌سازی خودکارسازی اقدامات اصلاحی با AI

## ✅ کارهای انجام شده

### 1. سرویس خودکارسازی (`corrective_actions/ai_automation.py`)
- کلاس `CorrectiveActionAutomation` برای خودکارسازی
- متد `create_corrective_action_from_anomaly`: ایجاد اقدام اصلاحی از آنومالی با AI
- متد `create_corrective_action_from_risk`: ایجاد اقدام اصلاحی از ریسک با AI
- متد `generate_control_measures_from_risk`: تولید 5 اقدام کنترلی با AI
- تولید خودکار شماره اقدام (tracking_code)

### 2. Celery Tasks (`corrective_actions/tasks.py`)
- `check_unresolved_anomalies`: بررسی آنومالی‌های رفع نشده (5 روز)
- `check_high_risk_assessments`: بررسی ریسک‌های زرد و قرمز
- ارسال اعلان به مسئولان
- مدیریت خطا و retry

### 3. تنظیمات Celery Beat (`HSCprojects/settings/base.py`)
- `check_unresolved_anomalies`: هر روز ساعت 6 صبح
- `check_high_risk_assessments`: هر روز ساعت 7 صبح

### 4. بهبود AI Helper (`corrective_actions/ai_helper.py`)
- بهبود `_get_risk_context` برای دریافت اطلاعات کامل ریسک
- پشتیبانی از اقدامات کنترلی (5 مورد)

## 🔄 فرآیند خودکارسازی

### برای آنومالی‌ها:
1. **بررسی روزانه**: هر روز ساعت 6 صبح
2. **فیلتر**: آنومالی‌های ناایمن (`action=False`) که بیش از 5 روز از ایجاد آنها گذشته
3. **AI**: تولید خودکار محتوا (شرح، علل ریشه‌ای، مراحل اقدام)
4. **ایجاد**: ایجاد اقدام اصلاحی با تمام جزئیات
5. **اعلان**: ارسال اعلان به مسئول پیگیری

### برای ریسک‌ها:
1. **بررسی روزانه**: هر روز ساعت 7 صبح
2. **فیلتر**: ریسک‌های زرد (RPN: 5-12) و قرمز (RPN >= 15) که تأیید شده‌اند
3. **AI - اقدامات کنترلی**: تولید 5 اقدام کنترلی (حذف، جایگزینی، مهندسی، اداری، PPE)
4. **AI - اقدام اصلاحی**: تولید محتوای اقدام اصلاحی
5. **ایجاد**: ایجاد اقدام اصلاحی با مراحل اقدام بر اساس اقدامات کنترلی
6. **به‌روزرسانی**: به‌روزرسانی ریسک با شماره اقدام و مهلت
7. **اعلان**: ارسال اعلان به مسئول ریسک

## 📋 اقدامات کنترلی تولید شده با AI

برای هر ریسک، AI این 5 اقدام را پیشنهاد می‌دهد:

1. **حذف خطر (Elimination)**: حذف کامل خطر
2. **جایگزینی (Substitution)**: جایگزین کردن با چیز کم‌خطرتر
3. **کنترل مهندسی (Engineering)**: کنترل‌های فنی و مهندسی
4. **کنترل اداری (Administrative)**: دستورالعمل‌ها، آموزش، تابلوها
5. **لوازم حفاظت فردی (PPE)**: تجهیزات حفاظت شخصی

این اقدامات:
- در فیلدهای ریسک ذخیره می‌شوند
- به عنوان مراحل اقدام در اقدام اصلاحی استفاده می‌شوند
- مهلت‌های متفاوتی دارند (7، 10، 13، 16، 19 روز)

## 🚀 نحوه استفاده

### راه‌اندازی:

1. **اجرای Celery Beat**:
```bash
celery -A HSCprojects beat -l info
```

2. **اجرای Celery Worker**:
```bash
celery -A HSCprojects worker -l info
```

### تست دستی:

```python
from corrective_actions.ai_automation import CorrectiveActionAutomation
from anomalis.models import Anomaly
from risk_assessment.models import RiskAssessment

automation = CorrectiveActionAutomation()

# تست برای آنومالی
anomaly = Anomaly.objects.filter(action=False).first()
action = automation.create_corrective_action_from_anomaly(anomaly)

# تست برای ریسک
risk = RiskAssessment.objects.filter(risk_number__gte=5).first()
action = automation.create_corrective_action_from_risk(risk)
```

## 📁 فایل‌های ایجاد شده

- `corrective_actions/ai_automation.py` - سرویس خودکارسازی
- `corrective_actions/tasks.py` - Celery tasks

## ⚙️ تنظیمات

### تغییر تعداد روزهای مجاز برای آنومالی:
در `check_unresolved_anomalies` task، می‌توانید `days_threshold` را تغییر دهید (پیش‌فرض: 5)

### تغییر زمان اجرا:
در `HSCprojects/settings/base.py`، زمان‌بندی Celery Beat را تغییر دهید:
```python
'check_unresolved_anomalies': {
    'task': 'corrective_actions.tasks.check_unresolved_anomalies',
    'schedule': crontab(hour=6, minute=0),  # تغییر ساعت
},
```

## ⚠️ نکات مهم

1. **AI باید فعال باشد**: مطمئن شوید که AI Service فعال است و API Key تنظیم شده است
2. **Celery باید اجرا شود**: Beat و Worker باید در حال اجرا باشند
3. **اعلان‌ها**: اعلان‌ها به مسئولان ارسال می‌شوند
4. **عدم تکرار**: سیستم از ایجاد اقدام اصلاحی تکراری جلوگیری می‌کند

## 🎯 نتیجه

سیستم به صورت خودکار:
- آنومالی‌های رفع نشده را شناسایی می‌کند
- ریسک‌های بالا را شناسایی می‌کند
- با استفاده از AI اقدامات اصلاحی ایجاد می‌کند
- اقدامات کنترلی پیشنهادی تولید می‌کند
- اعلان‌ها را ارسال می‌کند

همه این کارها به صورت خودکار و هوشمند انجام می‌شود! 🚀
