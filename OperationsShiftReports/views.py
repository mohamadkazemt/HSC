from accounts.models import UserProfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from .models import ShiftReport, LoadingOperation, ShiftLeave, VehicleReport
from shift_manager.utils import get_shift_for_date

def create_shift_report(request):
    today = timezone.now().date()
    shifts = get_shift_for_date(today)

    # دریافت اطلاعات گروه فعلی بر اساس پروفایل کاربر لاگین شده
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            current_group = user_profile.group  # دریافت گروه از پروفایل کاربر
            current_shift = shifts.get(current_group)  # دریافت شیفت برای گروه فعلی
        except UserProfile.DoesNotExist:
            messages.error(request, 'پروفایل کاربری یافت نشد. لطفاً با مدیر سیستم تماس بگیرید.')
            current_group = None
    else:
        messages.error(request, 'لطفاً وارد شوید.')
        return redirect('login')

    # فیلتر کردن پرسنل‌های متعلق به گروه شیفت جاری
    if current_group:
        personnels = UserProfile.objects.filter(group=current_group)
    else:
        personnels = UserProfile.objects.none()

    if request.method == "POST":
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
                'personnels': personnels,
                'error_message': 'لطفا تمام فیلدها را پر کنید و حداقل یک آیتم در هر بخش اضافه کنید.'
            })

        try:
            # ذخیره گزارش شیفت
            shift_report = ShiftReport.objects.create(
                shift_date=today,
                supervisor_comments=supervisor_comments,
                group=current_group  # گروه فعلی به صورت دینامیک
            )

            # ذخیره عملیات بارگیری
            for op in loading_operations:
                stone_type, load_count = op.split(',')
                loading_operation = LoadingOperation.objects.create(
                    stone_type=stone_type,
                    load_count=load_count
                )
                shift_report.loading_operations.add(loading_operation)

            # ذخیره مرخصی‌ها
            for leave in leaves:
                personnel_id, leave_status = leave.split(',')
                personnel = UserProfile.objects.get(id=personnel_id)

                shift_leave = ShiftLeave.objects.create(
                    personnel=personnel,
                    leave_status=leave_status
                )
                shift_report.shift_leaves.add(shift_leave)

            # ذخیره خودروها
            for vehicle in vehicles:
                vehicle_report = VehicleReport.objects.create(vehicle_name=vehicle)
                shift_report.vehicle_reports.add(vehicle_report)

            messages.success(request, 'گزارش شیفت با موفقیت ذخیره شد.')
            return redirect('create_shift_report')

        except Exception as e:
            messages.error(request, f'خطایی در ذخیره‌سازی اطلاعات رخ داد: {str(e)}')
            reports = ShiftReport.objects.all()
            return render(request, 'OperationsShiftReports/create_shift_report.html', {
                'shifts': shifts,
                'reports': reports,
                'personnels': personnels,
                'error_message': str(e)
            })

    reports = ShiftReport.objects.all()
    return render(request, 'OperationsShiftReports/create_shift_report.html', {
        'shifts': shifts,
        'reports': reports,
        'personnels': personnels,
        'current_shift': current_shift  # اضافه کردن شیفت فعلی برای نمایش در قالب
    })
