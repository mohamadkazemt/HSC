# app/views.py
import datetime
from django.shortcuts import render, redirect
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
import datetime







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




def shift_report_list(request):
    reports = ShiftReport.objects.all()

    year = request.GET.get('year')
    month = request.GET.get('month')
    day = request.GET.get('day')

    if year:
        reports = reports.filter(shift_date__year=int(year))
    if month:
        reports = reports.filter(shift_date__month=int(month))
    if day:
        reports = reports.filter(shift_date__day=int(day))

    grouped_reports = reports.values('shift_date', 'work_group').annotate(
        total_count=Count('id'),
        regular_leaves=Count('id', filter=Q(leave_type='regular')),
        hourly_leaves=Count('id', filter=Q(leave_type='hourly')),
        absences=Count('id', filter=Q(leave_type='absence'))
    )

    # تبدیل تاریخ‌ها به شمسی
    for report in grouped_reports:
        try:
            if isinstance(report['shift_date'], (datetime.date, datetime.datetime)):
                report['shift_date'] = jdatetime.date.fromgregorian(date=report['shift_date']).strftime('%Y/%m/%d')
            else:
                report['shift_date'] = "تاریخ نامعتبر"
        except Exception as e:
            print(f"Error converting date: {e}")
            report['shift_date'] = "تاریخ نامعتبر"

    valid_reports = [r for r in grouped_reports if r['shift_date'] != "تاریخ نامعتبر"]

    all_years = sorted(
        list({jdatetime.date.fromgregorian(date=r['shift_date']).year for r in valid_reports}),
        reverse=True
    )
    all_months = sorted(
        list({jdatetime.date.fromgregorian(date=r['shift_date']).month for r in valid_reports})
    )
    all_days = sorted(
        list({jdatetime.date.fromgregorian(date=r['shift_date']).day for r in valid_reports})
    )

    return render(request, 'leave_reports/shift_report_list.html', {
        'reports': grouped_reports,
        'years': all_years,
        'months': all_months,
        'days': all_days,
        'selected_year': year,
        'selected_month': month,
        'selected_day': day,
    })

