# app/views.py
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from accounts.models import UserProfile
from .forms import ShiftReportForm
from .models import ShiftReport
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from collections import defaultdict
from django.utils.timezone import localdate
import jdatetime
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.template.loader import get_template
from django.conf import settings
from jdatetime import date as jdate
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
import datetime
from django.db.models import Count, Q, Subquery, OuterRef, Min
from dashboard.utils import log_user_activity
from django.urls import reverse
from django.contrib import messages
from shift_manager.utils import get_shift_for_date  # Import the function
import openpyxl
from django.utils import timezone
from .utils import get_shift_for_date_and_time  # Import the new function


logger = logging.getLogger(__name__)


from django.db import transaction

@login_required
def create_shift_report(request):
    current_user = request.user.userprofile
    personnel_list = UserProfile.objects.select_related('user').filter(
        section=current_user.section,
    )

    # ثبت فعالیت مشاهده فرم ثبت مرخصی
    if request.method == 'GET':
        log_user_activity(
            user=request.user,
            activity_type='view',
            description='مشاهده فرم ثبت مرخصی',
            related_model='ShiftReport',
            related_object_id=None,
            url=reverse('leave_reports:shift_report'),
            request=request
        )

    if request.method == 'POST':
        logger.info("POST request received for create_shift_report")
        try:
            total_leaves = int(request.POST.get('total_leaves', 0))
            logger.info(f"Total leaves from request: {total_leaves}")
            if total_leaves == 0:
                messages.warning(request, 'هیچ موردی برای ثبت وجود ندارد')
                logger.warning("No leaves to process")
                return JsonResponse({'success': False})
            else:
                reports_to_create = []  # لیست برای ذخیره فرم ها
                form_valid = True  # پرچم
                
                # دریافت تاریخ شیفت از فرم یا استفاده از تاریخ امروز
                shift_date_str = request.POST.get('shift_date')
                if shift_date_str:
                    try:
                        # تبدیل تاریخ شمسی به میلادی
                        day, month, year = map(int, shift_date_str.split('/'))
                        shift_date = jdatetime.date(year, month, day).togregorian()
                    except (ValueError, AttributeError):
                        # اگر تاریخ نامعتبر بود، از تاریخ امروز استفاده کن
                        shift_date = datetime.date.today()
                        messages.warning(request, 'تاریخ وارد شده نامعتبر است. از تاریخ امروز استفاده شد.')
                else:
                    # اگر تاریخ ارسال نشده بود، از تاریخ امروز استفاده کن
                    shift_date = datetime.date.today()
                
                logger.info(f"Using shift date: {shift_date}")

                for i in range(total_leaves):
                    try:
                        user_id = request.POST.get(f'user_{i}')
                        report_data = {
                            'user': user_id,
                            'leave_type': request.POST.get(f'leave_type_{i}'),
                            'status': 'reported',
                            'description': request.POST.get(f'description_{i}'),
                            'shift_date': shift_date,  # اضافه کردن تاریخ شیفت به داده‌های فرم
                        }
                        if report_data['leave_type'] == 'hourly':
                            report_data.update({
                                'start_time': request.POST.get(f'start_time_{i}'),
                                'end_time': request.POST.get(f'end_time_{i}')
                            })

                        logger.info(f"Processing leave {i + 1} with data: {report_data}")

                        form = ShiftReportForm(report_data)
                        if form.is_valid():
                            report = form.save(commit=False)
                            report.crate_by = request.user.userprofile
                            report.work_group = request.user.userprofile.group

                            reports_to_create.append(report)  # ذخیره در لیست

                        else:
                            # تبدیل خطاهای فرم به پیام‌های فارسی
                            for field, error_list in form.errors.items():
                                field_name = {
                                    'user': 'کاربر',
                                    'leave_type': 'نوع مرخصی',
                                    'start_time': 'زمان شروع',
                                    'end_time': 'زمان پایان',
                                    'description': 'توضیحات',
                                    'shift_date': 'تاریخ شیفت',
                                    'status': 'وضعیت'
                                }.get(field, field)
                                
                                for error in error_list:
                                    messages.error(request, f"خطا در فیلد {field_name}: {error}")
                            form_valid = False  # تنظیم پرچم به False
                            logger.warning(f"Form not valid for leave {i + 1}: {form.errors}")
                    except Exception as e:
                        messages.error(request, f"خطا در پردازش مورد {i + 1}: {str(e)}")
                        logger.error(f"Error processing leave {i + 1}: {e}", exc_info=True)
                        form_valid = False  # تنظیم پرچم به False

                if form_valid: # ذخیره دسته‌ای اگر همه معتبر بودن
                    try:
                        with transaction.atomic():  # استفاده از atomic transaction
                            ShiftReport.objects.bulk_create(reports_to_create)
                            logger.info(f"{len(reports_to_create)} leaves saved successfully")
                            
                            # ثبت فعالیت ایجاد مرخصی
                            log_user_activity(
                                user=request.user,
                                activity_type='create',
                                description=f'ثبت {len(reports_to_create)} مورد مرخصی',
                                related_model='ShiftReport',
                                related_object_id=None,
                                url=reverse('leave_reports:shift_report_list'),
                                request=request
                            )
                            
                            messages.success(request, f'{len(reports_to_create)} مورد با موفقیت ثبت شد')
                            return JsonResponse({'success': True})
                    except Exception as e:
                        messages.error(request, f'خطا در ذخیره دسته‌ای: {str(e)}')
                        logger.error(f"Error during bulk create: {e}", exc_info=True)
                        return JsonResponse({'success': False})

                else:
                    logger.warning(f"Errors found, not saving.")
                    return JsonResponse({'success': False})

        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
            logger.error(f"System error: {e}", exc_info=True)
            return JsonResponse({'success': False})

    form = ShiftReportForm()
    context = {
        'form': form,
        'personnels': personnel_list,
        'title': 'ثبت مرخصی',
    }
    return render(request, 'leave_reports/shift_report.html', context)





@login_required
def shift_report_list(request):
    # ثبت فعالیت مشاهده لیست مرخصی‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست مرخصی‌ها',
        related_model='ShiftReport',
        related_object_id=None,
        url=reverse('leave_reports:shift_report_list'),
        request=request
    )
    
    # بررسی عضویت کاربر در گروه مدیر
    is_manager = request.user.groups.filter(name='مدیر').exists()

    # دریافت گزارش‌ها بر اساس شرایط
    if is_manager:
        reports = ShiftReport.objects.all()  # مدیر می‌تواند همه گزارش‌ها را ببیند
    else:
        reports = ShiftReport.objects.filter(crate_by=request.user.userprofile)  # کاربر فقط گزارش‌های خودش را می‌بیند

    # Get filter parameters from request
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    work_group = request.GET.get('work_group')
    today_filter = request.GET.get('today')

    # Apply filters
    if work_group:
        reports = reports.filter(work_group=work_group)

    if today_filter == 'true':
        reports = reports.filter(shift_date=datetime.date.today())

    if year and month and day:
        try:
            gregorian_date = jdatetime.date(year=int(year), month=int(month), day=int(day)).togregorian()
            reports = reports.filter(shift_date=gregorian_date)
        except ValueError as e:
            print(f"Error converting Jalali to Gregorian: {e}")
    elif year and month:
        try:
            gregorian_start = jdatetime.date(year=int(year), month=int(month), day=1).togregorian()
            if int(month) < 12:
                gregorian_end = jdatetime.date(year=int(year), month=int(month) + 1, day=1).togregorian()
            else:
                gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
            reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
        except ValueError as e:
            print(f"Error converting Jalali to Gregorian: {e}")
    elif year:
        try:
            gregorian_start = jdatetime.date(year=int(year), month=1, day=1).togregorian()
            gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
            reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
        except ValueError as e:
            print(f"Error converting Jalali to Gregorian: {e}")

    # Subquery to get the last created_at for each user per day
    last_created_at_subquery = reports.filter(
        user=OuterRef('user'),
        shift_date=OuterRef('shift_date'),
        work_group=OuterRef('work_group')
    ).order_by('-created_at').values('created_at')[:1]

    # Filter the reports based on the last created_at
    reports = reports.filter(created_at__in=Subquery(last_created_at_subquery))

    # Group the reports
    reports = reports.order_by('-shift_date', 'work_group', '-created_at').annotate(
        total_regular=Count('id', filter=Q(leave_type='regular')),
        total_hourly=Count('id', filter=Q(leave_type='hourly')),
        total_absence=Count('id', filter=Q(leave_type='absence')),
        total_sick_leave=Count('id', filter=Q(leave_type='sick_leave')),
        total_persons=Count('user', distinct=True),
        first_created_at=Min('created_at')
    )

    report_with_ids = []
    for report in reports:
        # Get the shift for the report's creation date
        shift_info = get_shift_for_date(report.shift_date)
        report_shift = shift_info.get(report.work_group)

        report_dict = {
            'id': report.id,
            'shift_date': jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d'),
            'work_group': report.work_group,
            'crate_by_name': f"{report.crate_by.user.first_name} {report.crate_by.user.last_name}",
            'total_regular': report.total_regular,
            'total_hourly': report.total_hourly,
            'total_absence': report.total_absence,
            'total_sick_leave': report.total_sick_leave,
            'total_persons': report.total_persons,
            'created_at': report.first_created_at,
            'shift': report_shift,  # Add the shift here
        }
        report_with_ids.append(report_dict)

    # Implement pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(report_with_ids, 10)  # Show 10 reports per page
    try:
        reports_page = paginator.page(page)
    except PageNotAnInteger:
        reports_page = paginator.page(1)
    except EmptyPage:
        reports_page = paginator.page(paginator.num_pages)

    # Extract years, months, and days
    all_years = sorted(
        list({int(r['shift_date'].split('/')[0]) for r in report_with_ids}),
        reverse=True
    )
    all_months = sorted(
        list({int(r['shift_date'].split('/')[1]) for r in report_with_ids})
    )
    all_days = sorted(
        list({int(r['shift_date'].split('/')[2]) for r in report_with_ids})
    )

    # Extract work groups
    all_work_groups = sorted(list({r.work_group for r in ShiftReport.objects.all()}))

    return render(request, 'leave_reports/shift_report_list.html', {
        'reports': reports_page,
        'years': all_years,
        'months': all_months,
        'days': all_days,
        'selected_year': year,
        'selected_month': month,
        'selected_day': day,
        'page_obj': reports_page,
        'work_groups': all_work_groups,
        'selected_work_group': work_group,
        'today_filter': today_filter,
        'title': 'لیست مرخصی ها',
    })


@login_required
def delete_leave(request, leave_id):
    # دریافت شیء مرخصی
    leave = get_object_or_404(ShiftReport, id=leave_id)
    today = datetime.date.today()
    
    # استفاده از ماژول shift_manager برای تشخیص شیفت کاری فعلی کاربر
    try:
        from shift_manager.utils import get_current_shift_and_group
        current_shift, current_group = get_current_shift_and_group(request.user)
        logger.info(f"Current shift and group for user {request.user.username}: shift={current_shift}, group={current_group}")
    except ImportError as e:
        logger.error(f"Error importing shift_manager.utils: {e}", exc_info=True)
        current_group = request.user.userprofile.group if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group') else None
    except Exception as e:
        logger.error(f"Error getting current shift and group: {e}", exc_info=True)
        current_group = request.user.userprofile.group if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group') else None

    # بررسی مجوز کاربر برای حذف
    if leave.crate_by != request.user.userprofile:
        messages.error(request, 'شما اجازه حذف این مرخصی را ندارید.')
        return JsonResponse({'success': False, 'error': 'شما اجازه حذف این مرخصی را ندارید.'})
    
    # بررسی تاریخ مرخصی (فقط مرخصی‌های امروز قابل حذف هستند)
    if leave.shift_date != today:
        messages.error(request, 'فقط مرخصی‌های امروز قابل حذف هستند.')
        return JsonResponse({'success': False, 'error': 'فقط مرخصی‌های امروز قابل حذف هستند.'})
    
    # بررسی گروه کاری (فقط مرخصی‌های گروه کاری فعلی کاربر قابل حذف هستند)
    if leave.work_group != current_group:
        messages.error(request, 'شما فقط می‌توانید مرخصی‌های گروه کاری فعلی خود را حذف کنید.')
        return JsonResponse({'success': False, 'error': 'شما فقط می‌توانید مرخصی‌های گروه کاری فعلی خود را حذف کنید.'})

    if request.method == 'POST':
        try:
            # ذخیره اطلاعات مورد نیاز قبل از حذف
            shift_date = leave.shift_date
            work_group = leave.work_group
            
            # ثبت فعالیت حذف مرخصی
            log_user_activity(
                user=request.user,
                activity_type='delete',
                description=f'حذف مرخصی با شناسه {leave_id}',
                related_model='ShiftReport',
                related_object_id=leave_id,
                url=request.META.get('HTTP_REFERER', '/'),
                request=request
            )
            
            # حذف مرخصی
            leave.delete()
            
            messages.success(request, 'مرخصی با موفقیت حذف شد.')
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error deleting leave: {e}", exc_info=True)
            messages.error(request, f'خطا در حذف مرخصی: {str(e)}')
            return JsonResponse({'success': False, 'error': f'خطا در حذف مرخصی: {str(e)}'})
    else:
        messages.error(request, 'درخواست نامعتبر است.')
        return JsonResponse({'success': False, 'error': 'درخواست نامعتبر است.'})

@login_required
def add_leave(request):
    if request.method == 'POST':
        # ثبت داده‌های دریافتی برای دیباگ
        logger.info(f"Received POST data: {request.POST}")
        
        # استفاده از ماژول shift_manager برای تشخیص شیفت کاری فعلی کاربر
        try:
            from shift_manager.utils import get_current_shift_and_group
            current_shift, current_group = get_current_shift_and_group(request.user)
            logger.info(f"Current shift and group for user {request.user.username}: shift={current_shift}, group={current_group}")
        except ImportError as e:
            logger.error(f"Error importing shift_manager.utils: {e}", exc_info=True)
            current_group = request.user.userprofile.group if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group') else None
        except Exception as e:
            logger.error(f"Error getting current shift and group: {e}", exc_info=True)
            current_group = request.user.userprofile.group if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group') else None
        
        # دریافت شناسه گزارش
        report_id = request.POST.get('report_id')
        if not report_id:
            logger.error("Missing report_id in request")
            return JsonResponse({'success': False, 'error': 'شناسه گزارش یافت نشد.'})
        
        # دریافت گزارش اصلی
        try:
            report = ShiftReport.objects.get(id=report_id)
        except ShiftReport.DoesNotExist:
            logger.error(f"Report with ID {report_id} not found")
            return JsonResponse({'success': False, 'error': 'گزارش مورد نظر یافت نشد.'})
        
        # بررسی تاریخ گزارش (فقط گزارش‌های امروز قابل ویرایش هستند)
        today = datetime.date.today()
        if report.shift_date != today:
            logger.warning(f"Attempt to add leave to a report not from today. Report date: {report.shift_date}, Today: {today}")
            return JsonResponse({'success': False, 'error': 'فقط می‌توانید به گزارش‌های امروز مرخصی اضافه کنید.'})
        
        # بررسی گروه کاری (فقط گزارش‌های گروه کاری فعلی کاربر قابل ویرایش هستند)
        if report.work_group != current_group:
            logger.warning(f"Attempt to add leave to a report from different work group. Report group: {report.work_group}, User group: {current_group}")
            return JsonResponse({'success': False, 'error': 'فقط می‌توانید به گزارش‌های گروه کاری فعلی خود مرخصی اضافه کنید.'})
        
        # دریافت نوع مرخصی
        leave_type = request.POST.get('leave_type')
        
        # بررسی توضیحات برای غیبت
        if leave_type == 'absence':
            description = request.POST.get('description', '').strip()
            if not description:
                logger.warning("Missing description for absence")
                return JsonResponse({'success': False, 'error': 'برای ثبت غیبت، وارد کردن توضیحات الزامی است.'})
        
        # بررسی توضیحات برای مرخصی استعلاجی
        if leave_type == 'sick_leave':
            description = request.POST.get('description', '').strip()
            if not description:
                logger.warning("Missing description for sick leave")
                return JsonResponse({'success': False, 'error': 'برای ثبت مرخصی استعلاجی، وارد کردن توضیحات الزامی است.'})
        
        # بررسی زمان شروع و پایان برای مرخصی ساعتی
        if leave_type == 'hourly':
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            if not start_time or not end_time:
                logger.warning(f"Missing start_time or end_time for hourly leave. start_time: {start_time}, end_time: {end_time}")
                return JsonResponse({'success': False, 'error': 'برای ثبت مرخصی ساعتی، وارد کردن زمان شروع و پایان الزامی است.'})
        
        # ایجاد فرم با داده‌های دریافتی
        post_data = request.POST.copy()
        post_data['shift_date'] = report.shift_date
        post_data['status'] = 'reported'
        form = ShiftReportForm(post_data)
        
        if form.is_valid():
            try:
                # ایجاد شیء مرخصی جدید بدون ذخیره
                leave = form.save(commit=False)
                
                # تنظیم فیلدهای اضافی
                leave.shift_date = report.shift_date
                leave.work_group = current_group  # استفاده از گروه کاری فعلی کاربر
                leave.crate_by = request.user.userprofile
                
                # اطمینان از ذخیره توضیحات
                if leave_type in ['absence', 'sick_leave']:
                    leave.description = post_data.get('description', '').strip()
                
                # ذخیره مرخصی
                leave.save()
                
                # ثبت فعالیت افزودن مرخصی
                log_user_activity(
                    user=request.user,
                    activity_type='create',
                    description=f'افزودن مرخصی جدید به گزارش {report_id}',
                    related_model='ShiftReport',
                    related_object_id=leave.id,
                    url=request.META.get('HTTP_REFERER', '/'),
                    request=request
                )
                
                logger.info(f"Leave successfully added: {leave.id}")
                return JsonResponse({'success': True})
            except Exception as e:
                logger.error(f"Error saving leave: {e}", exc_info=True)
                return JsonResponse({'success': False, 'error': f'خطا در ذخیره مرخصی: {str(e)}'})
        else:
            # ثبت خطاهای اعتبارسنجی فرم
            logger.warning(f"Form validation errors: {form.errors}")
            errors = []
            for field, error_list in form.errors.items():
                for error in error_list:
                    errors.append(f"{field}: {error}")
            
            return JsonResponse({'success': False, 'errors': errors, 'error': 'خطا در اعتبارسنجی فرم.'})
    else:
        return JsonResponse({'success': False, 'error': 'درخواست نامعتبر است.'})

@login_required
def shift_report_detail(request, report_id):
    # دریافت گزارش اصلی
    report = get_object_or_404(ShiftReport, id=report_id)
    today_date = datetime.date.today()

    # استفاده از ماژول shift_manager برای تشخیص شیفت کاری فعلی کاربر
    try:
        from shift_manager.utils import get_current_shift_and_group
        current_shift, current_group = get_current_shift_and_group(request.user)
        logger.info(f"Current shift and group for user {request.user.username}: shift={current_shift}, group={current_group}")
    except ImportError as e:
        logger.error(f"Error importing shift_manager.utils: {e}", exc_info=True)
        current_shift = None
        current_group = request.user.userprofile.group if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group') else None
    except Exception as e:
        logger.error(f"Error getting current shift and group: {e}", exc_info=True)
        current_shift = None
        current_group = request.user.userprofile.group if hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group') else None

    # ثبت فعالیت مشاهده جزئیات مرخصی
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات مرخصی شماره {report_id}',
        related_model='ShiftReport',
        related_object_id=report_id,
        url=reverse('leave_reports:shift_report_detail', args=[report_id]),
        request=request
    )

    # تبدیل تاریخ شیفت به شمسی
    shift_date_jalali = jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d')

    # دریافت مرخصی‌ها، غیبت‌ها، مرخصی‌های ساعتی و مرخصی استعلاجی مرتبط
    leaves = ShiftReport.objects.filter(
        shift_date=report.shift_date,
        work_group=report.work_group,
        leave_type='regular'
    ).select_related('user__userprofile')

    absences = ShiftReport.objects.filter(
        shift_date=report.shift_date,
        work_group=report.work_group,
        leave_type='absence'
    ).select_related('user__userprofile')

    hourly_leaves = ShiftReport.objects.filter(
        shift_date=report.shift_date,
        work_group=report.work_group,
        leave_type='hourly'
    ).select_related('user__userprofile')

    sick_leaves = ShiftReport.objects.filter(
        shift_date=report.shift_date,
        work_group=report.work_group,
        leave_type='sick_leave'
    ).select_related('user__userprofile')
    
    # دریافت لیست پرسنل برای انتخاب
    personnel_list = UserProfile.objects.select_related('user').filter(
        section=request.user.userprofile.section,
    )

    form = ShiftReportForm()

    # اگر current_group تعیین نشده، از گروه کاربر استفاده کنیم
    if current_group is None and hasattr(request.user, 'userprofile') and hasattr(request.user.userprofile, 'group'):
        current_group = request.user.userprofile.group
        logger.info(f"Using user's profile group as current_group: {current_group}")

    # بررسی آیا کاربر می‌تواند مرخصی اضافه کند
    # کاربر فقط می‌تواند در روز جاری و برای گروه کاری فعلی خود مرخصی ثبت کند
    can_add_leave = (
        report.shift_date == today_date and 
        report.work_group == current_group
    )

    # Get the shift for the report
    shift_info = get_shift_for_date(report.shift_date)
    report_shift = shift_info.get(report.work_group)

    context = {
        'report': report,
        'shift_date_jalali': shift_date_jalali,
        'leaves': leaves,
        'absences': absences,
        'hourly_leaves': hourly_leaves,
        'sick_leaves': sick_leaves,
        'title': f'جزئیات مرخصی {shift_date_jalali}',
        'form': form,
        'personnel_list': personnel_list,
        'today_date': today_date,
        'can_add_leave': can_add_leave,
        'current_shift': current_shift,
        'current_group': current_group,
        'report_shift': report_shift, # Add report_shift to context
    }
    return render(request, 'leave_reports/shift_report_detail.html', context)


@login_required
def shift_report_pdf_view(request, pk):
    # دریافت گزارش شیفت
    shift_report = get_object_or_404(ShiftReport, pk=pk)

    # دریافت مرخصی‌ها، غیبت‌ها و مرخصی‌های ساعتی مرتبط
    leaves = ShiftReport.objects.filter(
        work_group=shift_report.work_group,
        leave_type='regular',
        shift_date=shift_report.shift_date
    )
    absences = ShiftReport.objects.filter(
        work_group=shift_report.work_group,
        leave_type='absence',
        shift_date=shift_report.shift_date
    )
    hourly_leaves = ShiftReport.objects.filter(
        work_group=shift_report.work_group,
        leave_type='hourly',
        shift_date=shift_report.shift_date
    )
    sick_leaves = ShiftReport.objects.filter(
        work_group=shift_report.work_group,
        leave_type='sick_leave',
        shift_date=shift_report.shift_date
    )

    # تبدیل تاریخ شیفت به شمسی
    try:
        shift_date_jalali = jdate.fromgregorian(date=shift_report.shift_date).strftime('%Y/%m/%d')
    except Exception as e:
        print(f"Error converting shift_date: {e}")
        shift_date_jalali = "تاریخ نامعتبر"

    # ایجاد URL کامل برای دسترسی به فایل‌های استاتیک و مدیا
    static_url = request.build_absolute_uri(settings.STATIC_URL)
    media_url = request.build_absolute_uri(settings.MEDIA_URL)

    # Get shift information
    shift_info = get_shift_for_date(shift_report.shift_date)
    shift = shift_info.get(shift_report.work_group)


    # رندر کردن HTML
    template = get_template('leave_reports/shift_report_pdf.html')
    html_content = template.render({
        'shift_report': shift_report,
        'leaves': leaves,
        'absences': absences,
        'hourly_leaves': hourly_leaves,
        'sick_leaves': sick_leaves,  # مرخصی استعلاجی
        'shift_date_jalali': shift_date_jalali,
        'today': jdate.today().strftime('%Y/%m/%d'),
        'static_url': static_url,
        'media_url': media_url,
        'shift': shift, # Add shift to the context
    }, request)

    # تنظیم پاسخ به صورت PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="shift_report_{pk}.pdf"'

    # تولید PDF
    HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(response)

    return response

@login_required
def shift_report_edit(request, report_id):
    report = get_object_or_404(ShiftReport, id=report_id)
    today = datetime.date.today()

    # بررسی مجوز کاربر برای ویرایش گزارش
    if report.crate_by != request.user.userprofile:
        messages.error(request, 'شما اجازه ویرایش این گزارش را ندارید.')
        return redirect('leave_reports:shift_report_list')
    
    # بررسی تاریخ گزارش (فقط گزارش‌های امروز قابل ویرایش هستند)
    if report.shift_date != today:
        messages.error(request, 'فقط گزارش‌های امروز قابل ویرایش هستند.')
        return redirect('leave_reports:shift_report_detail', report_id=report.id)
    
    # بررسی گروه کاری (فقط گزارش‌های گروه کاری خود کاربر قابل ویرایش هستند)
    if report.work_group != request.user.userprofile.group:
        messages.error(request, 'شما فقط می‌توانید گزارش‌های گروه کاری خود را ویرایش کنید.')
        return redirect('leave_reports:shift_report_detail', report_id=report.id)

    if request.method == 'POST':
        form = ShiftReportForm(request.POST, instance=report)
        if form.is_valid():
            try:
                form.save()
                
                # ثبت فعالیت ویرایش مرخصی
                log_user_activity(
                    user=request.user,
                    activity_type='update',
                    description=f'ویرایش مرخصی با شناسه {report_id}',
                    related_model='ShiftReport',
                    related_object_id=report_id,
                    url=reverse('leave_reports:shift_report_detail', args=[report_id]),
                    request=request
                )
                
                messages.success(request, 'گزارش با موفقیت به‌روزرسانی شد.')
                return redirect('leave_reports:shift_report_detail', report_id=report.id)
            except Exception as e:
                logger.error(f"Error updating report: {e}", exc_info=True)
                messages.error(request, f'خطا در به‌روزرسانی گزارش: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'خطا در فیلد {field}: {error}')
    else:
        form = ShiftReportForm(instance=report)

    return render(request, 'leave_reports/shift_report_edit.html', {
        'form': form, 
        'report': report,
        'title': 'ویرایش مرخصی'
    })

def get_personnels(request):
    personnels = UserProfile.objects.all()
    data = []
    for personnel in personnels:
        data.append({
            'user_id': personnel.user.id,
            'full_name': personnel.user.get_full_name(),
            'personnel_code': personnel.personnel_code
        })
    return JsonResponse(data, safe=False)

@login_required
def export_shift_reports_excel(request):
    # بررسی دسترسی کاربر (مثلاً، فقط کارشناسان اداری)
    if not request.user.groups.filter(name='کارشناس اداری').exists():
        return HttpResponse("شما دسترسی به این صفحه را ندارید.", status=403)

    try:
        # دریافت و فیلتر کردن گزارش‌ها (مانند تابع shift_report_list)
        if request.user.groups.filter(name='مدیر').exists():
            reports = ShiftReport.objects.all()  # مدیر می‌تواند همه گزارش‌ها را ببیند
        else:
            reports = ShiftReport.objects.filter(crate_by=request.user.userprofile)  # کاربر فقط گزارش‌های خودش را می‌بیند

        year = request.GET.get('year')
        month = request.GET.get('month')
        day = request.GET.get('day')
        work_group = request.GET.get('work_group')
        today_filter = request.GET.get('today')

        # اگر هیچ فیلتری انتخاب نشده، گزارش‌های یک ماه اخیر رو نمایش بده
        if not year and not month and not day and not work_group and not today_filter:
            today = timezone.now().date()
            one_month_ago = today - datetime.timedelta(days=30)
            reports = reports.filter(shift_date__gte=one_month_ago, shift_date__lte=today)

        if work_group:
            reports = reports.filter(work_group=work_group)

        if today_filter == 'true':
            reports = reports.filter(shift_date=datetime.date.today())

        if year and month and day:
            try:
                gregorian_date = jdatetime.date(year=int(year), month=int(month), day=int(day)).togregorian()
                reports = reports.filter(shift_date=gregorian_date)
            except ValueError as e:
                print(f"Error converting Jalali to Gregorian: {e}")
        elif year and month:
            try:
                gregorian_start = jdatetime.date(year=int(year), month=int(month), day=1).togregorian()
                if int(month) < 12:
                    gregorian_end = jdatetime.date(year=int(year), month=int(month) + 1, day=1).togregorian()
                else:
                    gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
                reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
            except ValueError as e:
                print(f"Error converting Jalali to Gregorian: {e}")
        elif year:
            try:
                gregorian_start = jdatetime.date(year=int(year), month=1, day=1).togregorian()
                gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
                reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
            except ValueError as e:
                print(f"Error converting Jalali to Gregorian: {e}")
        
        logger.info(f"Number of reports found: {reports.count()}")  # لاگ تعداد گزارش‌ها
        
        # ایجاد فایل اکسل
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Shift Reports"

        # اضافه کردن سرفصل‌ها
        ws.append([
            'ثبت کننده', 'گروه کاری', 'شیفت کاری', 'نوع مرخصی', 'کاربر', 'کد پرسنلی', 'توضیحات',
            'زمان شروع', 'زمان پایان', 'تاریخ ثبت', 'ساعت ثبت'
        ])

        # اضافه کردن داده‌ها
        for report in reports:
            logger.info(f"Processing report: {report.id}")  # لاگ شناسه گزارش
            
            # Convert Gregorian dates to Jalali
            # shift_date_jalali = jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d')
            created_at_jalali_date = jdatetime.datetime.fromgregorian(datetime=report.created_at).strftime('%Y/%m/%d')
            created_at_jalali_time = jdatetime.datetime.fromgregorian(datetime=report.created_at).strftime('%H:%M')

            # Get shift information
            shift_info = get_shift_for_date_and_time(report.shift_date, report.created_at.time(), report.work_group)
            shift = shift_info

            ws.append([
                f"{report.crate_by.user.first_name} {report.crate_by.user.last_name}",
                report.work_group,
                # shift_date_jalali,  # Use Jalali shift date
                shift,  # Add shift information here
                report.get_leave_type_display(),
                report.user.get_full_name(),
                report.user.userprofile.personnel_code if report.user.userprofile else '',
                report.description or '',
                report.start_time.strftime('%H:%M') if report.start_time else '',
                report.end_time.strftime('%H:%M') if report.end_time else '',
                created_at_jalali_date,  # Jalali created_at date
                created_at_jalali_time,  # Jalali created_at time
            ])

        # تنظیم پاسخ HTTP برای دانلود فایل
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="shift_reports.xlsx"'
        wb.save(response)
        return response

    except Exception as e:
        logger.error(f"Error in export_shift_reports_excel: {str(e)}", exc_info=True)  # لاگ کامل خطا
        return HttpResponse(f"خطا در ایجاد فایل اکسل: {str(e)}")