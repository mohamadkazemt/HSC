import json
import logging
from typing import Any, Dict, Iterable, Optional

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
try:
    # django-ratelimit <4
    from ratelimit.decorators import ratelimit  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - newer versions
    from django_ratelimit.decorators import ratelimit  # type: ignore

from .constants import (
    CONNECTION_CODE_TTL_MINUTES,
    DEEPLINK_TEMPLATE,
    MAX_USERS_PER_PAGE,
    WEBHOOK_RATE_LIMIT,
    is_ip_allowed,
)
from .models import RubikaBotSettings, RubikaConnectionCode, RubikaUser, WebhookLog
from .services import RubPyIntegrationService
from .tasks import send_rubika_message

logger = logging.getLogger(__name__)


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def settings_view(request: HttpRequest) -> HttpResponse:
    """Render and update Rubika bot settings."""
    settings_obj = RubikaBotSettings.get_solo()
    if request.method == 'POST':
        token = (request.POST.get('token') or '').strip() or None
        bot_username = (request.POST.get('bot_username') or '').strip() or None
        settings_obj.token = token
        settings_obj.bot_username = bot_username
        settings_obj.save()
        RubPyIntegrationService.reset()
        return redirect('rubika_bot:settings')

    users_qs = RubikaUser.objects.select_related('user').order_by('-updated_at')
    search = request.GET.get('q')
    if search:
        users_qs = users_qs.filter(
            Q(chat_id__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(user__username__icontains=search)
        )
    paginator = Paginator(users_qs, MAX_USERS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    deeplink_example = None
    if settings_obj.bot_username:
        deeplink_example = DEEPLINK_TEMPLATE.format(
            bot_username=settings_obj.bot_username.lstrip('@'),
            code='YOUR_CODE',
        )

    context = {
        'settings': settings_obj,
        'users_page': page_obj,
        'webhook_url': request.build_absolute_uri(reverse('rubika_bot:webhook')),
        'deeplink_template': DEEPLINK_TEMPLATE,
        'deeplink_example': deeplink_example,
        'search_query': search or '',
    }
    return render(request, 'rubika_bot/settings.html', context)


@superuser_required
@require_http_methods(["POST"])
def action_register_webhook(request: HttpRequest) -> JsonResponse:
    """Register the webhook endpoints using the RubPy client."""
    try:
        settings_obj = RubikaBotSettings.get_solo()
        if not settings_obj.token:
            return JsonResponse(
                {'ok': False, 'error': 'توکن ربات تنظیم نشده است'}, status=400
            )

        service = RubPyIntegrationService.get_instance()
        webhook_url = request.build_absolute_uri(reverse('rubika_bot:webhook'))
        result = service.update_endpoints(webhook_url)
        WebhookLog.log_info(
            'ثبت وبهوک',
            'نتیجه ثبت وبهوک',
            {'webhook_url': webhook_url, 'result': result},
        )
        status = 200 if result.get('ok') else 500
        return JsonResponse({'ok': result.get('ok'), 'details': result}, status=status)
    except Exception as exc:  # pragma: no cover - network failures
        logger.exception("Webhook registration failed: %s", exc)
        WebhookLog.log_error('ثبت وبهوک', str(exc))
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)


@superuser_required
@require_http_methods(["GET"])
def action_get_webhook_info(request: HttpRequest) -> JsonResponse:
    """Retrieve current webhook status from Rubika."""
    settings_obj = RubikaBotSettings.get_solo()
    if not settings_obj.token:
        return JsonResponse({'ok': False, 'error': 'توکن تنظیم نشده است'}, status=400)
    try:
        service = RubPyIntegrationService.get_instance()
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
    result = service.fetch_webhook_info()
    status = 200 if result.get('ok') else 500
    if not result.get('ok'):
        WebhookLog.log_warning('دریافت وضعیت وبهوک', 'عدم موفقیت در دریافت اطلاعات', result)
    return JsonResponse(result, status=status)


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
    WebhookLog.log_info(
        'ارسال همگانی',
        f'پیام برای {len(chat_ids)} کاربر صف‌بندی شد',
        {'preview': text[:120]},
    )
    return JsonResponse({'ok': True, 'count': len(chat_ids)})


@superuser_required
def get_webhook_logs(request: HttpRequest) -> JsonResponse:
    """Return recent webhook logs optionally filtered by type."""
    try:
        log_type = request.GET.get('type', 'all')
        limit = int(request.GET.get('limit', 50))
        logs = WebhookLog.objects.all()
        if log_type != 'all':
            logs = logs.filter(log_type=log_type)
        logs = logs[:limit]
        payload = [
            {
                'id': log.id,
                'log_type': log.log_type,
                'title': log.title,
                'message': log.message,
                'data': log.data,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]
        return JsonResponse({'ok': True, 'logs': payload, 'count': len(payload)})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)


@superuser_required
@require_http_methods(["POST"])
def clear_webhook_logs(request: HttpRequest) -> JsonResponse:
    """Delete all webhook logs."""
    count = WebhookLog.objects.count()
    WebhookLog.objects.all().delete()
    return JsonResponse({'ok': True, 'deleted': count})


@superuser_required
def export_webhook_logs(request: HttpRequest) -> HttpResponse:
    """Export webhook logs in JSON or text format."""
    log_type = request.GET.get('type', 'all')
    format_type = request.GET.get('format', 'json')
    limit = int(request.GET.get('limit', 1000))
    logs = WebhookLog.objects.all()
    if log_type != 'all':
        logs = logs.filter(log_type=log_type)
    logs = logs.order_by('-created_at')[:limit]

    if format_type == 'text':
        lines = [
            "=" * 80,
            f"لاگ‌های Webhook - {log_type} - تعداد: {logs.count()}",
            "=" * 80,
            "",
        ]
        for log in logs:
            lines.append(f"[{log.created_at:%Y-%m-%d %H:%M:%S}] {log.log_type.upper()}")
            lines.append(f"عنوان: {log.title}")
            lines.append(f"پیام: {log.message}")
            if log.data:
                lines.append(json.dumps(log.data, ensure_ascii=False, indent=2))
            lines.append("-" * 80)
            lines.append("")
        response = HttpResponse(
            '\n'.join(lines), content_type='text/plain; charset=utf-8'
        )
        filename = f"webhook_logs_{log_type}_{timezone.now():%Y%m%d_%H%M%S}.txt"
    else:
        payload = [
            {
                'id': log.id,
                'log_type': log.log_type,
                'title': log.title,
                'message': log.message,
                'data': log.data,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]
        response = HttpResponse(
            json.dumps(payload, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8',
        )
        filename = f"webhook_logs_{log_type}_{timezone.now():%Y%m%d_%H%M%S}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@superuser_required
@require_http_methods(["POST"])
def action_disconnect_user(request: HttpRequest, chat_id: str) -> JsonResponse:
    """Disconnect a user from their linked Rubika account."""
    try:
        rubika_user = RubikaUser.objects.select_related('user').get(chat_id=chat_id)
    except RubikaUser.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'کاربر یافت نشد'}, status=404)
    previous = rubika_user.user.username if rubika_user.user else None
    rubika_user.user = None
    rubika_user.save(update_fields=['user'])
    WebhookLog.log_info(
        'قطع اتصال کاربر',
        f'کاربر {chat_id} از حساب {previous} جدا شد',
    )
    RubPyIntegrationService.get_instance().send_text_message(
        chat_id,
        'اتصال حساب کاربری شما از ربات قطع شد. ❌\n\nبرای اتصال مجدد، یک کد جدید از پنل دریافت کنید.',
    )
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------------------
# Service-backed overrides for legacy handlers
# ---------------------------------------------------------------------------

def _get_service() -> RubPyIntegrationService:
    try:
        return RubPyIntegrationService.get_instance()
    except ValueError as exc:
        WebhookLog.log_error('خطای webhook', f'توکن تنظیم نشده است: {exc}')
        raise


def handle_inline_message(payload: Dict[str, Any]) -> JsonResponse:
    WebhookLog.log_info('پیام اینلاین', 'پردازش با RubPyIntegrationService', {'payload': payload})
    service = _get_service()
    service.handle_webhook_payload({'inline_message': payload})
    return JsonResponse({'ok': True}, status=200)


def handle_query(payload: Dict[str, Any]) -> JsonResponse:
    query_data = payload.get('query') or {}
    chat_id = str(query_data.get('chat_id') or '')
    button_id = str(query_data.get('button_id') or '')
    query_id = query_data.get('query_id')

    WebhookLog.log_info('دکمه فشرده شده', f'دکمه {button_id} از چت {chat_id}', {'query': query_data})

    if not chat_id or not button_id:
        return JsonResponse({'ok': True, 'status': 'ignored'}, status=200)

    user = RubikaUser.get_or_create_by_chat(chat_id)
    user.touch_seen()

    try:
        service = _get_service()
        service.engine._handle_button(chat_id, button_id, user)  # type: ignore[attr-defined]
        if query_id:
            try:
                service.client.answer_query(query_id, '✅ انجام شد')
            except Exception:
                logger.debug("answer_query failed for %s", query_id, exc_info=True)
    except Exception as exc:
        logger.exception("Failed to handle query %s for chat %s", button_id, chat_id)
        WebhookLog.log_error(
            'خطای Query',
            f'خطا در پردازش کوئری: {exc}',
            {'payload': payload},
        )
    return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


def handle_selection_item(payload: Dict[str, Any]) -> JsonResponse:
    WebhookLog.log_info('آیتم انتخاب شد', 'درخواست getSelectionItem دریافت شد', {'payload': payload})
    return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


def handle_search_selection(payload: Dict[str, Any]) -> JsonResponse:
    WebhookLog.log_info('جستجوی آیتم', 'درخواست searchSelectionItems دریافت شد', {'payload': payload})
    return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


def handle_receive_update(payload: Dict[str, Any], chat_id: Any, text: str, user_data: Dict[str, Any]) -> JsonResponse:
    service = _get_service()
    service.handle_webhook_payload(payload)
    return JsonResponse({'ok': True}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate=WEBHOOK_RATE_LIMIT, block=True)
def webhook_receiver(request: HttpRequest) -> JsonResponse:
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        WebhookLog.log_error('وبهوک نامعتبر', 'JSON معتبر نیست', {'ip': ip})
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    if not is_ip_allowed(ip):
        WebhookLog.log_warning('وبهوک غیرمجاز', f'درخواست از IP غیرمجاز: {ip}')
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    WebhookLog.log_incoming(
        'دریافت وبهوک',
        f'دریافت به‌روزرسانی از {ip}',
        {'ip': ip, 'payload': payload},
    )

    try:
        service = _get_service()
    except ValueError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=503)

    result = service.handle_webhook_payload(payload)
    return JsonResponse(result)


@login_required
def connect_page(request: HttpRequest) -> HttpResponse:
    """Render the connection page for authenticated users."""
    settings_obj = RubikaBotSettings.get_solo()
    rubika_user = getattr(request.user, 'rubika_profile', None)
    is_connected = bool(rubika_user and rubika_user.user)
    chat_id = rubika_user.chat_id if rubika_user else None

    existing_code = RubikaConnectionCode.objects.filter(
        user=request.user,
        used=False,
        expires_at__gt=timezone.now(),
    ).first()
    if not existing_code:
        RubikaConnectionCode.objects.filter(
            user=request.user, used=False
        ).delete()
        code_obj = RubikaConnectionCode.generate_for_user(
            request.user, ttl_minutes=CONNECTION_CODE_TTL_MINUTES
        )
    else:
        code_obj = existing_code

    direct_link = None
    if settings_obj.bot_username:
        template = getattr(settings_obj, 'deeplink_template', None) or DEEPLINK_TEMPLATE
        direct_link = template.format(
            bot_username=settings_obj.bot_username.lstrip('@'),
            code=code_obj.code,
        )

    context = {
        'code': code_obj.code,
        'expires_at': code_obj.expires_at,
        'bot_username': settings_obj.bot_username,
        'direct_link': direct_link,
        'is_connected': is_connected,
        'chat_id': chat_id,
        'connected_user': request.user if is_connected else None,
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
    settings_obj = RubikaBotSettings.get_solo()
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(
        request.user, ttl_minutes=CONNECTION_CODE_TTL_MINUTES
    )
    link = None
    if settings_obj.bot_username:
        template = getattr(settings_obj, 'deeplink_template', None) or DEEPLINK_TEMPLATE
        link = template.format(
            bot_username=settings_obj.bot_username.lstrip('@'),
            code=code.code,
        )
    return JsonResponse(
        {
            'ok': True,
            'code': code.code,
            'link': link,
            'expires_at': code.expires_at.isoformat(),
            'instructions': 'روی لینک کلیک کنید یا دستور /start را به همراه کد ارسال کنید.',
        }
    )


@login_required
@require_http_methods(["POST"])
def generate_connection_code(request: HttpRequest) -> JsonResponse:
    """Generate a fresh connection code for the logged-in user."""
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(
        request.user, ttl_minutes=CONNECTION_CODE_TTL_MINUTES
    )
    return JsonResponse(
        {
            'ok': True,
            'code': code.code,
            'expires_at': code.expires_at.isoformat(),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate=WEBHOOK_RATE_LIMIT, block=True)
def webhook_receiver(request: HttpRequest) -> JsonResponse:
    """Receive webhook updates from Rubika and delegate to RubPy."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if not is_ip_allowed(ip):
        WebhookLog.log_warning('وبهوک غیرمجاز', f'درخواست از IP غیرمجاز: {ip}')
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        WebhookLog.log_error('وبهوک نامعتبر', 'JSON معتبر نیست', {'ip': ip})
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    WebhookLog.log_incoming(
        'دریافت وبهوک',
        f'دریافت به‌روزرسانی از {ip}',
        {'ip': ip, 'payload': payload},
    )

    try:
        service = RubPyIntegrationService.get_instance()
    except ValueError as exc:
        logger.warning("Webhook received but token not configured: %s", exc)
        return JsonResponse({'ok': False, 'error': str(exc)}, status=503)

    result = service.handle_webhook_payload(payload)
    return JsonResponse(result)


def _register_webhook_camelcase(webhook_url, token):
    """روش camelCase - همه endpoint ها در یک درخواست"""
    
    # امتحان با URL های مختلف
    urls = [
        f"https://botapi.rubika.ir/v3/{token}/updateBotEndpoint",
        f"https://botapi.rubika.ir/{token}/updateBotEndpoint",
    ]
    
    payload = {
        "receiveUpdate": webhook_url,
        "receiveInlineMessage": webhook_url,
        "receiveQuery": webhook_url,
        "getSelectionItem": webhook_url,
        "searchSelectionItems": webhook_url,
    }
    
    for url in urls:
        # امتحان هم با data و هم با json
        for method in ['data', 'json']:
            try:
                if method == 'data':
                    response = requests.post(url, data=payload, timeout=30)
                else:
                    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                
                try:
                    result = response.json()
                except:
                    result = {"raw": response.text[:200], "status_code": response.status_code}
                
                # بررسی موفقیت
                if result.get("status") == "ok" or response.status_code in [200, 201]:
                    return {
                        'success': True,
                        'url': url,
                        'method': method,
                        'data': result,
                        'endpoints': list(payload.keys())
                    }
                
            except Exception as e:
                continue
    
    # اگر هیچکدام موفق نبود
    return {
        'success': False,
        'error': 'همه URL ها ناموفق بودند',
        'tried_urls': urls
    }


@superuser_required
def action_get_webhook_info(request):
    """دریافت اطلاعات webhook فعلی"""
    try:
        settings_obj = RubikaBotSettings.get_solo()
        if not settings_obj.token:
            return JsonResponse({'ok': False, 'error': 'توکن تنظیم نشده است'}, status=400)
        
        # استفاده از RubikaClient برای دریافت اطلاعات
        try:
            client = RubikaClient()
            result = client.get_bot_endpoint()
            
            # بررسی نتیجه - اگر ok نباشد یا error داشته باشد
            if result and result.get('ok') is not False and 'error' not in result:
                WebhookLog.log_info('بررسی وضعیت Webhook', 'دریافت اطلاعات از API', result)
                return JsonResponse({'ok': True, 'data': result})
            else:
                # اگر خطا داشت، لاگ کن و ادامه بده
                if result and 'error' in result:
                    WebhookLog.log_warning('بررسی وضعیت Webhook', f'خطا از RubikaClient: {result.get("error")}')
                # اگر get_bot_endpoint نتیجه نداد، امتحان مستقیم
                token = settings_obj.token
                urls = [
                    f"https://botapi.rubika.ir/v3/{token}/getBotEndpoint",
                    f"https://botapi.rubika.ir/{token}/getBotEndpoint",
                    # api.rubika.ir حذف شد چون DNS resolve نمی‌شود
                ]
                
                last_error = None
                for url in urls:
                    try:
                        response = requests.get(url, timeout=15)
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                WebhookLog.log_info('بررسی وضعیت Webhook', f'دریافت اطلاعات از {url}', data)
                                return JsonResponse({'ok': True, 'data': data, 'source_url': url})
                            except ValueError as e:
                                last_error = f'JSON decode error: {str(e)}'
                                continue
                        else:
                            last_error = f'HTTP {response.status_code}: {response.text[:200]}'
                            continue
                    except requests.exceptions.RequestException as e:
                        error_str = str(e)
                        # فیلتر کردن خطاهای DNS که غیرضروری هستند
                        if 'NameResolutionError' in error_str or 'Failed to resolve' in error_str or 'api.rubika.ir' in error_str:
                            # این خطا را نادیده بگیریم چون endpoint در دسترس نیست
                            continue
                        last_error = f'Request error: {error_str}'
                        continue
                
                WebhookLog.log_error('بررسی وضعیت Webhook', f'نتوانست اطلاعات را دریافت کند. آخرین خطا: {last_error}')
                return JsonResponse({
                    'ok': False, 
                    'error': 'نتوانست اطلاعات را دریافت کند',
                    'details': last_error
                }, status=500)
                
        except ValueError as e:
            # اگر token تنظیم نشده باشد
            WebhookLog.log_error('بررسی وضعیت Webhook', f'خطا در تنظیمات: {str(e)}')
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'خطا در action_get_webhook_info: {str(e)}', exc_info=True)
        WebhookLog.log_error('بررسی وضعیت Webhook', f'خطای غیرمنتظره: {str(e)}')
        return JsonResponse({'ok': False, 'error': str(e), 'data': None}, status=500)


@superuser_required
def action_broadcast(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    text = (request.POST.get('text') or '').strip()
    if not text:
        return JsonResponse({'ok': False, 'error': 'empty message'}, status=400)
    # enqueue via Celery to avoid blocking
    from .tasks import send_rubika_message
    # Optimize: single query instead of count + values_list
    chat_ids = list(RubikaUser.objects.values_list('chat_id', flat=True))
    user_count = len(chat_ids)
    for chat_id in chat_ids:
        send_rubika_message.delay(str(chat_id), text)
    
    WebhookLog.log_info('ارسال همگانی', f'پیام به {user_count} کاربر ارسال شد', {'text': text[:100]})
    return JsonResponse({'ok': True})


@superuser_required
def get_webhook_logs(request):
    """دریافت لاگ‌های webhook"""
    try:
        # پارامترها
        log_type = request.GET.get('type', 'all')  # all, incoming, outgoing, error, info
        limit = int(request.GET.get('limit', 50))
        
        # Query
        logs = WebhookLog.objects.all()
        
        if log_type != 'all':
            logs = logs.filter(log_type=log_type)
        
        logs = logs[:limit]
        
        # تبدیل به JSON
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'log_type': log.log_type,
                'title': log.title,
                'message': log.message,
                'data': log.data,
                'created_at': log.created_at.isoformat()
            })
        
        return JsonResponse({
            'ok': True,
            'logs': logs_data,
            'count': len(logs_data)
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@superuser_required
def clear_webhook_logs(request):
    """پاک کردن لاگ‌ها"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    
    try:
        # حذف لاگ‌ها
        count = WebhookLog.objects.count()
        WebhookLog.objects.all().delete()
        
        return JsonResponse({
            'ok': True,
            'message': f'{count} لاگ پاک شد'
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@superuser_required
def export_webhook_logs(request):
    """Export لاگ‌ها به JSON یا text"""
    try:
        log_type = request.GET.get('type', 'all')
        format_type = request.GET.get('format', 'json')  # json or text
        limit = int(request.GET.get('limit', 1000))
        
        # Query
        logs = WebhookLog.objects.all().order_by('-created_at')
        
        if log_type != 'all':
            logs = logs.filter(log_type=log_type)
        
        logs = logs[:limit]
        
        if format_type == 'text':
            # Export به صورت text
            lines = []
            lines.append("=" * 80)
            lines.append(f"لاگ‌های Webhook - {log_type} - تعداد: {logs.count()}")
            lines.append("=" * 80)
            lines.append("")
            
            for log in logs:
                lines.append(f"[{log.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {log.log_type.upper()}")
                lines.append(f"عنوان: {log.title}")
                lines.append(f"پیام: {log.message}")
                if log.data:
                    lines.append(f"داده‌ها: {json.dumps(log.data, ensure_ascii=False, indent=2)}")
                lines.append("-" * 80)
                lines.append("")
            
            response = HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="webhook_logs_{log_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.txt"'
            return response
        else:
            # Export به صورت JSON
            logs_data = []
            for log in logs:
                logs_data.append({
                    'id': log.id,
                    'log_type': log.log_type,
                    'title': log.title,
                    'message': log.message,
                    'data': log.data,
                    'created_at': log.created_at.isoformat()
                })
            
            response = HttpResponse(
                json.dumps(logs_data, ensure_ascii=False, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="webhook_logs_{log_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
            return response
            
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


def handle_inline_message(payload):
    """پردازش پیام‌های اینلاین (مطابق Flask bot)"""
    WebhookLog.log_info('پیام اینلاین', 'پیام اینلاین دریافت شد', {'payload': payload})
    return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


def handle_query(payload):
    """پردازش کوئری‌های اینلاین کیبورد (ReceiveQuery) - مطابق Flask bot"""
    try:
        query_data = payload.get('query', {})
        chat_id = query_data.get('chat_id')
        button_id = query_data.get('button_id')
        query_id = query_data.get('query_id')
        
        WebhookLog.log_info('دکمه فشرده شده', f'دکمه {button_id} از چت {chat_id}', {'query': query_data})
        
        client = RubikaClient()
        
        # پردازش دکمه‌های مختلف - مطابق Flask bot
        if not chat_id or not button_id:
            if query_id:
                try:
                    client.answer_query(query_id, '⚠️ اطلاعات ناقص')
                except Exception:
                    pass  # اگر answer_query خطا داد، ادامه بده
            return JsonResponse({'ok': True, 'status': 'ok'}, status=200)
        
        # دریافت candidates برای fallback
        candidates = [str(chat_id)]
        
        # پردازش دکمه‌های دستورات
        if button_id == 'start':
            if query_id:
                try:
                    client.answer_query(query_id, '✅ در حال شروع...')
                except Exception:
                    pass
            # ارسال پیام welcome با دکمه‌ها
            welcome_msg = 'سلام! 👋\n\nبه ربات خوش آمدید.\n\n👇 می‌توانید از دکمه‌های زیر استفاده کنید:'
            buttons = create_command_buttons()
            try:
                result = client.send_message_with_buttons(str(chat_id), welcome_msg, buttons)
                if not result.get('ok'):
                    client.send_message(str(chat_id), welcome_msg, alternatives=candidates)
            except Exception:
                client.send_message(str(chat_id), welcome_msg, alternatives=candidates)
                
        elif button_id == 'account':
            if query_id:
                try:
                    client.answer_query(query_id, '✅ در حال دریافت وضعیت...')
                except Exception:
                    pass
            # دریافت وضعیت کاربر
            try:
                ru = RubikaUser.objects.get(chat_id=chat_id)
                if ru.user:
                    msg = f'📊 وضعیت حساب شما:\n\n✅ متصل به: {ru.user.username}\n👤 نام: {ru.first_name or "بدون نام"}'
                else:
                    msg = '📊 وضعیت حساب شما:\n\n❌ متصل نشده\n\nبرای اتصال، یک کد از پنل دریافت کنید.'
                client.send_message(str(chat_id), msg, alternatives=candidates)
            except RubikaUser.DoesNotExist:
                client.send_message(str(chat_id), '❌ اطلاعات کاربر یافت نشد.', alternatives=candidates)
                
        elif button_id == 'connect':
            if query_id:
                try:
                    client.answer_query(query_id, '✅ برای اتصال، یک کد از پنل دریافت کنید.')
                except Exception:
                    pass
            msg = '🔗 برای اتصال به حساب کاربری:\n\n'
            msg += 'روش 1️⃣: از پنل وب لینک اتصال را دریافت کنید\n'
            msg += 'روش 2️⃣: از پنل وب کد اتصال را دریافت کنید و دستور زیر را ارسال کنید:\n'
            msg += '   /connect [کد]\n\n'
            msg += '💡 برای دریافت کد، به پنل کاربری خود مراجعه کنید.'
            client.send_message(str(chat_id), msg, alternatives=candidates)
            
        elif button_id == 'disconnect':
            if query_id:
                try:
                    client.answer_query(query_id, '✅ در حال قطع اتصال...')
                except Exception:
                    pass
            try:
                ru = RubikaUser.objects.get(chat_id=chat_id)
                if ru.user:
                    old_username = ru.user.username
                    ru.user = None
                    ru.save(update_fields=['user'])
                    msg = f'حساب کاربری "{old_username}" از ربات قطع شد. ❌\n\nبرای اتصال مجدد، یک کد جدید از پنل دریافت کنید.'
                else:
                    msg = 'شما قبلاً به هیچ حساب کاربری متصل نیستید. ⚠️'
                client.send_message(str(chat_id), msg, alternatives=candidates)
            except RubikaUser.DoesNotExist:
                client.send_message(str(chat_id), '❌ اطلاعات کاربر یافت نشد.', alternatives=candidates)
                
        elif button_id == 'help':
            if query_id:
                try:
                    client.answer_query(query_id, '✅ راهنما در حال ارسال...')
                except Exception:
                    pass
            help_msg = '📖 راهنمای ربات:\n\n'
            help_msg += '🔹 /start - شروع کار با ربات\n'
            help_msg += '🔹 /connect [کد] - اتصال به حساب کاربری\n'
            help_msg += '🔹 /account یا /status - مشاهده وضعیت اتصال\n'
            help_msg += '🔹 /disconnect - قطع اتصال از حساب کاربری\n'
            help_msg += '🔹 /help - نمایش این راهنما\n'
            help_msg += '\n💡 برای اتصال به حساب کاربری، ابتدا از پنل وب یک کد اتصال دریافت کنید.\n\n'
            help_msg += '👇 می‌توانید از دکمه‌های زیر استفاده کنید:'
            buttons = create_command_buttons()
            try:
                result = client.send_message_with_buttons(str(chat_id), help_msg, buttons)
                if not result.get('ok'):
                    client.send_message(str(chat_id), help_msg, alternatives=candidates)
            except Exception:
                client.send_message(str(chat_id), help_msg, alternatives=candidates)
        else:
            if query_id:
                client.answer_query(query_id, '⚠️ دکمه ناشناخته')
        
        return JsonResponse({'ok': True, 'status': 'ok'}, status=200)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'خطا در پردازش کوئری: {e}', exc_info=True)
        WebhookLog.log_error('خطای Query', f'خطا در پردازش کوئری: {str(e)}', {'payload': payload})
        return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


def handle_selection_item(payload):
    """پردازش انتخاب آیتم (GetSelectionItem) - مطابق Flask bot"""
    WebhookLog.log_info('آیتم انتخاب شد', 'آیتم انتخاب شد', {'payload': payload})
    return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


def handle_search_selection(payload):
    """پردازش جستجوی آیتم‌ها (SearchSelectionItems) - مطابق Flask bot"""
    WebhookLog.log_info('جستجوی آیتم', 'جستجوی آیتم', {'payload': payload})
    return JsonResponse({'ok': True, 'status': 'ok'}, status=200)


@csrf_exempt
def webhook_receiver(request):
    if request.method != 'POST':
        return JsonResponse({'ok': True})
    
    # لاگ IP و اطلاعات request
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Unknown'))
    
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        
        # لاگ payload خام (مطابق Flask bot)
        WebhookLog.log_incoming(
            'RAW Webhook',
            f'دریافت از {client_ip}',
            {'ip': client_ip, 'raw_payload': payload}
        )
        
    except json.JSONDecodeError as e:
        WebhookLog.log_error('خطای Webhook', f'JSON نامعتبر از {client_ip}', {'error': str(e)})
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    # Normalize to message/chat_id/text similar to working Flask bot
    message = payload.get('message') or {}

    # Inline normalization - اگر button_id دارد، به handle_query بفرست
    if isinstance(payload, dict) and 'inline_message' in payload:
        im = payload.get('inline_message', {})
        aux_data = im.get('aux_data', {})
        button_id = aux_data.get('button_id')
        
        # اگر button_id دارد، این یک کلیک دکمه است نه پیام اینلاین
        if button_id:
            # تبدیل به فرمت ReceiveQuery
            query_payload = {
                'query': {
                    'chat_id': im.get('chat_id'),
                    'button_id': button_id,
                    'query_id': aux_data.get('start_id') or f"query_{im.get('message_id', 'unknown')}"
                }
            }
            WebhookLog.log_info('تشخیص کلیک دکمه', f'دکمه {button_id} از inline_message', {
                'button_id': button_id,
                'chat_id': im.get('chat_id')
            })
            return handle_query(query_payload)
        
        # در غیر این صورت پیام اینلاین عادی است
        message = {
            'chat': {'chat_id': im.get('chat_id')},
            'text': im.get('text', ''),
            'user': {'guid': im.get('sender_id')}
        }

    # update wrapper normalization - چک کردن button_id در new_message
    if isinstance(payload, dict) and 'update' in payload:
        u = payload.get('update') or {}
        if u.get('type') == 'NewMessage':
            nm = u.get('new_message') or {}
            aux_data = nm.get('aux_data', {})
            button_id = aux_data.get('button_id')
            
            # اگر button_id دارد، این یک کلیک دکمه است
            if button_id:
                query_payload = {
                    'query': {
                        'chat_id': u.get('chat_id'),
                        'button_id': button_id,
                        'query_id': aux_data.get('start_id') or f"query_{nm.get('message_id', 'unknown')}"
                    }
                }
                WebhookLog.log_info('تشخیص کلیک دکمه از NewMessage', f'دکمه {button_id} از new_message', {
                    'button_id': button_id,
                    'chat_id': u.get('chat_id')
                })
                return handle_query(query_payload)
            
            message = {
                'chat': {'chat_id': u.get('chat_id')},
                'text': nm.get('text', ''),
                'user': {'guid': nm.get('sender_id')}
            }
            # تنظیم update_type از update.type
            if 'update_type' not in payload:
                payload['update_type'] = 'ReceiveUpdate'

    # Support update_type routing (مطابق Flask bot)
    update_type = payload.get('update_type', 'ReceiveUpdate')
    
    # لاگ برای debugging
    WebhookLog.log_info('Routing Webhook', f'update_type: {update_type}, has_message: {bool(message.get("text"))}', {
        'update_type': update_type,
        'message_text': message.get('text', '')[:50] if message else None,
        'payload_keys': list(payload.keys())
    })
    
    # Routing بر اساس update_type (مطابق Flask bot)
    if update_type == 'ReceiveInlineMessage':
        return handle_inline_message(payload)
    elif update_type == 'ReceiveQuery':
        return handle_query(payload)
    elif update_type == 'GetSelectionItem':
        return handle_selection_item(payload)
    elif update_type == 'SearchSelectionItems':
        return handle_search_selection(payload)
    elif update_type == 'ReceiveUpdate':
        # ادامه پردازش ReceiveUpdate
        pass
    else:
        WebhookLog.log_warning('Webhook نوع ناشناخته', f'نوع به‌روزرسانی ناشناخته: {update_type}', {'payload': payload})
        return JsonResponse({'ok': True, 'status': 'ignored'}, status=200)

    # پردازش ReceiveUpdate (مطابق Flask bot)
    chat_data = message.get('chat') or {}
    chat_id = chat_data.get('chat_id')
    text = (message.get('text') or '').strip()
    user_data = message.get('user') or {}
    
    # لاگ برای debugging
    WebhookLog.log_info('پردازش ReceiveUpdate', f'chat_id: {chat_id}, text: {text[:50]}', {
        'chat_data': chat_data,
        'text': text,
        'message_keys': list(message.keys()) if message else []
    })

    # Collect fallback candidates
    candidates = []
    for k in ("chat_id", "id", "guid"):
        v = chat_data.get(k)
        if v:
            candidates.append(str(v))
    for k in ("chat_id", "chat_guid", "object_guid", "author_object_guid", "user_guid"):
        v = message.get(k)
        if v:
            candidates.append(str(v))
    if isinstance(user_data, dict):
        for k in ("guid", "user_guid"):
            v = user_data.get(k)
            if v:
                candidates.append(str(v))
    if not chat_id and candidates:
        chat_id = candidates[0]

    if not chat_id:
        WebhookLog.log_warning('Webhook بدون chat_id', f'پیام بدون chat_id دریافت شد', {
            'payload_keys': list(payload.keys()),
            'message_keys': list(message.keys()) if message else [],
            'candidates': candidates
        })
        return JsonResponse({'ok': False, 'error': 'no chat_id'}, status=200)

    # Extract user info from payload
    first_name = None
    last_name = None
    
    if isinstance(user_data, dict):
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
    
    # Fallback: try to get from message level
    if not first_name:
        first_name = message.get('first_name')
        last_name = message.get('last_name')
    
    # Ensure RubikaUser exists
    ru = RubikaUser.get_or_create_by_chat(str(chat_id), defaults={
        'first_name': first_name,
        'last_name': last_name,
        'metadata': {'raw': payload},
    })
    ru.touch_seen()
    
    # Update name if we got new info
    if first_name and ru.first_name != first_name:
        ru.first_name = first_name
        ru.last_name = last_name
        ru.save(update_fields=['first_name', 'last_name'])

    client = RubikaClient()

    # Build user display name
    user_display_name = ""
    if ru.first_name:
        user_display_name = ru.first_name
        if ru.last_name:
            user_display_name += " " + ru.last_name
    
    if not user_display_name:
        user_display_name = "کاربر گرامی"

    # Handle help command
    text_lower = text.lower().strip()
    
    if text.startswith('/help') or text.startswith('/راهنما'):
        help_msg = '📖 راهنمای ربات:\n\n'
        help_msg += '🔹 /start - شروع کار با ربات\n'
        help_msg += '🔹 /connect [کد] - اتصال به حساب کاربری\n'
        help_msg += '🔹 /account یا /status - مشاهده وضعیت اتصال\n'
        help_msg += '🔹 /disconnect - قطع اتصال از حساب کاربری\n'
        help_msg += '🔹 /help - نمایش این راهنما\n'
        help_msg += '\n💡 برای اتصال به حساب کاربری، ابتدا از پنل وب یک کد اتصال دریافت کنید.\n\n'
        help_msg += '👇 می‌توانید از دکمه‌های زیر استفاده کنید:'
        buttons = create_command_buttons()
        try:
            result = client.send_message_with_buttons(str(chat_id), help_msg, buttons)
            if result.get('ok'):
                WebhookLog.log_outgoing('ارسال راهنما با دکمه', f'راهنما با دکمه‌ها به {chat_id} ارسال شد', {'result': result})
            else:
                # Fallback به پیام ساده
                client.send_message(str(chat_id), help_msg, alternatives=candidates)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'خطا در ارسال راهنما با دکمه: {str(e)}', exc_info=True)
            # Fallback به پیام ساده
            client.send_message(str(chat_id), help_msg, alternatives=candidates)
        return JsonResponse({'ok': True})
    
    # Handle account status command
    if text.startswith('/account') or text.startswith('/status'):
        if ru.user:
            msg = f'📊 وضعیت حساب شما:\n\n'
            msg += f'✅ متصل به: {ru.user.username}\n'
            msg += f'👤 نام: {user_display_name}\n'
            if ru.user.email:
                msg += f'📧 ایمیل: {ru.user.email}\n'
            msg += f'\n📌 برای قطع اتصال، دستور /disconnect را ارسال کنید.'
        else:
            msg = f'📊 وضعیت حساب شما:\n\n'
            msg += f'❌ متصل نشده\n'
            msg += f'👤 نام: {user_display_name}\n'
            msg += f'\n📌 برای اتصال به حساب کاربری، یک کد از پنل دریافت کنید و دستور /connect را ارسال کنید.'
        client.send_message(str(chat_id), msg, alternatives=candidates)
        return JsonResponse({'ok': True})
    
    # Handle disconnect command
    if text.startswith('/disconnect'):
        if ru.user:
            old_username = ru.user.username
            ru.user = None
            ru.save(update_fields=['user'])
            msg = f'حساب کاربری "{old_username}" از ربات قطع شد. ❌\n\nبرای اتصال مجدد، یک کد جدید از پنل دریافت کنید و دستور /connect را ارسال کنید.'
            client.send_message(str(chat_id), msg, alternatives=candidates)
        else:
            msg = 'شما قبلاً به هیچ حساب کاربری متصل نیستید. ⚠️\n\nبرای اتصال، یک کد از پنل دریافت کنید و دستور /connect را ارسال کنید.'
            client.send_message(str(chat_id), msg, alternatives=candidates)
        return JsonResponse({'ok': True})
    
    # Handle connect command: /connect <code> or /start <code>
    if text.startswith('/connect') or text.startswith('/start'):
        parts = text.split()
        if len(parts) == 2:
            code_str = parts[1]
            # Log the code for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Received connection code: {code_str} from chat_id: {chat_id}")
            
            code = RubikaConnectionCode.objects.filter(code=code_str, used=False, expires_at__gt=timezone.now()).first()
            if code:
                # Check if already connected to a different account
                old_user = None
                if ru.user and ru.user != code.user:
                    old_user = ru.user.username
                
                # Connect to new account
                ru.user = code.user
                ru.save(update_fields=['user'])
                code.mark_used(chat_id=str(chat_id))
                
                if old_user:
                    welcome_msg = f'سلام {user_display_name} عزیز! 👋\n\nحساب شما از اکانت "{old_user}" به اکانت "{code.user.username}" تغییر یافت! ✅'
                else:
                    welcome_msg = f'سلام {user_display_name} عزیز! 👋\n\nحساب شما با موفقیت متصل شد! ✅\n\nاکانت کاربری: {code.user.username}'
                
                client.send_message(str(chat_id), welcome_msg, alternatives=candidates)
                logger.info(f"Successfully linked chat_id {chat_id} to user {code.user.username} (previous: {old_user})")
            else:
                # Check if code exists but is expired or used
                expired_code = RubikaConnectionCode.objects.filter(code=code_str).first()
                if expired_code:
                    if expired_code.used:
                        error_msg = 'این کد قبلاً استفاده شده است. ❌\n\nلطفاً از پنل کاربری یک کد جدید دریافت کنید.'
                    elif expired_code.expires_at <= timezone.now():
                        error_msg = 'کد اتصال منقضی شده است. ❌\n\nلطفاً از پنل کاربری یک کد جدید دریافت کنید.'
                    else:
                        error_msg = 'کد اتصال نامعتبر است. ❌'
                else:
                    error_msg = 'کد اتصال وجود ندارد. ❌\n\nلطفاً از پنل کاربری یک کد معتبر دریافت کنید.'
                
                client.send_message(str(chat_id), error_msg, alternatives=candidates)
                logger.warning(f"Invalid/expired connection code: {code_str} from chat_id: {chat_id}")
        else:
            # No code provided - show welcome message with connection instructions
            try:
                welcome_msg = f'سلام {user_display_name} عزیز! 👋\n\nبه ربات خوش آمدید.\n\n'
                buttons = None
                if ru.user:
                    welcome_msg += f'✅ شما قبلاً به اکانت "{ru.user.username}" متصل شده‌اید.\n\n'
                    welcome_msg += '📌 می‌توانید از دکمه‌های زیر استفاده کنید:\n'
                    buttons = [
                        [
                            create_button("account", "📊 وضعیت"),
                            create_button("disconnect", "❌ قطع اتصال")
                        ],
                        [
                            create_button("help", "📖 راهنما")
                        ]
                    ]
                else:
                    welcome_msg += '🔗 برای اتصال به حساب کاربری:\n\n'
                    welcome_msg += 'روش 1️⃣: از پنل وب لینک اتصال را دریافت کنید\n'
                    welcome_msg += 'روش 2️⃣: از پنل وب کد اتصال را دریافت کنید و دستور زیر را ارسال کنید:\n'
                    welcome_msg += '   /connect [کد]\n\n'
                    welcome_msg += '💡 برای دریافت کد، به پنل کاربری خود مراجعه کنید.\n\n'
                    welcome_msg += '👇 می‌توانید از دکمه‌های زیر استفاده کنید:'
                    buttons = create_command_buttons()
                
                # ارسال پیام با دکمه‌ها
                if buttons:
                    try:
                        result = client.send_message_with_buttons(str(chat_id), welcome_msg, buttons)
                        if result.get('ok'):
                            WebhookLog.log_outgoing('ارسال welcome با دکمه', f'پیام welcome با دکمه‌ها به {chat_id} ارسال شد', {'result': result})
                        else:
                            # Fallback به پیام ساده
                            client.send_message(str(chat_id), welcome_msg, alternatives=candidates)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f'خطا در ارسال welcome با دکمه: {str(e)}', exc_info=True)
                        # Fallback به پیام ساده
                        client.send_message(str(chat_id), welcome_msg, alternatives=candidates)
                else:
                    client.send_message(str(chat_id), welcome_msg, alternatives=candidates)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to send welcome message with buttons: {str(e)}', exc_info=True)
                # Fallback to simple message
                try:
                    client.send_message(str(chat_id), f'سلام {user_display_name}! خوش آمدید 🌟', alternatives=candidates)
                except Exception:
                    logger.error(f'Failed to send fallback welcome message to {chat_id}')
        return JsonResponse({'ok': True})
    
    # Handle greeting messages
    WebhookLog.log_info('بررسی پیام', f'text: "{text}", text_lower: "{text_lower}"', {
        'text': text,
        'text_lower': text_lower,
        'is_greeting': text_lower in ['سلام', 'درود', 'hi', 'hello', 'salam']
    })
    
    # بررسی پیام‌های سلام و درود
    if text_lower.startswith('سلام') or text_lower.startswith('salam') or text_lower in ['درود', 'hi', 'hello']:
        greeting_msg = f'سلام {user_display_name} عزیز! 👋\n\nخوش اومدی! چطور می‌تونم کمکت کنم؟ 🌟'
        # ارسال مستقیم پیام (synchronous)
        try:
            result = client.send_message(str(chat_id), greeting_msg, alternatives=candidates)
            if result.get('ok'):
                WebhookLog.log_outgoing('پاسخ به سلام', f'ارسال موفق به {chat_id}', {'text': greeting_msg, 'result': result})
            else:
                WebhookLog.log_error('ارسال ناموفق', f'نتوانست پاسخ را به {chat_id} ارسال کند', {
                    'text': greeting_msg,
                    'result': result,
                    'error': result.get('error')
                })
        except Exception as e:
            error_str = str(e)
            # فیلتر کردن خطاهای DNS برای api.rubika.ir
            if 'api.rubika.ir' in error_str and ('NameResolutionError' in error_str or 'Failed to resolve' in error_str):
                # این خطا را لاگ نکن چون انتظار می‌رود
                pass
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'خطا در ارسال پاسخ به سلام: {str(e)}', exc_info=True)
                WebhookLog.log_error('خطا در ارسال پاسخ', f'Exception در ارسال پاسخ به {chat_id}: {str(e)}', {'error': str(e)})
        return JsonResponse({'ok': True})
    
    # Handle general messages
    if text:
        response_msg = f'سلام {user_display_name}! ✅\n\nپیام شما دریافت شد:\n"{text}"'
        # ارسال مستقیم پیام (synchronous)
        try:
            result = client.send_message(str(chat_id), response_msg, alternatives=candidates)
            if result.get('ok'):
                WebhookLog.log_outgoing('پاسخ به پیام', f'ارسال موفق به {chat_id}', {'text': response_msg, 'result': result})
            else:
                WebhookLog.log_error('ارسال ناموفق', f'نتوانست پاسخ را به {chat_id} ارسال کند', {
                    'text': response_msg,
                    'result': result,
                    'error': result.get('error')
                })
        except Exception as e:
            error_str = str(e)
            # فیلتر کردن خطاهای DNS برای api.rubika.ir
            if 'api.rubika.ir' in error_str and ('NameResolutionError' in error_str or 'Failed to resolve' in error_str):
                # این خطا را لاگ نکن چون انتظار می‌رود
                pass
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'خطا در ارسال پاسخ به پیام: {str(e)}', exc_info=True)
                WebhookLog.log_error('خطا در ارسال پاسخ', f'Exception در ارسال پاسخ به {chat_id}: {str(e)}', {'error': str(e)})
        return JsonResponse({'ok': True})

    # این قسمت دیگر استفاده نمی‌شود چون routing در بالا انجام شده

    return JsonResponse({'ok': True})
