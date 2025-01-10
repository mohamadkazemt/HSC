from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from permissions.utils import permission_required
from .models import IncidentReport, InjuryType
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


@permission_required("incident_report")
@login_required
def report_incident(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "پروفایل کاربری شما یافت نشد. لطفا با مدیر سیستم تماس بگیرید.")
        return render(request, 'hse_incidents/incident_report_form.html')

    locations = Location.objects.all()
    sections = LocationSection.objects.all()

    if request.method == 'POST':
        incident_date_str = request.POST.get('incident_date')
        incident_time = request.POST.get('incident_time')
        location_id = request.POST.get('location')
        section_id = request.POST.get('section')

        involved_person_ids = request.POST.getlist('involved_person')
        involved_equipment = request.POST.get('involved_equipment')
        injury_type_ids = request.POST.getlist('injury_type')
        affected_body_part = request.POST.get('affected_body_part')
        damage_description = request.POST.get('damage_description')
        related_entity = request.POST.get('related_entity')
        related_contractor_id = request.POST.get('related_contractor')
        related_contractor_employees_ids = request.POST.getlist('related_contractor_employees')
        fire_truck_needed = request.POST.get('fire_truck_needed') == 'on'
        fire_truck_arrival_time = request.POST.get('fire_truck_arrival_time')
        ambulance_needed = request.POST.get('ambulance_needed') == 'on'
        ambulance_arrival_time = request.POST.get('ambulance_arrival_time')
        hospitalized = request.POST.get('hospitalized') == 'on'
        hospitalized_time = request.POST.get('hospitalized_time')
        transportation_type = request.POST.get('transportation_type')
        full_description = request.POST.get('full_description')
        initial_cause = request.POST.get('initial_cause')

        try:
            # تبدیل تاریخ شمسی به میلادی
            incident_date_parts = list(map(int, incident_date_str.split('-')))
            incident_date_gregorian = jdatetime.date(incident_date_parts[0], incident_date_parts[1],
                                                     incident_date_parts[2]).togregorian()
            incident_date = incident_date_gregorian
            # Convert empty time strings to None
            fire_truck_arrival_time = fire_truck_arrival_time if fire_truck_arrival_time else None
            ambulance_arrival_time = ambulance_arrival_time if ambulance_arrival_time else None
            hospitalized_time = hospitalized_time if hospitalized_time else None

            incident = IncidentReport.objects.create(
                incident_date=incident_date,
                incident_time=incident_time,
                location=Location.objects.get(id=location_id) if location_id else None,
                section=LocationSection.objects.get(id=section_id) if section_id else None,
                involved_equipment=involved_equipment,
                affected_body_part=affected_body_part,
                damage_description=damage_description,
                related_entity=related_entity,
                fire_truck_needed=fire_truck_needed,
                fire_truck_arrival_time=fire_truck_arrival_time,
                ambulance_needed=ambulance_needed,
                ambulance_arrival_time=ambulance_arrival_time,
                hospitalized=hospitalized,
                hospitalized_time=hospitalized_time,
                transportation_type=transportation_type,
                full_description=full_description,
                initial_cause=initial_cause,
                report_author=user_profile
            )

            if related_contractor_id:
                incident.related_contractor = Contractor.objects.get(id=related_contractor_id)
            incident.save()

            incident.involved_person.set(UserProfile.objects.filter(id__in=involved_person_ids))
            incident.injury_type.set(InjuryType.objects.filter(id__in=injury_type_ids))
            incident.related_contractor_employees.set(Employee.objects.filter(id__in=related_contractor_employees_ids))
            messages.success(request, "گزارش حادثه با موفقیت ثبت شد.")
        except Exception as e:
            messages.error(request, f"خطا در ثبت گزارش: {e}")

    return render(request, 'hse_incidents/incident_report_form.html', {'locations': locations, 'sections': sections})


@permission_required("get_injury_types_ajax")
def get_injury_types_ajax(request):
    injury_types = []
    search_term = request.GET.get('term', '')
    if search_term:
        injury_types = InjuryType.objects.filter(Q(name__icontains=search_term)).values("id", "name")
    else:
        injury_types = InjuryType.objects.values("id", "name")
    return JsonResponse(list(injury_types), safe=False)


@permission_required("list_reports")
@login_required
def list_reports(request):
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
            | Q(report_author__user__first_name__icontains=search_query)
            | Q(report_author__user__last_name__icontains=search_query)
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
                  {'reports': reports, 'search_query': search_query, 'from_date': from_date_str,
                   'to_date': to_date_str})


@permission_required("report_details")
@login_required
def report_details(request, report_id):
    report = get_object_or_404(IncidentReport, id=report_id)
    return render(request, 'hse_incidents/report_details.html', {'report': report})


@permission_required("export_reports_excel")
@login_required
def export_reports_excel(request):
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
            | Q(report_author__user__first_name__icontains=search_query)
            | Q(report_author__user__last_name__icontains=search_query)
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

    reports = reports.order_by('-incident_date')
    df_data = []
    for report in reports:
        incident_date_jalali = jdatetime.date.fromgregorian(date=report.incident_date).strftime(
            '%Y/%m/%d') if report.incident_date else ''
        df_data.append({
            'تاریخ وقوع حادثه': incident_date_jalali,
            'ساعت وقوع حادثه': report.incident_time.strftime('%H:%M') if report.incident_time else '',
            'سایت': report.location.name if report.location else '',
            'محل شناسایی آنومالی': report.section.section if report.section else '',
            'اشخاص مرتبط با حادثه': ', '.join([str(person) for person in report.involved_person.all()]),
            'تجهیزات مرتبط با حادثه': report.involved_equipment,
            'نوع جراحت': ', '.join([str(injury) for injury in report.injury_type.all()]),
            'عضو آسیب دیده': report.affected_body_part,
            'شرح آسیب وارده': report.damage_description,
            'نوع ارتباط': report.related_entity,
            'پیمانکار مرتبط': str(report.related_contractor) if report.related_contractor else '',
            'خودرو آتش نشانی': 'بله' if report.fire_truck_needed else 'خیر',
            'زمان رسیدن خودرو آتش نشانی': report.fire_truck_arrival_time.strftime(
                '%H:%M') if report.fire_truck_arrival_time else '',
            'آمبولانس اعزام شده': 'بله' if report.ambulance_needed else 'خیر',
            'زمان رسیدن آمبولانس': report.ambulance_arrival_time.strftime(
                '%H:%M') if report.ambulance_arrival_time else '',
            'اعزام به بیمارستان': 'بله' if report.hospitalized else 'خیر',
            'زمان اعزام به بیمارستان': report.hospitalized_time.strftime('%H:%M') if report.hospitalized_time else '',
            'نوع وسیله اعزام': report.transportation_type,
            'شرح کامل حادثه': report.full_description,
            'علت حادثه': report.initial_cause,
            'نویسنده گزارش': str(report.report_author)
        })
    df = pd.DataFrame(df_data)
    excel_file = BytesIO()
    writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='گزارشات حوادث', index=False)
    writer.close()
    excel_file.seek(0)
    response = HttpResponse(excel_file.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=incident_reports.xlsx'
    return response


@permission_required("report_details_pdf")
@login_required
def report_details_pdf(request, report_id):
    report = get_object_or_404(IncidentReport, id=report_id)
    user_signature_path = None
    if report.report_author and report.report_author.signature:
        user_signature_path = os.path.join(settings.MEDIA_ROOT, str(report.report_author.signature))

    title = f"گزارش حادثه شماره {report.id}"

    context = {
        'report': report,
        'title': title,
        'user_signature': user_signature_path,
    }
    html = render_to_string('hse_incidents/daily_report_pdf.html', context)
    # font_config = FontConfiguration()
    css = CSS(string='@page { size: A4; margin: 10mm; }')
    pdf_file = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(
        stylesheets=[css])  # base_url رو درست تنظیم کردیم
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="incident_report_{report.id}.pdf"'
    return response