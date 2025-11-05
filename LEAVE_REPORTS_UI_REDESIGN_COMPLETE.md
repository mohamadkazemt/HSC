# بازطراحی کامل UI/UX ماژول Leave Reports

## 📋 خلاصه پروژه

بازطراحی کامل رابط کاربری ماژول `leave_reports` با تمرکز بر:
- ✅ پشتیبانی کامل از حالت تاریک و روشن
- ✅ استفاده از Alpine.js برای تعاملات
- ✅ عملیات AJAX برای تجربه کاربری بهتر
- ✅ طراحی مدرن با Tailwind CSS
- ✅ نوتیفیکیشن‌های Toast سفارشی
- ✅ انیمیشن‌های روان

---

## 🎨 فایل‌های بازطراحی شده

### 1️⃣ `manage_approvers.html`
**تغییرات کلیدی:**
- ✨ کامپوننت Alpine.js با نام `approversManager()`
- 🔍 Select2 AJAX برای جستجوی تأییدکننده‌ها
- 📦 بارگذاری داینامیک Parts بر اساس Section
- 🗑️ مودال تأیید حذف با Alpine.js
- 🌐 عملیات حذف با AJAX و انیمیشن
- 🌓 پشتیبانی کامل از دارک مود

**فایل پشتیبان:** `manage_approvers_old.html`

---

### 2️⃣ `request_leave.html`
**تغییرات کلیدی:**
- 🎯 ویزارد 4 مرحله‌ای با Alpine.js
- 📊 نوار پیشرفت
- 🎴 انتخاب نوع مرخصی به صورت کارتی
- ⚙️ نمایش فیلدهای شرطی
- 📤 ارسال فرم با FormData (پشتیبانی از آپلود فایل)
- 🔔 سیستم Toast سفارشی
- 🌓 دارک مود کامل

**فایل پشتیبان:** `request_leave_old_backup.html`

**مراحل ویزارد:**
1. انتخاب نوع مرخصی (کارت‌های انتخابی)
2. تاریخ و جزئیات (فیلدهای شرطی)
3. انتخاب جانشین (فقط برای مرخصی عادی)
4. خلاصه و ارسال نهایی

---

### 3️⃣ `my_inbox.html`
**تغییرات کلیدی:**
- 📊 کارت‌های آمار با گرادیانت
- 🗂️ سیستم تب برای "درخواست‌های من" و "تأییدهای در انتظار"
- ⏱️ تایم‌لاین بصری برای وضعیت درخواست
- ✅ تأیید/رد با AJAX و لودینگ
- 💬 مودال برای دلیل رد
- 🏷️ رنگ‌بندی Badge برای وضعیت‌ها

**فایل پشتیبان:** `my_inbox_old.html`

**کارت‌های آمار:**
- کل درخواست‌های من
- در انتظار تأیید جانشین
- در انتظار تأیید مدیر
- تأیید شده

---

### 4️⃣ `leave_archive.html`
**تغییرات کلیدی:**
- 🎛️ پنل فیلتر آکاردئونی با Alpine.js
- 🔍 فیلترهای جستجو: تاریخ، نوع، وضعیت، کاربر، شیفت، گروه کاری
- 📊 آمار خلاصه در 5 کارت
- 🔀 تغییر نمای جدول/کارت
- 📄 صفحه‌بندی پیشرفته
- 📥 دکمه خروجی اکسل
- 🌓 دارک مود کامل

**فایل پشتیبان:** `leave_archive_old.html`

**فیلترهای جستجو:**
- جستجوی کاربر (نام/نام خانوادگی)
- نوع مرخصی
- وضعیت
- بازه تاریخی (شمسی با Jalali Date Picker)
- نوع شیفت
- گروه کاری

---

### 5️⃣ `leave_detail.html`
**تغییرات کلیدی:**
- 📋 کارت‌های جزئیات درخواست
- ⏱️ تایم‌لاین تصویری برای مسیر تأیید
- ✅ دکمه‌های عملیات AJAX (تأیید/رد)
- 💬 مودال دلیل رد
- 📊 اطلاعات تکمیلی در سایدبار
- 🔗 لینک‌های سریع
- 🌓 دارک مود کامل

**فایل پشتیبان:** `leave_detail_old.html`

**مراحل تایم‌لاین:**
1. ثبت درخواست (با آیکون و تاریخ)
2. تأیید جانشین (با وضعیت رنگی)
3. تأیید مدیر (با وضعیت رنگی)

---

## 🔧 تغییرات Backend

### ✏️ `forms.py`
**تغییرات در `ShiftReportForm`:**
```python
# قبل: class="form-control"
# بعد: class="w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500"
```

**فیلدهای به‌روز شده:**
- `shift_date` → کلاس `jalali-date` اضافه شد
- `replacement_person` → کلاس `select2-ajax` اضافه شد
- `medical_document` → استایل Tailwind
- همه فیلدها → پشتیبانی دارک مود

**تغییرات در `LeaveSearchForm`:**
- تغییر نام فیلد `search` به `user_search`
- اضافه شدن فیلد `shift_type`
- اضافه شدن فیلد `work_group`
- به‌روزرسانی همه ویجت‌ها با Tailwind + دارک مود
- تغییر کلاس `persian-datepicker` به `jalali-date`

---

### 🔌 `views.py`

#### تابع `api_get_users_for_replacement` (خطوط 803-838)
```python
@login_required
def api_get_users_for_replacement(request):
    """API endpoint برای جستجوی کاربران در Select2"""
    # پشتیبانی از pagination و search
    # فرمت خروجی: {'results': [...], 'pagination': {...}}
```

#### تابع `my_inbox` (به‌روزرسانی)
**متغیرهای context اضافه شده:**
- `my_requests_count` - تعداد کل درخواست‌های کاربر
- `pending_replacement_count` - در انتظار تأیید جانشین
- `pending_manager_count` - در انتظار تأیید مدیر
- `approved_count` - تأیید شده

**تغییر نام متغیر:**
- `pending_for_me` → `pending_approvals`

#### تابع `manage_approvers` (به‌روزرسانی)
**متغیر context اضافه شده:**
- `sections` - لیست تمام Section‌ها برای بارگذاری Parts

#### تابع `leave_archive` (به‌روزرسانی کامل)
**فیلترهای اضافه شده:**
- `user_search` - جستجوی نام کاربری
- `shift_type` - نوع شیفت
- `work_group` - گروه کاری

**متغیرهای context اضافه شده:**
- `total_count` - کل درخواست‌ها
- `pending_count` - در انتظار
- `approved_count` - تأیید شده
- `rejected_count` - رد شده
- `today_count` - امروز
- `page_obj` - صفحه‌بندی شده (تغییر از `leaves`)

---

## 🎯 ویژگی‌های کلیدی پیاده‌سازی شده

### 🌗 دارک مود
همه المان‌ها با کلاس‌های `dark:` برای سازگاری کامل:
```css
dark:bg-gray-800
dark:text-white
dark:border-gray-700
dark:hover:bg-gray-700
```

### ⚡ Alpine.js
کامپوننت‌های reactive برای هر صفحه:
- `approversManager()` - مدیریت تأییدکنندگان
- `leaveRequestWizard()` - ویزارد ثبت درخواست
- `inboxManager()` - صندوق ورودی
- `archiveManager()` - آرشیو
- `leaveDetailManager()` - جزئیات

### 🔔 Toast Notifications
سیستم Toast سفارشی با:
- پیام‌های موفقیت/خطا
- نوار پیشرفت
- بسته شدن خودکار پس از 3 ثانیه
- انیمیشن ورود/خروج

### 🎨 Tailwind CSS
- کلاس‌های utility-first
- گرادیانت‌های زیبا
- سایه‌ها و انیمیشن‌ها
- responsive design

### 🔍 Select2 AJAX
- جستجوی لحظه‌ای کاربران
- pagination داخلی
- بارگذاری تنبل
- کش کردن نتایج

### 📅 Jalali Date Picker
- خودکار از طریق کلاس `.jalali-date`
- فرمت شمسی
- اعتبارسنجی تاریخ

---

## 📊 آمار تغییرات

| فایل | خطوط قبل | خطوط بعد | تغییر |
|------|---------|---------|-------|
| manage_approvers.html | ~250 | ~420 | +68% |
| request_leave.html | ~180 | ~530 | +194% |
| my_inbox.html | ~220 | ~480 | +118% |
| leave_archive.html | ~150 | ~440 | +193% |
| leave_detail.html | ~200 | ~640 | +220% |
| forms.py (LeaveSearchForm) | ~50 | ~70 | +40% |
| views.py (api + updates) | 0 | ~40 | جدید |

**جمع کل:** حدود 2600+ خط کد جدید/بازنویسی شده

---

## 🧪 تست‌های پیشنهادی

### ✅ مدیریت تأییدکنندگان
1. افزودن تأییدکننده جدید
2. حذف تأییدکننده با مودال تأیید
3. بارگذاری داینامیک Parts بر اساس Section
4. عملکرد Select2 AJAX

### ✅ ثبت درخواست
1. طی کردن ویزارد 4 مرحله‌ای
2. انتخاب هر نوع مرخصی
3. نمایش فیلدهای شرطی (ساعتی، مرخصی استعلاجی)
4. انتخاب جانشین با Select2
5. آپلود مدرک پزشکی
6. ارسال فرم با FormData
7. نمایش Toast موفقیت/خطا

### ✅ صندوق ورودی
1. نمایش کارت‌های آمار
2. تعویض بین تب‌های "درخواست‌های من" و "تأییدهای در انتظار"
3. تأیید درخواست با AJAX
4. رد درخواست با مودال و دلیل
5. تایم‌لاین وضعیت

### ✅ آرشیو
1. باز/بسته کردن پنل فیلتر
2. جستجوی کاربر
3. فیلتر بر اساس نوع، وضعیت، تاریخ
4. تعویض نمای جدول/کارت
5. صفحه‌بندی
6. خروجی اکسل

### ✅ جزئیات درخواست
1. نمایش اطلاعات کامل
2. تایم‌لاین مسیر تأیید
3. دکمه‌های تأیید/رد (برای کاربران مجاز)
4. مودال دلیل رد
5. لینک‌های سریع

---

## 🎨 رنگ‌بندی وضعیت‌ها

| وضعیت | رنگ | کلاس Tailwind |
|-------|-----|---------------|
| در انتظار جانشین | نارنجی | `bg-amber-100 text-amber-800` |
| در انتظار تأیید | آبی | `bg-blue-100 text-blue-800` |
| تأیید شده | سبز | `bg-green-100 text-green-800` |
| رد شده | قرمز | `bg-red-100 text-red-800` |

---

## 🔒 امنیت

### CSRF Protection
همه عملیات AJAX با توکن CSRF:
```javascript
headers: {
    'X-CSRFToken': '{{ csrf_token }}'
}
```

### دسترسی‌ها
- بررسی دسترسی در سمت سرور
- نمایش شرطی دکمه‌های عملیات
- محدودیت API endpoints

---

## 🚀 نکات عملکردی

### بهینه‌سازی Query
```python
ShiftReport.objects.all().select_related(
    'user', 'replacement_person', 'final_approver', 
    'rejected_by', 'crate_by'
)
```

### Pagination
- 20 آیتم در هر صفحه
- نمایش 3 صفحه قبل/بعد
- حفظ query string در pagination

### کش کردن
- Select2 کش داخلی
- Alpine.js reactive state
- تصاویر SVG inline

---

## 📱 Responsive Design

همه صفحات با breakpoint‌های Tailwind:
- `sm:` - ≥640px
- `md:` - ≥768px
- `lg:` - ≥1024px
- `xl:` - ≥1280px

---

## 🎓 الگوهای کدنویسی استفاده شده

### Alpine.js Component Pattern
```javascript
function componentName() {
    return {
        // State
        loading: false,
        
        // Methods
        async someMethod() {
            // Logic
        }
    };
}
```

### AJAX Pattern
```javascript
const formData = new FormData();
formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');

const response = await fetch(url, {
    method: 'POST',
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': '{{ csrf_token }}'
    },
    body: formData
});

const data = await response.json();
```

### Toast Pattern
```javascript
showToast(message, type = 'success') {
    this.toast.message = message;
    this.toast.type = type;
    this.toast.show = true;
    // Auto-hide after 3s with progress bar
}
```

---

## 🔄 Migration از قدیمی به جدید

### Template Changes
- jQuery → Alpine.js
- Bootstrap → Tailwind CSS
- Django Messages → Toast Notifications
- Form Submit → AJAX Submit

### Class Mapping
| قدیمی | جدید |
|-------|------|
| `form-control` | `w-full rounded-lg border-gray-300 dark:...` |
| `btn btn-primary` | `bg-indigo-600 text-white rounded-xl ...` |
| `persian-datepicker` | `jalali-date` |
| `card` | `bg-white dark:bg-gray-800 rounded-2xl shadow-lg` |

---

## 📚 منابع مرتبط

### Documentation
- Alpine.js: https://alpinejs.dev/
- Tailwind CSS: https://tailwindcss.com/
- Select2: https://select2.org/
- Jalali Date Picker: (custom implementation)

### Dependencies از base.html
- Alpine.js 3.x
- Tailwind CSS 3.x
- Select2 4.1.0
- Font Awesome 6.x

---

## ✅ Checklist نهایی

- [x] بازطراحی manage_approvers.html
- [x] بازطراحی request_leave.html
- [x] بازطراحی my_inbox.html
- [x] بازطراحی leave_archive.html
- [x] بازطراحی leave_detail.html
- [x] به‌روزرسانی forms.py
- [x] به‌روزرسانی views.py
- [x] پشتیبانی کامل دارک مود
- [x] عملیات AJAX
- [x] Toast Notifications
- [x] Select2 AJAX Integration
- [x] Jalali Date Picker
- [x] Responsive Design
- [x] Security (CSRF)
- [x] پشتیبان‌گیری از فایل‌های قدیمی

---

## 🎉 نتیجه

پروژه بازطراحی کامل ماژول Leave Reports با موفقیت انجام شد. همه مشکلات UI/UX برطرف شده و یک رابط کاربری مدرن، responsive و قابل استفاده ایجاد شده است.

**تاریخ تکمیل:** {{ current_date }}
**تعداد فایل‌های تغییر یافته:** 7 فایل
**تعداد خطوط کد جدید:** 2600+ خط

---

*این سند توسط GitHub Copilot تهیه شده است.*
