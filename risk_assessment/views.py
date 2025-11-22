from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from accounts.models import Position
from .models import RiskAssessment
from .forms import RiskAssessmentForm, RiskReEvaluationForm, RiskFilterForm
from .analytics import (
    get_high_frequency_hazards,
    get_incident_based_hazards,
    get_position_risk_suggestions,
    get_critical_locations,
    generate_risk_insights,
)


@login_required
def risk_dashboard(request):
    """
    داشبورد اصلی - نمایش لیست مشاغل با تعداد ریسک‌های هر کدام
    """
    positions = Position.objects.annotate(
        total_risks=Count('risk_assessments'),
        high_risks=Count('risk_assessments', filter=Q(risk_assessments__risk_level='High')),
        medium_risks=Count('risk_assessments', filter=Q(risk_assessments__risk_level='Medium')),
        low_risks=Count('risk_assessments', filter=Q(risk_assessments__risk_level='Low')),
    ).filter(total_risks__gt=0).order_by('-high_risks', '-total_risks')
    
    # آمار کلی
    total_assessments = RiskAssessment.objects.count()
    high_risk_count = RiskAssessment.objects.filter(risk_level='High').count()
    medium_risk_count = RiskAssessment.objects.filter(risk_level='Medium').count()
    low_risk_count = RiskAssessment.objects.filter(risk_level='Low').count()
    
    # تحلیل‌های هوشمند
    high_frequency_hazards = get_high_frequency_hazards(days=90, min_count=3)
    incident_data = get_incident_based_hazards(months=12)
    critical_locations = get_critical_locations()
    
    context = {
        'positions': positions,
        'total_assessments': total_assessments,
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
        'high_frequency_hazards': high_frequency_hazards[:5],  # 5 خطر پرتکرار
        'incident_stats': incident_data,
        'critical_locations': critical_locations[:5],  # 5 مکان حساس
    }
    
    return render(request, 'risk_assessment/dashboard.html', context)


@login_required
def position_risk_list(request, position_id):
    """
    نمایش جدول ریسک‌های یک شغل خاص (مشابه اکسل)
    """
    position = get_object_or_404(Position, id=position_id)
    
    # فیلتر کردن
    risks = RiskAssessment.objects.filter(position=position).select_related(
        'hazard', 'consequence', 'responsible_person', 'created_by'
    ).prefetch_related('people_at_risk')
    
    filter_form = RiskFilterForm(request.GET)
    
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('risk_level'):
            risks = risks.filter(risk_level=filter_form.cleaned_data['risk_level'])
        
        if filter_form.cleaned_data.get('risk_source'):
            risks = risks.filter(risk_source=filter_form.cleaned_data['risk_source'])
        
        if filter_form.cleaned_data.get('is_routine') == 'true':
            risks = risks.filter(is_routine=True)
        elif filter_form.cleaned_data.get('is_routine') == 'false':
            risks = risks.filter(is_routine=False)
        
        if filter_form.cleaned_data.get('corrective_action_required') == 'true':
            risks = risks.filter(corrective_action_required=True)
        elif filter_form.cleaned_data.get('corrective_action_required') == 'false':
            risks = risks.filter(corrective_action_required=False)
    
    # مرتب‌سازی بر اساس عدد ریسک (بالاترین اول)
    risks = risks.order_by('-risk_number', '-created_at')

    # آمار سطح ریسک برای نمایش کارت‌های خلاصه
    total_count = risks.count()
    high_count = risks.filter(risk_level='High').count()
    medium_count = risks.filter(risk_level='Medium').count()
    low_count = risks.filter(risk_level='Low').count()
    corrective_open = risks.filter(corrective_action_required=True).count()
    reevaluated_count = risks.filter(residual_risk_number__isnull=False).count()
    overdue_count = risks.filter(corrective_action_required=True, action_deadline__lt=None).count()
    # اقدام‌های اصلاحی با مهلت گذشته (deadline تاریخ گذشته و هنوز اقدام لازم است)
    from django.utils import timezone
    today = timezone.now().date()
    overdue_count = risks.filter(corrective_action_required=True, action_deadline__lt=today).count()

    # درصد کاهش میانگین ریسک در ارزیابی‌های مجدد (در صورت وجود داده باقی‌مانده)
    residual_with_initial = risks.filter(residual_risk_number__isnull=False)
    avg_initial = residual_with_initial.aggregate(c=Count('id'))['c'] and sum(
        r.risk_number for r in residual_with_initial
    ) / residual_with_initial.count() if residual_with_initial.count() else 0
    avg_residual = residual_with_initial.aggregate(c=Count('id'))['c'] and sum(
        r.residual_risk_number for r in residual_with_initial
    ) / residual_with_initial.count() if residual_with_initial.count() else 0
    reduction_percent = 0
    if avg_initial and avg_residual:
        reduction_percent = round(((avg_initial - avg_residual) / avg_initial) * 100, 1)

    # روند ۶ ماهه ایجاد ریسک برای این شغل بر اساس سطح ریسک
    from datetime import datetime, timedelta
    six_months_ago = (timezone.now() - timedelta(days=180))
    trend_qs = risks.filter(created_at__gte=six_months_ago)
    trend = trend_qs.annotate(m=TruncMonth('created_at')).values('m', 'risk_level').annotate(cnt=Count('id')).order_by('m')
    # ساخت ساختار داده قابل استفاده در نمودار
    trend_labels = []
    trend_high = []
    trend_medium = []
    trend_low = []
    # ایندکس‌سازی: ماه -> سطح -> تعداد
    from collections import defaultdict
    month_map = defaultdict(lambda: {'High':0,'Medium':0,'Low':0})
    for row in trend:
        month_map[row['m'].strftime('%Y-%m')] [row['risk_level']] = row['cnt']
    for month in sorted(month_map.keys()):
        trend_labels.append(month)
        trend_high.append(month_map[month]['High'])
        trend_medium.append(month_map[month]['Medium'])
        trend_low.append(month_map[month]['Low'])
    
    # Pagination
    paginator = Paginator(risks, 20)  # 20 ریسک در هر صفحه
    page_number = request.GET.get('page')
    risks_page = paginator.get_page(page_number)
    
    context = {
        'position': position,
        'risks': risks_page,
        'filter_form': filter_form,
        'total_count': total_count,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'corrective_open': corrective_open,
        'reevaluated_count': reevaluated_count,
        'overdue_count': overdue_count,
        'reduction_percent': reduction_percent,
        'trend_labels': trend_labels,
        'trend_high': trend_high,
        'trend_medium': trend_medium,
        'trend_low': trend_low,
    }
    
    return render(request, 'risk_assessment/risk_matrix.html', context)


@login_required
def risk_create_start(request):
    """
    صفحه شروع - انتخاب شغل برای ثبت ریسک
    """
    positions = Position.objects.all().order_by('name')
    
    context = {
        'positions': positions,
    }
    
    return render(request, 'risk_assessment/select_position.html', context)


@login_required
def risk_create_for_position(request, position_id):
    """
    ایجاد ریسک جدید برای یک شغل
    """
    position = get_object_or_404(Position, id=position_id)
    
    # پیشنهادات هوشمند
    risk_suggestions = get_position_risk_suggestions(position)
    
    if request.method == 'POST':
        form = RiskAssessmentForm(request.POST)
        if form.is_valid():
            risk = form.save(commit=False)
            risk.position = position
            if hasattr(request.user, 'userprofile'):
                risk.created_by = request.user.userprofile
            risk.save()
            form.save_m2m()  # ذخیره ManyToMany fields
            
            messages.success(request, f'ریسک با موفقیت ثبت شد. عدد ریسک: {risk.risk_number}')
            return redirect('risk_assessment:position_risks', position_id=position.id)
    else:
        form = RiskAssessmentForm(initial={'position': position})
    
    context = {
        'form': form,
        'position': position,
        'action': 'create',
        'risk_suggestions': risk_suggestions,
    }
    
    return render(request, 'risk_assessment/risk_form.html', context)


@login_required
def risk_create(request, position_id):
    """
    [DEPRECATED] استفاده از risk_create_for_position
    """
    return risk_create_for_position(request, position_id)


@login_required
def risk_update(request, risk_id):
    """
    ویرایش ریسک موجود
    """
    risk = get_object_or_404(RiskAssessment, id=risk_id)
    
    if request.method == 'POST':
        form = RiskAssessmentForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            messages.success(request, 'ریسک با موفقیت بروزرسانی شد.')
            return redirect('risk_assessment:position_risks', position_id=risk.position.id)
    else:
        form = RiskAssessmentForm(instance=risk)
    
    context = {
        'form': form,
        'risk': risk,
        'position': risk.position,
        'action': 'update',
    }
    
    return render(request, 'risk_assessment/risk_form.html', context)


@login_required
def risk_detail(request, risk_id):
    """
    نمایش جزئیات کامل یک ریسک
    """
    risk = get_object_or_404(
        RiskAssessment.objects.select_related(
            'position', 'hazard', 'consequence', 'responsible_person', 'created_by'
        ).prefetch_related('people_at_risk'),
        id=risk_id
    )
    
    # تولید بینش‌های هوشمند
    insights = generate_risk_insights(risk)
    
    context = {
        'risk': risk,
        'insights': insights,
        'related_anomalies': insights['related_anomalies'],
        'related_incidents': insights['related_incidents'],
        'trend_data': insights['anomaly_trend'],
        'suggestions': insights['suggestions'],
    }
    
    return render(request, 'risk_assessment/risk_detail.html', context)


@login_required
def risk_re_evaluate(request, risk_id):
    """
    ارزیابی مجدد ریسک (پس از اقدامات اصلاحی)
    """
    risk = get_object_or_404(RiskAssessment, id=risk_id)
    
    if request.method == 'POST':
        form = RiskReEvaluationForm(request.POST, instance=risk)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                f'ارزیابی مجدد انجام شد. ریسک باقی‌مانده: {risk.residual_risk_number}'
            )
            return redirect('risk_assessment:risk_detail', risk_id=risk.id)
    else:
        form = RiskReEvaluationForm(instance=risk)
    
    context = {
        'form': form,
        'risk': risk,
    }
    
    return render(request, 'risk_assessment/risk_re_evaluate.html', context)


@login_required
def risk_delete(request, risk_id):
    """
    حذف ریسک
    """
    risk = get_object_or_404(RiskAssessment, id=risk_id)
    position_id = risk.position.id
    
    if request.method == 'POST':
        risk.delete()
        messages.success(request, 'ریسک با موفقیت حذف شد.')
        return redirect('risk_assessment:position_risks', position_id=position_id)
    
    context = {
        'risk': risk,
    }
    
    return render(request, 'risk_assessment/risk_confirm_delete.html', context)


@login_required
def risk_matrix_view(request):
    """
    نمایش ماتریس ۵×۵ ریسک (برای تمام ریسک‌ها)
    """
    # ساخت ساختار سطرها برای استفاده ساده در قالب
    rows = []
    for severity in range(1, 6):
        cells = []
        for probability in range(1, 6):
            rpn = severity * probability
            count = RiskAssessment.objects.filter(
                severity=severity,
                probability=probability
            ).count()
            if rpn >= 17:
                color = 'danger'
            elif rpn >= 7:
                color = 'warning'
            else:
                color = 'success'
            cells.append({
                'severity': severity,
                'probability': probability,
                'rpn': rpn,
                'count': count,
                'color': color,
            })
        rows.append({'severity': severity, 'cells': cells})

    context = {
        'rows': rows,
        'severities': range(1, 6),
        'probabilities': range(1, 6),
    }
    return render(request, 'risk_assessment/matrix_view.html', context)
