# راهنمای تست خودکارسازی اقدامات اصلاحی

## 🧪 روش‌های تست

### روش 1: استفاده از Django Management Command (پیشنهادی)

این روش ساده‌ترین و بهترین روش برای تست است.

#### نصب:
فایل‌های لازم در `corrective_actions/management/commands/test_ai_automation.py` ایجاد شده‌اند.

#### استفاده:

```bash
# تست پیش‌فرض (آنومالی و ریسک)
python manage.py test_ai_automation

# تست با آنومالی خاص
python manage.py test_ai_automation --anomaly-id 1

# تست با ریسک خاص
python manage.py test_ai_automation --risk-id 5

# ایجاد داده‌های تست
python manage.py test_ai_automation --create-test-data

# اجرای Celery Tasks
python manage.py test_ai_automation --run-tasks
```

---

### روش 2: استفاده از Django Shell

#### گام 1: باز کردن Django Shell
```bash
python manage.py shell
```

#### گام 2: اجرای کد تست

```python
# تست برای آنومالی
from corrective_actions.ai_automation import CorrectiveActionAutomation
from anomalis.models import Anomaly

automation = CorrectiveActionAutomation()

# پیدا کردن یک آنومالی ناایمن
anomaly = Anomaly.objects.filter(action=False).first()

if anomaly:
    print(f"آنومالی پیدا شد: #{anomaly.id}")
    action = automation.create_corrective_action_from_anomaly(
        anomaly=anomaly,
        auto_generate=True
    )
    if action:
        print(f"✓ اقدام اصلاحی ایجاد شد: {action.tracking_code}")
        print(f"  - تعداد مراحل: {action.action_steps.count()}")
```

```python
# تست برای ریسک
from corrective_actions.ai_automation import CorrectiveActionAutomation
from risk_assessment.models import RiskAssessment

automation = CorrectiveActionAutomation()

# پیدا کردن یک ریسک زرد یا قرمز
risk = RiskAssessment.objects.filter(
    risk_number__gte=5,
    approval_status='approved'
).first()

if risk:
    print(f"ریسک پیدا شد: #{risk.id}, RPN: {risk.risk_number}")
    
    # تولید اقدامات کنترلی
    control_measures = automation.generate_control_measures_from_risk(risk)
    print(f"✓ {len(control_measures)} اقدام کنترلی تولید شد")
    
    # ایجاد اقدام اصلاحی
    action = automation.create_corrective_action_from_risk(
        risk=risk,
        auto_generate=True
    )
    if action:
        print(f"✓ اقدام اصلاحی ایجاد شد: {action.tracking_code}")
        print(f"  - تعداد مراحل: {action.action_steps.count()}")
```

---

### روش 3: اجرای فایل تست

```bash
# روش 1: اجرا در shell
python manage.py shell < corrective_actions/test_automation.py

# روش 2: در Django shell
python manage.py shell
>>> exec(open('corrective_actions/test_automation.py').read())
```

---

### روش 4: تست Celery Tasks

#### گام 1: اجرای Celery Worker
```bash
celery -A HSCprojects worker -l info
```

#### گام 2: اجرای Celery Beat (برای زمان‌بندی)
```bash
celery -A HSCprojects beat -l info
```

#### گام 3: تست دستی Task

```python
# در Django shell
from corrective_actions.tasks import check_unresolved_anomalies, check_high_risk_assessments

# تست task آنومالی‌ها
result = check_unresolved_anomalies(days_threshold=5)
print(f"بررسی شده: {result['checked_count']}, ایجاد شده: {result['created_count']}")

# تست task ریسک‌ها
result = check_high_risk_assessments()
print(f"بررسی شده: {result['checked_count']}, ایجاد شده: {result['created_count']}")
```

---

## 📋 چک‌لیست تست

### قبل از تست:
- [ ] AI Service فعال است و API Key تنظیم شده است
- [ ] می‌توانید به AI API دسترسی داشته باشید
- [ ] حداقل یک آنومالی ناایمن در سیستم وجود دارد
- [ ] حداقل یک ریسک زرد یا قرمز تأیید شده در سیستم وجود دارد

### تست‌های پیشنهادی:

#### ✅ تست 1: تست سرویس خودکارسازی
```bash
python manage.py test_ai_automation
```

#### ✅ تست 2: ایجاد داده‌های تست
```bash
python manage.py test_ai_automation --create-test-data
```

#### ✅ تست 3: تست با آنومالی خاص
```bash
python manage.py test_ai_automation --anomaly-id 1
```

#### ✅ تست 4: تست با ریسک خاص
```bash
python manage.py test_ai_automation --risk-id 5
```

#### ✅ تست 5: تست Celery Tasks
```bash
python manage.py test_ai_automation --run-tasks
```

---

## 🔍 بررسی نتایج

### بررسی اقدام اصلاحی ایجاد شده:

```python
from corrective_actions.models import CorrectiveAction

# آخرین اقدام اصلاحی
action = CorrectiveAction.objects.order_by('-id').first()

print(f"شماره: {action.tracking_code}")
print(f"نوع: {action.get_action_type_display()}")
print(f"موضوع: {action.get_topic_display()}")
print(f"شرح: {action.description}")
print(f"علل ریشه‌ای: {action.root_cause_analysis}")
print(f"تعداد مراحل: {action.action_steps.count()}")

# نمایش مراحل
for step in action.action_steps.all():
    print(f"  - {step.description}")
    print(f"    مهلت: {step.deadline}")
```

### بررسی اقدامات کنترلی در ریسک:

```python
from risk_assessment.models import RiskAssessment

risk = RiskAssessment.objects.get(pk=1)

print(f"حذف خطر: {risk.control_elimination}")
print(f"جایگزینی: {risk.control_substitution}")
print(f"کنترل مهندسی: {risk.control_engineering}")
print(f"کنترل اداری: {risk.control_admin}")
print(f"PPE: {risk.control_ppe}")
```

---

## 🐛 عیب‌یابی

### مشکل: AI کار نمی‌کند
- بررسی کنید که API Key درست تنظیم شده است
- بررسی کنید که AI Service فعال است (`core.ai_models.AISettings`)
- لاگ‌ها را بررسی کنید: `logs/application.log`

### مشکل: هیچ آنومالی/ریسکی پیدا نمی‌شود
- مطمئن شوید که داده‌های تست وجود دارند
- از `--create-test-data` استفاده کنید
- بررسی کنید که فیلترها درست هستند

### مشکل: Celery Tasks کار نمی‌کند
- مطمئن شوید که Celery Worker در حال اجرا است
- بررسی کنید که Celery Beat در حال اجرا است
- لاگ‌های Celery را بررسی کنید

---

## 📊 بررسی لاگ‌ها

```bash
# لاگ‌های Django
tail -f logs/application.log

# لاگ‌های Celery
celery -A HSCprojects worker -l info --logfile=logs/celery.log
```

---

## ✅ تست موفق

اگر همه چیز درست کار کند، باید:
1. ✓ اقدام اصلاحی ایجاد شود
2. ✓ مراحل اقدام ایجاد شوند
3. ✓ اقدامات کنترلی در ریسک ذخیره شوند
4. ✓ اعلان‌ها ارسال شوند
5. ✓ لاگ‌ها بدون خطا باشند

---

## 🎯 نکات مهم

1. **تست در محیط Development**: همیشه ابتدا در محیط توسعه تست کنید
2. **بررسی API Key**: مطمئن شوید که API Key معتبر است
3. **محدودیت‌های API**: مراقب محدودیت‌های rate limit باشید
4. **لاگ‌ها**: همیشه لاگ‌ها را بررسی کنید
5. **داده‌های تست**: از داده‌های واقعی برای تست استفاده نکنید

---

## 📞 پشتیبانی

اگر مشکلی داشتید:
1. لاگ‌ها را بررسی کنید
2. تنظیمات AI را بررسی کنید
3. مطمئن شوید که همه وابستگی‌ها نصب شده‌اند
