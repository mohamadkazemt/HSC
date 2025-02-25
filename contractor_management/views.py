# views.py
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, JsonResponse
from permissions.utils import permission_required
from .forms import ReportForm, ReportFilterForm
from django.contrib.auth.decorators import login_required
from .models import Report
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import get_current_user_shift_and_group, SHIFT_PATTERN
from django.shortcuts import render, redirect, get_object_or_404
from .models import Contractor, Employee, Vehicle  # Vehicle را هم ایمپورت کنید
from django.contrib.auth.decorators import user_passes_test
from dashboard.utils import log_user_activity  # اضافه کردن ایمپورت
from django.urls import reverse  # برای ساخت URL
import json

@permission_required("create_report")
@login_required
def create_report(request):
    # ثبت فعالیت مشاهده فرم ایجاد گزارش
    if request.method == 'GET':
        log_user_activity(
            user=request.user,
            activity_type='view',
            description='مشاهده فرم ایجاد گزارش جدید',
            related_model='Report',
            related_object_id=None,
            url=reverse('contractor_management:create_report'),
            request=request
        )
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.report_datetime = timezone.now()

            # اضافه کردن پیمانکار بر اساس خودرو
            selected_vehicle = form.cleaned_data.get('vehicle')
            if selected_vehicle:  # چک برای اینکه مطمئن شویم خودرویی انتخاب شده
                report.contractor = selected_vehicle.contractor

            user_shift, user_group = get_current_user_shift_and_group(report.user)

            if user_shift and user_group:
                report.shift = user_shift
                report.group = user_group
            else:
                messages.error(request, 'امکان ثبت گزارش در این بازه زمانی وجود ندارد.')
                return render(request, 'contractor_management/report_form.html', {
                    'form': form,
                    'messages': messages.get_messages(request)
                })

            if report.report_datetime:
                existing_report = Report.objects.filter(
                    user=report.user,
                    vehicle=report.vehicle,
                    report_datetime__date=report.report_datetime.date(),
                    shift=report.shift,
                    group=report.group
                ).exists()
                if existing_report:
                    messages.error(request, 'شما قبلاً برای این خودرو در این شیفت و گروه گزارش ثبت کرده‌اید.')
                    return render(request, 'contractor_management/report_form.html', {
                        'form': form,
                        'messages': messages.get_messages(request)
                    })
                else:
                    try:
                        report.save()
                        
                        # ثبت فعالیت ایجاد گزارش
                        log_user_activity(
                            user=request.user,
                            activity_type='create',
                            description=f'ثبت گزارش جدید برای خودرو {report.vehicle.license_plate} متعلق به پیمانکار {report.contractor.company_name}',
                            related_model='Report',
                            related_object_id=report.id,
                            url=reverse('contractor_management:report_detail', args=[report.id]),
                            request=request
                        )
                        
                        messages.success(request, 'گزارش با موفقیت ثبت شد.')
                        return redirect('contractor_management:create_report')
                    except Exception as e:
                        messages.error(request, f'خطا در ثبت گزارش: {e}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {form[field].label} : {error}")
    else:
        form = ReportForm()
    return render(request, 'contractor_management/report_form.html', {'form': form})


@permission_required("all_reports")
@login_required
def all_reports(request):
    # ثبت فعالیت مشاهده همه گزارش‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده همه گزارش‌های پیمانکاران',
        related_model='Report',
        related_object_id=None,
        url=reverse('contractor_management:all_reports'),
        request=request
    )
    
    form = ReportFilterForm(request.GET)
    reports = Report.objects.all()
    query = Q()

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        contractor = form.cleaned_data.get('contractor')
        vehicle = form.cleaned_data.get('vehicle')
        shift = form.cleaned_data.get('shift')
        group = form.cleaned_data.get('group')
        if start_date and end_date:
            query &= Q(report_datetime__date__range=[start_date, end_date])
        elif start_date:
            query &= Q(report_datetime__date__gte=start_date)
        elif end_date:
            query &= Q(report_datetime__date__lte=end_date)
        if contractor:
            query &= Q(contractor__company_name=contractor)
        if vehicle:
            query &= Q(vehicle__license_plate=vehicle)
        if shift:
          query &= Q(shift=shift)
        if group:
            query &= Q(group=group)
            
        # اگر فیلتری اعمال شده، فعالیت جستجو را هم ثبت کنیم
        if any([start_date, end_date, contractor, vehicle, shift, group]):
            log_user_activity(
                user=request.user,
                activity_type='view',
                description='جستجو در همه گزارش‌های پیمانکاران',
                related_model='Report',
                related_object_id=None,
                url=request.get_full_path(),
                request=request
            )


    reports = reports.filter(query)
    paginator = Paginator(reports, 10)  # Show 10 reports per page

    page = request.GET.get('page')
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)
    return render(request, 'contractor_management/reports/all_reports.html', {
        'reports': reports,
        'form': form,
    })


def get_contractors_ajax(request):
    # ثبت فعالیت دریافت لیست پیمانکاران
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='دریافت لیست پیمانکاران از طریق AJAX',
        related_model='Contractor',
        related_object_id=None,
        url=None,
        request=request
    )
    
    contractors = []
    search_term = request.GET.get('term', '')
    
    if search_term:
        # ثبت فعالیت جستجوی پیمانکاران
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'جستجوی پیمانکار با عبارت "{search_term}"',
            related_model='Contractor',
            related_object_id=None,
            url=None,
            request=request
        )
        
        contractors = Contractor.objects.filter(
            Q(company_name__icontains=search_term)
        ).values("id", "company_name")
    else:
        contractors = Contractor.objects.values("id", "company_name")
    
    return JsonResponse(list(contractors), safe=False)


def get_contractor_employees_ajax(request):
    # ثبت فعالیت دریافت لیست کارکنان پیمانکار
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='دریافت لیست کارکنان پیمانکار از طریق AJAX',
        related_model='Employee',
        related_object_id=None,
        url=None,
        request=request
    )
    
    employees = []
    search_term = request.GET.get('term', '')
    
    if search_term:
        # ثبت فعالیت جستجوی کارکنان پیمانکار
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'جستجوی کارمند پیمانکار با عبارت "{search_term}"',
            related_model='Employee',
            related_object_id=None,
            url=None,
            request=request
        )
        
        employees = Employee.objects.filter(
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term)
        ).values("id", "first_name", "last_name")
    else:
        employees = Employee.objects.values("id", "first_name", "last_name")
    
    formatted_employees = []
    for employee in employees:
        formatted_employees.append({
            "id": employee['id'],
            "name": f"{employee['first_name']} {employee['last_name']}"
        })
    
    return JsonResponse(list(formatted_employees), safe=False)


def get_all_vehicles_ajax(request):
    # ثبت فعالیت دریافت لیست خودروها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='دریافت لیست تمام خودروهای پیمانکاران از طریق AJAX',
        related_model='Vehicle',
        related_object_id=None,
        url=None,
        request=request
    )
    
    vehicles = Vehicle.objects.all().values('id', 'driver_name', 'license_plate', 'contractor__company_name')
    vehicle_list = [
        {
            'id': v['id'],
            'text': f"{v['driver_name']} ({v['license_plate']}) - {v['contractor__company_name']}"
        } for v in vehicles
    ]
    
    return JsonResponse(vehicle_list, safe=False)


@login_required
def report_list(request):
    # ثبت فعالیت مشاهده لیست گزارش‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست گزارش‌های پیمانکاران',
        related_model='Report',
        related_object_id=None,
        url=reverse('contractor_management:report_list'),
        request=request
    )
    
    reports = Report.objects.all()
    query = Q()
    
    if request.method == 'POST':
        form = ReportFilterForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            contractor = form.cleaned_data.get('contractor')
            vehicle = form.cleaned_data.get('vehicle')
            shift = form.cleaned_data.get('shift')
            group = form.cleaned_data.get('group')
            if start_date and end_date:
                query &= Q(report_datetime__date__range=[start_date, end_date])
            elif start_date:
                query &= Q(report_datetime__date__gte=start_date)
            elif end_date:
                query &= Q(report_datetime__date__lte=end_date)
            if contractor:
                query &= Q(contractor__company_name=contractor)
            if vehicle:
                query &= Q(vehicle__license_plate=vehicle)
            if shift:
                query &= Q(shift=shift)
            if group:
                query &= Q(group=group)
                
            # ثبت فعالیت جستجو در گزارش‌ها
            log_user_activity(
                user=request.user,
                activity_type='view',
                description='جستجو در لیست گزارش‌های پیمانکاران',
                related_model='Report',
                related_object_id=None,
                url=request.get_full_path(),
                request=request
            )
    else:
        form = ReportFilterForm()

    reports = reports.filter(query)
    paginator = Paginator(reports, 10)  # Show 10 reports per page

    page = request.GET.get('page')
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)
    return render(request, 'contractor_management/reports/all_reports.html', {
        'reports': reports,
        'form': form,
    })


@login_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    # ثبت فعالیت مشاهده جزئیات گزارش
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات گزارش خودرو {report.vehicle.license_plate}',
        related_model='Report',
        related_object_id=report.id,
        url=reverse('contractor_management:report_detail', args=[pk]),
        request=request
    )
    
    return render(request, 'contractor_management/report_detail.html', {'report': report})


@login_required
def edit_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    # ثبت فعالیت مشاهده فرم ویرایش گزارش
    if request.method == 'GET':
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'مشاهده فرم ویرایش گزارش خودرو {report.vehicle.license_plate}',
            related_model='Report',
            related_object_id=report.id,
            url=reverse('contractor_management:edit_report', args=[pk]),
            request=request
        )
    
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            
            # ثبت فعالیت ویرایش گزارش
            log_user_activity(
                user=request.user,
                activity_type='update',
                description=f'ویرایش گزارش خودرو {report.vehicle.license_plate}',
                related_model='Report',
                related_object_id=report.id,
                url=reverse('contractor_management:report_detail', args=[pk]),
                request=request
            )
            
            messages.success(request, 'گزارش با موفقیت ویرایش شد.')
            return redirect('contractor_management:report_detail', pk=pk)
    else:
        form = ReportForm(instance=report)
        
    return render(request, 'contractor_management/edit_report.html', {'form': form, 'report': report})


@login_required
def delete_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    # ثبت فعالیت مشاهده صفحه حذف گزارش
    if request.method == 'GET':
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'مشاهده صفحه حذف گزارش خودرو {report.vehicle.license_plate}',
            related_model='Report',
            related_object_id=report.id,
            url=reverse('contractor_management:delete_report', args=[pk]),
            request=request
        )
    
    if request.method == 'POST':
        vehicle_info = f'{report.vehicle.license_plate}'
        report_id = report.id
        report.delete()
        
        # ثبت فعالیت حذف گزارش
        log_user_activity(
            user=request.user,
            activity_type='delete',
            description=f'حذف گزارش خودرو {vehicle_info}',
            related_model='Report',
            related_object_id=report_id,
            url=None,
            request=request
        )
        
        messages.success(request, 'گزارش با موفقیت حذف شد.')
        return redirect('contractor_management:report_list')
    
    return render(request, 'contractor_management/delete_report.html', {'report': report})


@login_required
def contractor_list(request):
    # ثبت فعالیت مشاهده لیست پیمانکاران
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست پیمانکاران',
        related_model='Contractor',
        related_object_id=None,
        url=reverse('contractor_management:contractor_list'),
        request=request
    )
    
    contractors = Contractor.objects.all()
    return render(request, 'contractor_management/contractor_list.html', {'contractors': contractors})


@login_required
def contractor_detail(request, pk):
    contractor = get_object_or_404(Contractor, pk=pk)
    
    # ثبت فعالیت مشاهده جزئیات پیمانکار
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات پیمانکار {contractor.company_name}',
        related_model='Contractor',
        related_object_id=contractor.id,
        url=reverse('contractor_management:contractor_detail', args=[pk]),
        request=request
    )
    
    return render(request, 'contractor_management/contractor_detail.html', {'contractor': contractor})


@login_required
def employee_list(request):
    # ثبت فعالیت مشاهده لیست کارکنان
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست کارکنان پیمانکاران',
        related_model='Employee',
        related_object_id=None,
        url=reverse('contractor_management:employee_list'),
        request=request
    )
    
    employees = Employee.objects.all()
    return render(request, 'contractor_management/employee_list.html', {'employees': employees})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    # ثبت فعالیت مشاهده جزئیات کارمند
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات کارمند {employee.first_name} {employee.last_name}',
        related_model='Employee',
        related_object_id=employee.id,
        url=reverse('contractor_management:employee_detail', args=[pk]),
        request=request
    )
    
    return render(request, 'contractor_management/employee_detail.html', {'employee': employee})


@login_required
def vehicle_list(request):
    # ثبت فعالیت مشاهده لیست خودروها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست خودروهای پیمانکاران',
        related_model='Vehicle',
        related_object_id=None,
        url=reverse('contractor_management:vehicle_list'),
        request=request
    )
    
    vehicles = Vehicle.objects.all()
    return render(request, 'contractor_management/vehicle_list.html', {'vehicles': vehicles})


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    # ثبت فعالیت مشاهده جزئیات خودرو
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات خودرو {vehicle.license_plate}',
        related_model='Vehicle',
        related_object_id=vehicle.id,
        url=reverse('contractor_management:vehicle_detail', args=[pk]),
        request=request
    )
    
    return render(request, 'contractor_management/vehicle_detail.html', {'vehicle': vehicle})