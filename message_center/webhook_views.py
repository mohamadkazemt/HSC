import hashlib
import hmac
import json
import logging

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from permissions.utils import permission_required

from .models import InboundMessage, WebhookConfig, generate_webhook_secret

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-Rubika-Signature"


def _signature_valid(config, body_bytes, header_value):
    if not config.secret or not header_value:
        return False
    expected = hmac.new(
        config.secret.encode(), body_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, str(header_value).strip().lower())


@csrf_exempt
@require_POST
def inbound_webhook(request):
    """Receiver for PeyamHub inbound-message webhooks (server-to-server).

    Security: HMAC-SHA256 of the raw body in ``X-Rubika-Signature``,
    compared in constant time against WebhookConfig.secret.
    """
    config = WebhookConfig.load()
    if not config.is_active:
        return JsonResponse({"ok": False, "error": "وب‌هوک غیرفعال است."}, status=503)

    body = request.body
    if not _signature_valid(config, body, request.headers.get(SIGNATURE_HEADER)):
        logger.warning("PeyamHub webhook rejected: bad signature")
        return JsonResponse({"ok": False, "error": "امضای نامعتبر است."}, status=403)

    try:
        payload = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "بدنه JSON نامعتبر است."}, status=400)

    message = payload.get("message") or {}
    received_at = message.get("received_at")
    parsed_received_at = None
    if received_at:
        from django.utils.dateparse import parse_datetime

        parsed_received_at = parse_datetime(received_at)

    InboundMessage.objects.create(
        account_phone=payload.get("phone", ""),
        chat_guid=message.get("chat_guid", ""),
        author_guid=message.get("author_guid", ""),
        message_type=message.get("type", ""),
        text=message.get("text", ""),
        message_id=str(message.get("message_id", "")),
        received_at=parsed_received_at,
        raw=payload,
    )
    WebhookConfig.objects.filter(pk=config.pk).update(last_received_at=timezone.now())
    return JsonResponse({"ok": True})


@permission_required("message_webhook_settings")
def webhook_settings(request):
    """صفحه تنظیمات وب‌هوک: URL، کد امنیتی و آخرین پیام‌های دریافتی."""
    config = WebhookConfig.load()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "regenerate_secret":
            config.secret = generate_webhook_secret()
            config.save(update_fields=("secret", "updated_at"))
        elif action == "toggle_active":
            config.is_active = not config.is_active
            config.save(update_fields=("is_active", "updated_at"))
        return redirect("message_center:webhook_settings")

    webhook_url = request.build_absolute_uri("/message-center/webhook/inbound/")
    context = {
        "config": config,
        "webhook_url": webhook_url,
        "inbounds": InboundMessage.objects.all()[:30],
        "inbound_count": InboundMessage.objects.count(),
    }
    return render(request, "message_center/webhook_settings.html", context)
