# تست سریع Tasks

## ✅ وضعیت فعلی

Tasks در Celery Worker ثبت شده‌اند:
- ✅ `corrective_actions.tasks.check_unresolved_anomalies`
- ✅ `corrective_actions.tasks.check_high_risk_assessments`

## 🎯 چرا در Beat خروجی نیست؟

Beat فقط زمانی task را می‌فرستد که زمان schedule آن رسیده باشد:
- `check_unresolved_anomalies`: ساعت 6 صبح
- `check_high_risk_assessments`: ساعت 7 صبح

اگر الان بعد از ظهر است، Beat هیچ taskی نمی‌فرستد.

## 🚀 تست دستی Tasks

### روش 1: از Django Shell

```python
python manage.py shell

from corrective_actions.tasks import check_unresolved_anomalies, check_high_risk_assessments

# تست آنومالی‌ها
result = check_unresolved_anomalies(days_threshold=5)
print(f"✓ بررسی شده: {result['checked_count']}")
print(f"✓ ایجاد شده: {result['created_count']}")

# تست ریسک‌ها
result = check_high_risk_assessments()
print(f"✓ بررسی شده: {result['checked_count']}")
print(f"✓ ایجاد شده: {result['created_count']}")
```

### روش 2: از Celery CLI

```bash
cd /var/www/HSC
source venv/bin/activate

# تست task آنومالی‌ها
celery -A HSCprojects call corrective_actions.tasks.check_unresolved_anomalies --kwargs '{"days_threshold": 5}'

# تست task ریسک‌ها
celery -A HSCprojects call corrective_actions.tasks.check_high_risk_assessments
```

### روش 3: از Python مستقیماً

```python
python manage.py shell

from corrective_actions.tasks import check_unresolved_anomalies, check_high_risk_assessments

# اجرای مستقیم (بدون Celery)
result = check_unresolved_anomalies.apply(args=[5]).get()
print(result)

result = check_high_risk_assessments.apply().get()
print(result)
```

## ⏰ تغییر Schedule برای تست سریع

اگر می‌خواهید tasks را زودتر تست کنید، می‌توانید schedule را موقتاً تغییر دهید:

```python
# در HSCprojects/settings/base.py
# موقتاً برای تست:
'check_unresolved_anomalies': {
    'task': 'corrective_actions.tasks.check_unresolved_anomalies',
    'schedule': crontab(minute='*/5'),  # هر 5 دقیقه (برای تست)
    'options': {'expires': 3600}
},
'check_high_risk_assessments': {
    'task': 'corrective_actions.tasks.check_high_risk_assessments',
    'schedule': crontab(minute='*/5'),  # هر 5 دقیقه (برای تست)
    'options': {'expires': 3600}
},
```

**⚠️ مهم**: بعد از تست، schedule را به حالت اصلی برگردانید:
- `check_unresolved_anomalies`: `crontab(hour=6, minute=0)`
- `check_high_risk_assessments`: `crontab(hour=7, minute=0)`

## 📊 بررسی نتایج

بعد از اجرای tasks:

```python
python manage.py shell

from corrective_actions.models import CorrectiveAction
from django.utils import timezone
from datetime import timedelta

# بررسی اقدامات اصلاحی ایجاد شده در 24 ساعت گذشته
recent_actions = CorrectiveAction.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=24)
)

print(f"✓ اقدامات اصلاحی ایجاد شده: {recent_actions.count()}")

for action in recent_actions:
    print(f"  - {action.tracking_code}")
    print(f"    آنومالی: {action.related_anomaly_id if action.related_anomaly else 'ندارد'}")
    print(f"    ریسک: {action.related_risk_id if action.related_risk else 'ندارد'}")
    print(f"    مراحل: {action.action_steps.count()}")
    print(f"    ریسک‌های ناشی از اقدام: {action.side_effect_risks.count()}")
```

## 🔍 بررسی لاگ‌های Beat

برای دیدن اینکه Beat چه زمانی task می‌فرستد:

```bash
# بررسی لاگ‌های Beat
sudo journalctl -u celery-beat.service -f

# یا فقط خطوط مربوط به Scheduler
sudo journalctl -u celery-beat.service | grep "Scheduler: Sending"
```

## ✅ خلاصه

1. ✅ Tasks ثبت شده‌اند
2. ✅ Worker در حال اجرا است
3. ✅ Beat در حال اجرا است
4. ⏰ Tasks در زمان مقرر (6 و 7 صبح) اجرا می‌شوند
5. 🧪 می‌توانید دستی تست کنید

همه چیز درست کار می‌کند! 🎉

