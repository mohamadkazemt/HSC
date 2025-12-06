from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.template.loader import render_to_string
import json
from django.forms import formset_factory
from datetime import datetime, timedelta
import csv
from io import StringIO
import jdatetime
import re
import pandas as pd
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View
import io

from accounts.models import UserProfile
from permissions.utils import permission_required
from dashboard.models import Notification
from contractor_management.models import Employee

from .models import (
    MedicalVisit, 
    MedicineUsage, 
    Medicine, 
    MedicineCategory, 
    MedicalService,
    MedicineReturn,
    Hospital,
    EmergencyEquipment
)
from .forms import (
    MedicalVisitForm, 
    MedicineSelectForm, 
    MedicineForm, 
    MedicineCategoryForm, 
    MedicalServiceForm,
    MedicineReturnForm,
    HospitalForm,
    EmergencyEquipmentForm,
    EmergencyPersonnelForm
)
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from functools import wraps

def emergency_personnel_required(view_func):
    """دکوریتور برای محدود کردن دسترسی به پرسنل اورژانس"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # چک کردن اینکه کاربر پرسنل اورژانس است
        is_emergency_personnel = request.user.groups.filter(
            name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
        ).exists()
        
        if not is_emergency_personnel and not request.user.is_superuser:
            messages.error(request, 'شما مجوز دسترسی به پورتال اورژانس ندارید.')
            return redirect('emergency_services:emergency_login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def persian_to_english_numbers(text):
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers, english_numbers)
    return text.translate(translation_table)

@login_required
@emergency_personnel_required
def visit_list(request):
    """لیست مراجعات پزشکی"""
    visits = MedicalVisit.objects.all().order_by('-visit_time')
    
    # فیلترها
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    personnel_type = request.GET.get('personnel_type')
    service_type = request.GET.get('service_type')
    medicine_category = request.GET.get('medicine_category')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            visits = visits.filter(visit_time__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to + timedelta(days=1)  # تا پایان روز
            visits = visits.filter(visit_time__lt=date_to)
        except ValueError:
            pass
    
    if personnel_type:
        visits = visits.filter(personnel_type=personnel_type)
    
    if service_type:
        visits = visits.filter(services__id=service_type)
    
    if medicine_category:
        visits = visits.filter(medicine_usages__medicine__category__id=medicine_category)
    
    # صفحه‌بندی
    paginator = Paginator(visits, 25)
    page = request.GET.get('page')
    visits = paginator.get_page(page)
    
    # برای فیلترها
    services = MedicalService.objects.all()
    medicine_categories = MedicineCategory.objects.all()
    
    context = {
        'visits': visits,
        'services': services,
        'medicine_categories': medicine_categories,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'personnel_type': personnel_type,
            'service_type': service_type,
            'medicine_category': medicine_category,
        }
    }
    
    return render(request, 'emergency_services/visit_list.html', context)

@login_required
@emergency_personnel_required
def create_visit(request):
    """ایجاد مراجعه جدید"""
    MedicineSelectFormSet = formset_factory(MedicineSelectForm, extra=1)
    
    if request.method == 'POST':
        print('POST data:', request.POST)  # لاگ داده‌های POST دریافتی
        
        # کپی کردن داده‌های POST برای تغییر
        data = request.POST.copy()
        
        # تبدیل تاریخ‌های دریافتی
        date_conversion_errors = []
        try:
            # تبدیل تاریخ مراجعه
            if data.get('visit_time'):
                try:
                    visit_time = persian_to_english_numbers(data['visit_time'].strip())
                    visit_time = re.sub(r'[^0-9/ :]', '', visit_time)
                    if ' ' not in visit_time:
                        date_conversion_errors.append('فرمت زمان مراجعه نامعتبر است. لطفاً تاریخ و ساعت را با فاصله وارد کنید.')
                    else:
                        date_part, time_part = visit_time.split(' ', 1)
                        year, month, day = map(int, date_part.split('/'))
                        
                        # جدا کردن ساعت، دقیقه، ثانیه و میلی‌ثانیه
                        time_parts = time_part.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        second = int(time_parts[2].split('.')[0]) if len(time_parts) > 2 and '.' in time_parts[2] else (int(time_parts[2]) if len(time_parts) > 2 else 0)
                        
                        # تصحیح سال دو رقمی
                        if year < 100:
                            year += 1400
                        
                        # تبدیل به تاریخ میلادی
                        jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
                        gregorian_date = jalali_date.togregorian()
                        data['visit_time'] = gregorian_date.strftime('%Y-%m-%d %H:%M:%S')
                        print('Converted visit time:', data['visit_time'])
                except (ValueError, IndexError, AttributeError) as e:
                    date_conversion_errors.append(f'خطا در تبدیل زمان مراجعه: {str(e)}')
                    print('Error converting visit_time:', str(e))
            
            # تبدیل تاریخ پذیرش در بیمارستان
            if data.get('hospital_admission_time'):
                try:
                    admission_time = persian_to_english_numbers(data['hospital_admission_time'].strip())
                    admission_time = re.sub(r'[^0-9/ :]', '', admission_time)
                    if ' ' not in admission_time:
                        date_conversion_errors.append('فرمت زمان پذیرش در بیمارستان نامعتبر است.')
                    else:
                        date_part, time_part = admission_time.split(' ', 1)
                        year, month, day = map(int, date_part.split('/'))
                        
                        # جدا کردن ساعت، دقیقه، ثانیه و میلی‌ثانیه
                        time_parts = time_part.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        second = int(time_parts[2].split('.')[0]) if len(time_parts) > 2 and '.' in time_parts[2] else (int(time_parts[2]) if len(time_parts) > 2 else 0)
                        
                        # تصحیح سال دو رقمی
                        if year < 100:
                            year += 1400
                        
                        # تبدیل به تاریخ میلادی
                        jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
                        gregorian_date = jalali_date.togregorian()
                        data['hospital_admission_time'] = gregorian_date.strftime('%Y-%m-%d %H:%M:%S')
                        print('Converted admission time:', data['hospital_admission_time'])
                except (ValueError, IndexError, AttributeError) as e:
                    date_conversion_errors.append(f'خطا در تبدیل زمان پذیرش: {str(e)}')
                    print('Error converting hospital_admission_time:', str(e))
            
            # تبدیل تاریخ ترخیص از بیمارستان
            if data.get('hospital_discharge_time'):
                try:
                    discharge_time = persian_to_english_numbers(data['hospital_discharge_time'].strip())
                    discharge_time = re.sub(r'[^0-9/ :]', '', discharge_time)
                    if ' ' not in discharge_time:
                        date_conversion_errors.append('فرمت زمان ترخیص از بیمارستان نامعتبر است.')
                    else:
                        date_part, time_part = discharge_time.split(' ', 1)
                        year, month, day = map(int, date_part.split('/'))
                        
                        # جدا کردن ساعت، دقیقه، ثانیه و میلی‌ثانیه
                        time_parts = time_part.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                        second = int(time_parts[2].split('.')[0]) if len(time_parts) > 2 and '.' in time_parts[2] else (int(time_parts[2]) if len(time_parts) > 2 else 0)
                        
                        # تصحیح سال دو رقمی
                        if year < 100:
                            year += 1400
                        
                        # تبدیل به تاریخ میلادی
                        jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
                        gregorian_date = jalali_date.togregorian()
                        data['hospital_discharge_time'] = gregorian_date.strftime('%Y-%m-%d %H:%M:%S')
                        print('Converted discharge time:', data['hospital_discharge_time'])
                except (ValueError, IndexError, AttributeError) as e:
                    date_conversion_errors.append(f'خطا در تبدیل زمان ترخیص: {str(e)}')
                    print('Error converting hospital_discharge_time:', str(e))
            
            # اگر خطا در تبدیل تاریخ‌ها وجود داشت، فرم را با خطا نمایش بده
            if date_conversion_errors:
                for error_msg in date_conversion_errors:
                    messages.error(request, error_msg)
                form = MedicalVisitForm(data)
                medicine_formset = MedicineSelectFormSet(data, prefix='medicines')
                services = MedicalService.objects.all()
                initial_personnel_type = request.POST.get('personnel_type') or 'company'
                return render(request, 'emergency_services/visit_form.html', {
                    'form': form,
                    'medicine_formset': medicine_formset,
                    'services': services,
                    'initial_personnel_type': initial_personnel_type,
                })
        except Exception as e:
            print('Unexpected error converting dates:', str(e))
            messages.error(request, f'خطای غیرمنتظره در تبدیل تاریخ‌ها: {str(e)}')
            form = MedicalVisitForm(data)
            medicine_formset = MedicineSelectFormSet(data, prefix='medicines')
            services = MedicalService.objects.all()
            initial_personnel_type = request.POST.get('personnel_type') or 'company'
            return render(request, 'emergency_services/visit_form.html', {
                'form': form,
                'medicine_formset': medicine_formset,
                'services': services,
                'initial_personnel_type': initial_personnel_type,
            })
        
        form = MedicalVisitForm(data)
        medicine_formset = MedicineSelectFormSet(data, prefix='medicines')
        
        if form.is_valid() and medicine_formset.is_valid():
            try:
                # لاگ مقادیر تاریخ قبل از ذخیره
                print('Visit time from form:', form.cleaned_data.get('visit_time'))
                print('Hospital admission time from form:', form.cleaned_data.get('hospital_admission_time'))
                print('Hospital discharge time from form:', form.cleaned_data.get('hospital_discharge_time'))
                
                # ذخیره فرم مراجعه
                visit = form.save(commit=False)
                # ایجاد UserProfile در صورت عدم وجود
                user_profile, created = UserProfile.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'personnel_code': '',
                        'mobile': '',
                    }
                )
                visit.created_by = user_profile
                visit.save()
                form.save_m2m()  # ذخیره رابطه چند به چند خدمات
                
                # لاگ مقادیر تاریخ بعد از ذخیره
                print('Visit time in model:', visit.visit_time)
                print('Hospital admission time in model:', visit.hospital_admission_time)
                print('Hospital discharge time in model:', visit.hospital_discharge_time)
                
                # ذخیره داروهای انتخاب شده
                for medicine_form in medicine_formset:
                    if medicine_form.cleaned_data and medicine_form.cleaned_data.get('medicine'):
                        medicine = medicine_form.cleaned_data['medicine']
                        quantity = medicine_form.cleaned_data['quantity']
                        
                        # ایجاد رکورد استفاده دارو
                        MedicineUsage.objects.create(
                            visit=visit,
                            medicine=medicine,
                            quantity=quantity
                        )
                
                messages.success(request, 'مراجعه با موفقیت ثبت شد.')
                return redirect('emergency_services:visit_detail', pk=visit.pk)
            except Exception as e:
                print('Error in saving visit:', str(e))  # لاگ خطاهای احتمالی
                messages.error(request, f'خطا در ثبت مراجعه: {str(e)}')
                return render(request, 'emergency_services/visit_form.html', {
                    'form': form,
                    'medicine_formset': medicine_formset,
                    'services': MedicalService.objects.all(),
                })
        else:
            print('Form errors:', form.errors)  # لاگ خطاهای فرم
            print('Medicine formset errors:', medicine_formset.errors)  # لاگ خطاهای فرم‌ست داروها
            
            # جمع‌آوری تمام خطاها برای نمایش به کاربر
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if field in form.fields else field
                    error_messages.append(f"{field_label}: {error}")
            
            for form_index, form_errors in enumerate(medicine_formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            error_messages.append(f"دارو (ردیف {form_index + 1}): {error}")
            
            if error_messages:
                messages.error(request, 'لطفاً خطاهای زیر را برطرف کنید:')
                for msg in error_messages[:5]:  # نمایش حداکثر 5 خطای اول
                    messages.error(request, f'  • {msg}')
                if len(error_messages) > 5:
                    messages.error(request, f'  و {len(error_messages) - 5} خطای دیگر...')
    else:
        form = MedicalVisitForm()
        medicine_formset = MedicineSelectFormSet(prefix='medicines')
    
    services = MedicalService.objects.all()
    
    # تعیین نوع پرسنل از POST یا از فرم یا مقدار پیش‌فرض
    if request.method == 'POST':
        initial_personnel_type = request.POST.get('personnel_type') or form.data.get('personnel_type') or 'company'
    else:
        initial_personnel_type = getattr(form, 'initial', {}).get('personnel_type') or 'company'

    context = {
        'form': form,
        'medicine_formset': medicine_formset,
        'services': services,
        'initial_personnel_type': initial_personnel_type,
    }
    
    return render(request, 'emergency_services/visit_form.html', context)

@login_required
@emergency_personnel_required
def visit_detail(request, pk):
    """جزئیات مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    medicine_usages = visit.medicine_usages.all()
    
    context = {
        'visit': visit,
        'medicine_usages': medicine_usages,
    }
    
    return render(request, 'emergency_services/visit_detail.html', context)

@login_required
@emergency_personnel_required
def edit_visit(request, pk):
    """ویرایش مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    
    if request.method == 'POST':
        data = request.POST.copy()
        try:
            if data.get('visit_time'):
                vt = persian_to_english_numbers(data['visit_time'].strip())
                vt = re.sub(r'[^0-9/ :]', '', vt)
                d, t = vt.split(' ')
                y, m, day = map(int, d.split('/'))
                hh, mm, ss = t.split(':')
                ss = ss.split('.')[0]
                if y < 100: y += 1400
                g = jdatetime.datetime(y, int(m), int(day), int(hh), int(mm), int(ss)).togregorian()
                data['visit_time'] = g.strftime('%Y-%m-%d %H:%M:%S')
            if data.get('hospital_admission_time'):
                at = persian_to_english_numbers(data['hospital_admission_time'].strip())
                at = re.sub(r'[^0-9/ :]', '', at)
                d, t = at.split(' ')
                y, m, day = map(int, d.split('/'))
                hh, mm, ss = t.split(':')
                ss = ss.split('.')[0]
                if y < 100: y += 1400
                g = jdatetime.datetime(y, int(m), int(day), int(hh), int(mm), int(ss)).togregorian()
                data['hospital_admission_time'] = g.strftime('%Y-%m-%d %H:%M:%S')
            if data.get('hospital_discharge_time'):
                dt = persian_to_english_numbers(data['hospital_discharge_time'].strip())
                dt = re.sub(r'[^0-9/ :]', '', dt)
                d, t = dt.split(' ')
                y, m, day = map(int, d.split('/'))
                hh, mm, ss = t.split(':')
                ss = ss.split('.')[0]
                if y < 100: y += 1400
                g = jdatetime.datetime(y, int(m), int(day), int(hh), int(mm), int(ss)).togregorian()
                data['hospital_discharge_time'] = g.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            messages.error(request, 'فرمت تاریخ/زمان نامعتبر است. (نمونه 1404/02/07 18:49:51)')
            form = MedicalVisitForm(instance=visit)
            return render(request, 'emergency_services/visit_edit.html', {'form': form, 'visit': visit, 'medicine_usages': visit.medicine_usages.all()})
        
        form = MedicalVisitForm(data, instance=visit)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'مراجعه با موفقیت بروزرسانی شد.')
            return redirect('emergency_services:visit_detail', pk=visit.pk)
    else:
        form = MedicalVisitForm(instance=visit)
    
    context = {
        'form': form,
        'visit': visit,
        'medicine_usages': visit.medicine_usages.all(),
    }
    
    return render(request, 'emergency_services/visit_edit.html', context)

@login_required
@emergency_personnel_required
def add_medicine_to_visit(request, visit_id):
    """افزودن دارو به مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=visit_id)
    
    if request.method == 'POST':
        form = MedicineSelectForm(request.POST)
        
        if form.is_valid():
            medicine = form.cleaned_data['medicine']
            quantity = form.cleaned_data['quantity']
            
            # ایجاد رکورد استفاده دارو
            MedicineUsage.objects.create(
                visit=visit,
                medicine=medicine,
                quantity=quantity
            )
            
            messages.success(request, f'داروی {medicine.name} با موفقیت به مراجعه اضافه شد.')
            return redirect('emergency_services:visit_detail', pk=visit.pk)
    else:
        form = MedicineSelectForm()
    
    context = {
        'form': form,
        'visit': visit,
    }
    
    return render(request, 'emergency_services/add_medicine.html', context)

@login_required
@emergency_personnel_required
def remove_medicine_from_visit(request, usage_id):
    """حذف دارو از مراجعه"""
    usage = get_object_or_404(MedicineUsage, pk=usage_id)
    visit_id = usage.visit.pk
    
    medicine_name = usage.medicine.name
    usage.delete()
    
    messages.success(request, f'داروی {medicine_name} با موفقیت از مراجعه حذف شد.')
    return redirect('emergency_services:visit_detail', pk=visit_id)

@login_required
@emergency_personnel_required
@login_required
@emergency_personnel_required
def medicine_list(request):
    """لیست داروها"""
    medicines = Medicine.objects.all().order_by('name')
    
    # فیلترها
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category')
    is_expired = request.GET.get('is_expired')
    is_critical = request.GET.get('is_critical')
    is_active = request.GET.get('is_active')
    
    # جستجو در تمام ستون‌ها
    if search:
        medicines = medicines.filter(
            Q(name__icontains=search) |
            Q(category__name__icontains=search) |
            Q(drug_type__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category:
        medicines = medicines.filter(category_id=category)
    
    if is_expired == 'true':
        medicines = medicines.filter(expiry_date__lt=timezone.now().date())
    
    if is_critical == 'true':
        medicines = medicines.filter(quantity__lte=F('critical_threshold'))
    
    if is_active:
        is_active_bool = is_active == 'true'
        medicines = medicines.filter(is_active=is_active_bool)
    
    # صفحه‌بندی
    paginator = Paginator(medicines, 25)
    page = request.GET.get('page')
    medicines = paginator.get_page(page)
    
    # برای فیلترها
    categories = MedicineCategory.objects.all()
    
    context = {
        'medicines': medicines,
        'categories': categories,
        'filters': {
            'search': search,
            'category': category,
            'is_expired': is_expired,
            'is_critical': is_critical,
            'is_active': is_active,
        }
    }
    
    return render(request, 'emergency_services/medicine_list.html', context)

@login_required
@emergency_personnel_required
def create_medicine(request):
    """ایجاد داروی جدید"""
    if request.method == 'POST':
        data = request.POST.copy()
        expiry_date = data.get('expiry_date')
        print('POST data:', request.POST)  # لاگ داده‌های POST
        print('Expiry date from POST:', expiry_date)  # لاگ تاریخ دریافتی
        
        # تبدیل تاریخ شمسی به میلادی
        if expiry_date:
            try:
                # تبدیل اعداد فارسی به انگلیسی
                expiry_date = persian_to_english_numbers(expiry_date.strip())
                # حذف کاراکترهای اضافی
                expiry_date = re.sub(r'[^0-9/]', '', expiry_date)
                year, month, day = map(int, expiry_date.split('/'))
                
                # تصحیح سال دو رقمی
                if year < 100:
                    year += 1400
                
                # تبدیل به تاریخ میلادی
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                data['expiry_date'] = gregorian_date.strftime('%Y-%m-%d')
                print('Converted to Gregorian:', data['expiry_date'])
            except (ValueError, IndexError, AttributeError) as e:
                print('Error converting date:', str(e))
                messages.error(request, 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)')
                form = MedicineForm()
                return render(request, 'emergency_services/medicine_form.html', {
                    'form': form,
                    'title': 'افزودن داروی جدید'
                })
        
        form = MedicineForm(data)
        
        if form.is_valid():
            print('Form is valid')
            print('Cleaned expiry date:', form.cleaned_data.get('expiry_date'))  # لاگ تاریخ پردازش شده
            form.save()
            messages.success(request, 'داروی جدید با موفقیت اضافه شد.')
            return redirect('emergency_services:medicine_list')
        else:
            print('Form errors:', form.errors)  # لاگ خطاهای فرم
            print('Form expiry_date errors:', form.errors.get('expiry_date'))  # لاگ خطاهای مربوط به تاریخ
    else:
        form = MedicineForm()
    
    context = {
        'form': form,
        'title': 'افزودن داروی جدید',
    }
    
    return render(request, 'emergency_services/medicine_form.html', context)

@login_required
@emergency_personnel_required
def edit_medicine(request, pk):
    """ویرایش دارو"""
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        data = request.POST.copy()
        expiry_date = data.get('expiry_date')
        print('POST data:', request.POST)  # لاگ داده‌های POST
        print('Expiry date from POST:', expiry_date)  # لاگ تاریخ دریافتی
        
        # تبدیل تاریخ شمسی به میلادی
        if expiry_date:
            try:
                # تبدیل اعداد فارسی به انگلیسی
                expiry_date = persian_to_english_numbers(expiry_date.strip())
                # حذف کاراکترهای اضافی
                expiry_date = re.sub(r'[^0-9/]', '', expiry_date)
                year, month, day = map(int, expiry_date.split('/'))
                
                # تصحیح سال دو رقمی
                if year < 100:
                    year += 1400
                
                # تبدیل به تاریخ میلادی
                jalali_date = jdatetime.date(year, month, day)
                gregorian_date = jalali_date.togregorian()
                data['expiry_date'] = gregorian_date.strftime('%Y-%m-%d')
                print('Converted to Gregorian:', data['expiry_date'])
            except (ValueError, IndexError, AttributeError) as e:
                print('Error converting date:', str(e))
                messages.error(request, 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)')
                form = MedicineForm(instance=medicine)
                return render(request, 'emergency_services/medicine_form.html', {
                    'form': form,
                    'medicine': medicine,
                    'title': f'ویرایش داروی {medicine.name}'
                })
        
        form = MedicineForm(data, instance=medicine)
        
        if form.is_valid():
            print('Form is valid')
            print('Cleaned expiry date:', form.cleaned_data.get('expiry_date'))  # لاگ تاریخ پردازش شده
            form.save()
            messages.success(request, 'دارو با موفقیت بروزرسانی شد.')
            return redirect('emergency_services:medicine_list')
        else:
            print('Form errors:', form.errors)  # لاگ خطاهای فرم
            print('Form expiry_date errors:', form.errors.get('expiry_date'))  # لاگ خطاهای مربوط به تاریخ
    else:
        form = MedicineForm(instance=medicine)
    
    context = {
        'form': form,
        'medicine': medicine,
        'title': f'ویرایش داروی {medicine.name}',
    }
    
    return render(request, 'emergency_services/medicine_form.html', context)

@login_required
@emergency_personnel_required
def category_list(request):
    """لیست دسته‌بندی‌ها"""
    categories = MedicineCategory.objects.all()
    
    if request.method == 'POST':
        form = MedicineCategoryForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'دسته‌بندی جدید با موفقیت اضافه شد.')
            return redirect('emergency_services:category_list')
    else:
        form = MedicineCategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    
    return render(request, 'emergency_services/category_list.html', context)

@login_required
@emergency_personnel_required
def edit_category(request, pk):
    """ویرایش دسته‌بندی"""
    category = get_object_or_404(MedicineCategory, pk=pk)
    
    if request.method == 'POST':
        form = MedicineCategoryForm(request.POST, instance=category)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'دسته‌بندی با موفقیت بروزرسانی شد.')
            return redirect('emergency_services:category_list')
    else:
        form = MedicineCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
    }
    
    return render(request, 'emergency_services/category_edit.html', context)

@login_required
@emergency_personnel_required
def service_list(request):
    """لیست خدمات درمانی"""
    services = MedicalService.objects.all()
    
    if request.method == 'POST':
        form = MedicalServiceForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'خدمت درمانی جدید با موفقیت اضافه شد.')
            return redirect('emergency_services:service_list')
    else:
        form = MedicalServiceForm()
    
    context = {
        'services': services,
        'form': form,
    }
    
    return render(request, 'emergency_services/service_list.html', context)

@login_required
@emergency_personnel_required
def edit_service(request, pk):
    """ویرایش خدمت درمانی"""
    service = get_object_or_404(MedicalService, pk=pk)
    
    if request.method == 'POST':
        form = MedicalServiceForm(request.POST, instance=service)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'خدمت درمانی با موفقیت بروزرسانی شد.')
            return redirect('emergency_services:service_list')
    else:
        form = MedicalServiceForm(instance=service)
    
    context = {
        'form': form,
        'service': service,
    }
    
    return render(request, 'emergency_services/service_edit.html', context)

@login_required
@emergency_personnel_required
def return_medicine(request, usage_id):
    """برگشت دارو به انبار"""
    usage = get_object_or_404(MedicineUsage, pk=usage_id)
    
    if request.method == 'POST':
        form = MedicineReturnForm(request.POST, usage=usage)
        
        if form.is_valid():
            return_obj = form.save(commit=False)
            return_obj.usage = usage
            # ایجاد UserProfile در صورت عدم وجود
            user_profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'personnel_code': '',
                    'mobile': '',
                }
            )
            return_obj.returned_by = user_profile
            return_obj.save()
            
            messages.success(request, f'برگشت {return_obj.quantity} عدد {usage.medicine.name} با موفقیت ثبت شد.')
            return redirect('emergency_services:visit_detail', pk=usage.visit.pk)
    else:
        form = MedicineReturnForm(usage=usage)
    
    context = {
        'form': form,
        'usage': usage,
    }
    
    return render(request, 'emergency_services/return_medicine.html', context)

@login_required
def dashboard(request):
    """داشبورد اورژانس معدن"""
    # چک کردن اینکه کاربر پرسنل اورژانس است
    is_emergency_personnel = request.user.groups.filter(
        name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
    ).exists()
    
    # اگر پرسنل اورژانس نیست و سوپریوزر هم نیست
    if not is_emergency_personnel and not request.user.is_superuser:
        messages.error(request, 'شما مجوز دسترسی به پورتال اورژانس نیستید.')
        return redirect('dashboard:home')
    
    # تشخیص نقش کاربر
    user_role = None
    user_groups = request.user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse'])
    if user_groups.exists():
        user_role = user_groups.first().name
    
    # آمار کلی مراجعات
    total_visits = MedicalVisit.objects.count()
    today_visits = MedicalVisit.objects.filter(visit_time__date=timezone.now().date()).count()
    monthly_visits = MedicalVisit.objects.filter(visit_time__month=timezone.now().month).count()
    
    # آمار مراجعات پرسنل شرکت و پیمانکار
    company_visits = MedicalVisit.objects.filter(personnel_type='company').count()
    contractor_visits = MedicalVisit.objects.filter(personnel_type='contractor').count()
    
    # آمار خاص بر اساس نقش
    my_visits_count = 0
    my_recent_visits = []
    if user_role in ['EmergencyDoctor', 'EmergencyNurse']:
        # created_by is ForeignKey to UserProfile, so we need to filter by userprofile__user
        try:
            user_profile = request.user.userprofile
            my_visits_count = MedicalVisit.objects.filter(created_by=user_profile).count()
            my_recent_visits = MedicalVisit.objects.filter(created_by=user_profile).order_by('-visit_time')[:5]
        except:
            pass
    
    # آمار داروها
    total_medicines = Medicine.objects.count()
    low_stock_medicines = Medicine.objects.filter(quantity__lte=F('critical_threshold')).count()
    expired_medicines = Medicine.objects.filter(expiry_date__lt=timezone.now().date()).count()
    critical_medicines = Medicine.objects.filter(quantity__lte=F('critical_threshold')).order_by('quantity')[:5]
    expired_medicines_list = Medicine.objects.filter(expiry_date__lt=timezone.now().date()).order_by('expiry_date')[:5]
    
    # تجهیزات - وضعیت کالیبراسیون
    equip_calibration_due = EmergencyEquipment.objects.filter(next_calibration_date__lte=timezone.now().date() + timedelta(days=30)).count()
    equip_calibration_overdue = EmergencyEquipment.objects.filter(next_calibration_date__lt=timezone.now().date()).count()
    
    # خدمات پرمصرف
    # For ManyToMany reverse relationship, use medicalvisit (lowercase model name)
    popular_services = MedicalService.objects.annotate(
        usage_count=Count('medicalvisit')
    ).order_by('-usage_count')[:5]
    
    # داروهای پرمصرف
    popular_medicines = Medicine.objects.annotate(
        usage_count=Count('medicineusage')
    ).order_by('-usage_count')[:5]
    
    # نمودار مراجعات هفتگی
    weekly_visits = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        count = MedicalVisit.objects.filter(visit_time__date=date).count()
        weekly_visits.append({
            'date': date.isoformat(),  # تبدیل به string برای JSON
            'count': count
        })
    weekly_visits.reverse()
    
    # بیشترین مراجعه‌کننده در ماه جاری
    # فیلتر مراجعات ماه جاری
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_visits_qs = MedicalVisit.objects.filter(
        visit_time__year=current_year,
        visit_time__month=current_month
    )
    
    # شمارش مراجعات برای هر فرد (پرسنل شرکت)
    company_visitors = monthly_visits_qs.filter(
        personnel_type='company',
        company_personnel__isnull=False
    ).values('company_personnel').annotate(
        visit_count=Count('id')
    ).order_by('-visit_count')
    
    # شمارش مراجعات برای هر فرد (پرسنل پیمانکار)
    contractor_visitors = monthly_visits_qs.filter(
        personnel_type='contractor',
        contractor_personnel__isnull=False
    ).values('contractor_personnel').annotate(
        visit_count=Count('id')
    ).order_by('-visit_count')
    
    # پیدا کردن بیشترین تعداد مراجعات
    top_visitors = []
    max_count = 0
    
    # بررسی پرسنل شرکت
    for visitor in company_visitors:
        count = visitor['visit_count']
        try:
            person = UserProfile.objects.get(pk=visitor['company_personnel'])
            if count > max_count:
                max_count = count
                top_visitors = [{
                    'person': person,
                    'count': count,
                    'type': 'company'
                }]
            elif count == max_count and max_count > 0:
                top_visitors.append({
                    'person': person,
                    'count': count,
                    'type': 'company'
                })
        except UserProfile.DoesNotExist:
            continue
    
    # بررسی پرسنل پیمانکار
    for visitor in contractor_visitors:
        count = visitor['visit_count']
        try:
            person = Employee.objects.get(pk=visitor['contractor_personnel'])
            if count > max_count:
                max_count = count
                top_visitors = [{
                    'person': person,
                    'count': count,
                    'type': 'contractor'
                }]
            elif count == max_count and max_count > 0:
                top_visitors.append({
                    'person': person,
                    'count': count,
                    'type': 'contractor'
                })
        except Employee.DoesNotExist:
            continue
    
    context = {
        'total_visits': total_visits,
        'today_visits': today_visits,
        'monthly_visits': monthly_visits,
        'company_visits': company_visits,
        'contractor_visits': contractor_visits,
        'total_medicines': total_medicines,
        'low_stock_medicines': low_stock_medicines,
        'expired_medicines': expired_medicines,
        'critical_medicines': critical_medicines,
        'popular_services': popular_services,
        'popular_medicines': popular_medicines,
        'weekly_visits': weekly_visits,
        'expired_medicines_list': expired_medicines_list,
        'equip_calibration_due': equip_calibration_due,
        'equip_calibration_overdue': equip_calibration_overdue,
        'user_role': user_role,
        'my_visits_count': my_visits_count,
        'my_recent_visits': my_recent_visits,
        'top_visitors': top_visitors,
        'max_visit_count': max_count,
    }
    
    return render(request, 'emergency_services/dashboard.html', context)

@login_required
@emergency_personnel_required
def export_visits_csv(request):
    """خروجی CSV از مراجعات"""
    # فیلترها
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    personnel_type = request.GET.get('personnel_type')
    service_type = request.GET.get('service_type')
    
    visits = MedicalVisit.objects.all().order_by('-visit_time')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            visits = visits.filter(visit_time__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            date_to = date_to + timedelta(days=1)  # تا پایان روز
            visits = visits.filter(visit_time__lt=date_to)
        except ValueError:
            pass
    
    if personnel_type:
        visits = visits.filter(personnel_type=personnel_type)
    
    if service_type:
        visits = visits.filter(services__id=service_type)
    
    # ایجاد فایل CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="visits.csv"'
    
    # تنظیم هدرها و نوع انکودینگ
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response)
    writer.writerow(['تاریخ مراجعه', 'نام مراجعه کننده', 'نوع پرسنل', 'علت مراجعه', 'توصیه پزشک', 'خدمات', 'داروها'])
    
    for visit in visits:
        if visit.personnel_type == 'company':
            person_name = str(visit.company_personnel) if visit.company_personnel else ""
        else:
            person_name = str(visit.contractor_personnel) if visit.contractor_personnel else ""
        
        services = ", ".join([s.name for s in visit.services.all()])
        medicines = ", ".join([f"{m.medicine.name} ({m.quantity})" for m in visit.medicine_usages.all()])
        
        writer.writerow([
            visit.visit_time.strftime('%Y-%m-%d %H:%M'),
            person_name,
            visit.get_personnel_type_display(),
            visit.visit_reason,
            visit.doctor_recommendation,
            services,
            medicines
        ])
    
    return response

@login_required
@emergency_personnel_required
def export_medicines_csv(request):
    """خروجی CSV از داروها"""
    medicines = Medicine.objects.all().order_by('name')
    
    # ایجاد فایل CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="medicines.csv"'
    
    # تنظیم هدرها و نوع انکودینگ
    response.write(u'\ufeff'.encode('utf8'))
    
    writer = csv.writer(response)
    writer.writerow(['نام دارو', 'دسته‌بندی', 'موجودی فعلی', 'حد بحرانی', 'تاریخ انقضا', 'وضعیت'])
    
    for medicine in medicines:
        writer.writerow([
            medicine.name,
            medicine.category.name if medicine.category else "",
            medicine.quantity,
            medicine.critical_threshold,
            medicine.expiry_date.strftime('%Y-%m-%d'),
            'فعال' if medicine.is_active else 'غیرفعال'
        ])
    
    return response

@login_required
@emergency_personnel_required
def print_visit(request, pk):
    """چاپ فرم مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    medicine_usages = visit.medicine_usages.all()
    
    context = {
        'visit': visit,
        'medicine_usages': medicine_usages,
    }
    
    return render(request, 'emergency_services/print_visit.html', context)

@login_required
@emergency_personnel_required
def hospital_list(request):
    """لیست بیمارستان‌ها"""
    hospitals = Hospital.objects.all().order_by('name')
    
    context = {
        'hospitals': hospitals,
    }
    
    return render(request, 'emergency_services/hospital_list.html', context)

@login_required
@emergency_personnel_required
def create_hospital(request):
    """ایجاد بیمارستان جدید"""
    if request.method == 'POST':
        form = HospitalForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'بیمارستان با موفقیت ثبت شد.')
            return redirect('emergency_services:hospital_list')
    else:
        form = HospitalForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'emergency_services/hospital_form.html', context)

@login_required
@emergency_personnel_required
def edit_hospital(request, pk):
    """ویرایش بیمارستان"""
    hospital = get_object_or_404(Hospital, pk=pk)
    
    if request.method == 'POST':
        form = HospitalForm(request.POST, instance=hospital)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'بیمارستان با موفقیت بروزرسانی شد.')
            return redirect('emergency_services:hospital_list')
    else:
        form = HospitalForm(instance=hospital)
    
    context = {
        'form': form,
        'hospital': hospital,
    }
    
    return render(request, 'emergency_services/hospital_form.html', context)

@login_required
@emergency_personnel_required
def delete_hospital(request, pk):
    """حذف بیمارستان"""
    hospital = get_object_or_404(Hospital, pk=pk)
    
    # بررسی وجود مراجعات مرتبط
    if MedicalVisit.objects.filter(hospital=hospital).exists():
        messages.error(request, 'این بیمارستان دارای مراجعات مرتبط است و نمی‌توان آن را حذف کرد.')
        return redirect('emergency_services:hospital_list')
    
    hospital.delete()
    messages.success(request, 'بیمارستان با موفقیت حذف شد.')
    return redirect('emergency_services:hospital_list')

@method_decorator(permission_required("import_medicines_excel"), name='dispatch')
class ImportMedicinesExcelView(View):
    def post(self, request):
        try:
            excel_file = request.FILES['excel_file']
            
            # خواندن فایل اکسل
            df = pd.read_excel(excel_file)
            
            # بررسی ستون‌های مورد نیاز
            required_columns = ['نام دارو', 'دسته‌بندی', 'موجودی', 'حد بحرانی', 'تاریخ انقضا', 'وضعیت']
            if not all(col in df.columns for col in required_columns):
                return JsonResponse({
                    'status': 'error',
                    'message': 'ستون‌های فایل اکسل با فرمت مورد نظر مطابقت ندارد.'
                })
            
            success_count = 0
            error_count = 0
            errors = []
            
            # پردازش هر ردیف
            for index, row in df.iterrows():
                try:
                    # تبدیل تاریخ شمسی به میلادی
                    expiry_date = row['تاریخ انقضا']
                    if isinstance(expiry_date, str):
                        year, month, day = map(int, expiry_date.split('/'))
                        jalali_date = jdatetime.date(year, month, day)
                        expiry_date = jalali_date.togregorian()
                    
                    # تبدیل وضعیت به بولین
                    is_active = row['وضعیت'] == 'فعال'
                    
                    # یافتن یا ایجاد دسته‌بندی
                    category_name = row['دسته‌بندی']
                    category, created = MedicineCategory.objects.get_or_create(name=category_name)
                    
                    # ایجاد یا بروزرسانی دارو
                    medicine, created = Medicine.objects.update_or_create(
                        name=row['نام دارو'],
                        defaults={
                            'category': category,
                            'quantity': int(row['موجودی']),
                            'critical_threshold': int(row['حد بحرانی']),
                            'expiry_date': expiry_date,
                            'is_active': is_active
                        }
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f'خطا در ردیف {index + 2}: {str(e)}')
            
            return JsonResponse({
                'status': 'success',
                'message': f'تعداد {success_count} دارو با موفقیت وارد شدند.',
                'errors': errors if errors else None
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در پردازش فایل: {str(e)}'
            })

@permission_required("import_medicines_excel")
def download_sample_excel(request):
    # ایجاد یک DataFrame نمونه
    sample_data = {
        'نام دارو': ['پاراستامول', 'آموکسی سیلین', 'ایبوپروفن'],
        'دسته‌بندی': ['مسکن', 'آنتی‌بیوتیک', 'مسکن'],
        'موجودی': [100, 50, 75],
        'حد بحرانی': [20, 10, 15],
        'تاریخ انقضا': ['1403/12/29', '1403/11/15', '1404/01/10'],
        'وضعیت': ['فعال', 'فعال', 'غیرفعال']
    }
    
    df = pd.DataFrame(sample_data)
    
    # ایجاد فایل اکسل در حافظه
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='داروها')
        
        # تنظیم عرض ستون‌ها
        worksheet = writer.sheets['داروها']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
    
    output.seek(0)
    
    # ایجاد پاسخ HTTP
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=sample_medicines.xlsx'
    
    return response

@login_required
@emergency_personnel_required
def equipment_list(request):
    """لیست تجهیزات اورژانس"""
    equipments = EmergencyEquipment.objects.all().order_by('next_calibration_date')
    
    # فیلترها
    status = request.GET.get('status')
    calibration_status = request.GET.get('calibration_status')
    
    if status == 'active':
        equipments = equipments.filter(is_active=True)
    elif status == 'inactive':
        equipments = equipments.filter(is_active=False)
    
    if calibration_status == 'due':
        equipments = equipments.filter(next_calibration_date__lte=timezone.now().date() + timedelta(days=30))
    elif calibration_status == 'overdue':
        equipments = equipments.filter(next_calibration_date__lt=timezone.now().date())
    
    # صفحه‌بندی
    paginator = Paginator(equipments, 25)
    page = request.GET.get('page')
    equipments = paginator.get_page(page)
    
    context = {
        'equipments': equipments,
        'filters': {
            'status': status,
            'calibration_status': calibration_status,
        }
    }
    
    return render(request, 'emergency_services/equipment_list.html', context)

@login_required
@emergency_personnel_required
def create_equipment(request):
    """ایجاد تجهیز جدید"""
    if request.method == 'POST':
        data = request.POST.copy()
        # تبدیل تاریخ شمسی به میلادی
        for field in ['last_calibration_date', 'next_calibration_date']:
            date_val = data.get(field)
            if date_val:
                try:
                    date_val = persian_to_english_numbers(date_val.strip())
                    date_val = re.sub(r'[^0-9/]', '', date_val)
                    year, month, day = map(int, date_val.split('/'))
                    if year < 100:
                        year += 1400
                    jalali_date = jdatetime.date(year, month, day)
                    gregorian_date = jalali_date.togregorian()
                    data[field] = gregorian_date.strftime('%Y-%m-%d')
                except Exception as e:
                    messages.error(request, 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)')
                    form = EmergencyEquipmentForm()
                    return render(request, 'emergency_services/equipment_form.html', {'form': form})
        form = EmergencyEquipmentForm(data)
        if form.is_valid():
            try:
                equipment = form.save()
                messages.success(request, 'تجهیز با موفقیت ثبت شد.')
                return redirect('emergency_services:equipment_list')
            except Exception as e:
                messages.error(request, f'خطا در ثبت تجهیز: {str(e)}')
        else:
            print(form.errors)
    else:
        form = EmergencyEquipmentForm()
    return render(request, 'emergency_services/equipment_form.html', {'form': form})

@login_required
@emergency_personnel_required
def edit_equipment(request, pk):
    """ویرایش تجهیز"""
    equipment = get_object_or_404(EmergencyEquipment, pk=pk)
    
    if request.method == 'POST':
        data = request.POST.copy()
        for field in ['last_calibration_date', 'next_calibration_date']:
            date_val = data.get(field)
            if date_val:
                try:
                    date_val = persian_to_english_numbers(date_val.strip())
                    date_val = re.sub(r'[^0-9/]', '', date_val)
                    year, month, day = map(int, date_val.split('/'))
                    if year < 100:
                        year += 1400
                    jalali_date = jdatetime.date(year, month, day)
                    gregorian_date = jalali_date.togregorian()
                    data[field] = gregorian_date.strftime('%Y-%m-%d')
                except Exception as e:
                    messages.error(request, 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)')
                    form = EmergencyEquipmentForm(instance=equipment)
                    return render(request, 'emergency_services/equipment_form.html', {'form': form, 'equipment': equipment})
        form = EmergencyEquipmentForm(data, instance=equipment)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'تجهیز با موفقیت بروزرسانی شد.')
                return redirect('emergency_services:equipment_list')
            except Exception as e:
                messages.error(request, f'خطا در بروزرسانی تجهیز: {str(e)}')
    else:
        form = EmergencyEquipmentForm(instance=equipment)
    
    return render(request, 'emergency_services/equipment_form.html', {'form': form, 'equipment': equipment})

# ==================== Data Management Page ====================
@login_required
def data_management(request):
    """صفحه مدیریت داده‌ها - فقط برای مدیر اورژانس"""
    # چک کردن اینکه کاربر مدیر اورژانس است یا سوپریوزر
    is_emergency_manager = request.user.groups.filter(name='EmergencyManager').exists()
    
    if not is_emergency_manager and not request.user.is_superuser:
        messages.error(request, 'فقط مدیر اورژانس مجاز به دسترسی به این بخش می‌باشد.')
        return redirect('emergency_services:dashboard')
    
    context = {
        'page_title': 'مدیریت داده‌های اورژانس',
    }
    return render(request, 'emergency_services/data_management.html', context)

# ==================== API Endpoints for AJAX Operations ====================

@login_required
def api_medicines_list(request):
    """API لیست داروها"""
    medicines = Medicine.objects.all().select_related('category')
    
    search = request.GET.get('search', '')
    if search:
        medicines = medicines.filter(
            Q(name__icontains=search) | 
            Q(category__name__icontains=search)
        )
    
    data = []
    for medicine in medicines:
        data.append({
            'id': medicine.id,
            'name': medicine.name,
            'category': medicine.category.name if medicine.category else '',
            'quantity': medicine.quantity,
            'critical_threshold': medicine.critical_threshold,
            'expiry_date': medicine.expiry_date.strftime('%Y/%m/%d'),
            'is_active': medicine.is_active,
            'is_expired': medicine.is_expired(),
            'is_critical': medicine.is_critical(),
        })
    
    return JsonResponse({'data': data})

@login_required
def api_medicine_save(request):
    """API ذخیره دارو (ایجاد/ویرایش)"""
    if request.method == 'POST':
        medicine_id = request.POST.get('id')
        
        if medicine_id:
            medicine = get_object_or_404(Medicine, pk=medicine_id)
            form = MedicineForm(request.POST, instance=medicine)
        else:
            form = MedicineForm(request.POST)
        
        # تبدیل تاریخ شمسی به میلادی
        data = request.POST.copy()
        expiry_date = data.get('expiry_date')
        if expiry_date:
            try:
                expiry_date_str = persian_to_english_numbers(expiry_date.strip())
                expiry_date_str = re.sub(r'[^0-9/]', '', expiry_date_str)
                
                # بررسی فرمت تاریخ
                if '/' not in expiry_date_str:
                    return JsonResponse({
                        'success': False,
                        'errors': {'expiry_date': ['فرمت تاریخ باید به صورت YYYY/MM/DD باشد']}
                    })
                
                parts = expiry_date_str.split('/')
                if len(parts) != 3:
                    return JsonResponse({
                        'success': False,
                        'errors': {'expiry_date': ['فرمت تاریخ نامعتبر است']}
                    })
                
                year, month, day = map(int, parts)
                
                # تبدیل سال دو رقمی به چهار رقمی
                if year < 100:
                    year += 1400
                
                # بررسی صحت تاریخ شمسی
                try:
                    jalali_date = jdatetime.date(year, month, day)
                except ValueError as ve:
                    return JsonResponse({
                        'success': False,
                        'errors': {'expiry_date': [f'تاریخ نامعتبر: {str(ve)}']}
                    })
                
                # تبدیل به تاریخ میلادی
                gregorian_date = jalali_date.togregorian()
                
                # بررسی اینکه تاریخ انقضا در آینده باشد
                if gregorian_date < timezone.now().date():
                    return JsonResponse({
                        'success': False,
                        'errors': {'expiry_date': ['تاریخ انقضا نمی‌تواند در گذشته باشد']}
                    })
                
                data['expiry_date'] = gregorian_date.strftime('%Y-%m-%d')
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'expiry_date': [f'خطا در تبدیل تاریخ: {str(e)}']}
                })
        
        form = MedicineForm(data, instance=medicine if medicine_id else None)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'متد نامعتبر'})

@login_required
def api_medicine_delete(request, pk):
    """API حذف دارو"""
    if request.method == 'POST':
        medicine = get_object_or_404(Medicine, pk=pk)
        medicine.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_medicine_increase_stock(request, pk):
    """API افزایش موجودی دارو"""
    if request.method == 'POST':
        medicine = get_object_or_404(Medicine, pk=pk)
        
        try:
            from jdatetime import datetime as jdatetime
            from datetime import datetime
            
            quantity = int(request.POST.get('quantity', 0))
            notes = request.POST.get('notes', '').strip()
            expiry_date_str = request.POST.get('expiry_date', '').strip()
            
            if quantity <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'مقدار باید بیشتر از صفر باشد'
                })
            
            # تبدیل تاریخ انقضا اگر وارد شده باشد
            if expiry_date_str:
                try:
                    # تبدیل تاریخ شمسی به میلادی
                    parts = expiry_date_str.replace('/', '-').split('-')
                    if len(parts) == 3:
                        j_year, j_month, j_day = int(parts[0]), int(parts[1]), int(parts[2])
                        j_date = jdatetime(j_year, j_month, j_day)
                        expiry_date = j_date.togregorian()
                        
                        # بررسی اینکه تاریخ انقضا در آینده باشد
                        if expiry_date <= datetime.now().date():
                            return JsonResponse({
                                'success': False,
                                'message': 'تاریخ انقضا باید در آینده باشد'
                            })
                        medicine.expiry_date = expiry_date
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': 'فرمت تاریخ نامعتبر است. از فرمت YYYY/MM/DD استفاده کنید'
                        })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'خطا در تبدیل تاریخ: {str(e)}'
                    })
            
            # افزایش موجودی
            medicine.quantity += quantity
            medicine.save()
            
            # ثبت در لاگ (اختیاری - می‌توانید مدل جداگانه برای تاریخچه بسازید)
            return JsonResponse({
                'success': True,
                'message': f'موجودی دارو با موفقیت {quantity} واحد افزایش یافت',
                'new_quantity': medicine.quantity
            })
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'مقدار وارد شده نامعتبر است'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در افزایش موجودی: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'متد نامعتبر'})

@login_required
def api_categories_list(request):
    """API لیست دسته‌بندی‌ها"""
    categories = MedicineCategory.objects.all()
    
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    
    data = []
    for category in categories:
        data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description or '',
        })
    
    return JsonResponse({'data': data})

@login_required
def api_category_save(request):
    """API ذخیره دسته‌بندی"""
    if request.method == 'POST':
        category_id = request.POST.get('id')
        
        if category_id:
            category = get_object_or_404(MedicineCategory, pk=category_id)
            form = MedicineCategoryForm(request.POST, instance=category)
        else:
            form = MedicineCategoryForm(request.POST)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required
def api_category_delete(request, pk):
    """API حذف دسته‌بندی"""
    if request.method == 'POST':
        category = get_object_or_404(MedicineCategory, pk=pk)
        category.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_services_list(request):
    """API لیست خدمات درمانی"""
    services = MedicalService.objects.all()
    
    search = request.GET.get('search', '')
    if search:
        services = services.filter(name__icontains=search)
    
    data = []
    for service in services:
        data.append({
            'id': service.id,
            'name': service.name,
            'description': service.description or '',
        })
    
    return JsonResponse({'data': data})

@login_required
def api_service_save(request):
    """API ذخیره خدمت درمانی"""
    if request.method == 'POST':
        service_id = request.POST.get('id')
        
        if service_id:
            service = get_object_or_404(MedicalService, pk=service_id)
            form = MedicalServiceForm(request.POST, instance=service)
        else:
            form = MedicalServiceForm(request.POST)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required
def api_service_delete(request, pk):
    """API حذف خدمت درمانی"""
    if request.method == 'POST':
        service = get_object_or_404(MedicalService, pk=pk)
        service.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_equipment_list(request):
    """API لیست تجهیزات"""
    equipment = EmergencyEquipment.objects.all()
    
    search = request.GET.get('search', '')
    if search:
        equipment = equipment.filter(
            Q(name__icontains=search) | 
            Q(serial_number__icontains=search)
        )
    
    data = []
    for item in equipment:
        data.append({
            'id': item.id,
            'name': item.name,
            'serial_number': item.serial_number,
            'last_calibration_date': item.last_calibration_date.strftime('%Y/%m/%d'),
            'next_calibration_date': item.next_calibration_date.strftime('%Y/%m/%d'),
            'is_active': item.is_active,
            'is_calibration_due': item.is_calibration_due(),
        })
    
    return JsonResponse({'data': data})

@login_required
def api_equipment_save(request):
    """API ذخیره تجهیز"""
    if request.method == 'POST':
        equipment_id = request.POST.get('id')
        data = request.POST.copy()
        
        # تبدیل تاریخ‌های شمسی به میلادی
        for field in ['last_calibration_date', 'next_calibration_date']:
            date_val = data.get(field)
            if date_val:
                try:
                    date_val = persian_to_english_numbers(date_val.strip())
                    date_val = re.sub(r'[^0-9/]', '', date_val)
                    year, month, day = map(int, date_val.split('/'))
                    if year < 100:
                        year += 1400
                    jalali_date = jdatetime.date(year, month, day)
                    gregorian_date = jalali_date.togregorian()
                    data[field] = gregorian_date.strftime('%Y-%m-%d')
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'errors': {field: ['فرمت تاریخ نامعتبر است']}
                    })
        
        if equipment_id:
            equipment = get_object_or_404(EmergencyEquipment, pk=equipment_id)
            form = EmergencyEquipmentForm(data, instance=equipment)
        else:
            form = EmergencyEquipmentForm(data)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required
def api_equipment_delete(request, pk):
    """API حذف تجهیز"""
    if request.method == 'POST':
        equipment = get_object_or_404(EmergencyEquipment, pk=pk)
        equipment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_hospitals_list(request):
    """API لیست بیمارستان‌ها"""
    hospitals = Hospital.objects.all()
    
    search = request.GET.get('search', '')
    if search:
        hospitals = hospitals.filter(name__icontains=search)
    
    data = []
    for hospital in hospitals:
        data.append({
            'id': hospital.id,
            'name': hospital.name,
            'address': hospital.address,
            'phone': hospital.phone,
            'is_active': hospital.is_active,
        })
    
    return JsonResponse({'data': data})

@login_required
def api_hospital_save(request):
    """API ذخیره بیمارستان"""
    if request.method == 'POST':
        hospital_id = request.POST.get('id')
        
        if hospital_id:
            hospital = get_object_or_404(Hospital, pk=hospital_id)
            form = HospitalForm(request.POST, instance=hospital)
        else:
            form = HospitalForm(request.POST)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required
def api_hospital_delete(request, pk):
    """API حذف بیمارستان"""
    if request.method == 'POST':
        hospital = get_object_or_404(Hospital, pk=pk)
        if MedicalVisit.objects.filter(hospital=hospital).exists():
            return JsonResponse({
                'success': False,
                'message': 'این بیمارستان دارای مراجعات مرتبط است و نمی‌توان آن را حذف کرد.'
            })
        hospital.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_personnel_list(request):
    """لیست پرسنل اورژانس API"""
    # Allow superuser or users with specific permission
    if not request.user.is_superuser:
        from permissions.utils import check_permission
        if not check_permission(request.user, "api_personnel_list"):
            return JsonResponse({'error': 'شما اجازه دسترسی به این بخش را ندارید'}, status=403)
    
    emergency_groups = Group.objects.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse'])
    users = User.objects.filter(groups__in=emergency_groups).distinct()
    
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search)
        )
    
    data = []
    for user in users:
        user_groups = user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse'])
        role = user_groups.first().name if user_groups.exists() else ''
        
        # تعیین رنگ بج بر اساس نقش
        role_badge = {
            'EmergencyManager': {'label': 'مدیر اورژانس', 'color': 'primary'},
            'EmergencyDoctor': {'label': 'پزشک اورژانس', 'color': 'success'},
            'EmergencyNurse': {'label': 'پرستار اورژانس', 'color': 'info'},
        }.get(role, {'label': 'نامشخص', 'color': 'secondary'})
        
        data.append({
            'id': user.id,
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'username': user.username,
            'role': role,
            'role_label': role_badge['label'],
            'role_color': role_badge['color'],
            'is_active': user.is_active,
        })
    
    return JsonResponse({'data': data})

@login_required
def api_personnel_save(request):
    """ذخیره پرسنل اورژانس API"""
    # Allow superuser or users with specific permission
    if not request.user.is_superuser:
        from permissions.utils import check_permission
        if not check_permission(request.user, "api_personnel_save"):
            return JsonResponse({'error': 'شما اجازه دسترسی به این بخش را ندارید'}, status=403)
    
    if request.method == 'POST':
        user_id = request.POST.get('id')
        
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            form = EmergencyPersonnelForm(request.POST, instance=user)
        else:
            form = EmergencyPersonnelForm(request.POST)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required
def api_personnel_delete(request, pk):
    """حذف پرسنل اورژانس API"""
    # Allow superuser or users with specific permission
    if not request.user.is_superuser:
        from permissions.utils import check_permission
        if not check_permission(request.user, "api_personnel_delete"):
            return JsonResponse({'error': 'شما اجازه دسترسی به این بخش را ندارید'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        # حذف از گروه‌های اورژانس به جای حذف کاربر
        emergency_groups = user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse'])
        user.groups.remove(*emergency_groups)
        user.is_active = False
        user.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def api_personnel_detail(request, pk):
    """جزئیات پرسنل اورژانس API"""
    # Allow superuser or users with specific permission
    if not request.user.is_superuser:
        from permissions.utils import check_permission
        if not check_permission(request.user, "api_personnel_detail"):
            return JsonResponse({'error': 'شما اجازه دسترسی به این بخش را ندارید'}, status=403)
    
    user = get_object_or_404(User, pk=pk)
    user_groups = user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse'])
    role = user_groups.first().name if user_groups.exists() else ''
    
    data = {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': role,
        'is_active': user.is_active,
    }
    
    return JsonResponse(data)

# ==================== Emergency Portal Login/Logout ====================

def emergency_login_view(request):
    """لاگین اختصاصی پرسنل اورژانس"""
    if request.user.is_authenticated:
        # Check if user is emergency personnel
        if request.user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']).exists():
            return redirect('emergency_services:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Check if user is in emergency groups
            if user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']).exists():
                login(request, user)
                messages.success(request, f'خوش آمدید {user.get_full_name() or user.username}')
                return redirect('emergency_services:dashboard')
            else:
                messages.error(request, 'شما مجاز به ورود به پورتال اورژانس نیستید.')
        else:
            messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
    
    return render(request, 'emergency_services/emergency_login.html')

def emergency_logout_view(request):
    """خروج از پورتال اورژانس"""
    logout(request)
    messages.info(request, 'شما با موفقیت خارج شدید.')
    return redirect('emergency_services:emergency_login')

def emergency_password_reset_view(request):
    """بازیابی رمز عبور پرسنل اورژانس"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # جستجوی کاربر با ایمیل و عضویت در گروه‌های اورژانس
        try:
            user = User.objects.get(email=email)
            if user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']).exists():
                # ایجاد توکن بازیابی
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.conf import settings
                
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # ساخت URL بازیابی
                reset_url = request.build_absolute_uri(
                    f"/emergency/password-reset-confirm/{uid}/{token}/"
                )
                
                # ارسال ایمیل (به صورت ساده)
                subject = 'بازیابی رمز عبور - پورتال اورژانس'
                message = f'''
سلام {user.get_full_name() or user.username},

درخواست بازیابی رمز عبور برای حساب کاربری شما در پورتال اورژانس دریافت شد.

برای تنظیم رمز عبور جدید، لطفاً روی لینک زیر کلیک کنید:

{reset_url}

این لینک فقط برای ۲۴ ساعت معتبر است.

اگر این درخواست را نداده‌اید، لطفاً این ایمیل را نادیده بگیرید.

با تشکر،
تیم پورتال اورژانس
                '''
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    messages.success(request, 'لینک بازیابی رمز عبور به ایمیل شما ارسال شد.')
                    return redirect('emergency_services:emergency_password_reset_done')
                except Exception as e:
                    messages.error(request, f'خطا در ارسال ایمیل: {str(e)}')
            else:
                messages.error(request, 'شما مجاز به استفاده از پورتال اورژانس نیستید.')
        except User.DoesNotExist:
            # برای امنیت، پیام یکسان نمایش داده می‌شود
            messages.info(request, 'اگر این ایمیل در سیستم موجود باشد، لینک بازیابی برای شما ارسال خواهد شد.')
    
    return render(request, 'emergency_services/emergency_password_reset.html')

def emergency_password_reset_done_view(request):
    """صفحه تایید ارسال ایمیل بازیابی"""
    return render(request, 'emergency_services/emergency_password_reset_done.html')

# ==================== Emergency Personnel Profile ====================

@login_required
def emergency_profile(request):
    """پروفایل پرسنل اورژانس"""
    user = request.user
    
    # Get user's emergency group
    emergency_groups = user.groups.filter(
        name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']
    )
    
    if not emergency_groups.exists():
        messages.error(request, 'شما به عنوان پرسنل اورژانس ثبت نشده‌اید.')
        return redirect('emergency_services:dashboard')
    
    role = emergency_groups.first()
    
    # Get user's recent activities
    recent_visits = MedicalVisit.objects.filter(
        created_by__user=user
    ).order_by('-created_at')[:10]
    
    # Get statistics
    total_visits_created = MedicalVisit.objects.filter(created_by__user=user).count()
    today_visits_created = MedicalVisit.objects.filter(
        created_by__user=user,
        created_at__date=timezone.now().date()
    ).count()
    
    context = {
        'user': user,
        'role': role,
        'recent_visits': recent_visits,
        'total_visits_created': total_visits_created,
        'today_visits_created': today_visits_created,
    }
    
    return render(request, 'emergency_services/emergency_profile.html', context)

@login_required
def emergency_change_password(request):
    """تغییر رمز عبور پرسنل اورژانس"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'رمز عبور شما با موفقیت تغییر کرد.')
            return redirect('emergency_services:emergency_profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'emergency_services/emergency_change_password.html', context)

@login_required
@emergency_personnel_required
def delete_equipment(request, pk):
    """حذف تجهیز"""
    equipment = get_object_or_404(EmergencyEquipment, pk=pk)
    
    if request.method == 'POST':
        try:
            equipment.delete()
            messages.success(request, 'تجهیز با موفقیت حذف شد.')
        except Exception as e:
            messages.error(request, f'خطا در حذف تجهیز: {str(e)}')
    
    return redirect('emergency_services:equipment_list')


@login_required
@emergency_personnel_required
def expired_medicines_report(request):
    """گزارش داروهای منقضی برای بازرسان و مدیران"""
    from emergency_services.models import ExpiredMedicineLog
    from django.core.paginator import Paginator
    
    # بررسی دسترسی (فقط مدیران و بازرسان)
    is_manager = request.user.groups.filter(
        name__in=['مدیر HSE', 'مدیر اورژانس']
    ).exists()
    is_inspector = request.user.groups.filter(name='بازرس HSE').exists()
    
    if not (is_manager or is_inspector or request.user.is_superuser):
        messages.error(request, 'شما مجاز به دسترسی به این گزارش نیستید.')
        return redirect('emergency_services:dashboard')
    
    # فیلترها
    logs = ExpiredMedicineLog.objects.all().order_by('-disposal_date')
    
    search = request.GET.get('search', '').strip()
    if search:
        logs = logs.filter(
            Q(medicine_name__icontains=search) |
            Q(medicine_category__icontains=search)
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(disposal_date__gte=date_from)
        except:
            pass
    
    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            logs = logs.filter(disposal_date__lte=date_to)
        except:
            pass
    
    disposal_method = request.GET.get('disposal_method')
    if disposal_method:
        logs = logs.filter(disposal_method=disposal_method)
    
    # آمار‌ها
    total_logs = logs.count()
    total_quantity = logs.aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    # صفحه‌بندی
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)
    
    context = {
        'logs': logs_page,
        'total_logs': total_logs,
        'total_quantity': total_quantity,
        'search': search,
        'date_from': date_from if date_from else '',
        'date_to': date_to if date_to else '',
        'disposal_method': disposal_method,
        'disposal_methods': [
            ('deleted', 'حذف از سیستم'),
            ('incinerated', 'سوزانده شده'),
            ('donated', 'اهدا شده'),
            ('returned', 'برگشت به تولیدکننده'),
            ('other', 'سایر'),
        ]
    }
    
    return render(request, 'emergency_services/expired_medicines_report.html', context)
