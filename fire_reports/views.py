from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import FireReport, VehicleChecklist
from .forms import FireReportForm
from shift_manager.utils import get_current_shift_and_group
from accounts.models import UserProfile
from django.conf import settings
from dashboard.sms_utils import send_template_sms
from permissions.utils import permission_required
from BaseInfo.models import EmergencyVehicle
from django.http import JsonResponse
import requests
import json
import logging
from django.urls import reverse
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
from PIL import Image, ImageChops, ImageFilter
from io import BytesIO
from django.core.files.base import ContentFile
import base64
from .notifications import (
    notify_fire_report_created,
    notify_fire_report_approval,
    notify_fire_report_rejection,
)

logger = logging.getLogger('fire_reports')

# تعریف شناسه قالب پیامک
SMS_TEMPLATE_ID = 410890  # قالب پیامک برای همه وضعیت‌ها

def send_report_sms(mobile, report_id, status):
    """
    ارسال پیامک با استفاده از قالب واحد
    """
    try:
        if mobile:
            parameters = [
                {"Name": "status", "Value": status},
                {"Name": "report_id", "Value": str(report_id)}
            ]
            send_template_sms(mobile, SMS_TEMPLATE_ID, parameters)
            logger.info(f"SMS sent to {mobile} for report {report_id} with status {status}")
    except Exception as e:
        logger.error(f"Error sending SMS for report {report_id}: {e}")

def remove_background(image_path, threshold=200):
    """
    حذف پس‌زمینه یک تصویر با استفاده از آستانه‌گذاری.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # ایجاد یک ماسک بر اساس آستانه
        alpha = img.split()[-1]
        alpha = alpha.filter(ImageFilter.GaussianBlur(2))  # Blur the mask slightly

        # Define a function to apply to each pixel
        def threshold_function(x):
            return 255 if x > threshold else 0

        alpha = alpha.point(threshold_function)

        # Convert to RGBA if it's not already
        if img.mode != 'RGBA':
            img = img.convert("RGBA")

        # Paste the image with the mask
        img.putalpha(alpha)

        return img
    except Exception as e:
        print(f"Error removing background: {e}")
        return None

@permission_required("report_list")
@login_required
def fire_report_list(request):
    logger.info("Accessing fire report list view")
    reports = FireReport.objects.select_related(
        'shift_operator', 'firefighter', 'company_vehicle', 'contractor_vehicle'
    ).prefetch_related(
        'vehicle_checklists__company_vehicle', 
        'vehicle_checklists__contractor_vehicle'
    ).all().order_by('-report_date')
    logger.info(f"Found {reports.count()} reports")
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    logger.info(f"Current page: {page_obj.number}, Total pages: {page_obj.paginator.num_pages}")
    return render(request, 'fire_reports/report_list.html', {'page_obj': page_obj})

@permission_required("report_create")
@login_required
def fire_report_create(request):
    if request.method == 'POST':
        logger.info("Received POST request for fire report creation")
        logger.info(f"POST data: {request.POST}")
        
        # دریافت شیفت کاری و گروه کاری فعلی
        current_shift, current_group = get_current_shift_and_group(request.user)
        logger.info(f"Current shift: {current_shift}, Current group: {current_group}")
        
        # یافتن متصدی شیفت آتش نشانی در گروه کاری فعلی
        try:
            shift_operator = UserProfile.objects.filter(
                group=current_group,
                position__name='متصدی شیفت آتش نشانی'
            ).first()
            if not shift_operator:
                logger.error(f"No shift operator found for group: {current_group}")
                messages.error(request, 'متصدی شیفت آتش نشانی برای گروه کاری شما یافت نشد.')
                return redirect('fire_reports:report_create')
            logger.info(f"Found shift operator: {shift_operator.user.username}")
        except Exception as e:
            logger.error(f"Error finding shift operator: {e}")
            messages.error(request, 'خطا در یافتن متصدی شیفت آتش نشانی.')
            return redirect('fire_reports:report_create')
        
        # اضافه کردن مقادیر اولیه به داده‌های POST
        post_data = request.POST.copy()
        post_data['shift_operator'] = shift_operator.user.id
        post_data['firefighter'] = request.user.id
        post_data['shift'] = current_shift
        
        # بررسی اینکه آیا از فرم جدید (چندین خودرو) استفاده شده است
        has_multiple_vehicles = any(key.startswith('vehicle_0_') for key in post_data.keys())
        
        # اگر از فرم جدید استفاده نشده، مقادیر پیش‌فرض را برای فیلدهای قدیمی تنظیم کن
        if not has_multiple_vehicles:
            # اگر هیچ vehicle_0_* وجود نداشته باشد، یعنی از فرم قدیمی استفاده شده
            # در این صورت فیلدهای قدیمی را الزامی می‌کنیم
            if 'vehicle_source' not in post_data:
                post_data['vehicle_source'] = 'company'
            if 'horn_status' not in post_data:
                post_data['horn_status'] = 'suitable'
            if 'hose_status' not in post_data:
                post_data['hose_status'] = 'suitable'
            if 'monitor_status' not in post_data:
                post_data['monitor_status'] = 'suitable'
            if 'extinguisher_status' not in post_data:
                post_data['extinguisher_status'] = 'suitable'
            if 'equipment_status' not in post_data:
                post_data['equipment_status'] = 'suitable'
            if 'foam_status' not in post_data:
                post_data['foam_status'] = 'suitable'
            if 'water_status' not in post_data:
                post_data['water_status'] = 'suitable'
            if 'tire_status' not in post_data:
                post_data['tire_status'] = 'suitable'
            if 'brake_status' not in post_data:
                post_data['brake_status'] = 'suitable'
            if 'lighting_status' not in post_data:
                post_data['lighting_status'] = 'suitable'
        else:
            # اگر از فرم جدید استفاده شده، فیلدهای قدیمی را اختیاری می‌کنیم
            # مقادیر پیش‌فرض را تنظیم می‌کنیم تا فرم اعتبارسنجی شود
            if 'vehicle_source' not in post_data:
                post_data['vehicle_source'] = ''
            if 'horn_status' not in post_data:
                post_data['horn_status'] = 'suitable'
            if 'hose_status' not in post_data:
                post_data['hose_status'] = 'suitable'
            if 'monitor_status' not in post_data:
                post_data['monitor_status'] = 'suitable'
            if 'extinguisher_status' not in post_data:
                post_data['extinguisher_status'] = 'suitable'
            if 'equipment_status' not in post_data:
                post_data['equipment_status'] = 'suitable'
            if 'foam_status' not in post_data:
                post_data['foam_status'] = 'suitable'
            if 'water_status' not in post_data:
                post_data['water_status'] = 'suitable'
            if 'tire_status' not in post_data:
                post_data['tire_status'] = 'suitable'
            if 'brake_status' not in post_data:
                post_data['brake_status'] = 'suitable'
            if 'lighting_status' not in post_data:
                post_data['lighting_status'] = 'suitable'
        
        form = FireReportForm(post_data)
        
        if form.is_valid():
            try:
                from django.db import transaction
                
                with transaction.atomic():
                    # اگر از فرم جدید استفاده شده، فیلدهای قدیمی را با مقادیر پیش‌فرض پر کن
                    if has_multiple_vehicles:
                        report = form.save(commit=False)
                        # تنظیم مقادیر پیش‌فرض برای فیلدهای الزامی مدل
                        if not report.vehicle_source:
                            report.vehicle_source = 'company'
                        if not report.horn_status:
                            report.horn_status = 'suitable'
                        if not report.hose_status:
                            report.hose_status = 'suitable'
                        if not report.monitor_status:
                            report.monitor_status = 'suitable'
                        if not report.extinguisher_status:
                            report.extinguisher_status = 'suitable'
                        if not report.equipment_status:
                            report.equipment_status = 'suitable'
                        if not report.foam_status:
                            report.foam_status = 'suitable'
                        if not report.water_status:
                            report.water_status = 'suitable'
                        if not report.tire_status:
                            report.tire_status = 'suitable'
                        if not report.brake_status:
                            report.brake_status = 'suitable'
                        if not report.lighting_status:
                            report.lighting_status = 'suitable'
                        report.save()
                    else:
                        report = form.save()
                    
                    # ذخیره چندین خودرو از فرم
                    vehicles_data = []
                    
                    # دریافت داده‌های خودروها از POST
                    # فرم چندین خودرو را به صورت vehicle_0_source, vehicle_0_company_vehicle, ... ارسال می‌کند
                    vehicle_index = 0
                    while True:
                        vehicle_source_key = f'vehicle_{vehicle_index}_source'
                        if vehicle_source_key not in post_data:
                            break
                        
                        vehicle_source = post_data.get(vehicle_source_key)
                        company_vehicle_id = post_data.get(f'vehicle_{vehicle_index}_company_vehicle')
                        contractor_vehicle_id = post_data.get(f'vehicle_{vehicle_index}_contractor_vehicle')
                        
                        if not vehicle_source or (not company_vehicle_id and not contractor_vehicle_id):
                            vehicle_index += 1
                            continue
                        
                        vehicle_data = {
                            'fire_report': report,
                            'vehicle_source': vehicle_source,
                            'company_vehicle_id': company_vehicle_id if vehicle_source == 'company' else None,
                            'contractor_vehicle_id': contractor_vehicle_id if vehicle_source == 'contractor' else None,
                            'statuses': {},
                            'descriptions': {}
                        }
                        
                        # دریافت وضعیت‌ها و توضیحات برای هر خودرو
                        checklist_items = [
                            'horn', 'hose', 'monitor', 'extinguisher', 'equipment',
                            'foam', 'water', 'tire', 'brake', 'lighting'
                        ]
                        
                        for item in checklist_items:
                            status_key = f'vehicle_{vehicle_index}_{item}_status'
                            desc_key = f'vehicle_{vehicle_index}_{item}_description'
                            
                            if status_key in post_data:
                                vehicle_data['statuses'][f'{item}_status'] = post_data.get(status_key, 'suitable')
                            if desc_key in post_data:
                                vehicle_data['descriptions'][f'{item}_description'] = post_data.get(desc_key, '')
                        
                        vehicles_data.append(vehicle_data)
                        vehicle_index += 1
                    
                    # اگر از فرم جدید استفاده شده ولی هیچ خودرویی ارسال نشده، خطا بده
                    if has_multiple_vehicles and not vehicles_data:
                        error_msg = 'لطفاً حداقل یک خودرو را انتخاب و چک‌لیست آن را تکمیل کنید.'
                        messages.error(request, error_msg)
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': False,
                                'message': error_msg
                            }, status=400)
                        
                        form = FireReportForm(post_data)
                        return render(request, 'fire_reports/report_form.html', {
                            'form': form,
                            'title': 'ثبت گزارش جدید'
                        })
                    
                    # اگر هیچ خودرویی از فرم جدید ارسال نشده، از فیلدهای قدیمی استفاده کن
                    if not vehicles_data:
                        # استفاده از فیلدهای قدیمی FireReport برای backward compatibility
                        if report.vehicle_source and (report.company_vehicle or report.contractor_vehicle):
                            vehicle_checklist = VehicleChecklist(
                                fire_report=report,
                                vehicle_source=report.vehicle_source,
                                company_vehicle=report.company_vehicle,
                                contractor_vehicle=report.contractor_vehicle,
                                horn_status=report.horn_status,
                                horn_description=report.horn_description,
                                hose_status=report.hose_status,
                                hose_description=report.hose_description,
                                monitor_status=report.monitor_status,
                                monitor_description=report.monitor_description,
                                extinguisher_status=report.extinguisher_status,
                                extinguisher_description=report.extinguisher_description,
                                equipment_status=report.equipment_status,
                                equipment_description=report.equipment_description,
                                foam_status=report.foam_status,
                                foam_description=report.foam_description,
                                water_status=report.water_status,
                                water_description=report.water_description,
                                tire_status=report.tire_status,
                                tire_description=report.tire_description,
                                brake_status=report.brake_status,
                                brake_description=report.brake_description,
                                lighting_status=report.lighting_status,
                                lighting_description=report.lighting_description,
                            )
                            vehicle_checklist.full_clean()
                            vehicle_checklist.save()
                    else:
                        # ذخیره چندین خودرو
                        for vehicle_data in vehicles_data:
                            vehicle_checklist = VehicleChecklist(
                                fire_report=vehicle_data['fire_report'],
                                vehicle_source=vehicle_data['vehicle_source'],
                                company_vehicle_id=vehicle_data['company_vehicle_id'],
                                contractor_vehicle_id=vehicle_data['contractor_vehicle_id'],
                            )
                            
                            # تنظیم وضعیت‌ها و توضیحات
                            for status_key, status_value in vehicle_data['statuses'].items():
                                setattr(vehicle_checklist, status_key, status_value)
                            for desc_key, desc_value in vehicle_data['descriptions'].items():
                                setattr(vehicle_checklist, desc_key, desc_value)
                            
                            vehicle_checklist.full_clean()
                            vehicle_checklist.save()
                    
                    # ارسال پیامک به متصدی شیفت
                    if hasattr(report.shift_operator, 'userprofile') and report.shift_operator.userprofile.mobile:
                        send_report_sms(
                            report.shift_operator.userprofile.mobile,
                            report.id,
                            'ثبت شده'
                        )

                messages.success(request, 'گزارش با موفقیت ثبت شد.')

                notify_fire_report_created(report, actor=request.user)

                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'گزارش با موفقیت ثبت شد.',
                        'redirect': reverse('fire_reports:report_detail', args=[report.pk]),
                        'report_id': report.pk
                    })
                
                return redirect('fire_reports:report_detail', pk=report.pk)
            except Exception as e:
                logger.error(f"Error saving report: {e}")
                error_msg = f'خطا در ذخیره گزارش: {str(e)}'
                messages.error(request, error_msg)
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    }, status=400)
        else:
            logger.error(f"Form validation failed: {form.errors}")
            error_msg = 'لطفاً تمام فیلدهای الزامی را پر کنید.'
            messages.error(request, error_msg)
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0] if error_list else ''
                return JsonResponse({
                    'success': False,
                    'message': error_msg,
                    'errors': errors
                }, status=400)
    else:
        # دریافت شیفت کاری و گروه کاری فعلی
        current_shift, current_group = get_current_shift_and_group(request.user)
        logger.info(f"Initializing form with shift: {current_shift}, group: {current_group}")
        
        # یافتن متصدی شیفت آتش نشانی در گروه کاری فعلی
        try:
            shift_operator = UserProfile.objects.filter(
                group=current_group,
                position__name='متصدی شیفت آتش نشانی'
            ).first()
            if not shift_operator:
                logger.error(f"No shift operator found for group: {current_group}")
                messages.error(request, 'متصدی شیفت آتش نشانی برای گروه کاری شما یافت نشد.')
                return redirect('fire_reports:report_list')
            logger.info(f"Found shift operator: {shift_operator.user.username}")
        except Exception as e:
            logger.error(f"Error finding shift operator: {e}")
            messages.error(request, 'خطا در یافتن متصدی شیفت آتش نشانی.')
            return redirect('fire_reports:report_list')
        
        form = FireReportForm(initial={
            'shift': current_shift,
            'shift_operator': shift_operator.user,
            'firefighter': request.user,
        })

    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'title': 'ثبت گزارش جدید',
    })

@permission_required("report_detail")
@login_required
def fire_report_detail(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    # دریافت تمام چک‌لیست‌های خودرو برای این گزارش
    vehicle_checklists = report.vehicle_checklists.all()
    return render(request, 'fire_reports/report_detail.html', {
        'report': report,
        'vehicle_checklists': vehicle_checklists
    })

@permission_required("report_edit")
@login_required
def fire_report_edit(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    
    # دریافت شیفت کاری و گروه کاری فعلی
    current_shift, current_group = get_current_shift_and_group(request.user)
    
    # یافتن متصدی شیفت آتش نشانی در گروه کاری فعلی
    try:
        shift_operator = UserProfile.objects.filter(
            group=current_group,
            position__name='متصدی شیفت آتش نشانی'
        ).first()
        if not shift_operator:
            messages.error(request, 'متصدی شیفت آتش نشانی برای گروه کاری شما یافت نشد.')
            return redirect('fire_reports:report_list')
    except Exception as e:
        messages.error(request, 'خطا در یافتن متصدی شیفت آتش نشانی.')
        return redirect('fire_reports:report_list')

    if request.method == 'POST':
        # اضافه کردن مقادیر اولیه به داده‌های POST
        post_data = request.POST.copy()
        post_data['shift_operator'] = report.shift_operator.id  # استفاده از متصدی شیفت موجود
        post_data['firefighter'] = report.firefighter.id  # استفاده از آتش‌نشان موجود
        
        form = FireReportForm(post_data, instance=report)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'گزارش با موفقیت بروزرسانی شد.')
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'گزارش با موفقیت بروزرسانی شد.',
                        'redirect': reverse('fire_reports:report_detail', args=[report.pk]),
                        'report_id': report.pk
                    })
                
                return redirect('fire_reports:report_detail', pk=report.pk)
            except Exception as e:
                logger.error(f"Error saving report: {e}")
                error_msg = f'خطا در ذخیره گزارش: {str(e)}'
                messages.error(request, error_msg)
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    }, status=400)
        else:
            logger.error(f"Form errors: {form.errors}")
            error_msg = 'لطفاً خطاهای فرم را برطرف کنید.'
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{form[field].label if hasattr(form[field], 'label') else field}: {error}")
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0] if error_list else ''
                return JsonResponse({
                    'success': False,
                    'message': error_msg,
                    'errors': errors
                }, status=400)
    else:
        form = FireReportForm(instance=report, initial={
            'shift_operator': report.shift_operator.id,
            'firefighter': report.firefighter.id,
        })
    
    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'title': 'ویرایش گزارش',
        'report': report,
    })

@permission_required("report_delete")
@login_required
def fire_report_delete(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'گزارش با موفقیت حذف شد.')
        return redirect('fire_reports:report_list')
    return render(request, 'fire_reports/report_confirm_delete.html', {'report': report})

@permission_required("report_approve")
@login_required
def fire_report_approve(request, pk):
    """
    ویو تأیید/رد گزارش آتش‌نشانی
    کاربران با permission 'report_approve' می‌توانند گزارش را تأیید یا رد کنند.
    """
    report = get_object_or_404(FireReport, pk=pk)
    
    # @permission_required("report_approve") قبلاً بررسی کرده که کاربر مجاز است
    # نیازی به بررسی position اضافی نیست - اگر permission داشته باشد، مجاز است

    if request.method == 'POST':
        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason')

        if action == 'approve':
            report.approval_status = 'approved'
            report.approved_by = request.user
            report.approval_date = timezone.now()
            report.save()

            # ارسال پیامک به آتش‌نشان
            if hasattr(report.firefighter, 'userprofile') and report.firefighter.userprofile.mobile:
                send_report_sms(
                    report.firefighter.userprofile.mobile,
                    report.id,
                    'تأیید شده'
                )

            notify_fire_report_approval(report, actor=request.user)

            messages.success(request, 'گزارش با موفقیت تأیید شد.')
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'گزارش با موفقیت تأیید شد.',
                    'redirect': reverse('fire_reports:report_detail', args=[report.pk])
                })

        elif action == 'reject':
            if not rejection_reason:
                error_msg = 'لطفاً دلیل رد را وارد کنید.'
                messages.error(request, error_msg)
                
                # Handle AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    }, status=400)
                
                return render(request, 'fire_reports/report_approve.html', {'report': report})
            
            report.approval_status = 'rejected'
            report.rejection_reason = rejection_reason
            report.save()

            # ارسال پیامک به آتش‌نشان
            if hasattr(report.firefighter, 'userprofile') and report.firefighter.userprofile.mobile:
                send_report_sms(
                    report.firefighter.userprofile.mobile,
                    report.id,
                    'رد شده'
                )

            notify_fire_report_rejection(report, reason=rejection_reason, actor=request.user)

            messages.success(request, 'گزارش رد شد.')
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'گزارش رد شد.',
                    'redirect': reverse('fire_reports:report_detail', args=[report.pk])
                })

        return redirect('fire_reports:report_detail', pk=report.pk)

    return render(request, 'fire_reports/report_approve.html', {'report': report})

@permission_required("report_pdf")
@login_required
def fire_report_pdf(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    template = get_template('fire_reports/report_pdf.html')

    # ایجاد مسیر کامل فایل‌های استاتیک و مدیا
    static_url = request.build_absolute_uri(settings.STATIC_URL)
    media_url = request.build_absolute_uri(settings.MEDIA_URL)
    print(f"Media URL: {media_url}")  # اضافه کردن این خط برای بررسی مقدار media_url

    # حذف پس‌زمینه تصاویر امضا
    firefighter_signature_no_bg = None
    shift_operator_signature_no_bg = None

    if report.firefighter.userprofile.signature:
        img_no_bg = remove_background(report.firefighter.userprofile.signature.path)
        if img_no_bg:
            buffer = BytesIO()
            img_no_bg.save(buffer, format='PNG')
            firefighter_signature_no_bg = base64.b64encode(buffer.getvalue()).decode('utf-8')

    if report.approval_status == 'approved' and report.shift_operator.userprofile.signature:
        img_no_bg = remove_background(report.shift_operator.userprofile.signature.path)
        if img_no_bg:
            buffer = BytesIO()
            img_no_bg.save(buffer, format='PNG')
            shift_operator_signature_no_bg = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # دریافت تمام چک‌لیست‌های خودرو برای این گزارش
    vehicle_checklists = report.vehicle_checklists.all()
    
    # رندر کردن HTML
    html_content = template.render({
        'report': report,
        'vehicle_checklists': vehicle_checklists,
        'title': 'گزارش آتش‌نشانی',
        'static_url': static_url,
        'media_url': media_url,
        'firefighter_signature_no_bg': firefighter_signature_no_bg,
        'shift_operator_signature_no_bg': shift_operator_signature_no_bg,
    }, request)

    # ایجاد فایل PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="fire_report_{pk}.pdf"'

    # اضافه کردن base_url برای دسترسی به فایل‌های رسانه‌ای
    HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(response)

    return response

@login_required
def get_vehicle_info(request, vehicle_id):
    """API endpoint برای دریافت اطلاعات خودرو"""
    try:
        vehicle_type = request.GET.get('type', 'company')  # company or contractor
        
        if vehicle_type == 'company':
            vehicle = get_object_or_404(EmergencyVehicle, id=vehicle_id)
            data = {
                'has_horn': vehicle.has_horn,
                'has_hose': vehicle.has_hose,
                'has_monitor': vehicle.has_monitor,
                'has_extinguisher': vehicle.has_extinguisher,
                'has_equipment': vehicle.has_equipment,
                'has_foam': vehicle.has_foam,
                'has_water': vehicle.has_water,
                'has_tire': vehicle.has_tire,
                'has_brake': vehicle.has_brake,
                'has_lighting': vehicle.has_lighting,
            }
        else:  # contractor vehicle - all equipment available by default
            from contractor_management.models import Vehicle as ContractorVehicle
            vehicle = get_object_or_404(ContractorVehicle, id=vehicle_id)
            # For contractor vehicles, assume all equipment is available
            data = {
                'has_horn': True,
                'has_hose': True,
                'has_monitor': True,
                'has_extinguisher': True,
                'has_equipment': True,
                'has_foam': True,
                'has_water': True,
                'has_tire': True,
                'has_brake': True,
                'has_lighting': True,
            }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting vehicle info: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_contractor_vehicles_ajax(request):
    """API endpoint برای دریافت لیست خودروهای پیمانکار آتش‌نشانی"""
    try:
        from contractor_management.models import Vehicle as ContractorVehicle
        vehicles = ContractorVehicle.objects.filter(
            contractor__company_name__icontains='آتش نشانی'
        ).values('id', 'driver_name', 'license_plate', 'contractor__company_name')
        vehicle_list = [
            {
                'id': v['id'],
                'text': f"{v['driver_name']} ({v['license_plate']}) - {v['contractor__company_name']}"
            } for v in vehicles
        ]
        return JsonResponse(vehicle_list, safe=False)
    except Exception as e:
        logger.error(f"Error getting contractor vehicles: {e}")
        return JsonResponse({'error': str(e)}, status=500)
