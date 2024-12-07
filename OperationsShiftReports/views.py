from django.core.paginator import Paginator
import jdatetime
import json
from django.db.models import Sum
from shift_manager.utils import get_shift_for_date, SHIFT_PATTERN
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.utils import timezone
from accounts.models import UserProfile
from BaseInfo.models import  MiningMachine, MiningBlock, MachineryWorkGroup, TypeMachine
from .models import (
    ShiftReport,
    LoadingOperation,
    VehicleReport,
    LoaderStatus
)
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .permissions import operations_required
from django.contrib.auth.decorators import login_required

def convert_to_persian_day(date):
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






@login_required
def create_shift_report(request):
    if request.method == "POST":
        try:
            # دریافت توضیحات سرشیفت
            supervisor_comments = request.POST.get('supervisor_comments', '').strip()
            if not supervisor_comments:
                return JsonResponse({'messages': [{'tags': 'error', 'message': 'توضیحات سرشیفت الزامی است.'}]})

            # دریافت داده‌های جدول بارکننده‌ها
            loader_statuses = json.loads(request.POST.get('loader_statuses', '[]'))
            if not loader_statuses:
                return JsonResponse({'messages': [{'tags': 'error', 'message': 'داده‌های بارکننده‌ها خالی است.'}]})

            # بررسی پروفایل کاربری
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                current_group = user_profile.group
            except UserProfile.DoesNotExist:
                return JsonResponse({'messages': [{'tags': 'error', 'message': 'پروفایل کاربری یافت نشد.'}]})

            # ایجاد گزارش شیفت
            shift_report = ShiftReport.objects.create(
                shift_date=timezone.now().date(),
                supervisor_comments=supervisor_comments,
                group=current_group,
                creator=user_profile
            )

            # ذخیره وضعیت بارکننده‌ها
            for loader_data in loader_statuses:
                loader_id, block_id, status, inactive_reason = loader_data.split(',')
                try:
                    loader = MiningMachine.objects.get(id=int(loader_id), is_active=True)
                    block = MiningBlock.objects.get(id=int(block_id))
                except (MiningMachine.DoesNotExist, MiningBlock.DoesNotExist):
                    return JsonResponse({'messages': [{'tags': 'error', 'message': 'بارکننده یا بلوک معتبر نیست.'}]})

                LoaderStatus.objects.create(
                    loader=loader,
                    block=block,
                    status=status,
                    inactive_reason=inactive_reason if status == 'inactive' else None
                )

            return JsonResponse({'messages': [{'tags': 'success', 'message': 'گزارش با موفقیت ثبت شد.'}]})

        except Exception as e:
            return JsonResponse({'messages': [{'tags': 'error', 'message': f'خطا در ثبت گزارش: {str(e)}'}]})

    else:  # درخواست GET
        today = timezone.now().date()

        # بازیابی شیفت‌های مرتبط
        shifts = get_shift_for_date(today)
        current_group = None
        current_shift = None

        if request.user.is_authenticated:
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                current_group = user_profile.group
                current_shift = shifts.get(current_group)
            except UserProfile.DoesNotExist:
                pass

        # دریافت لیست پرسنل گروه
        personnels = UserProfile.objects.filter(group=current_group) if current_group else UserProfile.objects.none()

        # فیلتر بارکننده‌ها
        try:
            loader_workgroup = MachineryWorkGroup.objects.get(name="بارکننده")
            type_machines = TypeMachine.objects.filter(machine_workgroup=loader_workgroup)
            mining_machines = MiningMachine.objects.filter(machine_type__in=type_machines, is_active=True)
        except MachineryWorkGroup.DoesNotExist:
            mining_machines = MiningMachine.objects.none()

        # دریافت بلوک‌های فعال و در حال بارگیری
        mining_blocks = MiningBlock.objects.filter(is_active=True, status='loading')

        context = {
            'shifts': shifts,
            'current_shift': current_shift,
            'mining_machines': mining_machines,  # دستگاه‌های بارکننده فعال
            'mining_blocks': mining_blocks,      # بلوک‌های فعال
        }

        return render(request, 'OperationsShiftReports/create_shift_report.html', context)





@login_required
@operations_required
def loading_operations_list(request):
    operations = LoadingOperation.objects.prefetch_related(
        'shift_reports',
        'shift_reports__creator',
        'shift_reports__creator__user'
    ).all().order_by('-id')

    operations_data = []

    for operation in operations:
        shift_reports = list(operation.shift_reports.all())
        if shift_reports:
            shift_report = shift_reports[0]
            jalali_date = jdatetime.date.fromgregorian(date=shift_report.shift_date)
            day_name = convert_to_persian_day(jalali_date)  # اینجا نام تابع تغییر کرد
            shift_details = get_shift_details(shift_report.group, shift_report.shift_date)

            creator = shift_report.creator
            if creator:
                # ساخت نام کامل با اولویت نام و نام خانوادگی
                first_name = creator.user.first_name.strip()
                last_name = creator.user.last_name.strip()

                if first_name and last_name:
                    display_name = f"{first_name} {last_name}"
                elif first_name:
                    display_name = first_name
                elif last_name:
                    display_name = last_name
                else:
                    display_name = creator.user.username

                creator_data = {
                    'full_name': display_name,
                    'display_name': display_name,
                    'username': creator.user.username,
                    'personnel_code': creator.personnel_code,
                    'group': creator.get_group_display() if creator.group else 'بدون گروه',
                    'image_url': creator.image.url if creator.image else None,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            else:
                creator_data = {
                    'full_name': 'نامشخص',
                    'display_name': 'نامشخص',
                    'username': 'نامشخص',
                    'personnel_code': '',
                    'group': 'نامشخص',
                    'image_url': None,
                    'first_name': '',
                    'last_name': ''
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
                    'display_name': 'نامشخص',
                    'username': 'نامشخص',
                    'personnel_code': '',
                    'group': 'نامشخص',
                    'image_url': None,
                    'first_name': '',
                    'last_name': ''
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


@login_required
@operations_required
def operation_detail(request, pk):
    operation = get_object_or_404(LoadingOperation, id=pk)

    # Get the shift report that contains this operation
    shift_report = ShiftReport.objects.select_related(
        'creator',
        'creator__user'
    ).prefetch_related(
        'loader_statuses',
        'loader_statuses__loader',
        'loader_statuses__block',
        'shift_leaves',
        'shift_leaves__personnel_name',
        'shift_leaves__personnel_name__user',
        'vehicle_reports',
        'loading_operations'
    ).filter(
        loading_operations=operation
    ).first()

    if not shift_report:
        raise Http404("No shift report found for this operation")

    # محاسبه مجموع بارها به تفکیک نوع سنگ
    loading_summary = {
        'total': 0,
        'details': []
    }

    for op in shift_report.loading_operations.all():
        loading_summary['total'] += op.load_count
        loading_summary['details'].append({
            'stone_type': op.get_stone_type_display(),
            'load_count': op.load_count
        })

    # تبدیل تاریخ میلادی به شمسی
    jalali_date = jdatetime.date.fromgregorian(date=shift_report.shift_date)

    # دریافت اطلاعات شیفت
    shift_details = get_shift_details(shift_report.group, shift_report.shift_date)

    # پردازش اطلاعات فایل پیوست
    file_info = None
    if shift_report.attached_file:
        try:
            # بررسی وجود فیزیکی فایل
            if default_storage.exists(shift_report.attached_file.name):
                filename = os.path.basename(shift_report.attached_file.name)
                file_extension = os.path.splitext(filename)[1].lower()
                file_size = default_storage.size(shift_report.attached_file.name)

                # تعیین نوع فایل
                is_image = file_extension in ['.jpg', '.jpeg', '.png']
                is_pdf = file_extension == '.pdf'
                is_doc = file_extension in ['.doc', '.docx']

                # محاسبه حجم فایل
                if file_size < 1000000:  # کمتر از 1MB
                    formatted_size = f"{file_size / 1024:.1f} KB"
                else:
                    formatted_size = f"{file_size / 1048576:.1f} MB"

                file_info = {
                    'name': filename,
                    'size': formatted_size,
                    'url': shift_report.attached_file.url,
                    'is_image': is_image,
                    'is_pdf': is_pdf,
                    'is_doc': is_doc
                }
        except Exception as e:
            # در صورت بروز خطا، اطلاعات فایل را نادیده می‌گیریم
            file_info = None

    context = {
        'operation': operation,
        'shift_report': shift_report,
        'jalali_date': jalali_date.strftime('%Y/%m/%d'),
        'shift_type': shift_details['shift_type'],
        'loading_summary': loading_summary,
        'file_info': file_info  # اضافه کردن اطلاعات فایل به context
    }

    return render(request, 'OperationsShiftReports/operation_detail.html', context)