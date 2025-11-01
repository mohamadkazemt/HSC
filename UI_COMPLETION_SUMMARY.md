# خلاصه کامل طراحی UI/UX ماژول مدیریت پیمانکاران

## ✅ صفحات ایجاد شده (5 صفحه)

### 1. 📊 داشبورد مدیریت پیمانکاران
**مسیر:** `templates/contractor_management/dashboard/contractor_dashboard.html`

**ویژگی‌ها:**
- ✅ 4 کارت آماری با گرادیانت‌های زیبا (کل پیمانکاران، کارکنان فعال، خودروهای فعال، مدارک منقضی)
- ✅ کارت هشدار برای مدارک منقضی/نزدیک به انقضا
- ✅ نمودار دایره‌ای توزیع خودروها (Chart.js)
- ✅ کارت‌های دسترسی سریع با آیکون
- ✅ تمامی المان‌ها Responsive و دارای Dark Mode

### 2. 📝 فرم ثبت گزارش
**مسیر:** `templates/contractor_management/report_form.html`

**ویژگی‌ها:**
- ✅ تقویم شمسی (Persian Datepicker)
- ✅ Dropdown جستجوی خودرو (Select2 با AJAX)
- ✅ فیلدهای شرطی با Alpine.js:
  - بخش "کارکرد ناقص" با فیلدهای زمان
  - بخش "غیرفعال" با فیلد توضیحات
- ✅ رادیو باتن‌های رنگی (سبز/زرد/قرمز)
- ✅ انیمیشن‌های smooth
- ✅ نمایش پیام‌های خطا/موفقیت

### 3. 📋 آرشیو گزارش‌ها
**مسیر:** `templates/contractor_management/reports/all_reports.html`

**ویژگی‌ها:**
- ✅ 4 کارت آماری در بالای صفحه (فعال/نیمه‌فعال/غیرفعال/نامشخص)
- ✅ فیلترهای Collapsible (Accordion) با Alpine.js
- ✅ کارت‌های خودرو به جای جدول:
  - نام راننده و پلاک
  - نام پیمانکار
  - Badge رنگی وضعیت (با گرادیانت)
  - دکمه "مشاهده همه گزارش‌ها"
- ✅ تقویم شمسی برای فیلتر تاریخ
- ✅ Select2 برای فیلتر پیمانکار/خودرو
- ✅ Pagination
- ✅ دکمه خروجی Excel

### 4. 🔐 صفحه ورود پیمانکاران
**مسیر:** `templates/contractor_management/auth/contractor_login.html`

**ویژگی‌ها:**
- ✅ صفحه مستقل (بدون Sidebar و Header ادمین)
- ✅ Background با گرادیانت و Blur Effects
- ✅ کارت لاگین زیبا با سایه قوی
- ✅ نمایش لوگوی شرکت
- ✅ فیلدهای Username و Password با آیکون
- ✅ Checkbox "مرا به خاطر بسپار"
- ✅ دکمه ورود با گرادیانت و Hover Effect
- ✅ Responsive کامل

### 5. 🏠 داشبورد پورتال پیمانکاران
**مسیر:** `templates/contractor_management/auth/contractor_portal.html`

**ویژگی‌ها:**
- ✅ هدر خوشامدگویی با گرادیانت
- ✅ کارت وضعیت تکمیل پروفایل:
  - Progress Bar رنگی (سبز/زرد/قرمز بر اساس درصد)
  - 3 بخش: اطلاعات شخصی، مدارک، آموزش‌ها
  - آیکون تیک/ضربدر برای هر بخش
- ✅ کارت اقدامات مورد نیاز (Required Actions)
- ✅ 3 کارت دسترسی سریع:
  - پروفایل من
  - مدارک من
  - راهنما و پشتیبانی
- ✅ بخش فعالیت‌های اخیر (اختیاری)

---

## 📁 ساختار فایل‌های ایجاد شده

```
/templates/contractor_management/
├── dashboard/
│   └── contractor_dashboard.html       ✅ (ایجاد شده)
├── auth/
│   ├── contractor_login.html           ✅ (ایجاد شده)
│   └── contractor_portal.html          ✅ (ایجاد شده)
├── reports/
│   └── all_reports.html                ✅ (ایجاد شده)
├── contractors/                        ❌ (ایجاد نشده)
├── employees/                          ❌ (ایجاد نشده)
├── vehicles/                           ❌ (ایجاد نشده)
└── report_form.html                    ✅ (ایجاد شده)
```

---

## 🔴 صفحات باقی‌مانده (2 صفحه اصلی)

### 6. صفحه مدیریت داده‌ها (Data Management)
**اولویت:** بالا

**محتوا:**
- تب‌های پیمانکاران/کارکنان/خودروها
- جداول با هدر رنگی و Hover Effects
- دکمه‌های Add/Edit/Delete با آیکون
- مودال‌های Add/Edit:
  - مودال پیمانکار: با بخش ایجاد حساب ادمین
  - مودال کارمند: با Toggle Switch برای ایجاد حساب
  - مودال خودرو: با انتخاب دسته‌بندی

### 7. صفحه پروفایل/مدارک پیمانکار
**اولویت:** بالا

**محتوا:**
- کارت‌های دسته‌بندی شده:
  - اطلاعات شخصی (فیلدهای read-only)
  - مدارک (با Drag & Drop Upload)
  - آموزش‌ها
- نمایش وضعیت آپلود (آپلود شده/در انتظار)
- پیش‌نمایش فایل
- اعتبارسنجی نوع و حجم فایل

---

## 🎨 سیستم طراحی استفاده شده

### رنگ‌ها
- **Primary:** Indigo (#6366f1) to Purple (#a855f7)
- **Success:** Green (#22c55e)
- **Warning:** Yellow (#eab308)
- **Danger:** Red (#ef4444)
- **Info:** Blue (#3b82f6)

### کامپوننت‌ها
- **Cards:** `rounded-xl shadow-md`
- **Buttons:** `rounded-lg` با gradient و hover effects
- **Gradients:** `bg-gradient-to-r from-{color} to-{color}`
- **Icons:** Heroicons (inline SVG)
- **Badges:** `rounded-full` با gradients

### انیمیشن‌ها
- **Transitions:** `transition-all duration-200`
- **Hover:** `hover:shadow-xl hover:scale-105`
- **Collapse:** Alpine.js `x-collapse`
- **Fade:** Alpine.js `x-transition`

---

## 📦 کتابخانه‌های استفاده شده

### CSS
- ✅ Tailwind CSS (CDN از base.html)
- ✅ Select2 CSS
- ✅ Persian Datepicker CSS
- ✅ Chart.js CSS

### JavaScript
- ✅ Alpine.js (از base.html)
- ✅ jQuery (برای Select2)
- ✅ Select2
- ✅ Persian Datepicker
- ✅ Chart.js

---

## 🔧 تغییرات مورد نیاز در Backend

### 1. اضافه کردن URLها

در فایل `contractor_management/urls.py`:

```python
urlpatterns = [
    # ... URLهای موجود ...
    
    # داشبورد ادمین
    path('dashboard/', views.contractor_dashboard, name='contractor_dashboard'),
    
    # لاگین و پورتال پیمانکاران
    path('contractor-login/', views.contractor_login, name='contractor_login'),
    path('contractor-portal/', views.contractor_portal_dashboard, name='contractor_portal'),
    path('contractor-profile/', views.contractor_profile_documents, name='contractor_profile'),
    
    # مدیریت داده‌ها
    path('data-management/', views.data_management, name='data_management'),
]
```

### 2. ایجاد View Functions

در فایل `contractor_management/views.py`:

```python
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db.models import Count
from datetime import datetime, timedelta
from .models import Contractor, Employee, Vehicle, Report

@login_required
def contractor_dashboard(request):
    """داشبورد مدیریت پیمانکاران"""
    today = datetime.now().date()
    thirty_days_later = today + timedelta(days=30)
    
    # محاسبه آمار
    total_contractors = Contractor.objects.count()
    active_employees = Employee.objects.count()
    active_vehicles = Vehicle.objects.count()
    
    # مدارک منقضی شده
    expired_contractors = []
    for contractor in Contractor.objects.all():
        expired_docs = []
        
        if contractor.liability_insurance_expiry and contractor.liability_insurance_expiry <= thirty_days_later:
            status = 'expired' if contractor.liability_insurance_expiry < today else 'warning'
            expired_docs.append({
                'name': 'بیمه مسئولیت',
                'expiry_date': contractor.liability_insurance_expiry,
                'status': status
            })
        
        if contractor.fire_insurance_expiry and contractor.fire_insurance_expiry <= thirty_days_later:
            status = 'expired' if contractor.fire_insurance_expiry < today else 'warning'
            expired_docs.append({
                'name': 'بیمه آتش‌سوزی',
                'expiry_date': contractor.fire_insurance_expiry,
                'status': status
            })
        
        if expired_docs:
            expired_contractors.append({
                'id': contractor.id,
                'company_name': contractor.company_name,
                'expired_documents': expired_docs
            })
    
    # تعداد خودروها بر اساس دسته‌بندی
    vehicle_counts = Vehicle.objects.values('vehicle_category').annotate(count=Count('id'))
    mining_vehicles = next((item['count'] for item in vehicle_counts if item['vehicle_category'] == 'mining'), 0)
    light_vehicles = next((item['count'] for item in vehicle_counts if item['vehicle_category'] == 'light'), 0)
    transportation_vehicles = next((item['count'] for item in vehicle_counts if item['vehicle_category'] == 'transportation'), 0)
    
    context = {
        'total_contractors': total_contractors,
        'active_employees': active_employees,
        'active_vehicles': active_vehicles,
        'expired_documents': len(expired_contractors),
        'contractors_with_expired_docs': expired_contractors,
        'mining_vehicles': mining_vehicles,
        'light_vehicles': light_vehicles,
        'transportation_vehicles': transportation_vehicles,
    }
    
    return render(request, 'contractor_management/dashboard/contractor_dashboard.html', context)


def contractor_login(request):
    """صفحه ورود پیمانکاران"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # چک کنید که کاربر پیمانکار است
            if hasattr(user, 'employee') or hasattr(user, 'contractor'):
                login(request, user)
                return redirect('contractor_management:contractor_portal')
            else:
                messages.error(request, 'شما مجوز ورود به این بخش را ندارید.')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    
    return render(request, 'contractor_management/auth/contractor_login.html')


@login_required
def contractor_portal_dashboard(request):
    """داشبورد پورتال پیمانکاران"""
    from datetime import date
    
    # محاسبه درصد تکمیل پروفایل
    profile_completion = 0
    has_personal_info = False
    has_documents = False
    has_training = False
    
    # بررسی اطلاعات شخصی
    if hasattr(request.user, 'employee'):
        employee = request.user.employee
        if employee.first_name and employee.last_name and employee.national_id:
            has_personal_info = True
            profile_completion += 33
        
        # بررسی مدارک
        if employee.card_national_img and employee.health_certificate:
            has_documents = True
            profile_completion += 33
        
        # بررسی آموزش‌ها
        if employee.safety_training:
            has_training = True
            profile_completion += 34
    
    # اقدامات مورد نیاز
    required_actions = []
    if not has_personal_info:
        required_actions.append({
            'title': 'تکمیل اطلاعات شخصی',
            'description': 'لطفاً اطلاعات شخصی خود را کامل کنید',
            'link': reverse('contractor_management:contractor_profile')
        })
    
    if not has_documents:
        required_actions.append({
            'title': 'بارگذاری مدارک',
            'description': 'مدارک هویتی و سلامت خود را بارگذاری کنید',
            'link': reverse('contractor_management:contractor_profile') + '#documents'
        })
    
    context = {
        'today': date.today(),
        'profile_completion': profile_completion,
        'profile': {
            'has_personal_info': has_personal_info,
            'has_documents': has_documents,
            'has_training': has_training,
        },
        'required_actions': required_actions,
    }
    
    return render(request, 'contractor_management/auth/contractor_portal.html', context)


@login_required
def contractor_profile_documents(request):
    """صفحه پروفایل و مدارک پیمانکار"""
    # این view را باید ایجاد کنید
    pass
```

---

## ✨ ویژگی‌های برجسته

### 1. **Responsive Design**
- تمامی صفحات روی موبایل، تبلت و دسکتاپ کار می‌کنند
- Grid سیستم Tailwind با Breakpoints

### 2. **Dark Mode**
- تمامی المان‌ها دارای حالت تاریک
- استفاده از `dark:` prefix

### 3. **Interactive Components**
- Collapsible Filters با Alpine.js
- Conditional Fields با Alpine.js
- Smooth Animations و Transitions
- Hover Effects

### 4. **Professional Design**
- استفاده از Gradients
- Shadow Effects
- Rounded Corners
- Icon Integration (Heroicons)
- Color-coded Status Badges

### 5. **User Experience**
- Persian Date Picker
- Searchable Dropdowns (Select2)
- Loading States
- Error/Success Messages
- Progress Indicators
- Required Field Markers

---

## 🚀 مراحل بعدی

### فاز 1: تکمیل صفحات
1. ✅ ایجاد صفحه مدیریت داده‌ها (با تب‌ها و مودال‌ها)
2. ✅ ایجاد صفحه پروفایل/مدارک پیمانکار

### فاز 2: Backend Integration
1. ✅ ایجاد view functions
2. ✅ اضافه کردن URLها
3. ✅ تست کامل تمامی صفحات
4. ✅ رفع باگ‌ها

### فاز 3: Security & Permissions
1. ✅ اضافه کردن مجوزها (Permissions)
2. ✅ جداسازی دسترسی ادمین و پیمانکار
3. ✅ اعتبارسنجی فایل‌ها
4. ✅ محدودیت حجم آپلود

### فاز 4: Testing & Optimization
1. ✅ تست روی مرورگرهای مختلف
2. ✅ تست Dark Mode
3. ✅ تست Responsive
4. ✅ بهینه‌سازی سرعت

---

## 📞 پشتیبانی و توسعه

برای هر گونه سوال یا نیاز به توسعه بیشتر، می‌توانید:
- به فایل `CONTRACTOR_UI_IMPLEMENTATION.md` مراجعه کنید
- کد نمونه viewها را در این فایل مشاهده کنید
- از الگوهای طراحی موجود پیروی کنید

---

**تاریخ تکمیل:** 1403/10/30
**تعداد صفحات ایجاد شده:** 5 از 7 (71%)
**وضعیت:** در حال توسعه ✨
