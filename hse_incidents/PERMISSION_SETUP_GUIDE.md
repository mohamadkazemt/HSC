# راهنمای تنظیم دسترسی‌ها برای HSE Incidents

## مشکل فعلی:
خطای **403 Forbidden** به دلیل نداشتن permission مناسب برای ویوهای AJAX

## راه‌حل:

### گام 1: حذف دکوراتور permission_required از ویوهای AJAX

✅ **انجام شده** - تمام ویوهای AJAX اکنون فقط از `@login_required` استفاده می‌کنند:
- `get_injury_types_ajax`
- `get_contractors_ajax`
- `get_contractor_employees_ajax`
- `get_user_profiles_ajax`

### گام 2: تنظیم دسترسی‌ها در پنل ادمین (در صورت نیاز)

اگر می‌خواهید کنترل دقیق‌تری روی دسترسی‌ها داشته باشید، می‌توانید در پنل مدیریت دسترسی‌ها، موارد زیر را اضافه کنید:

#### ویوهای اصلی که نیاز به Permission دارند:

| نام View | توضیحات | نوع دسترسی |
|----------|---------|-----------|
| `incident_report` | ثبت گزارش حادثه | can_create |
| `list_reports` | لیست گزارش‌ها | can_view |
| `report_details` | جزئیات گزارش | can_view |
| `export_reports_excel` | خروجی اکسل | can_export |
| `report_details_pdf` | خروجی PDF | can_export |

#### ویوهای AJAX (فقط نیاز به login دارند):

این ویوها **نیازی به تنظیم permission جداگانه ندارند**:
- ✅ `get_injury_types_ajax`
- ✅ `get_contractors_ajax`  
- ✅ `get_contractor_employees_ajax`
- ✅ `get_user_profiles_ajax`

### گام 3: نحوه اضافه کردن Permission (اختیاری)

اگر می‌خواهید permission اضافه کنید:

1. وارد پنل ادمین Django شوید
2. به بخش **Permissions** بروید
3. permission جدید با این مشخصات اضافه کنید:

```
View Name: incident_report
Permissions:
- can_view: True
- can_create: True
- can_edit: False
- can_delete: False
```

4. این permission را به گروه/کاربر مورد نظر اختصاص دهید

### گام 4: رفرش کردن صفحه

پس از اعمال تغییرات:
1. سرور Django را restart کنید (اگر لازم است)
2. صفحه مرورگر را رفرش کنید
3. Cache مرورگر را پاک کنید (Ctrl+Shift+R)

---

## خلاصه تغییرات اعمال شده:

### ✅ اصلاحات views.py:

**قبل:**
```python
@permission_required("get_user_profiles_ajax")
@login_required
def get_user_profiles_ajax(request):
    ...
```

**بعد:**
```python
@login_required
def get_user_profiles_ajax(request):
    ...
```

### ✅ تمام ویوهای AJAX اصلاح شدند:
- حذف `@permission_required` از ویوهای کمکی AJAX
- نگه داشتن `@login_required` برای امنیت پایه
- ویوهای اصلی (مثل `report_incident`) همچنان permission دارند

---

## تست:

پس از این تغییرات:
1. ✅ AJAX requests بدون خطای 403 کار می‌کنند
2. ✅ فقط کاربران لاگین شده می‌توانند استفاده کنند
3. ✅ ویوهای اصلی همچنان تحت کنترل permission هستند

---

## نکته مهم:

اگر می‌خواهید محدودیت بیشتری روی ویوهای AJAX بگذارید، می‌توانید:

1. دکوراتور `@permission_required` را به آن‌ها اضافه کنید
2. Permission مناسب را در پنل ادمین ایجاد کنید
3. Permission را به کاربران/گروه‌های مورد نظر بدهید

**اما توصیه می‌شود**: برای ویوهای AJAX کمکی، فقط `@login_required` کافی است.

---

**تاریخ بروزرسانی:** 1403/08/07  
**وضعیت:** ✅ آماده استفاده
