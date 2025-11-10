# راهنمای سریع پیاده‌سازی نوتیفیکیشن 🚀

> **به‌روزرسانی مهم (آبان ۱۴۰۴):** قبل از ایجاد یا ویرایش اعلان جدید، ابتدا بخش «[NOTIFICATION_STYLE_GUIDE.md](NOTIFICATION_STYLE_GUIDE.md)» را مطالعه کنید تا لحن و ساختار پیام‌ها مطابق استاندارد جدید باشد. پس از اتمام توسعه نیز تست‌های پیشنهادی بخش «اجرای تست‌ها» در همین فایل را اجرا کنید.

## برای شروع سریع فاز 1 (anomalis)

### گام 1: ایجاد فایل notifications.py

در پوشه `anomalis` فایل `notifications.py` را بسازید:

```python
# anomalis/notifications.py
from dashboard.models import Notification
from django.urls import reverse

def notify_followup_new_anomaly(anomaly):
    """ارسال نوتیفیکیشن به مسئول پیگیری هنگام ثبت آنومالی جدید"""
    if anomaly.followup and anomaly.followup.user:
        Notification.objects.create(
            user=anomaly.followup.user,
            title='آنومالی جدید برای پیگیری',
            message=f'{anomaly.created_by.user.get_full_name()} آنومالی جدید در {anomaly.location} برای پیگیری شما ثبت کرد',
            notification_type='warning',
            url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
        )

def notify_creator_status_change(anomaly):
    """ارسال نوتیفیکیشن به ایجاد کننده هنگام تغییر وضعیت"""
    if anomaly.created_by and anomaly.created_by.user:
        status_text = 'رفع شد' if anomaly.action else 'رفع نشده'
        Notification.objects.create(
            user=anomaly.created_by.user,
            title='تغییر وضعیت آنومالی',
            message=f'وضعیت آنومالی شما در {anomaly.location} به "{status_text}" تغییر کرد',
            notification_type='success' if anomaly.action else 'info',
            url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
        )

def notify_new_comment(comment):
    """ارسال نوتیفیکیشن هنگام کامنت جدید"""
    anomaly = comment.anomaly
    
    # اطلاع به ایجاد کننده آنومالی (اگر کامنت از خودش نباشد)
    if anomaly.created_by.user != comment.user.user:
        Notification.objects.create(
            user=anomaly.created_by.user,
            title='کامنت جدید روی آنومالی',
            message=f'{comment.user.user.get_full_name()} روی آنومالی شما کامنت گذاشت',
            notification_type='info',
            url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
        )
    
    # اطلاع به مسئول پیگیری (اگر کامنت از خودش نباشد)
    if anomaly.followup and anomaly.followup.user != comment.user.user:
        Notification.objects.create(
            user=anomaly.followup.user,
            title='کامنت جدید روی آنومالی',
            message=f'{comment.user.user.get_full_name()} روی آنومالی در پیگیری شما کامنت گذاشت',
            notification_type='info',
            url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
        )

def notify_comment_reply(reply):
    """ارسال نوتیفیکیشن هنگام پاسخ به کامنت"""
    if reply.parent and reply.parent.user.user != reply.user.user:
        Notification.objects.create(
            user=reply.parent.user.user,
            title='پاسخ به کامنت شما',
            message=f'{reply.user.user.get_full_name()} به کامنت شما پاسخ داد',
            notification_type='info',
            url=reverse('anomalis:anomaly_detail', args=[reply.anomaly.id])
        )

def notify_high_priority_anomaly(anomaly):
    """ارسال نوتیفیکیشن به مدیران برای آنومالی‌های با اولویت بالا"""
    from django.contrib.auth.models import Group
    
    # فرض بر این که گروه "HSE_Manager" وجود دارد
    try:
        hse_group = Group.objects.get(name='HSE_Manager')
        managers = hse_group.user_set.all()
        
        for manager in managers:
            Notification.objects.create(
                user=manager,
                title='آنومالی فوری',
                message=f'آنومالی با اولویت {anomaly.priority} در {anomaly.location} ثبت شد',
                notification_type='error',
                url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
            )
    except Group.DoesNotExist:
        pass  # گروه وجود ندارد

def notify_anomaly_approval_request(anomaly):
    """ارسال نوتیفیکیشن برای درخواست تأیید آنومالی"""
    if anomaly.approved_by:
        Notification.objects.create(
            user=anomaly.approved_by,
            title='درخواست تأیید آنومالی',
            message=f'{anomaly.requested_by.get_full_name()} درخواست تأیید آنومالی در {anomaly.location} را دارد',
            notification_type='warning',
            url=reverse('anomalis:anomaly_detail', args=[anomaly.id])
        )
```

### گام 2: اضافه کردن به views.py

در فایل `anomalis/views.py`، نوتیفیکیشن‌ها را اضافه کنید:

```python
# در ابتدای فایل
from .notifications import (
    notify_followup_new_anomaly,
    notify_creator_status_change,
    notify_new_comment,
    notify_comment_reply,
    notify_high_priority_anomaly,
    notify_anomaly_approval_request
)

# در view ثبت آنومالی جدید:
def create_anomaly(request):
    # ... کد موجود ...
    if form.is_valid():
        anomaly = form.save()
        
        # ارسال نوتیفیکیشن‌ها
        notify_followup_new_anomaly(anomaly)
        
        # اگر اولویت بالاست
        if anomaly.priority.priority in ['فوری', 'بحرانی']:
            notify_high_priority_anomaly(anomaly)
        
        # اگر درخواست تأیید دارد
        if anomaly.is_request_sent:
            notify_anomaly_approval_request(anomaly)
        
        messages.success(request, 'آنومالی با موفقیت ثبت شد')
        return redirect('anomalis:anomaly_detail', pk=anomaly.id)

# در view تغییر وضعیت:
def update_anomaly_status(request, pk):
    anomaly = get_object_or_404(Anomaly, pk=pk)
    old_status = anomaly.action
    
    # ... کد تغییر وضعیت ...
    
    if old_status != anomaly.action:
        notify_creator_status_change(anomaly)
    
    # ... بقیه کد ...

# در view ثبت کامنت:
def add_comment(request, anomaly_id):
    # ... کد موجود ...
    if form.is_valid():
        comment = form.save(commit=False)
        comment.anomaly_id = anomaly_id
        comment.save()
        
        # ارسال نوتیفیکیشن
        if comment.parent:
            notify_comment_reply(comment)
        else:
            notify_new_comment(comment)
        
        messages.success(request, 'کامنت شما ثبت شد')
        return redirect('anomalis:anomaly_detail', pk=anomaly_id)
```

### گام 3: تست

1. یک آنومالی جدید ثبت کنید
2. به حساب کاربری مسئول پیگیری وارد شوید
3. بررسی کنید که نوتیفیکیشن نمایش داده می‌شود

---

## چک لیست پیاده‌سازی برای هر اپ

### ✅ قبل از شروع

- [ ] مطالعه فایل `NOTIFICATION_ANALYSIS.md`
- [ ] شناسایی viewها و modelهای مرتبط
- [ ] تعیین کاربران مخاطب برای هر نوتیفیکیشن
- [ ] بررسی URLهای موجود برای لینک نوتیفیکیشن

### 📝 در حین پیاده‌سازی

- [ ] ایجاد فایل `notifications.py` در اپ
- [ ] نوشتن توابع کمکی برای هر نوع نوتیفیکیشن
- [ ] import توابع در `views.py`
- [ ] اضافه کردن فراخوانی نوتیفیکیشن‌ها
- [ ] تست دستی هر نوتیفیکیشن
- [ ] بررسی لینک‌ها و محتوای پیام‌ها

### 🧪 بعد از پیاده‌سازی

- [ ] تست با داده‌های واقعی
- [ ] بررسی عملکرد با چند کاربر
- [ ] تست edge caseها (کاربر حذف شده، null values و غیره)
- [ ] بررسی عدم ایجاد نوتیفیکیشن تکراری
- [ ] مستندسازی تغییرات

---

## نکات مهم 🎯

### 1. مدیریت خطا
همیشه از try-except استفاده کنید:

```python
def notify_user(user, message):
    try:
        Notification.objects.create(...)
    except Exception as e:
        logger.error(f"خطا در ارسال نوتیفیکیشن: {e}")
        # نوتیفیکیشن نباید باعث خرابی سیستم شود
```

### 2. بررسی null
همیشه قبل از ارسال نوتیفیکیشن، کاربر را چک کنید:

```python
if anomaly.followup and anomaly.followup.user:
    # ارسال نوتیفیکیشن
```

### 3. جلوگیری از spam
از ارسال نوتیفیکیشن به خود کاربر خودداری کنید:

```python
if comment.user.user != anomaly.created_by.user:
    # ارسال نوتیفیکیشن
```

### 4. URL صحیح
همیشه URLهای کامل با namespace استفاده کنید:

```python
url=reverse('app_name:view_name', args=[object_id])
```

### 5. نوع مناسب
| نوع | کاربرد | رنگ |
|-----|--------|-----|
| `error` | خطر، حادثه، مشکل فوری | قرمز |
| `warning` | نیاز به اقدام، هشدار | زرد |
| `info` | اطلاع‌رسانی عادی | آبی |
| `success` | تأیید، موفقیت | سبز |

---

## مثال کامل: hse_incidents

```python
# hse_incidents/notifications.py
from dashboard.models import Notification
from django.urls import reverse
from django.contrib.auth.models import Group

def notify_incident_reported(incident):
    """اطلاع به مدیران HSE هنگام ثبت حادثه"""
    try:
        # دریافت گروه‌های مرتبط
        hse_group = Group.objects.get(name='HSE_Manager')
        security_group = Group.objects.get(name='Security_Manager')
        
        managers = list(hse_group.user_set.all()) + list(security_group.user_set.all())
        
        for manager in managers:
            Notification.objects.create(
                user=manager,
                title='حادثه جدید ثبت شد',
                message=f'حادثه در {incident.location} - {incident.section} گزارش شد. نیاز به پیگیری فوری',
                notification_type='error',
                url=reverse('hse_incidents:incident_detail', args=[incident.id])
            )
    except Group.DoesNotExist:
        pass
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"خطا در ارسال نوتیفیکیشن حادثه: {e}")

def notify_incident_with_injury(incident):
    """اطلاع فوری برای حوادث با آسیب جسمی"""
    try:
        # دریافت مدیران ارشد
        senior_managers = Group.objects.get(name='Senior_Management').user_set.all()
        hse_managers = Group.objects.get(name='HSE_Manager').user_set.all()
        legal_dept = Group.objects.get(name='Legal_Department').user_set.all()
        
        all_managers = list(senior_managers) + list(hse_managers) + list(legal_dept)
        
        injury_types = ', '.join([inj.name for inj in incident.injury_type.all()])
        
        for manager in all_managers:
            Notification.objects.create(
                user=manager,
                title='🚨 حادثه با آسیب جسمی',
                message=f'حادثه با آسیب جسمی ({injury_types}) در {incident.location}. نیاز به اقدام فوری',
                notification_type='error',
                url=reverse('hse_incidents:incident_detail', args=[incident.id])
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"خطا در ارسال نوتیفیکیشن آسیب جسمی: {e}")
```

---

## پشتیبانی و سوالات ❓

- برای سوالات فنی به فایل `NOTIFICATION_ANALYSIS.md` مراجعه کنید
- برای مثال‌های کامل به پوشه `leave_reports` نگاه کنید
- برای تست، از فایل `TESTING_GUIDE.md` در `leave_reports` استفاده کنید

---

**به‌روزرسانی**: 1403/08/20  
**نسخه**: 1.0

