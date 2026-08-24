from django.urls import path

from . import views, webhook_views

app_name = "message_center"

# ``name`` is the grantable permission string managed by the central
# permissions app and must match the value passed to @permission_required;
# ``url_name`` keeps the URL name stable for reverse(). The inbound webhook
# is intentionally not listed: its security is the HMAC secret, not a login.
URLS_WITH_LABELS = [
    {
        "path": "leave-reminders/",
        "view": views.leave_reminders,
        "url_name": "leave_reminders",
        "name": "send_leave_reminders",
        "label": "پیام_یادآوری تأیید مرخصی",
    },
    {
        "path": "webhook/settings/",
        "view": webhook_views.webhook_settings,
        "url_name": "webhook_settings",
        "name": "message_webhook_settings",
        "label": "پیام_تنظیمات وب‌هوک",
    },
]

urlpatterns = [
    path(item["path"], item["view"], name=item.get("url_name", item["name"]))
    for item in URLS_WITH_LABELS
] + [
    path("webhook/inbound/", webhook_views.inbound_webhook, name="webhook_inbound"),
]
