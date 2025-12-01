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
    return render(request, 'hse_incidents/report_details.html', {'report': report, 'form': form,'hse_completion':hse_completion})


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