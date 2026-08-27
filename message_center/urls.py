from django.urls import path

from . import views, webhook_views

app_name = "message_center"

# ``name`` is the grantable permission string managed by the central
# permissions app and must match the value passed to @permission_required;
# ``url_name`` keeps the URL name stable for reverse(). The inbound webhook
# is intentionally not listed: its security is the HMAC secret, not a login.
BROADCAST_URLS_WITH_LABELS = [
    {
        "path": "broadcast/",
        "view": views.broadcast_compose,
        "url_name": "broadcast_compose",
        "name": "message_broadcast_send",
        "label": "پیام_ارسال پیام گروهی",
    },
    {
        "path": "templates/",
        "view": views.template_list,
        "url_name": "template_list",
        "name": "message_broadcast_send",
        "label": "پیام_قالب‌های پیام",
    },
]

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
] + BROADCAST_URLS_WITH_LABELS

urlpatterns = [
    path(item["path"], item["view"], name=item.get("url_name", item["name"]))
    for item in URLS_WITH_LABELS
] + [
    path("webhook/inbound/", webhook_views.inbound_webhook, name="webhook_inbound"),
    path("broadcast/preview/", views.broadcast_preview, name="broadcast_preview"),
    path("broadcast/send/<int:broadcast_id>/", views.broadcast_send, name="broadcast_send"),
    path("broadcast/cancel/<int:broadcast_id>/", views.broadcast_cancel, name="broadcast_cancel"),
    path("broadcast/list/", views.broadcast_list, name="broadcast_list"),
    path("broadcast/<int:broadcast_id>/", views.broadcast_detail, name="broadcast_detail"),
    path("personnel/search/", views.personnel_search, name="personnel_search"),
    path("templates/", views.template_list, name="template_list"),
]
