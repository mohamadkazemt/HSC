# راهنمای کامل پیاده‌سازی سیستم مدیریت مرخصی

## ✅ کارهای انجام شده

### 1. بک‌اند (Backend)
- ✅ مدل‌ها بازطراحی شدند (`ShiftReport` و `ApprovalHierarchy`)
- ✅ Migration ها ایجاد و اجرا شدند
- ✅ فرم‌های جامع ایجاد شدند (LeaveRequestForm, RejectLeaveForm, ApprovalHierarchyForm, LeaveSearchForm)
- ✅ View های کامل با منطق تأیید/رد پیاده‌سازی شدند
- ✅ URL های جدید تعریف شدند
- ✅ Admin panel به‌روزرسانی شد

### 2. فایل‌های ایجاد شده
- `/home/mohamadkazem/HSC/leave_reports/models.py` - بازطراحی کامل
- `/home/mohamadkazem/HSC/leave_reports/forms.py` - فرم‌های جدید
- `/home/mohamadkazem/HSC/leave_reports/views_new.py` - View های جدید
- `/home/mohamadkazem/HSC/leave_reports/urls_new.py` - URL های جدید
- `/home/mohamadkazem/HSC/leave_reports/admin.py` - Admin بهبود یافته
- `/home/mohamadkazem/HSC/templates/leave_reports/base_leave.html` - قالب پایه مدرن
- `/home/mohamadkazem/HSC/templates/leave_reports/request_leave.html` - فرم درخواست
- `/home/mohamadkazem/HSC/leave_reports/views_old_backup.py` - نسخه قدیمی (پشتیبان)

## 📋 کارهای باقیمانده

### 3. قالب‌های (Templates) باقیمانده:

#### الف) `my_inbox.html` - کارتابل من
این صفحه باید شامل دو تب باشد:
1. **درخواست‌های من**: نمایش وضعیت با Timeline مدرن
2. **منتظر تأیید من**: لیست درخواست‌های نیاز به تأیید با دکمه‌های تأیید/رد

#### ب) `leave_archive.html` - آرشیو مرخصی‌ها
صفحه جستجو و فیلتر با:
- فرم جستجو پیشرفته
- جدول مدرن نتایج
- صفحه‌بندی (Pagination)

#### ج) `leave_detail.html` - جزئیات درخواست
نمایش کامل یک درخواست با:
- Timeline وضعیت
- اطلاعات درخواست دهنده
- جزئیات جایگزین و تأیید کننده
- دکمه‌های عملیات (در صورت نیاز)

#### د) `manage_approvers.html` - مدیریت تأیید کنندگان
پنل مدیریت برای سوپریوزر:
- فرم افزودن تأیید کننده
- جدول تأیید کنندگان موجود
- دکمه حذف

### 4. یکپارچه‌سازی (Integration):

#### الف) تغییر در `leave_reports/urls.py`:
```python
# محتوای فعلی را نگه دارید و این خطوط را اضافه کنید:
from . import views_new

# یا اینکه کل فایل را با urls_new.py جایگزین کنید
```

#### ب) تغییر فایل `views.py`:
- Option 1: Replace completely:
  ```bash
  cd /home/mohamadkazem/HSC/leave_reports
  mv views.py views_old_backup2.py
  mv views_new.py views.py
  ```
- Option 2: Keep both and import specific views

#### ج) به‌روزرسانی منوی سایدبار:
در فایل مربوط به منوی اصلی (معمولاً `templates/base.html` یا `templates/includes/sidebar.html`), افزودن منوی مرخصی:

```html
{% load permission_tags %}

<!-- منوی مدیریت مرخصی -->
<li class="nav-item has-treeview {% if request.resolver_match.namespace == 'leave_reports' %}menu-open{% endif %}">
    <a href="#" class="nav-link">
        <i class="nav-icon fas fa-calendar-check"></i>
        <p>
            مدیریت مرخصی
            <i class="right fas fa-angle-left"></i>
        </p>
    </a>
    <ul class="nav nav-treeview">
        {% if user|check_permission_filter:'leave_request_create' %}
        <li class="nav-item">
            <a href="{% url 'leave_reports:request_leave' %}" class="nav-link">
                <i class="far fa-paper-plane nav-icon"></i>
                <p>درخواست مرخصی جدید</p>
            </a>
        </li>
        {% endif %}
        
        {% if user|check_permission_filter:'leave_my_inbox' %}
        <li class="nav-item">
            <a href="{% url 'leave_reports:my_inbox' %}" class="nav-link">
                <i class="far fa-inbox nav-icon"></i>
                <p>کارتابل من</p>
            </a>
        </li>
        {% endif %}
        
        {% if user|check_permission_filter:'leave_archive_view' %}
        <li class="nav-item">
            <a href="{% url 'leave_reports:leave_archive' %}" class="nav-link">
                <i class="far fa-folder-open nav-icon"></i>
                <p>آرشیو مرخصی‌ها</p>
            </a>
        </li>
        {% endif %}
        
        {% if user.is_superuser %}
        <li class="nav-item">
            <a href="{% url 'leave_reports:manage_approvers' %}" class="nav-link">
                <i class="far fa-user-check nav-icon"></i>
                <p>مدیریت تأیید کنندگان</p>
            </a>
        </li>
        {% endif %}
    </ul>
</li>
```

### 5. تعریف Permissions:
در پنل Admin یا سیستم Permissions موجود, این دسترسی‌ها را اضافه کنید:
- `leave_request_create` - ایجاد درخواست مرخصی
- `leave_my_inbox` - مشاهده کارتابل
- `leave_archive_view` - مشاهده آرشیو

### 6. وابستگی‌های Frontend:
مطمئن شوید این کتابخانه‌ها در `base.html` یا قالب اصلی بارگذاری شده‌اند:
```html
<!-- Font Awesome -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">

<!-- Select2 -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

<!-- Persian DatePicker -->
<script src="{% static 'js/persian-datepicker.min.js' %}"></script>
<link rel="stylesheet" href="{% static 'css/persian-datepicker.min.css' %}">
```

### 7. تست سیستم:
1. ایجاد یک درخواست مرخصی توسط کاربر عادی
2. تأیید/رد توسط جایگزین
3. تأیید/رد نهایی توسط مدیر
4. تست جستجو در آرشیو
5. تست مدیریت تأیید کنندگان توسط superuser

## 🎨 ویژگی‌های طراحی:

### رنگ‌های اصلی:
- **Primary (بنفش/ایندیگو)**: `#667eea` - `#764ba2`
- **Success (سبز)**: `#10b981` - `#059669`
- **Warning (زرد/نارنجی)**: `#f59e0b` - `#d97706`
- **Danger (قرمز)**: `#ef4444` - `#dc2626`

### المان‌های مدرن:
- ✅ کارت‌های با گوشه گرد و سایه نرم
- ✅ Gradient Headers برای کارت‌ها
- ✅ آیکون‌های Font Awesome در همه جا
- ✅ انیمیشن‌های Fade-in و Slide-up
- ✅ دکمه‌های با Gradient و Hover Effects
- ✅ Timeline مدرن برای نمایش وضعیت
- ✅ بج‌های رنگی برای وضعیت‌ها
- ✅ Select2 برای dropdown ها
- ✅ Persian DatePicker برای تاریخ

## 🚀 مراحل نهایی فعال‌سازی:

```bash
cd /home/mohamadkazem/HSC

# 1. جایگزینی فایل‌های جدید
mv leave_reports/views.py leave_reports/views_old_complete_backup.py
mv leave_reports/views_new.py leave_reports/views.py
mv leave_reports/urls.py leave_reports/urls_old_backup.py
mv leave_reports/urls_new.py leave_reports/urls.py

# 2. Restart server
source .venv/bin/activate
python manage.py collectstatic --noinput
pkill -f runserver
python manage.py runserver 0.0.0.0:8000 &
```

## 📝 نکات مهم:

1. **همه چیز RTL است**: طراحی کامل برای فارسی
2. **AJAX محور**: تجربه کاربری روان بدون رفرش صفحه
3. **Responsive**: قابل استفاده در موبایل و تبلت
4. **Accessible**: با icon ها و رنگ‌های معنادار
5. **Permission-based**: تمام بخش‌ها با سیستم دسترسی یکپارچه هستند

## 🔔 سیستم اعلانات (TODO):
در کدها نقاطی با کامنت `# TODO: پیاده‌سازی سیستم اعلان` وجود دارد که می‌توانید بعداً پیاده‌سازی کنید:
- اعلان به جایگزین هنگام درخواست
- اعلان به مدیر بعد از تأیید جایگزین
- اعلان به درخواست دهنده بعد از تأیید/رد نهایی

---

**تاریخ ایجاد**: {{ now }}
**نسخه**: 1.0.0
**وضعیت**: 70% کامل - نیاز به ایجاد قالب‌های باقیمانده
