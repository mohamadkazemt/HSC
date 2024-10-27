from accounts.models import UserProfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import ShiftReport, LoadingOperation, ShiftLeave, VehicleReport
from BaseInfo.models import ContractorVehicle
from shift_manager.utils import get_shift_for_date
from django.core.paginator import Paginator


def create_shift_report(request):
    today = timezone.now().date()
    shifts = get_shift_for_date(today)
    current_group = None
    current_shift = None

    # دریافت اطلاعات گروه فعلی بر اساس پروفایل کاربر لاگین شده
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            current_group = user_profile.group  # دریافت گروه از پروفایل کاربر
            current_shift = shifts.get(current_group)  # دریافت شیفت برای گروه فعلی
            print(f"کاربر {request.user.username} در گروه {current_group} قرار دارد.")
        except UserProfile.DoesNotExist:
            messages.error(request, 'پروفایل کاربری یافت نشد. لطفاً با مدیر سیستم تماس بگیرید.')

    # فیلتر کردن پرسنل‌های متعلق به گروه شیفت جاری
    personnels = UserProfile.objects.filter(group=current_group) if current_group else UserProfile.objects.none()

    # دریافت تمامی خودروهای فعال
    vehicles = ContractorVehicle.objects.filter(is_active=True)

    if request.method == "POST":
        loading_operations = request.POST.getlist('loading_operations[]')
        leaves = request.POST.getlist('leaves[]')
        vehicles_post = request.POST.getlist('vehicles[]')
        supervisor_comments = request.POST.get('supervisor_comments')

        # اعتبارسنجی داده‌های فرم
        if not loading_operations:
            messages.error(request, 'لطفا حداقل یک عملیات بارگیری را اضافه کنید.')
        if not leaves:
            messages.error(request, 'لطفا حداقل یک مرخصی را اضافه کنید.')
        if not vehicles_post:
            messages.error(request, 'لطفا حداقل یک خودرو را اضافه کنید.')

        # بررسی اینکه آیا current_group معتبر است یا خیر
        if current_group is None:
            messages.error(request, 'گروه کاربر پیدا نشد. لطفاً با مدیر سیستم تماس بگیرید.')

        # اگر هیچ پیام خطایی وجود نداشته باشد، فرآیند ذخیره‌سازی را ادامه دهید
        if not list(messages.get_messages(request)):
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
                        personnel_name=personnel,
                        leave_status=leave_status
                    )
                    shift_report.shift_leaves.add(shift_leave)

                # ذخیره خودروها
                for vehicle_id in vehicles_post:
                    vehicle = ContractorVehicle.objects.get(id=vehicle_id)
                    vehicle_report = VehicleReport.objects.create(vehicle_name=vehicle.vehicle_name)
                    shift_report.vehicle_reports.add(vehicle_report)

                messages.success(request, 'گزارش شیفت با موفقیت ذخیره شد.')
                return redirect('operations:create_shift_report')

            except Exception as e:
                messages.error(request, f'خطایی در ذخیره‌سازی اطلاعات رخ داد: {str(e)}')

    reports = ShiftReport.objects.all()
    return render(request, 'OperationsShiftReports/create_shift_report.html', {
        'shifts': shifts,
        'reports': reports,
        'personnels': personnels,
        'vehicles': vehicles,
        'current_shift': current_shift,
    })


def loading_operations_list(request):
    loading_operations = LoadingOperation.objects.all()
    paginator = Paginator(loading_operations, 10)  # نمایش 10 عملیات در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if not page_obj:
        messages.warning(request, 'هیچ عملیات بارگیری برای نمایش وجود ندارد.')

    return render(request, 'OperationsShiftReports/list.html', {'loading_operations': page_obj})
