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
    Hospital
)
from .forms import (
    MedicalVisitForm, 
    MedicineSelectForm, 
    MedicineForm, 
    MedicineCategoryForm, 
    MedicalServiceForm,
    MedicineReturnForm,
    HospitalForm
)

def persian_to_english_numbers(text):
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers, english_numbers)
    return text.translate(translation_table)

@permission_required("visit_list")
@login_required
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

@permission_required("create_visit")
@login_required
def create_visit(request):
    """ایجاد مراجعه جدید"""
    MedicineSelectFormSet = formset_factory(MedicineSelectForm, extra=1)
    
    if request.method == 'POST':
        print('POST data:', request.POST)  # لاگ داده‌های POST دریافتی
        
        # کپی کردن داده‌های POST برای تغییر
        data = request.POST.copy()
        
        # تبدیل تاریخ‌های دریافتی
        try:
            # تبدیل تاریخ مراجعه
            if data.get('visit_time'):
                visit_time = persian_to_english_numbers(data['visit_time'].strip())
                visit_time = re.sub(r'[^0-9/ :]', '', visit_time)
                date_part, time_part = visit_time.split(' ')
                year, month, day = map(int, date_part.split('/'))
                
                # جدا کردن ساعت، دقیقه، ثانیه و میلی‌ثانیه
                time_parts = time_part.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2].split('.')[0]) if '.' in time_parts[2] else int(time_parts[2])
                
                # تصحیح سال دو رقمی
                if year < 100:
                    year += 1400
                
                # تبدیل به تاریخ میلادی
                jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
                gregorian_date = jalali_date.togregorian()
                data['visit_time'] = gregorian_date.strftime('%Y-%m-%d %H:%M:%S')
                print('Converted visit time:', data['visit_time'])
            
            # تبدیل تاریخ پذیرش در بیمارستان
            if data.get('hospital_admission_time'):
                admission_time = persian_to_english_numbers(data['hospital_admission_time'].strip())
                admission_time = re.sub(r'[^0-9/ :]', '', admission_time)
                date_part, time_part = admission_time.split(' ')
                year, month, day = map(int, date_part.split('/'))
                
                # جدا کردن ساعت، دقیقه، ثانیه و میلی‌ثانیه
                time_parts = time_part.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2].split('.')[0]) if '.' in time_parts[2] else int(time_parts[2])
                
                # تصحیح سال دو رقمی
                if year < 100:
                    year += 1400
                
                # تبدیل به تاریخ میلادی
                jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
                gregorian_date = jalali_date.togregorian()
                data['hospital_admission_time'] = gregorian_date.strftime('%Y-%m-%d %H:%M:%S')
                print('Converted admission time:', data['hospital_admission_time'])
            
            # تبدیل تاریخ ترخیص از بیمارستان
            if data.get('hospital_discharge_time'):
                discharge_time = persian_to_english_numbers(data['hospital_discharge_time'].strip())
                discharge_time = re.sub(r'[^0-9/ :]', '', discharge_time)
                date_part, time_part = discharge_time.split(' ')
                year, month, day = map(int, date_part.split('/'))
                
                # جدا کردن ساعت، دقیقه، ثانیه و میلی‌ثانیه
                time_parts = time_part.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = int(time_parts[2].split('.')[0]) if '.' in time_parts[2] else int(time_parts[2])
                
                # تصحیح سال دو رقمی
                if year < 100:
                    year += 1400
                
                # تبدیل به تاریخ میلادی
                jalali_date = jdatetime.datetime(year, month, day, hour, minute, second)
                gregorian_date = jalali_date.togregorian()
                data['hospital_discharge_time'] = gregorian_date.strftime('%Y-%m-%d %H:%M:%S')
                print('Converted discharge time:', data['hospital_discharge_time'])
        except (ValueError, IndexError, AttributeError) as e:
            print('Error converting dates:', str(e))
            messages.error(request, 'لطفاً تاریخ‌ها را به فرمت صحیح وارد کنید (مثال: 1404/02/07 18:49:51)')
            form = MedicalVisitForm()
            medicine_formset = MedicineSelectFormSet(prefix='medicines')
            return render(request, 'emergency_services/visit_form.html', {
                'form': form,
                'medicine_formset': medicine_formset,
                'services': MedicalService.objects.all(),
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
                visit.created_by = UserProfile.objects.get(user=request.user)
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
    else:
        form = MedicalVisitForm()
        medicine_formset = MedicineSelectFormSet(prefix='medicines')
    
    services = MedicalService.objects.all()
    
    context = {
        'form': form,
        'medicine_formset': medicine_formset,
        'services': services,
    }
    
    return render(request, 'emergency_services/visit_form.html', context)

@permission_required("visit_detail")
@login_required
def visit_detail(request, pk):
    """جزئیات مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    medicine_usages = visit.medicine_usages.all()
    
    context = {
        'visit': visit,
        'medicine_usages': medicine_usages,
    }
    
    return render(request, 'emergency_services/visit_detail.html', context)

@permission_required("edit_visit")
@login_required
def edit_visit(request, pk):
    """ویرایش مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    
    if request.method == 'POST':
        form = MedicalVisitForm(request.POST, instance=visit)
        
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

@permission_required("add_medicine_to_visit")
@login_required
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

@permission_required("remove_medicine_from_visit")
@login_required
def remove_medicine_from_visit(request, usage_id):
    """حذف دارو از مراجعه"""
    usage = get_object_or_404(MedicineUsage, pk=usage_id)
    visit_id = usage.visit.pk
    
    medicine_name = usage.medicine.name
    usage.delete()
    
    messages.success(request, f'داروی {medicine_name} با موفقیت از مراجعه حذف شد.')
    return redirect('emergency_services:visit_detail', pk=visit_id)

@permission_required("medicine_list")
@login_required
def medicine_list(request):
    """لیست داروها"""
    medicines = Medicine.objects.all().order_by('name')
    
    # فیلترها
    category = request.GET.get('category')
    is_expired = request.GET.get('is_expired')
    is_critical = request.GET.get('is_critical')
    is_active = request.GET.get('is_active')
    
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
            'category': category,
            'is_expired': is_expired,
            'is_critical': is_critical,
            'is_active': is_active,
        }
    }
    
    return render(request, 'emergency_services/medicine_list.html', context)

@permission_required("create_medicine")
@login_required
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

@permission_required("edit_medicine")
@login_required
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

@permission_required("category_list")
@login_required
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

@permission_required("edit_category")
@login_required
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

@permission_required("service_list")
@login_required
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

@permission_required("edit_service")
@login_required
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

@permission_required("return_medicine")
@login_required
def return_medicine(request, usage_id):
    """برگشت دارو به انبار"""
    usage = get_object_or_404(MedicineUsage, pk=usage_id)
    
    if request.method == 'POST':
        form = MedicineReturnForm(request.POST, usage=usage)
        
        if form.is_valid():
            return_obj = form.save(commit=False)
            return_obj.usage = usage
            return_obj.returned_by = UserProfile.objects.get(user=request.user)
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

@permission_required("dashboard")
@login_required
def dashboard(request):
    """داشبورد اورژانس معدن"""
    # آمار کلی مراجعات
    total_visits = MedicalVisit.objects.count()
    today_visits = MedicalVisit.objects.filter(visit_time__date=timezone.now().date()).count()
    monthly_visits = MedicalVisit.objects.filter(visit_time__month=timezone.now().month).count()
    
    # آمار مراجعات پرسنل شرکت و پیمانکار
    company_visits = MedicalVisit.objects.filter(personnel_type='company').count()
    contractor_visits = MedicalVisit.objects.filter(personnel_type='contractor').count()
    
    # آمار داروها
    total_medicines = Medicine.objects.count()
    low_stock_medicines = Medicine.objects.filter(quantity__lte=F('critical_threshold')).count()
    expired_medicines = Medicine.objects.filter(expiry_date__lt=timezone.now().date()).count()
    critical_medicines = Medicine.objects.filter(quantity__lte=F('critical_threshold')).order_by('quantity')[:5]
    
    # خدمات پرمصرف
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
            'date': date,
            'count': count
        })
    weekly_visits.reverse()
    
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
    }
    
    return render(request, 'emergency_services/dashboard.html', context)

@permission_required("export_visits_csv")
@login_required
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

@permission_required("export_medicines_csv")
@login_required
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

@permission_required("print_visit")
@login_required
def print_visit(request, pk):
    """چاپ فرم مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    medicine_usages = visit.medicine_usages.all()
    
    context = {
        'visit': visit,
        'medicine_usages': medicine_usages,
    }
    
    return render(request, 'emergency_services/print_visit.html', context)

@permission_required("hospital_list")
@login_required
def hospital_list(request):
    """لیست بیمارستان‌ها"""
    hospitals = Hospital.objects.all().order_by('name')
    
    context = {
        'hospitals': hospitals,
    }
    
    return render(request, 'emergency_services/hospital_list.html', context)

@permission_required("create_hospital")
@login_required
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

@permission_required("edit_hospital")
@login_required
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

@permission_required("delete_hospital")
@login_required
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