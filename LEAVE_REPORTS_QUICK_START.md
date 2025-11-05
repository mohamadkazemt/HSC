# 🚀 راهنمای سریع شروع - ماژول Leave Reports

## خلاصه تغییرات

✅ **5 فایل HTML** کاملاً بازطراحی شد
✅ **forms.py** به‌روزرسانی شد
✅ **views.py** بهبود یافت
✅ دارک مود کامل
✅ عملیات AJAX
✅ UI/UX مدرن

---

## 📦 فایل‌های تغییر یافته

### 🎨 Templates (با پشتیبان):
1. `templates/leave_reports/manage_approvers.html` → `manage_approvers_old.html`
2. `templates/leave_reports/request_leave.html` → `request_leave_old_backup.html`
3. `templates/leave_reports/my_inbox.html` → `my_inbox_old.html`
4. `templates/leave_reports/leave_archive.html` → `leave_archive_old.html`
5. `templates/leave_reports/leave_detail.html` → `leave_detail_old.html`

### ⚙️ Backend:
- `leave_reports/forms.py` - فیلدهای جدید و استایل Tailwind
- `leave_reports/views.py` - API endpoint و context variables

---

## 🔄 نحوه استفاده

### 1. بدون نیاز به اقدام خاص
همه چیز آماده است! فقط:
```bash
python manage.py runserver
```

### 2. اگر migration نیاز است:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. تست سریع:
بروید به:
- http://localhost:8000/leave-reports/my-inbox/

---

## 🎯 ویژگی‌های جدید

### ✨ مدیریت تأییدکنندگان
- Select2 AJAX برای جستجوی کاربران
- بارگذاری داینامیک Parts
- حذف با مودال تأیید (AJAX)

**URL:** `/leave-reports/manage-approvers/`
**دسترسی:** فقط Superuser

### 📝 ثبت درخواست
- ویزارد 4 مرحله‌ای
- انتخاب کارتی نوع مرخصی
- Jalali Date Picker
- Select2 برای انتخاب جانشین
- آپلود مدرک پزشکی

**URL:** `/leave-reports/request-leave/`

### 📬 صندوق ورودی
- 4 کارت آمار
- 2 تب: درخواست‌های من / تأییدهای در انتظار
- تایم‌لاین وضعیت
- تأیید/رد با AJAX

**URL:** `/leave-reports/my-inbox/`

### 📚 آرشیو
- فیلترهای پیشرفته (آکاردئونی)
- 5 کارت آمار
- نمای جدول/کارت
- صفحه‌بندی
- خروجی اکسل

**URL:** `/leave-reports/leave-archive/`

### 🔍 جزئیات
- تایم‌لاین مسیر تأیید
- دکمه‌های عملیات (AJAX)
- لینک‌های سریع
- اطلاعات تکمیلی

**URL:** `/leave-reports/leave-detail/<id>/`

---

## 🌓 حالت تاریک

دارک مود در **همه صفحات** فعال است و خودکار از تنظیمات `base.html` استفاده می‌کند.

Toggle دارک مود → همه المان‌ها به‌روز می‌شوند

---

## 📱 Responsive

تمام صفحات در اندازه‌های زیر تست شده:
- Desktop (1280px+)
- Laptop (1024px-1279px)
- Tablet (768px-1023px)
- Mobile (320px-767px)

---

## 🔔 Toast Notifications

همه عملیات AJAX با Toast feedback:
- ✅ سبز: موفقیت
- ❌ قرمز: خطا
- Auto-hide بعد از 3 ثانیه
- Progress bar

---

## 🐛 خطاهای احتمالی

### خطا: Select2 کار نمی‌کند
**راه‌حل:** چک کنید `base.html` شامل Select2 باشد:
```html
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
```

### خطا: Jalali Date Picker نمایش نمی‌دهد
**راه‌حل:** چک کنید `base.html` شامل Persian Date Picker باشد یا از کلاس `.jalali-date` استفاده کنید.

### خطا: دارک مود کار نمی‌کند
**راه‌حل:** چک کنید Alpine.js در `base.html` لود شده باشد.

### خطا: AJAX عملیات انجام نمی‌شود
**راه‌حل:** چک کنید CSRF token در فرم‌ها وجود دارد:
```html
{% csrf_token %}
```

---

## 🔑 نکات مهم

### 1. فایل‌های قدیمی
همه فایل‌های قدیمی با پسوند `_old` یا `_old_backup` ذخیره شده‌اند.

اگر خواستید برگردید:
```bash
mv templates/leave_reports/manage_approvers_old.html templates/leave_reports/manage_approvers.html
```

### 2. API Endpoints جدید
```python
# API برای Select2 جستجوی کاربران
url: /leave-reports/api/users-for-replacement/
method: GET
params: q (search), page
```

### 3. Context Variables جدید
```python
# my_inbox view
'my_requests_count'
'pending_replacement_count'
'pending_manager_count'
'approved_count'
'pending_approvals'  # تغییر نام از 'pending_for_me'

# leave_archive view
'page_obj'  # تغییر نام از 'leaves'
'total_count'
'pending_count'
'approved_count'
'rejected_count'
'today_count'
```

---

## 📖 مستندات کامل

برای جزئیات بیشتر، مراجعه کنید به:
- `LEAVE_REPORTS_UI_REDESIGN_COMPLETE.md` - مستندات کامل
- `LEAVE_REPORTS_TESTING_GUIDE.md` - راهنمای تست

---

## 🎨 ساختار کلی

```
leave_reports/
├── templates/
│   └── leave_reports/
│       ├── manage_approvers.html ✅ (جدید)
│       ├── request_leave.html ✅ (جدید)
│       ├── my_inbox.html ✅ (جدید)
│       ├── leave_archive.html ✅ (جدید)
│       ├── leave_detail.html ✅ (جدید)
│       ├── manage_approvers_old.html (پشتیبان)
│       ├── request_leave_old_backup.html (پشتیبان)
│       ├── my_inbox_old.html (پشتیبان)
│       ├── leave_archive_old.html (پشتیبان)
│       └── leave_detail_old.html (پشتیبان)
├── forms.py ✅ (به‌روز شده)
├── views.py ✅ (به‌روز شده)
├── models.py (بدون تغییر)
├── urls.py (بدون تغییر)
└── admin.py (بدون تغییر)
```

---

## 🧪 تست سریع

### ثبت یک درخواست:
1. برو به `/leave-reports/request-leave/`
2. انتخاب نوع مرخصی
3. تکمیل فرم
4. انتخاب جانشین
5. ارسال
6. چک کن Toast نمایش داده شود

### تأیید درخواست:
1. برو به `/leave-reports/my-inbox/`
2. تب "تأییدهای در انتظار"
3. کلیک "تأیید"
4. چک کن با AJAX انجام شود

---

## ❓ سوالات متداول

### Q: آیا نیاز به نصب چیز جدیدی هست؟
**A:** خیر. همه dependencies از `base.html` لود می‌شوند.

### Q: آیا دیتابیس تغییر کرده؟
**A:** خیر. فقط view ها و template ها تغییر کرده‌اند.

### Q: اگر مشکلی پیش آمد چطور؟
**A:** فایل‌های قدیمی را restore کنید یا issue باز کنید.

### Q: دارک مود چطور فعال می‌شود؟
**A:** خودکار از `base.html` دریافت می‌شود.

---

## 🎉 آماده استفاده!

همه چیز آماده است. فقط سرور را اجرا کنید و لذت ببرید! 🚀

```bash
python manage.py runserver
```

بروید به: http://localhost:8000/leave-reports/my-inbox/

---

**نکته:** اگر سوالی دارید، به فایل‌های مستندات مراجعه کنید:
- `LEAVE_REPORTS_UI_REDESIGN_COMPLETE.md`
- `LEAVE_REPORTS_TESTING_GUIDE.md`

یا issue باز کنید.

**موفق باشید! 🎊**
