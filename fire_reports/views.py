from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import FireReport, VehicleStatusReport
from .forms import FireReportForm, VehicleStatusFormSet
from shift_manager.utils import get_current_shift_and_group
from accounts.models import UserProfile
from django.conf import settings
from dashboard.models import Notification
from dashboard.sms_utils import send_template_sms
from permissions.utils import permission_required
from BaseInfo.models import EmergencyVehicle
from django.http import JsonResponse
import requests
import json
import logging
from django.contrib.auth.models import Group
from django.urls import reverse
from django.db import transaction
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
from PIL import Image, ImageChops, ImageFilter
from io import BytesIO
from django.core.files.base import ContentFile

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
    reports = FireReport.objects.all().order_by('-report_date')
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
        
        form = FireReportForm(post_data)
        formset = VehicleStatusFormSet(post_data, prefix='vehicles')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    report = form.save()
                    formset.instance = report
                    formset.save()
                    
                    # ارسال پیامک به متصدی شیفت
                    if hasattr(report.shift_operator, 'userprofile') and report.shift_operator.userprofile.mobile:
                        send_report_sms(
                            report.shift_operator.userprofile.mobile,
                            report.id,
                            'ثبت شده'
                        )

                messages.success(request, 'گزارش با موفقیت ثبت شد.')
                return redirect('fire_reports:report_detail', pk=report.pk)
            except Exception as e:
                logger.error(f"Error saving report: {e}")
                messages.error(request, 'خطا در ذخیره گزارش.')
                return redirect('fire_reports:report_create')
        else:
            logger.error(f"Form validation failed: {form.errors}")
            logger.error(f"Formset validation failed: {formset.errors}")
            messages.error(request, 'لطفاً تمام فیلدهای الزامی را پر کنید.')
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
        formset = VehicleStatusFormSet(prefix='vehicles')

    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'formset': formset,
        'title': 'ثبت گزارش جدید',
    })

@permission_required("report_detail")
@login_required
def fire_report_detail(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    return render(request, 'fire_reports/report_detail.html', {'report': report})

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
        formset = VehicleStatusFormSet(post_data, request.FILES, instance=report, prefix='vehicles')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                messages.success(request, 'گزارش با موفقیت بروزرسانی شد.')
                return redirect('fire_reports:report_detail', pk=report.pk)
            except Exception as e:
                logger.error(f"Error saving report: {e}")
                messages.error(request, f'خطا در ذخیره گزارش: {str(e)}')
        else:
            logger.error(f"Form errors: {form.errors}")
            logger.error(f"Formset errors: {formset.errors}")
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{form[field].label}: {error}")
            if formset.errors:
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        messages.error(request, f"خطا در خودرو #{i+1}")
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f"{field}: {error}")
    else:
        form = FireReportForm(instance=report, initial={
            'shift_operator': report.shift_operator.id,
            'firefighter': report.firefighter.id,
        })
        formset = VehicleStatusFormSet(instance=report, prefix='vehicles')
    
    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'formset': formset,
        'title': 'ویرایش گزارش'
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
    report = get_object_or_404(FireReport, pk=pk)
    
    # بررسی اینکه آیا کاربر متصدی شیفت آتش نشانی است
    try:
        user_profile = request.user.userprofile
        if not user_profile.position or user_profile.position.name != 'متصدی شیفت آتش نشانی':
            messages.error(request, 'شما مجاز به تأیید این گزارش نیستید.')
            return redirect('fire_reports:report_detail', pk=report.pk)
    except UserProfile.DoesNotExist:
        messages.error(request, 'پروفایل کاربری یافت نشد.')
        return redirect('fire_reports:report_detail', pk=report.pk)

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

            # ایجاد اعلان برای آتش‌نشان
            try:
                Notification.objects.create(
                    user=report.firefighter,
                    message=f"گزارش آتش‌ نشانی با شناسه {report.id} تأیید شد.",
                    url=reverse('fire_reports:report_detail', args=[report.id])
                )
                logger.info(f"Notification created for firefighter {report.firefighter.username}")
            except Exception as notif_error:
                logger.error(f"Error creating notification: {notif_error}")

            # ارسال اعلان به رئیس HSEC
            try:
                hsec_head = UserProfile.objects.filter(
                    position__name='رئیس HSEC'
                ).first()
                if hsec_head:
                    Notification.objects.create(
                        user=hsec_head.user,
                        message=f"گزارش آتش‌ نشانی با شناسه {report.id} تأیید شد.",
                        url=reverse('fire_reports:report_detail', args=[report.id])
                    )
                    logger.info(f"Notification created for HSEC head {hsec_head.user.username}")
                else:
                    logger.error("HSEC head not found.")
                    messages.error(request, "رئیس HSEC یافت نشد.")
            except Exception as hsec_error:
                logger.error(f"Error creating notification for HSEC head: {hsec_error}")

            messages.success(request, 'گزارش با موفقیت تأیید شد.')

        elif action == 'reject':
            if not rejection_reason:
                messages.error(request, 'لطفاً دلیل رد را وارد کنید.')
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

            # ایجاد اعلان برای آتش‌نشان
            try:
                Notification.objects.create(
                    user=report.firefighter,
                    message=f"گزارش آتش‌ نشانی با شناسه {report.id} رد شد. دلیل: {rejection_reason}",
                    url=reverse('fire_reports:report_detail', args=[report.id])
                )
                logger.info(f"Notification created for firefighter {report.firefighter.username}")
            except Exception as notif_error:
                logger.error(f"Error creating notification: {notif_error}")

            messages.success(request, 'گزارش رد شد.')

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
            firefighter_signature_no_bg = buffer.getvalue()

    if report.approval_status == 'approved' and report.shift_operator.userprofile.signature:
        img_no_bg = remove_background(report.shift_operator.userprofile.signature.path)
        if img_no_bg:
            buffer = BytesIO()
            img_no_bg.save(buffer, format='PNG')
            shift_operator_signature_no_bg = buffer.getvalue()

    # رندر کردن HTML
    html_content = template.render({
        'report': report,
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
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error getting vehicle info: {e}")
        return JsonResponse({'error': str(e)}, status=500)
