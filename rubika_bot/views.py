from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db.models import Q
import json

from .models import RubikaBotSettings, RubikaUser, RubikaConnectionCode
from .services import RubikaClient


def superuser_required(view):
    return user_passes_test(lambda u: u.is_superuser)(view)


@superuser_required
def settings_view(request):
    settings_obj = RubikaBotSettings.get_solo()
    if request.method == 'POST':
        token = (request.POST.get('token') or '').strip()
        bot_username = (request.POST.get('bot_username') or '').strip()
        deeplink_template = (request.POST.get('deeplink_template') or '').strip()
        settings_obj.token = token or None
        settings_obj.bot_username = bot_username or None
        settings_obj.deeplink_template = deeplink_template or None
        settings_obj.save()
        return redirect('rubika_bot:settings')
    # Users table
    users_qs = RubikaUser.objects.all().order_by('-updated_at')
    q = request.GET.get('q')
    if q:
        users_qs = users_qs.filter(Q(chat_id__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(user__username__icontains=q))
    context = {
        'settings': settings_obj,
        'users': users_qs[:200],
        'webhook_url': request.build_absolute_uri(reverse('rubika_bot:webhook')),
    }
    return render(request, 'rubika_bot/settings.html', context)


@superuser_required
def action_register_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    url = request.build_absolute_uri(reverse('rubika_bot:webhook'))
    client = RubikaClient()
    data = client.update_bot_endpoints(url)
    return JsonResponse({'ok': bool(data.get('ok')), 'data': data})


@superuser_required
def action_get_webhook_info(request):
    client = RubikaClient()
    data = client.get_bot_endpoint()
    return JsonResponse({'ok': True, 'data': data})


@superuser_required
def action_broadcast(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    text = (request.POST.get('text') or '').strip()
    if not text:
        return JsonResponse({'ok': False, 'error': 'empty message'}, status=400)
    # enqueue via Celery to avoid blocking
    from .tasks import send_rubika_message
    for u in RubikaUser.objects.values_list('chat_id', flat=True):
        send_rubika_message.delay(str(u), text)
    return JsonResponse({'ok': True})


@login_required
def quick_connect(request):
    settings_obj = RubikaBotSettings.get_solo()
    # generate a fresh code and redirect to bot deeplink if possible
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(request.user)
    if settings_obj.bot_username:
        template = settings_obj.deeplink_template or 'https://rubika.ir/{bot_username}?start={code}'
        link = template.format(bot_username=settings_obj.bot_username, code=code.code)
        return HttpResponseRedirect(link)
    # fallback: show settings page message
    return render(request, 'rubika_bot/quick_connect.html', {
        'code': code.code,
        'bot_username': settings_obj.bot_username,
    })


@login_required
def generate_connection_code(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    # Invalidate previous unused codes (optional)
    RubikaConnectionCode.objects.filter(user=request.user, used=False).delete()
    code = RubikaConnectionCode.generate_for_user(request.user)
    return JsonResponse({'ok': True, 'code': code.code, 'expires_at': code.expires_at.isoformat()})


@csrf_exempt
def webhook_receiver(request):
    if request.method != 'POST':
        return JsonResponse({'ok': True})
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'invalid json'}, status=400)

    # Normalize to message/chat_id/text similar to working Flask bot
    message = payload.get('message') or {}

    # Inline normalization
    if isinstance(payload, dict) and 'inline_message' in payload:
        im = payload.get('inline_message', {})
        message = {
            'chat': {'chat_id': im.get('chat_id')},
            'text': im.get('text', ''),
            'user': {'guid': im.get('sender_id')}
        }

    # update wrapper normalization
    if isinstance(payload, dict) and 'update' in payload:
        u = payload.get('update') or {}
        if u.get('type') == 'NewMessage':
            nm = u.get('new_message') or {}
            message = {
                'chat': {'chat_id': u.get('chat_id')},
                'text': nm.get('text', ''),
                'user': {'guid': nm.get('sender_id')}
            }

    # Support update_type routing
    update_type = payload.get('update_type')

    chat_data = message.get('chat') or {}
    chat_id = chat_data.get('chat_id')
    text = (message.get('text') or '').strip()
    user_data = message.get('user') or {}

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
        return JsonResponse({'ok': False, 'error': 'no chat_id'}, status=200)

    # Ensure RubikaUser exists
    ru = RubikaUser.get_or_create_by_chat(str(chat_id), defaults={
        'first_name': user_data.get('first_name') if isinstance(user_data, dict) else None,
        'last_name': user_data.get('last_name') if isinstance(user_data, dict) else None,
        'metadata': {'raw': payload},
    })
    ru.touch_seen()

    client = RubikaClient()

    # Handle connect command: /connect <code> or /start <code>
    if text.startswith('/connect') or text.startswith('/start'):
        parts = text.split()
        if len(parts) == 2:
            code_str = parts[1]
            code = RubikaConnectionCode.objects.filter(code=code_str, used=False, expires_at__gt=timezone.now()).first()
            if code:
                ru.user = code.user
                ru.save(update_fields=['user'])
                code.mark_used(chat_id=str(chat_id))
                client.send_message(str(chat_id), 'حساب شما با موفقیت متصل شد!', alternatives=candidates)
            else:
                client.send_message(str(chat_id), 'کد اتصال نامعتبر یا منقضی است.', alternatives=candidates)
        else:
            client.send_message(str(chat_id), 'فرمت دستور نادرست است. مثال: /connect <code>', alternatives=candidates)
        return JsonResponse({'ok': True})

    # Minimal button example (optional): reply to /start like Flask
    if text == '/start':
        try:
            client.send_message_with_buttons(str(chat_id), 'یکی از دکمه‌های زیر را انتخاب کن:', rows=[
                [{"id": "1", "type": "Simple", "button_text": "دکمه ۱"}],
                [{"id": "2", "type": "Simple", "button_text": "دکمه ۲"}, {"id": "3", "type": "Simple", "button_text": "دکمه ۳"}],
            ])
        except Exception:
            pass
        return JsonResponse({'ok': True})

    # Handle inline message
    if update_type == 'ReceiveInlineMessage':
        # Already normalized above if inline_message field exists
        # Optionally acknowledge or log; here we just return ok
        return JsonResponse({'ok': True})

    # Handle query callback
    if update_type == 'ReceiveQuery':
        q = payload.get('query') or {}
        qid = q.get('query_id')
        btn = q.get('button_id')
        if qid:
            txt = '✅ دکمه ۱ انتخاب شد!' if btn == '1' else ('✅ دکمه ۲ انتخاب شد!' if btn == '2' else ('✅ دکمه ۳ انتخاب شد!' if btn == '3' else '⚠️ دکمه ناشناخته'))
            client.answer_query(qid, txt)
        return JsonResponse({'ok': True})

    # Selection handlers — no-op acknowledgements (customize as needed)
    if update_type in ('GetSelectionItem', 'SearchSelectionItems'):
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': True})
