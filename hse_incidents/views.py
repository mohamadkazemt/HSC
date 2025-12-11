import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from permissions.utils import permission_required
from .models import IncidentReport, InjuryType, HseCompletionReport, IncidentDashboardSettings
from accounts.models import UserProfile
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
import jdatetime
from django.db.models import Q
import json
from django.http import HttpResponse
import pandas as pd
from io import BytesIO
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from contractor_management.models import Contractor, Employee
from django.template.loader import render_to_string
from django.conf import settings
import os
from weasyprint import HTML, CSS
from anomalis.models import Location, LocationSection
from .forms import HseCompletionReportForm, IncidentReportForm
from django.contrib.auth.models import Group
from dashboard.sms_utils import send_template_sms
from dashboard.utils import log_user_activity
from django.urls import reverse
from .notifications import notify_incident_report_created, notify_incident_completion
from risk_assessment.models import RiskAssessment
from anomalis.models import AnomalyDescription
from accounts.models import Position

logger = logging.getLogger(__name__)


def create_risk_from_incident(incident, position, user_profile):
    """
    ایجاد ریسک از حادثه ثبت شده
    """
    try:
        # دریافت اولین نوع جراحت (یا ایجاد یک پیش‌فرض)
        injury_type = incident.injury_type.first()
        if not injury_type:
            from .models import InjuryType
            # اگر نوع جراحتی وجود نداشت، یک پیش‌فرض ایجاد می‌کنیم یا از اولین نوع استفاده می‌کنیم
            injury_type = InjuryType.objects.first()
            if not injury_type:
                # اگر هیچ نوع جراحتی وجود نداشت، نمی‌توانیم ریسک ایجاد کنیم
                return None
        
        # دریافت اولین AnomalyDescription (یا ایجاد یک پیش‌فرض)
        # از آنجایی که نمی‌دانیم دقیقاً چه نوع خطری است، از اولین مورد استفاده می‌کنیم
        # یا می‌توانیم بر اساس توضیحات حادثه یک مورد مناسب پیدا کنیم
        hazard = AnomalyDescription.objects.first()
        if not hazard:
            # اگر هیچ AnomalyDescription وجود نداشت، نمی‌توانیم ریسک ایجاد کنیم
            return None
        
        # ایجاد ریسک با اطلاعات حادثه
        risk = RiskAssessment.objects.create(
            position=position,
            risk_source='incidents',  # منشا: حوادث و شبه حوادث
            activity_component=incident.section.section if incident.section else incident.location.name if incident.location else "حادثه",
            is_routine=False,  # حوادث معمولاً غیر روتین هستند
            hazard=hazard,
            potential_event=incident.full_description[:255] if len(incident.full_description) > 255 else incident.full_description,
            causes=incident.initial_cause,
            consequence=injury_type,
            existing_controls="کنترل‌های موجود در زمان حادثه بررسی نشده است",
            control_failure_causes="نیاز به بررسی بیشتر",
            probability=3,  # پیش‌فرض: متوسط (وقوع سالیانه)
            severity=3,  # پیش‌فرض: آسیب خیلی شدید
            created_by=user_profile,
            approval_status='pending',  # در انتظار تأیید
            notes=f"این ریسک از حادثه شماره {incident.id} ایجاد شده است."
        )
        
        # اتصال ریسک به حادثه
        incident.related_risk = risk
        incident.save()
        
        return risk
    except Exception as e:
        logger.error(f"خطا در ایجاد ریسک از حادثه {incident.id}: {e}")
        return None

def persian_to_english_numbers(persian_str):
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '/': '-'
    }
    return ''.join(persian_to_english.get(c, c) for c in persian_str)

@login_required
#@permission_required("incident_report")
@ensure_csrf_cookie
def report_incident(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "پروفایل کاربری شما یافت نشد. لطفا با مدیر سیستم تماس بگیرید.")
        today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
        return render(request, 'hse_incidents/incident_report_form.html', {
            'form': IncidentReportForm(),
            'today_jalali': today_jalali,
        })

    # ثبت فعالیت مشاهده فرم گزارش حادثه
    if request.method == 'GET':
        log_user_activity(
            user=request.user,
            activity_type='view',
            description='مشاهده فرم گزارش حادثه جدید',
            related_model='IncidentReport',
            related_object_id=None,
            url=reverse('hse_incidents:incident_report'),
            request=request
        )

    locations = Location.objects.all()
    sections = LocationSection.objects.all()
    positions = Position.objects.all().order_by('name')

    if request.method == 'POST':
        # کپی داده‌ها برای تبدیل تاریخ شمسی به میلادی قبل از اعتبارسنجی فرم
        post_data = request.POST.copy()
        raw_date = post_data.get('incident_date', '')
        if raw_date:
            try:
                normalized = persian_to_english_numbers(raw_date)
                # jalali usually with '/' or '-'
                parts = list(map(int, normalized.replace('/', '-').split('-')))
                gdate = jdatetime.date(parts[0], parts[1], parts[2]).togregorian()
                post_data['incident_date'] = gdate.strftime('%Y-%m-%d')
            except Exception:
                # اگر تبدیل شکست خورد، همان مقدار را می‌گذاریم تا فرم خطا دهد
                pass
        form = IncidentReportForm(post_data)
        if form.is_valid():
            try:
                cleaned = form.cleaned_data
                # بررسی وجود گزارش تکراری
                existing_report = IncidentReport.objects.filter(
                    incident_date=cleaned.get('incident_date'),
                    incident_time=cleaned.get('incident_time'),
                    location=cleaned.get('location'),
                    section=cleaned.get('section'),
                ).first()
                if existing_report:
                    messages.warning(request, "گزارش مشابهی برای این تاریخ، ساعت و محل قبلاً ثبت شده است. لطفاً بررسی کنید.")
                    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
                    return render(request, 'hse_incidents/incident_report_form.html', {
                        'form': form,
                        'locations': locations,
                        'sections': sections,
                        'positions': positions,
                        'today_jalali': today_jalali,
                    })

                incident = form.save(commit=False)
                incident.report_author = user_profile
                incident.save()
                form.save_m2m()
                
                # بررسی اینکه آیا کاربر می‌خواهد به ریسک اضافه شود
                add_to_risk = cleaned.get('add_to_risk', False)
                risk_position = cleaned.get('risk_position')
                
                if add_to_risk and risk_position:
                    risk = create_risk_from_incident(incident, risk_position, user_profile)
                    if risk:
                        messages.success(request, f"گزارش حادثه ثبت شد و ریسک مرتبط با عدد ریسک {risk.risk_number} ایجاد شد.")
                    else:
                        messages.warning(request, "گزارش حادثه ثبت شد اما ایجاد ریسک با خطا مواجه شد. لطفاً به صورت دستی ریسک را ایجاد کنید.")
                elif add_to_risk and not risk_position:
                    messages.warning(request, "گزارش حادثه ثبت شد اما برای ایجاد ریسک، لطفاً سمت/شغل را انتخاب کنید.")

                # ثبت فعالیت ایجاد گزارش حادثه
                log_user_activity(
                    user=request.user,
                    activity_type='create',
                    description=f'ثبت گزارش حادثه جدید در {incident.location.name if incident.location else "نامشخص"}',
                    related_model='IncidentReport',
                    related_object_id=incident.id,
                    url=reverse('hse_incidents:report_details', args=[incident.id]),
                    request=request
                )

                # ارسال پیامک به مدیران HSE
                template_id = 169411  # شناسه قالب
                try:
                    hse_group = Group.objects.get(name='مدیر HSE')
                    for user in hse_group.user_set.all():
                        try:
                            profile = user.userprofile
                            location_name = incident.location.name if incident.location else "نامشخص"
                            parameters = [
                                {"Name": "LOCATION", "Value": location_name},
                                {"Name": "INCIDENT_ID", "Value": str(incident.id)}
                            ]
                            send_template_sms(profile.mobile, template_id, parameters)
                            logger.info(f"پیامک به شماره {profile.mobile} برای حادثه {incident.id} ارسال شد")
                        except Exception as sms_error:
                            logger.error(f"خطا در ارسال پیامک برای حادثه {incident.id} به کاربر {user.username}: {sms_error}")
                            continue
                except Group.DoesNotExist:
                    logger.error("گروه 'مدیر HSE' یافت نشد")
                    messages.warning(request, "گروه 'مدیر HSE' یافت نشد، اما گزارش با موفقیت ثبت شد")

                notify_incident_report_created(incident, actor=request.user)

                messages.success(request, "گزارش حادثه با موفقیت ثبت شد")
                # پاسخ مخصوص AJAX
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'redirect': reverse('hse_incidents:report_details', args=[incident.id])
                    })
                return redirect('hse_incidents:report_details', report_id=incident.id)
            except Exception as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': f'خطا در ثبت گزارش: {e}'}, status=500)
                messages.error(request, f"خطا در ثبت گزارش: {e}")
        else:
            # فرم نامعتبر است
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'فرم نامعتبر است', 'errors': form.errors}, status=400)
            # Get today's date in Persian (Jalali) format for date picker maxDate
            today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
            return render(request, 'hse_incidents/incident_report_form.html', {
                'form': form,
                'locations': locations,
                'sections': sections,
                'positions': positions,
                'today_jalali': today_jalali,
            })

    # GET یا در صورت عدم POST موفق
    form = IncidentReportForm()
    # Get today's date in Persian (Jalali) format for date picker maxDate
    today_jalali = jdatetime.date.today().strftime('%Y/%m/%d')
    return render(request, 'hse_incidents/incident_report_form.html', {
        'form': form, 
        'locations': locations, 
        'sections': sections,
        'positions': positions,
        'today_jalali': today_jalali,
    })


@login_required
def get_injury_types_ajax(request):
    # ثبت فعالیت جستجوی انواع آسیب
    search_term = request.GET.get('term', '')
    if search_term:
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'جستجوی نوع آسیب با عبارت "{search_term}"',
            related_model='InjuryType',
            related_object_id=None,
            url=None,
            request=request
        )
    
    injury_types = []
    if search_term:
        injury_types = InjuryType.objects.filter(Q(name__icontains=search_term)).values("id", "name")
    else:
        injury_types = InjuryType.objects.values("id", "name")
    return JsonResponse(list(injury_types), safe=False)


@login_required
def get_contractors_ajax(request):
    contractors = Contractor.objects.all().values('id', 'company_name')
    return JsonResponse(list(contractors), safe=False)


@login_required
def get_contractor_employees_ajax(request):
    contractor_id = request.GET.get('contractor_id')
    if not contractor_id:
        return JsonResponse([], safe=False)
    employees = Employee.objects.filter(contractor_id=contractor_id).values('id', 'first_name', 'last_name')
    data = [{
        'id': e['id'],
        'name': f"{e['first_name']} {e['last_name']}".strip()
    } for e in employees]
    return JsonResponse(data, safe=False)


@login_required
def get_user_profiles_ajax(request):
    search_term = request.GET.get('term', '')
    profiles = UserProfile.objects.select_related('user').all()
    if search_term:
        profiles = profiles.filter(
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(user__username__icontains=search_term)
        )
    data = [{
        'id': p.id,
        'text': f"{p.user.first_name} {p.user.last_name} ({p.user.username})".strip()
    } for p in profiles[:50]]  # محدود به 50 نتیجه
    return JsonResponse(data, safe=False)


#@permission_required("list_reports")
@login_required
def list_reports(request):
    # ثبت فعالیت مشاهده لیست گزارش‌های حادثه
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست گزارش‌های حادثه',
        related_model='IncidentReport',
        related_object_id=None,
        url=reverse('hse_incidents:list_reports'),
        request=request
    )
    
    search_query = request.GET.get('search', '')
    from_date_str = request.GET.get('from_date', '')
    to_date_str = request.GET.get('to_date', '')
    
    # نگه‌داری مقادیر اصلی برای نمایش در فرم
    from_date_display = from_date_str
    to_date_display = to_date_str

    reports = IncidentReport.objects.all()

    if search_query:
        reports = reports.filter(
            Q(location__name__icontains=search_query) |
            Q(section__section__icontains=search_query) |
            Q(full_description__icontains=search_query) |
            Q(initial_cause__icontains=search_query)
            | Q(report_author__user__first_name__icontains=search_query)
            | Q(report_author__user__last_name__icontains=search_query)
        )
        
        # ثبت فعالیت جستجو در گزارش‌های حادثه
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'جستجو در گزارش‌های حادثه با عبارت "{search_query}"',
            related_model='IncidentReport',
            related_object_id=None,
            url=request.get_full_path(),
            request=request
        )

    if from_date_str:
        try:
            # تبدیل اعداد فارسی به انگلیسی
            persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            from_date_normalized = from_date_str.translate(persian_to_english)
            
            # پشتیبانی از هر دو فرمت / و -
            separator = '/' if '/' in from_date_normalized else '-'
            from_date_parts = list(map(int, from_date_normalized.split(separator)))
            from_date_gregorian = jdatetime.date(from_date_parts[0], from_date_parts[1],
                                                 from_date_parts[2]).togregorian()
            reports = reports.filter(incident_date__gte=from_date_gregorian)
        except (ValueError, IndexError):
            pass

    if to_date_str:
        try:
            # تبدیل اعداد فارسی به انگلیسی
            persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            to_date_normalized = to_date_str.translate(persian_to_english)
            
            # پشتیبانی از هر دو فرمت / و -
            separator = '/' if '/' in to_date_normalized else '-'
            to_date_parts = list(map(int, to_date_normalized.split(separator)))
            to_date_gregorian = jdatetime.date(to_date_parts[0], to_date_parts[1], to_date_parts[2]).togregorian()
            reports = reports.filter(incident_date__lte=to_date_gregorian)
        except (ValueError, IndexError):
            pass

    reports = reports.order_by('-incident_date')

    page = request.GET.get('page', 1)
    paginator = Paginator(reports, 10)
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    return render(request, 'hse_incidents/report_list.html',
                  {'reports': reports, 'search_query': search_query, 'from_date': from_date_display,
                   'to_date': to_date_display})


# hse_incidents/views.py
@permission_required("report_details")
@login_required
@ensure_csrf_cookie
def report_details(request, report_id):
    report = get_object_or_404(IncidentReport, id=report_id)
    
    # ثبت فعالیت مشاهده جزئیات گزارش حادثه
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات گزارش حادثه شماره {report_id}',
        related_model='IncidentReport',
        related_object_id=report_id,
        url=reverse('hse_incidents:report_details', args=[report_id]),
        request=request
    )
    
    try:
        hse_completion = HseCompletionReport.objects.get(incident_report=report)
    except HseCompletionReport.DoesNotExist:
        hse_completion = None

    if request.method == 'POST':
        form = HseCompletionReportForm(request.POST, request.FILES, instance=hse_completion)
        if form.is_valid():
            try:
                hse_completion = form.save(commit=False)
                hse_completion.incident_report = report
                hse_completion.save()
                report.is_completed = True
                report.save()
                notify_incident_completion(report, actor=request.user)
                
                # ثبت فعالیت تکمیل گزارش حادثه
                log_user_activity(
                    user=request.user,
                    activity_type='update',
                    description=f'تکمیل گزارش حادثه شماره {report_id}',
                    related_model='HseCompletionReport',
                    related_object_id=hse_completion.id,
                    url=reverse('hse_incidents:report_details', args=[report_id]),
                    request=request
                )
                
                messages.success(request, "گزارش حادثه با موفقیت تکمیل شد.")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'redirect': reverse('hse_incidents:report_details', args=[report_id])})
                return redirect('hse_incidents:report_details', report_id=report_id)
            except Exception as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': f'خطا در ثبت اطلاعات: {e}'}, status=500)
                messages.error(request, "خطا در ثبت اطلاعات، فرم را بررسی کنید")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'فرم نامعتبر است', 'errors': form.errors}, status=400)
            messages.error(request, "خطا در ثبت اطلاعات، فرم را بررسی کنید")
    else:
         if request.GET.get('form'): # چک کردن پارامتر فرم
            form = HseCompletionReportForm(instance=hse_completion)
            
            # ثبت فعالیت مشاهده فرم تکمیل گزارش حادثه
            log_user_activity(
                user=request.user,
                activity_type='view',
                description=f'مشاهده فرم تکمیل گزارش حادثه شماره {report_id}',
                related_model='IncidentReport',
                related_object_id=report_id,
                url=request.get_full_path(),
                request=request
            )
            
            return render(request, 'hse_incidents/hse_completion_form.html', {'form': form})
         else:
              form = HseCompletionReportForm(instance=hse_completion)
    
    # دریافت اقدامات اصلاحی مرتبط با این حادثه
    related_corrective_actions = []
    try:
        from corrective_actions.models import CorrectiveAction
        related_corrective_actions = CorrectiveAction.objects.filter(related_incident=report).select_related('requester', 'receiver').order_by('-created_at')
    except ImportError:
        pass
    
    return render(request, 'hse_incidents/report_details.html', {
        'report': report, 
        'form': form,
        'hse_completion': hse_completion,
        'related_corrective_actions': related_corrective_actions,
    })


@permission_required("export_reports_excel")
@login_required
def export_reports_excel(request):
    # ثبت فعالیت دریافت اکسل گزارش‌های حادثه
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='دریافت فایل اکسل گزارش‌های حادثه',
        related_model='IncidentReport',
        related_object_id=None,
        url=reverse('hse_incidents:export_reports_excel'),
        request=request
    )
    
    search_query = request.GET.get('search', '')
    from_date_str = request.GET.get('from_date', '')
    to_date_str = request.GET.get('to_date', '')

    reports = IncidentReport.objects.all()

    if search_query:
        reports = reports.filter(
            Q(location__name__icontains=search_query) |
            Q(section__section__icontains=search_query) |
            Q(full_description__icontains=search_query) |
            Q(initial_cause__icontains=search_query)
        )

    if from_date_str:
        try:
            from_date_parts = list(map(int, from_date_str.split('-')))
            from_date_gregorian = jdatetime.date(from_date_parts[0], from_date_parts[1],
                                                 from_date_parts[2]).togregorian()
            reports = reports.filter(incident_date__gte=from_date_gregorian)
        except ValueError:
            pass

    if to_date_str:
        try:
            to_date_parts = list(map(int, to_date_str.split('-')))
            to_date_gregorian = jdatetime.date(to_date_parts[0], to_date_parts[1], to_date_parts[2]).togregorian()
            reports = reports.filter(incident_date__lte=to_date_gregorian)
        except ValueError:
            pass

    # ایجاد دیتافریم پانداس
    data = []
    for report in reports:
        # تبدیل تاریخ میلادی به شمسی
        jalali_date = jdatetime.date.fromgregorian(date=report.incident_date)
        jalali_date_str = jalali_date.strftime('%Y-%m-%d')

        # دریافت نام‌های نوع آسیب
        injury_types = ", ".join([injury.name for injury in report.injury_type.all()])

        # دریافت نام‌های افراد درگیر
        involved_persons = ", ".join([f"{person.user.first_name} {person.user.last_name}" for person in
                                      report.involved_person.all()])

        # دریافت نام‌های کارکنان پیمانکار درگیر
        contractor_employees = ", ".join(
            [f"{employee.first_name} {employee.last_name}" for employee in report.related_contractor_employees.all()])

        row = {
            'شماره گزارش': report.id,
            'تاریخ حادثه': jalali_date_str,
            'زمان حادثه': report.incident_time,
            'محل حادثه': report.location.name if report.location else "",
            'بخش': report.section.section if report.section else "",
            'افراد درگیر': involved_persons,
            'تجهیزات درگیر': report.involved_equipment,
            'نوع آسیب': injury_types,
            'قسمت آسیب دیده بدن': report.affected_body_part,
            'شرح خسارت': report.damage_description,
            'نهاد مرتبط': report.related_entity,
            'پیمانکار مرتبط': report.related_contractor.company_name if report.related_contractor else "",
            'کارکنان پیمانکار': contractor_employees,
            'نیاز به ماشین آتش‌نشانی': "بله" if report.fire_truck_needed else "خیر",
            'زمان رسیدن ماشین آتش‌نشانی': report.fire_truck_arrival_time,
            'نیاز به آمبولانس': "بله" if report.ambulance_needed else "خیر",
            'زمان رسیدن آمبولانس': report.ambulance_arrival_time,
            'بستری شدن': "بله" if report.hospitalized else "خیر",
            'زمان بستری شدن': report.hospitalized_time,
            'نوع حمل و نقل': report.transportation_type,
            'شرح کامل حادثه': report.full_description,
            'علت اولیه': report.initial_cause,
            'گزارش دهنده': f"{report.report_author.user.first_name} {report.report_author.user.last_name}",
            'تاریخ ثبت': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'وضعیت تکمیل': "تکمیل شده" if report.is_completed else "در انتظار تکمیل"
        }
        data.append(row)

    df = pd.DataFrame(data)

    # ایجاد فایل اکسل
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='گزارش حوادث', index=False)
        worksheet = writer.sheets['گزارش حوادث']
        for i, col in enumerate(df.columns):
            # تنظیم عرض ستون‌ها
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)

    output.seek(0)
    response = HttpResponse(output.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=incident_reports.xlsx'
    return response


# AJAX endpoint برای ذخیره فرم تکمیل گزارش بدون CSRF
@csrf_exempt
@login_required
def submit_hse_completion_ajax(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    report = get_object_or_404(IncidentReport, id=report_id)
    try:
        try:
            hse_completion = HseCompletionReport.objects.get(incident_report=report)
        except HseCompletionReport.DoesNotExist:
            hse_completion = None
        form = HseCompletionReportForm(request.POST, request.FILES, instance=hse_completion)
        if not form.is_valid():
            # اگر AJAX نیست، بازگشت به صفحه جزئیات با پیام خطا
            if request.headers.get('x-requested-with') != 'XMLHttpRequest':
                messages.error(request, "خطا در ثبت اطلاعات، فرم را بررسی کنید")
                return redirect('hse_incidents:report_details', report_id=report_id)
            return JsonResponse({'status': 'error', 'message': 'فرم نامعتبر است', 'errors': form.errors}, status=400)
        hse_completion = form.save(commit=False)
        hse_completion.incident_report = report
        hse_completion.save()
        report.is_completed = True
        report.save()
        log_user_activity(
            user=request.user,
            activity_type='update',
            description=f'تکمیل گزارش حادثه شماره {report_id} (AJAX)',
            related_model='HseCompletionReport',
            related_object_id=hse_completion.id,
            url=reverse('hse_incidents:report_details', args=[report_id]),
            request=request
        )
        # اگر درخواست AJAX بود JSON برگردان، در غیر اینصورت ریدایرکت معمولی
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'redirect': reverse('hse_incidents:report_details', args=[report_id])})
        messages.success(request, "گزارش حادثه با موفقیت تکمیل شد.")
        return redirect('hse_incidents:report_details', report_id=report_id)
    except Exception as e:
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            messages.error(request, f"خطا: {e}")
            return redirect('hse_incidents:report_details', report_id=report_id)
        return JsonResponse({'status': 'error', 'message': f'خطا: {e}'}, status=500)


# hse_incidents/views.py
@permission_required("report_details_pdf")
@login_required
def report_details_pdf(request, report_id):
    from core.models import SiteSettings
    from django.utils import timezone
    
    report = get_object_or_404(IncidentReport, id=report_id)
    try:
        hse_completion = HseCompletionReport.objects.get(incident_report=report)
    except HseCompletionReport.DoesNotExist:
        hse_completion = None

    user_signature_path = None
    if report.report_author and report.report_author.signature:
        user_signature_path = os.path.join(settings.MEDIA_ROOT, str(report.report_author.signature))

    # دریافت تنظیمات سایت
    try:
        site_settings = SiteSettings.objects.first()
    except:
        site_settings = None

    title = f"گزارش حادثه شماره {report.id}"

    context = {
        'report': report,
        'title': title,
        'user_signature': user_signature_path,
        'hse_completion': hse_completion,
        'site_settings': site_settings,
        'now': timezone.now(),
        'STATIC_ROOT': settings.STATIC_ROOT,
        'MEDIA_ROOT': settings.MEDIA_ROOT,
    }
    html = render_to_string('hse_incidents/daily_report_pdf.html', context)
    # font_config = FontConfiguration()
    css = CSS(string='@page { size: A4; margin: 10mm; }')
    pdf_file = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(
        stylesheets=[css])  # base_url رو درست تنظیم کردیم
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="incident_report_{report.id}.pdf"'
    return response

# ============= مدیریت انواع جراحات =============

@login_required
@permission_required('injury_types_list')
def injury_types_list(request):
    """لیست انواع جراحات"""
    from django.urls import reverse
    from dashboard.utils import log_user_activity
    
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست انواع جراحت',
        related_model='InjuryType',
        related_object_id=None,
        url=reverse('hse_incidents:injury_types_list'),
        request=request
    )
    
    search_query = request.GET.get('search', '')
    injury_types = InjuryType.objects.all()
    
    if search_query:
        injury_types = injury_types.filter(name__icontains=search_query)
        log_user_activity(
            user=request.user,
            activity_type='view',
            description=f'جستجو در انواع جراحت با عبارت "{search_query}"',
            related_model='InjuryType',
            related_object_id=None,
            url=request.get_full_path(),
            request=request
        )
    
    injury_types = injury_types.order_by('name')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(injury_types, 15)
    try:
        injury_types = paginator.page(page)
    except PageNotAnInteger:
        injury_types = paginator.page(1)
    except EmptyPage:
        injury_types = paginator.page(paginator.num_pages)
    
    return render(request, 'hse_incidents/injury_types_list.html', {
        'injury_types': injury_types,
        'search_query': search_query,
    })


@login_required
@permission_required('injury_type_create')
def injury_type_create_ajax(request):
    """ایجاد نوع جراحت جدید (AJAX)"""
    from dashboard.utils import log_user_activity
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            
            if not name:
                return JsonResponse({'status': 'error', 'message': 'نام جراحت الزامی است'}, status=400)
            
            # بررسی تکراری بودن
            if InjuryType.objects.filter(name=name).exists():
                return JsonResponse({'status': 'error', 'message': 'این نوع جراحت قبلاً ثبت شده است'}, status=400)
            
            injury_type = InjuryType.objects.create(name=name)
            
            log_user_activity(
                user=request.user,
                activity_type='create',
                description=f'ایجاد نوع جراحت جدید: {name}',
                related_model='InjuryType',
                related_object_id=injury_type.id,
                url=None,
                request=request
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'نوع جراحت با موفقیت ایجاد شد',
                'injury_type': {
                    'id': injury_type.id,
                    'name': injury_type.name
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
@permission_required('injury_type_update')
def injury_type_update_ajax(request, pk):
    """ویرایش نوع جراحت (AJAX)"""
    from dashboard.utils import log_user_activity
    
    if request.method == 'POST':
        try:
            injury_type = get_object_or_404(InjuryType, pk=pk)
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            
            if not name:
                return JsonResponse({'status': 'error', 'message': 'نام جراحت الزامی است'}, status=400)
            
            # بررسی تکراری بودن (به جز خود این رکورد)
            if InjuryType.objects.filter(name=name).exclude(pk=pk).exists():
                return JsonResponse({'status': 'error', 'message': 'این نام قبلاً استفاده شده است'}, status=400)
            
            old_name = injury_type.name
            injury_type.name = name
            injury_type.save()
            
            log_user_activity(
                user=request.user,
                activity_type='update',
                description=f'ویرایش نوع جراحت: "{old_name}" به "{name}"',
                related_model='InjuryType',
                related_object_id=injury_type.id,
                url=None,
                request=request
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'نوع جراحت با موفقیت ویرایش شد',
                'injury_type': {
                    'id': injury_type.id,
                    'name': injury_type.name
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
@permission_required('injury_type_delete')
def injury_type_delete_ajax(request, pk):
    """حذف نوع جراحت (AJAX)"""
    from dashboard.utils import log_user_activity
    
    if request.method == 'POST':
        try:
            injury_type = get_object_or_404(InjuryType, pk=pk)
            
            # بررسی استفاده در گزارشات
            if injury_type.incidents.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': f'این نوع جراحت در {injury_type.incidents.count()} گزارش استفاده شده و قابل حذف نیست'
                }, status=400)
            
            name = injury_type.name
            injury_type.delete()
            
            log_user_activity(
                user=request.user,
                activity_type='delete',
                description=f'حذف نوع جراحت: {name}',
                related_model='InjuryType',
                related_object_id=pk,
                url=None,
                request=request
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'نوع جراحت با موفقیت حذف شد'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
def incident_dashboard(request):
    """داشبورد کامل حوادث HSE"""
    from datetime import date, timedelta, datetime
    from django.db.models import Count, Sum, Q, F
    from fire_reports.models import FireReport
    import jdatetime
    import math
    
    # دریافت تنظیمات داشبورد
    settings = IncidentDashboardSettings.get_settings()
    
    # محاسبه تاریخ ابتدای سال جاری (شمسی)
    today_jalali = jdatetime.date.today()
    year_start_jalali = jdatetime.date(today_jalali.year, 1, 1)
    year_start_gregorian = year_start_jalali.togregorian()
    
    # محاسبه روزهای بدون حادثه
    days_without_incident = 0
    start_date = None
    if settings.days_without_incident_start_date:
        start_date = settings.days_without_incident_start_date
    else:
        # اگر تاریخ شروع تنظیم نشده، از ابتدای سال استفاده می‌کنیم
        start_date = year_start_gregorian
    
    today = date.today()
    days_without_incident = (today - start_date).days
    if days_without_incident < 0:
        days_without_incident = 0
    
    # فیلتر حوادث از ابتدای سال تا کنون
    incidents_this_year = IncidentReport.objects.filter(
        incident_date__gte=year_start_gregorian
    )
    
    # محاسبه تعداد کل حوادث
    total_incidents = incidents_this_year.count()
    
    # محاسبه ساعت-کار کل (از ابتدای سال تا کنون)
    days_passed = (date.today() - year_start_gregorian).days + 1
    total_man_hours = days_passed * settings.average_man_hours_per_day
    
    # محاسبه شاخص FR (Frequency Rate)
    # FR = (تعداد حوادث × 1,000,000) / ساعت-کار کل
    fr_value = 0
    if total_man_hours > 0:
        fr_value = (total_incidents * 1_000_000) / total_man_hours
    
    # محاسبه شاخص SR (Severity Rate)
    # SR = (مجموع روزهای کاری از دست رفته × 1,000,000) / ساعت-کار کل
    total_lost_workdays = HseCompletionReport.objects.filter(
        incident_report__incident_date__gte=year_start_gregorian,
        lost_workdays__isnull=False
    ).aggregate(total=Sum('lost_workdays'))['total'] or 0
    
    sr_value = 0
    if total_man_hours > 0:
        sr_value = (total_lost_workdays * 1_000_000) / total_man_hours
    
    # محاسبه شاخص FSI (Frequency Severity Index)
    # FSI = √((FR × SR) / 1,000)
    fsi_value = 0
    if fr_value > 0 and sr_value > 0:
        fsi_value = math.sqrt((fr_value * sr_value) / 1_000)
    
    # آمار تفکیکی حوادث بر اساس نوع
    # حوادث فردی: حوادثی که related_entity = 'کاراوران' یا involved_person وجود دارد
    individual_incidents = incidents_this_year.filter(
        Q(related_entity__icontains='کاراوران') | Q(involved_person__isnull=False)
    ).distinct().count()
    
    # حوادث آتش‌سوزی: حوادثی که fire_truck_needed = True یا از FireReport
    fire_incidents_from_reports = incidents_this_year.filter(fire_truck_needed=True).count()
    # همچنین حوادث آتش از FireReport
    from django.utils import timezone
    year_start_datetime = timezone.make_aware(
        datetime.combine(year_start_gregorian, datetime.min.time())
    )
    fire_reports_this_year = FireReport.objects.filter(
        report_date__gte=year_start_datetime
    )
    fire_incidents_from_fire_reports = fire_reports_this_year.aggregate(
        total=Sum('fire_incident_count')
    )['total'] or 0
    fire_incidents = fire_incidents_from_reports + fire_incidents_from_fire_reports
    
    # حوادث تصادفات: حوادثی که transportation_type پر شده یا ambulance_needed = True
    accident_incidents = incidents_this_year.filter(
        Q(transportation_type__isnull=False) | Q(ambulance_needed=True)
    ).exclude(
        Q(related_entity__icontains='کاراوران') | Q(involved_person__isnull=False)
    ).exclude(fire_truck_needed=True).distinct().count()
    
    # سایر حوادث
    other_incidents = total_incidents - individual_incidents - fire_incidents_from_reports - accident_incidents
    
    # تفکیک بر اساس کارفرما و پیمانکاران
    # حوادث کارفرما (کاراوران)
    company_incidents = incidents_this_year.filter(
        Q(related_entity__icontains='کاراوران') | 
        (Q(related_contractor__isnull=True) & Q(involved_person__isnull=False))
    ).distinct().count()
    
    # حوادث پیمانکاران
    contractor_incidents = incidents_this_year.filter(
        Q(related_contractor__isnull=False) | 
        Q(related_contractor_employees__isnull=False)
    ).distinct().count()
    
    # آماده‌سازی داده‌های نمودار برای شاخص‌ها (12 ماه گذشته)
    chart_data = {
        'months': [],
        'fr_values': [],
        'sr_values': [],
        'fsi_values': [],
        'days_without_incident': [],
    }
    
    # محاسبه شاخص‌ها برای هر ماه از ابتدای سال
    current_date = year_start_gregorian
    cumulative_days_without = 0
    last_severe_incident_date = settings.days_without_incident_start_date
    
    while current_date <= date.today():
        month_start = date(current_date.year, current_date.month, 1)
        # محاسبه آخرین روز ماه
        if current_date.month == 12:
            month_end = date(current_date.year, 12, 31)
        else:
            month_end = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)
        
        if month_end > date.today():
            month_end = date.today()
        
        # حوادث این ماه
        month_incidents = IncidentReport.objects.filter(
            incident_date__gte=month_start,
            incident_date__lte=month_end
        )
        
        # بررسی حادثه شدید در این ماه
        severe_incident = month_incidents.filter(
            is_severe_production_stoppage=True
        ).order_by('-incident_date').first()
        
        if severe_incident:
            last_severe_incident_date = severe_incident.incident_date
            cumulative_days_without = 0
        elif last_severe_incident_date:
            cumulative_days_without = (month_end - last_severe_incident_date).days
        else:
            cumulative_days_without = (month_end - year_start_gregorian).days
        
        # محاسبه ساعت-کار این ماه
        month_days = (month_end - month_start).days + 1
        month_man_hours = month_days * settings.average_man_hours_per_day
        
        # محاسبه FR برای این ماه
        month_fr = 0
        if month_man_hours > 0:
            month_fr = (month_incidents.count() * 1_000_000) / month_man_hours
        
        # محاسبه SR برای این ماه
        month_lost_days = HseCompletionReport.objects.filter(
            incident_report__incident_date__gte=month_start,
            incident_report__incident_date__lte=month_end,
            lost_workdays__isnull=False
        ).aggregate(total=Sum('lost_workdays'))['total'] or 0
        
        month_sr = 0
        if month_man_hours > 0:
            month_sr = (month_lost_days * 1_000_000) / month_man_hours
        
        # محاسبه FSI برای این ماه
        month_fsi = 0
        if month_fr > 0 and month_sr > 0:
            month_fsi = math.sqrt((month_fr * month_sr) / 1_000)
        
        # تبدیل به شمسی برای نمایش
        month_jalali = jdatetime.date.fromgregorian(date=month_start)
        month_name = month_jalali.strftime('%Y/%m')
        
        chart_data['months'].append(month_name)
        chart_data['fr_values'].append(round(month_fr, 2))
        chart_data['sr_values'].append(round(month_sr, 2))
        chart_data['fsi_values'].append(round(month_fsi, 2))
        chart_data['days_without_incident'].append(cumulative_days_without)
        
        # رفتن به ماه بعد
        if current_date.month == 12:
            current_date = date(current_date.year + 1, 1, 1)
        else:
            current_date = date(current_date.year, current_date.month + 1, 1)
    
    # آماده‌سازی داده‌های نمودار تفکیک حوادث
    incident_type_chart = {
        'labels': ['حوادث فردی', 'آتش‌سوزی', 'تصادفات', 'سایر'],
        'data': [individual_incidents, fire_incidents, accident_incidents, other_incidents]
    }
    
    # آماده‌سازی داده‌های نمودار تفکیک کارفرما/پیمانکار
    entity_chart = {
        'labels': ['کارفرما (کاراوران)', 'پیمانکاران'],
        'data': [company_incidents, contractor_incidents]
    }
    
    # آخرین حوادث
    recent_incidents = incidents_this_year.order_by('-incident_date', '-incident_time')[:10]
    
    # حوادث شدید منجر به توقف تولید
    severe_incidents = incidents_this_year.filter(
        is_severe_production_stoppage=True
    ).order_by('-incident_date', '-incident_time')
    
    # تبدیل تاریخ شروع به شمسی برای نمایش
    start_date_jalali = None
    if start_date:
        start_date_jalali = jdatetime.date.fromgregorian(date=start_date).strftime('%Y/%m/%d')
    
    # بررسی اینکه آیا تاریخ شروع از تنظیمات آمده یا از ابتدای سال
    is_start_date_from_settings = bool(settings.days_without_incident_start_date)
    
    context = {
        'days_without_incident': days_without_incident,
        'start_date': start_date,
        'start_date_jalali': start_date_jalali,
        'is_start_date_from_settings': is_start_date_from_settings,
        'fr_value': round(fr_value, 2),
        'sr_value': round(sr_value, 2),
        'fsi_value': round(fsi_value, 2),
        'total_incidents': total_incidents,
        'total_lost_workdays': total_lost_workdays,
        'total_man_hours': total_man_hours,
        'individual_incidents': individual_incidents,
        'fire_incidents': fire_incidents,
        'accident_incidents': accident_incidents,
        'other_incidents': other_incidents,
        'company_incidents': company_incidents,
        'contractor_incidents': contractor_incidents,
        'chart_data': chart_data,
        'incident_type_chart': incident_type_chart,
        'entity_chart': entity_chart,
        'recent_incidents': recent_incidents,
        'severe_incidents': severe_incidents,
        'settings': settings,
        'year_start_jalali': year_start_jalali.strftime('%Y/%m/%d'),
    }
    
    return render(request, 'hse_incidents/dashboard.html', context)


@login_required
@ensure_csrf_cookie
def update_dashboard_start_date_ajax(request):
    """به‌روزرسانی تاریخ شروع شمارش روزهای بدون حادثه"""
    from datetime import date
    from accounts.models import UserProfile
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'پروفایل کاربری یافت نشد'}, status=400)
    
    try:
        data = json.loads(request.body)
        date_str = data.get('start_date', '').strip()
        
        if not date_str:
            return JsonResponse({'status': 'error', 'message': 'تاریخ الزامی است'}, status=400)
        
        # تبدیل تاریخ شمسی به میلادی
        try:
            normalized = persian_to_english_numbers(date_str)
            separator = '/' if '/' in normalized else '-'
            parts = list(map(int, normalized.split(separator)))
            gregorian_date = jdatetime.date(parts[0], parts[1], parts[2]).togregorian()
        except (ValueError, IndexError) as e:
            return JsonResponse({'status': 'error', 'message': 'فرمت تاریخ نامعتبر است'}, status=400)
        
        # به‌روزرسانی تنظیمات
        settings = IncidentDashboardSettings.get_settings()
        settings.days_without_incident_start_date = gregorian_date
        settings.updated_by = user_profile
        settings.save()
        
        # محاسبه روزهای بدون حادثه جدید
        today = date.today()
        days_without_incident = (today - gregorian_date).days
        if days_without_incident < 0:
            days_without_incident = 0
        
        # تبدیل به شمسی برای نمایش
        start_date_jalali = jdatetime.date.fromgregorian(date=gregorian_date).strftime('%Y/%m/%d')
        
        return JsonResponse({
            'status': 'success',
            'message': 'تاریخ شروع با موفقیت به‌روزرسانی شد',
            'days_without_incident': days_without_incident,
            'start_date_jalali': start_date_jalali
        })
        
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی تاریخ شروع: {e}")
        return JsonResponse({'status': 'error', 'message': f'خطا: {str(e)}'}, status=500)


@login_required
@permission_required('hse_incidents:download_import_template')
def download_import_template(request):
    """دانلود فایل الگوی اکسل برای ایمپورت حوادث"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    try:
        # ایجاد workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "الگوی ثبت حوادث"
        
        # تعریف استایل‌ها
        header_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        center_aligned = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # تعریف هدرها (فارسی) - دقت: فاصله‌ها مهم هستند!
        headers = [
            "تاریخ حادثه (1403/09/15)",
            "ساعت حادثه (14:30)",
            "نوع حادثه (human/equipment/environmental)",
            "نام سایت",
            "نام محل دقیق (اختیاری)",
            "کد پرسنلی اشخاص درگیر (جدا با کاما)",
            "تجهیزات مرتبط",
            "انواع جراحت (جدا با کاما)",
            "عضو آسیب دیده",
            "شرح آسیب",
            "نوع ارتباط",
            "نام شرکت پیمانکار (اختیاری)",
            "کد ملی پرسنل پیمانکار (جدا با کاما)",
            "آتش‌نشانی اعزام شد؟ (بله/خیر)",
            "ساعت رسیدن آتش‌نشانی",
            "آمبولانس اعزام شد؟ (بله/خیر)",
            "ساعت رسیدن آمبولانس",
            "به بیمارستان اعزام شد؟ (بله/خیر)",
            "ساعت اعزام به بیمارستان",
            "نوع وسیله نقلیه",
            "شرح کامل حادثه",
            "علت اولیه حادثه",
            "حادثه شدید توقف تولید؟ (بله/خیر)",
        ]
        
        # اضافه کردن هدرها به ردیف اول
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_aligned
            cell.border = border
            
        # تنظیم عرض ستون‌ها
        for col_num in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col_num)].width = 18
        
        # اضافه کردن یک ردیف نمونه با داده‌های واقعی
        # دریافت اولین سایت موجود
        first_location = Location.objects.first()
        location_name = first_location.name if first_location else "نام سایت خود را از Sheet لیست سایت‌ها کپی کنید"
        
        # دریافت اولین جراحت موجود
        first_injury = InjuryType.objects.first()
        injury_name = first_injury.name if first_injury else "نام جراحت از Sheet لیست جراحات"
        
        # دریافت اولین کد پرسنلی موجود
        first_person = UserProfile.objects.filter(personnel_code__isnull=False).exclude(personnel_code='').first()
        personnel_code_sample = first_person.personnel_code if first_person else "کد پرسنلی از Sheet لیست پرسنل"
        
        sample_data = [
            "1403/09/15",
            "14:30",
            "human",
            location_name,
            "محل دقیق (اختیاری)",
            personnel_code_sample,
            "دستگاه برش فلز",
            injury_name,
            "دست راست",
            "بریدگی عمیق در انگشت اشاره",
            "پرسنل شرکت",
            "",
            "",
            "خیر",
            "",
            "بله",
            "14:45",
            "بله",
            "15:00",
            "آمبولانس",
            "فرد هنگام کار با دستگاه برش فلز به دلیل عدم رعایت احتیاط دچار بریدگی شدید شد",
            "عدم استفاده از دستکش ایمنی و عدم توجه کافی",
            "خیر",
        ]
        
        for col_num, value in enumerate(sample_data, 1):
            cell = ws.cell(row=2, column=col_num)
            cell.value = value
            cell.border = border
            cell.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
        
        # تنظیم ارتفاع ردیف‌ها
        ws.row_dimensions[1].height = 40
        ws.row_dimensions[2].height = 30
        
        # اضافه کردن لیست سایت‌های موجود در sheet دوم
        ws_locations = wb.create_sheet("لیست سایت‌ها")
        ws_locations.cell(row=1, column=1).value = "سایت‌های موجود در سیستم:"
        ws_locations.cell(row=1, column=1).font = Font(bold=True, size=12, color="0000FF")
        
        locations = Location.objects.all()
        for idx, location in enumerate(locations, start=2):
            ws_locations.cell(row=idx, column=1).value = location.name
            ws_locations.cell(row=idx, column=1).alignment = Alignment(horizontal="right")
        
        ws_locations.column_dimensions['A'].width = 40
        
        # اضافه کردن لیست جراحات در sheet سوم
        ws_injuries = wb.create_sheet("لیست جراحات")
        ws_injuries.cell(row=1, column=1).value = "انواع جراحات موجود در سیستم:"
        ws_injuries.cell(row=1, column=1).font = Font(bold=True, size=12, color="0000FF")
        
        injury_types = InjuryType.objects.all()
        for idx, injury in enumerate(injury_types, start=2):
            ws_injuries.cell(row=idx, column=1).value = injury.name
            ws_injuries.cell(row=idx, column=1).alignment = Alignment(horizontal="right")
        
        ws_injuries.column_dimensions['A'].width = 40
        
        # اضافه کردن لیست پرسنل (کد پرسنلی و نام)
        ws_personnel = wb.create_sheet("لیست پرسنل")
        ws_personnel.cell(row=1, column=1).value = "کد پرسنلی"
        ws_personnel.cell(row=1, column=1).font = Font(bold=True, size=12, color="0000FF")
        ws_personnel.cell(row=1, column=2).value = "نام و نام خانوادگی"
        ws_personnel.cell(row=1, column=2).font = Font(bold=True, size=12, color="0000FF")
        
        personnel = UserProfile.objects.select_related('user').filter(personnel_code__isnull=False).exclude(personnel_code='')
        for idx, person in enumerate(personnel, start=2):
            ws_personnel.cell(row=idx, column=1).value = person.personnel_code
            ws_personnel.cell(row=idx, column=1).alignment = Alignment(horizontal="center")
            ws_personnel.cell(row=idx, column=2).value = person.user.get_full_name()
            ws_personnel.cell(row=idx, column=2).alignment = Alignment(horizontal="right")
        
        ws_personnel.column_dimensions['A'].width = 20
        ws_personnel.column_dimensions['B'].width = 30
        
        # اضافه کردن لیست پیمانکاران و پرسنل آنها
        ws_contractors = wb.create_sheet("لیست پیمانکاران")
        ws_contractors.cell(row=1, column=1).value = "نام شرکت پیمانکار"
        ws_contractors.cell(row=1, column=1).font = Font(bold=True, size=12, color="FF0000")
        ws_contractors.cell(row=1, column=2).value = "کد ملی پرسنل"
        ws_contractors.cell(row=1, column=2).font = Font(bold=True, size=12, color="FF0000")
        ws_contractors.cell(row=1, column=3).value = "نام و نام خانوادگی"
        ws_contractors.cell(row=1, column=3).font = Font(bold=True, size=12, color="FF0000")
        
        contractors = Contractor.objects.prefetch_related('employees').all()
        row_idx = 2
        for contractor in contractors:
            employees = contractor.employees.filter(national_id__isnull=False).exclude(national_id='')
            if employees.exists():
                for employee in employees:
                    ws_contractors.cell(row=row_idx, column=1).value = contractor.company_name
                    ws_contractors.cell(row=row_idx, column=1).alignment = Alignment(horizontal="right")
                    ws_contractors.cell(row=row_idx, column=2).value = employee.national_id
                    ws_contractors.cell(row=row_idx, column=2).alignment = Alignment(horizontal="center")
                    ws_contractors.cell(row=row_idx, column=3).value = f"{employee.first_name} {employee.last_name}"
                    ws_contractors.cell(row=row_idx, column=3).alignment = Alignment(horizontal="right")
                    row_idx += 1
            else:
                # اگر پیمانکار پرسنلی ندارد، فقط نام شرکت را نمایش بده
                ws_contractors.cell(row=row_idx, column=1).value = contractor.company_name
                ws_contractors.cell(row=row_idx, column=1).alignment = Alignment(horizontal="right")
                ws_contractors.cell(row=row_idx, column=2).value = "بدون پرسنل ثبت شده"
                ws_contractors.cell(row=row_idx, column=2).alignment = Alignment(horizontal="center")
                ws_contractors.cell(row=row_idx, column=3).value = "-"
                ws_contractors.cell(row=row_idx, column=3).alignment = Alignment(horizontal="center")
                row_idx += 1
        
        ws_contractors.column_dimensions['A'].width = 30
        ws_contractors.column_dimensions['B'].width = 20
        ws_contractors.column_dimensions['C'].width = 30
        
        # اضافه کردن راهنما در sheet ششم
        ws_guide = wb.create_sheet("راهنما")
        guide_text = [
            ["راهنمای استفاده از فایل الگو"],
            [""],
            ["📋 فیلدهای الزامی:"],
            ["1. تاریخ حادثه: به فرمت شمسی مثل 1403/09/15 یا 1403-09-15 (هر دو فرمت قابل قبول است)"],
            ["2. ساعت حادثه: به فرمت 24 ساعته مثل 14:30"],
            ["3. نوع حادثه: فقط یکی از این سه مقدار:"],
            ["   • human = حوادث انسانی (فردی)"],
            ["   • equipment = حوادث تجهیزاتی"],
            ["   • environmental = حوادث محیط زیستی"],
            ["4. نام سایت: از Sheet 'لیست سایت‌ها' کپی کنید (دقیقاً همان نام را بنویسید)"],
            [""],
            ["📝 فیلدهای اختیاری:"],
            ["5. نام محل دقیق: نام دقیق بخش یا قسمت (می‌توانید خالی بگذارید)"],
            ["6. کد پرسنلی اشخاص درگیر: از Sheet 'لیست پرسنل شرکت' کد پرسنلی را کپی کنید"],
            ["   • برای چند نفر با کاما جدا کنید (مثل: 123,456,789)"],
            ["7. انواع جراحت: از Sheet 'لیست جراحات' کپی کنید، برای چند مورد با کاما جدا کنید"],
            ["8. نام شرکت پیمانکار: از Sheet 'لیست پیمانکاران' نام دقیق شرکت را کپی کنید"],
            ["9. کد ملی پرسنل پیمانکار: از Sheet 'لیست پیمانکاران' کد ملی را کپی کنید"],
            ["   • ابتدا نام پیمانکار را وارد کنید، سپس کد ملی پرسنل آن پیمانکار"],
            ["   • برای چند نفر با کاما جدا کنید (مثل: 1234567890,0987654321)"],
            [""],
            ["✅ مقادیر بله/خیر:"],
            ["- فقط یکی از دو مقدار 'بله' یا 'خیر' را وارد کنید"],
            ["- اگر خالی بگذارید، به صورت پیش‌فرض 'خیر' در نظر گرفته می‌شود"],
            [""],
            ["⚠️ نکات مهم:"],
            ["- نام سایت و جراحات باید دقیقاً مطابق لیست‌های موجود باشند"],
            ["- کد پرسنلی (شرکت) و کد ملی (پیمانکار) باید دقیقاً مطابق Sheets مربوطه باشند"],
            ["- برای جداسازی چند مورد از کاما (,) استفاده کنید نه نقطه‌ویرگول"],
            ["- مثال صحیح: 123,456,789 یا 1234567890,0987654321 یا بریدگی,سوختگی"],
            ["- اگر سایت، جراحت، کد پرسنلی یا کد ملی پیدا نشد، آن بخش نادیده گرفته می‌شود"],
            ["- ردیف نمونه را می‌توانید حذف کنید یا روی آن بنویسید"],
            ["- می‌توانید چندین ردیف (حادثه) را همزمان وارد کنید"],
            [""],
            ["💡 راهنمای Sheets:"],
            ["• Sheet 1: الگوی ثبت حوادث - فرم اصلی برای ورود داده"],
            ["• Sheet 2: لیست سایت‌ها - سایت‌های قابل انتخاب"],
            ["• Sheet 3: لیست جراحات - جراحات قابل انتخاب"],
            ["• Sheet 4: لیست پرسنل شرکت - کد پرسنلی و نام پرسنل شرکت"],
            ["• Sheet 5: لیست پیمانکاران - نام پیمانکار، کد ملی و نام پرسنل پیمانکار"],
            ["• Sheet 6: راهنما - این صفحه"],
        ]
        
        for row_num, row_data in enumerate(guide_text, 1):
            cell = ws_guide.cell(row=row_num, column=1)
            cell.value = row_data[0]
            if row_num == 1:
                cell.font = Font(bold=True, size=14, color="FF0000")
            elif "⚠️" in str(row_data[0]):
                cell.font = Font(bold=True, size=12, color="FF6600")
            cell.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
        
        ws_guide.column_dimensions['A'].width = 100
        
        # ذخیره در حافظه و ارسال
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="incident_import_template.xlsx"'
        
        log_user_activity(
            request.user,
            'hse_incidents',
            'download_template',
            f'دانلود الگوی ایمپورت حوادث'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"خطا در ایجاد الگوی اکسل: {e}")
        messages.error(request, f'خطا در ایجاد فایل الگو: {str(e)}')
        return redirect('hse_incidents:list_reports')


@login_required
@permission_required('hse_incidents:import_incidents')
def import_incidents_from_excel(request):
    """ایمپورت حوادث از فایل اکسل"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'فقط متد POST مجاز است'}, status=405)
    
    if 'excel_file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': 'فایل اکسل ارسال نشده است'}, status=400)
    
    excel_file = request.FILES['excel_file']
    
    # بررسی پسوند فایل
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        return JsonResponse({'status': 'error', 'message': 'فرمت فایل باید اکسل (.xlsx یا .xls) باشد'}, status=400)
    
    try:
        # خواندن فایل اکسل
        df = pd.read_excel(excel_file, sheet_name=0)
        
        # چاپ تمام ستون‌ها برای دیباگ
        logger.info(f"ستون‌های موجود در فایل: {list(df.columns)}")
        print(f"📋 ستون‌های فایل اکسل: {list(df.columns)}")
        
        # بررسی وجود ستون‌های لازم
        required_columns = [
            'تاریخ حادثه (1403/09/15)',
            'ساعت حادثه (14:30)',
            'نوع حادثه (human/equipment/environmental)',
            'نام سایت',
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"❌ ستون‌های گمشده: {missing_columns}")
            return JsonResponse({
                'status': 'error',
                'message': f'ستون‌های الزامی در فایل وجود ندارند: {", ".join(missing_columns)}',
                'available_columns': list(df.columns),
                'missing_columns': missing_columns
            }, status=400)
        
        # دریافت پروفایل کاربر
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'پروفایل کاربری یافت نشد'}, status=400)
        
        # متغیرهای شمارش
        success_count = 0
        error_count = 0
        errors = []
        
        # پردازش هر ردیف
        for index, row in df.iterrows():
            row_number = index + 2  # +2 برای header و شروع از 1
            
            try:
                # بررسی خالی بودن ردیف
                if pd.isna(row['تاریخ حادثه (1403/09/15)']) or pd.isna(row['ساعت حادثه (14:30)']):
                    logger.debug(f"ردیف {row_number} خالی است، رد شد")
                    continue
                
                logger.info(f"شروع پردازش ردیف {row_number}")
                
                # پردازش تاریخ
                date_str = str(row['تاریخ حادثه (1403/09/15)']).strip()
                date_str = persian_to_english_numbers(date_str)
                # پشتیبانی از هر دو فرمت / و -
                separator = '/' if '/' in date_str else '-'
                date_parts = date_str.split(separator)
                incident_date = jdatetime.date(
                    int(date_parts[0]),
                    int(date_parts[1]),
                    int(date_parts[2])
                ).togregorian()
                
                # پردازش ساعت
                time_str = str(row['ساعت حادثه (14:30)']).strip()
                if ':' in time_str:
                    time_parts = time_str.split(':')
                    incident_time = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:00"
                else:
                    incident_time = "00:00:00"
                
                # نوع حادثه
                incident_type = str(row['نوع حادثه (human/equipment/environmental)']).strip().lower()
                if incident_type not in ['human', 'equipment', 'environmental']:
                    errors.append(f"ردیف {row_number}: نوع حادثه نامعتبر است")
                    error_count += 1
                    continue
                
                # سایت
                location_name = str(row['نام سایت']).strip()
                try:
                    location = Location.objects.get(name=location_name)
                except Location.DoesNotExist:
                    errors.append(f"ردیف {row_number}: سایت '{location_name}' یافت نشد")
                    error_count += 1
                    continue
                
                # محل دقیق (اختیاری)
                section = None
                if not pd.isna(row.get('نام محل دقیق (اختیاری)')):
                    section_name = str(row['نام محل دقیق (اختیاری)']).strip()
                    if section_name:
                        try:
                            section = LocationSection.objects.get(location=location, section=section_name)
                        except LocationSection.DoesNotExist:
                            pass  # اگر نباشد، None می‌ماند
                
                # بررسی فیلدهای الزامی
                involved_equipment = str(row.get('تجهیزات مرتبط', '')).strip()
                if not involved_equipment or involved_equipment == 'nan':
                    involved_equipment = 'نامشخص'
                
                affected_body_part = str(row.get('عضو آسیب دیده', '')).strip()
                if not affected_body_part or affected_body_part == 'nan':
                    affected_body_part = 'نامشخص'
                
                damage_description = str(row.get('شرح آسیب', '')).strip()
                if not damage_description or damage_description == 'nan':
                    damage_description = 'نامشخص'
                
                related_entity = str(row.get('نوع ارتباط', '')).strip()
                if not related_entity or related_entity == 'nan':
                    related_entity = 'نامشخص'
                
                full_description = str(row.get('شرح کامل حادثه', '')).strip()
                if not full_description or full_description == 'nan':
                    full_description = 'نامشخص'
                
                initial_cause = str(row.get('علت اولیه حادثه', '')).strip()
                if not initial_cause or initial_cause == 'nan':
                    initial_cause = 'در حال بررسی'
                
                logger.debug(f"ردیف {row_number}: تاریخ={incident_date}, نوع={incident_type}, سایت={location.name}")
                
                # ایجاد گزارش حادثه
                incident = IncidentReport.objects.create(
                    incident_date=incident_date,
                    incident_time=incident_time,
                    incident_type=incident_type,
                    location=location,
                    section=section,
                    involved_equipment=involved_equipment,
                    affected_body_part=affected_body_part,
                    damage_description=damage_description,
                    related_entity=related_entity,
                    full_description=full_description,
                    initial_cause=initial_cause,
                    report_author=user_profile,
                    is_severe_production_stoppage=str(row.get('حادثه شدید توقف تولید؟ (بله/خیر)', 'خیر')).strip() == 'بله',
                    fire_truck_needed=str(row.get('آتش‌نشانی اعزام شد؟ (بله/خیر)', 'خیر')).strip() == 'بله',
                    ambulance_needed=str(row.get('آمبولانس اعزام شد؟ (بله/خیر)', 'خیر')).strip() == 'بله',
                    hospitalized=str(row.get('به بیمارستان اعزام شد؟ (بله/خیر)', 'خیر')).strip() == 'بله',
                )
                
                logger.info(f"ردیف {row_number}: حادثه با ID {incident.id} ایجاد شد")
                
                # پردازش اشخاص درگیر (M2M)
                # بررسی با نام ستون جدید (کد پرسنلی)
                personnel_codes_col = None
                for col_name in ['کد پرسنلی اشخاص درگیر (جدا با کاما)', 'کد پرسنلی  اشخاص درگیر (جدا با کاما)']:
                    if col_name in df.columns and not pd.isna(row.get(col_name)):
                        personnel_codes_col = col_name
                        break
                
                if personnel_codes_col:
                    personnel_codes_str = str(row[personnel_codes_col]).strip()
                    logger.info(f"ردیف {row_number}: کد پرسنلی اشخاص = '{personnel_codes_str}'")
                    print(f"👤 ردیف {row_number}: پردازش کد پرسنلی اشخاص: {personnel_codes_str}")
                    
                    if personnel_codes_str and personnel_codes_str != 'nan':
                        # جداسازی با کاما (,)
                        personnel_codes = personnel_codes_str.split(',')
                        for pc in personnel_codes:
                            pc = pc.strip()
                            if pc and pc != 'nan':
                                try:
                                    profile = UserProfile.objects.get(personnel_code=pc)
                                    incident.involved_person.add(profile)
                                    logger.info(f"✅ شخص با کد پرسنلی {pc} اضافه شد: {profile.user.get_full_name()}")
                                    print(f"   ✅ افزوده شد: {profile.user.get_full_name()} (کد پرسنلی: {pc})")
                                except UserProfile.DoesNotExist:
                                    logger.warning(f"❌ شخصی با کد پرسنلی {pc} یافت نشد")
                                    print(f"   ❌ کد پرسنلی {pc} در سیستم یافت نشد")
                else:
                    logger.debug(f"ردیف {row_number}: کد پرسنلی اشخاص خالی است یا وجود ندارد")
                
                # پردازش انواع جراحت (M2M)
                injury_col = 'انواع جراحت (جدا با کاما)'
                if injury_col in df.columns and not pd.isna(row.get(injury_col)):
                    injury_names_str = str(row[injury_col]).strip()
                    logger.info(f"ردیف {row_number}: انواع جراحت = '{injury_names_str}'")
                    print(f"🩹 ردیف {row_number}: پردازش انواع جراحت: {injury_names_str}")
                    
                    if injury_names_str and injury_names_str != 'nan':
                        # جداسازی با کاما (,)
                        injury_names = injury_names_str.split(',')
                        for injury_name in injury_names:
                            injury_name = injury_name.strip()
                            if injury_name and injury_name != 'nan':
                                injury_type, created = InjuryType.objects.get_or_create(name=injury_name)
                                incident.injury_type.add(injury_type)
                                action = "ایجاد و افزوده شد" if created else "افزوده شد"
                                logger.info(f"✅ جراحت '{injury_name}' {action}")
                                print(f"   ✅ {injury_name} ({action})")
                
                # پیمانکار (اختیاری)
                contractor_col = 'نام شرکت پیمانکار (اختیاری)'
                contractor_obj = None
                if contractor_col in df.columns and not pd.isna(row.get(contractor_col)):
                    contractor_name = str(row[contractor_col]).strip()
                    if contractor_name and contractor_name != 'nan':
                        try:
                            contractor_obj = Contractor.objects.get(company_name=contractor_name)
                            incident.related_contractor = contractor_obj
                            incident.save()
                            logger.info(f"✅ پیمانکار '{contractor_name}' اضافه شد")
                            print(f"🏢 پیمانکار افزوده شد: {contractor_name}")
                        except Contractor.DoesNotExist:
                            logger.warning(f"❌ پیمانکار '{contractor_name}' در سیستم یافت نشد")
                            print(f"   ❌ پیمانکار '{contractor_name}' یافت نشد")
                
                # پرسنل پیمانکار (اختیاری)
                contractor_personnel_col = 'کد ملی پرسنل پیمانکار (جدا با کاما)'
                if contractor_personnel_col in df.columns and not pd.isna(row.get(contractor_personnel_col)):
                    contractor_personnel_str = str(row[contractor_personnel_col]).strip()
                    logger.info(f"ردیف {row_number}: کد ملی پرسنل پیمانکار = '{contractor_personnel_str}'")
                    print(f"👷 ردیف {row_number}: پردازش پرسنل پیمانکار: {contractor_personnel_str}")
                    
                    if contractor_personnel_str and contractor_personnel_str != 'nan':
                        if not contractor_obj:
                            logger.warning(f"⚠️ برای افزودن پرسنل پیمانکار، ابتدا باید نام پیمانکار را وارد کنید")
                            print(f"   ⚠️ نام پیمانکار مشخص نیست، پرسنل اضافه نمی‌شود")
                        else:
                            contractor_personnel_codes = contractor_personnel_str.split(',')
                            for national_id in contractor_personnel_codes:
                                national_id = national_id.strip()
                                if national_id and national_id != 'nan':
                                    try:
                                        employee = Employee.objects.get(
                                            contractor=contractor_obj,
                                            national_id=national_id
                                        )
                                        incident.related_contractor_employees.add(employee)
                                        employee_name = f"{employee.first_name} {employee.last_name}"
                                        logger.info(f"✅ پرسنل پیمانکار با کد ملی {national_id} اضافه شد: {employee_name}")
                                        print(f"   ✅ افزوده شد: {employee_name} (کد ملی: {national_id})")
                                    except Employee.DoesNotExist:
                                        logger.warning(f"❌ پرسنل پیمانکار با کد ملی {national_id} در پیمانکار '{contractor_obj.company_name}' یافت نشد")
                                        print(f"   ❌ کد ملی {national_id} در پیمانکار یافت نشد")
                
                # زمان‌های اضطراری
                if incident.fire_truck_needed and not pd.isna(row.get('ساعت رسیدن آتش‌نشانی')):
                    time_str = str(row['ساعت رسیدن آتش‌نشانی']).strip()
                    if ':' in time_str:
                        time_parts = time_str.split(':')
                        incident.fire_truck_arrival_time = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:00"
                
                if incident.ambulance_needed and not pd.isna(row.get('ساعت رسیدن آمبولانس')):
                    time_str = str(row['ساعت رسیدن آمبولانس']).strip()
                    if ':' in time_str:
                        time_parts = time_str.split(':')
                        incident.ambulance_arrival_time = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:00"
                
                if incident.hospitalized:
                    if not pd.isna(row.get('ساعت اعزام به بیمارستان')):
                        time_str = str(row['ساعت اعزام به بیمارستان']).strip()
                        if ':' in time_str:
                            time_parts = time_str.split(':')
                            incident.hospitalized_time = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:00"
                    
                    if not pd.isna(row.get('نوع وسیله نقلیه')):
                        incident.transportation_type = str(row['نوع وسیله نقلیه']).strip()
                
                incident.save()
                success_count += 1
                
                # ارسال نوتیفیکیشن
                try:
                    notify_incident_report_created(incident)
                except Exception as notif_error:
                    logger.warning(f"خطا در ارسال نوتیفیکیشن برای حادثه {incident.id}: {notif_error}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"ردیف {row_number}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"خطا در پردازش ردیف {row_number}: {e}", exc_info=True)
                # چاپ در کنسول برای دیباگ
                print(f"❌ {error_msg}")
        
        # لاگ فعالیت
        log_user_activity(
            request.user,
            'hse_incidents',
            'import_excel',
            f'ایمپورت {success_count} حادثه از اکسل - {error_count} خطا'
        )
        
        # پاسخ
        response_data = {
            'status': 'success' if success_count > 0 else 'error',
            'message': f'تعداد {success_count} حادثه با موفقیت ایمپورت شد.',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10] if errors else [],  # فقط 10 خطای اول
        }
        
        if error_count > 0:
            response_data['message'] += f' تعداد {error_count} ردیف با خطا مواجه شد.'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"خطا در ایمپورت اکسل: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در پردازش فایل: {str(e)}'
        }, status=500)