# نحوه تعیین زمان موعد چک‌لیست‌های برنامه‌ریزی شده

## خلاصه

زمان موعد (due_date) چک‌لیست‌های برنامه‌ریزی شده به صورت **خودکار** توسط سیستم تعیین می‌شود. این فرآیند شامل مراحل زیر است:

## 1. تعریف برنامه زمان‌بندی (ChecklistSchedule)

در Django Admin، یک `ChecklistSchedule` ایجاد می‌کنید که مشخص می‌کند:
- **نوع برنامه‌ریزی**: 
  - `monthly_days`: روزهای مشخص ماه (مثلاً 1 و 15 هر ماه)
  - `specific_dates`: تاریخ‌های مشخص (مثلاً ["2024-12-25", "2025-01-01"])
  - `weekly`: هفتگی (مثلاً هر دوشنبه)

- **هدف**: ماشین، مکان، یا خودرو پیمانکار مشخص

## 2. ایجاد خودکار Instances (نمونه‌ها)

### روش 1: Celery Beat (توصیه می‌شود)

یک Celery task به صورت **خودکار هر روز ساعت 00:00** اجرا می‌شود و instances را برای **امروز و 30 روز آینده** ایجاد می‌کند.

**تنظیمات در `HSCprojects/settings/base.py`:**
```python
CELERY_BEAT_SCHEDULE = {
    'create_scheduled_checklist_instances': {
        'task': 'checklist_app.tasks.create_scheduled_checklist_instances',
        'schedule': crontab(hour=0, minute=0),  # هر روز ساعت 00:00
    },
}
```

**برای فعال‌سازی:**
```bash
# اجرای Celery Beat
celery -A HSCprojects beat -l info
```

### روش 2: Management Command (دستی)

می‌توانید به صورت دستی یا با cron job اجرا کنید:

```bash
# ایجاد instances برای امروز و 7 روز آینده
python manage.py create_scheduled_instances --days-ahead 7

# ایجاد instances برای تاریخ مشخص
python manage.py create_scheduled_instances --date 2024-12-25

# ایجاد instances برای امروز و 30 روز آینده
python manage.py create_scheduled_instances --days-ahead 30
```

**برای cron job (Linux/Mac):**
```bash
# هر روز ساعت 00:00
0 0 * * * cd /path/to/project && /path/to/venv/bin/python manage.py create_scheduled_instances --days-ahead 30
```

**برای Windows Task Scheduler:**
- ایجاد یک task که هر روز ساعت 00:00 اجرا شود
- Command: `python manage.py create_scheduled_instances --days-ahead 30`

## 3. منطق تعیین زمان موعد

### برای `monthly_days`:
```python
# اگر schedule.monthly_days = [1, 15]
# و امروز = 2024-12-15
# → یک instance با due_date = 2024-12-15 ایجاد می‌شود

# اگر امروز = 2024-12-20
# → هیچ instance ایجاد نمی‌شود (چون 20 در لیست نیست)

# در 1 ژانویه 2025
# → یک instance با due_date = 2025-01-01 ایجاد می‌شود
```

### برای `specific_dates`:
```python
# اگر schedule.specific_dates = ["2024-12-25", "2025-01-01"]
# و امروز = 2024-12-25
# → یک instance با due_date = 2024-12-25 ایجاد می‌شود

# اگر امروز = 2024-12-26
# → هیچ instance ایجاد نمی‌شود
```

### برای `weekly`:
```python
# اگر schedule.schedule_type = 'weekly'
# و امروز = دوشنبه (weekday = 0)
# → یک instance با due_date = امروز ایجاد می‌شود
```

## 4. نمایش چک‌لیست‌های آینده

کاربران می‌توانند چک‌لیست‌های آینده را در صفحه زیر مشاهده کنند:

**URL:** `/checklist_app/upcoming-scheduled/`

این صفحه:
- تمام چک‌لیست‌های برنامه‌ریزی شده تا 30 روز آینده را نشان می‌دهد
- بر اساس تاریخ گروه‌بندی شده است
- وضعیت هر instance (pending/completed) را نمایش می‌دهد
- لینک مستقیم برای شروع چک‌لیست‌های در انتظار دارد

## 5. مثال عملی

### سناریو: چک‌لیست ماهانه ماشین

1. **ایجاد Schedule:**
   - نام: "چک‌لیست ماهانه ماشین A"
   - نوع: `monthly_days`
   - روزهای ماه: `[1, 15]`
   - هدف: ماشین A

2. **اجرای Task (هر روز ساعت 00:00):**
   - 1 دسامبر 2024: instance با `due_date = 2024-12-01` ایجاد می‌شود
   - 15 دسامبر 2024: instance با `due_date = 2024-12-15` ایجاد می‌شود
   - 1 ژانویه 2025: instance با `due_date = 2025-01-01` ایجاد می‌شود

3. **نمایش برای کاربر:**
   - در صفحه "چک‌لیست‌های در انتظار": instances با `status='pending'` و `due_date <= today`
   - در صفحه "چک‌لیست‌های آینده": تمام instances تا 30 روز آینده

## نکات مهم

1. **Instances فقط یک بار ایجاد می‌شوند**: اگر instance برای یک تاریخ و schedule وجود داشته باشد، دوباره ایجاد نمی‌شود (unique constraint)

2. **پیش‌بینی آینده**: سیستم instances را برای 30 روز آینده ایجاد می‌کند تا کاربران بتوانند برنامه‌ریزی کنند

3. **به‌روزرسانی خودکار**: هر روز task اجرا می‌شود و instances جدید برای تاریخ‌های آینده ایجاد می‌کند

4. **مدیریت دستی**: می‌توانید instances را در Django Admin مشاهده و مدیریت کنید

## عیب‌یابی

### مشکل: Instances ایجاد نمی‌شوند

**بررسی کنید:**
1. آیا `ChecklistSchedule` فعال است؟ (`is_active=True`)
2. آیا Celery Beat در حال اجرا است؟
3. آیا تاریخ امروز با تنظیمات schedule مطابقت دارد؟
4. لاگ‌های Celery را بررسی کنید

### مشکل: Instances تکراری ایجاد می‌شوند

این مشکل نباید رخ دهد چون `unique_together = ('schedule', 'due_date')` در مدل تعریف شده است.

### مشکل: Instances برای تاریخ‌های گذشته ایجاد نمی‌شوند

این رفتار عادی است. سیستم فقط instances برای امروز و آینده ایجاد می‌کند. برای تاریخ‌های گذشته باید به صورت دستی ایجاد کنید.

## دستورات مفید

```bash
# بررسی instances ایجاد شده
python manage.py shell
>>> from checklist_app.models import ScheduledChecklistInstance
>>> ScheduledChecklistInstance.objects.filter(status='pending').count()

# ایجاد instances برای یک ماه کامل
python manage.py create_scheduled_instances --days-ahead 31

# تست task به صورت دستی
python manage.py shell
>>> from checklist_app.tasks import create_scheduled_checklist_instances
>>> create_scheduled_checklist_instances()
```

