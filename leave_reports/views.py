# app/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from accounts.models import UserProfile
from .forms import ShiftReportForm
from .models import ShiftReport
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory


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




@login_required
def shift_report_list(request):
    reports = ShiftReport.objects.all()
    print(reports)
    return render(request, 'leave_reports/shift_report_list.html', {'reports': reports})