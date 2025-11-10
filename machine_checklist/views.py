from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
import os

from permissions.utils import permission_required
from .models import Checklist, Question, Answer
from BaseInfo.models import MiningMachine, TypeMachine, MachineryWorkGroup
from accounts.models import UserProfile
from core.models import SiteSettings
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from datetime import datetime
import jdatetime
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from shift_manager.utils import get_current_shift_and_group  # حذف import اضافی
from dashboard.utils import log_user_activity  # اضافه کردن ایمپورت
from django.urls import reverse  # برای ساخت URL
from .notifications import notify_checklist_submission, ISSUE_OPTIONS

@permission_required("checklist_form")
def checklist_form_view(request):
    # ثبت فعالیت مشاهده فرم چک‌لیست
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده فرم چک‌لیست ماشین‌آلات',
        related_model='Checklist',
        related_object_id=None,
        url=reverse('machine_checklist:checklist_form'),
        request=request
    )
    
    machines = MiningMachine.objects.filter(is_active=True).select_related('machine_workgroup', 'machine_type')
    
    # Group machines by workgroup
    machines_by_group = {}
    
    # Get all workgroups that have active machines
    workgroups = MachineryWorkGroup.objects.filter(
        miningmachine__is_active=True
    ).distinct()
    
    for workgroup in workgroups:
        group_machines = [m for m in machines if m.machine_workgroup == workgroup]
        if group_machines:
            machines_by_group[workgroup] = group_machines
    
    # Also include machines without workgroup
    machines_without_group = [m for m in machines if m.machine_workgroup is None]
    if machines_without_group:
        machines_by_group[None] = machines_without_group
    
    return render(request, 'machine_checklist/checklist_form.html', {
        'machines_by_group': machines_by_group,
        'workgroups': workgroups
    })

@permission_required("get_questions")
def get_questions(request, machine_id):
    # ثبت فعالیت دریافت سوالات چک‌لیست
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'دریافت سوالات چک‌لیست برای ماشین شماره {machine_id}',
        related_model='Question',
        related_object_id=None,
        url=request.path,
        request=request
    )
    
    machine = get_object_or_404(MiningMachine, id=machine_id)
    questions = Question.objects.filter(machine_type=machine.machine_type)
    question_list = []
    for question in questions:
        question_list.append({
            'id': question.id,
            'text': question.text,
            'is_required': question.is_required,
            'question_type': question.question_type,
            'options': question.options,
        })
    return JsonResponse({'questions': question_list})


@csrf_exempt
def submit_checklist(request):
    if request.method == 'POST':
        machine_id = request.POST.get('machine')
        try:
            machine = MiningMachine.objects.get(id=machine_id)

            # بررسی اینکه آیا کاربر قبلاً در این روز چک‌لیستی ثبت کرده است یا خیر
            if request.user and request.user.is_authenticated:
                today = timezone.localdate() # استفاده از timezone.localdate() برای دریافت تاریخ محلی
                existing_checklist = Checklist.objects.filter(
                    user=request.user,
                    machine=machine,
                    date__date=today # فیلتر بر اساس تاریخ روز
                ).first()
                if existing_checklist:
                    return JsonResponse({'success': False, 'error': f'شما قبلاً یک چک‌لیست برای دستگاه {machine.workshop_code} در امروز ثبت کرده‌اید.'})

                current_shift, current_group = get_current_shift_and_group(request.user)
                if hasattr(request.user, 'userprofile'):
                    shift_group = request.user.userprofile.group
                else:
                    shift_group = current_group
            else:
                current_shift, current_group = get_current_shift_and_group()
                shift_group = current_group
            checklist = Checklist.objects.create(
                                               user=request.user if request.user.is_authenticated else None,
                                               machine=machine,
                                               shift=current_shift,
                                                shift_group=shift_group
                                               )
                                               
            # ثبت فعالیت ارسال چک‌لیست
            log_user_activity(
                user=request.user,
                activity_type='create',
                description=f'ثبت چک‌لیست جدید برای ماشین {machine.workshop_code}',
                related_model='Checklist',
                related_object_id=checklist.id,
                url=reverse('machine_checklist:checklist_detail', args=[checklist.id]),
                request=request
            )
            
        except MiningMachine.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'ماشین مورد نظر یافت نشد.'})

        issue_answers = []
        for key, value in request.POST.items():
            if key.startswith('answer_'):
                question_id = key.split('_')[1]
                question = get_object_or_404(Question, id=question_id)
                description = request.POST.get(f'description_{question_id}')
                answer_obj = None
                if question.question_type == 'text':
                    answer_obj = Answer.objects.create(checklist=checklist, question=question, answer_text=value,
                                          description=description)
                elif question.question_type == 'option':
                    answer_obj = Answer.objects.create(checklist=checklist, question=question, selected_option=value,
                                          description=description)

                if answer_obj and question.question_type == 'option':
                    selected = (answer_obj.selected_option or '').strip()
                    if selected in ISSUE_OPTIONS:
                        issue_answers.append(answer_obj)

        notify_checklist_submission(checklist, issues=issue_answers, actor=request.user if request.user.is_authenticated else None)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'متد نامعتبر.'})

@permission_required("checklist_list")
def checklist_list_view(request):
    # ثبت فعالیت مشاهده لیست چک‌لیست‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='مشاهده لیست چک‌لیست‌های ماشین‌آلات',
        related_model='Checklist',
        related_object_id=None,
        url=reverse('machine_checklist:checklist_list'),
        request=request
    )
    
    # دریافت فیلترها
    query = request.GET.get('q', '').strip()
    from_date_str = request.GET.get('start_date', '').strip()
    to_date_str = request.GET.get('end_date', '').strip()
    group_filter = request.GET.get('group_filter', '').strip()
    shift_filter = request.GET.get('shift_filter', '').strip()
    machine_type_filter = request.GET.get('machine_type_filter', '').strip()

    # شروع با queryset اصلی
    checklists = Checklist.objects.select_related('user', 'machine', 'machine__machine_type').prefetch_related('user__userprofile').order_by('-date')
    
    # فیلتر تاریخ (شمسی یا میلادی)
    if from_date_str:
        try:
            # بررسی فرمت: اگر فرمت شمسی است (YYYY/MM/DD)
            if '/' in from_date_str:
                from_date_parts = list(map(int, from_date_str.split('/')))
                from_date_gregorian = jdatetime.date(from_date_parts[0], from_date_parts[1], from_date_parts[2]).togregorian()
            else:
                # فرمت میلادی (YYYY-MM-DD)
                from_date_gregorian = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            from_date_gregorian = datetime.combine(from_date_gregorian, datetime.min.time())
            checklists = checklists.filter(date__gte=from_date_gregorian)
        except (ValueError, IndexError):
            pass
    
    if to_date_str:
        try:
            # بررسی فرمت: اگر فرمت شمسی است (YYYY/MM/DD)
            if '/' in to_date_str:
                to_date_parts = list(map(int, to_date_str.split('/')))
                to_date_gregorian = jdatetime.date(to_date_parts[0], to_date_parts[1], to_date_parts[2]).togregorian()
            else:
                # فرمت میلادی (YYYY-MM-DD)
                to_date_gregorian = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            to_date_gregorian = datetime.combine(to_date_gregorian, datetime.max.time())
            checklists = checklists.filter(date__lte=to_date_gregorian)
        except (ValueError, IndexError):
            pass
    
    # فیلتر جستجو
    if query:
        checklists = checklists.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__userprofile__personnel_code__icontains=query) |
            Q(machine__workshop_code__icontains=query) |
            Q(machine__machine_type__name__icontains=query)
        )
    
    # فیلتر گروه کاری
    if group_filter:
        checklists = checklists.filter(user__userprofile__group=group_filter)
    
    # فیلتر شیفت
    if shift_filter:
        checklists = checklists.filter(shift=shift_filter)
    
    # فیلتر نوع ماشین
    if machine_type_filter:
        try:
            machine_type_id = int(machine_type_filter)
            checklists = checklists.filter(machine__machine_type_id=machine_type_id)
        except ValueError:
            pass

    # داده‌های فیلتر برای نمایش در template
    groups = UserProfile.GROUP_CHOICES
    shifts = Checklist.objects.exclude(shift__isnull=True).exclude(shift='').values_list('shift', flat=True).distinct().order_by('shift')
    machine_types = TypeMachine.objects.all().order_by('name')

    # صفحه‌بندی
    page = request.GET.get('page', 1)
    paginator = Paginator(checklists, 20)  # افزایش به 20 مورد در هر صفحه
    try:
        checklists_page = paginator.page(page)
    except PageNotAnInteger:
        checklists_page = paginator.page(1)
    except EmptyPage:
        checklists_page = paginator.page(paginator.num_pages)
    
    # تبدیل تاریخ میلادی به شمسی برای نمایش در template
    from_date_display = ''
    to_date_display = ''
    if from_date_str and '-' in from_date_str:
        try:
            g_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            j_date = jdatetime.date.fromgregorian(date=g_date)
            from_date_display = j_date.strftime('%Y/%m/%d')
        except:
            from_date_display = from_date_str
    
    if to_date_str and '-' in to_date_str:
        try:
            g_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            j_date = jdatetime.date.fromgregorian(date=g_date)
            to_date_display = j_date.strftime('%Y/%m/%d')
        except:
            to_date_display = to_date_str
    
    context = {
        'checklists': checklists_page,
        'from_date': from_date_display or from_date_str,  # نمایش شمسی در template
        'to_date': to_date_display or to_date_str,  # نمایش شمسی در template
        'from_date_gregorian': from_date_str,  # برای export
        'to_date_gregorian': to_date_str,  # برای export
        'query': query,
        'group_filter': group_filter,
        'shift_filter': shift_filter,
        'machine_type_filter': machine_type_filter,
        'groups': groups,
        'shifts': shifts,
        'machine_types': machine_types,
        'total_count': paginator.count,
    }
    
    return render(request, 'machine_checklist/checklist_list.html', context)

@permission_required("checklist_detail")
def checklist_detail_view(request, checklist_id):
    # ثبت فعالیت مشاهده جزئیات چک‌لیست
    log_user_activity(
        user=request.user,
        activity_type='view',
        description=f'مشاهده جزئیات چک‌لیست شماره {checklist_id}',
        related_model='Checklist',
        related_object_id=checklist_id,
        url=reverse('machine_checklist:checklist_detail', args=[checklist_id]),
        request=request
    )
    
    checklist = get_object_or_404(Checklist, id=checklist_id)
    answers = Answer.objects.filter(checklist=checklist).select_related('question')
    
    # Calculate statistics
    option_count = sum(1 for answer in answers if answer.question.question_type == 'option')
    text_count = sum(1 for answer in answers if answer.question.question_type == 'text')
    
    return render(request, 'machine_checklist/checklist_detail.html', {
        'checklist': checklist, 
        'answers': answers,
        'option_count': option_count,
        'text_count': text_count
    })


@permission_required("export_checklists_excel")
def export_checklists_excel(request):
    # ثبت فعالیت دریافت اکسل چک‌لیست‌ها
    log_user_activity(
        user=request.user,
        activity_type='view',
        description='دریافت فایل اکسل چک‌لیست‌های ماشین‌آلات',
        related_model='Checklist',
        related_object_id=None,
        url=reverse('machine_checklist:export_checklists_excel'),
        request=request
    )
    
    # دریافت فیلترها - اگر export_all=1 باشد، همه فیلترها نادیده گرفته می‌شوند
    export_all = request.GET.get('export_all', '0') == '1'
    
    if export_all:
        # خروجی کل داده‌ها بدون فیلتر
        checklists = Checklist.objects.select_related('user', 'machine', 'machine__machine_type').prefetch_related('user__userprofile').order_by('-date')
    else:
        # استفاده از فیلترهای اعمال شده
        query = request.GET.get('q', '').strip()
        # دریافت تاریخ‌ها از GET (فرمت میلادی YYYY-MM-DD از hidden field)
        from_date_str = request.GET.get('start_date', '').strip()
        to_date_str = request.GET.get('end_date', '').strip()
        group_filter = request.GET.get('group_filter', '').strip()
        shift_filter = request.GET.get('shift_filter', '').strip()
        machine_type_filter = request.GET.get('machine_type_filter', '').strip()

        checklists = Checklist.objects.select_related('user', 'machine', 'machine__machine_type').prefetch_related('user__userprofile').order_by('-date')
        
        # اعمال فیلتر تاریخ (فرمت میلادی YYYY-MM-DD)
        if from_date_str:
            try:
                # اگر فرمت شمسی است (YYYY/MM/DD)
                if '/' in from_date_str:
                    from_date_parts = list(map(int, from_date_str.split('/')))
                    from_date_gregorian = jdatetime.date(from_date_parts[0], from_date_parts[1], from_date_parts[2]).togregorian()
                else:
                    # فرمت میلادی (YYYY-MM-DD)
                    from_date_gregorian = datetime.strptime(from_date_str, '%Y-%m-%d').date()
                from_date_gregorian = datetime.combine(from_date_gregorian, datetime.min.time())
                checklists = checklists.filter(date__gte=from_date_gregorian)
            except (ValueError, IndexError) as e:
                pass
        
        if to_date_str:
            try:
                # اگر فرمت شمسی است (YYYY/MM/DD)
                if '/' in to_date_str:
                    to_date_parts = list(map(int, to_date_str.split('/')))
                    to_date_gregorian = jdatetime.date(to_date_parts[0], to_date_parts[1], to_date_parts[2]).togregorian()
                else:
                    # فرمت میلادی (YYYY-MM-DD)
                    to_date_gregorian = datetime.strptime(to_date_str, '%Y-%m-%d').date()
                to_date_gregorian = datetime.combine(to_date_gregorian, datetime.max.time())
                checklists = checklists.filter(date__lte=to_date_gregorian)
            except (ValueError, IndexError) as e:
                pass
        
        if query:
            checklists = checklists.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__userprofile__personnel_code__icontains=query) |
                Q(machine__workshop_code__icontains=query) |
                Q(machine__machine_type__name__icontains=query)
            )
        
        if group_filter:
            checklists = checklists.filter(user__userprofile__group=group_filter)
        
        if shift_filter:
            checklists = checklists.filter(shift=shift_filter)
        
        if machine_type_filter:
            try:
                machine_type_id = int(machine_type_filter)
                checklists = checklists.filter(machine__machine_type_id=machine_type_id)
            except ValueError:
                pass


    # Get site settings
    site_settings = SiteSettings.objects.first()
    company_name = site_settings.site_name if site_settings and site_settings.site_name else "شرکت"
    
    # Create Excel workbook
    workbook = openpyxl.Workbook()

    # Define styles
    title_font = Font(name='B Nazanin', size=16, bold=True, color="FFFFFF")
    header_font = Font(name='B Nazanin', size=12, bold=True, color="FFFFFF")
    data_font = Font(name='B Nazanin', size=11)
    
    title_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Dark blue
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")  # Blue
    even_row_fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")  # Light gray
    
    center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    right_alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
    
    # Border style
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Group checklists by machine type
    grouped_checklists = {}
    for checklist in checklists:
        if checklist.machine and checklist.machine.machine_type:
            machine_type = checklist.machine.machine_type
            if machine_type not in grouped_checklists:
                grouped_checklists[machine_type] = []
            grouped_checklists[machine_type].append(checklist)
        else:
            # Handle checklists without machine or machine_type
            if None not in grouped_checklists:
                grouped_checklists[None] = []
            grouped_checklists[None].append(checklist)

    for machine_type, checklists_for_type in grouped_checklists.items():
        if checklists_for_type: # Only create sheet if there are checklists for this machine type
            sheet_name = machine_type.name if machine_type else "بدون نوع"
            # Limit sheet name to 31 characters (Excel limit)
            if len(sheet_name) > 31:
                sheet_name = sheet_name[:28] + "..."
            sheet = workbook.create_sheet(title=sheet_name)

            # Fetch all unique questions for headers for this machine type
            if machine_type:
                questions = Question.objects.filter(machine_type=machine_type).order_by('id')
            else:
                questions = Question.objects.none()
            
            # Prepare headers
            headers = [
                "کاربر", "کد پرسنلی", "ماشین", "نوع ماشین", "تاریخ", "شیفت", "گروه شیفت"
            ]
            question_headers = [question.text for question in questions]
            headers.extend(question_headers)
            headers.extend(["توضیحات " + q.text for q in questions])
            
            num_cols = len(headers)
            
            # Add company header with logo
            header_row = 1
            sheet.row_dimensions[header_row].height = 50
            
            # Add logo if available (in column A)
            logo_added = False
            if site_settings and site_settings.company_logo:
                try:
                    logo_path = site_settings.company_logo.path
                    if os.path.exists(logo_path):
                        logo_img = XLImage(logo_path)
                        # Resize logo to fit nicely
                        logo_img.height = 45
                        logo_img.width = 45
                        # Place logo in column A
                        sheet.add_image(logo_img, f'A{header_row}')
                        # Set column width for logo
                        sheet.column_dimensions['A'].width = 12
                        logo_added = True
                except Exception:
                    pass
            
            # Title row (merge from B to last column if logo exists, otherwise from A)
            title_start_col = 'B' if logo_added else 'A'
            title_cell = sheet.cell(row=header_row, column=2 if logo_added else 1, value=f"گزارش چک‌لیست ماشین‌آلات - {company_name}")
            title_cell.font = title_font
            title_cell.fill = title_fill
            title_cell.alignment = center_alignment
            sheet.merge_cells(f'{title_start_col}{header_row}:{get_column_letter(num_cols)}{header_row}')
            
            # Machine type subtitle
            header_row += 1
            machine_type_name = machine_type.name if machine_type else "بدون نوع"
            subtitle_cell = sheet.cell(row=header_row, column=1, value=f"نوع ماشین: {machine_type_name}")
            subtitle_cell.font = Font(name='B Nazanin', size=12, bold=True)
            subtitle_cell.fill = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid")
            subtitle_cell.alignment = right_alignment
            sheet.merge_cells(f'A{header_row}:{get_column_letter(num_cols)}{header_row}')
            sheet.row_dimensions[header_row].height = 25
            
            # Headers row (always start from column A for consistency)
            header_row += 1
            for col_idx, header in enumerate(headers, start=1):
                cell = sheet.cell(row=header_row, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
                cell.border = thin_border
            # If logo was added, fill column A in header row with header style for consistency
            if logo_added:
                logo_header_cell = sheet.cell(row=header_row, column=1)
                logo_header_cell.fill = header_fill
                logo_header_cell.border = thin_border
            sheet.row_dimensions[header_row].height = 30

            # Add data
            answers_qs = Answer.objects.filter(checklist__in=checklists_for_type).select_related('question', 'checklist')
            answers_dict = {}
            for answer in answers_qs:
                key = (answer.checklist.id, answer.question.id)
                if key not in answers_dict:
                    answers_dict[key] = answer
            
            data_start_row = header_row + 1
            for row_idx, checklist in enumerate(checklists_for_type):
                current_row = data_start_row + row_idx
                
                user_name = ""
                personnel_code = ""
                if checklist.user:
                    if checklist.user.first_name or checklist.user.last_name:
                        user_name = f"{checklist.user.first_name or ''} {checklist.user.last_name or ''}".strip()
                    else:
                        user_name = checklist.user.username or ""
                    if hasattr(checklist.user, 'userprofile') and checklist.user.userprofile:
                        personnel_code = checklist.user.userprofile.personnel_code or ""
                
                # تبدیل تاریخ به شمسی
                date_str = ""
                if checklist.date:
                    try:
                        # تبدیل datetime به date برای jdatetime
                        if isinstance(checklist.date, datetime):
                            gregorian_date = checklist.date.date()
                        else:
                            gregorian_date = checklist.date
                        
                        # تبدیل به شمسی
                        jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
                        # فرمت تاریخ و زمان شمسی
                        if isinstance(checklist.date, datetime):
                            date_str = jalali_date.strftime("%Y/%m/%d") + " " + checklist.date.strftime("%H:%M:%S")
                        else:
                            date_str = jalali_date.strftime("%Y/%m/%d")
                    except:
                        # در صورت خطا، از فرمت میلادی استفاده می‌کنیم
                        date_str = checklist.date.strftime("%Y/%m/%d %H:%M:%S") if isinstance(checklist.date, datetime) else str(checklist.date)
                
                row_data = [
                    user_name,
                    personnel_code,
                    checklist.machine.workshop_code if checklist.machine else "",
                    checklist.machine.machine_type.name if (checklist.machine and checklist.machine.machine_type) else "",
                    date_str,
                    checklist.shift or "",
                    checklist.shift_group or "",
                ]
                
                # Add answers
                for question in questions:
                    answer = answers_dict.get((checklist.id, question.id))
                    if answer:
                        if question.question_type == 'text':
                            row_data.append(answer.answer_text or '')
                        elif question.question_type == 'option':
                            row_data.append(answer.selected_option or '')
                    else:
                        row_data.append('')
                
                # Add descriptions
                for question in questions:
                    answer = answers_dict.get((checklist.id, question.id))
                    if answer:
                        row_data.append(answer.description or '')
                    else:
                        row_data.append('')
                
                # Apply styling to each cell
                for col_idx, value in enumerate(row_data, start=1):
                    cell = sheet.cell(row=current_row, column=col_idx, value=value)
                    cell.font = data_font
                    cell.border = thin_border
                    cell.alignment = right_alignment  # Right align for all columns
                    
                    # Alternate row colors for better readability
                    if row_idx % 2 == 1:
                        cell.fill = even_row_fill
                
                # Set row height
                sheet.row_dimensions[current_row].height = 20
            
            # Auto-adjust column widths
            for col_idx in range(1, num_cols + 1):
                col_letter = get_column_letter(col_idx)
                max_length = 0
                
                # Check header
                header_cell = sheet.cell(row=header_row, column=col_idx)
                if header_cell.value:
                    max_length = len(str(header_cell.value))
                
                # Check data cells
                for row_idx in range(data_start_row, data_start_row + len(checklists_for_type)):
                    cell = sheet.cell(row=row_idx, column=col_idx)
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                
                # Set column width (with some padding)
                adjusted_width = min(max_length + 3, 50)  # Max width of 50
                sheet.column_dimensions[col_letter].width = adjusted_width if adjusted_width > 10 else 15


    # Remove default sheet if exists
    if 'Sheet' in workbook.sheetnames:
        workbook.remove(workbook['Sheet'])
    
    # Prepare the response
    filename = 'checklists_all.xlsx' if export_all else 'checklists_filtered.xlsx'
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    workbook.save(response)
    return response