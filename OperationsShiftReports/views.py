import os
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from .models import ShiftReport, LoadingOperation, ShiftLeave, VehicleReport
from accounts.models import UserProfile
from BaseInfo.models import ContractorVehicle
from shift_manager.utils import get_shift_for_date


def create_shift_report(request):
    if request.method == "POST":
        try:
            loading_operations = request.POST.getlist('loading_operations[]')
            leaves = request.POST.getlist('leaves[]')
            vehicles_post = request.POST.getlist('vehicles[]')
            supervisor_comments = request.POST.get('supervisor_comments')
            attached_file = request.FILES.get('attached_file')

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
            if not supervisor_comments:
                return JsonResponse({
                    'messages': [{'tags': 'error', 'message': 'لطفا توضیحات سرشیفت را وارد کنید.'}]
                })

            # اعتبارسنجی فایل
            if attached_file:
                # بررسی سایز فایل (5MB)
                if attached_file.size > 5 * 1024 * 1024:
                    return JsonResponse({
                        'messages': [{'tags': 'error', 'message': 'حجم فایل نباید بیشتر از 5 مگابایت باشد.'}]
                    })

                # بررسی پسوند فایل
                allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                ext = os.path.splitext(attached_file.name)[1].lower()
                if ext not in allowed_extensions:
                    return JsonResponse({
                        'messages': [{'tags': 'error', 'message': 'فرمت فایل مجاز نیست.'}]
                    })

            user_profile = UserProfile.objects.get(user=request.user)
            current_group = user_profile.group

            # ایجاد گزارش شیفت
            shift_report = ShiftReport.objects.create(
                shift_date=timezone.now().date(),
                supervisor_comments=supervisor_comments,
                group=current_group,
                attached_file=attached_file if attached_file else None,
                creator = request.user.userprofile
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

    else:
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

        context = {
            'shifts': shifts,
            'personnels': personnels,
            'vehicles': vehicles,
            'current_shift': current_shift,
        }

        return render(request, 'OperationsShiftReports/create_shift_report.html', context)


from django.core.paginator import Paginator
from django.shortcuts import render
from .models import LoadingOperation
import jdatetime
from shift_manager.utils import get_shift_for_date, SHIFT_PATTERN  # اضافه کردن SHIFT_PATTERN


def get_day_name(date):
    """تبدیل روز هفته به فارسی برای تاریخ شمسی"""
    days = {
        5: 'پنج‌شنبه',
        4: 'چهارشنبه',
        3: 'سه‌شنبه',
        2: 'دوشنبه',
        1: 'یکشنبه',
        0: 'شنبه',
        6: 'جمعه'
    }
    # استفاده از weekday() تاریخ شمسی
    if isinstance(date, jdatetime.date):
        return days[date.weekday()]
    else:
        # تبدیل به تاریخ شمسی اگر میلادی باشد
        jalali_date = jdatetime.date.fromgregorian(date=date)
        return days[jalali_date.weekday()]


def get_shift_details(group, date):
    """دریافت جزئیات شیفت"""
    shifts = get_shift_for_date(date)
    shift_name = shifts.get(group, "نامشخص")

    # نمایش نوع شیفت (روزکار، عصرکار، شب‌کار)
    if 'روزکار' in shift_name:
        shift_type = 'روزکار'
    elif 'عصرکار' in shift_name:
        shift_type = 'عصرکار'
    elif 'شب کار' in shift_name:
        shift_type = 'شب‌کار'
    elif 'OFF' in shift_name:
        shift_type = 'استراحت'
    else:
        shift_type = 'نامشخص'

    # نمایش شماره شیفت (اول یا دوم)
    shift_number = 'اول' if 'اول' in shift_name else 'دوم'

    return {
        'shift_name': shift_name,  # نام کامل شیفت
        'shift_type': shift_type,  # نوع شیفت
        'shift_number': shift_number  # شماره شیفت
    }


def loading_operations_list(request):
    operations = LoadingOperation.objects.prefetch_related(
        'shift_reports',
        'shift_reports__creator__userprofile'  # اصلاح prefetch برای userprofile
    ).all().order_by('-id')

    for operation in operations:
        shift_reports = list(operation.shift_reports.all())
        if shift_reports:
            shift_report = shift_reports[0]
            jalali_date = jdatetime.date.fromgregorian(date=shift_report.shift_date)
            day_name = get_day_name(jalali_date)
            shift_details = get_shift_details(shift_report.group, shift_report.shift_date)

            # اطلاعات ایجاد کننده با استفاده از userprofile
            creator = shift_report.creator
            if creator:
                try:
                    creator_profile = creator.userprofile
                    creator_data = {
                        'full_name': creator.get_full_name() or creator.username,
                        'username': creator.username,
                        'personnel_code': creator_profile.personnel_code,
                        'group': creator_profile.get_group_display() if creator_profile.group else 'بدون گروه',
                        'image_url': creator_profile.image.url if creator_profile.image else None
                    }
                except UserProfile.DoesNotExist:
                    creator_data = {
                        'full_name': creator.get_full_name() or creator.username,
                        'username': creator.username,
                        'personnel_code': '',
                        'group': 'بدون گروه',
                        'image_url': None
                    }
            else:
                creator_data = {
                    'full_name': 'نامشخص',
                    'username': 'نامشخص',
                    'personnel_code': '',
                    'group': 'نامشخص',
                    'image_url': None
                }

            data = {
                'id': operation.id,
                'stone_type': operation.get_stone_type_display(),
                'load_count': operation.load_count,
                'jalali_date': jalali_date.strftime('%Y/%m/%d'),
                'day_name': day_name,
                'group': f"گروه {shift_report.group}",
                'shift_type': shift_details['shift_type'],
                'shift_number': shift_details['shift_number'],
                'shift_name': shift_details['shift_name'],
                'creator': creator_data
            }
        else:
            data = {
                'id': operation.id,
                'stone_type': operation.get_stone_type_display(),
                'load_count': operation.load_count,
                'jalali_date': 'نامشخص',
                'day_name': 'نامشخص',
                'group': 'نامشخص',
                'shift_type': 'نامشخص',
                'shift_number': 'نامشخص',
                'shift_name': 'نامشخص',
                 'creator': {
                    'full_name': 'نامشخص',
                    'username': 'نامشخص',
                    'avatar': None
                }
            }
        operations_data.append(data)



    paginator = Paginator(operations_data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'loading_operations': page_obj,
        'page_range': paginator.page_range,
    }

    return render(request, 'OperationsShiftReports/list.html', context)