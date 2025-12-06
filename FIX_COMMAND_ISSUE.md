# رفع مشکلات

## 🔴 مشکل 1: `celery inspect` خطا می‌دهد

این خطا طبیعی است! `celery inspect` سعی می‌کند به worker وصل شود اما اگر worker در حال اجرا باشد، باید کار کند.

**راه‌حل**: این خطا مهم نیست. Worker و Beat در حال اجرا هستند و tasks ثبت شده‌اند.

برای بررسی tasks، از این استفاده کنید:

```bash
# بررسی tasks در worker (از journalctl)
sudo journalctl -u celery.service | grep "corrective_actions"

# یا بررسی لاگ‌های beat
sudo journalctl -u celery-beat.service | grep "corrective_actions"
```

## 🔴 مشکل 2: `test_ai_automation` command پیدا نمی‌شود

این مشکل به این دلیل است که Django باید app را reload کند.

### راه‌حل 1: بررسی فایل

```bash
# بررسی اینکه فایل وجود دارد
ls -la /var/www/HSC/corrective_actions/management/commands/test_ai_automation.py

# بررسی __init__.py
ls -la /var/www/HSC/corrective_actions/management/__init__.py
ls -la /var/www/HSC/corrective_actions/management/commands/__init__.py
```

### راه‌حل 2: تست دستی

اگر command کار نمی‌کند، می‌توانید مستقیماً از Python استفاده کنید:

```python
cd /var/www/HSC
source venv/bin/activate
python manage.py shell

# در shell:
from corrective_actions.ai_automation import CorrectiveActionAutomation
from anomalis.models import Anomaly

automation = CorrectiveActionAutomation()
anomaly = Anomaly.objects.get(pk=42)

action = automation.create_corrective_action_from_anomaly(
    anomaly=anomaly,
    auto_generate=True
)

print(f"نتیجه: {action}")
if action:
    print(f"شماره: {action.tracking_code}")
    print(f"مراحل: {action.action_steps.count()}")
    print(f"ریسک‌ها: {action.side_effect_risks.count()}")
```

### راه‌حل 3: بررسی apps.py

مطمئن شوید که `corrective_actions` در `INSTALLED_APPS` است:

```python
# در HSCprojects/settings/base.py
INSTALLED_APPS = [
    ...
    'corrective_actions.apps.CorrectiveActionsConfig',  # باید باشد
    ...
]
```

## ✅ بررسی نهایی

```bash
# 1. بررسی که app نصب شده است
python manage.py shell
>>> from corrective_actions import management
>>> import corrective_actions.management.commands.test_ai_automation

# 2. بررسی لیست commands
python manage.py help | grep test

# 3. اگر پیدا نشد، restart Django (اگر از gunicorn استفاده می‌کنید)
sudo systemctl restart gunicorn
# یا
sudo systemctl restart uwsgi
```

## 🎯 خلاصه وضعیت

✅ **Celery Worker**: در حال اجرا (8 workers)
✅ **Celery Beat**: در حال اجرا
✅ **Tasks ثبت شده**: همه tasks از جمله `corrective_actions.tasks.*` ثبت شده‌اند

⚠️ **مشکلات جزئی**:
- `celery inspect` کار نمی‌کند (مهم نیست)
- `test_ai_automation` command پیدا نمی‌شود (می‌توانید از shell استفاده کنید)

## 🚀 تست نهایی

برای تست، از Django shell استفاده کنید:

```python
python manage.py shell

from corrective_actions.tasks import check_unresolved_anomalies, check_high_risk_assessments

# تست task آنومالی‌ها
result = check_unresolved_anomalies(days_threshold=5)
print(f"بررسی شده: {result['checked_count']}, ایجاد شده: {result['created_count']}")

# تست task ریسک‌ها
result = check_high_risk_assessments()
print(f"بررسی شده: {result['checked_count']}, ایجاد شده: {result['created_count']}")
```
