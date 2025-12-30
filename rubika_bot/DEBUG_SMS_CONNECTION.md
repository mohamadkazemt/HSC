# راهنمای بررسی لاگ‌های اتصال SMS

این راهنما به شما کمک می‌کند تا مشکل اتصال SMS را تشخیص دهید.

## روش 1: استفاده از دستور مدیریتی (توصیه می‌شود)

### بررسی یک کاربر خاص

```bash
python manage.py debug_sms_connection --national-code 3090886375 --personnel-code 110326
```

این دستور:
- کاربر را با کد ملی و کد پرسنلی جستجو می‌کند
- اطلاعات کاربر را نمایش می‌دهد
- لاگ‌های مربوطه را بررسی می‌کند

### بررسی SMS برای یک شماره موبایل

```bash
python manage.py debug_sms_connection --mobile 09123456789
```

یا:

```bash
python manage.py debug_sms_connection --mobile 9123456789
```

### نمایش آخرین لاگ‌های خطا

```bash
python manage.py debug_sms_connection --last 50
```

این دستور آخرین 50 لاگ خطا را نمایش می‌دهد.

### بررسی لاگ‌های چند ساعت گذشته

```bash
python manage.py debug_sms_connection --last 20 --hours 12
```

این دستور آخرین 20 لاگ خطا در 12 ساعت گذشته را نمایش می‌دهد.

## روش 2: استفاده از پنل وب

### مشاهده Webhook Logs

1. به آدرس زیر بروید:
   ```
   /rubika-bot/settings/webhook-logs/
   ```

2. یا از منوی تنظیمات ربات، روی "مشاهده لاگ‌ها" کلیک کنید.

3. می‌توانید لاگ‌ها را بر اساس نوع فیلتر کنید:
   - همه لاگ‌ها
   - فقط خطاها
   - فقط پیام‌های دریافتی
   - فقط پیام‌های ارسالی

### مشاهده SMS Logs

1. به پنل ادمین Django بروید
2. به بخش "Dashboard" > "SMS Logs" بروید
3. لاگ‌های SMS را مشاهده کنید

## روش 3: استفاده از Django Shell

### بررسی کاربر در Shell

```python
python manage.py shell

from accounts.models import UserProfile
from rubika_bot.services import normalize_digits
from django.db.models import Q

national_code = "3090886375"
personnel_code = "110326"

# Normalize
national_code_norm = normalize_digits(national_code)
personnel_code_norm = normalize_digits(personnel_code)

# جستجو
profile = UserProfile.objects.filter(
    Q(national_code=national_code_norm) | Q(national_code=national_code),
    Q(personnel_code=personnel_code_norm) | Q(personnel_code=personnel_code)
).select_related('user').first()

if profile:
    print(f"کاربر یافت شد: {profile.user.username}")
    print(f"کد ملی در DB: {profile.national_code}")
    print(f"کد پرسنلی در DB: {profile.personnel_code}")
    print(f"شماره موبایل: {profile.mobile}")
else:
    print("کاربر یافت نشد")
```

### بررسی Webhook Logs

```python
from rubika_bot.models import WebhookLog
from django.utils import timezone
from datetime import timedelta

# آخرین 20 لاگ خطا
errors = WebhookLog.objects.filter(
    log_type='error',
    created_at__gte=timezone.now() - timedelta(hours=24)
).order_by('-created_at')[:20]

for error in errors:
    print(f"[{error.created_at}] {error.title}")
    print(f"  {error.message}")
    print(f"  داده: {error.data}")
    print()
```

### بررسی SMS Logs

```python
from dashboard.models_sms import SMSLog
from django.utils import timezone
from datetime import timedelta

mobile = "09123456789"

# Normalize mobile
mobile_norm = normalize_digits(mobile)
if not mobile_norm.startswith('0'):
    if mobile_norm.startswith('98'):
        mobile_norm = '0' + mobile_norm[2:]
    elif len(mobile_norm) == 10:
        mobile_norm = '0' + mobile_norm

# جستجو
logs = SMSLog.objects.filter(
    mobile_number__in=[mobile, mobile_norm]
).order_by('-created_at')[:10]

for log in logs:
    print(f"[{log.created_at}] {log.status}")
    print(f"  شماره: {log.mobile_number}")
    print(f"  قالب: {log.template_id}")
    if log.error_message:
        print(f"  خطا: {log.error_message}")
    print()
```

## مشکلات رایج و راه‌حل

### مشکل 1: "کاربری با این کد ملی و کد پرسنلی یافت نشد"

**علل احتمالی:**
- کد ملی یا کد پرسنلی اشتباه است
- کدها در دیتابیس به صورت فارسی ذخیره شده‌اند
- کد ملی در فیلد `username` ذخیره شده است

**راه‌حل:**
1. با دستور `debug_sms_connection` بررسی کنید
2. بررسی کنید که کدها در دیتابیس به چه فرمتی هستند
3. اگر کدها فارسی هستند، باید normalize شوند

### مشکل 2: "خطا در ارسال پیامک"

**علل احتمالی:**
- شماره موبایل نامعتبر است
- Rate limiting فعال است
- مشکل در سرویس SMS
- شماره موبایل normalize نشده است

**راه‌حل:**
1. بررسی SMS logs برای یافتن دلیل دقیق
2. بررسی کنید که شماره موبایل به فرمت صحیح است (09123456789)
3. بررسی rate limiting

### مشکل 3: "شماره موبایل برای این کاربر ثبت نشده است"

**راه‌حل:**
1. در پنل ادمین، به پروفایل کاربر بروید
2. شماره موبایل را وارد کنید
3. دوباره تلاش کنید

## نکات مهم

1. **همیشه از normalize استفاده کنید**: کدهای فارسی باید به انگلیسی تبدیل شوند
2. **شماره موبایل باید با 0 شروع شود**: 09123456789 نه 9123456789
3. **لاگ‌ها را مرتب بررسی کنید**: برای تشخیص سریع مشکل
4. **Rate limiting را در نظر بگیرید**: ممکن است به حد مجاز رسیده باشید

## دستورات مفید

```bash
# بررسی یک کاربر
python manage.py debug_sms_connection --national-code 3090886375 --personnel-code 110326

# بررسی SMS برای یک شماره
python manage.py debug_sms_connection --mobile 09123456789

# آخرین 50 لاگ خطا
python manage.py debug_sms_connection --last 50

# لاگ‌های 12 ساعت گذشته
python manage.py debug_sms_connection --last 20 --hours 12
```

