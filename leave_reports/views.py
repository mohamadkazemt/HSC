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
from django.db.models import Count, Q, Subquery, OuterRef



logger = logging.getLogger(__name__)


from django.db import transaction

@login_required
def create_shift_report(request):
    current_user = request.user.userprofile
    personnel_list = UserProfile.objects.select_related('user').filter(
        section=current_user.section,
    )

    errors = []
    if request.method == 'POST':
        logger.info("POST request received for create_shift_report")
        try:
            total_leaves = int(request.POST.get('total_leaves', 0))
            logger.info(f"Total leaves from request: {total_leaves}")
            if total_leaves == 0:
                errors.append('هیچ موردی برای ثبت وجود ندارد')
                logger.warning("No leaves to process")
            else:
                reports_to_create = []  # لیست برای ذخیره فرم ها
                form_valid = True  # پرچم

                for i in range(total_leaves):
                    try:
                        user_id = request.POST.get(f'user_{i}')
                        report_data = {
                            'user': user_id,
                            'leave_type': request.POST.get(f'leave_type_{i}'),
                            'status': 'reported',
                            'description': request.POST.get(f'description_{i}'),
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
                            for field, error_list in form.errors.items():
                                for error in error_list:
                                    errors.append(f"خطا در فیلد {field}: {error}")
                            form_valid = False  # تنظیم پرچم به False
                        logger.warning(f"Form not valid for leave {i + 1}: {form.errors}")
                    except Exception as e:
                        errors.append(f"خطا در پردازش مورد {i + 1}: {str(e)}")
                        logger.error(f"Error processing leave {i + 1}: {e}", exc_info=True)
                        form_valid = False  # تنظیم پرچم به False

                if form_valid: # ذخیره دسته‌ای اگر همه معتبر بودن
                    try:
                        with transaction.atomic():  # استفاده از atomic transaction
                            ShiftReport.objects.bulk_create(reports_to_create)
                            logger.info(f"{len(reports_to_create)} leaves saved successfully")
                            return JsonResponse({'success': True, 'message': f'{len(reports_to_create)} مورد با موفقیت ثبت شد'})
                    except Exception as e:
                        errors.append(f'خطا در ذخیره دسته‌ای: {str(e)}')
                        logger.error(f"Error during bulk create: {e}", exc_info=True)
                        return JsonResponse({'success': False, 'error': 'خطا در ثبت اطلاعات', 'details': errors})

                else:
                    logger.warning(f"Errors found, not saving. Errors:{errors}")
                    return JsonResponse({'success': False, 'error': 'خطا در ثبت اطلاعات', 'details': errors})

        except Exception as e:
            errors.append(f'خطای سیستمی: {str(e)}')
            logger.error(f"System error: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'خطای سیستمی: {str(e)}'})

    form = ShiftReportForm()
    context = {
        'form': form,
        'personnels': personnel_list,
        'errors': errors,
        'title': 'ثبت مرخصی',
    }
    return render(request, 'leave_reports/shift_report.html', context)





@login_required
def shift_report_list(request):
    reports = ShiftReport.objects.all()  # Get all reports initially

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
    grouped_reports = reports.values('shift_date', 'work_group').annotate(
        total_regular=Count('id', filter=Q(leave_type='regular')),
        total_hourly=Count('id', filter=Q(leave_type='hourly')),
        total_absence=Count('id', filter=Q(leave_type='absence')),
        total_sick_leave=Count('id', filter=Q(leave_type='sick_leave')),
        total_persons=Count('user', distinct=True)
    ).order_by('-shift_date')

    # Convert Gregorian date to Jalali and add ID to grouped reports
    report_with_ids = []
    for report in grouped_reports:
        matching_report = ShiftReport.objects.filter(
            shift_date=report['shift_date'],
            work_group=report['work_group']
        ).first()

        if matching_report:
            report['id'] = matching_report.id
        report['shift_date'] = jdatetime.date.fromgregorian(date=report['shift_date']).strftime('%Y/%m/%d')
        report_with_ids.append(report)

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
def shift_report_detail(request, report_id):
    # دریافت گزارش اصلی
    report = get_object_or_404(ShiftReport, id=report_id)

    # تبدیل تاریخ شیفت به شمسی
    shift_date_jalali = jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d')

    # دسته‌بندی داده‌ها
    leaves = ShiftReport.objects.filter(work_group=report.work_group, leave_type='regular',
                                        shift_date=report.shift_date)
    absences = ShiftReport.objects.filter(work_group=report.work_group, leave_type='absence',
                                          shift_date=report.shift_date)
    hourly_leaves = ShiftReport.objects.filter(work_group=report.work_group, leave_type='hourly',
                                               shift_date=report.shift_date)
    sick_leaves = ShiftReport.objects.filter(work_group=report.work_group, leave_type='sick_leave',
                                             shift_date=report.shift_date)

    context = {
        'report': report,
        'shift_date_jalali': shift_date_jalali,  # تاریخ شمسی
        'leaves': leaves,
        'absences': absences,
        'hourly_leaves': hourly_leaves,
        'sick_leaves': sick_leaves,
        'title': 'جزییات مرخصی',
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
    }, request)

    # تنظیم پاسخ به صورت PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="shift_report_{pk}.pdf"'

    # تولید PDF
    HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(response)

    return response