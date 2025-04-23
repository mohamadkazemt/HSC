# سیستم مدیریت جلسات

این سیستم برای مدیریت جلسات و ارسال نوتیفیکیشن به کاربران طراحی شده است.

## ویژگی‌ها

- ثبت جلسات با اطلاعات کامل
- ارسال نوتیفیکیشن به تمام کاربران سیستم
- ارسال پیامک یادآوری به شرکت‌کنندگان
- ارسال پیامک به هماهنگ‌کننده سرویس ایاب و ذهاب
- گزارش‌گیری از جلسات
- مدیریت دسترسی‌ها

## پیش‌نیازها

- Python 3.8+
- Django 4.2+
- Redis
- Celery
- Kavenegar API (برای ارسال پیامک)

## نصب

1. نصب پکیج‌های مورد نیاز:
```bash
pip install -r requirements.txt
```

2. تنظیم متغیرهای محیطی در فایل `settings.py`:
```python
# تنظیمات ایمیل
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'

# تنظیمات Kavenegar
KAVENEGAR_API_KEY = 'your-api-key'
```

3. اجرای مایگریشن‌ها:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. ایجاد گروه هماهنگ‌کننده سرویس:
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import Group
Group.objects.create(name='transport_coordinator')
```

5. اجرای سرور Redis:
```bash
redis-server
```

6. اجرای Celery:
```bash
celery -A project worker -l info
```

7. اجرای Celery Beat برای زمان‌بندی تسک‌ها:
```bash
celery -A project beat -l info
```

8. اجرای سرور Django:
```bash
python manage.py runserver
```

## استفاده

1. ورود به سیستم با حساب کاربری دارای دسترسی مناسب
2. ایجاد جلسه جدید از طریق فرم مربوطه
3. مشاهده لیست جلسات و گزارش‌ها
4. دریافت نوتیفیکیشن‌ها و پیامک‌های یادآوری

## دسترسی‌ها

- `meetings.add_meeting`: ایجاد جلسه جدید
- `meetings.view_meeting`: مشاهده جلسات
- `meetings.change_meeting`: ویرایش جلسات
- `meetings.delete_meeting`: حذف جلسات

## نکات مهم

- برای ارسال پیامک، نیاز به API Key از سرویس Kavenegar دارید
- برای ارسال ایمیل، نیاز به تنظیمات SMTP مناسب دارید
- گروه `transport_coordinator` باید از قبل ایجاد شده باشد
- سرور Redis باید در حال اجرا باشد
- Celery و Celery Beat باید در حال اجرا باشند 