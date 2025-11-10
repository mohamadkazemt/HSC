# راهنمای استقرار تغییرات روی سرور

## 🔧 تغییرات انجام شده

### 1. **فایل `HSCprojects/settings/base.py`**
```python
# قبل:
'rubika_bot',

# بعد:
'rubika_bot.apps.RubikaBotConfig',
```

**دلیل:** با این تغییر، `RubikaBotConfig.ready()` اجرا می‌شود و signal ها به درستی import می‌شوند.

### 2. **فایل `rubika_bot/signals.py`**
- افزودن logging کامل برای debug
- بهبود فرمت پیام‌های نوتیفیکیشن
- فیلتر کردن نوتیفیکیشن‌های با دکمه

### 3. **فایل `rubika_bot/tasks.py`**
- افزودن logging کامل برای debug
- Task جدید: `send_leave_approval_request`

### 4. **فایل `rubika_bot/services.py`**
- Handler های جدید برای تایید/رد درخواست‌ها
- پردازش دکمه‌های تایید/رد

### 5. **فایل `leave_reports/utils.py`**
- ارسال پیام با دکمه به ربات

---

## 📋 مراحل استقرار روی سرور

### مرحله 1: به‌روزرسانی کد

```bash
cd /var/www/HSC
git pull origin mkt
```

### مرحله 2: فعال‌سازی virtual environment

```bash
source venv/bin/activate
```

### مرحله 3: نصب وابستگی‌ها (در صورت نیاز)

```bash
pip install -r requirements.txt
```

### مرحله 4: اجرای migration ها (در صورت نیاز)

```bash
python manage.py migrate
```

### مرحله 5: جمع‌آوری فایل‌های static

```bash
python manage.py collectstatic --noinput
```

### مرحله 6: Restart سرویس‌ها

```bash
# Restart Django (Gunicorn یا uWSGI)
sudo systemctl restart gunicorn
# یا
sudo systemctl restart uwsgi

# Restart Celery
sudo systemctl restart celery.service

# بررسی وضعیت
sudo systemctl status gunicorn
sudo systemctl status celery.service
```

---

## 🔍 بررسی و عیب‌یابی

### 1. بررسی کاربران متصل به ربات

```bash
python manage.py shell
```

```python
from rubika_bot.models import RubikaUser

# تعداد کاربران متصل
connected = RubikaUser.objects.filter(user__isnull=False)
print(f"Connected users: {connected.count()}")

# لیست کاربران
for ru in connected:
    print(f"- {ru.user.username} (Chat ID: {ru.chat_id})")
```

**اگر 0 است:** هیچ کاربری به ربات متصل نیست!

### 2. اتصال کاربران به ربات

**مراحل برای کاربران:**

1. وارد پنل وب شوید
2. به بخش تنظیمات ربات بروید
3. کد اتصال را کپی کنید
4. در ربات روبیکا دستور زیر را ارسال کنید:
   ```
   /connect [کد]
   ```

### 3. تست ارسال نوتیفیکیشن

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from dashboard.models import Notification

# انتخاب یک کاربر متصل
user = User.objects.get(username='your_username')

# ایجاد نوتیفیکیشن تستی
Notification.objects.create(
    user=user,
    title='تست ربات',
    message='این یک پیام تستی است',
    notification_type='info'
)
```

**نتیجه مورد انتظار:** کاربر باید در چند ثانیه پیام را در ربات دریافت کند.

### 4. بررسی لاگ‌های Celery

```bash
# مشاهده لاگ‌های زنده
sudo journalctl -u celery.service -f

# مشاهده 100 خط آخر
sudo journalctl -u celery.service -n 100
```

**لاگ‌های مورد انتظار بعد از ایجاد نوتیفیکیشن:**

```
🔔 Signal triggered for notification 123, created=True
  👤 User: username, Has rubika_profile: True
  ✅ User has chat_id: c0123456789
  📤 Sending message to rubika (chat_id: c0123456789)
  ✅ Message queued successfully
📨 Task 'send_rubika_message' started for chat_id: c0123456789
   Message length: 85 characters
   Getting RubPyIntegrationService instance...
   ✅ Service instance obtained
   Sending message to c0123456789...
✅ Task 'send_rubika_message' successfully sent message to c0123456789.
```

### 5. بررسی لاگ‌های Django

```bash
# اگر لاگ به فایل می‌نویسد
tail -f /var/log/django/app.log

# یا اگر از syslog استفاده می‌کنید
sudo journalctl -u gunicorn -f
```

---

## 🐛 مشکلات احتمالی و راه حل

### مشکل 1: Signal اجرا نمی‌شود

**علامت:** نوتیفیکیشن ایجاد می‌شود اما پیامی به ربات ارسال نمی‌شود.

**راه حل:**
1. بررسی کنید که `rubika_bot.apps.RubikaBotConfig` در INSTALLED_APPS است
2. Django را restart کنید
3. لاگ‌ها را بررسی کنید

### مشکل 2: هیچ کاربری متصل نیست

**علامت:** `RubikaUser.objects.filter(user__isnull=False).count()` برابر 0 است.

**راه حل:**
1. بررسی کنید که webhook ربات تنظیم شده باشد
2. بررسی کنید که توکن ربات معتبر است
3. کاربران باید از طریق `/connect [کد]` به ربات متصل شوند

### مشکل 3: Celery task اجرا نمی‌شود

**علامت:** لاگ Celery تغییری نمی‌کند.

**راه حل:**
```bash
# Restart Celery
sudo systemctl restart celery.service

# بررسی وضعیت
sudo systemctl status celery.service

# بررسی error ها
sudo journalctl -u celery.service -n 50
```

### مشکل 4: پیام ارسال می‌شود اما کاربر دریافت نمی‌کند

**علامت:** لاگ می‌گوید "successfully sent" اما کاربر چیزی نمی‌بینید.

**راه حل:**
1. بررسی کنید که توکن ربات معتبر است
2. بررسی کنید که chat_id صحیح است
3. ممکن است کاربر ربات را block کرده باشد

---

## ✅ چک لیست نهایی

قبل از تست نهایی، اطمینان حاصل کنید:

- [ ] کد از git pull شده است
- [ ] Django restart شده است (`sudo systemctl restart gunicorn`)
- [ ] Celery restart شده است (`sudo systemctl restart celery.service`)
- [ ] حداقل یک کاربر به ربات متصل است
- [ ] Webhook ربات تنظیم شده است
- [ ] توکن ربات معتبر است

---

## 🧪 تست نهایی

### تست 1: نوتیفیکیشن ساده

```python
from django.contrib.auth.models import User
from dashboard.models import Notification

user = User.objects.first()  # یا username خاصی را انتخاب کنید
Notification.objects.create(
    user=user,
    title='تست سیستم',
    message='این یک پیام تستی است',
    notification_type='success'
)
```

### تست 2: درخواست مرخصی

1. وارد پنل وب شوید
2. یک درخواست مرخصی استحقاقی ثبت کنید
3. جانشین باید پیام با دکمه‌های تایید/رد دریافت کند
4. روی تایید کلیک کنید
5. مدیر باید پیام دریافت کند
6. درخواست‌دهنده باید نوتیفیکیشن‌های تایید را دریافت کند

---

## 📞 پشتیبانی

اگر مشکلی پیش آمد، لاگ‌های زیر را بررسی کنید:

```bash
# Celery logs
sudo journalctl -u celery.service -n 200 > celery_logs.txt

# Django logs
sudo journalctl -u gunicorn -n 200 > django_logs.txt

# یا اگر از uWSGI استفاده می‌کنید
sudo journalctl -u uwsgi -n 200 > django_logs.txt
```

و فایل‌های لاگ را ارسال کنید.
