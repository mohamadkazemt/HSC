from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from shift_manager.utils import get_shift_for_date
from .models import ShiftReport, LoadingOperation, ShiftLeave, VehicleReport
from .forms import LoadingOperationFormSet, ShiftLeaveFormSet

def create_shift_report(request):
    today = timezone.now().date()
    shifts = get_shift_for_date(today)

    if request.method == "POST":
        # دریافت داده‌ها از فرم
        loading_operations = request.POST.getlist('loading_operations[]')
        leaves = request.POST.getlist('leaves[]')
        vehicles = request.POST.getlist('vehicles[]')
        supervisor_comments = request.POST.get('supervisor_comments')

        if not loading_operations or not leaves or not vehicles:
            messages.error(request, 'لطفا تمام فیلدها را پر کنید و حداقل یک آیتم در هر بخش اضافه کنید.')
            reports = ShiftReport.objects.all()
            return render(request, 'OperationsShiftReports/create_shift_report.html', {
                'shifts': shifts,
                'reports': reports,
                'error_message': 'لطفا تمام فیلدها را پر کنید و حداقل یک آیتم در هر بخش اضافه کنید.'
            })

        try:
            # ذخیره گزارش شیفت
            shift_report = ShiftReport.objects.create(
                shift_date=today,
                supervisor_comments=supervisor_comments
            )

            # ذخیره عملیات بارگیری
            for op in loading_operations:
                stone_type, load_count = op.split(',')
                if not stone_type or not load_count:
                    messages.error(request, 'خطا در ورود اطلاعات عملیات بارگیری.')
                    return redirect('create_shift_report')

                loading_operation = LoadingOperation.objects.create(
                    stone_type=stone_type,
                    load_count=load_count
                )
                shift_report.loading_operations.add(loading_operation)

            # ذخیره مرخصی‌ها
            for leave in leaves:
                personnel_name, leave_status = leave.split(',')
                if not personnel_name or not leave_status:
                    messages.error(request, 'خطا در ورود اطلاعات مرخصی‌ها.')
                    return redirect('create_shift_report')

                shift_leave = ShiftLeave.objects.create(
                    personnel_name=personnel_name,
                    leave_status=leave_status
                )
                shift_report.shift_leaves.add(shift_leave)

            # ذخیره خودروها
            for vehicle in vehicles:
                if not vehicle:
                    messages.error(request, 'خطا در ورود اطلاعات خودروها.')
                    return redirect('create_shift_report')

                vehicle_report = VehicleReport.objects.create(vehicle_name=vehicle)
                shift_report.vehicle_reports.add(vehicle_report)

            messages.success(request, 'گزارش شیفت با موفقیت ذخیره شد.')
            return redirect('create_shift_report')

        except Exception as e:
            # نمایش پیام خطای دقیق به کاربر
            messages.error(request, f'خطایی در ذخیره‌سازی اطلاعات رخ داد: {str(e)}')
            reports = ShiftReport.objects.all()
            return render(request, 'OperationsShiftReports/create_shift_report.html', {
                'shifts': shifts,
                'reports': reports,
                'error_message': str(e)
            })

    # دریافت تمام گزارشات برای نمایش
    reports = ShiftReport.objects.all()
    return render(request, 'OperationsShiftReports/create_shift_report.html', {'shifts': shifts, 'reports': reports})
