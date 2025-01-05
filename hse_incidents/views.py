# views.py (در اپلیکیشن hse_incidents)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import IncidentReport, InjuryType
from accounts.models import UserProfile
from django.contrib import messages
from django.http import JsonResponse
from contractor_management.models import Contractor
from datetime import datetime
import jdatetime
from django.db.models import Q
import json
from django.http import HttpResponse
import pandas as pd
from io import BytesIO
from django.utils import timezone

@login_required
def report_incident(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "پروفایل کاربری شما یافت نشد. لطفا با مدیر سیستم تماس بگیرید.")
        return render(request, 'hse_incidents/no_userprofile.html')

    if request.method == 'POST':
        incident_date_str = request.POST.get('incident_date')
        incident_time = request.POST.get('incident_time')
        incident_location = request.POST.get('incident_location')
        involved_person_ids = request.POST.getlist('involved_person')
        involved_equipment = request.POST.get('involved_equipment')
        injury_type_ids = request.POST.getlist('injury_type')
        affected_body_part = request.POST.get('affected_body_part')
        damage_description = request.POST.get('damage_description')
        related_entity = request.POST.get('related_entity')
        related_contractor_id = request.POST.get('related_contractor')
        fire_truck_needed = request.POST.get('fire_truck_needed') == 'on'
        ambulance_needed = request.POST.get('ambulance_needed') == 'on'
        hospitalized = request.POST.get('hospitalized') == 'on'
        transportation_type = request.POST.get('transportation_type')
        full_description = request.POST.get('full_description')
        initial_cause = request.POST.get('initial_cause')
        try:
            # تبدیل تاریخ شمسی به میلادی
            incident_date_parts = list(map(int, incident_date_str.split('-')))
            incident_date_gregorian = jdatetime.date(incident_date_parts[0], incident_date_parts[1], incident_date_parts[2]).togregorian()
            incident_date = incident_date_gregorian
            incident = IncidentReport.objects.create(
                incident_date=incident_date,
                incident_time=incident_time,
                incident_location=incident_location,
                involved_equipment=involved_equipment,
                affected_body_part=affected_body_part,
                damage_description=damage_description,
                related_entity=related_entity,
                fire_truck_needed=fire_truck_needed,
                ambulance_needed=ambulance_needed,
                hospitalized=hospitalized,
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
            messages.success(request, "گزارش حادثه با موفقیت ثبت شد.")
            return redirect('hse_incidents:incident_success')

        except Exception as e:
            messages.error(request, f"خطا در ثبت گزارش: {e}")
            return render(request, 'hse_incidents/incident_report_form.html')
    return render(request, 'hse_incidents/incident_report_form.html')

def incident_success(request):
    return render(request, 'hse_incidents/incident_success.html')
def get_injury_types_ajax(request):
    injury_types = []
    search_term = request.GET.get('term', '')
    if search_term:
       injury_types = InjuryType.objects.filter(Q(name__icontains=search_term)).values("id","name")
    else:
       injury_types = InjuryType.objects.values("id","name")
    return JsonResponse(list(injury_types), safe=False)

@login_required
def list_reports(request):
    """
    ویو لیست گزارشات با قابلیت جستجو.
    """
    reports = IncidentReport.objects.all()
      # فیلتر پیشرفته
    search_term = request.GET.get('search', '')
    if search_term:
        reports = reports.filter(
            Q(incident_location__icontains=search_term) |
            Q(affected_body_part__icontains=search_term) |
            Q(damage_description__icontains=search_term) |
            Q(full_description__icontains=search_term) |
            Q(initial_cause__icontains=search_term) |
            Q(report_author__user__first_name__icontains=search_term) |
            Q(report_author__user__last_name__icontains=search_term)
        )

    incident_date_start = request.GET.get('incident_date_start')
    incident_date_end = request.GET.get('incident_date_end')

    if incident_date_start:
        try:
            incident_date_start_date_parts = list(map(int, incident_date_start.split('-')))
            incident_date_start_date_gregorian = jdatetime.date(incident_date_start_date_parts[0],incident_date_start_date_parts[1], incident_date_start_date_parts[2]).togregorian()
            incident_date_start_date = incident_date_start_date_gregorian
            reports = reports.filter(incident_date__gte=incident_date_start_date)
        except:
             pass

    if incident_date_end:
        try:
              incident_date_end_date_parts = list(map(int, incident_date_end.split('-')))
              incident_date_end_date_gregorian = jdatetime.date(incident_date_end_date_parts[0], incident_date_end_date_parts[1],incident_date_end_date_parts[2]).togregorian()
              incident_date_end_date = incident_date_end_date_gregorian
              reports = reports.filter(incident_date__lte=incident_date_end_date)
        except:
              pass

    data = []
    for report in reports:
        injury_types = ", ".join([str(injury_type) for injury_type in report.injury_type.all()])
        involved_persons = ", ".join([str(person) for person in report.involved_person.all()])
        incident_date_shamsi = jdatetime.date.fromgregorian(date=report.incident_date).strftime('%Y/%m/%d')


        data.append({
            'id': report.id,
            'incident_date': incident_date_shamsi,  # تاریخ شمسی
            'incident_time': str(report.incident_time),
             'incident_location': report.incident_location,
            'involved_persons': involved_persons,
           })
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'reports':data})
    return render(request, 'hse_incidents/incident_list.html', {'reports': reports,
        'search_term': search_term,
        'incident_date_start': incident_date_start,
        'incident_date_end': incident_date_end,
    })


@login_required
def report_details(request, report_id):
    """
    ویو صفحه جزئیات یک گزارش.
    """
    report = get_object_or_404(IncidentReport, id=report_id)
    return render(request, 'hse_incidents/report_details.html', {'report': report})

@login_required
def export_reports_excel(request):
    """
    ویو برای خروجی اکسل گزارشات.
    """
    reports = IncidentReport.objects.all()
  # فیلتر پیشرفته
    search_term = request.GET.get('search', '')
    if search_term:
        reports = reports.filter(
            Q(incident_location__icontains=search_term) |
            Q(affected_body_part__icontains=search_term) |
            Q(damage_description__icontains=search_term) |
            Q(full_description__icontains=search_term) |
            Q(initial_cause__icontains=search_term) |
            Q(report_author__user__first_name__icontains=search_term) |
            Q(report_author__user__last_name__icontains=search_term)
        )

    incident_date_start = request.GET.get('incident_date_start')
    incident_date_end = request.GET.get('incident_date_end')

    if incident_date_start:
        try:
            incident_date_start_date_parts = list(map(int, incident_date_start.split('-')))
            incident_date_start_date_gregorian = jdatetime.date(incident_date_start_date_parts[0],incident_date_start_date_parts[1], incident_date_start_date_parts[2]).togregorian()
            incident_date_start_date = incident_date_start_date_gregorian
            reports = reports.filter(incident_date__gte=incident_date_start_date)
        except:
             pass


    if incident_date_end:
        try:
              incident_date_end_date_parts = list(map(int, incident_date_end.split('-')))
              incident_date_end_date_gregorian = jdatetime.date(incident_date_end_date_parts[0], incident_date_end_date_parts[1],incident_date_end_date_parts[2]).togregorian()
              incident_date_end_date = incident_date_end_date_gregorian
              reports = reports.filter(incident_date__lte=incident_date_end_date)
        except:
            pass

    data = []
    for report in reports:
        injury_types = ", ".join([str(injury_type) for injury_type in report.injury_type.all()])
        involved_persons = ", ".join([str(person) for person in report.involved_person.all()])
        report_date = timezone.make_naive(report.report_date)
        data.append({
             'تاریخ وقوع حادثه': jdatetime.date.fromgregorian(date=report.incident_date).strftime('%Y/%m/%d'),
            'ساعت وقوع حادثه': report.incident_time,
            'محل وقوع حادثه': report.incident_location,
            'شخص/اشخاص مرتبط با حادثه': involved_persons,
            'تجهیزات مرتبط با حادثه': report.involved_equipment,
            'نوع جراحت': injury_types,
            'عضو آسیب دیده': report.affected_body_part,
            'شرح آسیب وارده': report.damage_description,
            'نوع ارتباط': report.related_entity,
            'پیمانکار': report.related_contractor.name if report.related_contractor else '',
            'خودرو آتش نشانی اعزام گردید؟': report.fire_truck_needed,
            'آمبولانس اعزام گردید؟': report.ambulance_needed,
            'فرد حادثه به بیمارستان اعزام گردید؟': report.hospitalized,
            'نوع وسیله نقلیه جهت اعزام': report.transportation_type,
            'شرح کامل حادثه': report.full_description,
            'علت وقوع حادثه': report.initial_cause,
            'فرد گزارش دهنده': report.report_author,
            'تاریخ ثبت گزارش': jdatetime.datetime.fromgregorian(datetime=report_date).strftime('%Y/%m/%d'),
             'شیفت ثبت گزارش': report.report_shift,
        })
    df = pd.DataFrame(data)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter', engine_kwargs={'options': {'strings_to_urls': False}}) as writer:
        df.to_excel(writer, sheet_name='گزارشات', index=False)
        writer.close()
    buffer.seek(0)

    response = HttpResponse(
       buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=reports.xlsx'
    return response