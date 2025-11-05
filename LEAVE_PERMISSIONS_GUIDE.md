# 🔐 راهنمای تعریف دسترسی‌های مرخصی

## 📋 دسترسی‌های مورد نیاز

برای اینکه کاربران بتوانند منوهای مرخصی را ببینند، باید این دسترسی‌ها را در پنل مدیریت تعریف کنید:

### 1️⃣ درخواست مرخصی
**نام دسترسی:** `request_leave`
- **توضیح:** دسترسی به صفحه ثبت درخواست مرخصی جدید
- **URL:** `/leave_reports/request/`

### 2️⃣ آرشیو مرخصی‌ها
**نام دسترسی:** `leave_archive`
- **توضیح:** دسترسی به صفحه مشاهده و جستجوی تمام درخواست‌های مرخصی
- **URL:** `/leave_reports/archive/`

### 3️⃣ مدیریت تأییدکنندگان (فقط superuser)
- **توضیح:** فقط کاربران superuser می‌توانند تأییدکنندگان را مدیریت کنند
- **URL:** `/leave_reports/manage-approvers/`

---

## 🎯 نحوه تعریف دسترسی‌ها

### مرحله 1: ورود به پنل مدیریت دسترسی‌ها
```
http://localhost:8000/permissions/view-list/
```

### مرحله 2: افزودن دسترسی جدید
برای هر یک از دسترسی‌های زیر:

#### دسترسی 1: درخواست مرخصی
1. روی "افزودن View" کلیک کنید
2. فیلدها را پر کنید:
   - **View Name:** `request_leave`
   - **Label (فارسی):** `درخواست مرخصی`
   - **App Name:** `leave_reports`
   - **Category:** `مدیریت مرخصی`

#### دسترسی 2: آرشیو مرخصی
1. روی "افزودن View" کلیک کنید
2. فیلدها را پر کنید:
   - **View Name:** `leave_archive`
   - **Label (فارسی):** `آرشیو مرخصی‌ها`
   - **App Name:** `leave_reports`
   - **Category:** `مدیریت مرخصی`

---

## 👥 نحوه اختصاص دسترسی به کاربران

### روش 1: دسترسی مستقیم به کاربر
```
1. به پنل دسترسی‌ها بروید
2. "User Permissions" را انتخاب کنید
3. کاربر مورد نظر را انتخاب کنید
4. دسترسی‌های زیر را اضافه کنید:
   ✅ request_leave (با can_add, can_view)
   ✅ leave_archive (با can_view)
```

### روش 2: دسترسی بر اساس بخش (Section)
```
1. "Section Permissions" را انتخاب کنید
2. بخش مورد نظر (مثلاً "واحد اداری") را انتخاب کنید
3. دسترسی‌ها را اضافه کنید
4. تمام کاربران آن بخش دسترسی خواهند داشت
```

### روش 3: دسترسی بر اساس سمت (Position)
```
1. "Position Permissions" را انتخاب کنید
2. سمت مورد نظر (مثلاً "کارمند") را انتخاب کنید
3. دسترسی‌ها را اضافه کنید
4. تمام کاربران با آن سمت دسترسی خواهند داشت
```

---

## ✅ بررسی دسترسی

### چک کردن دسترسی کاربر:
1. با حساب کاربری لاگین کنید
2. Sidebar را باز کنید
3. به **واحد اداری → مدیریت مرخصی** بروید
4. باید منوهایی که دسترسی دارید را ببینید

### اگر منو نمایش داده نشد:
- ✅ مطمئن شوید که دسترسی‌ها را با نام دقیق `request_leave` و `leave_archive` ایجاد کرده‌اید
- ✅ چک کنید که دسترسی به کاربر/بخش/سمت اختصاص داده شده است
- ✅ صفحه را Refresh کنید (F5)
- ✅ Logout کنید و دوباره Login کنید

---

## 🎭 مثال عملی

### مثال: دادن دسترسی به یک کارمند

#### گام 1: تعریف دسترسی‌ها (اگر تعریف نشده‌اند)
```
View Name: request_leave
Label: درخواست مرخصی
App: leave_reports
```

```
View Name: leave_archive
Label: آرشیو مرخصی‌ها
App: leave_reports
```

#### گام 2: اختصاص به کاربر
```
User: ali_ahmadi
Permissions:
  - request_leave (can_add: ✓, can_view: ✓)
  - leave_archive (can_view: ✓)
```

#### گام 3: تست
1. Login با حساب ali_ahmadi
2. Sidebar → واحد اداری → مدیریت مرخصی
3. باید 2 منو ببیند:
   - ✅ درخواست مرخصی
   - ✅ آرشیو مرخصی‌ها

---

## 🔧 عیب‌یابی

### مشکل: منوها نمایش داده نمی‌شوند

**راه‌حل 1:** بررسی نام دسترسی‌ها
```bash
# در shell Django:
python manage.py shell

from permissions.models import View
views = View.objects.filter(name__in=['request_leave', 'leave_archive'])
for v in views:
    print(f"{v.name} - {v.label}")

# باید نتیجه بدهد:
# request_leave - درخواست مرخصی
# leave_archive - آرشیو مرخصی‌ها
```

**راه‌حل 2:** بررسی دسترسی کاربر
```python
# در shell:
from django.contrib.auth.models import User
from permissions.utils import check_permission

user = User.objects.get(username='YOUR_USERNAME')
print(check_permission(user, 'request_leave'))  # باید True باشد
print(check_permission(user, 'leave_archive'))  # باید True باشد
```

**راه‌حل 3:** پاک کردن cache
```bash
# اگر از cache استفاده می‌کنید:
python manage.py shell
from django.core.cache import cache
cache.clear()
```

---

## 📊 جدول دسترسی‌های پیشنهادی

| نقش کاربر | request_leave | leave_archive | manage_approvers |
|-----------|---------------|---------------|------------------|
| کارمند عادی | ✅ can_add, can_view | ✅ can_view | ❌ |
| سرپرست | ✅ can_add, can_view | ✅ can_view, can_edit | ❌ |
| مدیر HR | ✅ can_add, can_view | ✅ همه | ✅ (via superuser) |
| مدیر ارشد | ✅ can_add, can_view | ✅ همه | ✅ (via superuser) |

---

## 🎉 نتیجه

بعد از تعریف و اختصاص صحیح دسترسی‌ها:
- ✅ کاربران فقط منوهایی که دسترسی دارند را می‌بینند
- ✅ سیستم امن و کنترل شده است
- ✅ مدیریت دسترسی‌ها از پنل admin قابل انجام است
- ✅ نیازی به تغییر کد نیست

---

**توجه:** اگر هنوز مشکل دارید، مطمئن شوید که:
1. Template tag `check_permission` به درستی کار می‌کند
2. File `permissions/templatetags/permission_tags.py` وجود دارد
3. سرور را Restart کرده‌اید بعد از تغییرات
