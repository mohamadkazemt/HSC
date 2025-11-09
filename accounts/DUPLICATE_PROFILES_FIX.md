# راهنمای حل مشکل پروفایل‌های تکراری

## مشکل

خطای زیر هنگام آپلود فیش حقوقی رخ می‌دهد:

```
get() returned more than one UserProfile -- it returned 2!
```

این خطا زمانی رخ می‌دهد که دو یا چند `UserProfile` با یک `personnel_code` (کد پرسنلی) در دیتابیس وجود داشته باشد.

## علت

- `UserProfile` باید رابطه `OneToOneField` با `User` داشته باشد
- اما `personnel_code` ممکن است تکراری باشد
- هنگام جستجو با `UserProfile.objects.get(personnel_code=...)` اگر چند رکورد وجود داشته باشد، خطا رخ می‌دهد

## راه‌حل

### مرحله 1: شناسایی پروفایل‌های تکراری

برای مشاهده لیست پروفایل‌های تکراری:

```bash
python manage.py fix_duplicate_profiles --list
```

خروجی نمونه:

```
⚠️ تعداد 1 کد پرسنلی با پروفایل‌های تکراری یافت شد:

📋 کد پرسنلی: 111264 (2 پروفایل)
  1. ID=45, User=ahmad.rezaei (احمد رضایی), Payslips=3
  2. ID=78, User=ahmad.rezaei2 (احمد رضایی), Payslips=0
```

### مرحله 2: اصلاح خودکار

برای حذف پروفایل‌های تکراری و نگه‌داشتن اولین مورد:

```bash
python manage.py fix_duplicate_profiles --fix
```

این دستور:
- اولین پروفایل (با کمترین ID) را نگه می‌دارد
- فیش‌های حقوقی از پروفایل‌های تکراری را به پروفایل اصلی منتقل می‌کند
- پروفایل‌های تکراری را حذف می‌کند

### مرحله 3: بررسی نتیجه

بعد از اجرای دستور، دوباره لیست را بررسی کنید:

```bash
python manage.py fix_duplicate_profiles --list
```

باید پیام زیر را ببینید:

```
✅ هیچ پروفایل تکراری یافت نشد!
```

## اصلاح کد آپلود فیش

کد `batch_payslip_upload` در `accounts/views.py` به‌روزرسانی شده تا خطای `MultipleObjectsReturned` را هندل کند:

```python
try:
    user_profile = UserProfile.objects.get(personnel_code=personnel_code)
except UserProfile.DoesNotExist:
    # جستجوی با الگوهای دیگر
    ...
except UserProfile.MultipleObjectsReturned:
    # اگر چند پروفایل وجود دارد، اولین مورد را انتخاب می‌کنیم
    user_profile = UserProfile.objects.filter(personnel_code=personnel_code).first()
    errors.append(f"⚠️ فایل {filename}: چند پروفایل با کد '{personnel_code}' یافت شد. اولین مورد انتخاب شد.")
```

## پیشگیری از تکرار در آینده

### 1. اضافه کردن Unique Constraint

در `accounts/models.py`:

```python
class UserProfile(models.Model):
    personnel_code = models.CharField(
        max_length=10, 
        default='', 
        blank=True, 
        unique=True,  # اضافه کردن این خط
        verbose_name='کد پرسنلی'
    )
```

سپس migration ایجاد کنید:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. بررسی در Admin Panel

در `accounts/admin.py` می‌توانید یک action برای یافتن تکراری‌ها اضافه کنید:

```python
@admin.action(description='بررسی کدهای پرسنلی تکراری')
def check_duplicate_codes(modeladmin, request, queryset):
    from django.db.models import Count
    duplicates = (
        UserProfile.objects
        .values('personnel_code')
        .annotate(count=Count('id'))
        .filter(count__gt=1, personnel_code__isnull=False)
        .exclude(personnel_code='')
    )
    if duplicates:
        codes = [d['personnel_code'] for d in duplicates]
        modeladmin.message_user(
            request,
            f"⚠️ کدهای تکراری: {', '.join(codes)}",
            level='WARNING'
        )
    else:
        modeladmin.message_user(request, "✅ هیچ کد تکراری یافت نشد")
```

## بررسی دستی

برای بررسی دستی در Django shell:

```python
python manage.py shell

from accounts.models import UserProfile
from django.db.models import Count

# یافتن کدهای تکراری
duplicates = (
    UserProfile.objects
    .values('personnel_code')
    .annotate(count=Count('id'))
    .filter(count__gt=1, personnel_code__isnull=False)
    .exclude(personnel_code='')
)

for dup in duplicates:
    code = dup['personnel_code']
    profiles = UserProfile.objects.filter(personnel_code=code)
    print(f"\nکد {code}:")
    for p in profiles:
        print(f"  - ID={p.id}, User={p.user.username if p.user else 'None'}")
```

## سوالات متداول

### ❓ چرا پروفایل‌های تکراری ایجاد شده‌اند؟

ممکن است:
- Import داده از فایل Excel/CSV بدون بررسی تکراری
- ایجاد دستی پروفایل‌ها در admin panel
- مشکل در migration ها
- عدم وجود constraint در دیتابیس

### ❓ آیا حذف پروفایل‌های تکراری امن است؟

بله، اسکریپت `fix_duplicate_profiles`:
- فقط پروفایل‌های اضافی را حذف می‌کند
- فیش‌های حقوقی را به پروفایل اصلی منتقل می‌کند
- از حذف داده جلوگیری می‌کند

### ❓ اگر هر دو پروفایل فیش داشته باشند چه؟

اسکریپت:
- فیش‌های هر دو پروفایل را به پروفایل اصلی منتقل می‌کند
- اگر فیش تکراری برای یک ماه وجود داشته باشد، یکی را نگه می‌دارد

### ❓ چگونه مطمئن شوم مشکل حل شده؟

1. دستور `--list` را اجرا کنید
2. سعی کنید فیش حقوقی آپلود کنید
3. خطا نباید دیگر رخ دهد

## لاگ‌ها

تمام عملیات اسکریپت لاگ می‌شوند:

```bash
# مشاهده لاگ‌های Django
tail -f logs/django.log

# مشاهده لاگ‌های Celery
sudo journalctl -u celery.service -f
```

## پشتیبان‌گیری

قبل از اجرای `--fix`، حتماً از دیتابیس پشتیبان بگیرید:

```bash
# PostgreSQL
pg_dump dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# MySQL
mysqldump -u user -p dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

## تست

بعد از اصلاح:

1. آپلود فیش حقوقی از پنل ادمین
2. دریافت فیش از ربات روبیکا
3. دانلود فیش از پنل کاربری

همه باید بدون خطا کار کنند.

---

**تاریخ ایجاد:** 1404/08/18

**نسخه:** 1.0.0

