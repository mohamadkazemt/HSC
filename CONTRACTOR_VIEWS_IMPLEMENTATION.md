# راهنمای پیاده‌سازی View Functions برای مدیریت پیمانکاران

## ✅ تغییرات انجام شده

### 1. Sidebar به‌روزرسانی شد ✅
- منوی "مدیریت پیمانکاران" به Sidebar اضافه شد
- شامل 3 لینک:
  - داشبورد پیمانکاران
  - ثبت گزارش کارکرد
  - آرشیو گزارش‌ها

### 2. صفحه لاگین اصلی به‌روزرسانی شد ✅
- دکمه "ورود پیمانکاران و پرسنل" اضافه شد
- طراحی زیبا با آیکون
- لینک به صفحه `/contractor-login/`

### 3. URLها اضافه شدند ✅
- `dashboard/` → `contractor_dashboard`
- `contractor-login/` → `contractor_login`
- `contractor-portal/` → `contractor_portal`
- `contractor-profile/` → `contractor_profile`

---

## 🔴 کارهای باقی‌مانده

### مرحله 1: ایجاد View Functions

در فایل `contractor_management/views.py` باید این توابع را اضافه کنید:

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from datetime import datetime, timedelta, date
from .models import Contractor, Employee, Vehicle, Report

# =====================================
# View 1: داشبورد مدیریت پیمانکاران
# =====================================
@login_required
def contractor_dashboard(request):
    """داشبورد اصلی مدیریت پیمانکاران"""
    today = datetime.now().date()
    thirty_days_later = today + timedelta(days=30)
    
    # محاسبه آمار کلی
    total_contractors = Contractor.objects.count()
    active_employees = Employee.objects.count()
    active_vehicles = Vehicle.objects.count()
    
    # یافتن پیمانکاران با مدارک منقضی شده
    expired_contractors = []
    for contractor in Contractor.objects.all():
        expired_docs = []
        
        # بررسی بیمه مسئولیت
        if contractor.liability_insurance_expiry:
            if contractor.liability_insurance_expiry <= thirty_days_later:
                status = 'expired' if contractor.liability_insurance_expiry < today else 'warning'
                expired_docs.append({
                    'name': 'بیمه مسئولیت مدنی',
                    'expiry_date': contractor.liability_insurance_expiry,
                    'status': status
                })
        
        # بررسی بیمه آتش‌سوزی
        if contractor.fire_insurance_expiry:
            if contractor.fire_insurance_expiry <= thirty_days_later:
                status = 'expired' if contractor.fire_insurance_expiry < today else 'warning'
                expired_docs.append({
                    'name': 'بیمه آتش‌سوزی',
                    'expiry_date': contractor.fire_insurance_expiry,
                    'status': status
                })
        
        # بررسی صلاحیت پیمانکاری
        if contractor.contractor_certificate_expiry:
            if contractor.contractor_certificate_expiry <= thirty_days_later:
                status = 'expired' if contractor.contractor_certificate_expiry < today else 'warning'
                expired_docs.append({
                    'name': 'صلاحیت پیمانکاری',
                    'expiry_date': contractor.contractor_certificate_expiry,
                    'status': status
                })
        
        # بررسی صلاحیت ایمنی
        if contractor.safety_certificate_expiry:
            if contractor.safety_certificate_expiry <= thirty_days_later:
                status = 'expired' if contractor.safety_certificate_expiry < today else 'warning'
                expired_docs.append({
                    'name': 'صلاحیت ایمنی',
                    'expiry_date': contractor.safety_certificate_expiry,
                    'status': status
                })
        
        if expired_docs:
            expired_contractors.append({
                'id': contractor.id,
                'company_name': contractor.company_name,
                'expired_documents': expired_docs
            })
    
    # محاسبه تعداد خودروها بر اساس دسته‌بندی
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


# =====================================
# View 2: لاگین پیمانکاران
# =====================================
def contractor_login(request):
    """صفحه ورود اختصاصی پیمانکاران و پرسنل"""
    
    # اگر کاربر قبلاً لاگین کرده، هدایت به پورتال
    if request.user.is_authenticated:
        if hasattr(request.user, 'employee'):
            return redirect('contractor_management:contractor_portal')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # بررسی اینکه کاربر پیمانکار یا کارمند است
            if hasattr(user, 'employee'):
                login(request, user)
                messages.success(request, f'خوش آمدید {user.get_full_name()}')
                return redirect('contractor_management:contractor_portal')
            else:
                messages.error(request, 'شما مجوز ورود به این بخش را ندارید.')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    
    return render(request, 'contractor_management/auth/contractor_login.html')


# =====================================
# View 3: پورتال پیمانکاران
# =====================================
@login_required
def contractor_portal_dashboard(request):
    """داشبورد پورتال کاربری پیمانکاران"""
    
    # بررسی دسترسی
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'شما مجوز دسترسی به این بخش را ندارید.')
        return redirect('accounts:login')
    
    employee = request.user.employee
    
    # محاسبه درصد تکمیل پروفایل
    profile_completion = 0
    has_personal_info = False
    has_documents = False
    has_training = False
    
    # بررسی اطلاعات شخصی
    if employee.first_name and employee.last_name and employee.national_id and employee.birth_date:
        has_personal_info = True
        profile_completion += 33
    
    # بررسی مدارک
    documents_uploaded = 0
    if employee.card_national_img:
        documents_uploaded += 1
    if employee.certificate_img:
        documents_uploaded += 1
    if employee.health_certificate:
        documents_uploaded += 1
    if employee.background_check:
        documents_uploaded += 1
    
    if documents_uploaded >= 3:  # حداقل 3 مدرک
        has_documents = True
        profile_completion += 33
    
    # بررسی آموزش‌ها
    if employee.safety_training:
        has_training = True
        profile_completion += 34
    
    # لیست اقدامات مورد نیاز
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
            'description': 'لطفاً مدارک هویتی و سلامت خود را بارگذاری کنید',
            'link': reverse('contractor_management:contractor_profile') + '#documents'
        })
    
    if not has_training:
        required_actions.append({
            'title': 'گذراندن دوره ایمنی',
            'description': 'لطفاً گواهی دوره آموزش ایمنی عمومی را بارگذاری کنید',
            'link': reverse('contractor_management:contractor_profile') + '#training'
        })
    
    # بررسی مدارک منقضی شده
    today = date.today()
    if employee.entry_permit_expiration and employee.entry_permit_expiration <= today + timedelta(days=30):
        required_actions.append({
            'title': 'تمدید مجوز ورود',
            'description': f'مجوز ورود شما در تاریخ {employee.entry_permit_expiration} منقضی می‌شود',
            'link': reverse('contractor_management:contractor_profile')
        })
    
    context = {
        'today': today,
        'profile_completion': profile_completion,
        'profile': {
            'has_personal_info': has_personal_info,
            'has_documents': has_documents,
            'has_training': has_training,
        },
        'required_actions': required_actions,
        'recent_activity': None,  # می‌توانید بعداً اضافه کنید
    }
    
    return render(request, 'contractor_management/auth/contractor_portal.html', context)


# =====================================
# View 4: پروفایل و مدارک
# =====================================
@login_required
def contractor_profile_documents(request):
    """صفحه مدیریت پروفایل و مدارک کاربر"""
    
    # بررسی دسترسی
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'شما مجوز دسترسی به این بخش را ندارید.')
        return redirect('accounts:login')
    
    employee = request.user.employee
    
    if request.method == 'POST':
        # پردازش آپلود فایل‌ها
        # این بخش را بعداً پیاده‌سازی می‌کنیم
        pass
    
    context = {
        'employee': employee,
    }
    
    return render(request, 'contractor_management/auth/contractor_profile.html', context)
```

---

## 📝 نکات مهم

### 1. وابستگی‌ها
این کدها نیاز به این imports دارند:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from datetime import datetime, timedelta, date
from .models import Contractor, Employee, Vehicle, Report
```

### 2. مجوزها (Permissions)
در حال حاضر از `@login_required` استفاده شده. اگر می‌خواهید از سیستم permission استفاده کنید:

```python
from permissions.utils import permission_required

@permission_required("view_contractor_dashboard")
def contractor_dashboard(request):
    ...
```

### 3. رابطه User و Employee
کد فرض می‌کند که:
- در مدل `Employee` یک `OneToOneField` به `User` وجود دارد
- با `user.employee` می‌توان به اطلاعات کارمند دسترسی داشت

اگر این رابطه وجود ندارد، باید به مدل `Employee` اضافه شود:

```python
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    # ... سایر فیلدها
```

---

## 🧪 تست

بعد از اضافه کردن viewها:

1. **تست داشبورد:**
```
http://localhost:8000/contractor-management/dashboard/
```

2. **تست لاگین پیمانکاران:**
```
http://localhost:8000/contractor-management/contractor-login/
```

3. **تست پورتال:**
```
http://localhost:8000/contractor-management/contractor-portal/
```

---

## 🔄 مراحل بعدی

1. ✅ کپی کردن کد viewها به `views.py`
2. ✅ ایجاد یک کاربر تست با employee مرتبط
3. ✅ تست تمامی صفحات
4. ✅ ایجاد صفحه پروفایل/مدارک (template)
5. ✅ پیاده‌سازی آپلود فایل

---

**تاریخ:** 1403/10/30
**وضعیت:** آماده برای پیاده‌سازی ✨
