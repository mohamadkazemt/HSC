# تصحیح مشکل تاریخ انقضا و حذف خودکار داروهای منقضی

## 📋 مشکلات حل‌شده:

### ✅ 1. مشکل تاریخ انقضا برای داروهای جدید
**مشکل:** تاریخ انقضا برای داروهای جدید به‌درستی تبدیل نمی‌شد

**راه‌حل:**
- تبدیل بهتر تاریخ شمسی به میلادی با validation دقیق
- بررسی فرمت تاریخ (YYYY/MM/DD)
- بررسی صحت تاریخ شمسی قبل از تبدیل
- بررسی اینکه تاریخ انقضا در آینده باشد
- نمایش تاریخ میلادی به شکل شمسی در فرم

**فایل‌های تغییر‌یافته:**
- `emergency_services/forms.py` - بهبود `__init__` و `clean` در `MedicineForm`
- `emergency_services/views.py` - بهبود `api_medicine_save` با validation دقیق

### ✅ 2. حذف خودکار داروهای منقضی
**مشکل:** داروهای منقضی باقی می‌ماندند در سیستم

**راه‌حل:**
- Management command برای حذف دستی: `python manage.py cleanup_expired_medicines`
- سه Celery Task برای اتوماسیون:
  1. **cleanup_expired_medicines_task** - هر روز ساعت 2 صبح
  2. **check_medicine_stock_levels_task** - هر روز ساعت 8 صبح
  3. **mark_expired_medicines_inactive_task** - هر ساعت

**فایل‌های ایجاد‌شده:**
- `emergency_services/management/commands/cleanup_expired_medicines.py` - Management Command
- `emergency_services/tasks.py` - Celery Tasks

**فایل‌های تغییر‌یافته:**
- `HSCprojects/settings/base.py` - اضافه‌کردن Celery Beat Schedule

---

## 🔧 نحوه استفاده:

### 1. استفاده از Management Command

**حذف داروهای منقضی:**
```bash
python manage.py cleanup_expired_medicines
```

**تست بدون حذف واقعی:**
```bash
python manage.py cleanup_expired_medicines --dry-run
```

**حذف داروهایی که 7 روز پیش منقضی شده‌اند:**
```bash
python manage.py cleanup_expired_medicines --days 7
```

### 2. استفاده از Celery Tasks

**اجرای دستی یک Task:**
```python
from emergency_services.tasks import cleanup_expired_medicines_task
result = cleanup_expired_medicines_task.delay()
```

**Celery Beat برنامه‌ریزی خودکار:**

| Task | زمان اجرا | توصیف |
|------|----------|--------|
| cleanup_expired_medicines_task | هر روز 2 صبح | حذف داروهای منقضی |
| check_medicine_stock_levels_task | هر روز 8 صبح | بررسی موجودی بحرانی |
| mark_expired_medicines_inactive_task | هر ساعت | تعطیل کردن داروهای منقضی |

### 3. شروع Celery Worker و Beat:

```bash
# Celery Worker
celery -A HSCprojects worker -l info

# Celery Beat (Schedule)
celery -A HSCprojects beat -l info

# یا همزمان:
celery -A HSCprojects worker --beat -l info
```

---

## 🔍 بهبود‌های اضافی:

### ✨ فیلد تاریخ انقضا:
- تبدیل خودکار تاریخ شمسی به میلادی
- نمایش تاریخ میلادی به شکل شمسی در فرم ویرایش
- Validation دقیق و پیام‌های خطای واضح

### 📧 اطلاع‌رسانی‌های خودکار:
- اطلاع برای مدیران هنگام حذف داروهای منقضی
- اطلاع برای موجودی بحرانی (یک‌بار در روز)
- جلوگیری از اطلاع‌رسانی‌های تکراری

### 🛡️ Safety Features:
- `--dry-run` برای تست قبل از حذف
- Logging جزئی برای تمام عملیات
- Exception handling برای هر Task

---

## 📊 مثال‌های عملی:

### تست حذف داروهای منقضی:
```bash
$ python manage.py cleanup_expired_medicines --dry-run

============================================================
لیست داروهای منقضی:
============================================================
  • آسپرین - تاریخ انقضا: 2024-03-15 (نمایش فقط)
  • پنی‌سیلین - تاریخ انقضا: 2024-02-10 (نمایش فقط)

✓ این یک تست است - هیچ تغییری انجام نشده است
```

### حذف واقعی:
```bash
$ python manage.py cleanup_expired_medicines

============================================================
لیست داروهای منقضی:
============================================================
  • آسپرین - تاریخ انقضا: 2024-03-15 (حذف شود)
  • پنی‌سیلین - تاریخ انقضا: 2024-02-10 (حذف شود)

✓ 2 دارو منقضی با موفقیت حذف شد
✓ 3 مدیر مطلع شدند
```

---

## ⚙️ تنظیمات اضافی:

### تغییر زمان اجرای Tasks:

در `HSCprojects/settings/base.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'cleanup_expired_medicines': {
        'task': 'emergency_services.tasks.cleanup_expired_medicines_task',
        'schedule': crontab(hour=2, minute=0),  # ← تغییر دهید
    },
    'check_medicine_stock_levels': {
        'task': 'emergency_services.tasks.check_medicine_stock_levels_task',
        'schedule': crontab(hour=8, minute=0),  # ← تغییر دهید
    },
    'mark_expired_medicines_inactive': {
        'task': 'emergency_services.tasks.mark_expired_medicines_inactive_task',
        'schedule': crontab(minute=0),  # ← تغییر دهید
    },
}
```

---

## 🐛 Troubleshooting:

### مشکل: Celery Tasks اجرا نمی‌شوند
1. بررسی اینکه Celery Worker و Beat اجرا شده‌اند
2. بررسی PostgreSQL/Redis connection
3. چک کردن Celery Logs

### مشکل: تاریخ انقضا باز هم مشکل دارد
1. بررسی فرمت تاریخ (باید YYYY/MM/DD باشد)
2. بررسی اینکه سال شمسی درست باشد
3. بررسی Timezone تنظیمات

### مشکل: اطلاع‌رسانی‌ها ارسال نمی‌شوند
1. بررسی اینکه Group‌های مدیریت وجود دارند
2. بررسی Notification Model
3. بررسی Permissions

---

## 📝 Notes:

- تمام Tasks با proper logging کار می‌کنند
- تمام اطلاع‌رسانی‌ها به Dashboard ارسال می‌شوند
- تغییرات backward compatible هستند (تاثیری روی کد قدیم ندارد)
