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
    MedicineReturn
)
from .forms import (
    MedicalVisitForm, 
    MedicineSelectForm, 
    MedicineForm, 
    MedicineCategoryForm, 
    MedicalServiceForm,
    MedicineReturnForm
)


@login_required
@permission_required('emergency_services.visit_list')
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
@permission_required('emergency_services.create_visit')
def create_visit(request):
    """ایجاد مراجعه جدید"""
    MedicineSelectFormSet = formset_factory(MedicineSelectForm, extra=1)
    
    if request.method == 'POST':
        form = MedicalVisitForm(request.POST)
        medicine_formset = MedicineSelectFormSet(request.POST, prefix='medicines')
        
        if form.is_valid() and medicine_formset.is_valid():
            # ذخیره فرم مراجعه
            visit = form.save(commit=False)
            visit.created_by = UserProfile.objects.get(user=request.user)
            visit.save()
            form.save_m2m()  # ذخیره رابطه چند به چند خدمات
            
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


@login_required
@permission_required('emergency_services.visit_detail')
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
@permission_required('emergency_services.edit_visit')
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


@login_required
@permission_required('emergency_services.add_medicine_to_visit')
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
@permission_required('emergency_services.remove_medicine_from_visit')
def remove_medicine_from_visit(request, usage_id):
    """حذف دارو از مراجعه"""
    usage = get_object_or_404(MedicineUsage, pk=usage_id)
    visit_id = usage.visit.pk
    
    medicine_name = usage.medicine.name
    usage.delete()
    
    messages.success(request, f'داروی {medicine_name} با موفقیت از مراجعه حذف شد.')
    return redirect('emergency_services:visit_detail', pk=visit_id)


@login_required
@permission_required('emergency_services.medicine_list')
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


@login_required
@permission_required('emergency_services.create_medicine')
def create_medicine(request):
    """ایجاد داروی جدید"""
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'داروی جدید با موفقیت اضافه شد.')
            return redirect('emergency_services:medicine_list')
    else:
        form = MedicineForm()
    
    context = {
        'form': form,
        'title': 'افزودن داروی جدید',
    }
    
    return render(request, 'emergency_services/medicine_form.html', context)


@login_required
@permission_required('emergency_services.edit_medicine')
def edit_medicine(request, pk):
    """ویرایش دارو"""
    medicine = get_object_or_404(Medicine, pk=pk)
    
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'دارو با موفقیت بروزرسانی شد.')
            return redirect('emergency_services:medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    
    context = {
        'form': form,
        'medicine': medicine,
        'title': f'ویرایش داروی {medicine.name}',
    }
    
    return render(request, 'emergency_services/medicine_form.html', context)


@login_required
@permission_required('emergency_services.category_list')
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
@permission_required('emergency_services.edit_category')
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
@permission_required('emergency_services.service_list')
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
@permission_required('emergency_services.edit_service')
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
@permission_required('emergency_services.return_medicine')
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


@login_required
@permission_required('emergency_services.dashboard')
def dashboard(request):
    """داشبورد اورژانس"""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # آمار بازدیدها
    total_visits = MedicalVisit.objects.count()
    today_visits = MedicalVisit.objects.filter(visit_time__date=today).count()
    monthly_visits = MedicalVisit.objects.filter(visit_time__date__gte=this_month_start).count()
    
    # آمار داروها
    total_medicines = Medicine.objects.count()
    low_stock_medicines = Medicine.objects.filter(quantity__lt=F('critical_threshold')).count()
    
    # آمار مصرف دارو
    recent_medicine_usages = MedicineUsage.objects.select_related(
        'visit', 'medicine', 'visit__company_personnel'
    ).order_by('-created_at')[:10]
    
    # نمودار مراجعات هفتگی
    week_days = []
    visits_count = []
    for i in range(7, 0, -1):
        day = today - timedelta(days=i-1)
        count = MedicalVisit.objects.filter(visit_time__date=day).count()
        week_days.append(day.strftime('%Y-%m-%d'))
        visits_count.append(count)
    
    context = {
        'total_visits': total_visits,
        'today_visits': today_visits,
        'monthly_visits': monthly_visits,
        'total_medicines': total_medicines,
        'low_stock_medicines': low_stock_medicines,
        'recent_medicine_usages': recent_medicine_usages,
        'week_days': json.dumps(week_days),
        'visits_count': json.dumps(visits_count),
    }
    
    return render(request, 'emergency_services/dashboard.html', context)


@login_required
@permission_required('emergency_services.export_visits_csv')
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
@permission_required('emergency_services.export_medicines_csv')
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
@permission_required('emergency_services.print_visit')
def print_visit(request, pk):
    """چاپ فرم مراجعه"""
    visit = get_object_or_404(MedicalVisit, pk=pk)
    medicine_usages = visit.medicine_usages.all()
    
    context = {
        'visit': visit,
        'medicine_usages': medicine_usages,
    }
    
    return render(request, 'emergency_services/print_visit.html', context) 