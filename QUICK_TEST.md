# تست سریع خودکارسازی

## 🔍 مشکل فعلی

از خروجی ترمینال مشخص است که:
- ✓ آنومالی پیدا شد (#1)
- ✗ خطا در ایجاد اقدام اصلاحی

## 🧪 تست بدون AI (برای عیب‌یابی)

برای تست بدون استفاده از AI (اگر AI کار نمی‌کند):

```bash
python manage.py test_ai_automation --no-ai
```

یا برای آنومالی خاص:

```bash
python manage.py test_ai_automation --anomaly-id 1 --no-ai
```

## 🔍 بررسی خطا

برای دیدن جزئیات خطا، کد اصلاح شده است. حالا خطا را نمایش می‌دهد.

### روش 1: تست با نمایش خطا

```bash
python manage.py test_ai_automation --anomaly-id 1
```

### روش 2: بررسی لاگ‌ها

```bash
# در Windows PowerShell
Get-Content logs\application.log -Tail 50

# یا در CMD
type logs\application.log | more
```

### روش 3: تست در Django Shell

```python
python manage.py shell

from corrective_actions.ai_automation import CorrectiveActionAutomation
from anomalis.models import Anomaly

automation = CorrectiveActionAutomation()
anomaly = Anomaly.objects.get(pk=1)

# تست بدون AI
action = automation.create_corrective_action_from_anomaly(
    anomaly=anomaly,
    auto_generate=False  # بدون AI
)
print(f"نتیجه: {action}")
```

## ✅ چک‌لیست عیب‌یابی

1. **بررسی AI Service**:
   - آیا AI Service فعال است؟
   - آیا API Key تنظیم شده است؟
   - تست اتصال: `/ai-settings/` → دکمه "تست اتصال"

2. **بررسی داده‌ها**:
   - آیا آنومالی وجود دارد؟
   - آیا آنومالی ناایمن است (`action=False`)؟

3. **بررسی لاگ‌ها**:
   - خطاهای AI در `logs/application.log`
   - خطاهای Django در console

## 🎯 تست موفق

اگر همه چیز درست باشد، باید ببینید:
```
✓ اقدام اصلاحی ایجاد شد: CA-250122-001
  - نوع: اصلاحی
  - موضوع: ایمنی، بهداشت و محیط زیست
  - تعداد مراحل: 3
  - وضعیت: در حال اجرا
```

## 💡 نکته

اگر AI کار نمی‌کند، می‌توانید با `--no-ai` تست کنید تا ببینید آیا مشکل از AI است یا از کد.
