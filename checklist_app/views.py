from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Checklist, Question, Answer
from BaseInfo.models import MiningMachine, TypeMachine
from contractor_management.models import Vehicle
from anomalis.models import (
    LocationSection, 
    AnomalyDescription, 
    Priority, 
    Anomaly,
    Anomalytype,
    CorrectiveAction,
    Location
)
from accounts.models import UserProfile
import json
from permissions.utils import permission_required
import jdatetime
from datetime import datetime, time
from urllib.parse import urlencode
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO
from difflib import SequenceMatcher
from collections import OrderedDict
from .notifications import notify_checklist_failure, notify_checklist_success
from anomalis.notifications import notify_anomaly_created

User = get_user_model()

# Create your views here.
@login_required
@permission_required("general_checklist_list")
def general_checklist_list_view(request):
    base_qs = Checklist.objects.all().order_by('-date')
    
    # دریافت پارامترهای فیلتر
    checklist_type = request.GET.get('checklist_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    shift = request.GET.get('shift', '')
    shift_group = request.GET.get('shift_group', '')
    user_q = request.GET.get('user_q', '')

    # اعمال فیلترهای نوع و تاریخ برای محاسبه گزینه‌های موجود
    qs_for_facets = base_qs
    if checklist_type:
        qs_for_facets = qs_for_facets.filter(checklist_type=checklist_type)

    if date_from:
        try:
            jalali_date = date_from.split('/')
            gregorian_date = jdatetime.date(int(jalali_date[0]), int(jalali_date[1]), int(jalali_date[2])).togregorian()
            qs_for_facets = qs_for_facets.filter(date__date__gte=gregorian_date)
        except (ValueError, IndexError):
            pass

    if date_to:
        try:
            jalali_date = date_to.split('/')
            gregorian_date = jdatetime.date(int(jalali_date[0]), int(jalali_date[1]), int(jalali_date[2])).togregorian()
            end_datetime = datetime.combine(gregorian_date, time(23, 59, 59))
            qs_for_facets = qs_for_facets.filter(date__lte=end_datetime)
        except (ValueError, IndexError):
            pass

    # محاسبه گزینه‌های موجود برای شیفت و گروه
    shift_display_map = dict(Checklist.CHECKLIST_SHIFT_CHOICES)
    # گروه‌بندی شیفت‌ها بر اساس برچسب فارسی برای حذف تکرار لیبل‌ها
    codes = list(filter(None, qs_for_facets.values_list('shift', flat=True)))
    label_to_codes = {}
    for c in codes:
        label = shift_display_map.get(c, c)
        label_to_codes.setdefault(label, set()).add(c)
    available_shifts = []
    for label, code_set in sorted(label_to_codes.items(), key=lambda x: x[0]):
        value = ",".join(sorted(code_set))  # مثل day,day2
        available_shifts.append((value, label))
    available_groups = sorted(filter(None, set(qs_for_facets.values_list('shift_group', flat=True))))

    # پیشنهاد ثبت‌کنندگان برای جستجو (حذف موارد تکراری)
    submitter_rows = qs_for_facets.values(
        'user__first_name', 'user__last_name', 'user__username', 'user__userprofile__personnel_code'
    ).distinct()
    labels_set = set()
    for r in submitter_rows:
        name = f"{(r.get('user__first_name') or '').strip()} {(r.get('user__last_name') or '').strip()}".strip()
        code = (r.get('user__userprofile__personnel_code') or '').strip()
        username = (r.get('user__username') or '').strip()
        label = name if name else username
        if code:
            label = f"{label} ({code})"
        if label:
            labels_set.add(label)
    available_submitters = sorted(labels_set)

    # حالا فیلترهای شیفت و گروه را اعمال می‌کنیم
    checklists = qs_for_facets
    if shift:
        if ',' in shift:
            checklists = checklists.filter(shift__in=shift.split(','))
        else:
            checklists = checklists.filter(shift=shift)

    if shift_group:
        checklists = checklists.filter(shift_group=shift_group)

    if user_q:
        checklists = checklists.filter(
            Q(user__first_name__icontains=user_q) |
            Q(user__last_name__icontains=user_q) |
            Q(user__username__icontains=user_q) |
            Q(user__userprofile__personnel_code__icontains=user_q)
        )

    # صفحه‌بندی
    paginator = Paginator(checklists, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # ساخت querystring برای حفظ فیلترها در صفحه‌بندی/لینک‌ها
    filters_params = {
        'checklist_type': checklist_type,
        'date_from': date_from,
        'date_to': date_to,
        'shift': shift,
        'shift_group': shift_group,
        'user_q': user_q,
    }
    filters_params = {k: v for k, v in filters_params.items() if v}
    query = urlencode(filters_params)

    context = {
        'page_obj': page_obj,
        'checklist_types': Checklist.CHECKLIST_TYPE_CHOICES,
        'available_shifts': available_shifts,
        'available_groups': available_groups,
        'available_submitters': available_submitters,
        'current_filters': {
            'checklist_type': checklist_type,
            'date_from': date_from,
            'date_to': date_to,
            'shift': shift,
            'shift_group': shift_group,
            'user_q': user_q,
        },
        'query': query,
    }
    return render(request, 'checklist_app/checklist_list.html', context)

@login_required
@permission_required("general_checklist_form")
def general_checklist_form_view(request):
    machines = MiningMachine.objects.all()
    location_sections = LocationSection.objects.all()
    contractor_vehicles = Vehicle.objects.all()
    
    context = {
        'machines': machines,
        'location_sections': location_sections,
        'contractor_vehicles': contractor_vehicles,
        'shift_choices': Checklist.CHECKLIST_SHIFT_CHOICES,
    }
    return render(request, 'checklist_app/checklist_form.html', context)

@login_required
@permission_required("general_checklist_detail")
def general_checklist_detail_view(request, pk):
    checklist = get_object_or_404(Checklist, pk=pk)
    answers = Answer.objects.filter(checklist=checklist)
    
    context = {
        'checklist': checklist,
        'answers': answers,
    }
    return render(request, 'checklist_app/checklist_detail.html', context)

@csrf_exempt
@login_required
@permission_required("get_general_questions")
@require_http_methods(["POST"])
def get_general_questions(request):
    data = json.loads(request.body)
    checklist_type = data.get('checklist_type')
    machine_id = data.get('machine_id')
    location_section_id = data.get('location_section_id')
    vehicle_id = data.get('vehicle_id')
    
    all_questions = Question.objects.all()
    questions = [q for q in all_questions if checklist_type in q.question_scopes]
    if checklist_type == 'machine' and machine_id:
        machine = MiningMachine.objects.get(id=machine_id)
        questions = [q for q in questions if machine.machine_type in q.machine_types.all()]
    elif checklist_type == 'location' and location_section_id:
        questions = [q for q in questions if int(location_section_id) in [ls.id for ls in q.location_sections.all()]]
    elif checklist_type == 'contractor_vehicle' and vehicle_id:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        questions = [q for q in questions if vehicle.vehicle_category in q.vehicle_categories]
    
    questions_data = [{
        'id': q.id,
        'text': q.text,
        'is_required': q.is_required,
        'question_type': q.question_type,
        'options': q.options.split(',') if q.options else [],
    } for q in questions]
    
    return JsonResponse({'questions': questions_data})

@login_required
@permission_required("submit_general_checklist")
@require_http_methods(["POST"])
def submit_general_checklist(request):
    data = json.loads(request.body)
    print(f"Received data: {data}")
    
    # همیشه از گروه کاری کاربر استفاده می‌کنیم
    user_profile = UserProfile.objects.get(user=request.user)
    data['shift_group'] = user_profile.group
    
    checklist = Checklist.objects.create(
        user=request.user,
        checklist_type=data['checklist_type'],
        machine_id=data.get('machine_id'),
        location_section_id=data.get('location_section_id'),
        contractor_vehicle_id=data.get('vehicle_id'),
        shift=data['shift'],
        shift_group=data['shift_group']
    )
    
    has_unacceptable_answers = False
    unacceptable_answers = []
    
    for answer_data in data['answers']:
        print(f"Processing answer: {answer_data}")
        question = Question.objects.get(id=answer_data['question_id'])
        answer = Answer.objects.create(
            checklist=checklist,
            question=question,
            answer_text=answer_data.get('answer_text'),
            selected_option=answer_data.get('selected_option'),
            description=answer_data.get('description')
        )
        
        # بررسی پاسخ‌های غیرقابل قبول
        if question.question_type == 'option' and question.unacceptable_options:
            unacceptable_list = [opt.strip() for opt in question.unacceptable_options.split(',')]
            if answer.selected_option in unacceptable_list:
                print(f"Unacceptable answer found: {answer.selected_option}")
                has_unacceptable_answers = True
                unacceptable_answers.append(answer)
    
    # اگر پاسخ غیرقابل قبول وجود دارد، آنومالی ایجاد می‌شود
    if has_unacceptable_answers:
        print(f"Found {len(unacceptable_answers)} unacceptable answers")
        notify_checklist_failure(checklist, unacceptable_answers=unacceptable_answers, actor=request.user)
        return JsonResponse({
            'status': 'failure_detected',
            'checklist_id': checklist.id,
            'unacceptable_answers': [{'id': a.id, 'text': a.question.text} for a in unacceptable_answers]
        })
    
    notify_checklist_success(checklist, actor=request.user)
    return JsonResponse({'status': 'success', 'checklist_id': checklist.id})

@login_required
@permission_required("create_anomaly_from_failure")
@require_http_methods(["POST"])
def create_anomaly_from_failure_view(request):
    data = json.loads(request.body)
    checklist = get_object_or_404(Checklist, id=data['checklist_id'])
    followup_user = get_object_or_404(User, id=data['followup_id'])
    followup_profile = UserProfile.objects.get(user=followup_user)
    
    # دریافت تمام پاسخ‌های غیرقابل قبول برای این چک‌لیست
    unacceptable_answers = []
    for answer in Answer.objects.filter(checklist=checklist):
        question = answer.question
        if question.question_type == 'option' and question.unacceptable_options:
            unacceptable_list = [opt.strip() for opt in question.unacceptable_options.split(',')]
            if answer.selected_option in unacceptable_list:
                unacceptable_answers.append(answer)
    
    anomalies_created = []
    for answer in unacceptable_answers:
        try:
            question = answer.question
            # استفاده از نوع آنومالی پیش‌فرض سوال یا ایجاد یک نوع پیش‌فرض
            anomaly_type = question.anomaly_type or Anomalytype.objects.get_or_create(
                type="چک‌لیست",
                defaults={'description': 'آنومالی ناشی از چک‌لیست'}
            )[0]

            # استفاده از شرح آنومالی پیش‌فرض سوال یا ایجاد یک شرح جدید
            anomaly_description = question.default_anomaly_description or AnomalyDescription.objects.create(
                description=f"پاسخ غیرقابل قبول به سوال: {question.text}\nپاسخ: {answer.selected_option}",
                anomalytype=anomaly_type,
                hse_type=question.hse_type or 'S'  # استفاده از نوع HSE پیش‌فرض سوال یا Safety
            )

            # ایجاد عملیات اصلاحی
            corrective_action = CorrectiveAction.objects.create(
                anomali_type=anomaly_description,
                description=question.default_corrective_action or "نیاز به بررسی و اقدام اصلاحی"
            )

            # تعیین اولویت
            priority = question.default_priority_on_fail or Priority.objects.get_or_create(
                priority="متوسط",
                defaults={'priority': 'متوسط'}
            )[0]

            # تعیین location و section
            if checklist.checklist_type == 'location' and checklist.location_section:
                location = checklist.location_section.location
                section = checklist.location_section
            elif checklist.checklist_type == 'machine' and checklist.machine:
                # برای ماشین‌آلات، از location_sections سوال استفاده می‌کنیم
                location_sections = question.location_sections.all()
                if location_sections.exists():
                    location = location_sections.first().location
                    section = location_sections.first()
                else:
                    # اگر سوال location_sections نداشت، از location_section پیش‌فرض استفاده می‌کنیم
                    default_section = LocationSection.objects.filter(section__icontains='ماشین‌آلات').first()
                    if default_section:
                        location = default_section.location
                        section = default_section
                    else:
                        # اگر هیچ بخش مکانی مناسب پیدا نشد، از اولین بخش مکانی استفاده می‌کنیم
                        first_section = LocationSection.objects.first()
                        if first_section:
                            location = first_section.location
                            section = first_section
                        else:
                            raise ValueError("هیچ بخش مکانی در سیستم تعریف نشده است")
            elif checklist.checklist_type == 'contractor_vehicle' and checklist.contractor_vehicle:
                # برای ماشین‌آلات پیمانکار، از location_section پیش‌فرض استفاده می‌کنیم
                default_section = LocationSection.objects.filter(section__icontains='پیمانکاران').first()
                if default_section:
                    location = default_section.location
                    section = default_section
                else:
                    # اگر بخش پیمانکاران وجود نداشت، از اولین بخش مکانی استفاده می‌کنیم
                    first_section = LocationSection.objects.first()
                    if first_section:
                        location = first_section.location
                        section = first_section
                    else:
                        raise ValueError("هیچ بخش مکانی در سیستم تعریف نشده است")
            else:
                raise ValueError("نوع چک‌لیست نامعتبر است")

            # ایجاد آنومالی
            anomaly = Anomaly.objects.create(
                location=location,
                section=section,
                anomalytype=anomaly_type,
                anomalydescription=anomaly_description,
                hse_type=question.hse_type or 'S',
                correctiveaction=corrective_action,
                created_by=UserProfile.objects.get(user=request.user),
                followup=followup_profile,
                group=followup_profile.group,
                description=f"آنومالی ایجاد شده از چک‌لیست شماره {checklist.id}\n"
                           f"سوال: {question.text}\n"
                           f"پاسخ: {answer.selected_option}\n"
                           f"توضیحات: {answer.description or ''}",
                priority=priority,
                action=False  # وضعیت اولیه ناایمن
            )
            notify_anomaly_created(anomaly, actor=request.user)
            anomalies_created.append(anomaly)

        except Exception as e:
            print(f"Error creating anomaly for answer {answer.id}: {str(e)}")
            continue
    
    if anomalies_created:
        return JsonResponse({
            'status': 'success',
            'message': f'{len(anomalies_created)} آنومالی با موفقیت ایجاد شد.'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': 'خطا در ایجاد آنومالی‌ها'
    })

@login_required
@permission_required("export_checklists_excel")
def export_general_checklists_excel(request):
    # دریافت پارامترهای فیلتر
    checklist_type = request.GET.get('checklist_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    shift = request.GET.get('shift', '')
    shift_group = request.GET.get('shift_group', '')
    user_q = request.GET.get('user_q', '')

    # کوئری اولیه
    checklists = Checklist.objects.all().order_by('-date')

    # اعمال فیلترها
    if checklist_type:
        checklists = checklists.filter(checklist_type=checklist_type)

    if date_from:
        try:
            jalali_date = date_from.split('/')
            gregorian_date = jdatetime.date(int(jalali_date[0]), int(jalali_date[1]), int(jalali_date[2])).togregorian()
            checklists = checklists.filter(date__date__gte=gregorian_date)
        except (ValueError, IndexError):
            pass

    if date_to:
        try:
            jalali_date = date_to.split('/')
            gregorian_date = jdatetime.date(int(jalali_date[0]), int(jalali_date[1]), int(jalali_date[2])).togregorian()
            end_datetime = datetime.combine(gregorian_date, time(23, 59, 59))
            checklists = checklists.filter(date__lte=end_datetime)
        except (ValueError, IndexError):
            pass

    if shift:
        if ',' in shift:
            checklists = checklists.filter(shift__in=shift.split(','))
        else:
            checklists = checklists.filter(shift=shift)

    if shift_group:
        checklists = checklists.filter(shift_group=shift_group)

    if user_q:
        checklists = checklists.filter(
            Q(user__first_name__icontains=user_q) |
            Q(user__last_name__icontains=user_q) |
            Q(user__username__icontains=user_q) |
            Q(user__userprofile__personnel_code__icontains=user_q)
        )

    # ایجاد فایل اکسل
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "چک‌لیست‌ها"

    # تنظیم استایل‌های سلول‌ها
    header_font = Font(name='B Nazanin', size=12, bold=True)
    header_fill = PatternFill(start_color='ECECFF', end_color='ECECFF', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    title_font = Font(name='B Nazanin', size=14, bold=True)
    cell_font = Font(name='B Nazanin', size=11)
    cell_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin = Side(border_style="thin", color="BBBBBB")

    # ستون‌های فایل اکسل
    headers = [
        'شماره', 'تاریخ', 'نوع چک‌لیست', 'ماشین/مکان', 'شیفت', 'گروه کاری',
        'ثبت کننده', 'سوال', 'پاسخ', 'توضیحات'
    ]

    # تنظیم عرض ستون‌ها
    column_widths = [8, 18, 16, 22, 14, 16, 22, 40, 22, 32]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # هدر بالای گزارش (نام شرکت و لوگو)
    from core.models import SiteSettings
    settings = None
    try:
        settings = SiteSettings.objects.first()
    except Exception:
        settings = None

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    ws['A1'] = f"گزارش چک‌لیست‌ها - {settings.site_name if settings else ''}"
    ws['A1'].font = title_font
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

    # درج لوگو (در صورت موجود بودن)
    if settings and settings.company_logo:
        try:
            img = XLImage(settings.company_logo.path)
            img.height = 48
            img.width = 120
            img.anchor = 'A1'
            ws.add_image(img)
        except Exception:
            pass

    # ردیف هدر جدول
    header_row = 3
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)

    # نوشتن داده‌ها
    row = header_row + 1
    for checklist in checklists:
        answers = Answer.objects.filter(checklist=checklist)
        
        # تبدیل تاریخ به شمسی
        jalali_date = jdatetime.datetime.fromgregorian(datetime=checklist.date)
        formatted_date = jalali_date.strftime('%Y/%m/%d %H:%M')

        # دریافت نام مورد مرتبط
        if checklist.checklist_type == 'machine' and checklist.machine:
            location = checklist.machine.workshop_code
        elif checklist.checklist_type == 'location' and checklist.location_section:
            location = checklist.location_section.section
        elif checklist.checklist_type == 'contractor_vehicle' and checklist.contractor_vehicle:
            location = checklist.contractor_vehicle.license_plate
        else:
            location = '-'

        # دریافت معادل فارسی شیفت
        shift_display = dict(Checklist.CHECKLIST_SHIFT_CHOICES).get(checklist.shift, checklist.shift)

        for answer in answers:
            # نوشتن داده‌های هر پاسخ
            data = [
                checklist.id,
                formatted_date,
                checklist.get_checklist_type_display(),
                location,
                shift_display,
                checklist.shift_group,
                f"{checklist.user.first_name} {checklist.user.last_name}",
                answer.question.text,
                (answer.selected_option or answer.answer_text or ''),
                (answer.description or '')
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.font = cell_font
                cell.alignment = cell_alignment

            row += 1

    # ذخیره فایل در حافظه
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    # ایجاد پاسخ HTTP
    response = HttpResponse(
        excel_file.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # تنظیم نام فایل با تاریخ شمسی
    current_jalali = jdatetime.datetime.now()
    filename = f"checklist_report_{current_jalali.strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

@login_required
@permission_required("general_checklist_detail")
def export_checklist_pdf_view(request, pk):
    checklist = get_object_or_404(Checklist, pk=pk)
    answers = Answer.objects.filter(checklist=checklist)
    context = {
        'checklist': checklist,
        'answers': answers,
    }
    # قالب چاپی HTML (کاربر می‌تواند به PDF چاپ کند)
    return render(request, 'checklist_app/checklist_pdf.html', context)

@login_required
@permission_required("get_followup_users")
def get_followup_users(request):
    try:
        # فیلتر کردن کاربران بر اساس گروه مسئول پیگیری
        users = UserProfile.objects.filter(
            user__groups__name='مسئول پیگیری',
            user__is_active=True
        ).select_related('user')
        
        users_data = [{
            'id': user.user.id,
            'name': f"{user.user.first_name} {user.user.last_name} ({user.personnel_code})"
        } for user in users]
        
        print(f"Found {len(users_data)} followup users")  # اضافه کردن لاگ
        return JsonResponse({'users': users_data})
    except Exception as e:
        print(f"Error in get_followup_users: {str(e)}")  # اضافه کردن لاگ خطا
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@permission_required("general_question_form")
def general_question_form_view(request):
    if request.method == 'POST':
        # دریافت داده‌های فرم
        data = request.POST
        
        # ایجاد سوال جدید
        question = Question.objects.create(
            question_scopes=data.getlist('question_scopes'),
            question_type=data['question_type'],
            text=data['text'],
            options=data.get('options', ''),
            unacceptable_options=data.get('unacceptable_options', ''),
            anomaly_type_id=data['anomaly_type'],
            hse_type=data['hse_type'],
            default_priority_on_fail_id=data['default_priority_on_fail'],
            default_corrective_action=data.get('default_corrective_action', ''),
            default_anomaly_description_id=data.get('default_anomaly_description', ''),
            vehicle_categories=data.getlist('vehicle_categories', [])
        )

        # تنظیم انواع ماشین
        if 'machine' in question.question_scopes:
            machine_types = data.getlist('machine_types')
            question.machine_types.set(machine_types)

        # تنظیم بخش‌های مکانی
        if 'location' in question.question_scopes:
            location_sections = data.getlist('location_sections')
            question.location_sections.set(location_sections)

        return JsonResponse({'success': True, 'message': 'سوال با موفقیت ایجاد شد'})
    
    # دریافت داده‌های مورد نیاز برای فرم
    context = {
        'machine_types': TypeMachine.objects.all(),
        'location_sections': LocationSection.objects.select_related('location').all(),
        'anomaly_types': Anomalytype.objects.all(),
        'priorities': Priority.objects.all(),
        'corrective_actions': CorrectiveAction.objects.all().values('description').distinct(),
        'anomaly_descriptions': AnomalyDescription.objects.all(),
    }
    
    return render(request, 'checklist_app/question_form.html', context)

@login_required
@permission_required("general_question_list")
def general_question_list_view(request):
    questions = Question.objects.all()
    
    # فیلترها
    search_query = request.GET.get('search', '')
    scope_filter = request.GET.get('scope', '')
    type_filter = request.GET.get('type', '')
    anomaly_type_filter = request.GET.get('anomaly_type', '')
    hse_type_filter = request.GET.get('hse_type', '')
    priority_filter = request.GET.get('priority', '')
    
    if search_query:
        questions = questions.filter(text__icontains=search_query)
    
    if scope_filter:
        questions = questions.filter(question_scope=scope_filter)
        
    if type_filter:
        questions = questions.filter(question_type=type_filter)
        
    if anomaly_type_filter:
        questions = questions.filter(anomaly_type_id=anomaly_type_filter)
        
    if hse_type_filter:
        questions = questions.filter(hse_type=hse_type_filter)
        
    if priority_filter:
        questions = questions.filter(default_priority_on_fail_id=priority_filter)
    
    # مرتب‌سازی
    sort_by = request.GET.get('sort_by', '-id')
    questions = questions.order_by(sort_by)
    
    # صفحه‌بندی
    paginator = Paginator(questions, 10)  # 10 آیتم در هر صفحه
    page = request.GET.get('page')
    questions_page = paginator.get_page(page)
    
    context = {
        'questions': questions_page,
        'anomaly_types': Anomalytype.objects.all(),
        'priorities': Priority.objects.all(),
        'search_query': search_query,
        'scope_filter': scope_filter,
        'type_filter': type_filter,
        'anomaly_type_filter': anomaly_type_filter,
        'hse_type_filter': hse_type_filter,
        'priority_filter': priority_filter,
        'sort_by': sort_by
    }
    return render(request, 'checklist_app/question_list.html', context)

@login_required
@permission_required("general_question_edit")
def general_question_edit_view(request, pk):
    question = get_object_or_404(Question, pk=pk)
    
    if request.method == 'POST':
        data = request.POST
        
        # به‌روزرسانی سوال
        question.question_scope = data['question_scope']
        question.question_type = data['question_type']
        question.text = data['text']
        question.options = data.get('options', '')
        question.unacceptable_options = data.get('unacceptable_options', '')
        question.anomaly_type_id = data['anomaly_type']
        question.hse_type = data['hse_type']
        question.default_priority_on_fail_id = data['default_priority_on_fail']
        question.default_corrective_action = data['default_corrective_action']
        question.default_anomaly_description_id = data.get('default_anomaly_description', '')

        # به‌روزرسانی نوع ماشین، بخش مکانی یا دسته‌بندی خودرو
        if data['question_scope'] == 'machine' and data.get('machine_type'):
            question.machine_type_id = data['machine_type']
            question.location_section = None
            question.vehicle_category = None
        elif data['question_scope'] == 'location' and data.get('location_section'):
            question.location_section_id = data['location_section']
            question.machine_type = None
            question.vehicle_category = None
        elif data['question_scope'] == 'contractor_vehicle' and data.get('vehicle_category'):
            question.vehicle_category = data['vehicle_category']
            question.machine_type = None
            question.location_section = None
        
        question.save()
        
        return redirect('checklist_app:general_question_list')
    
    context = {
        'question': question,
        'machine_types': TypeMachine.objects.all(),
        'location_sections': LocationSection.objects.select_related('location').all(),
        'anomaly_types': Anomalytype.objects.all(),
        'priorities': Priority.objects.all(),
        'corrective_actions': CorrectiveAction.objects.all().values('description').distinct(),
        'anomaly_descriptions': AnomalyDescription.objects.all(),
    }
    
    return render(request, 'checklist_app/question_form.html', context)

@login_required
@permission_required("general_question_delete")
@require_http_methods(["POST"])
def general_question_delete_view(request):
    data = json.loads(request.body)
    question_id = data.get('question_id')
    question_ids = data.get('question_ids')
    
    try:
        if question_id:
            # حذف تک سوال
            question = Question.objects.get(id=question_id)
            question.delete()
            return JsonResponse({'status': 'success'})
        elif question_ids:
            # حذف دسته‌جمعی
            Question.objects.filter(id__in=question_ids).delete()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'شناسه سوال مشخص نشده است'}, status=400)
    except Question.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'سوال مورد نظر یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def similar_text(a, b):
    """محاسبه میزان شباهت دو متن"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_similar_item(text, queryset, field_name='description', threshold=0.8):
    """پیدا کردن مورد مشابه در کوئری‌ست"""
    for item in queryset:
        field_value = getattr(item, field_name)
        if field_value and similar_text(text, field_value) >= threshold:
            return item
    return None

def find_all_similar_items(text, queryset, field_name='description', threshold=0.8):
    """پیدا کردن همه موارد مشابه در کوئری‌ست"""
    result = []
    for item in queryset:
        field_value = getattr(item, field_name)
        if field_value and similar_text(text, field_value) >= threshold:
            result.append(item)
    return result

@login_required
@require_http_methods(["POST"])
def import_questions_view(request):
    try:
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            return JsonResponse({'status': 'error', 'message': 'فایل اکسل انتخاب نشده است'}, status=400)
        
        print(f"Starting to process excel file: {excel_file.name}")
        
        # خواندن فایل اکسل
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # بررسی ساختار فایل
        headers = [cell.value for cell in ws[1]]
        print(f"Found headers: {headers}")
        
        required_headers = [
            'متن سوال', 'محدوده‌ها', 'نوع سوال', 'انواع ماشین', 'بخش‌های مکانی', 'دسته‌بندی‌های خودرو',
            'گزینه‌ها', 'گزینه‌های غیرقابل قبول', 'نوع آنومالی', 'حوزه HSE',
            'شرح آنومالی پیش‌فرض', 'اولویت', 'اقدام اصلاحی پیش‌فرض'
        ]
        
        missing_headers = [h for h in required_headers if h not in headers]
        if missing_headers:
            error_msg = f'ستون‌های زیر در فایل یافت نشد: {", ".join(missing_headers)}'
            print(f"Error: {error_msg}")
            return JsonResponse({
                'status': 'error',
                'message': error_msg
            }, status=400)
        
        # ایجاد نقشه ستون‌ها
        header_map = {header: idx for idx, header in enumerate(headers, 1)}
        print(f"Header map: {header_map}")
        
        # خواندن و ذخیره سوالات
        success_count = 0
        error_count = 0
        errors = []
        
        for row in range(2, ws.max_row + 1):
            try:
                print(f"\nProcessing row {row}")
                
                # خواندن داده‌های سطر
                text = ws.cell(row=row, column=header_map['متن سوال']).value
                scopes = ws.cell(row=row, column=header_map['محدوده‌ها']).value or ''
                question_type = ws.cell(row=row, column=header_map['نوع سوال']).value
                machine_types_str = ws.cell(row=row, column=header_map['انواع ماشین']).value or ''
                location_sections_str = ws.cell(row=row, column=header_map['بخش‌های مکانی']).value or ''
                vehicle_categories_str = ws.cell(row=row, column=header_map['دسته‌بندی‌های خودرو']).value or ''
                options = ws.cell(row=row, column=header_map['گزینه‌ها']).value
                unacceptable_options = ws.cell(row=row, column=header_map['گزینه‌های غیرقابل قبول']).value
                anomaly_type_name = ws.cell(row=row, column=header_map['نوع آنومالی']).value
                hse_type = ws.cell(row=row, column=header_map['حوزه HSE']).value
                anomaly_description = ws.cell(row=row, column=header_map['شرح آنومالی پیش‌فرض']).value
                priority_value = ws.cell(row=row, column=header_map['اولویت']).value
                corrective_action = ws.cell(row=row, column=header_map['اقدام اصلاحی پیش‌فرض']).value
                
                print(f"Row data: text={text}, scopes={scopes}, type={question_type}, machine_types={machine_types_str}, "
                      f"location_sections={location_sections_str}, vehicle_categories={vehicle_categories_str}, anomaly_type={anomaly_type_name}, "
                      f"hse_type={hse_type}, priority={priority_value}")
                
                # تبدیل مقادیر به فرمت مناسب
                scope_map = {'ماشین': 'machine', 'مکان': 'location', 'ماشین‌آلات پیمانکار': 'contractor_vehicle'}
                type_map = {'متنی': 'text', 'گزینه‌ای': 'option'}
                hse_map = {'H': 'H', 'S': 'S', 'E': 'E', 'Health': 'H', 'Safety': 'S', 'Environment': 'E'}
                vehicle_category_map = {'ماشین‌آلات معدنی': 'mining', 'خودروهای سبک': 'light', 'حمل و نقل': 'transportation'}
                
                # محدوده‌ها
                scope_list = [scope_map[s.strip()] for s in scopes.split(',') if s.strip() in scope_map]
                if not scope_list:
                    raise ValueError('حداقل یک محدوده معتبر باید وارد شود.')

                # انواع ماشین
                machine_type_names = [s.strip() for s in machine_types_str.split(',') if s.strip()]
                # بخش‌های مکانی
                location_section_names = [s.strip() for s in location_sections_str.split(',') if s.strip()]
                # دسته‌بندی‌های خودرو
                vehicle_category_list = [vehicle_category_map[s.strip()] for s in vehicle_categories_str.split(',') if s.strip() in vehicle_category_map]

                # سایر اعتبارسنجی‌ها
                if not question_type in type_map:
                    raise ValueError(f'نوع سوال نامعتبر: {question_type}. باید یکی از این مقادیر باشد: {", ".join(type_map.keys())}')
                if not hse_type in hse_map:
                    raise ValueError(f'نوع HSE نامعتبر: {hse_type}. باید یکی از این مقادیر باشد: {", ".join(hse_map.keys())}')
                
                # یافتن یا ساخت نوع آنومالی
                similar_anomaly_type = find_similar_item(
                    anomaly_type_name,
                    Anomalytype.objects.all(),
                    field_name='type'
                )
                if similar_anomaly_type:
                    anomaly_type = similar_anomaly_type
                else:
                    anomaly_type = Anomalytype.objects.create(type=anomaly_type_name)

                # یافتن یا ساخت شرح آنومالی
                similar_anomaly_desc = find_similar_item(
                    anomaly_description,
                    AnomalyDescription.objects.filter(anomalytype=anomaly_type),
                    field_name='description'
                )
                if similar_anomaly_desc:
                    anomaly_desc = similar_anomaly_desc
                else:
                    anomaly_desc = AnomalyDescription.objects.create(
                        description=anomaly_description,
                        anomalytype=anomaly_type,
                        hse_type=hse_map[hse_type]
                    )

                # یافتن یا ساخت اولویت مشابه
                similar_priority = find_similar_item(
                    priority_value,
                    Priority.objects.all(),
                    field_name='priority'
                )
                if similar_priority:
                    priority = similar_priority
                else:
                    priority = Priority.objects.create(priority=priority_value)

                # ایجاد سوال
                question = Question.objects.create(
                    text=text,
                    question_scopes=scope_list,
                    question_type=type_map[question_type],
                    options=options,
                    unacceptable_options=unacceptable_options,
                    anomaly_type=anomaly_type,
                    hse_type=hse_map[hse_type],
                    default_priority_on_fail=priority,
                    default_corrective_action=corrective_action,
                    default_anomaly_description=anomaly_desc,
                    is_required=True,
                    vehicle_categories=vehicle_category_list
                )
                # تنظیم انواع ماشین
                if 'machine' in scope_list and machine_type_names:
                    machine_types = []
                    for mt_name in machine_type_names:
                        similar_machine_types = find_all_similar_items(
                            mt_name,
                            TypeMachine.objects.all(),
                            field_name='name'
                        )
                        if similar_machine_types:
                            machine_types.extend(similar_machine_types)
                        else:
                            machine_types.append(TypeMachine.objects.create(name=mt_name))
                    question.machine_types.set(machine_types)
                # تنظیم بخش‌های مکانی
                if 'location' in scope_list and location_section_names:
                    location_sections = []
                    for ls_name in location_section_names:
                        similar_location_section = find_similar_item(
                            ls_name,
                            LocationSection.objects.all(),
                            field_name='section',
                            threshold=0.9
                        )
                        if similar_location_section:
                            location_sections.append(similar_location_section)
                        else:
                            default_location = Location.objects.first()
                            if not default_location:
                                default_location = Location.objects.create(
                                    name="مکان پیش‌فرض",
                                    description="مکان پیش‌فرض برای سوالات ایمپورت شده"
                                )
                            location_sections.append(LocationSection.objects.create(
                                section=ls_name,
                                location=default_location
                            ))
                    question.location_sections.set(location_sections)
                question.save()
                success_count += 1
                print(f"Successfully saved question {success_count}")
                
            except Exception as e:
                error_count += 1
                error_msg = f'خطا در سطر {row}: {str(e)}'
                print(f"Error: {error_msg}")
                errors.append(error_msg)
                continue
        
        result = {
            'status': 'success',
            'message': f'{success_count} سوال با موفقیت ایمپورت شد. {error_count} خطا رخ داد.',
            'errors': errors
        }
        print(f"Final result: {result}")
        return JsonResponse(result)
        
    except Exception as e:
        error_msg = f'خطا در پردازش فایل: {str(e)}'
        print(f"Fatal error: {error_msg}")
        return JsonResponse({
            'status': 'error',
            'message': error_msg
        }, status=500)
