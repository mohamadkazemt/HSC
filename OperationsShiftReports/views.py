from accounts.models import UserProfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import ShiftReport, LoadingOperation, ShiftLeave, VehicleReport
from BaseInfo.models import ContractorVehicle
from shift_manager.utils import get_shift_for_date
from django.core.paginator import Paginator


from django.http import JsonResponse

def create_shift_report(request):
    if request.method == "POST":
        try:
            loading_operations = request.POST.getlist('loading_operations[]')
            leaves = request.POST.getlist('leaves[]')
            vehicles_post = request.POST.getlist('vehicles[]')
            supervisor_comments = request.POST.get('supervisor_comments')

            # اعتبارسنجی داده‌های ورودی
            if not loading_operations:
                return JsonResponse({
                    'messages': [{'tags': 'error', 'message': 'لطفا حداقل یک عملیات بارگیری را اضافه کنید.'}]
                })
            if not leaves:
                return JsonResponse({
                    'messages': [{'tags': 'error', 'message': 'لطفا حداقل یک مرخصی را اضافه کنید.'}]
                })
            if not vehicles_post:
                return JsonResponse({
                    'messages': [{'tags': 'error', 'message': 'لطفا حداقل یک خودرو را اضافه کنید.'}]
                })

            # دریافت گروه کاربر
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                current_group = user_profile.group
            except UserProfile.DoesNotExist:
                return JsonResponse({
                    'messages': [{'tags': 'error', 'message': 'پروفایل کاربری یافت نشد.'}]
                })

            # ایجاد گزارش شیفت
            shift_report = ShiftReport.objects.create(
                shift_date=timezone.now().date(),
                supervisor_comments=supervisor_comments,
                group=current_group
            )

            # ذخیره عملیات بارگیری
            for op in loading_operations:
                stone_type, load_count = op.split(',')
                loading_operation = LoadingOperation.objects.create(
                    stone_type=stone_type,
                    load_count=int(load_count)
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

            return JsonResponse({
                'messages': [{'tags': 'success', 'message': 'گزارش شیفت با موفقیت ثبت شد.'}]
            })

        except Exception as e:
            return JsonResponse({
                'messages': [{'tags': 'error', 'message': f'خطا در ثبت گزارش: {str(e)}'}]
            })

    # GET request - نمایش فرم
    today = timezone.now().date()
    shifts = get_shift_for_date(today)
    current_group = None
    current_shift = None

    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            current_group = user_profile.group
            current_shift = shifts.get(current_group)
        except UserProfile.DoesNotExist:
            messages.error(request, 'پروفایل کاربری یافت نشد.')

    personnels = UserProfile.objects.filter(group=current_group) if current_group else UserProfile.objects.none()
    vehicles = ContractorVehicle.objects.filter(is_active=True)

    return render(request, 'OperationsShiftReports/create_shift_report.html', {
        'shifts': shifts,
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
