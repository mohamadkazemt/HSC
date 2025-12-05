# راهنمای استفاده از هوش مصنوعی در فرم اقدام اصلاحی

## 📋 خلاصه

سیستم اقدام اصلاحی اکنون از قابلیت هوش مصنوعی برای خودکارسازی پر کردن فرم‌ها استفاده می‌کند. این قابلیت می‌تواند بر اساس اطلاعات آنومالی، حادثه، یا ریسک مرتبط، پیشنهادات هوشمند برای پر کردن فرم ارائه دهد.

## 🚀 راه‌اندازی

### 1. تنظیم API Key

برای استفاده از هوش مصنوعی، باید API Key مربوط به سرویس AI را تنظیم کنید.

#### استفاده از OpenAI:

```bash
# در فایل .env یا environment variables
export AI_API_KEY="sk-your-openai-api-key"
export AI_API_BASE_URL="https://api.openai.com/v1"
export AI_MODEL="gpt-4"  # یا "gpt-3.5-turbo"
export AI_PROVIDER="openai"
```

#### استفاده از Anthropic Claude:

```bash
export AI_API_KEY="sk-ant-your-anthropic-api-key"
export AI_API_BASE_URL="https://api.anthropic.com/v1"
export AI_MODEL="claude-3-opus-20240229"
export AI_PROVIDER="anthropic"
```

#### استفاده از API محلی (Ollama):

```bash
export AI_API_KEY=""  # برای API محلی نیاز نیست
export AI_API_BASE_URL="http://localhost:11434/v1"
export AI_MODEL="llama2"  # یا مدل‌های دیگر
export AI_PROVIDER="local"
```

### 2. نصب وابستگی‌ها

کتابخانه `requests` که برای ارتباط با API استفاده می‌شود، احتمالاً قبلاً نصب شده است. در صورت نیاز:

```bash
pip install requests
```

## 💡 نحوه استفاده

### در فرم ایجاد اقدام اصلاحی:

1. **کمک هوش مصنوعی کامل**: 
   - دکمه "کمک هوش مصنوعی" در بالای فرم را کلیک کنید
   - سیستم به صورت خودکار تمام فیلدهای فرم را بر اساس اطلاعات مرتبط (آنومالی، حادثه، ریسک) پر می‌کند
   - شامل:
     - نوع اقدام
     - موضوع
     - ورودی عدم انطباق
     - شرح عدم انطباق
     - تحلیل علل ریشه‌ای
     - مراحل اقدام (با مهلت)
     - ریسک‌های ناشی از اقدام

2. **تولید تحلیل علل ریشه‌ای**:
   - ابتدا شرح عدم انطباق را وارد کنید
   - روی دکمه "تولید تحلیل علل ریشه‌ای" کنار فیلد شرح کلیک کنید
   - سیستم به صورت خودکار تحلیل علل ریشه‌ای را تولید می‌کند

## 🔧 تنظیمات پیشرفته

### تنظیمات در `settings/base.py`:

```python
# Timeout برای درخواست‌های AI (ثانیه)
AI_TIMEOUT = 30

# تعداد تلاش مجدد در صورت خطا
AI_MAX_RETRIES = 3

# زمان کش نتایج (ثانیه) - 1 ساعت پیش‌فرض
AI_CACHE_TIMEOUT = 3600
```

### غیرفعال کردن کش:

برای غیرفعال کردن کش در یک درخواست خاص، از پارامتر `use_cache=False` استفاده کنید:

```python
from core.ai_service import get_ai_service

ai_service = get_ai_service()
result = ai_service.generate_text(
    prompt="...",
    use_cache=False
)
```

## 📝 API Endpoints

### 1. تولید پیشنهادات کامل

**URL**: `/corrective-actions/api/ai/generate-suggestions/`

**Method**: POST

**Headers**:
- `Content-Type: application/json`
- `X-CSRFToken: <csrf-token>`

**Body**:
```json
{
    "related_anomaly_id": 123,  // اختیاری
    "related_incident_id": 456,  // اختیاری
    "related_risk_id": 789,  // اختیاری
    "user_description": "شرح اضافی"  // اختیاری
}
```

**Response**:
```json
{
    "success": true,
    "suggestions": {
        "action_type": "corrective",
        "topic": "hse",
        "source": "inspection",
        "description": "شرح عدم انطباق...",
        "root_cause_analysis": "تحلیل علل ریشه‌ای...",
        "action_steps": [
            {
                "description": "اقدام 1",
                "deadline_days": 7,
                "deadline": "2024-01-15",
                "deadline_jalali": "1402/10/25"
            }
        ],
        "side_effect_risks": [
            {
                "hazard": "خطر",
                "event": "رویداد",
                "consequence": "پیامد",
                "control_measure": "اقدام کنترلی"
            }
        ]
    }
}
```

### 2. تولید تحلیل علل ریشه‌ای

**URL**: `/corrective-actions/api/ai/generate-root-cause/`

**Method**: POST

**Body**:
```json
{
    "description": "شرح عدم انطباق"
}
```

**Response**:
```json
{
    "success": true,
    "root_cause_analysis": "تحلیل علل ریشه‌ای..."
}
```

## 🛠️ استفاده در کد Python

### استفاده مستقیم از AI Helper:

```python
from corrective_actions.ai_helper import CorrectiveActionAIHelper

ai_helper = CorrectiveActionAIHelper()

# تولید داده‌های کامل
suggestions = ai_helper.generate_corrective_action_data(
    related_anomaly_id=123,
    related_incident_id=None,
    related_risk_id=None,
    user_description="شرح اضافی"
)

# تولید تحلیل علل ریشه‌ای
root_cause = ai_helper.generate_root_cause_analysis(
    description="شرح عدم انطباق"
)

# تولید مراحل اقدام
action_steps = ai_helper.generate_action_steps(
    description="شرح عدم انطباق",
    root_cause="علل ریشه‌ای"
)
```

### استفاده مستقیم از AI Service:

```python
from core.ai_service import get_ai_service

ai_service = get_ai_service()

# تولید متن
text = ai_service.generate_text(
    prompt="سوال شما",
    system_prompt="دستورالعمل سیستم",
    temperature=0.7
)

# تولید JSON
data = ai_service.generate_json(
    prompt="درخواست JSON",
    system_prompt="دستورالعمل",
    temperature=0.3
)
```

## ⚠️ نکات مهم

1. **هزینه API**: استفاده از APIهای هوش مصنوعی ممکن است هزینه‌بر باشد. کش نتایج برای کاهش هزینه‌ها فعال است.

2. **کیفیت نتایج**: نتایج تولید شده توسط AI باید همیشه توسط کاربر بررسی و در صورت نیاز ویرایش شوند.

3. **امنیت**: API Key را هرگز در کد قرار ندهید. از environment variables استفاده کنید.

4. **خطاها**: در صورت خطا در ارتباط با API، سیستم به صورت خودکار از پیشنهادات پیش‌فرض استفاده می‌کند.

## 🔍 عیب‌یابی

### خطا: "API Key تنظیم نشده است"

**راه حل**: مطمئن شوید که `AI_API_KEY` در environment variables تنظیم شده است.

### خطا: "خطا در ارتباط با سرور"

**راه حل**: 
- بررسی کنید که API Base URL صحیح است
- برای API محلی (Ollama)، مطمئن شوید که سرویس در حال اجرا است
- بررسی کنید که firewall یا proxy مانع ارتباط نمی‌شود

### نتایج نامناسب

**راه حل**:
- دما (temperature) را کاهش دهید (مثلاً از 0.7 به 0.3)
- دستورالعمل سیستم (system prompt) را بهبود دهید
- اطلاعات context بیشتری ارائه دهید

## 📚 منابع بیشتر

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/)
- [Ollama Documentation](https://ollama.ai/docs)
