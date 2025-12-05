# corrective_actions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from .models import CorrectiveAction, ActionStep, SideEffectRisk
from .forms import CorrectiveActionForm, ActionStepFormSet, SideEffectRiskFormSet
from .ai_helper import CorrectiveActionAIHelper
from accounts.models import UserProfile
import jdatetime
import json


@login_required
def corrective_action_list(request):
    """لیست اقدامات اصلاحی/پیشگیرانه"""
    corrective_actions = CorrectiveAction.objects.all().select_related(
        'requester', 'receiver', 'related_incident', 'related_risk', 'related_anomaly'
    ).prefetch_related('action_steps', 'side_effect_risks')
    
    # فیلتر بر اساس وضعیت
    status_filter = request.GET.get('status', '')
    if status_filter:
        corrective_actions = corrective_actions.filter(status=status_filter)
    
    # جستجو
    search_query = request.GET.get('search', '')
    if search_query:
        corrective_actions = corrective_actions.filter(
            Q(tracking_code__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(requester__user__first_name__icontains=search_query) |
            Q(requester__user__last_name__icontains=search_query)
        )
    
    # مرتب‌سازی
    ordering = request.GET.get('ordering', '-created_at')
    corrective_actions = corrective_actions.order_by(ordering)
    
    # صفحه‌بندی
    paginator = Paginator(corrective_actions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'ordering': ordering,
        'status_choices': CorrectiveAction.STATUS_CHOICES,
    }
    
    return render(request, 'corrective_actions/corrective_action_list.html', context)


@login_required
def corrective_action_create(request):
    """ایجاد اقدام اصلاحی/پیشگیرانه جدید"""
    # دریافت incident_id، risk_id یا anomaly_id از query string در صورت وجود
    related_incident_id = request.GET.get('incident_id', None)
    related_risk_id = request.GET.get('risk_id', None)
    related_anomaly_id = request.GET.get('anomaly_id', None)
    
    # تبدیل به integer در صورت نیاز
    if related_incident_id:
        try:
            related_incident_id = int(related_incident_id)
        except (ValueError, TypeError):
            related_incident_id = None
    if related_risk_id:
        try:
            related_risk_id = int(related_risk_id)
        except (ValueError, TypeError):
            related_risk_id = None
    if related_anomaly_id:
        try:
            related_anomaly_id = int(related_anomaly_id)
        except (ValueError, TypeError):
            related_anomaly_id = None
    
    if request.method == 'POST':
        form = CorrectiveActionForm(request.POST, related_incident_id=related_incident_id, related_risk_id=related_risk_id, related_anomaly_id=related_anomaly_id)
        action_step_formset = ActionStepFormSet(request.POST, prefix='action_steps')
        side_effect_risk_formset = SideEffectRiskFormSet(request.POST, prefix='side_effect_risks')
        
        if form.is_valid() and action_step_formset.is_valid() and side_effect_risk_formset.is_valid():
            try:
                with transaction.atomic():
                    # ذخیره اقدام اصلی
                    corrective_action = form.save(commit=False)
                    
                    # تنظیم requester به صورت خودکار اگر خالی باشد
                    if not corrective_action.requester:
                        user_profile, created = UserProfile.objects.get_or_create(
                            user=request.user,
                            defaults={'personnel_code': '', 'mobile': ''}
                        )
                        corrective_action.requester = user_profile
                    
                    corrective_action.save()
                    
                    # ذخیره مراحل اقدام
                    action_step_formset.instance = corrective_action
                    action_step_formset.save()
                    
                    # ذخیره ریسک‌های ناشی از اقدام
                    side_effect_risk_formset.instance = corrective_action
                    side_effect_risk_formset.save()
                    
                    messages.success(request, f'اقدام اصلاحی/پیشگیرانه با شماره {corrective_action.tracking_code} با موفقیت ایجاد شد.')
                    return redirect('corrective_actions:detail', pk=corrective_action.pk)
            except Exception as e:
                messages.error(request, f'خطا در ایجاد اقدام: {str(e)}')
        else:
            # نمایش خطاهای فرم
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{form.fields[field].label}: {error}')
            if not action_step_formset.is_valid():
                messages.error(request, 'خطا در مراحل اقدام. لطفاً اطلاعات را بررسی کنید.')
            if not side_effect_risk_formset.is_valid():
                messages.error(request, 'خطا در ریسک‌های ناشی از اقدام. لطفاً اطلاعات را بررسی کنید.')
    else:
        form = CorrectiveActionForm(related_incident_id=related_incident_id, related_risk_id=related_risk_id, related_anomaly_id=related_anomaly_id)
        action_step_formset = ActionStepFormSet(prefix='action_steps')
        side_effect_risk_formset = SideEffectRiskFormSet(prefix='side_effect_risks')
    
    context = {
        'form': form,
        'action_step_formset': action_step_formset,
        'side_effect_risk_formset': side_effect_risk_formset,
        'related_incident_id': related_incident_id,
        'related_risk_id': related_risk_id,
        'related_anomaly_id': related_anomaly_id,
    }
    
    return render(request, 'corrective_actions/corrective_action_form.html', context)


@login_required
def corrective_action_detail(request, pk):
    """نمایش جزئیات اقدام اصلاحی/پیشگیرانه"""
    corrective_action = get_object_or_404(
        CorrectiveAction.objects.select_related(
            'requester', 'receiver', 'related_incident', 'related_risk', 'related_anomaly'
        ).prefetch_related('action_steps__responsible', 'side_effect_risks'),
        pk=pk
    )
    
    # تبدیل تاریخ‌ها به شمسی برای نمایش
    try:
        if corrective_action.created_at:
            jalali_date = jdatetime.date.fromgregorian(date=corrective_action.created_at)
            corrective_action.jalali_created_at = jalali_date.strftime('%Y/%m/%d')
    except:
        corrective_action.jalali_created_at = None
    
    # تبدیل تاریخ‌های مراحل اقدام
    for step in corrective_action.action_steps.all():
        try:
            if step.deadline:
                jalali_deadline = jdatetime.date.fromgregorian(date=step.deadline)
                step.jalali_deadline = jalali_deadline.strftime('%Y/%m/%d')
            if step.completion_date:
                jalali_completion = jdatetime.date.fromgregorian(date=step.completion_date)
                step.jalali_completion_date = jalali_completion.strftime('%Y/%m/%d')
        except:
            pass
    
    context = {
        'corrective_action': corrective_action,
    }
    
    return render(request, 'corrective_actions/corrective_action_detail.html', context)


@login_required
def corrective_action_update(request, pk):
    """ویرایش اقدام اصلاحی/پیشگیرانه"""
    corrective_action = get_object_or_404(CorrectiveAction, pk=pk)
    
    if request.method == 'POST':
        form = CorrectiveActionForm(request.POST, instance=corrective_action)
        action_step_formset = ActionStepFormSet(
            request.POST,
            instance=corrective_action,
            prefix='action_steps'
        )
        side_effect_risk_formset = SideEffectRiskFormSet(
            request.POST,
            instance=corrective_action,
            prefix='side_effect_risks'
        )
        
        if form.is_valid() and action_step_formset.is_valid() and side_effect_risk_formset.is_valid():
            try:
                with transaction.atomic():
                    # ذخیره اقدام اصلی
                    corrective_action = form.save()
                    
                    # ذخیره مراحل اقدام
                    action_step_formset.save()
                    
                    # ذخیره ریسک‌های ناشی از اقدام
                    side_effect_risk_formset.save()
                    
                    messages.success(request, f'اقدام اصلاحی/پیشگیرانه با شماره {corrective_action.tracking_code} با موفقیت به‌روزرسانی شد.')
                    return redirect('corrective_actions:detail', pk=corrective_action.pk)
            except Exception as e:
                messages.error(request, f'خطا در به‌روزرسانی اقدام: {str(e)}')
        else:
            # نمایش خطاهای فرم
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{form.fields[field].label}: {error}')
            if not action_step_formset.is_valid():
                messages.error(request, 'خطا در مراحل اقدام. لطفاً اطلاعات را بررسی کنید.')
            if not side_effect_risk_formset.is_valid():
                messages.error(request, 'خطا در ریسک‌های ناشی از اقدام. لطفاً اطلاعات را بررسی کنید.')
    else:
        form = CorrectiveActionForm(instance=corrective_action)
        action_step_formset = ActionStepFormSet(
            instance=corrective_action,
            prefix='action_steps'
        )
        side_effect_risk_formset = SideEffectRiskFormSet(
            instance=corrective_action,
            prefix='side_effect_risks'
        )
    
    context = {
        'form': form,
        'action_step_formset': action_step_formset,
        'side_effect_risk_formset': side_effect_risk_formset,
        'corrective_action': corrective_action,
    }
    
    return render(request, 'corrective_actions/corrective_action_form.html', context)


@login_required
@require_http_methods(["POST"])
def action_step_toggle_done(request, pk):
    """تغییر وضعیت انجام مرحله اقدام"""
    action_step = get_object_or_404(ActionStep, pk=pk)
    
    action_step.is_done = not action_step.is_done
    if action_step.is_done and not action_step.completion_date:
        from django.utils import timezone
        action_step.completion_date = timezone.now().date()
    elif not action_step.is_done:
        action_step.completion_date = None
    action_step.save()
    
    return JsonResponse({
        'success': True,
        'is_done': action_step.is_done,
        'completion_date': action_step.completion_date.strftime('%Y-%m-%d') if action_step.completion_date else None
    })


@login_required
@require_http_methods(["POST"])
def corrective_action_update_status(request, pk):
    """تغییر وضعیت اقدام اصلاحی/پیشگیرانه"""
    corrective_action = get_object_or_404(CorrectiveAction, pk=pk)
    
    new_status = request.POST.get('status')
    if new_status in dict(CorrectiveAction.STATUS_CHOICES):
        corrective_action.status = new_status
        corrective_action.save()
        messages.success(request, f'وضعیت اقدام به {corrective_action.get_status_display()} تغییر یافت.')
        return redirect('corrective_actions:detail', pk=pk)
    else:
        messages.error(request, 'وضعیت نامعتبر است.')
        return redirect('corrective_actions:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def ai_generate_suggestions(request):
    """
    API endpoint برای تولید پیشنهادات AI برای فرم اقدام اصلاحی
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        related_anomaly_id = data.get('related_anomaly_id')
        related_incident_id = data.get('related_incident_id')
        related_risk_id = data.get('related_risk_id')
        user_description = data.get('user_description', '')
        
        # تبدیل به integer
        if related_anomaly_id:
            try:
                related_anomaly_id = int(related_anomaly_id)
            except (ValueError, TypeError):
                related_anomaly_id = None
        
        if related_incident_id:
            try:
                related_incident_id = int(related_incident_id)
            except (ValueError, TypeError):
                related_incident_id = None
        
        if related_risk_id:
            try:
                related_risk_id = int(related_risk_id)
            except (ValueError, TypeError):
                related_risk_id = None
        
        # استفاده از AI Helper
        ai_helper = CorrectiveActionAIHelper()
        suggestions = ai_helper.generate_corrective_action_data(
            related_anomaly_id=related_anomaly_id,
            related_incident_id=related_incident_id,
            related_risk_id=related_risk_id,
            user_description=user_description
        )
        
        # محاسبه تاریخ مهلت برای action_steps
        today = timezone.now().date()
        for step in suggestions.get('action_steps', []):
            deadline_days = step.get('deadline_days', 7)
            step['deadline'] = (today + timedelta(days=deadline_days)).strftime('%Y-%m-%d')
            step['deadline_jalali'] = jdatetime.date.fromgregorian(date=today + timedelta(days=deadline_days)).strftime('%Y/%m/%d')
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'داده‌های ارسالی نامعتبر است'
        }, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"خطا در تولید پیشنهادات AI: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'خطا در تولید پیشنهادات: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_generate_root_cause(request):
    """
    API endpoint برای تولید تحلیل علل ریشه‌ای با AI
    """
    try:
        data = json.loads(request.body) if request.body else {}
        description = data.get('description', '')
        
        if not description:
            return JsonResponse({
                'success': False,
                'error': 'شرح عدم انطباق الزامی است'
            }, status=400)
        
        ai_helper = CorrectiveActionAIHelper()
        root_cause = ai_helper.generate_root_cause_analysis(description)
        
        return JsonResponse({
            'success': True,
            'root_cause_analysis': root_cause
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'داده‌های ارسالی نامعتبر است'
        }, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"خطا در تولید تحلیل علل ریشه‌ای: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'خطا در تولید تحلیل: {str(e)}'
        }, status=500)
