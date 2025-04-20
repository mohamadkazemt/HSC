# app/views.py
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from accounts.models import UserProfile
from django.contrib.auth.models import User
from .forms import ShiftReportForm
from .models import ShiftReport
from django.contrib.auth.decorators import login_required, permission_required
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
from django.db import transaction, models


logger = logging.getLogger(__name__)


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
                return JsonResponse({'success': False, 'error': 'هیچ موردی برای ثبت وجود ندارد'})
            else:
                reports_to_create = []  # لیست برای ذخیره فرم ها
                form_valid = True  # پرچم
                errors = []  # لیست خطاها
                
                for i in range(total_leaves):
                    try:
                        user_id = request.POST.get(f'user_{i}')
                        shift_date_str = request.POST.get(f'shift_date_{i}')  # تاریخ شمسی
                        shift_type = request.POST.get(f'shift_type_{i}')
                        
                        # تبدیل تاریخ شمسی به میلادی
                        try:
                            year, month, day = map(int, shift_date_str.split('-'))
                            jalali_date = jdatetime.date(year, month, day)
                            shift_date = jalali_date.togregorian()
                            logger.info(f"Date conversion successful: Jalali {shift_date_str} -> Gregorian {shift_date}")
                        except ValueError as e:
                            errors.append(f'تاریخ نامعتبر در مورد {i + 1}: {str(e)}')
                            form_valid = False
                            continue

                        # اعتبارسنجی تکراری نبودن گزارش
                        existing_report = ShiftReport.objects.filter(
                            user_id=user_id,
                            shift_date=shift_date
                        ).first()

                        if existing_report:
                            errors.append(f'برای کاربر {User.objects.get(id=user_id).get_full_name()} در تاریخ {shift_date_str} قبلاً گزارش ثبت شده است')
                            form_valid = False
                            continue

                        report_data = {
                            'user': user_id,
                            'leave_type': request.POST.get(f'leave_type_{i}'),
                            'status': 'reported',
                            'description': request.POST.get(f'description_{i}'),
                            'shift_date': shift_date,
                            'shift_type': shift_type,
                        }

                        if report_data['leave_type'] == 'hourly':
                            start_time = request.POST.get(f'start_time_{i}')
                            end_time = request.POST.get(f'end_time_{i}')
                            
                            # اعتبارسنجی زمان شروع و پایان
                            if not start_time or not end_time:
                                errors.append(f'برای مرخصی ساعتی در مورد {i + 1} باید ساعت شروع و پایان وارد شود')
                                form_valid = False
                                continue
                                
                            report_data.update({
                                'start_time': start_time,
                                'end_time': end_time
                            })
                        elif report_data['leave_type'] in ['absence', 'sick_leave']:
                            description = request.POST.get(f'description_{i}')
                            if not description:
                                errors.append(f'برای {report_data["leave_type"]} در مورد {i + 1} باید توضیحات وارد شود')
                                form_valid = False
                                continue

                        logger.info(f"Processing leave {i + 1} with data: {report_data}")

                        form = ShiftReportForm(report_data)
                        if form.is_valid():
                            report = form.save(commit=False)
                            report.crate_by = request.user.userprofile
                            report.work_group = request.user.userprofile.group
                            reports_to_create.append(report)
                        else:
                            for field, error_list in form.errors.items():
                                field_name = {
                                    'user': 'کاربر',
                                    'leave_type': 'نوع مرخصی',
                                    'start_time': 'زمان شروع',
                                    'end_time': 'زمان پایان',
                                    'description': 'توضیحات',
                                    'shift_date': 'تاریخ شیفت',
                                    'shift_type': 'شیفت کاری',
                                    'status': 'وضعیت'
                                }.get(field, field)
                                
                                for error in error_list:
                                    errors.append(f"خطا در فیلد {field_name} در مورد {i + 1}: {error}")
                            form_valid = False
                            logger.warning(f"Form not valid for leave {i + 1}: {form.errors}")
                    except Exception as e:
                        errors.append(f"خطا در پردازش مورد {i + 1}: {str(e)}")
                        logger.error(f"Error processing leave {i + 1}: {e}", exc_info=True)
                        form_valid = False

                if form_valid:
                    try:
                        with transaction.atomic():
                            ShiftReport.objects.bulk_create(reports_to_create)
                            logger.info(f"{len(reports_to_create)} leaves saved successfully")
                            
                            log_user_activity(
                                user=request.user,
                                activity_type='create',
                                description=f'ثبت {len(reports_to_create)} مورد مرخصی',
                                related_model='ShiftReport',
                                related_object_id=None,
                                url=reverse('leave_reports:shift_report_list'),
                                request=request
                            )
                            
                            return JsonResponse({
                                'success': True,
                                'message': f'{len(reports_to_create)} مورد با موفقیت ثبت شد'
                            })
                    except Exception as e:
                        logger.error(f"Error during bulk create: {e}", exc_info=True)
                        return JsonResponse({
                            'success': False,
                            'error': f'خطا در ذخیره دسته‌ای: {str(e)}'
                        })
                else:
                    logger.warning(f"Errors found, not saving.")
                    return JsonResponse({
                        'success': False,
                        'errors': errors
                    })

        except Exception as e:
            logger.error(f"System error: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'خطای سیستمی: {str(e)}'
            })

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
    
    # Get filter parameters from request
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')
    work_group = request.GET.get('work_group')
    today_filter = request.GET.get('today')
    search_query = request.GET.get('search', '').strip()
    
    # Get all reports without user restrictions
    reports = ShiftReport.objects.select_related('user', 'user__userprofile', 'crate_by', 'crate_by__user').all()

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
            logger.error(f"Error converting Jalali to Gregorian: {e}")
            messages.error(request, 'خطا در تبدیل تاریخ')
    elif year and month:
        try:
            gregorian_start = jdatetime.date(year=int(year), month=int(month), day=1).togregorian()
            if int(month) < 12:
                gregorian_end = jdatetime.date(year=int(year), month=int(month) + 1, day=1).togregorian()
            else:
                gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
            reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
        except ValueError as e:
            logger.error(f"Error converting Jalali to Gregorian: {e}")
            messages.error(request, 'خطا در تبدیل تاریخ')
    elif year:
        try:
            gregorian_start = jdatetime.date(year=int(year), month=1, day=1).togregorian()
            gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
            reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
        except ValueError as e:
            logger.error(f"Error converting Jalali to Gregorian: {e}")
            messages.error(request, 'خطا در تبدیل تاریخ')

    # تغییر نحوه گروه‌بندی برای نمایش بر اساس پرسنل
    report_list = []
    for report in reports:
        # تبدیل تاریخ میلادی به شمسی
        shift_date_jalali = jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d')
        created_at_jalali = jdatetime.datetime.fromgregorian(datetime=report.created_at).strftime('%Y/%m/%d %H:%M')
        
        report_data = {
            'user_id': report.user.id,
            'user_name': f"{report.user.first_name} {report.user.last_name}",
            'personnel_code': report.user.userprofile.personnel_code if hasattr(report.user, 'userprofile') else '',
            'shift_date': shift_date_jalali,
            'leave_type': report.leave_type,
            'leave_type_display': report.get_leave_type_display(),
            'shift': report.get_shift_type_display(),
            'description': report.description or '',
            'start_time': report.start_time.strftime('%H:%M') if report.start_time else '-',
            'end_time': report.end_time.strftime('%H:%M') if report.end_time else '-',
            'crate_by': f"{report.crate_by.user.first_name} {report.crate_by.user.last_name}",
            'created_at': created_at_jalali,
            'status': report.status,
            'exported_to_excel': report.exported_to_excel,
            'registration': report.registration,
            'leave_ids': [report.id]
        }
        report_list.append(report_data)
        
    # اعمال جستجو روی تمام فیلدها
    if search_query:
        filtered_list = []
        search_query = search_query.lower()
        for item in report_list:
            if any(search_query in str(value).lower() for value in item.values()):
                filtered_list.append(item)
        report_list = filtered_list

    # مرتب‌سازی بر اساس تاریخ مرخصی و نام کاربر
    report_list.sort(key=lambda x: (x['shift_date'], x['user_name']))

    # Implement pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(report_list, 10)  # Show 10 reports per page
    try:
        reports_page = paginator.page(page)
    except PageNotAnInteger:
        reports_page = paginator.page(1)
    except EmptyPage:
        reports_page = paginator.page(paginator.num_pages)

    # Extract years, months, and days
    all_years = set()
    all_months = set()
    all_days = set()
    
    for r in report_list:
        if 'shift_date' in r and r['shift_date']:
            try:
                date_parts = r['shift_date'].split('/')
                if len(date_parts) == 3:
                    all_years.add(int(date_parts[0]))
                    all_months.add(int(date_parts[1]))
                    all_days.add(int(date_parts[2]))
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing date: {e}")
                continue

    # تبدیل به لیست و مرتب‌سازی
    all_years = sorted(list(all_years), reverse=True)
    all_months = sorted(list(all_months))
    all_days = sorted(list(all_days))

    # Extract work groups
    all_work_groups = sorted(list({r.work_group for r in ShiftReport.objects.all() if r.work_group}))

    # تمیز کردن پارامترهای None
    year = year if year not in ['None', None] else ''
    month = month if month not in ['None', None] else ''
    day = day if day not in ['None', None] else ''
    work_group = work_group if work_group not in ['None', None] else ''
    today_filter = today_filter if today_filter not in ['None', None] else ''

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
        
        # دریافت نوع مرخصی
        leave_type = request.POST.get('leave_type')
        if not leave_type:
            logger.error("Missing leave_type in request")
            return JsonResponse({'success': False, 'error': 'نوع مرخصی یافت نشد.'})
        
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
        'report_shift': report.get_shift_type_display(), # Use shift_type display instead of shift_info
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
        'shift': shift_report.get_shift_type_display(), # Use shift_type display instead of shift_info
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
    try:
        # دریافت همه گزارش‌ها
        reports = ShiftReport.objects.all().select_related('user', 'user__userprofile', 'crate_by', 'crate_by__user')

        # دریافت پارامترهای فیلتر
        year = request.GET.get('year')
        month = request.GET.get('month')
        day = request.GET.get('day')
        work_group = request.GET.get('work_group')
        today_filter = request.GET.get('today')
        search_query = request.GET.get('search', '').strip()

        # اعمال فیلترها
        if work_group:
            reports = reports.filter(work_group=work_group)

        if today_filter == 'true':
            reports = reports.filter(shift_date=datetime.date.today())

        if year and month and day:
            try:
                gregorian_date = jdatetime.date(year=int(year), month=int(month), day=int(day)).togregorian()
                reports = reports.filter(shift_date=gregorian_date)
            except ValueError as e:
                logger.error(f"Error converting Jalali to Gregorian: {e}")
        elif year and month:
            try:
                gregorian_start = jdatetime.date(year=int(year), month=int(month), day=1).togregorian()
                if int(month) < 12:
                    gregorian_end = jdatetime.date(year=int(year), month=int(month) + 1, day=1).togregorian()
                else:
                    gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
                reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
            except ValueError as e:
                logger.error(f"Error converting Jalali to Gregorian: {e}")
        elif year:
            try:
                gregorian_start = jdatetime.date(year=int(year), month=1, day=1).togregorian()
                gregorian_end = jdatetime.date(year=int(year) + 1, month=1, day=1).togregorian()
                reports = reports.filter(shift_date__gte=gregorian_start, shift_date__lt=gregorian_end)
            except ValueError as e:
                logger.error(f"Error converting Jalali to Gregorian: {e}")

        # اعمال جستجو
        if search_query:
            reports = reports.filter(
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query) |
                models.Q(user__userprofile__personnel_code__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(shift_type__icontains=search_query) |
                models.Q(leave_type__icontains=search_query)
            )

        # مرتب‌سازی بر اساس تاریخ مرخصی و نام کاربر
        reports = reports.order_by('shift_date', 'user__first_name', 'user__last_name')

        # تبدیل به لیست برای پردازش
        report_list = []
        for report in reports:
            # تبدیل تاریخ میلادی به شمسی
            shift_date_jalali = jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d')
            created_at_jalali = jdatetime.datetime.fromgregorian(datetime=report.created_at).strftime('%Y/%m/%d %H:%M')
            
            report_data = {
                'user_name': f"{report.user.first_name} {report.user.last_name}",
                'personnel_code': report.user.userprofile.personnel_code if hasattr(report.user, 'userprofile') else '',
                'shift_date': shift_date_jalali,
                'leave_type': report.get_leave_type_display(),
                'shift': report.get_shift_type_display(),
                'description': report.description or '',
                'start_time': report.start_time.strftime('%H:%M') if report.start_time else '',
                'end_time': report.end_time.strftime('%H:%M') if report.end_time else '',
                'crate_by': f"{report.crate_by.user.first_name} {report.crate_by.user.last_name}" if report.crate_by else '',
                'created_at': created_at_jalali,
                'registration': report.registration,
                'leave_ids': [report.id]
            }
            report_list.append(report_data)

        # ایجاد فایل اکسل
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Shift Reports"

        # اضافه کردن سرفصل‌ها
        headers = [
            'نام و نام خانوادگی',
            'کد پرسنلی',
            'تاریخ مرخصی',
            'نوع مرخصی',
            'شیفت کاری',
            'توضیحات',
            'زمان شروع',
            'زمان پایان',
            'ثبت کننده',
            'تاریخ ثبت',
            'وضعیت ثبت'
        ]
        ws.append(headers)

        # اضافه کردن داده‌ها
        for report in report_list:
            row = [
                report['user_name'],
                report['personnel_code'],
                report['shift_date'],
                report['leave_type'],
                report['shift'],
                report['description'],
                report['start_time'],
                report['end_time'],
                report['crate_by'],
                report['created_at'],
                'ثبت شده' if report['registration'] else 'ثبت نشده'
            ]
            ws.append(row)

        # تنظیم عرض ستون‌ها
        for column in ws.columns:
            max_length = 0
            column = list(column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column[0].column_letter].width = adjusted_width

        # علامت‌گذاری گزارش‌ها به عنوان خروجی گرفته شده
        reports.update(exported_to_excel=True)

        # تنظیم پاسخ HTTP برای دانلود فایل
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="shift_reports.xlsx"'
        wb.save(response)
        return response

    except Exception as e:
        logger.error(f"Error in export_shift_reports_excel: {str(e)}", exc_info=True)
        return HttpResponse(f"خطا در ایجاد فایل اکسل: {str(e)}")

@login_required
def toggle_status(request, report_id):
    if request.method == 'POST':
        try:
            # بررسی دسترسی کاربر
            if not hasattr(request.user, 'userprofile') or not request.user.userprofile.is_hr_user:
                return JsonResponse({
                    'success': False,
                    'error': 'شما دسترسی لازم برای این عملیات را ندارید'
                })

            # دریافت گزارش
            report = get_object_or_404(ShiftReport, id=report_id)
            
            # تغییر وضعیت
            report.status = not report.status
            report.save()

            # ثبت فعالیت
            status_text = 'ثبت شده' if report.status else 'ثبت نشده'
            log_user_activity(
                user=request.user,
                activity_type='update',
                description=f'تغییر وضعیت مرخصی {report_id} به {status_text}',
                related_model='ShiftReport',
                related_object_id=report_id,
                url=request.META.get('HTTP_REFERER', '/'),
                request=request
            )

            return JsonResponse({
                'success': True,
                'new_status': report.status
            })

        except Exception as e:
            logger.error(f"Error toggling report status: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'درخواست نامعتبر'
    })

@login_required
@permission_required('auth.کارشناس اداری', raise_exception=True)
def toggle_registration(request, report_id):
    try:
        report = ShiftReport.objects.get(id=report_id)
        report.registration = not report.registration
        report.save()
        return JsonResponse({
            'success': True,
            'message': 'وضعیت ثبت گزارش با موفقیت تغییر کرد',
            'registration': report.registration
        })
    except ShiftReport.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'گزارش مورد نظر یافت نشد'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)