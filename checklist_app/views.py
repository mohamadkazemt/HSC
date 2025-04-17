from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Checklist, Question, Answer
from BaseInfo.models import MiningMachine, TypeMachine
from anomalis.models import (
    LocationSection, 
    AnomalyDescription, 
    Priority, 
    Anomaly,
    Anomalytype,
    CorrectiveAction
)
from accounts.models import UserProfile
import json
from permissions.utils import permission_required

User = get_user_model()

# Create your views here.
@permission_required("general_checklist_list")
@login_required
def general_checklist_list_view(request):
    checklists = Checklist.objects.all().order_by('-date')
    paginator = Paginator(checklists, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'checklist_app/checklist_list.html', context)

@permission_required("general_checklist_form")
@login_required
def general_checklist_form_view(request):
    machines = MiningMachine.objects.all()
    location_sections = LocationSection.objects.all()
    
    context = {
        'machines': machines,
        'location_sections': location_sections,
    }
    return render(request, 'checklist_app/checklist_form.html', context)

@permission_required("general_checklist_detail")
@login_required
def general_checklist_detail_view(request, pk):
    checklist = get_object_or_404(Checklist, pk=pk)
    answers = Answer.objects.filter(checklist=checklist)
    
    context = {
        'checklist': checklist,
        'answers': answers,
    }
    return render(request, 'checklist_app/checklist_detail.html', context)

@permission_required("get_general_questions")
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def get_general_questions(request):
    data = json.loads(request.body)
    checklist_type = data.get('checklist_type')
    machine_id = data.get('machine_id')
    location_section_id = data.get('location_section_id')
    
    questions = Question.objects.filter(question_scope=checklist_type)
    if checklist_type == 'machine' and machine_id:
        machine = MiningMachine.objects.get(id=machine_id)
        questions = questions.filter(machine_type=machine.machine_type)
    elif checklist_type == 'location' and location_section_id:
        questions = questions.filter(location_section_id=location_section_id)
    
    questions_data = [{
        'id': q.id,
        'text': q.text,
        'is_required': q.is_required,
        'question_type': q.question_type,
        'options': q.options.split(',') if q.options else [],
    } for q in questions]
    
    return JsonResponse({'questions': questions_data})

@permission_required("submit_general_checklist")
@login_required
@require_http_methods(["POST"])
def submit_general_checklist(request):
    data = json.loads(request.body)
    print(f"Received data: {data}")
    
    checklist = Checklist.objects.create(
        user=request.user,
        checklist_type=data['checklist_type'],
        machine_id=data.get('machine_id'),
        location_section_id=data.get('location_section_id'),
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
        return JsonResponse({
            'status': 'failure_detected',
            'checklist_id': checklist.id,
            'unacceptable_answers': [{'id': a.id, 'text': a.question.text} for a in unacceptable_answers]
        })
    
    return JsonResponse({'status': 'success', 'checklist_id': checklist.id})

@permission_required("create_general_anomaly_from_failure")
@login_required
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
                # برای ماشین‌آلات، از location_section سوال استفاده می‌کنیم
                if question.location_section:
                    location = question.location_section.location
                    section = question.location_section
                else:
                    # اگر سوال location_section نداشت، از location_section پیش‌فرض استفاده می‌کنیم
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

@permission_required("export_checklists_excel")
@login_required
def export_general_checklists_excel(request):
    # این تابع باید با توجه به نیاز شما پیاده‌سازی شود
    pass

@permission_required("get_followup_users")
@login_required
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

@permission_required("question_form")
@login_required
def general_question_form_view(request):
    if request.method == 'POST':
        # دریافت داده‌های فرم
        data = request.POST
        
        # ایجاد سوال جدید
        question = Question.objects.create(
            question_scope=data['question_scope'],
            question_type=data['question_type'],
            text=data['text'],
            options=data.get('options', ''),
            unacceptable_options=data.get('unacceptable_options', ''),
            anomaly_type_id=data['anomaly_type'],
            hse_type=data['hse_type'],
            default_priority_on_fail_id=data['default_priority_on_fail'],
            default_corrective_action=data.get('default_corrective_action', ''),
            default_anomaly_description_id=data.get('default_anomaly_description', ''),
            is_required=True
        )

        # اضافه کردن نوع ماشین یا بخش مکانی بر اساس نوع سوال
        if data['question_scope'] == 'machine' and data.get('machine_type'):
            question.machine_type_id = data['machine_type']
        elif data['question_scope'] == 'location' and data.get('location_section'):
            question.location_section_id = data['location_section']
        question.save()
        
        return redirect('checklist_app:general_question_list')
    
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

@permission_required("question_list")
@login_required
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

@permission_required("question_edit")
@login_required
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
        question.save()
        
        return redirect('checklist_app:general_question_list')
    
    context = {
        'question': question,
        'anomaly_types': Anomalytype.objects.all(),
        'priorities': Priority.objects.all(),
        'anomaly_descriptions': AnomalyDescription.objects.all(),
    }
    
    return render(request, 'checklist_app/question_form.html', context)

@permission_required("question_delete")
@login_required
@require_http_methods(["POST"])
def general_question_delete_view(request):
    data = json.loads(request.body)
    question_id = data.get('question_id')
    
    try:
        question = Question.objects.get(id=question_id)
        question.delete()
        return JsonResponse({'status': 'success'})
    except Question.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'سوال مورد نظر یافت نشد'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
