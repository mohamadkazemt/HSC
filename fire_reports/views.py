from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import FireReport, VehicleStatusReport
from .forms import FireReportForm, VehicleStatusFormSet
from shift_manager.utils import get_current_shift_and_group
from accounts.models import UserProfile
from django.contrib.auth import get_user_model
from django.conf import settings
from dashboard.models import Notification
from dashboard.sms_utils import send_template_sms
from permissions.utils import permission_required
from BaseInfo.models import EmergencyVehicle
from contractor_management.models import Vehicle as ContractorVehicle
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

User = get_user_model()

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
        
        # Build filtered user querysets according to UnitGroup name and Position
        operator_qs = User.objects.filter(
            userprofile__unit_group__name='آتش نشانی',
            userprofile__position__name='متصدی شیفت آتش نشانی',
            is_active=True
        ).select_related('userprofile').order_by('userprofile__personnel_code', 'first_name', 'last_name')

        firefighter_qs = User.objects.filter(
            userprofile__unit_group__name='آتش نشانی',
            is_active=True
        ).select_related('userprofile').order_by('userprofile__personnel_code', 'first_name', 'last_name')

        if not firefighter_qs.exists():
            messages.error(request, 'هیچ آتش‌نشان فعالی در گروه آتش نشانی یافت نشد.')
            return redirect('fire_reports:report_list')

        if not operator_qs.exists():
            messages.error(request, 'متصدی شیفت آتش نشانی برای گروه آتش نشانی یافت نشد.')
            return redirect('fire_reports:report_list')

        # Prepare POST data defaults (ensure required hidden fields exist)
        post_data = request.POST.copy()
        # If client didn't post a shift_operator or firefighter, set sensible defaults
        post_data.setdefault('shift_operator', operator_qs.first().id)
        post_data.setdefault('firefighter', request.user.id)
        post_data.setdefault('shift', current_shift)

        # pass filtered querysets into the form so dropdowns are populated
        form = FireReportForm(post_data, firefighter_queryset=firefighter_qs, operator_queryset=operator_qs)
        
        # Query company and contractor vehicles so template dropdowns are populated
        try:
            # EmergencyVehicle uses `status` field with values like 'active'/'inactive'
            company_vehicles = EmergencyVehicle.objects.filter(status='active').order_by('model', 'license_plate')
        except Exception:
            company_vehicles = EmergencyVehicle.objects.all()
        try:
            # Contractor Vehicle model doesn't have `is_active`; return all contractor vehicles
            contractor_vehicles = ContractorVehicle.objects.select_related('contractor').order_by('license_plate')
        except Exception:
            contractor_vehicles = ContractorVehicle.objects.all()

        form_kwargs = {
            'company_vehicles_queryset': company_vehicles,
            'contractor_vehicles_queryset': contractor_vehicles,
        }
        formset = VehicleStatusFormSet(post_data, prefix='vehicles', form_kwargs=form_kwargs)

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

        # Prepare formset data for JS even in POST (so template's JSON.parse won't fail)
        formset_data = []
        try:
            for f in formset.forms:
                vehicle_data = {
                    'id': getattr(f.instance, 'id', '') or '',
                    'DELETE': False,
                    'vehicle_source': getattr(f.instance, 'vehicle_source', 'company') or 'company',
                    'company_vehicle': getattr(getattr(f.instance, 'company_vehicle', None), 'id', '') or '',
                    'contractor_vehicle': getattr(getattr(f.instance, 'contractor_vehicle', None), 'id', '') or ''
                }
                formset_data.append(vehicle_data)
        except Exception:
            formset_data = []
    else:
        # دریافت شیفت کاری و گروه کاری فعلی
        current_shift, current_group = get_current_shift_and_group(request.user)
        logger.info(f"Initializing form with shift: {current_shift}, group: {current_group}")
        
        # Build filtered user querysets for the GET form as well
        operator_qs = User.objects.filter(
            userprofile__unit_group__name='آتش نشانی',
            userprofile__position__name='متصدی شیفت آتش نشانی',
            is_active=True
        ).select_related('userprofile').order_by('userprofile__personnel_code', 'first_name', 'last_name')

        firefighter_qs = User.objects.filter(
            userprofile__unit_group__name='آتش نشانی',
            is_active=True
        ).select_related('userprofile').order_by('userprofile__personnel_code', 'first_name', 'last_name')

        if not firefighter_qs.exists():
            messages.error(request, 'هیچ آتش‌نشان فعالی در گروه آتش نشانی یافت نشد.')
            return redirect('fire_reports:report_list')

        if not operator_qs.exists():
            messages.error(request, 'متصدی شیفت آتش نشانی برای گروه آتش نشانی یافت نشد.')
            return redirect('fire_reports:report_list')

        # For a better UX, pre-select a shift operator if available
        shift_operator = operator_qs.first()

        form = FireReportForm(initial={
            'shift': current_shift,
            'shift_operator': shift_operator,
            'firefighter': request.user,
        }, firefighter_queryset=firefighter_qs, operator_queryset=operator_qs)
        
        # Query vehicles for GET so dropdowns show options
        try:
            company_vehicles = EmergencyVehicle.objects.filter(status='active').order_by('model', 'license_plate')
        except Exception:
            company_vehicles = EmergencyVehicle.objects.all()
        try:
            contractor_vehicles = ContractorVehicle.objects.select_related('contractor').order_by('license_plate')
        except Exception:
            contractor_vehicles = ContractorVehicle.objects.all()

        form_kwargs = {
            'company_vehicles_queryset': company_vehicles,
            'contractor_vehicles_queryset': contractor_vehicles,
        }
        formset = VehicleStatusFormSet(prefix='vehicles', form_kwargs=form_kwargs)

        # Prepare formset data for JavaScript
        formset_data = []
        for f in formset.forms:
            vehicle_data = {
                'id': getattr(f.instance, 'id', '') or '',
                'DELETE': False,
                'vehicle_source': getattr(f.instance, 'vehicle_source', 'company') or 'company',
                'company_vehicle': getattr(getattr(f.instance, 'company_vehicle', None), 'id', '') or '',
                'contractor_vehicle': getattr(getattr(f.instance, 'contractor_vehicle', None), 'id', '') or ''
            }
            formset_data.append(vehicle_data)

    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'formset': formset,
        'formset_data': json.dumps(formset_data),
        'user_select_options': json.dumps({
            'operator': [{ 'id': u.id, 'text': f"{u.get_full_name()} ({getattr(getattr(u, 'userprofile', None), 'personnel_code', '')})" } for u in operator_qs],
            'firefighter': [{ 'id': u.id, 'text': f"{u.get_full_name()} ({getattr(getattr(u, 'userprofile', None), 'personnel_code', '')})" } for u in firefighter_qs]
        }, ensure_ascii=False),
        'title': 'ثبت گزارش جدید',
        'company_vehicles': company_vehicles,
        'contractor_vehicles': contractor_vehicles,
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

    # Always prepare the filtered querysets up-front so forms always get them
    operator_qs = User.objects.filter(
        userprofile__unit_group__name='آتش نشانی',
        userprofile__position__name='متصدی شیفت آتش نشانی',
        is_active=True
    ).select_related('userprofile').order_by('userprofile__personnel_code', 'first_name', 'last_name')

    firefighter_qs = User.objects.filter(
        userprofile__unit_group__name='آتش نشانی',
        is_active=True
    ).select_related('userprofile').order_by('userprofile__personnel_code', 'first_name', 'last_name')

    # Query company and contractor vehicles once so templates can render dropdowns
    try:
        company_vehicles = EmergencyVehicle.objects.filter(status='active').order_by('model', 'license_plate')
    except Exception:
        company_vehicles = EmergencyVehicle.objects.all()
    try:
        contractor_vehicles = ContractorVehicle.objects.select_related('contractor').order_by('license_plate')
    except Exception:
        contractor_vehicles = ContractorVehicle.objects.all()

    # Basic availability checks (redirects if no users found)
    if not firefighter_qs.exists():
        messages.error(request, 'هیچ آتش‌نشان فعالی در گروه آتش نشانی یافت نشد.')
        return redirect('fire_reports:report_list')

    if not operator_qs.exists():
        messages.error(request, 'متصدی شیفت آتش نشانی برای گروه آتش نشانی یافت نشد.')
        return redirect('fire_reports:report_list')

    if request.method == 'POST':
        # Copy POST data to allow modifications
        post_data = request.POST.copy()

        # Ensure shift_operator/firefighter fields exist in POST so form validation
        # doesn't fail due to missing keys; prefer existing report values.
        try:
            post_data.setdefault('shift_operator', getattr(report.shift_operator, 'id', ''))
        except Exception:
            post_data.setdefault('shift_operator', '')
        try:
            post_data.setdefault('firefighter', getattr(report.firefighter, 'id', ''))
        except Exception:
            post_data.setdefault('firefighter', '')

        form = FireReportForm(post_data, instance=report, firefighter_queryset=firefighter_qs, operator_queryset=operator_qs)
        
        form_kwargs = {
            'company_vehicles_queryset': company_vehicles,
            'contractor_vehicles_queryset': contractor_vehicles,
        }
        formset = VehicleStatusFormSet(post_data, request.FILES, instance=report, prefix='vehicles', form_kwargs=form_kwargs)

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
            # Collect and show validation errors, but do not bail out — we need to
            # re-render the form with the same bound form/formset so the user can fix them.
            logger.error(f"Form errors: {form.errors}")
            logger.error(f"Formset errors: {formset.errors}")
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        # Some form fields may not be in form.fields (custom handling) — guard access
                        label = form[field].label if field in form.fields else field
                        messages.error(request, f"{label}: {error}")
            if formset.errors:
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        messages.error(request, f"خطا در خودرو #{i+1}")
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f"{field}: {error}")
    else:
        # GET: prepare unbound (initial) form and formset
        form = FireReportForm(instance=report, initial={
            'shift_operator': getattr(report.shift_operator, 'id', ''),
            'firefighter': getattr(report.firefighter, 'id', ''),
        }, firefighter_queryset=firefighter_qs, operator_queryset=operator_qs)
        
        form_kwargs = {
            'company_vehicles_queryset': company_vehicles,
            'contractor_vehicles_queryset': contractor_vehicles,
        }
        formset = VehicleStatusFormSet(instance=report, prefix='vehicles', form_kwargs=form_kwargs)

    # Build formset_data for template JS in all code paths (GET or failed POST)
    formset_data = []
    try:
        for f in formset.forms:
            vehicle_data = {
                'id': getattr(getattr(f, 'instance', None), 'id', '') or '',
                'DELETE': False,
                'vehicle_source': getattr(getattr(f, 'instance', None), 'vehicle_source', 'company') or 'company',
                'company_vehicle': getattr(getattr(getattr(f, 'instance', None), 'company_vehicle', None), 'id', '') or '',
                'contractor_vehicle': getattr(getattr(getattr(f, 'instance', None), 'contractor_vehicle', None), 'id', '') or ''
            }
            formset_data.append(vehicle_data)
    except Exception:
        formset_data = []

    return render(request, 'fire_reports/report_form.html', {
        'form': form,
        'formset': formset,
        'formset_data': json.dumps(formset_data),
        'user_select_options': json.dumps({
            'operator': [{ 'id': u.id, 'text': f"{u.get_full_name()} ({getattr(getattr(u, 'userprofile', None), 'personnel_code', '')})" } for u in operator_qs],
            'firefighter': [{ 'id': u.id, 'text': f"{u.get_full_name()} ({getattr(getattr(u, 'userprofile', None), 'personnel_code', '')})" } for u in firefighter_qs]
        }, ensure_ascii=False),
        'title': 'ویرایش گزارش',
        'company_vehicles': company_vehicles,
        'contractor_vehicles': contractor_vehicles
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
