# rubika_bot/views.py

import json
import logging
from typing import Any, Dict

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
try:
    from django_ratelimit.decorators import ratelimit
except ModuleNotFoundError:
    from ratelimit.decorators import ratelimit

from .constants import (
    DEEPLINK_TEMPLATE,
    MAX_USERS_PER_PAGE,
    WEBHOOK_RATE_LIMIT,
    is_ip_allowed,
)
from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser, WebhookLog
from .services import RubPyIntegrationService
from .tasks import send_rubika_message
from .tasks import process_webhook_task # این import را اضافه یا جایگزین کنید


logger = logging.getLogger(__name__)


def superuser_required(view_func):
    """Decorator for views that require superuser access."""
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate=WEBHOOK_RATE_LIMIT, block=True)
def webhook_receiver(request: HttpRequest) -> JsonResponse:
    """
    The single entry point for all incoming webhook updates.
    It quickly receives the payload, queues it for background processing
    with Celery, and returns an immediate 200 OK response.
    """
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))

    if not is_ip_allowed(ip):
        WebhookLog.log_warning('وبهوک غیرمجاز', f'درخواست از IP غیرمجاز: {ip}')
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        WebhookLog.log_error('وبهوک نامعتبر', 'JSON معتبر نیست', {'ip': ip})
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    # Log the incoming request immediately
    WebhookLog.log_incoming(
        'دریافت وبهوک', f'دریافت به‌روزرسانی از {ip}', {'ip': ip, 'payload': payload}
    )

    # --- NEW ARCHITECTURE ---
    # Queue the payload for background processing and return immediately.
    process_webhook_task.delay(payload)
    
    # Return a success response instantly to the Rubika server.
    return JsonResponse({'ok': True, 'status': 'queued'})

# --- Admin Panel Views ---

@superuser_required
def settings_view(request: HttpRequest) -> HttpResponse:
    """Render and update Rubika bot settings in the admin panel."""
    settings_obj = RubikaBotSettings.get_solo()
    if request.method == 'POST':
        token = (request.POST.get('token') or '').strip() or None
        bot_username = (request.POST.get('bot_username') or '').strip() or None
        settings_obj.token = token
        settings_obj.bot_username = bot_username
        settings_obj.save()
        RubPyIntegrationService.reset() # Reset service to use new token
        return redirect('rubika_bot:settings')

    # User list with search and pagination
    users_qs = RubikaUser.objects.select_related('user').order_by('-updated_at')
    search = request.GET.get('q')
    if search:
        users_qs = users_qs.filter(
            Q(chat_id__icontains=search) | Q(first_name__icontains=search) |
            Q(last_name__icontains=search) | Q(user__username__icontains=search)
        )
    paginator = Paginator(users_qs, MAX_USERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'settings': settings_obj,
        'users_page': page_obj,
        'webhook_url': request.build_absolute_uri(reverse('rubika_bot:webhook')),
        'search_query': search or '',
    }
    return render(request, 'rubika_bot/settings.html', context)


@superuser_required
@require_http_methods(["POST"])
def action_register_webhook(request: HttpRequest) -> JsonResponse:
    """Register the webhook endpoints using the RubPy client."""
    try:
        service = RubPyIntegrationService.get_instance()
        webhook_url = request.build_absolute_uri(reverse('rubika_bot:webhook'))
        result = service.update_endpoints(webhook_url)
        WebhookLog.log_info('ثبت وبهوک', 'نتیجه ثبت وبهوک', {'result': result})
        status = 200 if result.get('ok') else 500
        return JsonResponse({'ok': result.get('ok'), 'details': result}, status=status)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        logger.exception("Webhook registration failed: %s", exc)
        WebhookLog.log_error('ثبت وبهوک', str(exc))
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)


@superuser_required
@require_http_methods(["GET"])
def action_get_webhook_info(request: HttpRequest) -> JsonResponse:
    """Retrieve current webhook status from Rubika."""
    try:
        service = RubPyIntegrationService.get_instance()
        result = service.fetch_webhook_info()
        status = 200 if result.get('ok') else 500
        return JsonResponse(result, status=status)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    except Exception as exc:
        logger.exception("Failed to get webhook info: %s", exc)
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)


@superuser_required
@require_http_methods(["POST"])
def action_broadcast(request: HttpRequest) -> JsonResponse:
    """Enqueue a broadcast message to all Rubika users."""
    text = (request.POST.get('text') or '').strip()
    if not text:
        return JsonResponse({'ok': False, 'error': 'متن پیام خالی است'}, status=400)
    
    chat_ids = list(RubikaUser.objects.values_list('chat_id', flat=True))
    for chat_id in chat_ids:
        send_rubika_message.delay(str(chat_id), text)
    
    WebhookLog.log_info('ارسال همگانی', f'پیام برای {len(chat_ids)} کاربر در صف قرار گرفت.')
    return JsonResponse({'ok': True, 'count': len(chat_ids)})


@superuser_required
@require_http_methods(["POST"])
def action_disconnect_user(request: HttpRequest, chat_id: str) -> JsonResponse:
    """Disconnect a user from their linked Rubika account via admin panel."""
    try:
        rubika_user = RubikaUser.objects.select_related('user').get(chat_id=chat_id)
    except RubikaUser.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'کاربر یافت نشد'}, status=404)

    service = RubPyIntegrationService.get_instance()
    service.engine._disconnect_user(chat_id, rubika_user) # Re-use the engine logic
    return JsonResponse({'ok': True})


# --- Log Management Views ---

@superuser_required
def get_webhook_logs(request: HttpRequest) -> JsonResponse:
    log_type = request.GET.get('type', 'all')
    limit = int(request.GET.get('limit', 50))
    logs_qs = WebhookLog.objects.all()
    if log_type != 'all':
        logs_qs = logs_qs.filter(log_type=log_type)
    
    payload = [
        {'id': log.id, 'log_type': log.get_log_type_display(), 'title': log.title, 'message': log.message, 'data': log.data, 'created_at': log.created_at.isoformat()}
        for log in logs_qs[:limit]
    ]
    return JsonResponse({'ok': True, 'logs': payload})

@superuser_required
@require_http_methods(["POST"])
def clear_webhook_logs(request: HttpRequest) -> JsonResponse:
    count, _ = WebhookLog.objects.all().delete()
    return JsonResponse({'ok': True, 'deleted': count})

@superuser_required
def export_webhook_logs(request: HttpRequest) -> HttpResponse:
    # This view can remain as it is, as it only queries the database.
    # ... (کد این تابع را از فایل فعلی خود کپی کنید) ...
    pass


# --- User-facing Connection Views ---

@login_required
def connect_page(request: HttpRequest) -> HttpResponse:
    """Render the connection page for authenticated users."""
    settings_obj = RubikaBotSettings.get_solo()
    rubika_user = getattr(request.user, 'rubika_profile', None)
    is_connected = bool(rubika_user and rubika_user.user)
    
    existing_code = RubikaConnectionCode.objects.filter(
        user=request.user, used=False, expires_at__gt=timezone.now()
    ).first()
    code_obj = existing_code or RubikaConnectionCode.generate_for_user(request.user)
    
    direct_link = None
    if settings_obj.bot_username:
        direct_link = DEEPLINK_TEMPLATE.format(
            bot_username=settings_obj.bot_username.lstrip('@'), code=code_obj.code
        )

    context = {
        'code': code_obj.code,
        'expires_at': code_obj.expires_at,
        'bot_username': settings_obj.bot_username,
        'direct_link': direct_link,
        'is_connected': is_connected,
        'chat_id': rubika_user.chat_id if rubika_user else None,
    }
    return render(request, 'rubika_bot/connect.html', context)


@login_required
def quick_connect(request: HttpRequest) -> HttpResponse:
    """Shortcut redirect to the connection page."""
    return redirect('rubika_bot:connect_page')


@login_required
@require_http_methods(["POST"])
def get_connection_link(request: HttpRequest) -> JsonResponse:
    """Generate a new connection link for the logged-in user."""
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(request.user)
    settings_obj = RubikaBotSettings.get_solo()
    link = None
    if settings_obj.bot_username:
        link = DEEPLINK_TEMPLATE.format(bot_username=settings_obj.bot_username.lstrip('@'), code=code.code)
    
    return JsonResponse({
        'ok': True, 'code': code.code, 'link': link, 'expires_at': code.expires_at.isoformat()
    })


@login_required
@require_http_methods(["POST"])
def generate_connection_code(request: HttpRequest) -> JsonResponse:
    """Generate a fresh connection code for the logged-in user."""
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(request.user)
    return JsonResponse({'ok': True, 'code': code.code, 'expires_at': code.expires_at.isoformat()})