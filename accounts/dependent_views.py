"""Public dependent-information portal (SMS OTP) and HR review views."""

from __future__ import annotations

import hashlib
import logging
import secrets
import time

import jdatetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.http import require_POST

from .dependent_notifications import notify_change_reviewed, notify_change_submitted
from .dependent_service import (
    EDUCATION_LEVEL_CHOICES,
    EDUCATION_STATUS_CHOICES,
    FIELD_LABELS,
    GENDER_CHOICES,
    MARITAL_STATUS_CHOICES,
    MILITARY_STATUS_CHOICES,
    RELATIONSHIP_CHOICES,
    ChangeRequestError,
    apply_change_request,
    build_diff,
    create_change_request,
    dependent_snapshot,
    humanize,
    normalize_mobile,
    parse_date,
    parse_jalali,
    reject_change_request,
    to_jalali,
    validate_dependent_data,
)
from .models import Dependent, DependentChangeRequest, UserProfile
from .views import superuser_required

logger = logging.getLogger(__name__)

PORTAL_SESSION_KEY = 'dependents_portal_auth'
PORTAL_OTP_SESSION_KEY = 'dependents_portal_otp'
SESSION_TTL = 1800


def _otp_digest(nonce, profile_id, code):
    return salted_hmac(
        'accounts.dependents.otp',
        f'{nonce}:{profile_id}:{code}',
    ).hexdigest()


def _set_portal_auth(request, profile):
    request.session[PORTAL_SESSION_KEY] = {
        'profile_id': profile.pk,
        'expires_at': int(time.time()) + SESSION_TTL,
    }


def _get_portal_profile(request, *, refresh=True):
    state = request.session.get(PORTAL_SESSION_KEY)
    if not state:
        return None
    if int(state.get('expires_at', 0)) < int(time.time()):
        request.session.pop(PORTAL_SESSION_KEY, None)
        return None
    profile = UserProfile.objects.select_related('user').filter(pk=state.get('profile_id')).first()
    if profile is None or profile.user is None or not profile.user.is_active:
        request.session.pop(PORTAL_SESSION_KEY, None)
        return None
    if refresh:
        _set_portal_auth(request, profile)
    return profile


def portal_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = _get_portal_profile(request)
        if profile is None:
            return redirect('dependents:home')
        request.dependent_profile = profile
        return view_func(request, *args, **kwargs)

    return _wrapped


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ---------------------------------------------------------------------------
# Authentication (personnel code + registered mobile + SMS code)
# ---------------------------------------------------------------------------

def dependent_portal(request):
    if _get_portal_profile(request, refresh=False) is not None:
        return redirect('dependents:info')
    return render(request, 'accounts/dependents_auth.html')


@require_POST
def dependent_portal_send_otp(request):
    personnel_code = (request.POST.get('personnel_code') or '').strip()
    mobile = normalize_mobile(request.POST.get('mobile'))
    if not personnel_code or not mobile:
        return JsonResponse({'success': False, 'message': 'کد پرسنلی و شماره موبایل را وارد کنید.'}, status=400)

    cooldown = int(getattr(settings, 'LOGIN_OTP_RESEND_SECONDS', 60))
    ttl = int(getattr(settings, 'LOGIN_OTP_TTL_SECONDS', 300))
    mobile_key = hashlib.sha256(mobile.encode()).hexdigest()
    cache_key = f'dependents-otp-send:{mobile_key}'
    if not cache.add(cache_key, True, cooldown):
        return JsonResponse({
            'success': False,
            'message': f'برای ارسال مجدد کد {cooldown} ثانیه صبر کنید.',
            'retry_after': cooldown,
        }, status=429)

    profile = UserProfile.objects.select_related('user').filter(personnel_code=personnel_code).first()
    profile_mobile = normalize_mobile(profile.mobile) if profile else ''
    if profile is None or profile.user is None or not profile.user.is_active or profile_mobile != mobile:
        cache.delete(cache_key)
        return JsonResponse({
            'success': False,
            'message': 'کد پرسنلی یا شماره موبایل با سوابق ما مطابقت ندارد. لطفاً با منابع انسانی تماس بگیرید.',
        }, status=400)

    from dashboard.sms_utils import send_template_sms

    code = f'{secrets.randbelow(1_000_000):06d}'
    nonce = secrets.token_hex(16)
    template_id = int(getattr(settings, 'DEPENDENTS_OTP_TEMPLATE_ID', getattr(settings, 'LOGIN_OTP_TEMPLATE_ID', 857178)))
    sent = send_template_sms(
        mobile,
        template_id,
        [
            {'Name': 'code', 'Value': code},
            {'Name': 'username', 'Value': profile.user.username},
        ],
        user_id=profile.user_id,
        request=request,
    )
    if not sent:
        cache.delete(cache_key)
        return JsonResponse({'success': False, 'message': 'ارسال پیامک انجام نشد؛ لطفاً دوباره تلاش کنید.'}, status=503)

    request.session[PORTAL_OTP_SESSION_KEY] = {
        'profile_id': profile.pk,
        'mobile': mobile,
        'nonce': nonce,
        'code_digest': _otp_digest(nonce, profile.pk, code),
        'expires_at': int(time.time()) + ttl,
        'attempts': 0,
    }
    return JsonResponse({
        'success': True,
        'code_sent': True,
        'message': 'کد تایید ارسال شد.',
        'expires_in': ttl,
        'retry_after': cooldown,
    })


@require_POST
def dependent_portal_verify_otp(request):
    raw_code = str(request.POST.get('code', ''))
    code = raw_code.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')).strip()
    state = request.session.get(PORTAL_OTP_SESSION_KEY)
    if not state or not code.isdigit() or len(code) != 6:
        return JsonResponse({'success': False, 'message': 'کد تایید نامعتبر است.'}, status=400)
    if int(state.get('expires_at', 0)) < int(time.time()):
        request.session.pop(PORTAL_OTP_SESSION_KEY, None)
        return JsonResponse({'success': False, 'message': 'کد منقضی شده است؛ کد جدید دریافت کنید.'}, status=400)

    max_attempts = int(getattr(settings, 'LOGIN_OTP_MAX_ATTEMPTS', 5))
    expected = _otp_digest(state.get('nonce', ''), state.get('profile_id'), code)
    if not constant_time_compare(expected, state.get('code_digest', '')):
        state['attempts'] = int(state.get('attempts', 0)) + 1
        if state['attempts'] >= max_attempts:
            request.session.pop(PORTAL_OTP_SESSION_KEY, None)
            message = 'تعداد تلاش‌ها بیش از حد مجاز بود؛ کد جدید دریافت کنید.'
        else:
            request.session[PORTAL_OTP_SESSION_KEY] = state
            message = 'کد تایید اشتباه است.'
        return JsonResponse({'success': False, 'message': message}, status=400)

    profile = UserProfile.objects.select_related('user').filter(pk=state.get('profile_id')).first()
    if profile is None or profile.user is None or not profile.user.is_active:
        request.session.pop(PORTAL_OTP_SESSION_KEY, None)
        return JsonResponse({'success': False, 'message': 'امکان ورود وجود ندارد.'}, status=400)

    request.session.pop(PORTAL_OTP_SESSION_KEY, None)
    _set_portal_auth(request, profile)
    return JsonResponse({'success': True, 'redirect': reverse('dependents:info')})


def dependent_portal_logout(request):
    request.session.pop(PORTAL_SESSION_KEY, None)
    return redirect('dependents:home')


# ---------------------------------------------------------------------------
# Portal pages
# ---------------------------------------------------------------------------

def _split_birth_date(data):
    value = parse_date(data.get('birth_date')) if data and data.get('birth_date') else None
    if value is None:
        return '', '', ''
    jalali = jdatetime.date.fromgregorian(date=value)
    return str(jalali.year), str(jalali.month), str(jalali.day)


def _form_context(profile, data=None, errors=None, dependent=None):
    data_dict = data or {}
    errs = errors or {}
    non_field_error = errs.get('__all__') or errs.get('general') or ''
    birth_year, birth_month, birth_day = _split_birth_date(data_dict)
    return {
        'profile': profile,
        'data': data_dict,
        'errors': errs,
        'non_field_error': non_field_error,
        'dependent': dependent,
        'birth_year': birth_year,
        'birth_month': birth_month,
        'birth_day': birth_day,
        'gender_choices': GENDER_CHOICES,
        'relationship_choices': RELATIONSHIP_CHOICES,
        'marital_choices': MARITAL_STATUS_CHOICES,
        'education_status_choices': EDUCATION_STATUS_CHOICES,
        'education_level_choices': EDUCATION_LEVEL_CHOICES,
        'military_choices': MILITARY_STATUS_CHOICES,
        'now_jalali': jdatetime.date.today(),
    }


def _collect_form_data(request):
    data = {field: request.POST.get(field, '') for field in (
        'first_name', 'last_name', 'father_name', 'national_code',
        'birth_certificate_number', 'gender', 'mobile', 'relationship',
        'marital_status', 'address', 'education_status', 'education_level',
        'field_of_study', 'study_place', 'job', 'military_status',
        'disease_type',
    )}
    birth_date = parse_jalali(
        request.POST.get('birth_year'), request.POST.get('birth_month'), request.POST.get('birth_day')
    )
    data['birth_date'] = birth_date.isoformat() if birth_date else ''
    return data


@portal_required
def dependent_portal_home(request):
    profile = request.dependent_profile
    if request.method == 'POST':
        if request.POST.get('action') == 'save_address':
            address = (request.POST.get('address') or '').strip()
            if not address:
                messages.error(request, 'آدرس محل سکونت را وارد کنید.')
            else:
                profile.address = address
                profile.save(update_fields=['address'])
                messages.success(request, 'آدرس شما با موفقیت ذخیره شد.')
            return redirect('dependents:info')

    dependents = list(profile.dependents.all().order_by('last_name', 'first_name'))
    pending = DependentChangeRequest.objects.filter(
        personnel=profile, status=DependentChangeRequest.Status.PENDING
    ).select_related('dependent')
    pending_by_dependent = {cr.dependent_id: cr for cr in pending if cr.dependent_id}
    my_requests = list(
        DependentChangeRequest.objects.filter(personnel=profile)
        .select_related('dependent')
        .order_by('-submitted_at')[:10]
    )
    rows = []
    for dependent in dependents:
        _, missing = validate_dependent_data(dependent_snapshot(dependent))
        rows.append({
            'dependent': dependent,
            'pending': pending_by_dependent.get(dependent.pk),
            'birth_date_jalali': to_jalali(dependent.birth_date),
            'missing_count': len(missing),
        })
    return render(request, 'accounts/dependents_portal.html', {
        'profile': profile,
        'rows': rows,
        'pending_creates': [cr for cr in pending if cr.dependent_id is None],
        'my_requests': my_requests,
    })


@portal_required
def dependent_portal_add(request):
    profile = request.dependent_profile
    data = {}
    errors = {}
    if request.method == 'POST':
        data = _collect_form_data(request)
        cleaned, errors = validate_dependent_data(data)
        if not errors:
            try:
                change = create_change_request(
                    profile,
                    DependentChangeRequest.Action.CREATE,
                    cleaned,
                    channel=DependentChangeRequest.Channel.WEB,
                    ip_address=_client_ip(request),
                )
                notify_change_submitted(change)
                messages.success(
                    request,
                    'اطلاعات ثبت شد و پس از بررسی منابع انسانی اعمال می‌شود.',
                )
                return redirect('dependents:info')
            except ChangeRequestError as exc:
                errors['__all__'] = str(exc)
    return render(request, 'accounts/dependents_form.html', _form_context(profile, data, errors))


@portal_required
def dependent_portal_edit(request, pk):
    profile = request.dependent_profile
    dependent = get_object_or_404(Dependent, pk=pk, personnel=profile)
    if DependentChangeRequest.objects.filter(
        dependent=dependent, status=DependentChangeRequest.Status.PENDING
    ).exists():
        messages.error(request, 'برای این فرد یک درخواست در انتظار بررسی وجود دارد.')
        return redirect('dependents:info')

    data = {}
    errors = {}
    if request.method == 'POST':
        data = _collect_form_data(request)
        cleaned, errors = validate_dependent_data(data)
        if not errors:
            try:
                change = create_change_request(
                    profile,
                    DependentChangeRequest.Action.UPDATE,
                    cleaned,
                    dependent=dependent,
                    channel=DependentChangeRequest.Channel.WEB,
                    ip_address=_client_ip(request),
                )
                notify_change_submitted(change)
                messages.success(
                    request,
                    'تغییرات ثبت شد و پس از بررسی منابع انسانی اعمال می‌شود.',
                )
                return redirect('dependents:info')
            except ChangeRequestError as exc:
                errors['__all__'] = str(exc)
    else:
        data = dependent_snapshot(dependent)
    context = _form_context(profile, data, errors, dependent=dependent)
    return render(request, 'accounts/dependents_form.html', context)


@require_POST
@portal_required
def dependent_portal_delete(request, pk):
    profile = request.dependent_profile
    dependent = get_object_or_404(Dependent, pk=pk, personnel=profile)
    if DependentChangeRequest.objects.filter(
        dependent=dependent, status=DependentChangeRequest.Status.PENDING
    ).exists():
        messages.error(request, 'برای این فرد یک درخواست در انتظار بررسی وجود دارد.')
        return redirect('dependents:info')
    try:
        change = create_change_request(
            profile,
            DependentChangeRequest.Action.DELETE,
            {},
            dependent=dependent,
            channel=DependentChangeRequest.Channel.WEB,
            ip_address=_client_ip(request),
        )
        notify_change_submitted(change)
        messages.success(
            request,
            'درخواست حذف ثبت شد و پس از تایید منابع انسانی اعمال می‌شود.',
        )
    except ChangeRequestError as exc:
        messages.error(request, str(exc))
    return redirect('dependents:info')


# ---------------------------------------------------------------------------
# HR review panel
# ---------------------------------------------------------------------------

@login_required
@superuser_required
def dependent_change_list(request):
    status = request.GET.get('status') or DependentChangeRequest.Status.PENDING
    query = request.GET.get('q', '').strip()
    requests_qs = DependentChangeRequest.objects.select_related(
        'personnel__user', 'dependent', 'submitted_by', 'reviewed_by'
    )
    if status in DependentChangeRequest.Status.values:
        requests_qs = requests_qs.filter(status=status)
    if query:
        requests_qs = requests_qs.filter(
            Q(personnel__user__first_name__icontains=query)
            | Q(personnel__user__last_name__icontains=query)
            | Q(personnel__user__username__icontains=query)
            | Q(personnel__personnel_code__icontains=query)
            | Q(new_data__national_code__icontains=query)
            | Q(old_data__national_code__icontains=query)
        )
    paginator = Paginator(requests_qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    counts = {
        'pending': DependentChangeRequest.objects.filter(status='pending').count(),
        'approved': DependentChangeRequest.objects.filter(status='approved').count(),
        'rejected': DependentChangeRequest.objects.filter(status='rejected').count(),
    }
    return render(request, 'accounts/dependent_changes_list.html', {
        'page_obj': page_obj,
        'status': status,
        'query': query,
        'counts': counts,
    })


@login_required
@superuser_required
def dependent_change_detail(request, pk):
    change = get_object_or_404(
        DependentChangeRequest.objects.select_related('personnel__user', 'dependent', 'submitted_by', 'reviewed_by'),
        pk=pk,
    )
    if request.method == 'POST' and change.status == DependentChangeRequest.Status.PENDING:
        action = request.POST.get('action')
        note = (request.POST.get('note') or '').strip()
        try:
            if action == 'approve':
                apply_change_request(change, reviewer=request.user, note=note)
                notify_change_reviewed(change)
                messages.success(request, 'درخواست تایید و اعمال شد.')
            elif action == 'reject':
                reject_change_request(change, reviewer=request.user, note=note)
                notify_change_reviewed(change)
                messages.success(request, 'درخواست رد شد.')
            else:
                messages.error(request, 'عملیات نامعتبر است.')
        except ChangeRequestError as exc:
            messages.error(request, str(exc))
        except Exception as exc:  # e.g. duplicate national code on create
            logger.exception('[dependents] failed to apply change %s', pk)
            messages.error(request, f'اعمال تغییرات انجام نشد: {exc}')
        return redirect('accounts:dependent_change_detail', pk=pk)

    if change.action == DependentChangeRequest.Action.CREATE:
        diff = [{
            'field': field,
            'label': FIELD_LABELS.get(field, field),
            'old': '—',
            'new': humanize(field, value),
        } for field, value in (change.new_data or {}).items()]
    elif change.action == DependentChangeRequest.Action.DELETE:
        diff = [{
            'field': field,
            'label': FIELD_LABELS.get(field, field),
            'old': humanize(field, value),
            'new': 'حذف می‌شود',
        } for field, value in (change.old_data or {}).items()]
    else:
        diff = build_diff(change.old_data or {}, change.new_data or {})

    return render(request, 'accounts/dependent_change_detail.html', {
        'change': change,
        'diff': diff,
        'submitted_at_jalali': _jalali_datetime(change.submitted_at),
        'reviewed_at_jalali': _jalali_datetime(change.reviewed_at),
    })


def _jalali_datetime(value):
    if not value:
        return ''
    local = timezone.localtime(value)
    return jdatetime.datetime.fromgregorian(datetime=local).strftime('%Y/%m/%d - %H:%M')
