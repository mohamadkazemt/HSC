# views.py
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from permissions.utils import permission_required
from .forms import ReportForm, ReportFilterForm, persian_to_english_numbers
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
import jdatetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Side, Border
import logging
import re
from shift_manager.utils import get_shift_for_date
import datetime # Ensure datetime is imported

logger = logging.getLogger(__name__)

@permission_required("create_report")
@login_required
def create_report(request):
    logger.info("Entering create_report view")
    
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
        post_data = request.POST.copy()
        logger.info(f"داده‌های POST اصلی: {post_data}")

        gdate = None # Initialize gdate
        report_date_input = post_data.get('reeport_date') or post_data.get('report_date')
        if report_date_input:
            try:
                # تبدیل اعداد فارسی به انگلیسی
                report_date = persian_to_english_numbers(report_date_input.strip())
                # حذف کاراکترهای اضافی
                report_date = re.sub(r'[^0-9/]', '', report_date)
                year, month, day = map(int, report_date.split('/'))
                
                # تصحیح سال دو رقمی
                if year < 100:
                    year += 1400
                
                # ساخت تاریخ شمسی
                jdate = jdatetime.date(year, month, day)
                gdate = jdate.togregorian() # Assign the Gregorian date object
                post_data['report_date'] = gdate.strftime('%Y-%m-%d')
                
                # دریافت شیفت کاری بر اساس تاریخ و گروه کاربر
                if hasattr(request.user, 'userprofile'):
                    shifts = get_shift_for_date(gdate, request.user.userprofile)
                    user_shift = shifts.get('user_group_shift')
                    if user_shift:
                        post_data['shift'] = user_shift
                        logger.info(f"شیفت کاری تشخیص داده شده: {user_shift}")
                    else:
                        logger.warning("شیفت کاری برای کاربر تشخیص داده نشد")
                
                logger.info(f"تاریخ میلادی محاسبه شده: {gdate}, Type: {type(gdate)}") # Log the calculated Gregorian date
                logger.info(f"تاریخ رشته‌ای برای فرم: {post_data['report_date']}")
            except (ValueError, IndexError, AttributeError) as e:
                logger.error(f"خطا در تبدیل تاریخ: {str(e)}")
                messages.error(request, 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)')
                form = ReportForm()
                return render(request, 'contractor_management/report_form.html', {'form': form})
        else:
             messages.error(request, 'فیلد تاریخ کارکرد الزامی است.')
             return render(request, 'contractor_management/report_form.html', {'form': ReportForm(post_data)})

        logger.info(f"داده‌های POST نهایی برای فرم: {post_data}")
        form = ReportForm(post_data)
        if form.is_valid():
            logger.info("فرم معتبر است")
            report = form.save(commit=False)
            report.user = request.user
            report.report_datetime = timezone.now()

            # --- شروع اصلاح ---
            # اطمینان از اینکه تاریخ میلادی استاندارد ذخیره می‌شود
            # حتی اگر فرم به اشتباه jdatetime.date برگردانده باشد
            if gdate and isinstance(gdate, datetime.date):
                 report.report_date = gdate
                 logger.info(f"Report.report_date explicitly set to Gregorian date: {report.report_date}, Type: {type(report.report_date)}")
            else:
                 # اگر gdate محاسبه نشده یا نوع آن اشتباه است، سعی کن از فرم بگیری
                 # اما ممکن است هنوز مشکل داشته باشد.
                 logger.warning(f"gdate was not a valid datetime.date. Using value from form: {report.report_date}, Type: {type(report.report_date)}")
                 # اگر نوع تاریخ فرم همچنان jdatetime.date است، خطا بده
                 if isinstance(report.report_date, jdatetime.date):
                     logger.error("Form provided jdatetime.date, cannot save correctly.")
                     messages.error(request, "خطای داخلی در پردازش تاریخ رخ داده است. لطفا با پشتیبانی تماس بگیرید.")
                     return render(request, 'contractor_management/report_form.html', {'form': form})
            # --- پایان اصلاح ---

            # اضافه کردن پیمانکار بر اساس خودرو
            selected_vehicle = form.cleaned_data.get('vehicle')
            logger.info(f"خودروی انتخاب شده: {selected_vehicle}")
            
            if selected_vehicle:
                report.contractor = selected_vehicle.contractor
                logger.info(f"پیمانکار تنظیم شده: {report.contractor}")

            user_shift, user_group = get_current_user_shift_and_group(report.user)
            logger.info(f"شیفت و گروه کاربر: شیفت={user_shift}, گروه={user_group}")

            if user_group:
                report.group = user_group
            else:
                # اگر گروه کاری تشخیص داده نشد، از پروفایل کاربر استفاده کنیم
                if hasattr(request.user, 'userprofile') and request.user.userprofile.group:
                    report.group = request.user.userprofile.group
                    logger.info(f"گروه کاری از پروفایل کاربر استخراج شد: {report.group}")
                else:
                    logger.warning("گروه کاری نامعتبر است")
                    messages.error(request, 'امکان ثبت گزارش در این بازه زمانی وجود ندارد.')
                    return render(request, 'contractor_management/report_form.html', {
                        'form': form
                    })

            try:
                logger.info("در حال ذخیره گزارش...")
                
                # بررسی شیفت کاری کاربر (با تاریخ میلادی صحیح)
                if hasattr(request.user, 'userprofile') and report.report_date:
                     try:
                        shifts = get_shift_for_date(report.report_date, request.user.userprofile)
                        user_shift = shifts.get('user_group_shift', '')
                        
                        if 'OFF' in user_shift:
                            logger.warning(f"کاربر در تاریخ {report.report_date} در شیفت {user_shift} (OFF) است")
                            # نمایش تاریخ شمسی در پیام خطا
                            jdate_display = jdatetime.date.fromgregorian(date=report.report_date).strftime('%Y/%m/%d')
                            messages.error(request, f'شما در تاریخ {jdate_display} در شیفت {user_shift} (OFF) هستید و امکان ثبت گزارش ندارید.')
                            return render(request, 'contractor_management/report_form.html', {
                                'form': form
                            })
                     except Exception as e:
                         logger.error(f"Error getting shift for date {report.report_date}: {e}")
                         # Handle error appropriately, maybe show a generic error message

                # بررسی وجود گزارش قبلی برای این خودرو در این تاریخ و شیفت (با تاریخ میلادی صحیح)
                if report.report_date:
                    existing_report = Report.objects.filter(
                        vehicle=report.vehicle,
                        report_date=report.report_date, # Use the correct Gregorian date
                        shift=report.shift,
                        user=request.user
                    ).first()
                    
                    if existing_report:
                        logger.warning(f"گزارش قبلی برای این خودرو در تاریخ {report.report_date} و شیفت {report.shift} توسط همین کاربر وجود دارد")
                        # نمایش تاریخ شمسی در پیام خطا
                        jdate_display = jdatetime.date.fromgregorian(date=report.report_date).strftime('%Y/%m/%d')
                        messages.error(request, f'شما قبلاً برای خودرو {report.vehicle} در تاریخ {jdate_display} و شیفت {report.shift} گزارش ثبت کرده‌اید. لطفاً از تاریخ یا شیفت دیگری استفاده کنید.')
                        return render(request, 'contractor_management/report_form.html', {
                            'form': form
                        })
                
                logger.info(f"Saving Report - Report Date before save: {report.report_date}, Type: {type(report.report_date)}")
                report.save()
                logger.info(f"گزارش با موفقیت ذخیره شد. شناسه: {report.id}")
                
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
                error_message = str(e)
                if "UNIQUE constraint failed" in error_message:
                    logger.error(f"خطا در ذخیره گزارش (محدودیت یکتا): {error_message}")
                    messages.error(request, f'شما قبلاً برای خودرو {report.vehicle} در تاریخ {report.report_date} و شیفت {report.shift} گزارش ثبت کرده‌اید. لطفاً از تاریخ یا شیفت دیگری استفاده کنید.')
                else:
                    logger.error(f"خطای غیرمنتظره در ذخیره گزارش: {error_message}")
                    messages.error(request, 'خطایی در ثبت گزارش رخ داد. لطفاً دوباره تلاش کنید.')
        else:
            logger.warning(f"خطاهای اعتبارسنجی فرم: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"خطا در فیلد {form[field].label} : {error}")
    else:
        form = ReportForm()
    return render(request, 'contractor_management/report_form.html', {'form': form})


@permission_required("all_reports")
@login_required
def all_reports(request):
    """نمایش همه گزارش‌های کارکرد خودروها"""
    logger.info("Entering all_reports view")
    
    reports = Report.objects.all().order_by('-report_datetime')
    vehicles = Vehicle.objects.all()
    
    # محاسبه وضعیت هر خودرو بر اساس آخرین گزارش
    vehicle_statuses = {}
    for vehicle in vehicles:
        latest_report = Report.objects.filter(vehicle=vehicle).order_by('-report_datetime', '-id').first()
        
        # تعیین وضعیت خودرو بر اساس آخرین گزارش
        vehicle_status, status_class = get_vehicle_status_display(latest_report)
        
        vehicle_statuses[vehicle.id] = {
            'status': vehicle_status,
            'status_class': status_class,
            'latest_report': latest_report
        }
    
    # ثبت فعالیت مشاهده لیست گزارش‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست گزارش‌های پیمانکاران',
        related_model='Report',
        related_object_id=None,
        url=reverse('contractor_management:all_reports'),
        request=request
    )
    
    form = ReportFilterForm(request.GET or None)
    query = Q()
    
    if request.method == 'GET' and any(request.GET.values()):
        logger.info(f"Applying filters from GET request: {request.GET}")
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            contractor = form.cleaned_data.get('contractor')
            vehicle = form.cleaned_data.get('vehicle')
            shift = form.cleaned_data.get('shift')
            group = form.cleaned_data.get('group')
            
            if start_date:
                try:
                    # تبدیل تاریخ شمسی به میلادی
                    logger.debug(f"Original start_date string: {start_date}")
                    # تبدیل اعداد فارسی به انگلیسی
                    start_date_en = persian_to_english_numbers(start_date.strip())
                    # حذف کاراکترهای اضافی
                    start_date_en = re.sub(r'[^0-9/]', '', start_date_en)
                    year, month, day = map(int, start_date_en.split('/'))
                    if year < 100: year += 1400 # تصحیح سال دو رقمی
                    start_date_j = jdatetime.date(year, month, day)
                    start_date_g = start_date_j.togregorian()
                    query &= Q(report_date__gte=start_date_g)
                    logger.info(f"Applied start_date filter: report_date >= {start_date_g}")
                except (ValueError, IndexError, AttributeError) as e:
                    logger.warning(f"Invalid start_date format: {start_date}. Error: {e}")
                    messages.error(request, f'فرمت تاریخ شروع ({start_date}) نامعتبر است. لطفا از فرمت YYYY/MM/DD استفاده کنید.')

            if end_date:
                try:
                    # تبدیل تاریخ شمسی به میلادی
                    logger.debug(f"Original end_date string: {end_date}")
                    end_date_en = persian_to_english_numbers(end_date.strip())
                    end_date_en = re.sub(r'[^0-9/]', '', end_date_en)
                    year, month, day = map(int, end_date_en.split('/'))
                    if year < 100: year += 1400 # تصحیح سال دو رقمی
                    end_date_j = jdatetime.date(year, month, day)
                    end_date_g = end_date_j.togregorian()
                    query &= Q(report_date__lte=end_date_g)
                    logger.info(f"Applied end_date filter: report_date <= {end_date_g}")
                except (ValueError, IndexError, AttributeError) as e:
                    logger.warning(f"Invalid end_date format: {end_date}. Error: {e}")
                    messages.error(request, f'فرمت تاریخ پایان ({end_date}) نامعتبر است. لطفا از فرمت YYYY/MM/DD استفاده کنید.')

            if contractor:
                query &= Q(contractor=contractor)
                vehicles = vehicles.filter(contractor=contractor)
                logger.info(f"Applied contractor filter: {contractor}")

            if vehicle:
                query &= Q(vehicle=vehicle)
                logger.info(f"Applied vehicle filter: {vehicle}")

            if shift:
                query &= Q(shift=shift)
                logger.info(f"Applied shift filter: {shift}")

            if group:
                query &= Q(group=group)
                logger.info(f"Applied group filter: {group}")

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
        else:
            logger.warning(f"Filter form is invalid: {form.errors}")

    reports = reports.filter(query)
    logger.info(f"Total reports after filtering: {reports.count()}")

    # --- اضافه کردن لاگ برای بررسی مقادیر تاریخ ---
    if reports.exists():
        logger.info("Logging report_date values for the first few reports:")
        for report in reports[:3]: # لاگ ۳ گزارش اول
            logger.info(f"Report ID: {report.id}, Report Date: {report.report_date}, Type: {type(report.report_date)}")
            try:
                # تلاش برای تبدیل و لاگ تاریخ شمسی
                jdate = jdatetime.date.fromgregorian(date=report.report_date)
                logger.info(f"Report ID: {report.id}, Converted Shamsi Date: {jdate.strftime('%Y/%m/%d')}")
            except Exception as e:
                logger.error(f"Error converting date for Report ID {report.id}: {e}")
    else:
        logger.info("No reports found after filtering.")
    # --- پایان بخش لاگ ---

    paginator = Paginator(reports, 10)  # Show 10 reports per page

    page = request.GET.get('page')
    try:
        reports_page = paginator.page(page)
    except PageNotAnInteger:
        reports_page = paginator.page(1)
    except EmptyPage:
        reports_page = paginator.page(paginator.num_pages)
    
    # محاسبه تعداد خودروهای فعال، نیمه فعال و غیرفعال
    active_count = sum(1 for status in vehicle_statuses.values() if status['status'] == 'فعال')
    partial_count = sum(1 for status in vehicle_statuses.values() if status['status'] == 'نیمه فعال')
    inactive_count = sum(1 for status in vehicle_statuses.values() if status['status'] == 'غیرفعال')
    unknown_count = sum(1 for status in vehicle_statuses.values() if status['status'] == 'نامشخص')
    
    context = {
        'reports': reports_page,
        'vehicles': vehicles,
        'vehicle_statuses': vehicle_statuses,
        'form': form,
        'title': 'گزارش‌های کارکرد خودروها',
        'active_count': active_count,
        'partial_count': partial_count,
        'inactive_count': inactive_count,
        'unknown_count': unknown_count
    }
    logger.info("Rendering all_reports.html template.")
    return render(request, 'contractor_management/reports/all_reports.html', context)


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
    
    context = {
        'report': report,
        'title': f'جزئیات گزارش کارکرد خودرو {report.vehicle.license_plate}'
    }
    
    return render(request, 'contractor_management/reports/report_detail.html', context)


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
    
    # بررسی آخرین گزارش خودرو برای تعیین وضعیت فعال/غیرفعال
    latest_report = Report.objects.filter(vehicle=vehicle).order_by('-report_datetime').first()
    
    # تعیین وضعیت خودرو
    if latest_report:
        if latest_report.status == 'inactive':
            vehicle_status = 'غیرفعال'
            status_class = 'danger'
        elif latest_report.status == 'partial':
            vehicle_status = 'نیمه فعال'
            status_class = 'warning'
        else:
            vehicle_status = 'فعال'
            status_class = 'success'
        
        # محاسبه زمان آخرین گزارش
        last_report_time = latest_report.report_datetime
    else:
        vehicle_status = 'نامشخص'
        status_class = 'secondary'
        last_report_time = None
    
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
    
    # گزارش‌های اخیر خودرو (۵ گزارش آخر)
    recent_reports = Report.objects.filter(vehicle=vehicle).order_by('-report_datetime')[:5]
    
    context = {
        'vehicle': vehicle,
        'vehicle_status': vehicle_status,
        'status_class': status_class,
        'last_report_time': last_report_time,
        'recent_reports': recent_reports,
        'title': f'جزئیات خودرو {vehicle.license_plate}'
    }
    
    return render(request, 'contractor_management/vehicle_detail.html', context)


@login_required
def vehicle_reports(request, vehicle_id):
    """نمایش گزارش‌های کارکرد یک خودروی خاص"""
    
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    
    # محاسبه وضعیت خودرو بر اساس آخرین گزارش
    latest_report = Report.objects.filter(vehicle=vehicle).order_by('-report_datetime', '-id').first()
    
    # تعیین وضعیت خودرو
    vehicle_status, status_class, last_report_time = get_vehicle_status(latest_report)
    
    # دریافت گزارش‌های فیلتر شده
    reports = get_filtered_reports(request, vehicle)
    
    # فرم فیلتر
    form = ReportFilterForm(request.GET or None)
    
    # ثبت فعالیت مشاهده گزارش‌های خودرو
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده گزارش‌های کارکرد خودرو {vehicle.license_plate}',
        related_model='Vehicle',
        related_object_id=vehicle.id,
        url=request.get_full_path(),
        request=request
    )
    
    context = {
        'vehicle': vehicle,
        'vehicle_status': vehicle_status,
        'status_class': status_class,
        'last_report_time': last_report_time,
        'latest_report': latest_report,
        'reports': reports,
        'form': form,
        'title': f'گزارش‌های کارکرد خودرو {vehicle.license_plate}'
    }
    
    return render(request, 'contractor_management/reports/vehicle_reports.html', context)


def get_vehicle_status(latest_report):
    """محاسبه وضعیت خودرو بر اساس آخرین گزارش"""
    if latest_report:
        if latest_report.status == 'inactive':
            vehicle_status = 'غیرفعال'
            status_class = 'danger'
        elif latest_report.status == 'partial':
            vehicle_status = 'نیمه فعال'
            status_class = 'warning'
        elif latest_report.status == 'full':
            vehicle_status = 'فعال'
            status_class = 'success'
        else:
            # حالت پیش‌فرض اگر مقدار status شناخته شده نباشد
            vehicle_status = f'نامشخص ({latest_report.status})'
            status_class = 'secondary'
        
        last_report_time = latest_report.report_datetime
    else:
        vehicle_status = 'نامشخص'
        status_class = 'secondary'
        last_report_time = None
    
    return vehicle_status, status_class, last_report_time


def get_filtered_reports(request, vehicle):
    """دریافت گزارش‌های فیلتر شده"""
    # فیلترهای جستجو
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    shift = request.GET.get('shift')
    group = request.GET.get('group')
    
    # پایه کوئری
    reports_query = Report.objects.filter(vehicle=vehicle).order_by('-report_datetime')
    
    # اعمال فیلترها
    reports_query = apply_date_filters(reports_query, start_date, end_date)
    
    if shift:
        reports_query = reports_query.filter(shift=shift)
    
    if group:
        reports_query = reports_query.filter(group=group)
    
    # صفحه‌بندی
    paginator = Paginator(reports_query, 10)  # 10 گزارش در هر صفحه
    page = request.GET.get('page')
    
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)
    
    return reports


def apply_date_filters(reports_query, start_date, end_date):
    """اعمال فیلترهای تاریخ به کوئری"""
    logger.debug(f"Applying date filters - Start: {start_date}, End: {end_date}")
    if start_date:
        try:
            # تبدیل تاریخ شمسی به میلادی
            start_date_en = persian_to_english_numbers(start_date.strip())
            start_date_en = re.sub(r'[^0-9/]', '', start_date_en)
            year, month, day = map(int, start_date_en.split('/'))
            if year < 100: year += 1400
            start_date_j = jdatetime.date(year, month, day)
            start_date_g = start_date_j.togregorian()
            reports_query = reports_query.filter(report_date__gte=start_date_g)
            logger.info(f"Applied start_date filter (apply_date_filters): report_date >= {start_date_g}")
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Error converting start_date in apply_date_filters: {start_date}. Error: {e}")
            pass

    if end_date:
        try:
            # تبدیل تاریخ شمسی به میلادی
            end_date_en = persian_to_english_numbers(end_date.strip())
            end_date_en = re.sub(r'[^0-9/]', '', end_date_en)
            year, month, day = map(int, end_date_en.split('/'))
            if year < 100: year += 1400
            end_date_j = jdatetime.date(year, month, day)
            end_date_g = end_date_j.togregorian()
            reports_query = reports_query.filter(report_date__lte=end_date_g)
            logger.info(f"Applied end_date filter (apply_date_filters): report_date <= {end_date_g}")
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Error converting end_date in apply_date_filters: {end_date}. Error: {e}")
            pass

    return reports_query


def get_vehicle_status_display(latest_report):
    """
    تعیین وضعیت خودرو و کلاس وضعیت (badge) بر اساس آخرین گزارش.
    """
    if latest_report:
        if latest_report.status == 'inactive':
            vehicle_status = 'غیرفعال'
            status_class = 'danger'
        elif latest_report.status == 'partial':
            vehicle_status = 'نیمه فعال'
            status_class = 'warning'
        elif latest_report.status == 'full':
            vehicle_status = 'فعال'
            status_class = 'success'
        else:
            vehicle_status = 'نامشخص'
            status_class = 'secondary'
    else:
        vehicle_status = 'نامشخص'
        status_class = 'secondary'
    
    return vehicle_status, status_class


def export_reports_to_excel(request, vehicle_id=None):
    """خروجی اکسل گزارش‌ها"""
    # ایجاد یک workbook جدید
    wb = Workbook()
    ws = wb.active
    ws.title = "گزارش‌های کارکرد خودرو"
    
    # تنظیمات اولیه
    ws.sheet_properties.rightToLeft = True
    
    # دریافت داده‌ها
    reports_query = Report.objects.all()
    
    # اعمال فیلترها اگر وجود داشته باشند
    if vehicle_id:
        reports_query = reports_query.filter(vehicle_id=vehicle_id)
        vehicle = Vehicle.objects.get(id=vehicle_id)
    
    # اعمال فیلترهای تاریخ اگر وجود داشته باشند
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date or end_date:
        reports_query = apply_date_filters(reports_query, start_date, end_date)
    
    # اعمال سایر فیلترها
    shift = request.GET.get('shift')
    group = request.GET.get('group')
    if shift:
        reports_query = reports_query.filter(shift=shift)
    if group:
        reports_query = reports_query.filter(group=group)
    
    # مرتب‌سازی
    reports_query = reports_query.order_by('-report_datetime')
    
    # تنظیم استایل‌ها
    title_font = Font(name='B Nazanin', size=24, bold=True)
    subtitle_font = Font(name='B Nazanin', size=16, bold=True)
    info_font = Font(name='B Nazanin', size=14)
    header_font = Font(name='B Nazanin', size=12, bold=True)
    data_font = Font(name='B Nazanin', size=11)
    
    header_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')  # خاکستری روشن
    title_fill = PatternFill(start_color='E8E8E8', end_color='E8E8E8', fill_type='solid')   # خاکستری خیلی روشن
    info_fill = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')    # نقره‌ای روشن
    
    center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    # تنظیم ارتفاع ردیف‌ها
    ws.row_dimensions[1].height = 45  # عنوان اصلی
    ws.row_dimensions[2].height = 35  # اطلاعات پیمانکار - ردیف 1
    ws.row_dimensions[3].height = 35  # اطلاعات پیمانکار - ردیف 2
    ws.row_dimensions[4].height = 30  # هدرها
    
    # اضافه کردن عنوان اصلی
    ws.merge_cells('A1:I1')
    title_cell = ws.cell(row=1, column=1, value='گزارش کارکرد خودرو')
    title_cell.font = title_font
    title_cell.fill = title_fill
    title_cell.alignment = center_alignment
    
    # اضافه کردن اطلاعات پیمانکار و خودرو در دو ردیف
    if vehicle_id:
        # ردیف اول اطلاعات
        ws.merge_cells('A2:I2')
        info_cell1 = ws.cell(row=2, column=1, value=f'نام پیمانکار: {vehicle.contractor.company_name}')
        info_cell1.font = subtitle_font
        info_cell1.fill = info_fill
        info_cell1.alignment = center_alignment
        
        # ردیف دوم اطلاعات
        ws.merge_cells('A3:C3')
        info_cell2_1 = ws.cell(row=3, column=1, value=f'نوع خودرو: {vehicle.vehicle_type}')
        info_cell2_1.font = info_font
        info_cell2_1.fill = info_fill
        info_cell2_1.alignment = center_alignment
        
        ws.merge_cells('D3:F3')
        info_cell2_2 = ws.cell(row=3, column=4, value=f'پلاک: {vehicle.license_plate}')
        info_cell2_2.font = info_font
        info_cell2_2.fill = info_fill
        info_cell2_2.alignment = center_alignment
        
        ws.merge_cells('G3:I3')
        info_cell2_3 = ws.cell(row=3, column=7, value=f'شماره تماس مدیر: {vehicle.contractor.manager_phone}')
        info_cell2_3.font = info_font
        info_cell2_3.fill = info_fill
        info_cell2_3.alignment = center_alignment
    
    # تعریف هدرها
    headers = [
        'شماره گزارش',
        'تاریخ و زمان ثبت',
        'ثبت کننده',
        'شیفت کاری',
        'گروه کاری',
        'وضعیت کارکرد',
        'ساعت شروع توقف',
        'ساعت پایان توقف',
        'توضیحات'
    ]
    
    # اضافه کردن هدرها
    header_row = 4 if vehicle_id else 1
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    # تنظیم عرض ستون‌ها
    column_widths = {
        'A': 12,  # شماره گزارش
        'B': 22,  # تاریخ و زمان
        'C': 20,  # ثبت کننده
        'D': 15,  # شیفت
        'E': 15,  # گروه
        'F': 18,  # وضعیت
        'G': 18,  # شروع توقف
        'H': 18,  # پایان توقف
        'I': 45,  # توضیحات
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    
    # اضافه کردن داده‌ها
    data_start_row = header_row + 1
    for row, report in enumerate(reports_query, data_start_row):
        ws.row_dimensions[row].height = 25  # تنظیم ارتفاع ردیف‌های داده
        
        ws.cell(row=row, column=1, value=report.id)
        ws.cell(row=row, column=2, value=report.report_datetime.strftime('%Y/%m/%d %H:%M:%S'))
        ws.cell(row=row, column=3, value=report.user.get_full_name())
        ws.cell(row=row, column=4, value=report.shift)
        ws.cell(row=row, column=5, value=report.group)
        ws.cell(row=row, column=6, value=dict(Report.STATUS_CHOICES)[report.status])
        ws.cell(row=row, column=7, value=report.stop_start_time if report.stop_start_time else '')
        ws.cell(row=row, column=8, value=report.stop_end_time if report.stop_end_time else '')
        ws.cell(row=row, column=9, value=report.description if report.description else '')
        
        # اعمال استایل به سلول‌ها
        for col in range(1, 10):
            cell = ws.cell(row=row, column=col)
            cell.font = data_font
            cell.alignment = center_alignment
            
            # اضافه کردن border به همه سلول‌ها
            thin_border = Side(border_style="thin", color="000000")
            cell.border = Border(top=thin_border, left=thin_border, right=thin_border, bottom=thin_border)
    
    # اضافه کردن border به هدرها و اطلاعات بالای صفحه
    for row in range(1, data_start_row):
        for col in range(1, 10):
            cell = ws.cell(row=row, column=col)
            thin_border = Side(border_style="thin", color="000000")
            cell.border = Border(top=thin_border, left=thin_border, right=thin_border, bottom=thin_border)
    
    # تنظیم نام فایل
    filename = f"reports_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    if vehicle_id:
        filename = f"reports_{vehicle.license_plate}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # ایجاد پاسخ HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # ذخیره فایل
    wb.save(response)
    
    # ثبت فعالیت خروجی اکسل
    log_user_activity(
        user=request.user,
        activity_type='export',
        description=f'دریافت خروجی اکسل گزارش‌ها',
        related_model='Report',
        related_object_id=None,
        url=request.get_full_path(),
        request=request
    )
    
    return response