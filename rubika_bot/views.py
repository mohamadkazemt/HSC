# rubika_bot/views.py

import asyncio
import json
import logging
import time
from urllib.parse import quote

import aiohttp

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import (
    HttpRequest,
    HttpResponse,
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

try:
    from aiohttp_socks import ProxyConnector
except ImportError:  # pragma: no cover
    ProxyConnector = None  # type: ignore[assignment]

from .constants import (
    DEEPLINK_TEMPLATE,
    MAX_USERS_PER_PAGE,
    WEBHOOK_RATE_LIMIT,
    is_ip_allowed,
)
from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser, WebhookLog
from .services import RubPyIntegrationService
from .tasks import send_rubika_message, process_webhook_task

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
        # Log warning asynchronously to avoid blocking
        process_webhook_task.delay({'_ip': ip, '_log_warning': 'وبهوک غیرمجاز', '_log_message': f'درخواست از IP غیرمجاز: {ip}'})
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        # Log error asynchronously to avoid blocking
        process_webhook_task.delay({'_ip': ip, '_log_error': 'وبهوک نامعتبر', '_log_message': 'JSON معتبر نیست', '_log_data': {'ip': ip}})
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    # Store IP in payload for logging in background task
    payload['_ip'] = ip

    # --- NEW ARCHITECTURE ---
    # Queue the payload for background processing and return immediately.
    # Logging is done asynchronously in the task to avoid blocking the response.
    process_webhook_task.delay(payload)
    
    # Return a success response instantly to the Rubika server.
    return JsonResponse({'ok': True, 'status': 'queued'})


# --- Admin Panel & User-facing Views ---
# (The following views are for your website's panel and user pages)

@superuser_required
def settings_view(request: HttpRequest) -> HttpResponse:
    """Render and update Rubika bot settings in the admin panel."""
    settings_obj = RubikaBotSettings.get_solo()
    # Use safe methods to handle any BadSignature errors
    settings_obj.get_token_safe()
    settings_obj.get_proxy_password_safe()
    
    if request.method == 'POST':
        token = (request.POST.get('token') or '').strip() or None
        bot_username = (request.POST.get('bot_username') or '').strip() or None
        settings_obj.token = token
        settings_obj.bot_username = bot_username

        proxy_enabled = request.POST.get('proxy_enabled') in {'on', 'true', '1'}
        proxy_scheme = (request.POST.get('proxy_scheme') or settings_obj.proxy_scheme or 'socks5').lower()
        proxy_host = (request.POST.get('proxy_host') or '').strip() or None
        proxy_port_raw = (request.POST.get('proxy_port') or '').strip()
        proxy_username = (request.POST.get('proxy_username') or '').strip() or None
        proxy_password_input = (request.POST.get('proxy_password') or '').strip()
        clear_proxy_password = request.POST.get('clear_proxy_password') == '1'

        settings_obj.proxy_enabled = proxy_enabled
        settings_obj.proxy_scheme = proxy_scheme if proxy_scheme in dict(settings_obj._meta.get_field('proxy_scheme').choices) else 'socks5'
        settings_obj.proxy_host = proxy_host

        try:
            settings_obj.proxy_port = int(proxy_port_raw) if proxy_port_raw else None
        except ValueError:
            settings_obj.proxy_port = None

        settings_obj.proxy_username = proxy_username
        if clear_proxy_password:
            settings_obj.proxy_password = None
        elif proxy_password_input:
            settings_obj.proxy_password = proxy_password_input

        settings_obj.save()
        RubPyIntegrationService.reset() # Reset service to use new token
        return redirect('rubika_bot:settings')

    # Get user statistics for the summary card
    total_users = RubikaUser.objects.count()
    connected_users = RubikaUser.objects.filter(user__isnull=False).count()
    unconnected_users = total_users - connected_users
    
    # Get recent users for quick preview
    recent_users = RubikaUser.objects.select_related('user', 'user__userprofile').order_by('-updated_at')[:5]

    sample_code = 'SAMPLECODE123'
    deeplink_example = None
    if settings_obj.bot_username:
        deeplink_example = DEEPLINK_TEMPLATE.format(
            bot_username=settings_obj.bot_username.lstrip('@'),
            code=sample_code,
        )

    # Safely access encrypted fields for context
    proxy_password_saved = bool(settings_obj.get_proxy_password_safe())
    proxy_preview = settings_obj.get_masked_proxy_url()

    context = {
        'settings': settings_obj,
        'total_users': total_users,
        'connected_users': connected_users,
        'unconnected_users': unconnected_users,
        'recent_users': recent_users,
        'webhook_url': request.build_absolute_uri(reverse('rubika_bot:webhook')),
        'deeplink_template': DEEPLINK_TEMPLATE,
        'deeplink_example': deeplink_example,
        'proxy_password_saved': proxy_password_saved,
        'proxy_preview': proxy_preview,
        'proxy_choices': RubikaBotSettings._meta.get_field('proxy_scheme').choices,
    }
    return render(request, 'rubika_bot/settings.html', context)


@superuser_required
def users_management_view(request: HttpRequest) -> HttpResponse:
    """View for managing Rubika bot users with detailed information."""
    from datetime import timedelta
    
    # Get filter parameters
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset with optimized queries
    users_qs = RubikaUser.objects.select_related('user', 'user__userprofile').order_by('-updated_at')
    
    # Apply status filter
    if status_filter == 'connected':
        users_qs = users_qs.filter(user__isnull=False)
    elif status_filter == 'unconnected':
        users_qs = users_qs.filter(user__isnull=True)
    
    # Apply search filter
    if search:
        users_qs = users_qs.filter(
            Q(chat_id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__userprofile__personnel_code__icontains=search) |
            Q(user__userprofile__national_code__icontains=search)
        )
    
    # Calculate statistics
    total_users = RubikaUser.objects.count()
    connected_users = RubikaUser.objects.filter(user__isnull=False).count()
    unconnected_users = total_users - connected_users
    today = timezone.now().date()
    active_today = RubikaUser.objects.filter(last_seen__date=today).count()
    
    # Pagination
    paginator = Paginator(users_qs, MAX_USERS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'users_page': page_obj,
        'search_query': search,
        'status_filter': status_filter,
        'total_users': total_users,
        'connected_users': connected_users,
        'unconnected_users': unconnected_users,
        'active_today': active_today,
    }
    
    return render(request, 'rubika_bot/users_management.html', context)


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
def action_test_proxy(request: HttpRequest) -> JsonResponse:
    """Test proxy connectivity before saving settings."""
    if ProxyConnector is None:
        return JsonResponse(
            {
                'ok': False,
                'error': 'پشتیبانی از پراکسی SOCKS نصب نشده است. پکیج aiohttp_socks را نصب کنید.'
            },
            status=400,
        )

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'داده ارسال شده نامعتبر است.'}, status=400)

    scheme = (payload.get('scheme') or 'socks5').lower()
    host = (payload.get('host') or '').strip()
    port_raw = payload.get('port') or payload.get('proxy_port')
    username = (payload.get('username') or '').strip()
    password = (payload.get('password') or '')
    use_saved_password = bool(payload.get('use_saved_password'))

    if not host or not port_raw:
        return JsonResponse({'ok': False, 'error': 'وارد کردن آدرس و پورت پراکسی الزامی است.'}, status=400)

    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'پورت وارد شده معتبر نیست.'}, status=400)

    settings_obj = RubikaBotSettings.get_solo()
    if use_saved_password and not password:
        password = settings_obj.get_proxy_password_safe() or ''
        if not username and settings_obj.proxy_username:
            username = settings_obj.proxy_username

    auth = ''
    if username:
        auth = quote(username, safe='')
        if password:
            auth += f':{quote(password, safe="")}'
        auth += '@'
    proxy_url = f'{scheme}://{auth}{host}:{port}'

    display_proxy = f'{scheme}://{username + "@" if username else ""}{host}:{port}'

    async def _check(url: str) -> int:
        connector = ProxyConnector.from_url(url)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=False) as session:
            async with session.get('https://botapi.rubika.ir/', allow_redirects=False) as response:
                await response.text()
                return response.status

    loop = asyncio.new_event_loop()
    start = time.perf_counter()
    try:
        asyncio.set_event_loop(loop)
        status_code = loop.run_until_complete(_check(proxy_url))
    except Exception as exc:
        logger.warning("Proxy test failed for %s: %s", display_proxy, exc)
        return JsonResponse({'ok': False, 'error': str(exc), 'proxy': display_proxy}, status=400)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)
    duration_ms = (time.perf_counter() - start) * 1000

    return JsonResponse(
        {
            'ok': True,
            'status': status_code,
            'proxy': display_proxy,
            'latency_ms': round(duration_ms, 2),
        }
    )


@superuser_required
def broadcast_view(request: HttpRequest) -> HttpResponse:
    """View for broadcast message page."""
    from datetime import timedelta
    
    # Get statistics
    total_users = RubikaUser.objects.count()
    connected_users = RubikaUser.objects.filter(user__isnull=False).count()
    unconnected_users = total_users - connected_users
    
    # Get all users data for search functionality
    users = RubikaUser.objects.select_related('user', 'user__userprofile').all()
    users_data = []
    for u in users:
        users_data.append({
            'chat_id': u.chat_id,
            'full_name': f"{u.user.first_name} {u.user.last_name}".strip() if u.user else (f"{u.first_name} {u.last_name or ''}".strip() or None),
            'username': u.user.username if u.user else None,
            'personnel_code': u.user.userprofile.personnel_code if u.user and hasattr(u.user, 'userprofile') else None,
            'national_code': u.user.userprofile.national_code if u.user and hasattr(u.user, 'userprofile') else None,
            'connected': bool(u.user),
        })
    
    context = {
        'total_users': total_users,
        'connected_users': connected_users,
        'unconnected_users': unconnected_users,
        'users_json': json.dumps(users_data),
    }
    
    return render(request, 'rubika_bot/broadcast.html', context)


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
def action_broadcast_send(request: HttpRequest) -> JsonResponse:
    """Send broadcast message with advanced options."""
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'داده ارسال شده نامعتبر است.'}, status=400)
    
    text = (payload.get('text') or '').strip()
    if not text:
        return JsonResponse({'ok': False, 'error': 'متن پیام خالی است'}, status=400)
    
    recipient_type = payload.get('recipient_type', 'all')
    custom_recipients = payload.get('custom_recipients', [])
    
    # Determine target users
    if recipient_type == 'all':
        chat_ids = list(RubikaUser.objects.values_list('chat_id', flat=True))
    elif recipient_type == 'connected':
        chat_ids = list(RubikaUser.objects.filter(user__isnull=False).values_list('chat_id', flat=True))
    elif recipient_type == 'unconnected':
        chat_ids = list(RubikaUser.objects.filter(user__isnull=True).values_list('chat_id', flat=True))
    elif recipient_type == 'custom':
        if not custom_recipients:
            return JsonResponse({'ok': False, 'error': 'هیچ کاربری انتخاب نشده است'}, status=400)
        chat_ids = custom_recipients
    else:
        return JsonResponse({'ok': False, 'error': 'نوع مخاطب نامعتبر است'}, status=400)
    
    # Enqueue messages
    for chat_id in chat_ids:
        send_rubika_message.delay(str(chat_id), text)
    
    # Log the action
    WebhookLog.log_info(
        'ارسال همگانی',
        f'پیام به {len(chat_ids)} کاربر ({recipient_type}) در صف قرار گرفت.',
        {'recipient_type': recipient_type, 'count': len(chat_ids)}
    )
    
    return JsonResponse({'ok': True, 'count': len(chat_ids)})


@superuser_required
@require_http_methods(["POST"])
def action_disconnect_user(request: HttpRequest, chat_id: str) -> JsonResponse:
    """Disconnect a user from their linked Rubika account via admin panel."""
    try:
        rubika_user = RubikaUser.objects.select_related('user').get(chat_id=chat_id)
        if rubika_user.user:
            service = RubPyIntegrationService.get_instance()
            # We can't await here, so we call the sync wrapper
            service.engine._disconnect_user(chat_id, rubika_user) 
        return JsonResponse({'ok': True})
    except RubikaUser.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'کاربر یافت نشد'}, status=404)


@superuser_required
def webhook_logs_view(request: HttpRequest) -> HttpResponse:
    """View for webhook logs management page."""
    return render(request, 'rubika_bot/webhook_logs.html')


@superuser_required
def get_webhook_logs(request: HttpRequest) -> JsonResponse:
    log_type = request.GET.get('type', 'all')
    limit = int(request.GET.get('limit', 50))
    logs_qs = WebhookLog.objects.all()
    if log_type != 'all':
        logs_qs = logs_qs.filter(log_type=log_type)
    
    logs = logs_qs.order_by('-created_at')[:limit]
    payload = [
        {
            'id': log.id, 
            'log_type': log.get_log_type_display(), 
            'log_type_value': log.log_type,
            'title': log.title, 
            'message': log.message, 
            'data': log.data, 
            'created_at': log.created_at.isoformat()
        }
        for log in logs
    ]
    return JsonResponse({'ok': True, 'logs': payload, 'count': len(payload)})


@superuser_required
@require_http_methods(["POST"])
def clear_webhook_logs(request: HttpRequest) -> JsonResponse:
    count, _ = WebhookLog.objects.all().delete()
    return JsonResponse({'ok': True, 'deleted': count})


@superuser_required
def export_webhook_logs(request: HttpRequest) -> HttpResponse:
    log_type = request.GET.get('type', 'all')
    format_type = request.GET.get('format', 'json')
    limit = int(request.GET.get('limit', 1000))
    logs_qs = WebhookLog.objects.all()
    if log_type != 'all':
        logs_qs = logs_qs.filter(log_type=log_type)
    logs = logs_qs.order_by('-created_at')[:limit]

    if format_type == 'text':
        lines = [f"[{log.created_at:%Y-%m-%d %H:%M:%S}] {log.log_type.upper()}: {log.title}\n{log.message}\n" for log in logs]
        response = HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')
        filename = f"webhook_logs_{log_type}_{timezone.now():%Y%m%d_%H%M%S}.txt"
    else:
        payload = [{'id': log.id, 'log_type': log.log_type, 'title': log.title, 'message': log.message, 'data': log.data, 'created_at': log.created_at.isoformat()} for log in logs]
        response = HttpResponse(json.dumps(payload, ensure_ascii=False, indent=2), content_type='application/json; charset=utf-8')
        filename = f"webhook_logs_{log_type}_{timezone.now():%Y%m%d_%H%M%S}.json"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def connect_page(request: HttpRequest) -> HttpResponse:
    """Render the connection page for authenticated users."""
    settings_obj = RubikaBotSettings.get_solo()
    rubika_user = getattr(request.user, 'rubika_profile', None)
    is_connected = bool(rubika_user and rubika_user.user)
    
    existing_code = RubikaConnectionCode.objects.filter(user=request.user, used=False, expires_at__gt=timezone.now()).first()
    code_obj = existing_code or RubikaConnectionCode.generate_for_user(request.user)
    
    direct_link = None
    if settings_obj.bot_username:
        direct_link = DEEPLINK_TEMPLATE.format(bot_username=settings_obj.bot_username.lstrip('@'), code=code_obj.code)

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
    
    return JsonResponse({'ok': True, 'code': code.code, 'link': link, 'expires_at': code.expires_at.isoformat()})


@login_required
@require_http_methods(["POST"])
def generate_connection_code(request: HttpRequest) -> JsonResponse:
    """Generate a fresh connection code for the logged-in user."""
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(request.user)
    return JsonResponse({'ok': True, 'code': code.code, 'expires_at': code.expires_at.isoformat()})


def short_link_redirect(request: HttpRequest, short_code: str) -> HttpResponse:
    """
    نمایش صفحه واسط برای کپی کد و باز کردن ربات
    مثال: miepcoj.ir/c/abc123 -> صفحه با کد قابل کپی + لینک ربات
    """
    try:
        from .shortener import get_connection_code_from_short
        
        logger.info(f"🔗 Short link requested: {short_code}")
        
        # دریافت کد کامل از cache
        connection_code = get_connection_code_from_short(short_code)
        
        if not connection_code:
            logger.warning(f"⚠️ Connection code not found for: {short_code}")
            return render(request, 'rubika_bot/link_expired.html', status=404)
        
        logger.info(f"✅ Connection code found: {connection_code[:10]}...")
        
        # دریافت نام کاربری ربات
        settings_obj = RubikaBotSettings.get_solo()
        if not settings_obj.bot_username:
            logger.error("❌ Bot username not configured")
            return HttpResponse('ربات پیکربندی نشده است. لطفاً ابتدا نام کاربری ربات را در تنظیمات وارد کنید.', status=500)
        
        # ساخت لینک ربات (بدون پارامتر start چون کاربر خودش کد را paste می‌کند)
        bot_username = settings_obj.bot_username.lstrip('@')
        bot_link = f"https://rubika.ir/{bot_username}"
        
        logger.info(f"📄 Showing connect page for code: {connection_code[:10]}...")
        
        # نمایش صفحه با کد قابل کپی
        context = {
            'code': connection_code,
            'bot_link': bot_link,
            'bot_username': bot_username,
        }
        
        return render(request, 'rubika_bot/connect_page.html', context)
        
    except Exception as e:
        logger.exception(f"💥 Error in short_link_redirect: {e}")
        return HttpResponse(f'خطا در پردازش لینک: {str(e)}', status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request: HttpRequest) -> JsonResponse:
    """
    Health check endpoint برای مانیتورینگ وضعیت سرویس
    """
    try:
        from django.db import connection
        from celery import current_app
        
        status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        # بررسی دیتابیس
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            status['checks']['database'] = 'ok'
        except Exception as e:
            status['checks']['database'] = f'error: {str(e)}'
            status['status'] = 'unhealthy'
        
        # بررسی Redis/Celery
        try:
            # بررسی اینکه celery worker زنده است
            inspect = current_app.control.inspect()
            active_workers = inspect.active()
            if active_workers:
                status['checks']['celery_workers'] = f'ok ({len(active_workers)} workers)'
            else:
                status['checks']['celery_workers'] = 'no workers found'
                status['status'] = 'degraded'
        except Exception as e:
            status['checks']['celery_workers'] = f'error: {str(e)}'
            status['status'] = 'unhealthy'
        
        # بررسی RubPy Integration Service
        try:
            service = RubPyIntegrationService.get_instance()
            status['checks']['rubpy_service'] = 'ok' if service else 'not initialized'
        except Exception as e:
            status['checks']['rubpy_service'] = f'error: {str(e)}'
        
        # تعیین HTTP status code
        http_status = 200 if status['status'] == 'healthy' else 503
        
        return JsonResponse(status, status=http_status)
        
    except Exception as e:
        logger.exception(f"Error in health_check: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)