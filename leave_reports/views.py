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
from django.db.models import Count, Q
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.template.loader import get_template
from django.conf import settings
from jdatetime import date as jdate



@login_required
def create_shift_report(request):
    current_user = request.user.userprofile

    personnel_list = UserProfile.objects.select_related('user').filter(
        group=current_user.group,
        department=current_user.department,
        unit=current_user.unit
    )

    if request.method == 'POST':
        try:
            total_leaves = int(request.POST.get('total_leaves', 0))
            if total_leaves == 0:
                return JsonResponse({'success': False, 'error': 'هیچ موردی برای ثبت وجود ندارد'})

            success_count = 0
            errors = []

            for i in range(total_leaves):
                try:
                    user_id = request.POST.get(f'user_{i}')
                    report_data = {
                        'user': user_id,
                        'leave_type': request.POST.get(f'leave_type_{i}'),
                        'status': 'reported'
                    }

                    if report_data['leave_type'] == 'hourly':
                        report_data.update({
                            'start_time': request.POST.get(f'start_time_{i}'),
                            'end_time': request.POST.get(f'end_time_{i}')
                        })

                    form = ShiftReportForm(report_data)
                    if form.is_valid():
                        report = form.save(commit=False)
                        report.crate_by = request.user.userprofile
                        report.work_group = request.user.userprofile.group
                        report.save()  # تاریخ به‌طور خودکار توسط مدل تنظیم می‌شود
                        success_count += 1
                    else:
                        errors.append(f"خطا در مورد {i + 1}: {form.errors}")
                except Exception as e:
                    errors.append(f"خطا در پردازش مورد {i + 1}: {str(e)}")

            if success_count > 0:
                return JsonResponse({'success': True, 'message': f'{success_count} مورد با موفقیت ثبت شد'})
            else:
                return JsonResponse({'success': False, 'error': 'خطا در ثبت اطلاعات', 'details': errors})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'خطای سیستمی: {str(e)}'})

    form = ShiftReportForm()
    return render(request, 'leave_reports/shift_report.html', {'form': form, 'personnels': personnel_list})









from django.db.models import Count, Q
import jdatetime
from django.shortcuts import render
import datetime

def shift_report_list(request):
    reports = ShiftReport.objects.all()

    # دریافت فیلترهای سال، ماه و روز
    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')

    # تبدیل تاریخ شمسی به میلادی برای فیلتر
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

    # گروه‌بندی گزارش‌ها و شمارش انواع مرخصی و تعداد افراد
    grouped_reports = reports.values('shift_date', 'work_group').annotate(
        total_regular=Count('id', filter=Q(leave_type='regular')),
        total_hourly=Count('id', filter=Q(leave_type='hourly')),
        total_absence=Count('id', filter=Q(leave_type='absence')),
        total_persons=Count('user', distinct=True)  # تعداد افراد یکتا
    )

    # نگاشت ID‌های اصلی به گزارش‌های گروه‌بندی‌شده
    report_with_ids = []
    for report in grouped_reports:
        matching_report = reports.filter(
            shift_date=report['shift_date'],
            work_group=report['work_group']
        ).first()

        if matching_report:
            report['id'] = matching_report.id
        report['shift_date'] = jdatetime.date.fromgregorian(date=report['shift_date']).strftime('%Y/%m/%d')
        report_with_ids.append(report)

    # استخراج سال‌ها، ماه‌ها و روزها به شمسی
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

    return render(request, 'leave_reports/shift_report_list.html', {
        'reports': report_with_ids,
        'years': all_years,
        'months': all_months,
        'days': all_days,
        'selected_year': year,
        'selected_month': month,
        'selected_day': day,
    })









@login_required
def shift_report_detail(request, report_id):
    # دریافت گزارش اصلی
    report = get_object_or_404(ShiftReport, id=report_id)

    # تبدیل تاریخ شیفت به شمسی
    shift_date_jalali = jdatetime.date.fromgregorian(date=report.shift_date).strftime('%Y/%m/%d')

    # دسته‌بندی داده‌ها
    leaves = ShiftReport.objects.filter(work_group=report.work_group, leave_type='regular', shift_date=report.shift_date)
    absences = ShiftReport.objects.filter(work_group=report.work_group, leave_type='absence', shift_date=report.shift_date)
    hourly_leaves = ShiftReport.objects.filter(work_group=report.work_group, leave_type='hourly', shift_date=report.shift_date)

    context = {
        'report': report,
        'shift_date_jalali': shift_date_jalali,  # تاریخ شمسی
        'leaves': leaves,
        'absences': absences,
        'hourly_leaves': hourly_leaves,
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




