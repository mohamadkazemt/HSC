from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import FireReport
from .forms import FireReportForm
from shift_manager.utils import get_current_shift_and_group
from accounts.models import UserProfile
from django.conf import settings
from dashboard.models import Notification
from dashboard.sms_utils import send_template_sms
import requests
import json
import logging
from django.contrib.auth.models import Group
from django.urls import reverse

logger = logging.getLogger('fire_reports')

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
        
        # تنظیم مقادیر پیش‌فرض برای فیلدهای تعداد حوادث
        if 'incident_dispatch_count' not in post_data:
            post_data['incident_dispatch_count'] = '0'
        if 'personal_incident_count' not in post_data:
            post_data['personal_incident_count'] = '0'
        if 'equipment_incident_count' not in post_data:
            post_data['equipment_incident_count'] = '0'
        if 'fire_incident_count' not in post_data:
            post_data['fire_incident_count'] = '0'
        
        logger.info(f"Modified POST data: {post_data}")
        
        form = FireReportForm(post_data)
        if form.is_valid():
            logger.info("Form is valid")
            report = form.save(commit=False)
            report.shift = current_shift
            report.shift_operator = shift_operator.user
            report.firefighter = request.user
            logger.info(f"Setting firefighter to: {request.user.username}")

            # پاک کردن توضیحات برای فیلدهایی که چک‌باکس آنها تیک نخورده است
            if not form.cleaned_data.get('show_horn_description'):
                report.horn_description = None
            if not form.cleaned_data.get('show_hose_description'):
                report.hose_description = None
            if not form.cleaned_data.get('show_monitor_description'):
                report.monitor_description = None
            if not form.cleaned_data.get('show_extinguisher_description'):
                report.extinguisher_description = None
            if not form.cleaned_data.get('show_equipment_description'):
                report.equipment_description = None
            if not form.cleaned_data.get('show_foam_description'):
                report.foam_description = None
            if not form.cleaned_data.get('show_water_description'):
                report.water_description = None
            if not form.cleaned_data.get('show_tire_description'):
                report.tire_description = None
            if not form.cleaned_data.get('show_brake_description'):
                report.brake_description = None
            if not form.cleaned_data.get('show_lighting_description'):
                report.lighting_description = None

            try:
                report.save()
                logger.info(f"Report saved successfully with ID: {report.id}")
                logger.info(f"Report data: shift={report.shift}, operator={report.shift_operator.username}, firefighter={report.firefighter.username}")
                logger.info(f"Report incidents: dispatch={report.incident_dispatch_count}, personal={report.personal_incident_count}, equipment={report.equipment_incident_count}, fire={report.fire_incident_count}")

                # ارسال پیامک به متصدی شیفت
                if hasattr(report.shift_operator, 'userprofile') and report.shift_operator.userprofile.mobile:
                    send_template_sms(
                        report.shift_operator.userprofile.mobile, 
                        684430, 
                        [
                            {"Name": "status", "Value": "ثبت شده"},
                            {"Name": "report_id", "Value": str(report.id)}
                        ]
                    )
                    logger.info(f"SMS sent to shift operator: {report.shift_operator.userprofile.mobile}")

                messages.success(request, 'گزارش با موفقیت ثبت شد.')
                return redirect('fire_reports:report_detail', pk=report.pk)
            except Exception as e:
                logger.error(f"Error saving report: {e}")
                messages.error(request, 'خطا در ذخیره گزارش.')
                return redirect('fire_reports:report_create')
        else:
            logger.error(f"Form validation failed: {form.errors}")
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

    # تنظیم فیلدهای تجهیزات برای قالب
    equipment_fields = {
        'horn': {
            'label': 'وضعیت بوق و چراغ گردان',
            'status': form['horn_status'],
            'show_description': form['show_horn_description'],
            'description': form['horn_description'],
            'help_text': 'وضعیت بوق و چراغ گردان خودرو را مشخص کنید'
        },
        'hose': {
            'label': 'وضعیت شیلنگ‌ها و اتصالات',
            'status': form['hose_status'],
            'show_description': form['show_hose_description'],
            'description': form['hose_description'],
            'help_text': 'وضعیت شیلنگ‌ها و اتصالات را مشخص کنید'
        },
        'monitor': {
            'label': 'وضعیت مانیتور',
            'status': form['monitor_status'],
            'show_description': form['show_monitor_description'],
            'description': form['monitor_description'],
            'help_text': 'وضعیت مانیتور را مشخص کنید'
        },
        'extinguisher': {
            'label': 'وضعیت خاموش‌کننده‌های دستی',
            'status': form['extinguisher_status'],
            'show_description': form['show_extinguisher_description'],
            'description': form['extinguisher_description'],
            'help_text': 'وضعیت خاموش‌کننده‌های دستی را مشخص کنید'
        },
        'equipment': {
            'label': 'وضعیت تجهیزات آتش‌نشانی',
            'status': form['equipment_status'],
            'show_description': form['show_equipment_description'],
            'description': form['equipment_description'],
            'help_text': 'وضعیت تجهیزات آتش‌نشانی را مشخص کنید'
        },
        'foam': {
            'label': 'وضعیت پودر و فوم',
            'status': form['foam_status'],
            'show_description': form['show_foam_description'],
            'description': form['foam_description'],
            'help_text': 'وضعیت پودر و فوم را مشخص کنید'
        },
        'water': {
            'label': 'وضعیت آب',
            'status': form['water_status'],
            'show_description': form['show_water_description'],
            'description': form['water_description'],
            'help_text': 'وضعیت آب را مشخص کنید'
        },
        'tire': {
            'label': 'وضعیت لاستیک‌ها',
            'status': form['tire_status'],
            'show_description': form['show_tire_description'],
            'description': form['tire_description'],
            'help_text': 'وضعیت لاستیک‌ها را مشخص کنید'
        },
        'brake': {
            'label': 'وضعیت سیستم ترمز',
            'status': form['brake_status'],
            'show_description': form['show_brake_description'],
            'description': form['brake_description'],
            'help_text': 'وضعیت سیستم ترمز را مشخص کنید'
        },
        'lighting': {
            'label': 'وضعیت سیستم روشنایی',
            'status': form['lighting_status'],
            'show_description': form['show_lighting_description'],
            'description': form['lighting_description'],
            'help_text': 'وضعیت سیستم روشنایی را مشخص کنید'
        }
    }

    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'title': 'ثبت گزارش جدید',
        'equipment_fields': equipment_fields
    })

@login_required
def fire_report_detail(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    return render(request, 'fire_reports/report_detail.html', {'report': report})

@login_required
def fire_report_edit(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    if request.method == 'POST':
        form = FireReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'گزارش با موفقیت بروزرسانی شد.')
            return redirect('fire_reports:report_detail', pk=report.pk)
    else:
        form = FireReportForm(instance=report)
    return render(request, 'fire_reports/report_form.html', {'form': form, 'title': 'ویرایش گزارش'})

@login_required
def fire_report_delete(request, pk):
    report = get_object_or_404(FireReport, pk=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'گزارش با موفقیت حذف شد.')
        return redirect('fire_reports:report_list')
    return render(request, 'fire_reports/report_confirm_delete.html', {'report': report})

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
            try:
                if hasattr(report.firefighter, 'userprofile') and report.firefighter.userprofile.mobile:
                    send_template_sms(
                        report.firefighter.userprofile.mobile, 
                        684430, 
                        [
                            {"Name": "status", "Value": "تأیید شده"},
                            {"Name": "report_id", "Value": str(report.id)}
                        ]
                    )
                    logger.info(f"SMS sent to {report.firefighter.userprofile.mobile} for report {report.id}")
            except Exception as sms_error:
                logger.error(f"Error while sending SMS for report {report.id}: {sms_error}")

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
            try:
                if hasattr(report.firefighter, 'userprofile') and report.firefighter.userprofile.mobile:
                    send_template_sms(
                        report.firefighter.userprofile.mobile, 
                        320925, 
                        [
                            {"Name": "status", "Value": "رد شده"},
                            {"Name": "report_id", "Value": str(report.id)}
                        ]
                    )
                    logger.info(f"SMS sent to {report.firefighter.userprofile.mobile} for report {report.id}")
            except Exception as sms_error:
                logger.error(f"Error while sending SMS for report {report.id}: {sms_error}")

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
